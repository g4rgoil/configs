#!/usr/bin/python

import re
import datetime


def format_timestamp(date) -> str:
    return date.strftime("%Y-%m-%d")


def require_no_spaces(string, msg):
    if re.search("\s", string) is not None:
        raise ValueError(msg)


class Task(object):
    def __init__(self, description, done=False, priority=None, completed=None,
                 created=None):
        self.done = done
        self.priority = priority
        self.completed = completed
        self.created = created
        self.description = Description(description)

    def __str__(self):
        task = "x " if self.done else ""
        task += "(%s) " % self.priority if self.priority is not None else ""
        task += "%s " % self.completed if self.completed is not None else ""
        task += "%s " % self.created if self.created is not None else ""
        task += "%s" % self.description

        return task

    def __repr__(self):
        return "Task('" + self.__str__() + "')"

    @classmethod
    def parse(cls, task):
        if task is None:
            return None

        task = task.strip().rstrip("\n")
        kwargs = dict()

        if task == "":
            return None

        if task.startswith("x "):
            kwargs["done"] = True
            task = task[1:].lstrip()

        match = re.match(r"\(([A-Z])\) ", task)
        if match is not None:
            kwargs["priority"] = match.group(1)
            task = task[match.end():].lstrip()

        regex = "({0}) (({0}) )?".format("\d{4}-\d{2}-\d{2}")
        match = re.match(regex, task)
        if match is not None:
            # Check whether both or only one date is specified
            if match.group(3) is not None:
                kwargs["created"] = match.goup(3)
                kwargs["completed"] = match.group(1)
            else:
                key = "completed" if kwargs["done"] else "created"
                kwargs[key] = match.group(1)

            task = task[match.end():].lstrip()

        kwargs["description"] = task

        return Task(**kwargs)

    def do(self):
        if not self.done:
            self.done = True
            self.set_completion_date()

    def undo(self):
        self.done = False
        self.unset_creation_date()

    def set_priority(self, priority):
        if priority is None:
            self.priority = None

        priority = priority.upper()
        if re.fullmatch("[A-Z]", priority):
            self.priority = priority
        else:
            raise ValueError("Not a valid priority " + priority)

    def unset_priority(self):
        self.set_priority(None)

    def inc_priority(self):
        new_char = chr(ord(self.priority) - 1)

        if new_char >= "A":
            self.set_priority(new_char)

    def dec_priority(self):
        new_char = chr(ord(self.priority) + 1)

        if new_char <= "Z":
            self.set_priority(new_char)

    def has_priority(self):
        return self.priority is not None

    def set_creation_date(self, date=None):
        if date is None:
            date = datetime.date.today()

        self.created = format_timestamp(date)

    def unset_creation_date(self):
        self.created = None

    def set_completion_date(self, date=None):
        if date is None:
            date = datetime.date.today()

        self.completed = format_timestamp(date)

    def unset_completion_date(self):
        self.completed = None


class Description(object):

    def __init__(self, description):
        if not description:
            raise ValueError("Description must not be None")

        self.__description = description

    def __str__(self):
        return self.__description

    def __repr__(self):
        return "Description('%s')" % self.description

    def search_pattern(self, pattern):
        return re.search(pattern, self.__description)

    def has_pattern(self, pattern):
        return self.search_pattern(pattern) is not None

    def replace(self, pattern, replacement):
        self.__description = re.sub(pattern, replacement,
                                    self.__description)

    def has_project(self, project):
        return self.has_pattern("(\s|^)\+%s(\s|$)" % project)

    def has_context(self, context):
        return self.has_pattern("(\s|^)@%s(\s|$)" % context)

    def has_kv_pair(self, key):
        return self.has_pattern("(\s|^)%s:\S+(\s|$)" % key)

    def strip(self, chars=None):
        self.__description = self.__description.strip(chars)

    def lstrip(self, chars=None):
        self.__description = self.__description.lstrip(chars)

    def rstrip(self, chars=None):
        self.__description = self.__description.rstrip(chars)

    def add_block(self, text):
        self.rstrip()
        self.__description += " " + text
        self.lstrip()

    def add_project(self, project):
        project = project.lstrip("+")
        require_no_spaces(project, "Project must not contain spaces")

        if self.has_project(project):
            return

        self.add_block("+" + project)

    def remove_project(self, project):
        project = project.lstrip("+")
        require_no_spaces(project, "Project must not contain spaces")

        if not self.has_project(project):
            return

        self.replace("(\s|^)\+%s(\s|$)" % project, " ")
        self.strip()

    def add_context(self, context):
        context = context.lstrip("@")
        require_no_spaces(context, "Context must not contain spaces")

        if self.has_context(context):
            return

        self.add_block("@" + context)

    def remove_context(self, context):
        context = context.lstrip("@")
        require_no_spaces(context, "Context must not contain spaces")

        if not self.has_context(context):
            return

        self.replace("(\s|^)@%s(\s|$)" % context, " ")
        self.strip()

    def set_key_value_pair(self, key, value):
        require_no_spaces(key, "Key must not contain spaces")
        require_no_spaces(value, "Value must not contain spaces")

        if not self.has_kv_pair(key):
            self.add_block("%s:%s" % (key, value))
        else:
            self.replace("(\s|^)%s:\S+(\s|$)" % key,
                         " %s:%s " % (key, value))
            self.strip()

    def remove_key_value_pair(self, key):
        require_no_spaces(key, "Key must not contain spaces")

        if not self.has_kv_pair(key):
            return

        self.replace("(\s|^)%s:\S+(\s|$)" % key, " ")
        self.strip()


class TaskFile(object):
    def __init__(self, path):
        self.__path = path
        self.__tasks = []

    def __enter__(self):
        self.read()
        return self

    def __exit__(self, type, value, traceback):
        self.write()

    def read(self):
        with open(self.__path) as task_file:
            for line in task_file.readlines():
                self.__tasks.append(Task.parse(line))

        self.__tasks = list(filter((None).__ne__, self.__tasks))

    def write(self):
        with open(self.__path, mode='w') as task_file:
            for task in self.__tasks:
                task_file.write(str(task) + "\n")

    def get_task(self, i):
        return self.__tasks[i-1]

    def sort(self):
        self.sort_by_description()
        self.sort_by_priority()

    def sort_by_description(self):
        self.__tasks.sort(key=lambda task: str(task.description).lower())

    def sort_by_priority(self):
        self.__tasks.sort(key=lambda task: "" if task.priority is None
                          else task.priority)
        self.__tasks.sort(key=lambda task: task.priority is None)
