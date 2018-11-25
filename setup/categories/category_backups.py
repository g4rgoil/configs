#!/usr/bin/env python3

from category import Category
from utils import require_root, get_dist

__version__ = "1.0.0"


class CategoryBackups(Category):
    """ Functionality for setting up backup_scripts on this system """

    directory = "backup_scripts"

    def __init__(self):
        super().__init__()

    def set_up(self, namespace=None) -> None:
        super().set_up(namespace)

    @require_root
    def _install_dependencies(self) -> None:
        dependencies = self.descriptor["dependencies"]
        dist = get_dist()

        if dist not in dependencies:
            raise OSError("Cannot install dependencies: Unknown linux "
                          "distribution '%s'" % dist)

        self.utils.install_packages(dist, *dependencies[dist])

        if dist == "arch":
            self.utils.run(["systemctl", "enable", "--now", "atd"])
