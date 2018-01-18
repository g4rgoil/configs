#!/usr/bin/env python3

import inspect
import shutil
import os as _os
import sys as _sys

from abc import ABC, abstractmethod
from pathlib import Path
from subprocess import run, CompletedProcess, DEVNULL
from typing import Tuple, List, Callable

__version__ = "1.1.0"


class Category(ABC):
    name = ""

    def __init__(self):
        self.src_dir: Path = None
        self.dst_dir: Path = None

        self.files = {}
        self.directories = {}

        self.parser = None
        self.utils = _SetupUtils()

    @abstractmethod
    def add_subparser(self, subparsers):
        pass

    @abstractmethod
    def set_up(self, namespace=None):
        self.back_up()
        self.delete()
        self.link()

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

    def _get_methods_by_prefix(self, prefix) -> List[Tuple[str, Callable]]:
        return [m for m in inspect.getmembers(self, predicate=inspect.ismethod)
                if m[0].startswith(prefix)]

    def _get_src_file(self, file):
        return self.src_dir / file

    def _get_dst_file(self, file):
        return self.dst_dir / file

    def _link_files(self):
        for src, dst in self.files.items():
            src_file = self._get_src_file(src)
            dst_file = self._get_dst_file(dst)

            try:
                self.utils.symlink(src_file, dst_file)
            except OSError as e:
                self.utils.error(str(e))

    def _link_directories(self):
        for src, dst in self.directories.items():
            src_dir = self._get_src_file(src)
            dst_dir = self._get_dst_file(dst)

            try:
                self.utils.symlink(src_dir, dst_dir)
            except OSError as e:
                self.utils.error(str(e))

    def _backup_files(self):
        for file in self.files.values():
            dst_file = self._get_dst_file(file)

            try:
                self.utils.backup_file(dst_file)
            except OSError as e:
                self.utils.error(str(e))

    def _backup_directories(self):
        for directory in self.directories.values():
            dst_dir = self._get_dst_file(directory)

            try:
                self.utils.backup_file(dst_dir)
            except OSError as e:
                self.utils.error(str(e))

    def _delete_files(self):
        for file in self.files.values():
            dst_file = self._get_dst_file(file)

            try:
                self.utils.delete_file(dst_file)
            except OSError as e:
                self.utils.error(str(e))

    def _delete_directories(self):
        for directory in self.directories.values():
            dst_dir = self._get_dst_file(directory)

            try:
                self.utils.delete_file(dst_dir)
            except OSError as e:
                self.utils.error(str(e))


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
