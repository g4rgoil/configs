#!/usr/bin/env python3
# -*- coding: utf8 -*-

"""Script for setting up vim on this machine"""

from pathlib import Path

from setup import Category
from setup import repo_dir

__version__ = "0.0.1"


class CategoryVim(Category):
    src_dir = repo_dir.joinpath("vim")
    dst_dir = Path.home() if True else Path("/etc")     # Todo

    def __init__(self):
        pass

    def set_up(self):
        pass

    def back_up(self):
        pass

    def delete(self):
        pass
