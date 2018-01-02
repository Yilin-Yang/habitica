#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Methods for getting, parsing, and editing Habitica tasks.
"""

from . import argparse


def add_tag(hbt, args):
    """Construct a tag of the given type and then publish it."""
    hbt.user.tags(name=args['--text'],
                  _method='post')


def delete_tags(hbt, args):
    """Apply the user-requested changes to all of the given tags."""

    # Populate a list with JSON API requests
    to_delete = get_these_tags(hbt, args)

    for t in to_delete:
        t['_method'] = 'delete'
        hbt.user.tags(**t)


def rename_tag(hbt, args):
    tags = get_these_tags(hbt, args)
    if len(tags) > 1:
        raise ValueError("Can't rename multiple tags at once!")
    tag_fields = tags[0]
    tag_fields['_method'] = 'put'
    tag_fields['name'] = args['--text']
    hbt.user.tags(**tag_fields)


def write_new_fields(task_json, new_vals):
    """Write new field values to a JSON file and return it"""
    for field, new_val in new_vals.items():
        task_json[field] = new_val
    return task_json


def get_tasks(hbt, task_type):
    """
    Return a list of tasks, from Habitica, of the requested type.

    e.g.
        get_tasks(hbt, 'habits')    # returns list of JSON habits for user
        get_tasks(hbt, 'todos')     # ditto, for todos
        get_tasks(hbt, 'dailys')    # ditto, for dailies
    """
    tasks = hbt.user.tasks(type=task_type)
    return tasks


def get_tags(hbt):
    """Return all of the user's tags."""
    return hbt.user.tags()


def add_task(hbt, args):
    """Construct a new task of the given type and publish it."""

    # Build a JSON API request as we go.
    task_fields = {}

    task_fields['text'] = args['--text']
    task_fields['type'] = argparse.task_type_from_args(args, 'singular')
    write_new_fields(task_fields, argparse.fields_from_args(args))
    task_fields['_method'] = 'post'

    hbt.user.tasks(**task_fields)


# TODO: figure out a more elegant way to implement this
def bulk_edit_tasks(hbt, action, args):
    """Apply the user-requested changes to all of the given tasks."""

    task_type = argparse.task_type_from_args(args, 'plural')
    cur_tasks = get_tasks(hbt, task_type)

    tids = argparse.parse_list_indices(args['<task-ids>'])
    for tid in tids:
        task_fields = cur_tasks[tid]
        if action == 'delete':
            task_fields['_method'] = 'delete'
        elif action == 'up' or action == 'down':
            # Habits, dailies, and todos are all checked with "up"
            # and unchecked/decremented with "down"
            task_fields['_direction'] = action
            task_fields['_method'] = 'post'
        elif action == 'edit':
            write_new_fields(task_fields, argparse.fields_from_args(args))
            task_fields['_method'] = 'put'

        hbt.user.tasks(**task_fields)


def move_tasks(hbt, args):
    """
    Move given tasks to requested position, maintaining their relative order.

    Given the following task list:
        [1]
        [2]
        [3]
        [4]
        [5]

    This command:
        habitica [task] move 1,4-5 2

    Will rearrange the list like so:
        [2]
        [1]
        [4]
        [5]
        [3]
    """
    task_type = argparse.task_type_from_args(args, 'plural')
    cur_tasks = get_tasks(hbt, task_type)
    new_pos = str(int(args['<new-pos>']) - 1)
    tids = argparse.parse_list_indices(args['<task-ids>'])
    for tid in reversed(tids):
        task_fields = cur_tasks[tid]
        task_fields['_method'] = 'post'
        task_fields['_position'] = new_pos
        hbt.user.tasks(**task_fields)


def get_these_tags(hbt, args):
    """Return the tags corresponding to these indices or names."""
    cur_tags = get_tags(hbt)
    ret_tags = []
    try:
        # parse_list_indices fails if given tag names
        tids = argparse.parse_list_indices(args['<task-ids>'])
        for i in tids:
            ret_tags.append(cur_tags[i])

    except ValueError:
        if ret_tags:
            raise Exception("Combined numerical and string-based indexing!")
        tstrs = argparse.parse_list_strings(args['<task-ids>'])
        for s in tstrs:
            for tag in cur_tags:
                if s == tag['name']:
                    ret_tags.append(tag)
                    break

    return ret_tags
