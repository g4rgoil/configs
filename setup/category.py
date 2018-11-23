#!/usr/bin/env python3

""" This module provides classes for setting up this system """

from argparse import ArgumentParser, HelpFormatter, ZERO_OR_MORE
from pathlib import Path

from utils import SetupUtils, FileMapping, require_repo_dir, \
    parse_json_descriptor

__version__ = "1.1.0"


class CategoryCollection(object):
    def __init__(self):
        instances = [c() for c in Category.__subclasses__()]
        self.dict = dict([(i.name, i) for i in instances])

    def __contains__(self, item):
        return item in self.dict

    def __delitem__(self, key):
        del self.dict[key]

    def __getitem__(self, item):
        return self.dict[item]

    def __iter__(self):
        for category in self.dict.values():
            yield category


class Category(object):
    directory = None

    def __init__(self, descriptor_path=None):
        self.name = None
        self.src_dir = None
        self.descriptor = None

        self.files = list()
        self.directories = list()
        self.install_dict = dict()

        self.parser = None
        self.utils = SetupUtils()

        if self.directory is not None:
            self.src_dir = require_repo_dir(self.directory)

        if descriptor_path is not None:
            self.descriptor = parse_json_descriptor(descriptor_path)
        elif self.src_dir is not None:
            path = Path(self.src_dir, ".category.json")
            self.descriptor = parse_json_descriptor(path)

        if self.descriptor is not None:
            self.name = self.descriptor["category"]["name"]

            self.files = self.parse_file_mapping_list(self.descriptor["files"])
            self.directories = self.parse_file_mapping_list(
                self.descriptor["directories"])

    def set_up(self, namespace=None):
        self.delete_backups()
        self.back_up()
        self.delete()
        self.link()

    def add_subparser(self, subparsers):
        if self.descriptor is None:
            raise ValueError("The descriptor dictionary has not been set")

        descriptor = self.descriptor["category"]
        # kwargs = dict(prog=descriptor["prog"], usage=descriptor["usage"],
        #               help=descriptor["help"], version=descriptor["version"])
        self.parser = subparsers.add_parser(self.name, **descriptor["parser"])

    def parse_file_mapping_list(self, dictionary_list):
        return [self.parse_file_mapping(d) for d in dictionary_list]

    def parse_file_mapping(self, dictionary):
        dictionary["src"] = Path(self.src_dir, dictionary["src"]).expanduser()
        dictionary["dst"] = Path(dictionary["dst"]).expanduser()

        try:
            mapping = FileMapping(**dictionary)
        except ValueError as e:
            self.utils.error("Failed to parse mapping %s: %s"
                             % (dictionary, str(e)))
            raise e

        return mapping

    def create_utils(self, namespace=None):
        self.utils = SetupUtils(namespace)

    def link(self):
        for mapping in self.files + self.directories:
            self.utils.try_execute(lambda: mapping.link(self.utils))

    def back_up(self):
        for mapping in self.files + self.directories:
            self.utils.try_execute(lambda: mapping.backup_dst(self.utils))

    def delete(self):
        for mapping in self.files + self.directories:
            self.utils.try_execute(lambda: mapping.delete_dst(self.utils))

    def delete_backups(self):
        for mapping in self.files + self.directories:
            self.utils.try_execute(lambda: mapping.delete_backup(self.utils))

    def install(self, keys):
        if "all" in keys:
            keys = [k for k in self.install_dict.keys() if k != "all"]

        for key in self.install_dict.keys():
            if key not in keys:
                continue

            try:
                self.install_dict[key]()
            except PermissionError as e:
                self.utils.error("Install %s:" % key, str(e))


class CategorySubParser(ArgumentParser):
    def __init__(self, version=None, **kwargs):
        super().__init__(**kwargs, formatter_class=MyHelpFormatter)

        self.version = version
        self.add_version_action()

    def add_version_action(self, version=None):
        if version is None:
            version = self.version

        kwargs = dict(action="version", version=self.prog + " " + version)
        self.add_argument("--version", **kwargs)

    def add_install_action(self, group=None, choices=None, help=None):
        group = self if group is None else group

        kwargs = dict(nargs="*", action="store", default=[], metavar="args",
                      choices=choices, help=help)
        group.add_argument("--install", **kwargs)


class MyHelpFormatter(HelpFormatter):
    def _format_args(self, action, default_metavar):
        get_metavar = self._metavar_formatter(action, default_metavar)

        if action.nargs == ZERO_OR_MORE:
            result = '[%s ...]' % get_metavar(1)
        else:
            result = super()._format_args(action, default_metavar)

        return result
