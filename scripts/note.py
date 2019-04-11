#!/usr/bin/env python3
# -*- coding: utf-8 -*-


#  TODO: Add dependencies for docopt, pandoc and entr <11-04-19, Pascal Mehnert> #


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
    note.py [-d <dir>] list [<prefix>] [-mlwca] [-r]
    note.py [-d <dir>] gen-make [--]
    note.py gen-config [--]
    note.py (-h | --help)
    note.py --version

Commands:
    create        Create a new note with the required pandoc header
    list          List notes and corresponding information
    gen-make  Create a Makefile that can compile the notes, using pandoc
    gen-config    Write a default config file to '{config}' or stdout

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
    --noedit         Don't open the note in an editor (aloways overrules --edit)
    --editor=<prog>  Use the specified progam to edit notes

Listing Options:
    -m, --modified  Print the date and time each note was last modified
    -l, --lines     Print the number of lines in each note
    -w, --words     Print the number of words in each note
    -c, --chars     Print the number of characters in each note
    -a, --all       Print all the information listed above
    -r, --reverse   Invert the order, in which notes are listed
"""


__header__ = """---
vim: spelllang=de
title: '{title}'
author: '{author}'
documentclass:
    scrartcl
---"""


__makefile__ = """
pandoc = /usr/bin/pandoc
type = -t latex

default : build

clean:
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


def get_notes(prefix):
    return [n for n in os.listdir() if re.fullmatch("%s-[0-9]+\.Rmd"
        % (".*" if prefix is None else prefix), n)]


def longest(notes, col, header=None):
    if header is None:
        header = col

    return max(notes + [{col: header}], key=lambda n: len(str(n[col])),
            default={col: ""})[col]


def print_header(args, widths, sep="   "):
    print(widths['index'] * " ", end=sep)
    print("Name".ljust(widths['name']), end=sep)

    if args['--modified'] or args['--all']:
        print("Modified".ljust(widths['date']), end=sep)
    if args['--lines'] or args['--all']:
        print("Lines".ljust(widths['lines']), end=sep)
    if args['--words'] or args['--all']:
        print("Words".ljust(widths['words']), end=sep)
    if args['--chars'] or args['--all']:
        print("Chars".ljust(widths['chars']), end=sep)

    print()


def print_line(args, widths, note, index, sep="   "):
    print(str(index).rjust(widths['index']), end=sep)
    print(note['name'].ljust(widths['name']), end=sep)

    if args['--modified'] or args['--all']:
        print(note['date'].ljust(widths['date']), end=sep)
    if args['--lines'] or args['--all']:
        print(str(note['lines']).ljust(widths['lines']), end=sep)
    if args['--words'] or args['--all']:
        print(str(note['words']).ljust(widths['words']), end=sep)
    if args['--chars'] or args['--all']:
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
        return echo("Note '%s' already exists" % file_name)

    if args['--edit']:
        echo("Opening note in '%s'" % os.path.basename(args['--editor']))
        sp.run([args['--editor'], file_name])


def list_notes(directory, args):
    if not change_directory(directory, create=False):
        return echo("'%s' doesn't exist" % directory)

    # NOTE: Defaults to listing all notes, regardless of prefix
    notes = [
        {
            "note":  note,
            "name":  os.path.splitext(note)[0],
            "date":  datetime.fromtimestamp(os.path.getmtime(note))
                        .strftime("%d. %b %H:%M").lstrip("0"),
            "lines": sum(1 for l in open(note)),
            "words": sum(len(re.sub("\s+", " ", l).split()) for l in open(note)),
            "chars": sum(len(l) for l in open(note))
        } for note in get_notes(args['<prefix>'])]

    notes = sorted(notes, key=lambda n: n['name'], reverse=args['--reverse'])

    if not notes:
        echo("No matching notes exist in '%s'" % os.getcwd())
        return

    widths = {
            "index": int(m.log10(len(notes))) + 1,
            "name":  len(longest(notes, "name",  header="Name")),
            "date":  len(longest(notes, "date",  header="Modified")),
            "lines": len(longest(notes, "lines", header="Lines")),
            "words": len(longest(notes, "words", header="Words")),
            "chars": len(longest(notes, "chars", header="Chars"))
        }

    print_header(args, widths)

    # TODO: Add options for sorting the notes
    for index, note in enumerate(notes):
        print_line(args, widths, note, index)


def generate_makefile(directory, args):
    if args['--']:
        print(__makefile__)
    else:
        if not change_directory(directory, create=True):
            return

        file_name = "Makefile"
        path = os.path.join(os.getcwd(), file_name)

        if os.path.exists(file_name):
            echo("'%s' already exists" % path)
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
            echo("'%s' already exists" % path)
            if not confirm("Do you want to overwrite it?", default=False):
                return

        echo("Writing default config to '%s'" % path)

        with open(path, "w") as config:
            json.dump(defaults, config, indent=2)


if __name__ == "__main__":
    args = docopt(__doc__, version="note.py-0.5.0")
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

