#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" This modules provides a curses interface for the setup script """

import npyscreen as nps

from category import CategoryCollection
from utils import load_categories


class SelectCategoryForm(nps.Form):
    def create(self):
        self.categories = self.create_categories()
        self.title = self.add(nps.TitleFixedText, use_two_lines=True,
                name="Avaiable Setup Categories")
        self.select = self.add(SelectCategoryWidget, values=list(self.categories))

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
    def create(self, *args, **kwargs):
        super(*args, **kwargs)

    def display_value(self, category):
        return category.name + " - " + category.help


def wrapper_func(*args):
    form = SelectCategoryForm()
    form.edit()


if __name__ == "__main__":
    load_categories()
    nps.wrapper_basic(wrapper_func)
