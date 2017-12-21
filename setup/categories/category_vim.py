#!/usr/bin/env python3
# -*- coding: utf8 -*-

"""Script for setting up vim on this machine"""

import inspect

from pathlib import Path

from categories.category import Category
from categories import __repo_dir__

__version__ = "0.0.1"


class CategoryVim(Category):
    name = "vim"
    usage = "setup.py [global options] vim [-h]"
    help = "set up files for the vim text editor"

    parser = None

    src_dir = __repo_dir__ / "vim"  # Todo
    dst_dir = Path.home()   # Todo user vs global

    def __init__(self):
        super().__init__()
        self.files = {"vimrc": ".vimrc", "gvimrc": ".gvimrc", "ideavimrc": ".ideavimrc"}
        self.directories = {"skeletons": ".vim/skeletons"}

    def add_subparser(self, subparsers):
        self.parser = subparsers.add_parser(self.name, help=self.help, usage=self.usage)
        self.parser.category = self

    def set_up(self):
        super().set_up()

    def back_up(self):
        pass

    def delete(self):
        pass

    def _install_linters(self):  # Todo
        pass

    def _install_plugins(self):  # Todo
        pass


Category.register(CategoryVim)
