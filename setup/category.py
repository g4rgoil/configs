#!/usr/bin/env python3

""" This module provides classes for setting up this system """

import argparse
import operator

from argparse import ArgumentParser, ZERO_OR_MORE
from pathlib import Path
from typing import List

from utils import SetupUtils, FileMapping, require_repo_dir, \
    parse_json_descriptor, __repo_dir__

__version__ = "2.0.0"


class CategoryCollection(object):
    """ Provides a collection of all available (imported) categories """

    def __init__(self):
        instances = [c() for c in Category.__subclasses__()]
        self.dict = dict(sorted([(i.name, i) for i in instances],
                                key=operator.itemgetter(0)))

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
    """ Provides a base class for all categories that can be set up """

    directory = None

    class _ChoicesContainer(list):
        def __contains__(self, item):
            if ":" in item:
                item = item.split(":", 1)[1]

            return super().__contains__(item)

    def __init__(self, descriptor_path=None):
        self.name = None
        self.help = None
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
            self.help = self.descriptor["category"]["parser"]["help"]

            for install_option in self.descriptor["category"]["install"]:
                self.install_dict[install_option["name"]] = {
                    "help": install_option["help"],
                    "handler": install_option["handler"]
                }

            if len(self.install_dict):
                self.install_dict["all"] = {
                    "help": "install all other available options",
                    "handler": None
                }

            if len(self.install_dict):
                epilog = "available install options:\n"
                epilog += "  {%s}\n" % ",".join(self.install_dict.keys())

                for install_option, option_dict in self.install_dict.items():
                    epilog += str.ljust(4 * " " + install_option, 24)
                    epilog += option_dict["help"] + "\n"

                temp = self.descriptor["category"]["parser"]["epilog"]
                if temp is not None:
                    epilog += "\n" + temp

                self.descriptor["category"]["parser"]["epilog"] = epilog

            self.files = self.parse_file_mapping_list(self.descriptor["files"])
            self.directories = self.parse_file_mapping_list(
                self.descriptor["directories"])

    def set_up(self, namespace=None) -> None:
        self.delete_backups()
        self.back_up()
        self.delete()
        self.link()

        if "install" in namespace:
            if namespace.install and len(self.install_dict):
                self.install(namespace.install)

    def add_subparser(self, subparsers) -> None:
        if self.descriptor is None:
            raise ValueError("The descriptor dictionary has not been set")

        descriptor = self.descriptor["category"]
        self.parser = subparsers.add_parser(self.name, **descriptor["parser"])

        if len(self.install_dict):
            self.add_install_option()

    def add_install_option(self):
        group = self.parser.add_argument_group(self.name + " specific options")

        choices = self._ChoicesContainer(self.install_dict.keys())
        help = "install the specified arguments; see below for information " \
               "on the available options"
        self.parser.add_install_action(group=group, choices=choices, help=help)

    def parse_file_mapping_list(self, dictionary_list) -> List[FileMapping]:
        return [self.parse_file_mapping(d) for d in dictionary_list]

    def parse_file_mapping(self, dictionary) -> FileMapping:
        dictionary["src"] = Path(self.src_dir, dictionary["src"]).expanduser()
        dictionary["dst"] = Path(dictionary["dst"]).expanduser()

        try:
            mapping = FileMapping(**dictionary)
        except ValueError as e:
            self.utils.error("Failed to parse mapping %s: %s"
                             % (dictionary, str(e)))
            raise e

        return mapping

    def create_utils(self, namespace=None) -> None:
        self.utils = SetupUtils(namespace)

    def link(self) -> None:
        for mapping in self.files + self.directories:
            self.utils.try_execute(lambda: mapping.link(self.utils))

    def back_up(self) -> None:
        for mapping in self.files + self.directories:
            self.utils.try_execute(lambda: mapping.backup_dst(self.utils))

    def delete(self) -> None:
        for mapping in self.files + self.directories:
            self.utils.try_execute(lambda: mapping.delete_dst(self.utils))

    def delete_backups(self) -> None:
        for mapping in self.files + self.directories:
            self.utils.try_execute(lambda: mapping.delete_backup(self.utils))

    def install(self, keys) -> None:
        keys = [k[max(0, k.find(":") + 1):] for k in keys if ":" not in k
                or str.startswith(k, self.name + ":")]

        if "all" in keys:
            keys = [k for k in self.install_dict.keys() if k != "all"]

        for key in self.install_dict.keys():
            if key not in keys:
                continue

            try:
                getattr(self, self.install_dict[key]["handler"])()
            except PermissionError as e:
                self.utils.error("Install %s:" % key, str(e))


class CategoryAll(Category):
    """ Functionality for setting up all other (imported) categories """

    directory = None

    def __init__(self):
        path = Path(__repo_dir__, "setup", "resources", "category_all.json")
        super().__init__(path)

    def set_up(self, namespace=None):
        for category in [c for c in CategoryCollection() if
                         c.name != self.name]:
            category.create_utils(namespace)
            category.set_up(namespace)

    def add_subparser(self, subparsers):
        super().add_subparser(subparsers)

        group = self.parser.add_argument_group("all specific options")

        help = "install the specified arguments; consult the help messages " \
               "of other categories for information on the available " \
               "options; to reference an option of a specific category you " \
               "may prefix the option with the name of the category " \
               "(eg. vim:plugins)"
        self.parser.add_install_action(group=group, help=help)


class CategorySubParser(ArgumentParser):
    def __init__(self, version=None, **kwargs) -> None:
        super().__init__(**kwargs, formatter_class=MyHelpFormatter)

        self.version = version
        self.add_version_action()

    def add_version_action(self, version=None) -> None:
        if version is None:
            version = self.version

        kwargs = dict(action="version", version=self.prog + " " + version)
        self.add_argument("--version", **kwargs)

    def add_install_action(self, group=None, choices=None, help=None) -> None:
        group = self if group is None else group

        kwargs = dict(nargs="*", action="store", default=[], metavar="opt",
                      choices=choices, help=help)
        group.add_argument("--install", **kwargs)


class MyHelpFormatter(argparse.RawDescriptionHelpFormatter):
    def _format_args(self, action, default_metavar):
        get_metavar = self._metavar_formatter(action, default_metavar)

        if action.nargs == ZERO_OR_MORE:
            result = '[%s ...]' % get_metavar(1)
        else:
            result = super()._format_args(action, default_metavar)

        return result
