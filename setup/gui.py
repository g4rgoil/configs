#!/usr/bin/env python3

""" This modules provides a curses interface for the setup script """

import curses
import locale
import signal
import sys
from curses import A_NORMAL, A_STANDOUT, A_UNDERLINE
from typing import List

from category import CategoryCollection, Category
from utils import load_categories

__version__ = "0.1.0"

locale.setlocale(locale.LC_ALL, "")


class CategoryGui(object):
    enter_keys = [curses.KEY_ENTER, ord("\n"), ord("\r")]

    def __init__(self):
        self.outer_window = None
        self.window = None

        try:
            self.categories = CategoryCollection()
        except ValueError as e:
            print("An error occurred while creating the categories: " + str(e))
            sys.exit(2)

        del self.categories["all"]

    @staticmethod
    def handle_global_keys(key):
        if key == ord("q"):
            sys.exit(0)

    @staticmethod
    def handle_movement_keys(key, current, limit) -> int:
        if key == ord("j") or key == curses.KEY_DOWN:
            current += 1
        elif key == ord("k") or key == curses.KEY_UP:
            current -= 1
        elif key == ord("g"):
            current = 0
        elif key == ord("G"):
            current = limit - 1

        return current

    def start(self, window):
        curses.curs_set(False)
        self.outer_window = window
        self.outer_window.box()
        self.outer_window.refresh()

        self.window = curses.newwin(curses.LINES - 3, curses.COLS - 4, 1, 2)
        categories = self.select_categories()
        self.setup_categories(categories)

    def select_categories(self) -> List[Category]:
        self.draw_key_help(
            "(j/↓) move down", "(k/↑) move down", "(l/↵) confirm",
            "(g) move top", "(G) move bottom", "(t) toggle", "(T) select all",
            "(q) quit")

        current, limit = 0, len(self.categories.dict)
        selected = set()

        while True:
            self.draw_categories(current, selected)

            self.window.refresh()
            key = self.outer_window.getch()

            self.handle_global_keys(key)
            current = self.handle_movement_keys(key, current, limit)

            if key == ord("t"):
                selected ^= {current}
            if key == ord("T"):
                selected = set() if len(selected) == limit \
                    else set(range(0, limit))
            elif key in self.enter_keys or key == ord("l"):
                selected.add(current)
                break

            current %= limit

        return selected

    def draw_categories(self, current=0, selected=None):
        fill_chars = len(max(self.categories, key=lambda c: len(c.name)).name)
        selected = set() if selected is None else selected
        self.window.clear()

        for index, category in enumerate(self.categories):
            self.draw_category(index, category, current == index,
                               index in selected, fill_chars)

    def draw_category(self, index, category, highlight, selected, fill_chars):
        decoration = A_NORMAL | (A_STANDOUT if highlight else 0) \
                     | (A_UNDERLINE if selected else 0)

        self.window.addstr(index, 0, str.ljust(category.name, fill_chars)
                           + "  -  " + category.help, decoration)

    def setup_categories(self, categories):
        self.draw_key_help(
            "(j/↓) move down", "(k/↑) move down", "(t/↵) confirm/toggle",
            "(g) move top", "(G) move bottom", "(T) select all",
            "(q) quit")

        self.outer_window.getch()

    def draw_install_options(self, category):
        pass

    def draw_install_option(self):
        pass

    def draw_key_help(self, *args):
        message = "   ".join(args)
        start = int(curses.COLS / 2) - int(len(message) / 2)

        self.outer_window.clear()
        self.outer_window.box()
        self.outer_window.addstr(curses.LINES - 2, start, message)
        self.outer_window.refresh()


if __name__ == "__main__":
    load_categories()

    signal.signal(signal.SIGINT, lambda *args: sys.exit(1))
    gui = CategoryGui()
    curses.wrapper(gui.start)
