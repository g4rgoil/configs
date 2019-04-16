#!/usr/bin/env python3

from pathlib import Path

from category import Category

__version__ = "2.0.0"


class CategoryTmux(Category):
    """ Functionality for setting up files and plugins for tmux """

    directory = "tmux"

    def __init__(self):
        super().__init__()

    def set_up(self, namespace=None) -> None:
        super().set_up(namespace)

    def _install_plugin_manager(self) -> None:
        install_location = Path("~/.tmux/plugins/tpm").expanduser()
        src_url = "https://github.com/tmux-plugins/tpm"

        self.utils.clone_repo(src_url, install_location,
                              name="Tmux Plugin Manger")

    def _install_powerline(self) -> None:
        install_location = Path("~/.tmux/powerline").expanduser()
        src_url = "https://github.com/erikw/tmux-powerline"

        self.utils.clone_repo(src_url, install_location,
                              name="Tmux Powerline")
