#!/usr/bin/env python3

""" This module provides a command line interface for the setup script """

import subprocess
import sys

from argparse import ArgumentParser, Namespace
from pathlib import Path

from category import CategoryCollection, CategorySubParser, MyHelpFormatter
from utils import __repo_dir__, parse_json_descriptor, remove_user_options, \
    start_subprocess, load_categories

__version__ = "1.2.0"


class SetupArgParser(ArgumentParser):
    """ This class provides an argument parser for for the setup script """

    def __init__(self):
        path = Path(__repo_dir__, "setup", "resources", "parser.json")
        self.descriptor = parse_json_descriptor(path)

        super().__init__(**self.descriptor["parser"],
                         formatter_class=MyHelpFormatter)

        try:
            self.categories = CategoryCollection()
        except ValueError as e:
            print("An error occurred while creating the categories: " + str(e))
            self.exit(2)

        self.add_optional_arguments()
        self.add_setup_options()
        self.add_subparsers()

    def parse_args(self, args=None, namespace=None) -> Namespace:
        namespace = super().parse_args(args, namespace)

        if namespace.user is None:
            return self.set_up(namespace)

        args = [sys.executable] + remove_user_options(sys.argv)

        for user in namespace.user:
            try:
                proc = start_subprocess(args, user)
                proc.wait()
            except subprocess.SubprocessError as e:
                print("ERROR: Failed to run as '%s'." % user)

        return namespace

    def set_up(self, namespace) -> Namespace:
        if namespace.category_name is not None:
            category = self.categories[namespace.category_name]
            category.create_utils(namespace)
            category.set_up(namespace)
        else:
            self.print_usage()

        return namespace

    def add_optional_arguments(self) -> None:
        """ Adds optional arguments to the parser """

        verbosity = self.add_mutually_exclusive_group(required=False)

        kwargs = dict(action="store_true", help="be more verbose")
        verbosity.add_argument("-v", "--verbose", **kwargs)

        kwargs = dict(action="store_true", help="don't print anything")
        verbosity.add_argument("-q", "--quiet", **kwargs)

        kwargs = dict(action="store_false", dest="confirm")
        kwargs["help"] = "Bypass confirmation dialogs"
        self.add_argument("--noconfirm", **kwargs)

        kwargs = dict(action="store_true", dest="confirm")
        kwargs["help"] = "Negate effects of previous --noconfirm"
        self.add_argument("--confirm", **kwargs)

        kwargs = dict(action="help", help="show this help message and exit")
        self.add_argument("-h", "--help", **kwargs)

        kwargs = dict(action="version",
                      version="setup.py %s" % self.descriptor["version"])
        self.add_argument("--version", **kwargs)

    def add_setup_options(self) -> None:
        """ Adds options for modifying the setup process """

        group = self.add_argument_group("setup options")

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

        kwargs = dict(action="store", nargs=1, default=["old"], metavar="S", )
        kwargs["help"] = "the suffix, used when backing up files [: old]"
        group.add_argument("-s", "--suffix", **kwargs)

        kwargs = dict(action="store_true", dest="delete_backups")
        kwargs["help"] = "delete old backups of files"
        group.add_argument("--delete-backups", **kwargs)

        kwargs = dict(action="append", default=None, metavar="U",
                      help="run for each user (specify once for each user)")
        group.add_argument("-u", "--user", **kwargs)

    def add_subparsers(self, **kwargs) -> None:
        """ Adds a subparser for each category defined in self.categories """

        kwargs = dict(title="setup categories", dest="category_name",
                      parser_class=CategorySubParser)
        subparsers = super().add_subparsers(**kwargs)
        self.set_defaults(category_name=None)

        for category in self.categories:
            category.add_subparser(subparsers)


if __name__ == "__main__":
    load_categories()
    arg_parser = SetupArgParser()
    arg_parser.parse_args()

    arg_parser.exit(0)
