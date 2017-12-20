#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test cases for miscellaneous functions that don't require API calls.
"""

from StringIO import StringIO
import os
import sys
import unittest

# Make sure we're using dev files, not the installed package
sys.path.insert(0, os.path.abspath('..'))
import habitica
import habitica.core
import habitica.taskmanip


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

        output = habitica.taskmanip.write_new_fields(self.cur_vals, new_vals)

        self.assertTrue(output == self.correct)

    def test_null_input(self):
        new_vals = {}
        output = habitica.taskmanip.write_new_fields(self.cur_vals, new_vals)
        self.assertTrue(output == self.correct)

    def test_one_replacement(self):
        new_vals = {'name': 'foo'}
        self.correct['name'] = 'foo'

        output = habitica.taskmanip.write_new_fields(self.cur_vals, new_vals)
        self.assertTrue(output == self.correct)

    def test_total_replacement(self):
        new_vals = {'name': 'foo',
                    'holy': 'grail',
                    'may': 'bae'}
        self.correct = new_vals

        output = habitica.taskmanip.write_new_fields(self.cur_vals, new_vals)

        self.assertTrue(output == self.correct)


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
