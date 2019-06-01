#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" This modules provides a curses interface for the setup script """

import npyscreen as nps
import pprint as pp

from category import CategoryCollection
from utils import load_categories


class SetupGui(nps.NPSAppManaged):
    def onStart(self):
        self.categories = list(self.create_categories())

        select_form = self.addForm("MAIN", SelectCategoryForm,
                name="Available Setup Categories", minimum_lines=23)

    @staticmethod
    def create_categories():
        try:
            categories = CategoryCollection()
        except ValueError as e:
            print("An error occurred while creating the categories: " + str(e))
            sys.exit(2)

        del categories["all"]
        return categories


class SelectCategoryForm(nps.FormBaseNew):
    def afterEditing(self):
        self.parentApp.setNextForm(None)

    def create(self):
        self.value = self.parentApp.categories

        self.select = self.add(SelectCategoryWidget,
                values=list(self.parentApp.categories),
                scroll_exit=True)

        self.nextrely += 2
        self.nextrelx += 8
        self.setup = self.add(nps.ButtonPress, name="Setup",
                when_pressed_function=self.on_setup)

        self.nextrely -= 1
        self.nextrelx += self.setup.width + 2
        self.install = self.add(nps.ButtonPress, name="Install",
                when_pressed_function=self.on_install)

        self.nextrely -= 1
        self.nextrelx += self.install.width + 2
        self.cancel = self.add(nps.ButtonPress, name="Cancel",
                when_pressed_function=self.on_cancel)

    def on_setup(self):
        pass

    def on_install(self):
        pass

    def on_cancel(self):
        pass


class SelectCategoryWidget(nps.MultiSelect):
    def when_parent_changes_value(self):
        self.values = self.parent.value

    def calculate_area_needed(self):
        return len(self.parent.value), 0

    def display_value(self, category):
        name_width = len(max(self.values, key=lambda c: len(c.name)).name)
        return category.name.ljust(name_width) + "  -  " + category.help


if __name__ == "__main__":
    load_categories()
    setup_gui = SetupGui().run()

