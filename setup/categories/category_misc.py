#!/usr/bin/env python3

""" Script for setting up miscellaneous files on this machine. """

from categories.category import Category

__version__ = "0.1.0"


class CategoryMisc(Category):
    directory = "misc"

    def __init__(self):
        super().__init__()

    def add_subparser(self, subparsers):
        super().add_subparser(subparsers)

        self.parser.add_version_action(__version__)

    def set_up(self, namespace=None):
        super().set_up(namespace)
