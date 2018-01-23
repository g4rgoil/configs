#!/usr/bin/env python3

""" Script for setting up miscellaneous files on this machine. """

import tempfile
import shutil
import os
import os.path as path
import shlex
import tarfile

from categories.category import Category
from categories import require_root, get_dist

__version__ = "0.1.0"


class CategoryMisc(Category):
    directory = "misc"

    def __init__(self):
        super().__init__()

        self.install_dict = {
            "font": self._install_font,
            "all": None
        }

    def add_subparser(self, subparsers):
        super().add_subparser(subparsers)

        self.parser.add_version_action(__version__)

        group = self.parser.add_argument_group("misc specific options")

        choices = self.install_dict.keys()
        help = "install all specified categories; valid categories are" \
               + ", ".join(choices)
        self.parser.add_install_action(group=group, choices=choices, help=help)

    def set_up(self, namespace=None):
        super().set_up(namespace)

        if namespace.install:
            self.install(namespace.install)

    @require_root
    def _install_font(self):
        dist = get_dist()

        self.utils.install_packages(dist, "wget")

        if dist == "debian":
            self.utils.debian_install_nodejs()
        elif dist == "arch":
            self.utils.install_packages("arch", "nodejs")

        tempdir = tempfile.mkdtemp()
        src_url = "https://github.com/adobe-fonts/source-code-pro/releases/" \
                  "download/variable-fonts/SourceCodeVariable-Roman.otf"
        self.utils.run(shlex.split("wget -P '%s' %s" % (tempdir, src_url)))

        src_file = path.join(tempdir, "SourceCodeVariable-Roman.otf")
        dst_dir = "/usr/share/fonts/SourceCodePro"
        os.mkdir(dst_dir)
        shutil.copy(src_file, dst_dir)

        self.utils.run(shlex.split("fc-cache -f -v '%s'" % "/usr/share/fonts"))

        shutil.rmtree(tempdir)
