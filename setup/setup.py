#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Small script for creating symbolic links to the files in this repository"""

import argparse
import sys

from typing import *

# noinspection PyUnresolvedReferences
from categories import *

__version__ = "0.0.1"


# repo_dir = Path(__file__).absolute().parent.parent


class SetupArgParser(argparse.ArgumentParser):
    usage = "setup.py [-h] [-v] [-b] [-d] <category> [<args>]"

    def __init__(self):
        super().__init__(prog="setup.py", add_help=False, usage=self.usage)

        self.__categories = self.create_categories()

        self.add_modifiers()
        self.add_subparsers()

    def parse_args(self, args=None, namespace=None):
        return super().parse_args(args, namespace)

    @staticmethod
    def create_categories() -> List[category.Category]:
        """
        Find all subclasses of Category and instantiate them.

        :return: a list of categories.
        """
        return [c() for c in category.Category.__subclasses__()]

    def add_modifiers(self):
        group = self.add_argument_group("global options")
        group.add_argument("-h", "--help", action="help", help="show this help message and exit")
        group.add_argument("--version", action="store_true", help="show version information")   # Todo
        group.add_argument("-v", "--verbose", action="store_true", help="be more verbose")      # Todo
        group.add_argument("-b", "--backup", action="store_true", help="backup existing files")    # Todo
        group.add_argument("-d", "--delete", action="store_true", help="delete existing files")    # Todo

    def add_subparsers(self):
        subparsers = super().add_subparsers(title="setup categories", parser_class=CategorySubParser, dest="category")

        for category in self.__categories:
            category.add_subparser(subparsers)


class CategorySubParser(argparse.ArgumentParser):
    def __init__(self, **kwargs):
        self.category = None
        super().__init__(**kwargs)


if __name__ == "__main__":
    arg_parser = SetupArgParser()
    arg_parser.parse_args()

    sys.exit(0)
