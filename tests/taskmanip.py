#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test cases for functions that perform API calls to Habitica.
"""

import unittest

import helpers

import habitica
import habitica.taskmanip


def setUpModule():
    """Make sure the developer configured a test account, and nuke it."""
    sys.argv = ['habitica', '-t', 'status']
    try:
        habitica.cli()
    except:
        print("Could not find test_auth.cfg file! Create one in the same "
              "directory as auth.cfg.")
        sys.exit(1)

    sys.argv = ['habitica', '-t', 'reset']
    try:
        habitica.cli()  # TODO: exit if the user answers no to this
    except SystemExit:
        print("NOT wiping the user account, so tests will not proceed.")
        sys.exit(0)


if __name__ == '__main__':
    unittest.main()
