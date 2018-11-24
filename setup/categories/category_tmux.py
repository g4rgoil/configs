#!/usr/bin/env python3

from pathlib import Path

from category import Category

__version__ = "1.0.0"


class CategoryTmux(Category):
    """ Functionality for setting up files and plugins for tmux """

    directory = "tmux"

    def __init__(self):
        super().__init__()

        self.install_dict = {
            "tpm": self._install_plugin_manager,
            "powerline": self._install_powerline,
            "all": None
        }

    def add_subparser(self, subparsers) -> None:
        super().add_subparser(subparsers)

        group = self.parser.add_argument_group("tmux specific options")

        choices = self.install_dict.keys()
        help = "install all specified categories; valid categories are " \
               + ", ".join(choices)
        self.parser.add_install_action(group=group, choices=choices, help=help)

    def set_up(self, namespace=None) -> None:
        super().set_up(namespace)

        if namespace.install:
            self.install(namespace.install)

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
