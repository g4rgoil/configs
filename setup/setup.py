#!/usr/bin/env python3

""" Small script for setting up files in this repository.  """

from argparse import ArgumentParser
from pathlib import Path

from category import Category, CategorySubParser, MyHelpFormatter
from category import parse_json_descriptor, __repo_dir__

__version__ = "0.6.0"


class SetupArgParser(ArgumentParser):
    """ Class that provides a command line interface for the setup script """

    def __init__(self):
        path = Path(__repo_dir__, "setup", "resources", "parser.json")
        self.descriptor = parse_json_descriptor(path)
        descriptor = self.descriptor

        super().__init__(prog=descriptor["prog"], usage=descriptor["usage"],
                         epilog=descriptor["epilog"], add_help=False,
                         formatter_class=MyHelpFormatter)

        self.categories = CategoryCache()

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

    def add_optional_arguments(self):
        verbosity = self.add_mutually_exclusive_group(required=False)

        kwargs = dict(action="store_true", help="be more verbose")
        verbosity.add_argument("-v", "--verbose", **kwargs)

        kwargs = dict(action="store_true", help="don't print anything")
        verbosity.add_argument("-q", "--quiet", **kwargs)

        kwargs = dict(action="help", help="show this help message and exit")
        self.add_argument("-h", "--help", **kwargs)

        kwargs = dict(action="version",
                      version="setup.py %s" % self.descriptor["version"])
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
        self.set_defaults(dst_handling="keep")

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

        for category in self.categories:
            category.add_subparser(subparsers)


class CategoryCache:
    def __init__(self):
        instances = [c() for c in Category.__subclasses__()]
        self.dict = dict([(i.name, i) for i in instances])

    def __getitem__(self, item):
        return self.dict[item]

    def __contains__(self, item):
        return item in self.dict

    def __iter__(self):
        return iter(self.dict.values())


if __name__ == "__main__":
    arg_parser = SetupArgParser()
    arg_parser.parse_args()

    arg_parser.exit(0)
