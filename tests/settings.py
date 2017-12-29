#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Finds the absolute filepath of the development habitica module and imports it.
"""

import sys
import os


def _stripNFields(filepath, fields):
    """Remove everything to the right of the rightmost slash, and the slash."""
    return filepath.rsplit('/', fields)[0]  # TODO: make this work on Windows


def _getProjectRootDirectory():
    """Get the repository's root directory."""
    return _stripNFields(os.path.realpath(__file__), 2)


PROJECT_ROOT = _getProjectRootDirectory()
sys.path.insert(0, PROJECT_ROOT)  # import from project directory first
