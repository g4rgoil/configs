#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Small script for creating symbolic links to the files in this repository"""

import builtins
import sys

from argparse import ArgumentParser
from os import *
from os.path import *
from shutil import move

__version__ = "0.1"


repo_dir = dirname(abspath(__file__))


def setup_zsh():
    require_root("Can't set up zsh")
    print("Setting up zsh")

    repo_zsh_dir = require_repo_dir("zsh")
    etc_zsh_dir = "/etc/zsh"
    

    if not isdir(etc_zsh_dir):
        mkdir(etc_zsh_dir)

    for file_name in listdir(repo_zsh_dir):

        repo_file_abs = join(repo_zsh_dir, file_name)
        etc_file_abs = join(etc_zsh_dir, file_name)

        create_backup(etc_file_abs)
        create_link(repo_file_abs, etc_file_abs)

    print_important("Succesfully set up zsh")


def setup_bash():
    require_root("Can't set up bash")
    print("Setting up bash")
    
    repo_bash_dir = require_repo_dir("bash")

    for file_name in listdir(repo_bash_dir):

        repo_file_abs = join(repo_bash_dir, file_name)
        etc_file_abs = join("/etc", "bash." + file_name)

        create_backup(etc_file_abs)
        create_link(repo_file_abs, etc_file_abs)

    print_important("Succesfully set up bash")


def setup_vim():
    require_root("Can't set up vim")
    print("Setting up vim")

    repo_vim_dir = require_repo_dir("vim")
    etc_vim_dir = "/etc/vim"

    repo_vimrc = join(repo_vim_dir, "vimrc")
    etc_vimrc = "/etc/vimrc"

    create_backup(etc_vimrc)
    create_link(repo_vimrc, etc_vimrc)

    repo_vim_skel = join(repo_vim_dir, "skeletons")
    etc_vim_skel = join(etc_vim_dir, "skeletons")

    create_backup(etc_vim_skel)
    create_link(repo_vim_skel, etc_vim_skel)

    print_important("Succesfully set up vim")


def setup_misc():
    print("Setting up misc files")


def create_backup(path):
    backup_path = path + ".old"
    print_move(path, backup_path)
    move(path, backup_path)


def create_link(src, dst):
    print_link(src, dst)
    symlink(src, dst)


def require_repo_dir(name):
    if not isdir(name):
        print_error("Can't find {} directory in repository".format(name))
        sys.exit(1)

    return join(repo_dir, name)


def require_root(msg):
    if geteuid() != 0:
        print_error("Missing root privileges: " + msg)
        sys.exit(2)


def print_link(src, dst):
    print("{:<14} {} -> {}".format("Creating link:", dst, src))


def print_move(old, new):
    print("{:<14} {} -> {}".format("Moving file:", old, new))


def create_arg_parser() -> ArgumentParser:
    arg_parser = ArgumentParser(prog="setup.py", add_help=False)
    arg_parser.add_argument("--help",    action="help",       help="show this help message and exit")
    arg_parser.add_argument("--verbose", action="store_true", help="be more verbose")
    arg_parser.add_argument("--quiet",   action="store_true", help="don't print anything")

    category_group = arg_parser.add_argument_group("file categories")
    category_group.add_argument("-a", "--all",  action="store_true", help="setup all files (default)")
    category_group.add_argument("-z", "--zsh",  action="store_true", help="setup files for zsh")
    category_group.add_argument("-b", "--bash", action="store_true", help="setup files for bash")
    category_group.add_argument("-v", "--vim",  action="store_true", help="setup files for vim")
    category_group.add_argument("-m", "--misc", action="store_true", help="setup miscellaneous files")

    return arg_parser


if __name__ == "__main__":
    arg_parser = create_arg_parser()
    parsed_args = arg_parser.parse_args()

    def print(*args):
        if parsed_args.verbose:
            builtins.print(*args)

    def print_important(*args):
        if not parsed_args.quiet:
            builtins.print(*args)

    def print_error(*args):
        builtins.print(*args)

    selected_any = parsed_args.zsh or parsed_args.bash or parsed_args.vim or parsed_args.misc
    
    def is_selected(item):
        return item or not selected_any or parsed_args.all

    if is_selected(parsed_args.zsh):
        setup_zsh()

    if is_selected(parsed_args.bash):
        setup_bash()

    if is_selected(parsed_args.vim):
        setup_vim()

    if is_selected(parsed_args.misc):
        setup_misc()

    sys.exit(0)

