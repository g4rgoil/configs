#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Small script for creating symbolic links to the files in this repository"""

import sys

from typing import *
from argparse import Action, ArgumentParser

# noinspection PyUnresolvedReferences
from categories import *

__version__ = "0.1.0"


# repo_dir = Path(__file__).absolute().parent.parent


class SetupArgParser(ArgumentParser):
    usage = "setup.py [-h] [-v] [-l | -n] [-b | -d | -k] <category> [args]"

    def __init__(self):
        super().__init__(prog="setup.py", add_help=False, usage=self.usage)

        self.categories = self.create_categories()

        self.add_modifiers()
        self.add_setup_modifiers()
        self.add_subparsers()

    def parse_args(self, args=None, namespace=None):
        namespace = super().parse_args(args, namespace)

        if namespace.category_name is not None:
            category = self.categories[namespace.category_name]
            category.set_up(namespace)
        else:
            self.print_usage()

        return namespace

    @staticmethod
    def create_categories() -> Dict[str, category.Category]:
        """
        Find all subclasses of Category and instantiate them. For a subclass to be recognized it must have been imported
        at some point. All classes in the categories directory are imported automatically.

        :return: a dictionary of categories and their names
        """
        return dict((c.name, c()) for c in category.Category.__subclasses__())

    def add_modifiers(self):
        group = self.add_argument_group("global options")

        group.add_argument("-h", "--help", action="help", help="show this help message and exit")
        group.add_argument("-v", "--verbose", action="store_true", help="be more verbose")       # Todo
        group.add_argument("--version", action=VersionAction, nargs=0, help="show version information")

    def add_setup_modifiers(self):  # Todo do properly
        group = self.add_argument_group("setup options")

        src_handling = group.add_mutually_exclusive_group(required=False)
        src_handling.add_argument("-l", "--link", action="store_true",
                                  help="create links to the files in this repository (default)")
        src_handling.add_argument("-n", "--no-link", action="store_true",
                                  help="don't create links to the files in this repository (dry run)")

        dst_handling = group.add_mutually_exclusive_group(required=False)
        dst_handling.add_argument("-k", "--keep", action="store_true", help="keep existing files (default)")
        dst_handling.add_argument("-b", "--backup", action="store_true", help="backup existing files")
        dst_handling.add_argument("-d", "--delete", action="store_true", help="delete existing files")

    def add_subparsers(self):
        subparsers = super().add_subparsers(title="setup categories", parser_class=CategorySubParser,
                                            dest="category_name")
        self.set_defaults(category_name=None)

        for category in self.categories.values():
            category.add_subparser(subparsers)


class CategorySubParser(ArgumentParser):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class VersionAction(Action):
    def __call__(self, *args, **kwargs):
        print("setup.py version", __version__)
        sys.exit(0)


if __name__ == "__main__":
    arg_parser = SetupArgParser()
    arg_parser.parse_args()

    sys.exit(0)
