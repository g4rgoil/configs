#!/usr/bin/env python3
# -*- coding: utf8 -*-

import os as _os
import re as _re
import shlex

from pathlib import Path
from subprocess import run, DEVNULL
from os.path import dirname, basename, isfile
from glob import glob

modules = glob(dirname(__file__) + "/*.py")
__all__ = [basename(f)[:-3] for f in modules if isfile(f) and not f.endswith("__init__.py")]

__repo_dir__ = Path(__file__).parents[2]


def require_repo_dir(name) -> Path:
    repo_dir = __repo_dir__ / name

    if not repo_dir.is_dir():
        raise NotADirectoryError("'%s' is not a directory")

    return repo_dir


def require_root(func):
    """ Function decorator for functions that require root privileges. """
    def new_function(*args, **kwargs):
        if _os.getuid() != 0:
            raise PermissionError("Cannot perform this operation: "
                                  "Missing root privileges")
        return func(*args, **kwargs)
    return new_function


def get_dist():
    with open("/etc/os-release", "r") as file:
        for line in file.read().splitlines():
            if _re.match("^ID=", line):
                return line.lstrip("ID=")

    return ""
