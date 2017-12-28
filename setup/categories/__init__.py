#!/usr/bin/env python3
# -*- coding: utf8 -*-

from pathlib import Path
from os.path import dirname, basename, isfile
from glob import glob

modules = glob(dirname(__file__) + "/*.py")
__all__ = [basename(f)[:-3] for f in modules if isfile(f) and not f.endswith("__init__.py")]

__repo_dir__ = Path(__file__).parents[2]
