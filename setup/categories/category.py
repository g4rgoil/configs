#!/usr/bin/env python3
# -*- coding: utf8 -*-

import inspect
import os
import shutil

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Tuple, List, Callable

from categories import __repo_dir__


class Category(ABC):
    backup_suffix = ".old"

    name = ""

    def __init__(self):
        self.src_dir: Path = None
        self.dst_dir: Path = None

        self.files = {}
        self.directories = {}

        self.parser = None

    @abstractmethod
    def add_subparser(self, subparsers):
        pass

    @abstractmethod
    def set_up(self, namespace):
        if namespace.backup:
            self.back_up()
        elif namespace.delete:
            self.delete()
        else:
            self.keep()     # keep

        if namespace.no_link:
            pass
        else:
            pass    # Todo if link is true or false

        print(namespace)  # Todo

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

    @abstractmethod
    def keep(self):
        for method_tuple in self._get_methods_by_prefix("_keep"):
            method_tuple[1]()

    @staticmethod
    def _require_repo_dir(name) -> Path:
        repo_dir = __repo_dir__ / name

        if not repo_dir.is_dir():
            raise NotADirectoryError()  # Todo error message

        return repo_dir

    @staticmethod
    def _symlink(src: Path, dst: Path, is_dir=False):
        dst.symlink_to(src, is_dir)

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

            if not src_file.is_file():
                raise FileNotFoundError()  # Todo

            if dst_file.exists() or dst_file.is_symlink():
                raise FileExistsError()  # Todo error message

            dst_file.symlink_to(src_file)

    def _link_directories(self):
        for directory in self.directories:
            src_dir, dst_dir = self._get_src_dir(directory), self._get_dst_dir(directory)

            if not src_dir.is_dir():
                raise FileNotFoundError()   # Todo

            if dst_dir.exists() or dst_dir.is_symlink():
                raise FileExistsError()     # Todo error message

            dst_dir.symlink_to(src_dir)

    def _backup_files(self):
        for file in self.files:
            dst_file = self._get_dst_file(file)
            dst_file_bak = dst_file.with_suffix(self.backup_suffix)

            if not dst_file.exists() and not dst_file.is_symlink():
                pass
            elif dst_file.is_file() or dst_file.is_symlink():
                os.rename(dst_file, dst_file_bak)
            else:
                raise NotARegularFileError()  # Todo error message

    def _backup_directories(self):
        for directory in self.directories:
            dst_dir = self.dst_dir / self.directories[directory]
            dst_dir_bak = dst_dir.with_suffix(self.backup_suffix)

            if not dst_dir.exists() and not dst_dir.is_symlink():
                pass
            elif dst_dir.is_dir() or dst_dir.is_symlink():
                os.rename(dst_dir, dst_dir_bak)
            else:
                raise NotADirectoryError()  # Todo error message

    def _delete_files(self):
        for file in self.files:
            dst_file = self.dst_dir / self.files[file]

            if not dst_file.exists() and not dst_file.is_symlink():
                pass
            elif dst_file.is_file() or dst_file.is_symlink():
                dst_file.unlink()
            else:
                raise NotARegularFileError()  # Todo error message

    def _delete_directories(self):
        for directory in self.directories:
            dst_dir = self.dst_dir / self.directories[directory]

            if not dst_dir.exists() and not dst_dir.is_symlink():
                pass
            elif dst_dir.is_dir() and not dst_dir.is_symlink():
                shutil.rmtree(dst_dir)
            elif dst_dir.is_dir():
                dst_dir.unlink()
            else:
                raise NotADirectoryError()  # Todo error message

    def _keep_files(self):
        for dst_file in self.files.values():
            if dst_file.is_file():
                pass

    def _keep_directories(self):
        pass


class NotARegularFileError(OSError):
    """ Operation only works on regular files. """
    def __init__(self, *args):
        super().__init__(*args)


class IsARegularFileError(OSError):
    """ Operation doesn't work on regular files. """
    def __init__(self, *args):
        super().__init__(*args)
