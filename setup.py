#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Small script for creating symbolic links to the files in this repository"""

import glob, sys

from argparse import ArgumentParser
from os import *
from os.path import *

__version__ = "0.1"


repo_dir = dirname(abspath(__file__))

def create_arg_parser() -> ArgumentParser:
    arg_parser = ArgumentParser(prog="setup.py")
    arg_parser.add_argument("-a", "--all", action="store_true", help="setup all files (default)")

    category_group = arg_parser.add_argument_group("file categories")
    category_group.add_argument("-z", "--zsh",  action="store_true", help="setup files for zsh")
    category_group.add_argument("-b", "--bash", action="store_true", help="setup files for bash")
    category_group.add_argument("-v", "--vim",  action="store_true", help="setup files for vim")
    category_group.add_argument("-m", "--misc", action="store_true", help="setup miscellaneous files")

    return arg_parser


def setup_zsh():
    print("Setting up zsh")

    repo_zsh_dir = join(repo_dir, "zsh")
    etc_zsh_dir = "/etc/zsh"
    if not isdir(repo_zsh_dir):
        print("Can't find zsh directory in repository")
        return

    if not isdir(etc_zsh_dir):
        mkdir(etc_zsh_dir)

    for file_name in listdir(repo_zsh_dir):

        repo_file_abs = join(repo_zsh_dir, file_name)
        etc_file_abs = join(etc_zsh_dir, file_name)

        if isfile(etc_file_abs):
            rename(etc_file_abs, etc_file_abs + ".old")

        if isfile(repo_file_abs):
            symlink(repo_file_abs, etc_file_abs)

    print()


def setup_bash():
    print("Setting up bash")
    
    repo_bash_dir = join(repo_dir, "bash")
    if not isdir(repo_bash_dir):
        print("Can't find bash directory in repository")


def setup_vim():
    print("Setting up vim")


def setup_misc():
    print("Setting up misc files")


if __name__ == "__main__":
    arg_parser = create_arg_parser()
    args = arg_parser.parse_args()

    selected_any = args.zsh or args.bash or args.vim or args.misc
    
    def is_selected(item: bool):
        return item or not selected_any or args.all

    if is_selected(args.zsh):
        setup_zsh()

    if is_selected(args.bash):
        setup_bash()

    if is_selected(args.vim):
        setup_vim()

    if is_selected(args.misc):
        setup_misc()

