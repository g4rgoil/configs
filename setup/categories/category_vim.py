#!/usr/bin/env python3

""" Script for setting up vim on this machine """

import shlex

from pathlib import Path

from categories.category import Category
from categories import require_repo_dir, require_root

__version__ = "1.0.0"


class CategoryVim(Category):
    directory = "vim"

    name = "vim"
    prog = "setup.py vim"
    usage = "setup.py [<global options>] vim [-h] " \
            "[--install [plugins] [linters]]"
    help = "set up files for the vim text editor"

    def __init__(self):
        super().__init__()
        self.src_dir = require_repo_dir(self.directory)
        self.dst_dir = Path.home()

        self.files = {
            "vimrc": ".vimrc", "gvimrc": ".gvimrc", "ideavimrc": ".ideavimrc"
        }
        self.directories = {"skeletons": ".vim/skeletons"}

        self.install_dict = {
            "vundle": self._install_plugin_manager,
            "plugins": self._install_plugins,
            "ycm": self._install_ycm,
            "linters": self._install_linters,
            "all": None
        }

        self.parser = None

    def add_subparser(self, subparsers):
        kwargs = dict(prog=self.prog, usage=self.usage, help=self.help)
        self.parser = subparsers.add_parser(self.name, **kwargs)

        kwargs = dict(action="version", version="setup.py vim " + __version__)
        self.parser.add_argument("--version", **kwargs)

        group = self.parser.add_argument_group("vim specific options")

        kwargs = dict(nargs="*", action="store", default=[], metavar="args",
                      choices=self.install_dict.keys())
        kwargs["help"] = "install all specified categories; valid categories" \
                         " are " + ", ".join(self.install_dict.keys())
        group .add_argument("--install", **kwargs)

    def set_up(self, namespace=None):
        super().set_up(namespace)

        if not namespace.install:
            pass
        elif "all" in namespace.install:
            self._install(
                [key for key in self.install_dict.keys() if key != "all"])
        else:
            self._install(namespace.install)

    def _install(self, keys):
        for key in keys:
            try:
                self.install_dict[key]()
            except PermissionError as e:
                self.utils.error("Install %s:" % key, str(e))

    def _install_plugin_manager(self):
        install_location = Path("~/.vim/bundle/Vundle.vim").expanduser()
        src_url = "https://github.com/VundleVim/Vundle.vim.git"

        self.utils.error("Installing Vundle to '%s'..."
                         % str(install_location))

        if install_location.exists():
            return self.utils.error("Vundle seems to already be installed")

        args = shlex.split("git clone -v") + [str(src_url),
                                              str(install_location)]
        proc = self.utils.run(args)

        if proc.returncode != 0:
            self.utils.error("Failed to install Vundle: Exited with code %s"
                             % proc.returncode)

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
        raise NotImplementedError()
