#!/usr/bin/env python3

from category import Category

__version__ = "1.0.0"


class CategoryBackups(Category):
    """ Functionality for setting up the setup script """

    directory = "setup"

    def __init__(self):
        super().__init__()

    def set_up(self, namespace=None) -> None:
        super().set_up(namespace)
