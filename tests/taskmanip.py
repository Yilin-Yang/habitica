#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test cases for functions that perform API calls to Habitica.
"""

import sys
import unittest

import helpers

import habitica
import habitica.taskmanip


class TestTagManipulation(helpers.TerminalOutputTestCase):

    to_add = ['foo', 'bar', 'moo', 'gar', 'mar']

    def test_tag_manip(self):
        # Test adding tags
        for tag in TestTagManipulation.to_add:
            output = self.callScriptTesting(
                *TestTagManipulation._add_tag_args(tag))

        print(output)  # TODO: remove debug
        self.assertTrue(output == ('[#] 1 foo\n'
                                   '[#] 2 bar\n'
                                   '[#] 3 moo\n'
                                   '[#] 4 gar\n'
                                   '[#] 5 mar\n'
                                   )
                        )

        # Test removing tags by name
        output = self.callScriptTesting(
            *TestTagManipulation._delete_tag_args('moo'))

        self.assertTrue(output == ('[#] 1 foo\n'
                                   '[#] 2 bar\n'
                                   '[#] 3 gar\n'
                                   '[#] 4 mar\n'
                                   )
                        )

        # Test removing tags by index
        output = self.callScriptTesting(
            *TestTagManipulation._delete_tag_args('2,4'))

        self.assertTrue(output == ('[#] 1 foo\n'
                                   '[#] 2 gar\n'
                                   )
                        )

        # Test removing multiple tags by name
        output = self.callScriptTesting(
            *TestTagManipulation._delete_tag_args('foo,gar'))

        self.assertTrue(output == '')

    @staticmethod
    def _add_tag_args(tag_name):
        """Produce command line arguments to add a tag with a given name."""
        return ('habitica', '-t', 'tags', 'add', '--text="%s"' % tag_name,)

    @staticmethod
    def _delete_tag_args(ids_or_names):
        """Produce command line arguments to delete a tag."""
        return ('habitica', '-t', 'tags', 'delete', ids_or_names)


def setUpModule():
    """Make sure the developer configured a test account, and nuke it."""
    sys.argv = ['habitica', '-t', 'status']
    try:  # TODO: causes double-printing. Is there a better way to do this?
        habitica.cli()
    except:
        print("Could not find test_auth.cfg file! Create one in the same "
              "directory as auth.cfg.")
        sys.exit(1)

    sys.argv = ['habitica', '-t', 'reset']
    try:
        habitica.cli()  # TODO: exit if the user answers no to this
        deleteAllTags()
    except SystemExit:
        print("NOT wiping the user account, so tests will not proceed.")
        sys.exit(0)


def deleteAllTags():
    """Delete all tags from the test account."""
    tag_output = helpers.runCmdLineAndRedirect(habitica.cli,
                                               'habitica',
                                               '-t',
                                               'tags')
    if not tag_output:
        # Tag list is already empty
        return

    # Parse the tag list output to find last tag number
    last_item = tag_output[tag_output.rfind('\n[#] '):]
    last_no = last_item.split(' ')[1]

    tag_output = helpers.runCmdLineAndRedirect(habitica.cli,
                                               'habitica',
                                               '-t',
                                               'tags',
                                               'delete',
                                               '1-%s' % last_no)


if __name__ == '__main__':
    unittest.main()
