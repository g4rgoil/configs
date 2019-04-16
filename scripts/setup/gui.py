#!/usr/bin/env python3

""" This modules provides a curses interface for the setup script """

import curses
import locale
import math
import signal
import subprocess
import sys
from curses import newwin, A_NORMAL, A_STANDOUT, A_BOLD
from os.path import abspath, dirname, join
from typing import Set, Tuple, List
from subprocess import Popen, PIPE, STDOUT

from category import CategoryCollection, Category
from utils import load_categories

__version__ = "0.1.0"
__setup_script__ = join(dirname(abspath(__file__)), "setup.py")

locale.setlocale(locale.LC_ALL, "")


class CategoryGui(object):
    enter_keys = [curses.KEY_ENTER, ord("\n"), ord("\r")]

    def __init__(self):
        self.outer_window = None

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

    def start(self, window):
        curses.curs_set(False)
        self.outer_window = window
        self.outer_window.box()
        self.outer_window.refresh()

        SelectCategoryWindow(self).main_loop()
        # self.setup_categories(categories)

    def setup_categories(self, categories):
        self.draw_key_help(
            "(j/↓) move down", "(k/↑) move down", "(t/↵) confirm/toggle",
            "(g) move top", "(G) move bottom", "(T) select all", "(q) quit")

        index = 0

        header_mid = int(min([max(
            [len( k + v["help"]) + 5 for k, v in dict(c.install_dict).items()
             if k != "all"]) for c in
            [c for c in categories if len(c.install_dict)]], default=0) / 2)

        for category in categories:
            if len(category.install_dict):
                index = self.draw_install_options(category, index, header_mid)

        self.outer_window.getch()

    def draw_install_options(self, category, start_index, header_mid) -> int:
        options = category.descriptor["category"]["install"]
        options = [o for o in options if o["name"] != "all"]

        header_start = header_mid - math.ceil(len(category.name) / 2)

        self.window.addstr(start_index, header_start, category.name, A_BOLD)
        start_index += 1

        fill_chars = len(max(options, key=lambda o: len(o["name"]))["name"])
        for option in options:
            self.draw_install_option(option, start_index, fill_chars)
            start_index += 1

        self.window.refresh()
        return start_index + 2

    def draw_install_option(self, option, index, fill_chars):
        self.window.addstr(index, 0, str.ljust(option["name"], fill_chars)
                           + "  -  " + option["help"])

    def draw_buttons(self, button_dict):
        button_string = "<" + (">      <".join(button_dict.keys())) + ">"
        start = int(curses.COLS / 2) - math.ceil(len(button_string) / 2)

        self.outer_window.addstr(curses.LINES - 7, start, button_string,
                                 A_BOLD)
        self.outer_window.refresh()

    def draw_key_help(self, *args):
        message = "   ".join(args)
        start = int(curses.COLS / 2) - math.ceil(len(message) / 2)

        self.outer_window.clear()
        self.outer_window.box()
        self.outer_window.addstr(curses.LINES - 2, start, message)
        self.outer_window.refresh()


class SelectCategoryWindow(object):
    buttons = ["<LINK>", "<BACKUP>", "<DELETE>", "<INSTALL>"]

    def __init__(self, category_gui: CategoryGui):
        self.gui = category_gui

        longest_name = max(self.gui.categories, key=lambda c: len(c.name)).name
        self.fill_chars = len(longest_name)

        longest = max(self.gui.categories, key=lambda c: len(c.name + c.help))
        width = int((len(longest.name + longest.help) + 5) * 1.5)

        self.width = min(width, curses.COLS - 2)
        self.height = len(self.gui.categories.dict) + 8
        self.top_left = (2, int(curses.COLS / 2) - math.ceil(width / 2))

        self.window = newwin(self.height, self.width, *self.top_left)
        self.init_window()

    @classmethod
    def handle_movement(cls, key, current, button, limit) -> Tuple[int, int]:
        if current < limit:
            if key == ord("j") or key == curses.KEY_DOWN:
                current += 1
            elif key == ord("k") or key == curses.KEY_UP:
                current = max(current - 1, 0)

        if current == limit:
            button = max(0, button)

            if key == ord("k") or key == curses.KEY_UP:
                current = limit - 1
                button = -1
            elif key == ord("l") or key == curses.KEY_RIGHT:
                button = min(button + 1, len(cls.buttons) - 1)
            elif key == ord("h") or key == curses.KEY_LEFT:
                button = max(button - 1, 0)

        return current, button

    @staticmethod
    def handle_selection(key, current, limit, selection) -> Set[int]:
        if key == ord("T"):
            return set() if len(selection) == limit else set(range(0, limit))

        if current < limit:
            if key == ord("t") or key in CategoryGui.enter_keys:
                return selection ^ {current}

        return selection

    def get_categories_from_selection(self, selection) -> List[Category]:
        return [c for i, c in enumerate(self.gui.categories) if i in selection]

    def handle_button(self, key, button, selection):
        if len(selection) and button != -1 and key in CategoryGui.enter_keys:
            categories = self.get_categories_from_selection(selection)
            handler = [self.handle_link_button, self.handle_backup_button,
                       self.handle_delete_button, self.handle_install_button]

            handler[button](categories)

    def handle_link_button(self, categories):
        self.run_subprocess(*[[
            sys.executable, __setup_script__, "-v", "--link", "--keep",
            c.name] for c in categories])

    def handle_backup_button(self, categories):
        self.run_subprocess(*[[
            sys.executable, __setup_script__, "-v", "--no-link", "--backup",
            c.name] for c in categories])

    def handle_delete_button(self, categories):
        self.run_subprocess(*[[
            sys.executable, __setup_script__, "-v", "--no-link", "--delete",
            c.name] for c in categories ])

    def handle_install_button(self, categories):
        pass

    def run_subprocess(self, *args):
        SubprocessWindow(*args).main_loop()

        self.gui.outer_window.touchwin()
        self.gui.outer_window.refresh()
        self.window.touchwin()
        self.window.refresh()

    def init_window(self):
        self.window.border()
        self.gui.draw_key_help(
            "(h/j/k/l) move left/down/up/right", "(t/\u21B5) confirm/toggle",
            "(T) select all", "(q) quit")

        header = "Available Setup Categories"
        start = int(self.width / 2) - math.ceil(len(header) / 2)
        self.window.addstr(1, start, header, A_BOLD)

    def main_loop(self):
        current, button, limit = 0, -1, len(self.gui.categories.dict)
        selection = set()

        while True:
            self.draw_categories(current, selection)
            self.draw_buttons(button)
            key = self.gui.outer_window.getch()

            self.gui.handle_global_keys(key)
            current, button = self.handle_movement(key, current, button, limit)
            selection = self.handle_selection(key, current, limit, selection)
            self.handle_button(key, button, selection)

    def draw_categories(self, current, selection):
        for i, c in enumerate(self.gui.categories):
            decoration = A_NORMAL | (int(current == i) * A_STANDOUT)
            line = c.name.ljust(self.fill_chars) + "  -  " + c.help
            line = ("\u2713  " if i in selection else "   ") + line
            line = str.ljust(line, self.width - 4)
            self.window.addstr(i + 3, 2, line, decoration)

        self.window.refresh()

    def draw_buttons(self, button):
        size = sum([len(s) for s in self.buttons]) + len(self.buttons) * 5 - 5
        start = int(self.width / 2) - math.ceil(size / 2)

        self.window.move(self.height - 3, start)

        for i, b in enumerate(self.buttons):
            if i != 0:
                self.window.addstr("   ")

            decoration = A_BOLD | (int(button == i) * A_STANDOUT)
            self.window.addstr(" " + b + " ", decoration)

        self.window.refresh()


class SubprocessWindow(object):
    def __init__(self, *arguments):
        if isinstance(arguments[0], str):
            self.arguments = [arguments]
        else:
            self.arguments = arguments

        self.width = math.ceil(curses.COLS / 1.5)
        self.height = math.ceil(curses.LINES / 1.5)

        self.output_line = self.height - 3

        start_x = int(curses.COLS / 2) - math.ceil(self.width / 2)
        start_y = int(curses.LINES / 2) - math.ceil(self.height / 2)
        self.outer_start = (start_y, start_x)
        self.start = (start_y + 1, start_x + 2)

        self.outer_window = newwin(self.height, self.width, *self.outer_start)
        self.window = newwin(self.height - 2, self.width - 4, *self.start)
        self.init_window()

    def print_line(self, s=None):
        self.window.scroll()
        self.window.addstr(self.output_line, 0, "" if s is None else s)

    def init_window(self):
        self.outer_window.border()
        self.outer_window.refresh()
        self.window.scrollok(True)

    def kill_window(self):
        del self.window
        del self.outer_window

    def main_loop(self):
        for args in self.arguments:
            self.print_line(" ".join(args))

            process = Popen(args, stdout=PIPE, stderr=STDOUT)
            self.dump_output(process)
            self.print_line()

        self.print_line()
        self.print_line("Press any key to exit")

        self.window.getch()
        self.kill_window()

    def dump_output(self, process):
        while True:
            line = process.stdout.readline()
            if line != b"" and line is not None:
                self.print_line(line.decode("UTF-8").rstrip("\n"))
                self.window.refresh()
            else:
                break


if __name__ == "__main__":
    load_categories()

    signal.signal(signal.SIGINT, lambda *args: sys.exit(1))
    gui = CategoryGui()
    curses.wrapper(gui.start)
