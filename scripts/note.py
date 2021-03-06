#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import getpass
import json
import math as m
import os
import re
import sys
import subprocess as sp
import pprint as pp

from docopt import docopt  # TODO: Add dependency
from datetime import datetime


__config_file__ = "~/.config/noterc"


__doc__ = """note.py - Easily create notes using Rmarkdown and pandoc

Usage:
    note.py [-d <dir>] create [<prefix>] [--author=<name>] [--edit | --noedit]
                              [--editor=<prog>]
    note.py [-d <dir>] list [<prefix>] [-c <cols>] [-s <col>] [-r]
    note.py [-d <dir>] gen-make [--]
    note.py gen-config [--]
    note.py (-h | --help)
    note.py --version

Commands:
    create      Create a new note with the required pandoc header
    list        List notes and corresponding information
    gen-make    Create a Makefile that can compile the notes, using pandoc
    gen-config  Write a default config file to '{config}' or stdout

Arguments:
    <prefix>  String used to prefix the names of notes, defaults to 'lecture'
              New notes will automatically be numbered in ascending order

General Options:
    -h, --help       Show this message and exit
    -d <dir>, --dir=<dir>
                     Use the specified directory, defaults either to './notes'
                     or just '.', if the cwd ends in 'notes'
    --author=<name>  The author of the note, will be used in the header
    --edit           Open the note in an editor upon creation
    --noedit         Don't open the note in an editor (always overrules --edit)
    --editor=<prog>  Use the specified progam to edit notes
    -c <cols>, --columns=<cols>
                     Display the the specified columns, <cols> may either be a
                     comma separated list of column names or a string of column
                     characters (defaults to 'index,name')
    -s <col>, --sort=<col>
                     Sort the notes by the specified column, <col> may be a
                     column name or character (defaults to 'name')
    -r, --reverse    Invert the order, in which notes are listed
    --               Write to stdout instead of a file

Available Columns:
    i, index        Print the index of each note
    n, name         Print the name of each note
    m, modified     Print the date and time each note was last modified
    l, lines        Print the number of lines in each note
    w, words        Print the number of words in each note
    c, chars        Print the number of characters in each note
""".format(config=__config_file__)


__columns__ = {
        "i": "index",
        "n": "name",
        "m": "modified",
        "l": "lines",
        "w": "words",
        "c": "chars"
    }


__header__ = """---
vim: spelllang=de:shiftwidth=2
title: '{title}'
author: '{author}'
documentclass:
    scrartcl
---"""


__makefile__ = """
pandoc = /usr/bin/pandoc
type = -t latex

default : build

clean :
    rm -r build

continuous :
    ls *.Rmd | entr -n $(MAKE) build

build : *.Rmd
    for file in *.Rmd ; do $(MAKE) build/$${file%.*}.pdf ; done

build/%.pdf : %.Rmd
    mkdir -p build
    $(pandoc) $< $(type) -o $@
""".lstrip("\n").replace("    ", "\t")


def echo(*args, **kwargs):
    print("note.py:", *args, **kwargs)


def warn(*args, **kwargs):
    print("warning:", *args, **kwargs)


def error(*args, **kwargs):
    print("error:", *args, **kwargs)


def confirm(msg, default=True):
    echo(msg, "[Y/n]" if default else "[y/N]", end=" ")
    choice = input().lower()

    return default if re.fullmatch("\s*", choice) \
            else re.fullmatch("[\sy]*y[\sy]*", choice)


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
        echo("'%s' doesn't exist" % directory)
        if confirm("Do you want to create it?", default=True):
            os.makedirs(directory)
        else:
            return False

    return True


def change_directory(directory, create=False):
    if create and not ensure_exists(directory):
        return False
    elif not create and not os.path.exists(directory):
        return False

    os.chdir(directory)
    return True


def load_config():
    path = os.path.expanduser(__config_file__)

    if os.path.exists(path):
        with open(path, "r") as config_file:
            return json.load(config_file)
    else:
        return dict()


def merge(args, config):
    return {k: (args.get(k) or config.get(k)) for k in set(args) | set(config)}


def init_args(args):
    args['--edit'] = args['--edit'] and not args['--noedit']

    if not args['--editor']:
        args['--editor'] = os.environ['VISUAL']
    elif args['--editor'].startswith("$"):
        args['--editor'] = os.environ[args['--editor'].lstrip("$")]

    if not args['--author']:
        args['--author'] = getpass.getuser()

    if not args['--columns']:
        args['--columns'] = "index,name"

    if not args['--sort']:
        args['--sort'] = "name"


def get_notes(prefix):
    return [n for n in os.listdir() if re.fullmatch("%s-[0-9]+\.Rmd"
        % (".*" if prefix is None else prefix), n)]


def sorted_notes(args, notes):
    sort_by = args['--sort']
    if sort_by not in __columns__.values():
        sort_by = __columns__[sort_by]
    if sort_by == "modified":
        sort_by = "date"

    return sorted(notes, key=lambda n: n[sort_by] if sort_by != "index" else 0,
            reverse=bool(args['--reverse']))


def longest(notes, col, header=None):
    if header is None:
        header = col

    return max(notes + [{col: header}], key=lambda n: len(str(n[col])),
            default={col: ""})[col]


def parse_columns(cols_string):
    if not cols_string:
        return error("cols must not be empty")

    if "," in cols_string or cols_string in __columns__.values():
        for col in cols_string.split(","):
            if col not in __columns__.values():
                return error("'%s' is not a valid column name" % col)

        return cols_string.split(",")
    else:
        for char in cols_string:
            if char not in __columns__.keys():
                return error("'%s' is not a valid column character" % char)

        return [__columns__[char] for char in cols_string]


def get_note_info(note):
    return {
            "note":  note,
            "name":  os.path.splitext(note)[0],
            "date":  datetime.fromtimestamp(os.path.getmtime(note))
                        .strftime("%d. %b %H:%M").lstrip("0"),
            "lines": sum(1 for l in open(note)),
            "words": sum(len(re.sub("\s+", " ", l).split()) for l in open(note)),
            "chars": sum(len(l) for l in open(note))
        }


def get_column_widths(notes):
    return {
            "index": int(m.log10(len(notes))) + 1,
            "name":  len(longest(notes, "name",  header="Name")),
            "date":  len(longest(notes, "date",  header="Modified")),
            "lines": len(longest(notes, "lines", header="Lines")),
            "words": len(longest(notes, "words", header="Words")),
            "chars": len(longest(notes, "chars", header="Chars"))
        }


def print_header(args, widths, columns, sep="   "):
    for column in columns:
        if column == "index":
            print(widths['index'] * " ", end=sep)
        elif column == "name":
            print("Name".ljust(widths['name']), end=sep)
        elif column == "modified":
            print("Modified".ljust(widths['date']), end=sep)
        elif column == "lines":
            print("Lines".ljust(widths['lines']), end=sep)
        elif column == "words":
            print("Words".ljust(widths['words']), end=sep)
        elif column == "chars":
            print("Chars".ljust(widths['chars']), end=sep)

    print()


def print_line(args, widths, columns, note, index, sep="   "):
    for column in columns:
        if column == "index":
            print(str(index).rjust(widths['index']), end=sep)
        elif column == "name":
            print(note['name'].ljust(widths['name']), end=sep)
        elif column == "modified":
            print(note['date'].ljust(widths['date']), end=sep)
        elif column == "lines":
            print(str(note['lines']).ljust(widths['lines']), end=sep)
        elif column == "words":
            print(str(note['words']).ljust(widths['words']), end=sep)
        elif column == "chars":
            print(str(note['chars']).ljust(widths['chars']), end=sep)

    print()


def create_note(directory, args):
    if not change_directory(directory, create=True):
        return

    prefix = args['<prefix>'] if args['<prefix>'] is not None else "lecture"
    notes = [os.path.splitext(note)[0] for note in get_notes(prefix)]
    highest_id = max([int(n.split("-")[-1]) for n in notes], default=0)
    new_id = highest_id + 1

    note_name = prefix + "-" + str(new_id).zfill(2)
    file_name = note_name + ".Rmd"

    if not os.path.exists(file_name):
        echo("Creating note '%s'" % file_name)
        with open(file_name, "w") as f:
            print(__header__.format(title=note_name, author=args['--author']),  # TODO
                    file=f, end="\n\n")
    else:
        #  NOTE: This should never happen
        return warn("Note '%s' already exists" % file_name)

    if args['--edit']:
        echo("Opening note in '%s'" % os.path.basename(args['--editor']))
        sp.run([args['--editor'], file_name])


def list_notes(directory, args):
    if not change_directory(directory, create=False):
        return error("'%s' doesn't exist" % directory)

    # NOTE: Defaults to listing all notes, regardless of prefix
    notes = sorted_notes(args, [get_note_info(n)
        for n in get_notes(args['<prefix>'])])

    if not notes:
        return warn("No matching notes exist in '%s'" % os.getcwd())

    widths = get_column_widths(notes)
    columns = parse_columns(args['--columns'])

    if not columns:
        return

    print_header(args, widths, columns)

    for index, note in enumerate(notes):
        print_line(args, widths, columns, note, index)


def generate_makefile(directory, args):
    if args['--']:
        print(__makefile__)
    else:
        if not change_directory(directory, create=True):
            return

        file_name = "Makefile"
        path = os.path.join(os.getcwd(), file_name)

        if os.path.exists(file_name):
            warn("'%s' already exists" % path)
            if not confirm("Do you want to overwrite it?", default=False):
                return

        echo("Writing Makefile to '%s'" % path)

        with open(path, "w") as makefile:
            print(__makefile__, file=makefile, end="\n")


def generate_config(args):
    defaults = docopt(__doc__, argv=['create'])
    init_args(defaults)

    defaults = {k: v for k, v in defaults.items() if k.startswith("-")
                and k not in ["--", "--dir", "--help", "--version"]}

    if args['--']:
        print(json.dumps(defaults, indent=2))
    else:
        path = os.path.expanduser(__config_file__)

        if os.path.exists(path):
            warn("'%s' already exists" % path)
            if not confirm("Do you want to overwrite it?", default=False):
                return

        echo("Writing default config to '%s'" % path)

        with open(path, "w") as config:
            json.dump(defaults, config, indent=2)


if __name__ == "__main__":
    args = docopt(__doc__, version="note.py-0.6.0")
    config = load_config()
    args = merge(args, config)
    init_args(args)

    directory = get_directory(args)

    if args['create']:
        create_note(directory, args)

    elif args['list']:
        list_notes(directory, args)

    elif args['gen-make']:
        generate_makefile(directory, args)

    elif args['gen-config']:
        generate_config(args)

