#!/usr/bin/env python3

from category import Category

__version__ = "1.0.0"


class CategoryMisc(Category):
    """ Functionality for setting up misceleanus things on this machine """

    directory = "misc"

    def __init__(self):
        super().__init__()

    def set_up(self, namespace=None):
        super().set_up(namespace)
