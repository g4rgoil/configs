#!/usr/bin/env python3

""" Script for setting up vim on this machine """

import shlex

from pathlib import Path

from categories.category import Category
from categories import require_root
from categories import get_dist

__version__ = "1.1.0"


class CategoryVim(Category):
    directory = "vim"

    def __init__(self):
        super().__init__()

        self.install_dict = {
            "vundle": self._install_plugin_manager,
            "plugins": self._install_plugins,
            "ycm": self._install_ycm,
            "linters": self._install_linters,
            "all": None
        }

    def add_subparser(self, subparsers):
        super().add_subparser(subparsers)

        self.parser.add_version_action(__version__)

        group = self.parser.add_argument_group("vim specific options")

        choices = self.install_dict.keys()
        help = "install all specified categories; valid categories " \
               + ", ".join(choices)
        self.parser.add_install_action(group=group, choices=choices, help=help)

    def set_up(self, namespace=None):
        super().set_up(namespace)

        if namespace.install:
            self.install(namespace.install)

    def _install_plugin_manager(self):
        install_location = Path("~/.vim/bundle/Vundle.vim").expanduser()
        src_url = "https://github.com/VundleVim/Vundle.vim.git"

        self.utils.clone_repo(src_url, install_location, name="Vundle")

    def _install_plugins(self):
        self.utils.error("Installing plugins with Vundle...")

        args = shlex.split("vim -c PluginInstall -c PluginUpdate "
                           "-c PluginClean -c quitall")
        proc = self.utils.run(args)

        if proc.returncode != 0:
            self.utils.error("Failed to install plugins: Exited with code %s"
                             % proc.returncode)

    def _install_ycm(self):
        self.utils.error("Installing YouCompleteMe...")

        ycm_installer = Path("~/.vim/bundle/YouCompleteMe/"
                             "install.py").expanduser()
        option_string = "--clang-completer"

        args = ["python", ycm_installer, option_string]
        proc = self.utils.run(args)

        if proc.returncode != 0:
            self.utils.error("Failed to install YouCompleteMe: "
                             "Exited with code %s" % proc.returncode)

    @require_root
    def _install_linters(self):  # Todo
        linters = self.descriptor["linters"]
        dist = get_dist()

        if dist not in linters or dist not in linters["requirements"]:
            raise OSError("Cannot install linters: Unknown linux "
                          "distribution '%s'" % dist)

        self.utils.install_packages(dist, *linters["requirements"][dist])

        if dist == "debian":
            self._debian_install_nodejs()

        self.utils.install_packages(dist, *linters[dist])
        self.utils.install_npm_packages(*linters["npm"])
        self.utils.install_pip_packages(*linters["pip"])

    @require_root
    def _debian_install_nodejs(self):
        src_url = "https://deb.nodesource.com/setup_9.x"
        install_location = Path("~/nodesource_setup.sh")

        self.utils.run(["curl", "-sL", src_url, "-o", str(install_location)])
        self.utils.run(["sh", str(install_location)])

        self.utils.install_packages("debian", "nodejs")
