#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Convenience functions for evaluating test output.
"""

from StringIO import StringIO
import os
import sys
import unittest

# Make sure we're using dev files, not the installed package
sys.path.insert(0, os.path.abspath('..'))
import habitica


class TerminalOutputTestCase(unittest.TestCase):
    """
    Base class for unit tests that evaluate terminal output.

    Implements setUp and tearDown methods for redirecting terminal output
    to a StringIO object, as well as callScript/callFunction methods for
    returning the terminal output of the given script or function call as
    a string.
    """

    term_output = StringIO()

    def setUp(self):
        """Redirect terminal output to a StringIO object."""
        self.term_output = StringIO()
        sys.stdout = self.term_output

    def tearDown(self):
        self.term_output.close()

    def callScript(self, *cli_args):
        """Pass the given input parameters to Habitica and store the output."""
        sys.argv = cli_args
        habitica.cli()
        sys.stdout = sys.__stdout__  # Without this, assertions fail
        return self.term_output.getvalue()

    def callFunction(self, function, *func_args):
        """Call function with the given arguments and store the output."""
        function(*func_args)
        sys.stdout = sys.__stdout__  # Without this, assertions fail
        return self.term_output.getvalue()
