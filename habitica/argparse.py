#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Methods for processing user-provided arguments.
"""

import logging

# https://trello.com/c/4C8w1z5h/17-task-difficulty-settings-v2-priority-multiplier
PRIORITY = {'easy': 1,
            'medium': 1.5,
            'hard': 2}

# Dictionary between user arguments and corresponding
# field in a JSON Habitica API request.
TASK_FIELDS = {'--text': 'text',
               '--notes': 'notes',
               '--checklist': 'collapseChecklist',
               '--difficulty': 'priority',
               '--date': 'date', }


def task_type_from_args(args, grammatical_number):
    """
    Return the user's requested task type from command-line args.

    Habitica names these fields differently depending on what type of
    API call you're making, e.g. when creating a task, these strings
    should be singular; but when getting all tasks of a particular type,
    these strings should be plural.

    Valid `grammatical_number` values are 'singular' and 'plural'.
    """

    if grammatical_number == 'singular':
        if args['todos']:
            return 'todo'
        if args['habits']:
            return 'habit'
        if args['dailies']:
            return 'daily'
        raise Exception("No task type provided!")
    elif grammatical_number == 'plural':
        if args['todos']:
            return 'todos'
        if args['habits']:
            return 'habits'
        if args['dailies']:
            return 'dailys'
        raise Exception("No task type provided!")

    raise Exception("Bad grammatical number! Accepted values are "
                    "'singular' and 'plural'.")


def parse_list_indices(tids):
    """
    handle task-id formats such as:
        habitica todos done 3
        habitica todos done 1,2,3
        habitica todos done 1-3,5
        habitica tags delete 1-3

    `tids` is a string consisting of comma-separated tokens that can be:
    - A single number (e.g. '3')
    - A range of numbers (e.g. '1-3')
    """
    logging.debug('raw task ids: %s' % tids)
    task_ids = []
    for token in tids.split(','):
        if '-' in token:
            start, stop = [int(e) for e in token.split('-')]
            if start > stop:
                start, stop = stop, start
            task_ids.extend(range(start, stop + 1))
        elif token == '':
            return []
        else:
            task_ids.append(int(token))

    return [e - 1 for e in set(task_ids)]


def parse_list_strings(tstrs):
    """
    handle task/tag names such as:
        habitica tags delete Work,School
        habitica tags rename Home --text="Housekeeping"

    `tstrs` is a string of comma-separated strings.
    """
    logging.debug('raw task names: %s' % tstrs)
    if tstrs == '':
        return []
    return tstrs.split(',')


def fields_from_args(args):
    """
    Extract the fields from user-supplied arguments

    Takes in user-supplied arguments from docopt and grabs any task fields
    it contains. Stores them in a dictionary whose keys are the names
    of those fields as they would be given in a request to the Habitica
    API.

    Does NOT retrieve the type of task being modified (e.g. 'todo', 'habit',
    etc.). See `task_type_from_args(args)`.

    e.g.
    Possible Input:

        {'--date': None,
         '--debug': False,
         '--difficulty': 'easy',
         '--help': False,
         '--notes': None,
         '--tags': 'foo,bar',
         '--text': 'Count to three',
         '--verbose': False,
         '--version': False, }

    Output:
        {'difficulty': 'easy',
         'tags': 'foo,bar',
         'text': 'Count to three', }
    """

    fields_and_values = {}
    for arg, field in TASK_FIELDS.items():
        if arg in args:
            if arg == '--difficulty':
                # Needs to be converted to a numerical value
                new_val = PRIORITY[args[arg]]
            else:
                new_val = args[arg]
            fields_and_values[field] = new_val

    return fields_and_values
