#!/usr/bin/env python3
# -*- coding: utf8 -*-

import inspect
import os, shutil

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Tuple, List, Callable


class Category(ABC):
    src_dir: Path = None    # Todo convert to instance variables?
    dst_dir: Path = None

    backup_suffix = ".old"

    def __init__(self):
        self.files = {}
        self.directories = {}

    @abstractmethod
    def add_subparser(self, subparsers):
        pass

    @abstractmethod
    def set_up(self):
        for method_tuple in self._get_method_by_prefix("_setup"):
            method_tuple[1]()

    @abstractmethod
    def back_up(self):
        for method_tuple in self._get_method_by_prefix("_backup"):
            method_tuple[1]()

    @abstractmethod
    def delete(self):
        for method_tuple in self._get_method_by_prefix("_delete"):
            method_tuple[1]()

    def _get_method_by_prefix(self, prefix) -> List[Tuple[str, Callable]]:
        return [m for m in inspect.getmembers(self, predicate=inspect.ismethod) if m[0].startswith(prefix)]

    def _get_src_file(self, file):
        return self.src_dir / file

    def _get_dst_file(self, file):
        return self.dst_dir / self.files[file]

    def _get_src_dir(self, directory):
        return self.src_dir / directory

    def _get_dst_dir(self, directory):
        return self.dst_dir / self.directories[directory]

    def _setup_files(self):
        for file in self.files:
            src_file, dst_file = self._get_src_file(file), self._get_dst_file(file)

            if dst_file.exists() or dst_file.is_symlink():
                raise FileExistsError()     # Todo error message

            dst_file.symlink_to(src_file)

    def _setup_directories(self):
        for directory in self.directories:
            src_dir, dst_dir = self._get_src_dir(directory), self._get_dst_dir(directory)

            if dst_dir.exists() or dst_dir.is_symlink():
                raise FileExistsError()     # Todo error message

            dst_dir.symlink_to(src_dir)

    def _backup_files(self):        # Todo handle existing links
        for file in self.files:
            dst_file = self._get_dst_file(file)
            dst_file_bak = dst_file.with_suffix(self.backup_suffix)

            if dst_file.is_file():
                os.rename(dst_file, dst_file_bak)
            else:
                raise ValueError()  # Todo different error

    def _backup_directories(self):
        for directory in self.directories:
            dst_dir = self.dst_dir / self.directories[directory]
            dst_dir_bak = dst_dir.with_suffix(self.backup_suffix)

            if dst_dir.is_file():
                os.rename(dst_dir, dst_dir_bak)
            else:
                raise ValueError()  # Todo different error

    def _delete_files(self):
        for file in self.files:
            dst_file = self.dst_dir / self.files[file]

            if dst_file.is_file() or dst_file.is_symlink():
                dst_file.unlink()
            elif dst_file.is_dir():
                raise ValueError()  # Todo different error

    def _delete_directories(self):
        for directory in self.directories:
            dst_dir = self.dst_dir / self.directories[directory]

            if dst_dir.is_dir():
                dst_dir.unlink() if dst_dir.is_symlink() else shutil.rmtree(dst_dir)    # Todo, simplify?
            else:
                raise ValueError()  # Todo different error
