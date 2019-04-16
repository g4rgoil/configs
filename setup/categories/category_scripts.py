#!/usr/bin/env python3

from category import Category
from utils import require_root, get_dist

__version__ = "2.0.0"


class CategoryScripts(Category):
    """ Functionality for setting up various scripts """

    directory = "scripts"

    def __init__(self):
        super().__init__()

    def set_up(self, namespace=None) -> None:
        super().set_up(namespace)

    @require_root
    def _install_dependencies(self) -> None:
        dependencies = self.descriptor["dependencies"]
        system_dependencies = dependencies["system"]
        pip_dependencies = dependencies["pip"]

        dist = get_dist()
        if dist not in system_dependencies:
            raise OSError("Cannot install dependencies: Unknown linux "
                          "distribution '%s'" % dist)

        self.utils.install_packages(dist, *system_dependencies[dist])
        self.utils.install_pip_packages(*pip_dependencies)

        if dist == "arch":
            self.utils.run("systemctl enable --now atd".split())
