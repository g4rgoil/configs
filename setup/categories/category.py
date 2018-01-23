#!/usr/bin/env python3

import inspect
import shutil
import json
import shlex
import os as _os
import sys as _sys

from abc import ABC, abstractmethod
from pathlib import Path
from subprocess import run, CompletedProcess, DEVNULL
from typing import Tuple, List, Dict, Callable

from categories import require_repo_dir, require_root

__version__ = "1.1.0"


class Category(ABC):
    directory = ""

    def __init__(self):
        self.src_dir: Path = require_repo_dir(self.directory)
        self.dst_dir: Path = None

        path = Path(self.src_dir, "category.json")
        self.descriptor = self.parse_json_descriptor(path)

        self.name = self.descriptor["category"]["name"]

        self.files = self.parse_src_dst_dict(self.descriptor, "files")
        self.directories = self.parse_src_dst_dict(self.descriptor,
                                                   "directories")

        self.install_dict = {}

        self.parser = None
        self.utils = _SetupUtils()

    @abstractmethod
    def add_subparser(self, subparsers):
        descriptor = self.descriptor["category"]

        kwargs = dict(prog=descriptor["prog"], usage=descriptor["usage"],
                      help=descriptor["help"])
        self.parser = subparsers.add_parser(descriptor["name"], **kwargs)

    @abstractmethod
    def set_up(self, namespace=None):
        self.back_up()
        self.delete()
        self.link()

    @staticmethod
    def parse_json_descriptor(path):
        with open(path, "r", encoding="utf-8") as file:
            json_file = json.load(file)

        return json_file

    def parse_src_dst_dict(self, json_descriptor, name) -> Dict[Path, Path]:
        target_dict = dict()

        for item in json_descriptor[name]:
            src = Path(self.src_dir, item["src"]).expanduser()
            dst = Path(item["dst"]).expanduser()

            target_dict[src] = dst

        return target_dict

    def create_utils(self, namespace=None):
        self.utils = _SetupUtils(namespace)

    def link(self):
        self._link_files()
        self._link_directories()

    def back_up(self):
        self._backup_files()
        self._backup_directories()

    def delete(self):
        self._delete_files()
        self._delete_directories()

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

    def _get_methods_by_prefix(self, prefix) -> List[Tuple[str, Callable]]:
        return [m for m in inspect.getmembers(self, predicate=inspect.ismethod)
                if m[0].startswith(prefix)]

    def _link_files(self):
        for src, dst in self.files.items():
            self.utils.try_execute(lambda: self.utils.symlink(src, dst))

    def _link_directories(self):
        for src, dst in self.directories.items():
            self.utils.try_execute(lambda: self.utils.symlink(src, dst))

    def _backup_files(self):
        for dst_file in self.files.values():
            self.utils.try_execute(lambda: self.utils.backup_file(dst_file))

    def _backup_directories(self):
        for dst_dir in self.directories.values():
            self.utils.try_execute(lambda: self.utils.backup_file(dst_dir))

    def _delete_files(self):
        for dst_file in self.files.values():
            self.utils.try_execute(lambda: self.utils.delete_file(dst_file))

    def _delete_directories(self):
        for dst_dir in self.directories.values():
            self.utils.try_execute(lambda: self.utils.delete_file(dst_dir))


class _SetupUtils:
    def __init__(self, namespace=None):
        def get_value_or_default(dictionary, key, default):
            return dictionary[key] if key in dictionary else default

        args_dict = vars(namespace) if namespace is not None else {}

        self.link = get_value_or_default(args_dict, "link", True)

        self.dry_run = get_value_or_default(args_dict, "dry_run", False)

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

        if not self.dry_run:
            dst.symlink_to(src)

    def backup_file(self, src: Path) -> None:
        if not self.backup:
            return

        if not src.exists() and not src.is_symlink():
            raise FileNotFoundError("Cannot backup '%s': No such file exists"
                                    % str(src))

        dst = src.with_suffix(self.suffix)

        self.print_move(src, dst)

        if not self.dry_run:
            _os.rename(str(src), str(dst))

    def delete_file(self, file: Path) -> None:
        if not self.delete:
            return

        if not file.exists() and not file.is_symlink():
            raise FileNotFoundError("Cannot delete '%s': No such file exists"
                                    % str(file))

        self.print_delete(file)

        if not self.dry_run:
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
            raise OSError("Cannot install packages: Unknown linux "
                          "distribution '%s'" % dist)

        for package in packages:
            process = self.run(shlex.split(command % package))

            if process.returncode != 0:
                self.error("Failed to install package '%s': Exited with code "
                           "%s" % (package, process.returncode))

    def install_pip_packages(self, *packages):
        command = "pip install %s"

        for package in packages:
            process = self.run(shlex.split(command % package))

            if process.returncode != 0:
                self.error("Failed to install pip package '%s': Exited with "
                           "code %s" % (package, process.returncode))

    def install_npm_packages(self, *packages):
        command = "npm install -g %s"

        for package in packages:
            process = self.run(shlex.split(command % package))

            if process.returncode != 0:
                self.error("Failed to install npm package '%s': Exited with "
                           "code %s" % (package, process.returncode))

    def install_gem_packages(self, *packages):
        command = "gem install %s"

        for package in packages:
            process = self.run(shlex.split(command % package))

            if process.returncode != 0:
                self.error("Failed to install gem package '%s': Exited with "
                           "code %s" % (package, process.returncode))

    def print(self, *args, **kwargs):
        """ This method might be reassigned in the constructor """
        pass

    def error(self, *args, **kwargs):
        """ This method might be reassigned in the constructor """
        print("setup.py:", *args, file=_sys.stderr, **kwargs)

    def print_create_symlink(self, src, dst):
        self.print("Creating link: '%s' -> '%s'" % (str(dst), str(src)))

    def print_delete(self, file):
        self.print("deleting file: '%s'" % str(file))

    def print_move(self, src, dst):
        self.print("Moving file: '%s' -> '%s'" % (str(src), str(dst)))

    def debian_install_nodejs(self):
        src_url = "https://deb.nodesource.com/setup_9.x"
        install_location = Path("~/nodesource_setup.sh")

        self.run(["curl", "-sL", src_url, "-o", str(install_location)])
        self.run(["sh", str(install_location)])

        self.install_packages("debian", "nodejs")
