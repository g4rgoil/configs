#!/usr/bin/env python3
# -*- coding: utf8 -*-

""" Script for setting up files for the Z shell on this machine. """

import shlex

from pathlib import Path

from categories.category import Category
from categories import require_repo_dir

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

        self.parser = None

    def add_subparser(self, subparsers):
        self.parser = subparsers.add_parser(self.name, prog=self.prog, help=self.help,
                                            usage=self.usage)

    def set_up(self, namespace=None):
        super().set_up(namespace)

    def _install_oh_my_zsh(self):
        install_location = Path("~/.oh-my-zsh").expanduser()
        src_url = "git://github.com/robbyrussell/oh-my-zsh.git"

        self.utils.error("Installing oh-my-zsh to '%s'..." % str(install_location))

        if install_location.exists():
            self.utils.error("oh-my-zsh seems to already be installed")
            return

        args = shlex.split("git clone -v") + [str(src_url), str(install_location)]
        proc = self.utils.run(args)

        if proc.returncode != 0:
            self.utils.error("Failed to install oh-my-zsh: Exited with code %s" %
                             proc.returncode)

    def _install_powerlevel9k(self):
        install_location = Path("~/.oh-my-zsh/custom/themes.powerlevel9k").expanduser()
        src_url = "https://github.com/bhilburn/powerlevel9k.git"

        self.utils.error("Installing Powerlevel9k to '%s'..." % str(install_location))
        install_location.parent.mkdir()

        if install_location.exists():
            self.utils.error("Powerlevel9k seems to already be installed")
            return

        args = shlex.split("git clone -v") + [str(src_url), str(install_location)]
        proc = self.utils.run(args)

        if proc.returncode != 0:
            self.utils.error("Failed to install Powerlevel9k: Exited with code %s" %
                             proc.returncode)

    def _install_syntax_highlighting(self):
        install_location = Path("~/.oh-my-zsh/custom}/plugins/zsh-syntax-highlighting").expanduser()
        src_url = "https://github.com/zsh-users/zsh-syntax-highlighting.git"

        self.utils.error("Installing zsh-syntax-highlighting to '%s'..." %
                         str(install_location.str))
        install_location.parent.mkdir()

        if install_location.exists():
            self.utils.error("zsh-syntax-highlighting seems to already bee installed")
            return

        args = shlex.split("git clone -v ") + [str(src_url), str(install_location)]
        proc = self.utils.run(args)

        if proc.returncode != 0:
            self.utils.error("Failed to install zsh-syntax-highlighting: Exited with code %s" %
                             proc.returncode)
