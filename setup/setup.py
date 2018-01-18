#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" Small script for creating symbolic links to the files in this repository """

from typing import *
from argparse import ArgumentParser, HelpFormatter, ZERO_OR_MORE

# noinspection PyUnresolvedReferences
from categories import *

__version__ = "0.6.0"


class SetupArgParser(ArgumentParser):
    usage = "setup.py [-h] [-v | -q] [-l | -n] [-b | -d | -k] [-s <suffix>] <category> [<args>]"

    def __init__(self):
        super().__init__(prog="setup.py", add_help=False, usage=self.usage,
                         formatter_class=MyHelpFormatter)

        self.categories = self.create_categories()

        self.add_optional_arguments()
        self.add_setup_options()
        self.add_subparsers()

    def parse_args(self, args=None, namespace=None):
        namespace = super().parse_args(args, namespace)

        if namespace.category_name is not None:
            category = self.categories[namespace.category_name]
            category.create_utils(namespace)
            category.set_up(namespace)
        else:
            self.print_usage()

        return namespace

    @staticmethod
    def create_categories() -> Dict[str, category.Category]:
        """
        Find all subclasses of Category and instantiate them. For a subclass to be recognized it
        must have been imported at some point. All classes in the categories directory are imported
        automatically.

        :return: a dictionary of categories and their names
        """
        return dict((c.name, c()) for c in category.Category.__subclasses__())

    def add_optional_arguments(self):
        verbosity = self.add_mutually_exclusive_group(required=False)
        verbosity.add_argument("-v", "--verbose", action="store_true", help="be more verbose")
        verbosity.add_argument("-q", "--quiet", action="store_true", help="don't print anything")

        self.add_argument("-h", "--help", action="help", help="show this help message and exit")
        self.add_argument("--version", action="version", version="setup.py " + __version__)

    def add_setup_options(self):
        group = self.add_argument_group("setup options")

        group.add_argument("--dry-run", action="store_true", help="don't actually set up anything")

        src_handling = group.add_mutually_exclusive_group(required=False)
        src_handling.add_argument("-l", "--link", action="store_true", dest="link",
                                  help="create links to the files in this repository (default)")
        src_handling.add_argument("-n", "--no-link", action="store_false", dest="link",
                                  help="don't create links to the files in this repository")
        self.set_defaults(link=True)

        dst_handling = group.add_mutually_exclusive_group(required=False)
        dst_handling.add_argument("-k", "--keep", action="store_const", dest="dst_handling",
                                  const="keep", help="keep existing files (default)")
        dst_handling.add_argument("-b", "--backup", action="store_const", dest="dst_handling",
                                  const="backup", help="backup existing files")
        dst_handling.add_argument("-d", "--delete", action="store_const", dest="dst_handling",
                                  const="delete", help="delete existing files")
        dst_handling.set_defaults(dst_handling="keep")

        group.add_argument("-s", "--suffix", action="store", nargs=1, default=["old"], metavar="S",
                           help="the suffix, used when backing up files (default: old)")

    def add_subparsers(self):
        subparsers = super().add_subparsers(title="setup categories", dest="category_name",
                                            parser_class=CategorySubParser)
        self.set_defaults(category_name=None)

        for category in self.categories.values():
            category.add_subparser(subparsers)


class CategorySubParser(ArgumentParser):
    def __init__(self, **kwargs):
        super().__init__(**kwargs, formatter_class=MyHelpFormatter)


class MyHelpFormatter(HelpFormatter):
    def _format_args(self, action, default_metavar):
        get_metavar = self._metavar_formatter(action, default_metavar)

        if action.nargs == ZERO_OR_MORE:
            result = '[%s ...]' % get_metavar(1)
        else:
            result = super()._format_args(action, default_metavar)

        return result


if __name__ == "__main__":
    arg_parser = SetupArgParser()
    arg_parser.parse_args()

    arg_parser.exit(0)
