#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import glob
import json
import logging
import logging.config
import os
from os.path import dirname, expanduser, join

import yaml


class Config(object):
    def __init__(self, path):
        self.config = Config.load_config(default_config())
        Config.merge(self.config, Config.load_config(path))

        if self.repo_path is None:
            raise ValueError("Repository path must not be null")

        if self.backup_paths is None or self.backup_paths == []:
            raise ValueError("At least one backup path must be specified")

        if self.use_ssh and (self.ssh_host is None or self.ssh_user is None):
            raise ValueError("If use-ssh ist True, ssh host and user must not be null")

        any(self.expand_user(*keys) for keys in [
            ('backup', 'paths'), ('backup', 'ensure-mounted'), ('backup', 'lock-file'), 
            ('backup', 'patterns-from'), ('repository', 'path'), ('repository', 'key-file'),
            ('repository', 'passphrase-file'), ('ssh', 'key-file'), ('logging', 'directory'),
            ('logging', 'log-file'), ('logging', 'borg-log'), ('logging', 'slack-hook-file')])

        self.set([x for p in self.backup_paths for x in glob.glob(p)], 'backup', 'paths')

    @property
    def log_name(self):
        return self.get('logging', 'name', default="backup")

    @property
    def log_dir(self):
        return self.get('logging', 'directory', default="/var/log/backups")

    @property
    def slack_hook(self):
        if self.slack_hook_file is not None:
            with open(self.slack_hook_file, 'r') as f:
                return f.readline().rstrip()
        else:
            return self.get('logging', 'slack-hook')

    @property
    def slack_hook_file(self):
       return self.get('logging', 'slack-hook-file')

    @property
    def log_base(self):
        return join(self.log_dir, self.log_name)

    @property
    def log_file(self):
        return self.get('logging', 'log-file', default=self.log_base + ".log")

    @property
    def borg_log(self):
        return self.get('logging', 'borg-log', default=self.log_base + ".borg")

    @property
    def lock_file(self):
        return self.get('backup', 'lock-file', default=join("/var/run", self.log_name) + "-backup.lock")

    @property
    def ssh_host(self):
        return self.get('ssh', 'host')

    @property
    def ssh_port(self):
        return self.get('ssh', 'port')

    @property
    def ssh_user(self):
        return self.get('ssh', 'user')

    @property
    def ssh_key_file(self):
       return self.get('ssh', 'key-file')

    @property
    def repo_path(self):
        return self.get('repository', 'path')

    @property
    def repo_key(self):
        return self.get('repository', 'key-file')

    @property
    def repo_passphrase(self):
        return self.get('repository', 'passphrase')

    @property
    def repo_passphrase_file(self):
        return self.get('repository', 'passphrase-file')

    @property
    def ask_repo_passphrase(self):
        return self.get('repository', 'ask-passphrase', default=False)

    @property
    def use_ssh(self):
        return self.get('repository', 'use-ssh', default=False)

    @property
    def backup_paths(self):
        if isinstance(self.get('backup', 'paths'), str):
            return [self.get('backup', 'paths')]
        else:
            return self.get('backup', 'paths')

    @property
    def ensure_mounted(self):
        if isinstance(self.get('backup', 'ensure-mounted'), str):
            return [self.get('backup', 'ensure-mounted')]
        else:
            return self.get('backup', 'ensure-mounted', default=[])

    @property
    def remote_ratelimit(self):
        return self.get('repository', 'ratelimit', default=0)

    @property
    def backup_delay(self):
        return self.get('backup', 'delay', default=0)

    @property
    def do_schedule(self):
        return self.backup_delay != 0

    @property
    def moved_repo_ok(self):
       return self.get('moved_repo_ok', default=True)

    @property
    def unknown_repo_ok(self):
       return self.get('unknown_repo_ok', default=True)

    @property
    def archive_name(self):
        return self.archive_prefix + self.archive_suffix

    @property
    def archive_prefix(self):
        return self.get('backup', 'prefix', default="{hostname}")

    @property
    def archive_suffix(self):
        return self.get('backup', 'suffix', default="-{now}")

    @property
    def archive_compression(self):
        return self.get('backup', 'compression', default="lz4")

    @property
    def patterns_from(self):
        return self.get('backup', 'patterns-from')

    @property
    def patterns(self):
        if isinstance(self.get('backup', 'patterns'), str):
            return [self.get('backup', 'patterns')]
        return self.get('backup', 'patterns', default=[])

    @property
    def do_prune(self):
        return any(v is not None for k, v in self.get('keep', default={}).items())

    @property
    def keep_within(self):
        return self.get('keep', 'within')

    @property
    def keep_last(self):
       return self.get('keep', 'last', default=0)

    def keep_unit(self, unit):
        return self.get('keep', unit, default=0)

    def get(self, *keys, default=None):
        value = self.config
        for key in keys:
            if value is None or not isinstance(value, dict):
                return default
            value = value.get(key)

        return default if value is None else value

    def set(self, value, *keys):
        if not keys:
            raise ValueError("At least one key must be specified")

        dictionary = self.config
        for key in keys[:-1]:
            if key not in dictionary or dictionary[key] is None:
                dictionary[key] = {}
            elif not isinstance(dictionary[key], dict):
                raise ValueError(f"Cant set value {'/'.join(keys)}")
            dictionary = dictionary[key]

        dictionary[keys[-1]] = value

    def expand_user(self, *keys):
        if isinstance((value := self.get(*keys)), str):
            self.set(expanduser(value), *keys)
        elif isinstance(value, list):
            self.set([expanduser(x) for x in value], *keys)

    @staticmethod
    def load_config(path):
        with open(path, 'r') as f:
            if (extension := path.split('.')[-1]) in ['yaml', 'yml']:
                return yaml.safe_load(f.read())
            elif extension == 'json':
                return json.load(f)
            else:
                raise NotImplementedError("Config must be either yaml or json")

    @staticmethod
    def merge(dict1, dict2):
        for k, v2 in dict2.items():
            v1 = dict1.get(k)

            if isinstance(v1, dict) and isinstance(v2, dict):
                Config.merge(v1, v2)
            else:
                dict1[k] = v2


def default_config():
    return join(dirname(__file__), "default.yaml")


def logging_config():
    return join(dirname(__file__), "logging.yaml")


def borg_logging_config():
    return join(dirname(__file__), "borg-logging.ini")


def init_logging(config, arguments):
    with open(logging_config(), 'r') as f:
        log_config = yaml.safe_load(f.read())

        os.makedirs(config.log_dir, exist_ok=True)

        log_config['handlers']['log']['filename'] = config.log_file
        log_config['handlers']['clean']['filename'] = config.log_file

        if config.slack_hook is None:
            log_config['loggers']['slack']['handlers'] = ['null-handler']
        else:
            log_config['handlers']['slack']['url'] = config.slack_hook
            log_config['formatters']['slack']['format'] = \
                log_config['formatters']['slack']['format'].format(config.log_name)

        levels = ["debug", "info", "warning", "error", "critical"]
        log_config['handlers']['console']['level'] = next(
            (l for l in levels if arguments["--" + l]), "warning").upper()

    logging.config.dictConfig(log_config)
    logging.getLogger("").handlers[0].addFilter(console_filter)


def console_filter(record):
    if record.name.startswith("apscheduler") and record.levelno < 30:
        return 0
    if record.name.startswith("tendo") and record.levelno < 30:
        return 0

    return 1
