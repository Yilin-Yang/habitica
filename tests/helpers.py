#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Convenience functions for evaluating test output.
"""

from StringIO import StringIO
import unittest
import sys

import settings  # use development code, not globally installed packages
import habitica


def runAndRedirect(to_run, *args, **kwargs):
    """
    Call the to_run object, returning everything it printed from stdout.

    This redirects ALL output from stdout for the duration of the
    function call.
    """
    assert(callable(to_run))
    term_output = _redirectStdout()
    to_run(*args, **kwargs)
    output = _getStringAndClose(term_output)
    _resetStdout()
    return output


def _redirectStdout():
    """Redirect terminal output to a StringIO object."""
    term_output = StringIO()
    sys.stdout = term_output
    return term_output


def _resetStdout():
    """Without doing this, assertions that compare strings seem to fail."""
    sys.stdout = sys.__stdout__


def _getStringAndClose(io):
    """Yank and return the contents of the StringIO object and close it."""
    output = io.getvalue()
    io.close()
    return output


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
        sys.argv = cli_args
        return runAndRedirect(habitica.cli)

    def callScriptTesting(self, *cli_args):
        """Safer version of callScript that always sends a '--test' flag."""
        if '-t' not in cli_args and '--test' not in cli_args:
            cli_args = ('-t',) + cli_args
        return self.callScript(*cli_args)

    def callFunction(self, function, *func_args):
        """
        Call function with the given arguments and store the output.

        Args:
            *func_args (:obj:`list` of :obj:`str`): Variable length argument
                list of the arguments you want to pass to the given function.
        """
        return runAndRedirect(function, *func_args)
