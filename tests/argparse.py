#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test cases for methods used for parsing user arguments.
"""

import os
import sys
import unittest

# Make sure we're using dev files, not the installed package
sys.path.insert(0, os.path.abspath('..'))
import habitica
import habitica.argparse


class TestFieldsFromArgs(unittest.TestCase):
    def test_field_extraction_only_valid(self):
        args = {'--date': '2017-12-01',
                '--difficulty': 'easy', }
        output = habitica.argparse.fields_from_args(args)
        self.assertTrue(output == {'date': '2017-12-01',
                                   'priority': 1, })

    def test_field_extraction_valid_and_invalid(self):
        args = {'--date': '2017-12-01',
                '--foo': None,
                '--difficulty': 'medium',
                '--bar': 123,
                '--barfoo': 'abcde', }
        output = habitica.argparse.fields_from_args(args)
        self.assertTrue(output == {'date': '2017-12-01',
                                   'priority': 1.5, })

    def test_field_extraction_only_invalid(self):
        args = {'--foo': None,
                '--bar': 123,
                '--barfoo': 'abcde', }
        output = habitica.argparse.fields_from_args(args)
        self.assertFalse(output)


class TestTaskTypeFromArgs(unittest.TestCase):

    def test_todos(self):
        args = {'--checklist': None,
                '--checklists': False,
                '--date': None,
                '--debug': False,
                '--difficulty': 'easy',
                '--help': False,
                '--notes': None,
                '--tags': None,
                '--text': None,
                '--verbose': False,
                '--version': False,
                'dailies': False,
                'edit': False,
                'habits': False,
                'task-ids': False,
                'todos': True}      # User requests todos
        output = habitica.argparse.task_type_from_args(args, 'singular')
        self.assertTrue(output == 'todo')

        output = habitica.argparse.task_type_from_args(args, 'plural')
        self.assertTrue(output == 'todos')

    def test_habits(self):
        args = {'--checklist': None,
                '--checklists': False,
                '--date': None,
                '--debug': False,
                '--difficulty': 'easy',
                '--help': False,
                '--notes': None,
                '--tags': None,
                '--text': None,
                '--verbose': False,
                '--version': False,
                'dailies': False,
                'edit': False,
                'habits': True,     # User requests habits
                'task-ids': False,
                'todos': False}
        output = habitica.argparse.task_type_from_args(args, 'singular')
        self.assertTrue(output == 'habit')

        output = habitica.argparse.task_type_from_args(args, 'plural')
        self.assertTrue(output == 'habits')

    def test_dailies(self):
        args = {'--checklist': None,
                '--checklists': False,
                '--date': None,
                '--debug': False,
                '--difficulty': 'easy',
                '--help': False,
                '--notes': None,
                '--tags': None,
                '--text': None,
                '--verbose': False,
                '--version': False,
                'dailies': True,    # User requests dailies
                'edit': False,
                'habits': False,
                'task-ids': False,
                'todos': False}
        output = habitica.argparse.task_type_from_args(args, 'singular')
        self.assertTrue(output == 'daily')

        output = habitica.argparse.task_type_from_args(args, 'plural')
        self.assertTrue(output == 'dailys')

    def test_no_type(self):
        args = {'--checklist': None,
                '--checklists': False,
                '--date': None,
                '--debug': False,
                '--difficulty': 'easy',
                '--help': False,
                '--notes': None,
                '--tags': None,
                '--text': None,
                '--verbose': False,
                '--version': False,
                'dailies': False,
                'edit': False,
                'habits': False,
                'task-ids': False,
                'todos': False}
        # User did not provide a task type.
        with self.assertRaises(Exception):
            habitica.argparse.task_type_from_args(args, 'singular')
        with self.assertRaises(Exception):
            habitica.argparse.task_type_from_args(args, 'plural')

    def test_bad_grammatical_number(self):
        args = {'--checklist': None,
                '--checklists': False,
                '--date': None,
                '--debug': False,
                '--difficulty': 'easy',
                '--help': False,
                '--notes': None,
                '--tags': None,
                '--text': None,
                '--verbose': False,
                '--version': False,
                'dailies': False,
                'edit': False,
                'habits': False,
                'task-ids': False,
                'todos': True}      # User requests todos
        with self.assertRaises(Exception):
            habitica.argparse.task_type_from_args(args, 'singulra')


class TestParseListIndices(unittest.TestCase):

    def test_standard_input(self):
        task_ids = '1,2-3,9,15-17'
        output = habitica.argparse.parse_list_indices(task_ids)
        self.assertTrue(output == [0, 1, 2, 8, 14, 15, 16])

    def test_empty(self):
        task_ids = ''
        output = habitica.argparse.parse_list_indices(task_ids)
        self.assertTrue(output == [])

    def test_one_value(self):
        task_ids = '23'
        output = habitica.argparse.parse_list_indices(task_ids)
        self.assertTrue(output == [22])

    def test_out_of_order(self):
        task_ids = '17, 1, 5-3'
        output = habitica.argparse.parse_list_indices(task_ids)
        output.sort()  # not guaranteed to return a sorted list
        self.assertTrue(output == [0, 2, 3, 4, 16])


class TestParseListStrings(unittest.TestCase):

    def test_standard_input(self):
        task_strings = 'foo,bar,moo,gar'
        output = habitica.argparse.parse_list_strings(task_strings)
        self.assertTrue(output == ['foo', 'bar', 'moo', 'gar'])

    def test_empty(self):
        task_strings = ''
        output = habitica.argparse.parse_list_strings(task_strings)
        self.assertTrue(output == [])

    def test_one_value(self):
        task_strings = 'foo'
        output = habitica.argparse.parse_list_strings(task_strings)
        self.assertTrue(output == ['foo'])


if __name__ == '__main__':
    unittest.main()
