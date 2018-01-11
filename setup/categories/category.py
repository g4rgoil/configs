#!/usr/bin/env python3
# -*- coding: utf8 -*-

import inspect
import shutil
import os as _os
import sys as _sys

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Tuple, List, Callable

from categories import __repo_dir__


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
        self.utils = _SetupUtils(namespace)
        # print(namespace)  # Todo get your shit together dude :D

    @abstractmethod
    def link(self):
        for method_tuple in self._get_methods_by_prefix("_link"):
            method_tuple[1]()

    @abstractmethod
    def back_up(self):
        for method_tuple in self._get_methods_by_prefix("_backup"):
            method_tuple[1]()

    @abstractmethod
    def delete(self):
        for method_tuple in self._get_methods_by_prefix("_delete"):
            method_tuple[1]()

    @staticmethod
    def _require_repo_dir(name) -> Path:
        repo_dir = __repo_dir__ / name

        if not repo_dir.is_dir():
            raise NotADirectoryError()  # Todo error message

        return repo_dir

    def _get_methods_by_prefix(self, prefix) -> List[Tuple[str, Callable]]:
        return [m for m in inspect.getmembers(self, predicate=inspect.ismethod) if m[0].startswith(prefix)]

    def _get_src_file(self, file):
        return self.src_dir / file

    def _get_dst_file(self, file):
        return self.dst_dir / self.files[file]

    def _get_src_dir(self, directory):
        return self.src_dir / directory

    def _get_dst_dir(self, directory):
        return self.dst_dir / self.directories[directory]

    def _link_files(self):
        for file in self.files:
            src_file, dst_file = self._get_src_file(file), self._get_dst_file(file)

            try:
                self.utils.symlink(src_file, dst_file)
            except OSError as e:
                self.utils.print_error(str(e))  # Todo

    def _link_directories(self):
        for directory in self.directories:
            src_dir, dst_dir = self._get_src_dir(directory), self._get_dst_dir(directory)

            try:
                self.utils.symlink(src_dir, dst_dir)
            except OSError as e:
                self.utils.print_error(str(e))  # Todo

    def _backup_files(self):
        for file in self.files.values():
            dst_file = self._get_dst_file(file)

            try:
                self.utils.backup(dst_file)
            except OSError as e:
                self.utils.print_error(str(e))

    def _backup_directories(self):
        for directory in self.directories.values():
            dst_dir = self._get_dst_dir(directory)

            try:
                self.utils.backup(dst_dir)
            except OSError as e:
                self.utils.print_error(str(e))

    def _delete_files(self):
        for file in self.files:
            dst_file = self.dst_dir / self.files[file]

            try:
                self.utils.delete(dst_file)
            except OSError as e:
                self.utils.print_error(str(e))

    def _delete_directories(self):
        for directory in self.directories:
            dst_dir = self.dst_dir / self.directories[directory]

            try:
                self.utils.delete(dst_dir)
            except OSError as e:
                self.utils.print_error(str(e))


class _SetupUtils:
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

        if self.verbose:
            self.print = print

        self.suffix = "." + get_value_or_default(args_dict, "suffix", "old").lstrip(".")

    def symlink(self, src: Path, dst: Path):
        if not src.exists() and not src.is_symlink():
            raise FileNotFoundError("cannot link to '%s': No such file exists" % str(src))

        if not self.keep and (dst.exists() or dst.is_symlink()):
            raise FileExistsError("cannot create link '%s': File exists" % str(dst))

        self.print_create_symlink(src, dst)

        if self.link:
            dst.symlink_to(src)

    def backup(self, src: Path):
        if not self.backup:
            return

        if not src.exists() and not src.is_symlink():
            raise FileNotFoundError("cannot backup '%s': No such file exists" % str(src))

        dst = src.with_suffix(self.suffix)

        self.print_move(src, dst)
        _os.rename(str(src), str(dst))

    def delete(self, file: Path):
        if not self.delete:
            return

        if not file.exists() and not file.is_symlink():
            raise FileNotFoundError("cannot delete '%s': No such file exists" % str(file))

        self.print_delete(file)

        if file.is_file() or file.is_symlink():
            file.unlink()
        elif file.is_dir():
            shutil.rmtree(str(file))

    def print(self, *args, **kwargs):
        """ The implementation of this method is assigned in the constructor """
        pass

    def print_error(self, *args, **kwargs):  # Todo
        self.print("setup.py:", *args, file=_sys.stderr, **kwargs)

    def print_create_symlink(self, src, dst):
        self.print("creating link: '%s' -> '%s'" % (str(dst), str(src)))

    def print_delete(self, file):
        self.print("deleting file: '%s'" % str(file))

    def print_move(self, src, dst):
        self.print("moving file: '%s' -> '%s'" % (str(src), str(dst)))

