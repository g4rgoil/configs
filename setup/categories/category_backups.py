#!/usr/bin/env python3

from category import Category
from utils import require_root, get_dist

__version__ = "1.0.0"


class CategoryBackups(Category):
    """ Functionality for setting up backup_scripts on this system """

    directory = "backup_scripts"

    def __init__(self):
        super().__init__()

        self.install_dict = {
            "dependencies": self._install_dependencies,
            "all": None
        }

    def add_subparser(self, subparsers) -> None:
        super().add_subparser(subparsers)

        group = self.parser.add_argument_group("backups specific options")

        choices = self.install_dict.keys()
        help = "install all specified categories; valid categories are " \
               + ", ".join(choices)
        self.parser.add_install_action(group=group, choices=choices, help=help)

    def set_up(self, namespace=None) -> None:
        super().set_up(namespace)

        if namespace.install:
            self.install(namespace.install)

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
