#!/usr/bin/env python3

""" This modules provides utility classes and functions """

import glob
import importlib
import json
import os
import pwd
import re
import shlex
import shutil
import subprocess
import sys

from pathlib import Path
from os.path import abspath, basename, dirname, isfile, join, splitext
from subprocess import CompletedProcess, DEVNULL, run
from typing import Callable, Optional

__version__ = "1.2.0"

__repo_dir__ = Path(__file__).parents[2]


def load_categories() -> None:
    category_dir = join(dirname(abspath(__file__)), "categories")
    sys.path.append(category_dir)

    for file in glob.iglob(join(category_dir, "**/*.py"), recursive=True):
        if isfile(file):
            importlib.import_module(splitext(basename(file))[0])


def require_repo_dir(name) -> Path:
    repo_dir = __repo_dir__ / name

    if not repo_dir.is_dir():
        raise NotADirectoryError("Cannot find directory '%s' in repository"
                                 % name)

    return repo_dir


def is_root() -> bool:
    return os.getuid() == 0


def require_root(func) -> Callable:
    """ Function decorator for functions that require root privileges. """

    def new_function(*args, **kwargs):
        if not is_root():
            raise PermissionError("Cannot perform this operation: "
                                  "Missing root privileges")
        return func(*args, **kwargs)

    return new_function


def get_dist() -> Optional[str]:
    """ Returns the name of the linux distribution on this system or None """
    with open("/etc/os-release", "r") as file:
        for line in file.read().splitlines():
            if re.match("^ID=", line):
                return line.lstrip("ID=")

    return None


def parse_json_descriptor(path) -> dict:
    """ Parses the specified json file and returns it as dict """
    with open(str(path), "r", encoding="utf-8") as file:
        json_file = json.load(file)

    return json_file


def remove_kv_pair(collection, option) -> bool:
    """ Removes the first option value pair from the collection. """
    index = -1
    if option in collection:
        index = collection.index(option)
        del collection[index:index + 2]

    return index != -1


def remove_user_options(argv=None) -> list:
    """ Removes all -u and --user option value pairs from argv or sys.argv. """
    if argv is None:
        argv = sys.argv
    argv = argv.copy()

    while remove_kv_pair(argv, "-u") or remove_kv_pair(argv, "--user"):
        pass

    return argv


def start_subprocess(args, user) -> subprocess.Popen:
    """ Executes the given arguments as the specified user. """
    pw_record = pwd.getpwnam(user)
    user_name = pw_record.pw_name
    user_home = pw_record.pw_dir
    uid = pw_record.pw_uid
    gid = pw_record.pw_gid

    cwd = os.getcwd()

    env = os.environ.copy()
    env["HOME"] = user_home
    env["LOGNAME"] = user_name
    env["PWD"] = cwd
    env["USER"] = user_name

    process = subprocess.Popen(
        args, preexec_fn=demote(uid, gid), cwd=cwd, env=env
    )

    return process


def demote(uid, gid) -> Callable[[], None]:
    """ Returns a functions that sets the uid and gid for the current user. """

    def result():
        try:
            os.setgid(gid)
            os.setuid(uid)
        except PermissionError:
            sys.exit(2)

    return result


class SetupUtils(object):
    def __init__(self, namespace=None):
        args_dict = vars(namespace) if namespace is not None else {}

        self.link = args_dict.get("link", True)

        dst_handling = args_dict.get("dst_handling", "keep")
        self.keep = (dst_handling == "keep")
        self.backup = (dst_handling == "backup")
        self.delete = (dst_handling == "delete")

        self.verbose = args_dict.get("verbose", False)
        self.quiet = args_dict.get("quiet", False)
        self.confirm = args_dict.get("confirm", True)  # TODO implement

        self.delete_backups = args_dict.get("delete_backups", False)

    @staticmethod
    def _delete_file(file) -> None:
        if file.is_file() or file.is_symlink():
            file.unlink()
        elif file.is_dir():
            shutil.rmtree(str(file))

    def symlink(self, src, dst) -> None:
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

    def backup_file(self, src) -> None:
        if not self.backup:
            return

        if not src.exists() and not src.is_symlink():
            return

        dst = src.with_suffix(".old")
        self.print_move(src, dst)
        os.rename(str(src), str(dst))

    def delete_file(self, file) -> None:
        if not self.delete:
            return

        if not file.exists() and not file.is_symlink():
            return

        self.print_delete(file)
        self._delete_file(file)

    def delete_backup(self, file) -> None:
        if not self.delete_backups:
            return

        backup = file.with_suffix(".old")

        if not backup.exists() and not backup.is_symlink():
            return

        self.print_delete(backup)
        self._delete_file(backup)

    def run(self, args) -> CompletedProcess:
        kwargs = dict(stdout=None if self.verbose else DEVNULL,
                      stderr=DEVNULL if self.quiet else None, check=False)

        return run(args, **kwargs)

    def clone_repo(self, url, path, name=None) -> None:
        if name is None:
            name = path.name

        path = path.expanduser()

        self.error("Installing %s to '%s'..." % (name, str(path)))

        if path.exists():
            if path.joinpath(".git").exists():
                self.error("%s is already installed, updating ..."
                        % name, prefix="warning:")

                args = ["git", "-C", str(path), "pull", "-v"]
                if not self.verbose:
                    args.remove("-v")

                process = self.run(args)

                if process.returncode != 0:
                    self.error("Failed to update %s: Exited with exit code %s"
                            % (name, process.returncode), prefix="error:")
                return

            self.error("'%s' already exists, but is no git repo" % path,
                    prefix="error:")
            if not self.confirm("Clone into the existing directory?", False):
                return self.error("Skipping installation of %s" % name,
                        prefix="warning:")

        path.mkdir(parents=True, exist_ok=True)

        args = ["git", "clone", "-v", str(url), str(path)]
        if not self.verbose:
            args.remove("-v")

        process = self.run(args)

        if process.returncode != 0:
            self.error("Failed to install %s: Exited with code %s"
                    % (name, process.returncode), prefix="error:")

    def try_execute(self, func) -> None:
        try:
            func()
        except (OSError, PermissionError) as e:
            self.error(str(e), prefix="error:")

    def install_packages(self, dist, *packages) -> None:
        if dist == "arch":
            command = "pacman -S --noconfirm %s"
        elif dist == "debian":
            command = "apt --assume-yes install %s"
        else:
            raise OSError("Cannot install packages: Unknown or unsupported "
                          "linux distribution '%s'" % dist)

        self._install_packages(command, *packages)

    def install_pip_packages(self, *packages) -> None:
        self._install_packages("pip install %s", *packages)

    def install_npm_packages(self, *packages) -> None:
        self._install_packages("npm install -g %s", *packages)

    def install_gem_packages(self, *packages) -> None:
        self._install_packages("gem install %s --no-user-install", *packages)

    def _install_packages(self, command, *packages) -> None:
        if len(packages) == 0:
            return

        process = self.run(shlex.split(command % " ".join(packages)))

        if process.returncode != 0:
            self.error("Failed to install packages '%s': Exited with code %s"
                    % (", ".join(packages), process.returncode),
                    prefix="error:")

    def print(self, prefix=None, *args, **kwargs) -> None:
        prefix = "setup.py:" if prefix is None else prefix
        if self.verbose:
            print(prefix, *args, **kwargs)

    def error(self, *args, prefix=None, **kwargs) -> None:
        prefix = "setup.py:" if prefix is None else prefix
        if not self.quiet:
            print(prefix, *args, file=sys.stderr, **kwargs)

    def confirm(self, msg, default=True) -> bool:
        """ Waits for user input to confirm or uses the default. """
        if self.quiet or not self.confirm:
            return default

        self.error(msg, "[Y/n]" if default else "[y/N]", end=" ")

        user_input = input()
        choices = {'y': True, 'Y': True, 'n': False, 'N': False, None: default,
                   '': default}

        return choices.get(user_input, not default)

    def print_create_symlink(self, src, dst) -> None:
        self.print("Creating link: '%s' -> '%s'" % (str(src), str(dst)))

    def print_delete(self, file) -> None:
        self.print("Deleting file: '%s'" % str(file))

    def print_move(self, src, dst) -> None:
        self.print("Moving file: '%s' -> '%s'" % (str(src), str(dst)))


class FileMapping(object):
    """
    Represents a mapping between a file in this repository and a file
    on this system.
    """

    utils = SetupUtils()

    def __init__(self, src, dst, root=False, distribution=None):
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
    def require_utils(cls, utils) -> SetupUtils:
        return utils if utils is not None else cls.utils

    def is_privileged(self) -> bool:
        return is_root() >= self.root

    def is_distribution(self) -> bool:
        return get_dist() in self.distributions or not self.distributions

    def can_setup(self) -> bool:
        return self.is_privileged() and self.is_distribution()

    def with_suffix(self, suffix):
        dst = self.dst + suffix
        return FileMapping(self.src, dst, self.root, self.distributions)

    def link(self, utils=None) -> None:
        if self.can_setup():
            self.require_utils(utils).symlink(self.src, self.dst)

    def delete_dst(self, utils=None) -> None:
        if self.can_setup():
            self.require_utils(utils).delete_file(self.dst)

    def delete_backup(self, utils=None) -> None:
        if self.can_setup():
            self.require_utils(utils).delete_backup(self.dst)

    def backup_dst(self, utils=None) -> None:
        if self.can_setup():
            self.require_utils(utils).backup_file(self.dst)
