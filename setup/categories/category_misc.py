#!/usr/bin/env python3

""" Script for setting up miscellaneous files on this machine. """

from pathlib import Path

from categories.category import Category
from categories import require_repo_dir

__version__ = "0.1.0"


class CategoryMisc(Category):
    directory = "misc"

    name = "misc"
    prog = "setup.py vim"
    usage = "setup.py [<global options>] misc [-h]"
    help = "set up miscellaneous files"

    def __init__(self):
        super().__init__()
        self.src_dir = require_repo_dir(self.directory)
        self.dst_dir = Path.home()

        self.files = {
            "yaourtrc": ".yaourtrc",
            "neofetch-config": ".neofetch-config",
            "warprc": ".warprc",
            "terminator": ".config/terminator/config"
        }
        self.directories = {}

        self.parser = None

    def add_subparser(self, subparsers):
        kwargs = dict(help=self.help, usage=self.usage)
        self.parser = subparsers.add_parser(self.name, **kwargs)

    def set_up(self, namespace=None):
        super().set_up(namespace)
