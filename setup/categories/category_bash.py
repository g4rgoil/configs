#!/usr/bin/env python3

from category import Category

__version__ = "2.0.0"


class CategoryBash(Category):
    """ Functionality for setting up the Bourne Again Shell on this system """

    directory = "bash"

    def __init__(self):
        super().__init__()

    def set_up(self, namespace=None) -> None:
        super().set_up(namespace)
