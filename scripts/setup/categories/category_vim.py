#!/usr/bin/env python3

from pathlib import Path
from shlex import split

from category import Category
from utils import require_root, get_dist

__version__ = "2.0.0"


class CategoryVim(Category):
    """ Functionality for setting up the vim text editor on this machine """

    directory = "vim"

    def __init__(self):
        super().__init__()

    def set_up(self, namespace=None) -> None:
        super().set_up(namespace)

    def _install_plugin_manager(self) -> None:
        install_location = Path("~/.vim/bundle/Vundle.vim").expanduser()
        src_url = "https://github.com/VundleVim/Vundle.vim.git"

        self.utils.clone_repo(src_url, install_location, name="Vundle")

    def _install_plugins(self) -> None:
        self.utils.error("Installing plugins with Vundle...")

        args = split("nvim -c PluginInstall -c PluginUpdate "
                     "-c PluginClean -c quitall")

        self.utils.verbose = True
        proc = self.utils.run(args)
        self.utils.verbose = False

        if proc.returncode != 0:
            self.utils.error("Failed to install plugins: Exited with code %s"
                    % proc.returncode, prefix="error:")

    def _install_completion(self) -> None:
        self.utils.error("Installing YouCompleteMe...")

        ycm_installer = Path("~/.vim/bundle/YouCompleteMe/"
                             "install.py").expanduser()
        option_string = "--clang-completer"

        args = ["python", ycm_installer, option_string]
        proc = self.utils.run(args)

        if proc.returncode != 0:
            self.utils.error("Failed to install YouCompleteMe: "
                    "Exited with code %s" % proc.returncode, prefix="error:")

    @require_root
    def _install_linters(self) -> None:
        linters = self.descriptor["linters"]
        dist = get_dist()

        if dist not in linters or dist not in linters["requirements"]:
            raise OSError("Cannot install linters: Unknown linux "
                          "distribution '%s'" % dist)

        self.utils.install_packages(dist, *linters["requirements"][dist])

        if dist == "debian":
            self.utils.debian_install_nodejs()

        self.utils.install_packages(dist, *linters[dist])
        self.utils.install_npm_packages(*linters["npm"])
        self.utils.install_pip_packages(*linters["pip"])
        self.utils.install_gem_packages(*linters["gem"])
