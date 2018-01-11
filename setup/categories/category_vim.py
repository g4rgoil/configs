#!/usr/bin/env python3
# -*- coding: utf8 -*-

""" Script for setting up vim on this machine """

from pathlib import Path

from categories.category import Category

__version__ = "0.1.0"


class CategoryVim(Category):
    directory = "vim"

    name = "vim"
    usage = "setup.py [global options] vim [-h]"
    help = "set up files for the vim text editor"

    def __init__(self):
        super().__init__()
        self.src_dir = self._require_repo_dir(self.directory)
        self.dst_dir = Path.home()  # Todo user vs global

        self.files = {"vimrc": ".vimrc", "gvimrc": ".gvimrc", "ideavimrc": ".ideavimrc"}
        self.directories = {"skeletons": ".vim/skeletons"}

        self.parser = None

    def add_subparser(self, subparsers):
        self.parser = subparsers.add_parser(self.name, help=self.help, usage=self.usage)

    def set_up(self, namespace=None):
        super().set_up(namespace)

    def link(self):
        super().link()

    def back_up(self):
        super().back_up()

    def delete(self):
        super().delete()

    def _install_linters(self):  # Todo
        raise NotImplementedError()

    def _install_plugins(self):  # Todo
        raise NotImplementedError()
