#!/usr/bin/env python3

""" This module provides classes for setting up this system """

import json
import shlex
import shutil
import os
import re
import sys

from argparse import ArgumentParser, HelpFormatter, ZERO_OR_MORE
from pathlib import Path
from subprocess import CompletedProcess, DEVNULL, run
from typing import List

__version__ = "1.1.0"

__repo_dir__ = Path(__file__).parents[1]


def require_repo_dir(name) -> Path:
    repo_dir = __repo_dir__ / name

    if not repo_dir.is_dir():
        raise NotADirectoryError("Cannot find directory '%s' in repository"
                                 % name)

    return repo_dir


def is_root() -> bool:
    return os.getuid() == 0


def require_root(func):
    """ Function decorator for functions that require root privileges. """

    def new_function(*args, **kwargs):
        if not is_root():
            raise PermissionError("Cannot perform this operation: "
                                  "Missing root privileges")
        return func(*args, **kwargs)

    return new_function


def get_dist():
    """ Returns the name of the linux distribution on this system or None """
    with open("/etc/os-release", "r") as file:
        for line in file.read().splitlines():
            if re.match("^ID=", line):
                return line.lstrip("ID=")

    return None


def parse_json_descriptor(path):
    """ Parses the specified json file and returns it as dict """
    with open(path, "r", encoding="utf-8") as file:
        json_file = json.load(file)

    return json_file


class CategoryCollection(object):
    def __init__(self):
        instances = [c() for c in Category.__subclasses__()]
        self.dict = dict([(i.name, i) for i in instances])

    def __contains__(self, item):
        return item in self.dict

    def __delitem__(self, key):
        del self.dict[key]

    def __getitem__(self, item):
        return self.dict[item]

    def __iter__(self):
        for category in self.dict.values():
            yield category


class Category(object):
    directory = None

    def __init__(self, descriptor_path: Path = None):
        self.name = None
        self.src_dir = None
        self.descriptor = None

        self.files = list()
        self.directories = list()
        self.install_dict = dict()

        self.parser = None
        self.utils = SetupUtils()

        if self.directory is not None:
            self.src_dir: Path = require_repo_dir(self.directory)

        if descriptor_path is not None:
            self.descriptor = parse_json_descriptor(descriptor_path)
        elif self.src_dir is not None:
            path = Path(self.src_dir, "category.json")
            self.descriptor = parse_json_descriptor(path)

        if self.descriptor is not None:
            self.name = self.descriptor["category"]["name"]

            self.files = self.parse_file_mapping_list(self.descriptor["files"])
            self.directories = self.parse_file_mapping_list(
                self.descriptor["directories"])

    def set_up(self, namespace=None):
        self.back_up()
        self.delete()
        self.link()

    def add_subparser(self, subparsers):
        if self.descriptor is None:
            raise ValueError("The descriptor dictionary has not been set")

        descriptor = self.descriptor["category"]
        # kwargs = dict(prog=descriptor["prog"], usage=descriptor["usage"],
        #               help=descriptor["help"], version=descriptor["version"])
        self.parser = subparsers.add_parser(self.name, **descriptor["parser"])

    def parse_file_mapping_list(self, dictionary_list):
        return [self.parse_file_mapping(d) for d in dictionary_list]

    def parse_file_mapping(self, dictionary):
        dictionary["src"] = Path(self.src_dir, dictionary["src"]).expanduser()
        dictionary["dst"] = Path(dictionary["dst"]).expanduser()

        try:
            mapping = FileMapping(**dictionary)
        except ValueError as e:
            self.utils.error("Failed to parse mapping %s: %s"
                             % (dictionary, str(e)))
            raise e

        return mapping

    def create_utils(self, namespace=None):
        self.utils = SetupUtils(namespace)

    def link(self):
        for mapping in self.files + self.directories:
            self.utils.try_execute(lambda: mapping.link(self.utils))

    def back_up(self):
        for mapping in self.files + self.directories:
            self.utils.try_execute(lambda: mapping.backup_dst(self.utils))

    def delete(self):
        for mapping in self.files + self.directories:
            self.utils.try_execute(lambda: mapping.delete_dst(self.utils))

    def install(self, keys):
        if "all" in keys:
            keys = [k for k in self.install_dict.keys() if k != "all"]

        for key in self.install_dict.keys():
            if key not in keys:
                continue

            try:
                self.install_dict[key]()
            except PermissionError as e:
                self.utils.error("Install %s:" % key, str(e))


class CategoryAll(Category):
    """ Functionality for setting up all other categories on this machine """

    directory = None

    def __init__(self):
        path = Path(__repo_dir__, "setup", "resources", "category_all.json")
        super().__init__(path)

    def set_up(self, namespace=None):
        for category in [c for c in CategoryCollection() if
                         c.name != self.name]:
            category.create_utils(namespace)
            category.set_up(namespace)

    def add_subparser(self, subparsers):
        super().add_subparser(subparsers)

        group = self.parser.add_argument_group("all specific options")

        help = "values to pass to the install action of each category; for " \
               "available values consult the help message for each category"
        self.parser.add_install_action(group=group, help=help)


class CategoryBackups(Category):
    """ Functionality for setting up backup_scripts on this system """

    directory = "backup_scripts"


class CategoryBash(Category):
    """ Functionality for setting up the bourne again shell on this system """

    directory = "bash"

    def __init__(self):
        super().__init__()

    def set_up(self, namespace=None):
        super().set_up(namespace)


class CategoryMisc(Category):
    """ Functionality for setting up misceleanus things on this machine """

    directory = "misc"

    def __init__(self):
        super().__init__()

    def set_up(self, namespace=None):
        super().set_up(namespace)


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

    def add_subparser(self, subparsers):
        super().add_subparser(subparsers)

        group = self.parser.add_argument_group("tmux specific options")

        choices = self.install_dict.keys()
        help = "install all specified categories; valid categories are " \
               + ", ".join(choices)
        self.parser.add_install_action(group=group, choices=choices, help=help)

    def set_up(self, namespace=None):
        super().set_up(namespace)

        if namespace.install:
            self.install(namespace.install)

    def _install_plugin_manager(self):
        install_location = Path("~/.tmux/plugins/tpm").expanduser()
        src_url = "https://github.com/tmux-plugins/tpm"

        self.utils.clone_repo(src_url, install_location,
                              name="Tmux Plugin Manger")

    def _install_powerline(self):
        install_location = Path("~/.tmux/powerline").expanduser()
        src_url = "https://github.com/erikw/tmux-powerline"

        self.utils.clone_repo(src_url, install_location,
                              name="Tmux Powerline")


class CategoryVim(Category):
    """ Functionality for setting up the vim text editor on this machine """

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

        group = self.parser.add_argument_group("vim specific options")

        choices = self.install_dict.keys()
        help = "install all specified categories; valid categories are " \
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
    def _install_linters(self):
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


class SetupUtils(object):
    def __init__(self, namespace=None):
        def get_value_or_default(dictionary, key, default):
            return dictionary[key] if key in dictionary else default

        args_dict = vars(namespace) if namespace is not None else {}

        self.link = get_value_or_default(args_dict, "link", True)

        dst_handling = get_value_or_default(args_dict, "dst_handling", "keep")
        self.keep = (dst_handling == "keep")
        self.backup = (dst_handling == "backup")
        self.delete = (dst_handling == "delete")

        self.verbose = get_value_or_default(args_dict, "verbose", False)
        self.quiet = get_value_or_default(args_dict, "quiet", False)

        if self.verbose:
            self.print = print

        if self.quiet:
            self.error = lambda *a, **kw: None

        self.suffix = "." + get_value_or_default(args_dict, "suffix",
                                                 ["old"])[0].lstrip(".")

    def symlink(self, src: Path, dst: Path) -> None:
        """ Create a symlink called dst pointing to src. """
        if not self.link:
            return

        if dst.exists() or dst.is_symlink():
            if not self.keep:
                raise FileExistsError("Cannot create link '%s': File exists"
                                      % str(dst))
            else:
                return

        if not src.exists() and not src.is_symlink():
            raise FileNotFoundError("Cannot link to '%s': No such file exists"
                                    % str(src))

        self.print_create_symlink(dst, src)
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.symlink_to(src)

    def backup_file(self, src: Path) -> None:
        if not self.backup:
            return

        if not src.exists() and not src.is_symlink():
            return

        dst = src.with_suffix(self.suffix)
        self.print_move(src, dst)
        os.rename(str(src), str(dst))

    def delete_file(self, file: Path) -> None:
        if not self.delete:
            return

        if not file.exists() and not file.is_symlink():
            return

        self.print_delete(file)

        if file.is_file() or file.is_symlink():
            file.unlink()
        elif file.is_dir():
            shutil.rmtree(str(file))

    def run(self, args: List[str]) -> CompletedProcess:
        kwargs = dict(stdout=None if self.verbose else DEVNULL,
                      stderr=DEVNULL if self.quiet else None, check=False)

        return run(args, **kwargs)

    def clone_repo(self, url: str, path: Path, name=None):
        if name is None:
            name = path.name

        path = path.expanduser()

        self.error("Installing %s to '%s'..." % (name, str(path)))

        if path.exists():
            return self.error("%s seems to already be installed" % name)

        path.mkdir(parents=True)

        args = ["git", "clone", "-v", str(url), str(path)]
        process = self.run(args)

        if process.returncode != 0:
            self.error("Failed to install %s: Exited with code %s"
                       % (name, process.returncode))

    def try_execute(self, func):
        try:
            func()
        except (OSError, PermissionError) as e:
            self.error(str(e))

    def install_packages(self, dist, *packages):
        if dist == "arch":
            command = "pacman -S --noconfirm %s"
        elif dist == "debian":
            command = "apt --assume-yes install %s"
        else:
            raise OSError("Cannot install packages: Unknown or unsupported "
                          "linux distribution '%s'" % dist)

        self._install_packages(command, *packages)

    def install_pip_packages(self, *packages):
        self._install_packages("pip install %s", *packages)

    def install_npm_packages(self, *packages):
        self._install_packages("npm install -g %s", *packages)

    def install_gem_packages(self, *packages):
        self._install_packages("gem install %s --no-user-install", *packages)

    def _install_packages(self, command, *packages):
        process = self.run(shlex.split(command % " ".join(packages)))

        if process.returncode != 0:
            self.error("Failed to install packages '%s': Exited with "
                       "code %s" % (", ".join(packages), process.returncode))

    def print(self, *args, **kwargs):
        """ This method might be reassigned in the constructor """
        pass

    def error(self, *args, **kwargs):
        """ This method might be reassigned in the constructor """
        print("setup.py:", *args, file=sys.stderr, **kwargs)

    def print_create_symlink(self, src, dst):
        self.print("Creating link: '%s' -> '%s'" % (str(dst), str(src)))

    def print_delete(self, file):
        self.print("Deleting file: '%s'" % str(file))

    def print_move(self, src, dst):
        self.print("Moving file: '%s' -> '%s'" % (str(src), str(dst)))

    def debian_install_nodejs(self):
        src_url = "https://deb.nodesource.com/setup_9.x"
        install_location = Path("~/nodesource_setup.sh")

        self.run(["curl", "-sL", src_url, "-o", str(install_location)])
        self.run(["sh", str(install_location)])

        self.install_packages("debian", "nodejs")


class FileMapping(object):
    """
    Represents a mapping between a file in this repository and a file
    on this system.
    """

    utils = SetupUtils()

    def __init__(self, src: Path, dst: Path, root=False, distribution=None):
        """
        :param src: the absolute path to the file in the repository
        :param dst: the absolute path to the file on the system
        :param root: whether root privileges are required for the file
        :param distribution: the (list of) linux distribution(s) the
                             file is used on
        """
        self.src = src
        self.dst = dst
        self.root = root
        self.distributions = list()

        if type(distribution) is str:
            self.distributions.append(distribution)
        elif type(distribution) is list:
            self.distributions.extend(distribution)
        elif distribution is not None:
            raise ValueError("Distribution must be either string or list")

    def __repr__(self):
        return "FileMapping(src='%s', dst='%s')" % (self.src, self.dst)

    @classmethod
    def require_utils(cls, utils: SetupUtils) -> SetupUtils:
        return utils if utils is not None else cls.utils

    def is_privileged(self) -> bool:
        return is_root() >= self.root

    def is_distribution(self) -> bool:
        return get_dist() in self.distributions or not self.distributions

    def can_setup(self):
        return self.is_privileged() and self.is_distribution()

    def link(self, utils=None):
        if self.can_setup():
            self.require_utils(utils).symlink(self.src, self.dst)

    def delete_dst(self, utils=None):
        if self.can_setup():
            self.require_utils(utils).delete_file(self.dst)

    def backup_dst(self, utils=None):
        if self.can_setup():
            self.require_utils(utils).backup_file(self.dst)


class CategorySubParser(ArgumentParser):
    def __init__(self, version=None, **kwargs):
        super().__init__(**kwargs, formatter_class=MyHelpFormatter)

        self.version = version
        self.add_version_action()

    def add_version_action(self, version=None):
        if version is None:
            version = self.version

        kwargs = dict(action="version", version=self.prog + " " + version)
        self.add_argument("--version", **kwargs)

    def add_install_action(self, group=None, choices=None, help=None):
        group = self if group is None else group

        kwargs = dict(nargs="*", action="store", default=[], metavar="args",
                      choices=choices, help=help)
        group.add_argument("--install", **kwargs)


class MyHelpFormatter(HelpFormatter):
    def _format_args(self, action, default_metavar):
        get_metavar = self._metavar_formatter(action, default_metavar)

        if action.nargs == ZERO_OR_MORE:
            result = '[%s ...]' % get_metavar(1)
        else:
            result = super()._format_args(action, default_metavar)

        return result
