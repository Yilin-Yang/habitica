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


TASK_TYPES = ('todos', 'dailies', 'habits',)
ELEMENT_TYPES = TASK_TYPES + ('tags',)


class TestTagManipulation(helpers.TerminalOutputTestCase):

    to_add = ['foo', 'bar', 'moo', 'gar', 'mar']

    def test_tag_manip(self):
        # Test adding tags
        for tag in TestTagManipulation.to_add:
            output = self.callScriptTesting(
                *TestTagManipulation._add_tag_args(tag))

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
        return ('habitica', '-t', 'tags', 'add', '--text=%s' % tag_name,)

    @staticmethod
    def _delete_tag_args(ids_or_names):
        """Produce command line arguments to delete a tag."""
        return ('habitica', '-t', 'tags', 'delete', ids_or_names)


def setUpModule():
    """Make sure the developer configured a test account, and nuke it."""
    try:  # TODO: causes double-printing. Is there a better way to do this?
        helpers.runCmdLineAndRedirect(habitica.cli,
                                      'habitica',
                                      '-t',
                                      'status')
    except:
        print("Could not find test_auth.cfg file! Create one in the same "
              "directory as auth.cfg.")
        sys.exit(1)

    sys.argv = ['habitica', '-t', 'reset']
    try:
        # Nuke the test account in its entirety.
        habitica.cli()
        deleteAllTags()
        verifyAccountEmpty()
    except SystemExit:
        print("NOT wiping the user account, so tests will not proceed.")
        sys.exit(0)


def deleteAllTags():
    """
    Delete all tags from the test account.

    This is still needed as an additional step, since tags persist across
    account resets.
    """
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


def verifyAccountEmpty():
    """Verify that the test account is empty of tasks and tags."""
    for elt_type in ELEMENT_TYPES:
        output = helpers.runCmdLineAndRedirect(habitica.cli,
                                               'habitica',
                                               '-t',
                                               elt_type)
        assert(not output)
    return


if __name__ == '__main__':
    unittest.main()
