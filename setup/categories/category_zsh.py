#!/usr/bin/env python3

from pathlib import Path

from category import Category

__version__ = "2.0.0"


class CategoryZsh(Category):
    """ Functionality for setting up the Z shell on this machine """

    directory = "zsh"

    def __init__(self):
        super().__init__()

    def set_up(self, namespace=None) -> None:
        super().set_up(namespace)

    def _install_oh_my_zsh(self) -> None:
        install_location = Path("~/.oh-my-zsh")
        src_url = "git://github.com/robbyrussell/oh-my-zsh.git"

        self.utils.clone_repo(src_url, install_location, name="oh-my-zsh")

    def _install_powerlevel9k(self) -> None:
        install_location = Path("~/.oh-my-zsh/custom/themes/powerlevel9k")
        src_url = "https://github.com/bhilburn/powerlevel9k.git"

        self.utils.clone_repo(src_url, install_location, name="Powerlevel9k")

    def _install_syntax_highlighting(self) -> None:
        install_location = Path("~/.oh-my-zsh/custom/plugins/"
                                "zsh-syntax-highlighting")
        src_url = "https://github.com/zsh-users/zsh-syntax-highlighting.git"

        self.utils.clone_repo(src_url, install_location,
                              name="zsh-syntax-highlighting")
