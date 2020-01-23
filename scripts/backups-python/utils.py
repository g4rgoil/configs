#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import errno
import logging
import os
import pprint as pp
import shlex
import subprocess as sp
import textwrap
import time
import traceback as tb
from datetime import datetime as dt
from os.path import dirname, join

from tendo import singleton

import config

logger = logging.getLogger(__name__)
slack = logging.getLogger("slack")


class CommandGenerator(object):
    # pylint: disable=used-before-assignment
    def __init__(self, config, arguments):
        self.config = config
        self.arguments = arguments

    def create(self):
        return " ".join(x for x in [
            "borg", "create", self.create_options(), self.compression(), self.ratelimit(),
            self.patterns_from(), self.patterns(), self.comment(), self.archive_url(), 
            self.paths()] if x != "")

    def prune(self):
        return " ".join(x for x in ["borg", "prune", self.prune_options(), self.prefix(),
                                    self.keep_options()] if x != "")

    def create_options(self):
        return "--info --stats --show-version --show-rc --exclude-caches --list --filter E"

    def prune_options(self):
        return "--info --stats --show-version --show-rc --list"

    def compression(self):
        return f"--compression '{self.config.archive_compression}'"

    def ratelimit(self):
        return  "" if (x := self.config.remote_ratelimit) == 0 else f"--remote-ratelimit {x}"

    def patterns_from(self):
        return "" if (x := self.config.patterns_from) is None else f"--patterns-from '{x}'"

    def patterns(self):
        return " ".join(f"--pattern '{p}'" for p in self.config.patterns)

    def prefix(self):
        return f"--prefix '{self.config.archive_prefix}'"

    def keep_options(self):
        return " ".join(x for x in [self.keep_within(), self.keep_last(), self.keep_units()] if x != "")

    def keep_within(self):
        return f"--keep-within {self.config.keep_within}" if self.config.keep_within is not None else ""

    def keep_last(self):
        return f"--keep-last {self.config.keep_last}" if self.config.keep_last != 0 else ""

    def keep_units(self):
        return " ".join(f"--keep-{x} {self.config.keep_unit(x)}" for x in [
                        'secondly', 'minutely', 'hourly', 'daily', 'weekly', 'monthly', 'yearly'
                        ] if self.config.keep_unit(x) != 0)

    def archive_url(self):
        return "'::" + self.config.archive_prefix + self.config.archive_suffix + "'"

    def paths(self):
        return "'" + "' '".join(self.config.backup_paths) + "'"

    def comment(self):
        return "" if (comment := self.arguments['--comment']) is None else f"--comment '{comment}''"


class EnvironmentGenerator(object):
    # pylint: disable=used-before-assignment
    def __init__(self, config):
        self.config = config

    def get_env(self):
        return {k: v for k,v in {
            "BORG_REPO": self.borg_repo(),
            "BORG_PASSPHRASE": self.passphrase(),
            "BORG_PASSCOMMAND": self.passphrase_file(),
            "BORG_KEY_FILE": self.key_file(),
            "BORG_LOGGING_CONF": config.borg_logging_config(),
            "BORG_RSH": self.rsh_command(),
            "BORG_RELOCATED_REPO_ACCESS_IS_OK": self.moved_repo_ok(),
            "BORG_UNKNOWN_UNENCRYPTED_REPO_ACCESS_IS_OK": self.unknown_repo_ok()
        }.items() if v != ''}

    def borg_repo(self):
        if self.config.use_ssh:
            return f"ssh://{self.ssh_string()}/{self.config.repo_path}"
        else:
            return f"file://{self.config.repo_path}"

    def ssh_string(self):
        port = ":" + str(self.config.ssh_port) if self.config.ssh_port is not None else ""
        return f"{self.config.ssh_user}@{self.config.ssh_host}{port}"

    def rsh_command(self):
        return "" if (x := self.config.ssh_key_file) is None else f"ssh -i '{x}'"

    def passphrase(self):
        return "" if (x := self.config.repo_passphrase) is None else x

    def passphrase_file(self):
        return "" if (x := self.config.repo_passphrase_file) is None else f"cat '{x}'"

    def key_file(self):
        return  "" if (x := self.config.repo_key) is None else x

    def moved_repo_ok(self):
        return "yes" if self.config.moved_repo_ok else "no"

    def unknown_repo_ok(self):
        return "yes" if self.config.unknown_repo_ok else "no"


def appendix(text, data):
    if isinstance(data, dict):
        return appendix(text, pp.pformat(data, width=200, sort_dicts=False))
    return text + '\n' + textwrap.indent(data.rstrip("\n"), 2 * ' ')


def append_tb(text):
    return appendix(text, tb.format_exc())


def ensure_single_instance(lock_file: str) -> singleton.SingleInstance:
    logger.info(f"Checking if there is another instance already running, lock_file='{lock_file}'")

    try:
        return singleton.SingleInstance(lockfile=lock_file)
    except singleton.SingleInstanceException:
        logger.error(f"Failed to acquire lock for '{lock_file}'")
    except PermissionError as e:
        logger.error(appendix(f"Failed to access lock file '{lock_file}'", str(e)))
    return None


def ensure_mounted(mount_point):
    logger.info(f"Making sure device is mounted, mount_point='{mount_point}'")

    if os.path.ismount(mount_point):
        logger.debug("A device is already mounted at the mount point, proceeding with backup")
        return True

    try:
        sp.check_output(shlex.split(f"mount '{mount_point}'"), stderr=sp.STDOUT)
    except sp.CalledProcessError as e:
        logger.error(f"An error occurred while mounting the device, exit_code={e.returncode}")
        logger.debug(appendix("mount produced the following output", e.output.decode().rstrip()))
        slack.error(f"Failed to mount the device at '{mount_point}'")
        return False

    if not os.path.ismount(mount_point):
        logger.critical(f"The device still doesn't seem to be mounted")
        slack.critical(f"There seems to be a serious issue with the mount point at {mount_point}")
        return False

    return False
    

def test_connection(user, host, port=None, identity_file=None):
    logger.info(f"Trying to reach ssh host, host='{host}'")

    command = " ".join(
        x for x in ["ssh", "-o ConnectTimeout=5", "" if port is None else f"-p {port}", 
        "" if identity_file is None else f"-i {identity_file}", f"{user}@{host} exit"] if x != "")

    try:
        sp.check_output(shlex.split(command), stderr=sp.STDOUT)
        return True
    except sp.CalledProcessError as e:
        logger.error(f"Unable to communicate with the ssh host, exit_code={e.returncode}")
        logger.debug(appendix("ping produced the following output", e.output.decode().rstrip()))
        slack.error("Unable to communicate with the ssh server")
    return False


def ask_passphrase(repo_name):
    try:
        return input(f"Passphrase for repository '{repo_name}': ")
    except EOFError:
        return ""


def trusty_sleep(duration):
    time_start = time.time()
    while (waited := time.time() - time_start) < duration:
        time.sleep(duration - waited)


class ConnectionError(Exception):
    pass


class SingleInstanceError(Exception):
    pass


class MountPointError(Exception):
    pass


class BorgCommandError(Exception):
    def __init__(self, *args, exit_code=None):
        super().__init__(*args)
        self.exit_code = exit_code

    @property
    def is_warning(self):
       return self.exit_code == 1

    @property
    def is_error(self):
       return not self.is_warning
