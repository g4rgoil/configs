#!/usr/bin/env python3

""" Script for setting up files for the Z shell on this machine. """

import shlex

from pathlib import Path

from categories.category import Category
from categories import require_repo_dir, require_root

__version__ = "0.0.1"


class CategoryZsh(Category):
    directory = "zsh"

    name = "zsh"
    prog = "setup.py zsh"
    usage = "setup.py [<global options>] zsh [-h]"
    help = "set up files for the Z shell"

    def __init__(self):
        super().__init__()
        self.src_dir = require_repo_dir(self.directory)
        self.dst_dir = Path.home()

        self.files = {"zshrc": ".zshrc", "zsh-aliases": ".zsh-aliases"}
        self.directories = {}

        self._install_dict = {
            "oh-my-zsh": self._install_oh_my_zsh,
            "powerline": self._install_powerlevel9k,
            "syntax": self._install_syntax_highlighting,
            "font": self._install_font,
            "all": None
        }

        self.parser = None

    def add_subparser(self, subparsers):
        kwargs = dict(prog=self.prog, usage=self.usage, help=self.help)
        self.parser = subparsers.add_parser(self.name, **kwargs)

        kwargs = dict(action="version", version=__version__)
        self.parser.add_argument("--version", **kwargs)

        group = self.parser.add_argument_group("zsh specific options")

        kwargs = dict(nargs="*", action="store", default=[], metavar="args",
                      choices=self._install_dict.keys())
        kwargs["help"] = "install all specified categories; valid categories " \
                         "are " + ", ".join(kwargs["choices"])
        group.add_argument("--install", **kwargs)

    def set_up(self, namespace=None):
        super().set_up(namespace)

    def _install_oh_my_zsh(self):
        install_location = Path("~/.oh-my-zsh")
        src_url = "git://github.com/robbyrussell/oh-my-zsh.git"

        self.utils.clone_repo(src_url, install_location, name="oh-my-zsh")

    def _install_powerlevel9k(self):
        install_location = Path("~/.oh-my-zsh/custom/themes/powerlevel9k")
        src_url = "https://github.com/bhilburn/powerlevel9k.git"

        self.utils.clone_repo(src_url, install_location, name="Powerlevel9k")

    def _install_syntax_highlighting(self):
        install_location = Path("~/.oh-my-zsh/custom/plugins/"
                                "zsh-syntax-highlighting")
        src_url = "https://github.com/zsh-users/zsh-syntax-highlighting.git"

        self.utils.clone_repo(src_url, install_location,
                              name="zsh-syntax-highlighting")

    @require_root
    def _install_font(self):
        pass
