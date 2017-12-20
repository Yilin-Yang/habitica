#!/usr/bin/env python
# -*- coding: utf-8 -*-

from StringIO import StringIO
import os
import sys
import unittest

# Make sure we're using dev files, not the installed package
sys.path.insert(0, os.path.abspath('..'))
import habitica
import habitica.core


class TestFieldsFromArgs(unittest.TestCase):
    def test_field_extraction_only_valid(self):
        args = {'--date': '2017-12-01',
                '--difficulty': 'easy', }
        output = habitica.core.fields_from_args(args)
        self.assertTrue(output == {'date': '2017-12-01',
                                   'priority': 1, })

    def test_field_extraction_valid_and_invalid(self):
        args = {'--date': '2017-12-01',
                '--foo': None,
                '--difficulty': 'medium',
                '--bar': 123,
                '--barfoo': 'abcde', }
        output = habitica.core.fields_from_args(args)
        self.assertTrue(output == {'date': '2017-12-01',
                                   'priority': 1.5, })

    def test_field_extraction_only_invalid(self):
        args = {'--foo': None,
                '--bar': 123,
                '--barfoo': 'abcde', }
        output = habitica.core.fields_from_args(args)
        self.assertFalse(output)


class TestInfoPrintOptions(unittest.TestCase):

    term_output = StringIO()

    def setUp(self):
        """Redirect terminal output to a StringIO object."""
        self.term_output = StringIO()
        sys.stdout = self.term_output

    def tearDown(self):
        self.term_output.close()

    def callScript(self, *args):
        sys.argv = args
        habitica.cli()
        sys.stdout = sys.__stdout__  # Without this, assertions fail
        return self.term_output.getvalue()

    def test_server_option(self):
        output = self.callScript('habitica', 'server')
        self.assertTrue(output == 'Habitica server is up\n'
                        or output == ('Habitica server down... '
                                      'or your computer cannot connect\n'))

    def test_user_status(self):
        output = self.callScript('habitica', 'status')

        # Search for keywords that we'd find in a status message
        self.assertTrue('Health:' in output
                        and 'XP:' in output
                        and 'Party:' in output
                        and 'Level ' in output)


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
        output = habitica.core.task_type_from_args(args, 'singular')
        self.assertTrue(output == 'todo')

        output = habitica.core.task_type_from_args(args, 'plural')
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
        output = habitica.core.task_type_from_args(args, 'singular')
        self.assertTrue(output == 'habit')

        output = habitica.core.task_type_from_args(args, 'plural')
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
        output = habitica.core.task_type_from_args(args, 'singular')
        self.assertTrue(output == 'daily')

        output = habitica.core.task_type_from_args(args, 'plural')
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
            habitica.core.task_type_from_args(args, 'singular')
        with self.assertRaises(Exception):
            habitica.core.task_type_from_args(args, 'plural')

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
            habitica.core.task_type_from_args(args, 'singulra')


class TestWriteNewFields(unittest.TestCase):

    def setUp(self):
        self.cur_vals = {'name': 'moo',
                         'holy': 'mail',
                         'may': 'may'}
        self.correct = self.cur_vals  # modify in test-case

    def test_standard_input(self):
        new_vals = {'name': 'foo',
                    'holy': 'grail'}
        self.correct = new_vals
        self.correct['may'] = 'may'

        output = habitica.core.write_new_fields(self.cur_vals, new_vals)

        self.assertTrue(output == self.correct)

    def test_null_input(self):
        new_vals = {}
        output = habitica.core.write_new_fields(self.cur_vals, new_vals)
        self.assertTrue(output == self.correct)

    def test_one_replacement(self):
        new_vals = {'name': 'foo'}
        self.correct['name'] = 'foo'

        output = habitica.core.write_new_fields(self.cur_vals, new_vals)
        self.assertTrue(output == self.correct)

    def test_total_replacement(self):
        new_vals = {'name': 'foo',
                    'holy': 'grail',
                    'may': 'bae'}
        self.correct = new_vals

        output = habitica.core.write_new_fields(self.cur_vals, new_vals)

        self.assertTrue(output == self.correct)


class TestParseListIndices(unittest.TestCase):

    def test_standard_input(self):
        task_ids = '1,2-3,9,15-17'
        output = habitica.core.parse_list_indices(task_ids)
        self.assertTrue(output == [0, 1, 2, 8, 14, 15, 16])

    def test_empty(self):
        task_ids = ''
        output = habitica.core.parse_list_indices(task_ids)
        self.assertTrue(output == [])

    def test_one_value(self):
        task_ids = '23'
        output = habitica.core.parse_list_indices(task_ids)
        self.assertTrue(output == [22])

    def test_out_of_order(self):
        task_ids = '17, 1, 5-3'
        output = habitica.core.parse_list_indices(task_ids)
        output.sort()  # not guaranteed to return a sorted list
        self.assertTrue(output == [0, 2, 3, 4, 16])


class TestParseListStrings(unittest.TestCase):

    def test_standard_input(self):
        task_strings = 'foo,bar,moo,gar'
        output = habitica.core.parse_list_strings(task_strings)
        self.assertTrue(output == ['foo', 'bar', 'moo', 'gar'])

    def test_empty(self):
        task_strings = ''
        output = habitica.core.parse_list_strings(task_strings)
        self.assertTrue(output == [])

    def test_one_value(self):
        task_strings = 'foo'
        output = habitica.core.parse_list_strings(task_strings)
        self.assertTrue(output == ['foo'])


class TestPrintTasks(unittest.TestCase):

    task_1 = {
        u'attribute': u'str',
        u'checklist': [],
        u'group':
            {u'approval':
                {u'requested': False,
                 u'required': False,
                 u'approved': False},
                u'assignedUsers': []},
        u'collapseChecklist': False,
        u'tags': [],
        u'text': u'foo',
        u'challenge': {},
        u'userId': u'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
        u'value': -1,
        u'id': u'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
        u'priority': 1,
        u'completed': False,
        u'notes': u'',
        u'updatedAt': u'2017-12-06T14:47:58.370 Z',
        u'_id': u'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
        u'type': u'todo',
        u'reminders': [],
        u'createdAt': u'2017-12-06T05:31:47.433Z'
    }

    task_2 = {
        u'attribute': u'str',
        u'checklist': [],
        u'group':
            {u'approval':
                {u'requested': False,
                 u'required': False,
                 u'approved': False},
                u'assignedUsers': []},
        u'collapseChecklist': False,
        u'tags': [],
        u'text': u'bar',
        u'challenge': {},
        u'userId': u'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
        u'value': -1,
        u'id': u'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
        u'priority': 1,
        u'completed': False,
        u'notes': u'',
        u'updatedAt': u'2017-12-06T14:47:58.370 Z',
        u'_id': u'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
        u'type': u'todo',
        u'reminders': [],
        u'createdAt': u'2017-12-06T05:31:47.433Z'
    }

    def setUp(self):
        """Redirect terminal output to a StringIO object."""
        self.term_output = StringIO()
        sys.stdout = self.term_output

    def tearDown(self):
        self.term_output.close()

    def callFunction(self, task_list):
        habitica.core.print_task_list(task_list)
        sys.stdout = sys.__stdout__  # Without this, assertions fail
        return self.term_output.getvalue()

    def test_empty(self):
        task_list = []
        output = self.callFunction(task_list)
        self.assertTrue(output == '')

    def test_single(self):
        output = self.callFunction([self.task_1])
        self.assertTrue(output == '[ ] 1 foo\n')

    def test_standard(self):
        output = self.callFunction([self.task_1, self.task_2])
        self.assertTrue(output == ('[ ] 1 foo\n'
                                   '[ ] 2 bar\n'))

    # TODO: add test cases for printing with checklists


class TestPrintTags(unittest.TestCase):

    tag_1 = {u'name': u'foo',
             u'id': u'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'}

    tag_2 = {u'name': u'bar',
             u'id': u'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'}

    def setUp(self):
        """Redirect terminal output to a StringIO object."""
        self.term_output = StringIO()
        sys.stdout = self.term_output

    def tearDown(self):
        self.term_output.close()

    def callFunction(self, tag_list):
        habitica.core.print_tags_list(tag_list)
        sys.stdout = sys.__stdout__  # Without this, assertions fail
        return self.term_output.getvalue()

    def test_empty(self):
        output = self.callFunction([])
        self.assertTrue(output == '')

    def test_single(self):
        output = self.callFunction([self.tag_1])
        self.assertTrue(output == '[#] 1 foo\n')

    def test_standard(self):
        output = self.callFunction([self.tag_1, self.tag_2])
        self.assertTrue(output == ('[#] 1 foo\n'
                                   '[#] 2 bar\n'))


if __name__ == '__main__':
    unittest.main()
