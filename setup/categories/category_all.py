#!/usr/bin/env python3

from pathlib import Path

from category import Category, CategoryCollection
from utils import __repo_dir__

__version__ = "1.0.0"


class CategoryAll(Category):
    """ Functionality for setting up all other categories on this machine """

    directory = None

    def __init__(self):
        path = Path(__repo_dir__, "setup", "resources", "category_all.json")
        super().__init__(path)

    def set_up(self, namespace=None):
        for category in [c for c in CategoryCollection() if
                         c.name != self.name]:
            category.create_utils(namespace)
            category.set_up(namespace)

    def add_subparser(self, subparsers):
        super().add_subparser(subparsers)

        group = self.parser.add_argument_group("all specific options")

        help = "values to pass to the install action of each category; for " \
               "available values consult the help message for each category"
        self.parser.add_install_action(group=group, help=help)
