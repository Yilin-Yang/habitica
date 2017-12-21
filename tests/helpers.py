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

    def callScript(self, *cli_args):
        """
        Pass the given input parameters to Habitica and store the output.

        Args:
            *cli_args (:obj:`list` of :obj:`str`): Variable length argument
                list of the flags you want to pass to the habitica script, e.g.
                    self.callScript('todos', 'add', '--text="foo"')
        """
        term_output = self._redirectStdout()

        sys.argv = cli_args
        habitica.cli()

        self._resetStdout()

        return self._getStringAndClose(term_output)

    def callScriptTesting(self, *cli_args):
        """Safer version of callScript that always sends a '--test' flag."""
        if '-t' not in cli_args and '--test' not in cli_args:
            cli_args.append('-t')
        return self.callScript(*cli_args)

    def callFunction(self, function, *func_args):
        """
        Call function with the given arguments and store the output.

        Args:
            *func_args (:obj:`list` of :obj:`str`): Variable length argument
                list of the arguments you want to pass to the given function.
        """
        term_output = self._redirectStdout()
        function(*func_args)
        self._resetStdout()

        return self._getStringAndClose(term_output)

    def _redirectStdout(self):
        """Redirect terminal output to a StringIO object."""
        term_output = StringIO()
        sys.stdout = term_output
        return term_output

    def _resetStdout(self):
        """Without doing this, assertions that compare strings fail?."""
        sys.stdout = sys.__stdout__

    def _getStringAndClose(self, io):
        """Yank and return the contents of the StringIO object and close it."""
        output = io.getvalue()
        io.close()
        return output
