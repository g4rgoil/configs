#!/usr/bin/python

import re
import datetime


def format_timestamp(date) -> str:
    return date.strftime("%Y-%m-%d")


def require_no_white_space(string, msg):
    if re.search("\s", string) is not None:
        raise ValueError(msg)


class Task(object):
    def __init__(self, description, done=False, priority=None, completed=None,
                 created=None, projects=None, contexts=None, tags=None):
        self.done = done
        self.priority = priority
        self.completed = completed
        self.created = created
        self.description = description
        self.projects = projects if projects is not None else []
        self.contexts = contexts if contexts is not None else []
        self.key_value_tags = tags if tags is not None else {}

    def __str__(self):
        task = "x " if self.done else ""
        task += "(%s) " % self.priority if self.priority is not None else ""
        task += "%s " % self.completion if self.completion is not None else ""
        task += "%s " % self.creation if self.creation is not None else ""
        task += "%s" % self.description

    def __repr__(self):
        return self.__str__()

    @classmethod
    def parse(cls, task):
        task = task.strip()
        kwargs = dict()

        if task.startswith("x "):
            kwargs["done"] = True
            task = task[1:].lstrip()

        match = re.match(r"\(([A-Z])\) ", task)
        if match is not None:
            kwargs["priority"] = match.group(1)
            task = task[match.end():].lstrip()

        match = re.match(r"(%s) ((%s) )?" % r"\d{4}-\d{2}-\d{2}", task)
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
        kwargs["projects"] = cls.parse_projects(task)
        kwargs["contexts"] = cls.parse_contexts(task)
        kwargs["tags"] = cls.parse_key_value_pairs(task)

        return Task(**kwargs)

    @classmethod
    def parse_projects(cls, description):
        return [e[2:] for e in re.findall(r"\s\+\S+", description)]

    @classmethod
    def parse_contexts(cls, description):
        return [e[2:] for e in re.findall(r"\s@\S+", description)]

    @classmethod
    def parse_key_value_pairs(cls, description):
        return dict([e.lstrip().split(":") for e in
                     re.findall(r"\s\S+:\S+")])

    def do(self):
        self.done = True
        self.set_completion_date()

    def undo(self):
        self.done = False
        self.completed = None

    def set_priority(self, priority):
        if re.fullmatch("[A-Z]", priority):
            self.priority = priority
        else:
            raise ValueError("Not a valid priority " + priority)

    def inc_priority(self):
        new_char = chr(ord(self.priority) + 1)

        if new_char <= "Z":
            self.set_priority(new_char)

    def dec_priority(self):
        new_char = chr(ord(self.priority) - 1)

        if new_char >= "A":
            self.set_priority(new_char)

    def set_completion_date(self, date=None):
        if date is None:
            date = datetime.date.today()

        self.completed = format_timestamp(date)

    def set_creation_date(self, date=None):
        if date is None:
            date = datetime.date.today()

        self.created = format_timestamp(date)

    def add_project(self, project):
        project = project.lstrip("+")

        require_no_white_space(project, "Project must not contain"
                               "white spaces")

        if project in self.projects:
            return

        if self.description:
            self.description = self.description.rstrip()
            self.description += " "

        self.description += "+" + project
        self.projects.append(project)

    def remove_project(self, project):
        project = project.lstrip("+")

        if project not in self.projects:
            return

    def add_context(self, context):
        context = context.lstrip("@")

        if context in self.contexts:
            return

        if self.description:
            self.description = self.description.rstrip()
            self.description += " "

        self.description += "@" + context
        self.contexts.append(context)

    def remove_context(self):
        pass

    def add_key_value_pair(self):
        pass

    def remove_key_value_pair(self):
        pass
