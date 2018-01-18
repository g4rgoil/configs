#!/usr/bin/env python3

""" Small script for setting up files in this repository.  """

from typing import *
from argparse import ArgumentParser, HelpFormatter, ZERO_OR_MORE

# noinspection PyUnresolvedReferences
from categories import *

__version__ = "0.6.0"


class SetupArgParser(ArgumentParser):
    usage = "setup.py [-h] [-v | -q] [-l | -n] [-b | -d | -k] [-s <suffix>]" \
            " <category> [<args>]"

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
        Find all subclasses of Category and instantiate them. For a
        subclass to be recognized it must have been imported at some
        point. All classes in the categories directory are imported
        automatically.

        :return: a dictionary of categories and their names
        """
        return dict((c.name, c()) for c in category.Category.__subclasses__())

    def add_optional_arguments(self):
        verbosity = self.add_mutually_exclusive_group(required=False)

        kwargs = dict(action="store_true", help="be more verbose")
        verbosity.add_argument("-v", "--verbose", **kwargs)

        kwargs = dict(action="store_true", help="don't print anything")
        verbosity.add_argument("-q", "--quiet", **kwargs)

        kwargs = dict(action="help", help="show this help message and exit")
        self.add_argument("-h", "--help", **kwargs)

        kwargs = dict(action="version", version="setup.py %s" % __version__)
        self.add_argument("--version", **kwargs)

    def add_setup_options(self):
        group = self.add_argument_group("setup options")

        kwargs = dict(action="store_true", help="don't modify the filesystem")
        group.add_argument("--dry-run", **kwargs)

        src_handling = group.add_mutually_exclusive_group(required=False)
        self.set_defaults(link=True)

        kwargs = dict(action="store_true", dest="link")
        kwargs["help"] = "link to the files in this repository (default)"
        src_handling.add_argument("-l", "--link", **kwargs)

        kwargs = dict(action="store_false", dest="link")
        kwargs["help"] = "don't link to the files in this repository"
        src_handling.add_argument("-n", "--no-link", **kwargs)

        dst_handling = group.add_mutually_exclusive_group(required=False)
        kwargs = dict(action="store_const", dest="dst_handling")

        kwargs["const"] = "keep"
        kwargs["help"] = "keep existing files (default)"
        dst_handling.add_argument("-k", "--keep", **kwargs)

        kwargs["const"] = "backup"
        kwargs["help"] = "backup existing files"
        dst_handling.add_argument("-b", "--backup", **kwargs)

        kwargs["const"] = "delete"
        kwargs["help"] = "delete existing files"
        dst_handling.add_argument("-d", "--delete", **kwargs)

        kwargs = dict(action="store", nargs=1, default=["old"], metavar="S",
                      help="the suffix, used when backing up files [: old]")
        group.add_argument("-s", "--suffix", **kwargs)

    def add_subparsers(self):
        kwargs = dict(title="setup categories", dest="category_name",
                      parser_class=CategorySubParser)
        subparsers = super().add_subparsers(**kwargs)
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
