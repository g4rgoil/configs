#!/usr/bin/env python3

from pathlib import Path

from category import Category

__version__ = "1.0.0"


class CategoryZsh(Category):
    """ Functionality for setting up the Z shell on this machine """

    directory = "zsh"

    def __init__(self):
        super().__init__()

        self.install_dict = {
            "oh-my-zsh": self._install_oh_my_zsh,
            "powerline": self._install_powerlevel9k,
            "fish": self._install_syntax_highlighting,
            "all": None
        }

    def add_subparser(self, subparsers):
        super().add_subparser(subparsers)

        group = self.parser.add_argument_group("zsh specific options")

        choices = self.install_dict.keys()
        help = "install the specified categories; valid categories are " \
               + ", ".join(choices)
        self.parser.add_install_action(group=group, choices=choices, help=help)

    def set_up(self, namespace=None):
        super().set_up(namespace)

        if namespace.install:
            self.install(namespace.install)

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
