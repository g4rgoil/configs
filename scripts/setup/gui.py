#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" This modules provides a curses interface for the setup script """

import npyscreen as nps
import pprint as pp

from category import CategoryCollection
from utils import load_categories


class SelectCategoryForm(nps.Form):
    def create(self):
        self.categories = self.create_categories()
        self.title = self.add(nps.TitleFixedText, use_two_lines=True,
                name="Avaiable Setup Categories")
        self.select = self.add(SelectCategoryWidget,
                values=list(self.categories))

    def h_display_help(self, *args, **kwargs):
        super().h_display_help(*args, **kwargs)
        help_form = SelectCategoryHelp()
        help_form.edit()

    @staticmethod
    def create_categories():
        try:
            categories = CategoryCollection()
        except ValueError as e:
            print("An error occurred while creating the categories: " + str(e))
            sys.exit(2)

        del categories["all"]
        return categories


class SelectCategoryWidget(nps.MultiSelect):
    def display_value(self, category):
        name_width = len(max(self.values, key=lambda c: len(c.name)).name)
        return category.name.ljust(name_width) + "  -  " + category.help


class SelectCategoryHelp(nps.Popup):
    def create(self):
        self.title =  self.add(nps.TitleFixedText, name="Fooooooooobar")


def wrapper_func(*args):
    form = SelectCategoryForm()
    form.edit()


if __name__ == "__main__":
    load_categories()
    nps.wrapper_basic(wrapper_func)
