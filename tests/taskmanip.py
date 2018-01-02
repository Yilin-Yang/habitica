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

TASK_FIELDS = ('--text',
               '--notes',
               '--date',
               '--tags',
               '--difficulty',
               )


def _add_tag_args(tag_name):
    """Produce command line arguments to add a tag with a given name."""
    return ('habitica', '-t', 'tags', 'add', '--text=%s' % tag_name,)


def _delete_tag_args(ids_or_names):
    """Produce command line arguments to delete a tag."""
    return ('habitica', '-t', 'tags', 'delete', ids_or_names)


def _task_manip_args(task_type, command, tids, **kwargs):
    """
    Produce command line arguments to add/edit/delete a task.

    To specify fields, use kwargs.

        _task_manip_args('todos', 'add', None
                         **{'--text':'Foo',
                            '--date':'2017-12-01'})
        Returns:
            ['habitica',
             '-t',
             'todos',
             'add',
             '--text=Foo',
             '--date='2017-12-01']

        _task_manip_args('dailies', 'edit', '1-3',
                         **{'--date':'2017-12-01'})
        Returns:
            ['habitica',
             '-t',
             'dailies',
             'edit',
             '1-3',
             '--date='2017-12-01']

    """
    args = ['habitica',
            '-t',
            task_type,
            command]

    if tids is not None:
        if command == 'add':
            raise ValueError("Can't specify tids with add command.")
        assert(isinstance(tids, basestring))
        args.append(tids)

    for field in TASK_FIELDS:
        if field in kwargs:
            args.append('%s=%s' % (field,
                                   kwargs.pop(field)))
    if kwargs:
        raise ValueError("Invalid fields: %s" % str(kwargs))

    return args


class TestTagManipulation(helpers.TerminalOutputTestCase):

    to_add = ['foo', 'bar', 'moo', 'gar', 'mar']

    def test_tag_manip(self):
        # Test adding tags
        for tag in TestTagManipulation.to_add:
            output = self.callScriptTesting(
                *_add_tag_args(tag))

        self.assertTrue(output == ('[#] 1 foo\n'
                                   '[#] 2 bar\n'
                                   '[#] 3 moo\n'
                                   '[#] 4 gar\n'
                                   '[#] 5 mar\n'
                                   )
                        )

        # Test removing tags by name
        output = self.callScriptTesting(
            *_delete_tag_args('moo'))

        self.assertTrue(output == ('[#] 1 foo\n'
                                   '[#] 2 bar\n'
                                   '[#] 3 gar\n'
                                   '[#] 4 mar\n'
                                   )
                        )

        # Test removing tags by index
        output = self.callScriptTesting(
            *_delete_tag_args('2,4'))

        self.assertTrue(output == ('[#] 1 foo\n'
                                   '[#] 2 gar\n'
                                   )
                        )

        # Test removing multiple tags by name
        output = self.callScriptTesting(
            *_delete_tag_args('foo,gar'))

        self.assertTrue(output == '')


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
