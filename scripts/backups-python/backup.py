#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Tool for creating borg backups

Usage:
  backup.py [--critical] [--error] [--warning] [--info] [--debug] [--no-create]
            [--no-prune] [--no-schedule] [--comment COMMENT] CONFIG
  backup.py (-h|--help)
  backup.py --version

Arguments:
  CONFIG               path to the backup config file

General Options:
  -h --help            show this message and exit
  --version            print version information and exit
  --critical           work on log level CRITICAL
  -q --quiet --error   work on log level ERROR
  --warning            work on log level WARNING (default)
  -v --verbose --info  work on log level INFO
  --debug              work on log level DEBUG
  --no-create          don't create a backup archive
  --no-prune           don't prune the repository
  --no-schedule        don't schedule a rerun if the ssh host can't be reached
  --comment COMMENT    add a comment text to the archive

Log levels refer to what is printed to stdout, lowest specified log
level takes precedence (i.e. DEBUG < INFO < ... < CRITICAL).
"""

# TODO: Launch backup scripts with nice
# TODO: backup.py [server/create/...]???
# TODO: improve format for delay config option

import logging
import os
import shlex
import subprocess as sp
import sys
import time
from datetime import datetime as dt
from datetime import timedelta as delta
from logging import makeLogRecord
from logging.handlers import RotatingFileHandler
from os.path import basename

from docopt import docopt
from tendo import singleton

import utils
from config import Config, init_logging
from utils import append_tb, appendix

logger = logging.getLogger(__name__)
slack = logging.getLogger("slack")


def prepare_backup(config, arguments) -> singleton.SingleInstance:
    if (lock := utils.ensure_single_instance(config.lock_file)) is None:
        raise utils.SingleInstanceError()

    if not all(map(utils.ensure_mounted, config.ensure_mounted)):
        raise utils.MountPointError()

    if config.use_ssh and not utils.test_connection(
        config.ssh_user, config.ssh_host, config.ssh_port, config.ssh_key_file):
        raise utils.ConnectionError()

    if config.ask_repo_passphrase:
        config.set(utils.ask_passphrase(basename(config.repo_path)), 'backup', 'repository', 'passphrase')

    return lock


def create_backup(config, command_gen, environment) -> int:
    logger.info(f"Creating backup archive, borg_log='{config.borg_log}'")

    if (exit_code := run_borg_command(command_gen.create(), config.borg_log, environment)) == 0:
        logger.debug("Successfully created the backup archive")
    elif exit_code == 1:
        logger.warning("Borg produced a warning while creating the archive, exit_code=1")
        logger.warning("Continuing backup procedure, consult the borg log for further information")
        slack.warning("Borg produced a warning while creating the archive")
    else:
        logger.error(f"Borg produced an error while creating the archive, exit_code={exit_code}")
        slack.error("Backup procedure failed: An error occurred while creating the archive")

    return exit_code

def prune_repository(config, command_gen, environment) -> int:
    logger.info(f"Pruning the repository, borg_log='{config.borg_log}'")

    if (exit_code := run_borg_command(command_gen.prune(), config.borg_log, environment)) == 0:
        logger.debug("Successfully pruned the repository")
    elif exit_code == 1:
        logger.warning("Borg produced a warning, while pruning the repository, exit_code=1")
        slack.warning("Borg produced a warning while pruning the repository")
    else:
        logger.error(f"Borg produced an error while pruning the repository, exit_code={exit_code}")
        slack.error("Backup procedure failed: An error occurred while pruning the repository")

    return exit_code

def run_borg_command(command, log_file, env) -> int:
    logger.debug(command)

    with open(log_file, 'ab') as f:
        try:
            exit_code = sp.check_call(shlex.split(command), bufsize=-1, stdout=f, stderr=f, env=env)
        except sp.CalledProcessError as e:
            exit_code = e.returncode
        finally:
            f.write(b"\n")

    RotatingFileHandler(log_file, mode='a', maxBytes=1048576, backupCount=1).emit(makeLogRecord({}))
    return exit_code


def main(config, arguments):
    logger.info("Prepearing backup procedure")

    lock = prepare_backup(config, arguments)

    logger.info("Performing backup procedure")
    command_gen = utils.CommandGenerator(config, arguments)
    env = utils.EnvironmentGenerator(config).get_env()
    logger.debug(appendix(f"Borg environment variables are:", env))

    backup_exit = 0

    if arguments['--no-create']:
        logger.info("No backup archive will be created, --no-create option is set")
    elif (backup_exit := create_backup(config, command_gen, env)) > 1:
        raise utils.BorgCommandError(exit_code=backup_exit)

    if not config.do_prune or arguments['--no-prune']:
        logger.info("Repository won't be pruned, --no-prune option set or no keep options set")
    elif (backup_exit := max(prune_repository(config, command_gen, env), backup_exit)) > 1:
        raise utils.BorgCommandError(exit_code=backup_exit)

    if backup_exit > 0:
        raise utils.BorgCommandError(exit_code=backup_exit)
    logger.info("Successfully completed backup procedure")


if __name__ == "__main__":
    arguments = docopt(__doc__, version='backup.py 0.5')

    config = Config(os.path.expanduser(arguments['CONFIG']))
    init_logging(config, arguments)
    exit_code, do_continue = 0, True

    while do_continue:
        do_continue = False

        try:
            main(config, arguments)
        except utils.ConnectionError as e:
            if not arguments['--no-schedule']:
                do_continue = True
                logger.warning(f"Scheduling backup to be rerun in {config.backup_delay} minutes")
                slack.info("Scheduling backup to be rerun")
            else:
                logger.error(f"Aborting backup procedure, --no-schedule option is set")
        except utils.BorgCommandError as e:
            exit_code = e.exit_code
            if e.is_error:
                logger.error("Aborting backup procedure, consult the borg log for further info")
        except utils.SingleInstanceError as e:
            exit_code = 2
            logger.error("Aborting backup procedure, another instance may already be running")
        except Exception as e:
            exit_code = 2
            logger.error(append_tb("An exception occurred during the backup procedure"))

        if do_continue:
            try:
                utils.trusty_sleep(config.backup_delay * 60)
            except KeyboardInterrupt:
                logger.warning("Received keyboard interrupt, backup won't be rerun")
                exit_code, do_continue = 2, False


    logging.getLogger('log').debug(f"Program exited with exit code {exit_code}")
    logging.getLogger('clean').debug("")
    sys.exit(exit_code)
