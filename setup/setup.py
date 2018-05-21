#!/usr/bin/env python3

""" This module provides a command line interface for the setup script """

import os
import sys
import pwd
import subprocess

from argparse import ArgumentParser
from pathlib import Path

from category import CategoryCollection, CategorySubParser, MyHelpFormatter
from category import parse_json_descriptor, __repo_dir__

__version__ = "1.1.0"


def remove_option_value_pair(collection, option):
    index = -1
    if option in collection:
        index = collection.index(option)
        del collection[index:index+2]

    return index


def remove_user_options(argv=None):
    if argv is None:
        argv = sys.argv
    argv = argv.copy()

    while remove_option_value_pair(argv, "-u") != -1 or \
            remove_option_value_pair(argv, "--user") != -1:
        pass

    return argv


def start_subprocess(args, user):
    pw_record = pwd.getpwnam(user)
    user_name = pw_record.pw_name
    user_home = pw_record.pw_dir
    uid = pw_record.pw_uid
    gid = pw_record.pw_gid

    cwd = os.getcwd()

    env = os.environ.copy()
    env["HOME"] = user_home
    env["LOGNAME"] = user_name
    env["PWD"] = cwd
    env["USER"] = user_name

    process = subprocess.Popen(
            args, preexec_fn=demote(uid, gid), cwd=cwd, env=env
    )

    return process


def demote(uid, gid):
    def result():
        try:
            os.setgid(gid)
            os.setuid(uid)
        except PermissionError:
            sys.exit(2)

    return result


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
            print("An error occured while creatin the categories: " + e)
            self.exit(2)

        self.add_optional_arguments()
        self.add_setup_options()
        self.add_subparsers()

    def parse_args(self, args=None, namespace=None):
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

    def set_up(self, namespace):
        if namespace.category_name is not None:
            category = self.categories[namespace.category_name]
            category.create_utils(namespace)
            category.set_up(namespace)

        else:
            self.print_usage()

        return namespace

    def add_optional_arguments(self):
        """ Adds optional arguments to the parser """
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

        kwargs = dict(action="store", nargs=1, default=["old"], metavar="S",
                      help="the suffix, used when backing up files [: old]")
        group.add_argument("-s", "--suffix", **kwargs)

        kwargs = dict(action="append", default=None, metavar="U",
                      help="run for each user (specify once for each user)")
        group.add_argument("-u", "--user", **kwargs)

    def add_subparsers(self, **kwargs):
        """ Adds a subparser for each category defined in self.categories """
        kwargs = dict(title="setup categories", dest="category_name",
                      parser_class=CategorySubParser)
        subparsers = super().add_subparsers(**kwargs)
        self.set_defaults(category_name=None)

        for category in self.categories:
            category.add_subparser(subparsers)


if __name__ == "__main__":
    arg_parser = SetupArgParser()
    arg_parser.parse_args()

    arg_parser.exit(0)
