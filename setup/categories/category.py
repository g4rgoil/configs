#!/usr/bin/env python3
# -*- coding: utf8 -*-

import inspect

from abc import ABC, abstractmethod
from pathlib import Path


class Category(ABC):
    src_dir: Path = None
    dst_dir: Path = None

    def __init__(self):
        self.files = {}
        self.directories = {}

    @abstractmethod
    def add_subparser(self, subparsers):
        pass

    def get_method_by_prefix(self, prefix):
        return [m for m in inspect.getmembers(self, predicate=inspect.ismethod) if m[0].startswith(prefix)]

    @abstractmethod
    def set_up(self):
        for method_tuple in self.get_method_by_prefix("_setup"):
            method_tuple[1]()

    @abstractmethod
    def back_up(self):
        for method_tuple in self.get_method_by_prefix("_backup"):
            method_tuple[1]()

    @abstractmethod
    def delete(self):
        for method_tuple in self.get_method_by_prefix("_delete"):
            method_tuple[1]()

    def _setup_files(self):
        for file in self.files:
            src_file: Path = self.src_dir / file
            dst_file: Path = self.dst_dir / self.files[file]

            dst_file.symlink_to(src_file)

    def _setup_directories(self):
        for directory in self.directories:
            src_dir: Path = self.src_dir / directory
            dst_dir: Path = self.dst_dir / self.directories[directory]

            dst_dir.symlink_to(src_dir)

    def _backup_files(self):
        for file in self.files:
            dst_file = self.dst_dir / self.files[file]

            if dst_file.is_file():
                dst_file.unlink()
            elif  dst_file.is_symlink():    # Handle broken symlinks
                dst_file.unlink()
            elif dst_file.is_dir():
                pass    # Todo handle, exception?

    def _backup_directories(self):
        for directory in self.directories:
            dst_dir = self.dst_dir / self.directories[directory]

            if dst_dir.is_dir():
                pass    # Todo

    def _delete_files(self):
        pass

    def _delete_directories(self):
        pass
