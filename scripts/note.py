#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import sys

from docopt import docopt  # TODO: Add dependency


__doc__ = """note.py - Easily create notes using Rmarkdown and pandoc

Usage:
    note.py [-d <dir>] create [<prefix>] [--edit] [--editor=<prog>]
    note.py [-d <dir>] edit <note> [--editor=<prog>]
    note.py [-d <dir>] delete <note>
    note.py [-d <dir>] list [<prefix>]
    note.py (-h | --help)
    note.py --version

Arguments:
    <prefix>   String used to prefix the names of notes, defaults to 'lecture'
               New notes will automatically be numbered in ascending order
    <note>     The name of a note in the specified directory

Options:
    -h, --help       Show this message and exit
    -d <dir>, --dir=<dir>
                     Manage notes in the specified directory. Defaults either
                     to './notes' or just '.', if the cwd ends in 'notes'
    --edit           Open the note in an editor upon creation
    --editor=<prog>  Use the specified progam to edit notes
                     [default: {visual}]
""".format(visual=os.environ['VISUAL'])

__header__ = """---
title: '{title}'
author: '{author}'
documentclass:
    scrartcl
---"""


def get_directory(args):
    directory = args['--dir']

    if directory is None:
        if os.path.basename(os.getcwd()) == "notes":
            directory = os.getcwd()
        else:
            directory = os.path.join(os.getcwd(), "notes")
    else:
        directory = os.path.abspath(directory)

    return directory


def ensure_exists(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)


def get_notes(prefix):
    return [os.path.splitext(n)[0] for n in os.listdir()
            if re.fullmatch("%s-[0-9]+\.([a-zA-Z]+)" % prefix)]


def create(args):
    notes = get_notes(args['prefix'])
    highest_id = max([int(n.split("-")[-1]) for n in notes])
    new_id = highest_id + 1


def edit(args):
    pass


def delete(args):
    pass


def list(args):
    pass


if __name__ == "__main__":
    args = docopt(__doc__, version="note.py-0.0.1")

    print(args)

    directory = get_directory(args)
    ensure_exists(directory)
    os.chdir(directory)

    if args['create']:
        create(args)

    elif args['edit']:
        edit(args)

    elif args['delete']:
        delete(args)

    elif args['list']:
        list(args)

