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


class TestFieldExtraction(unittest.TestCase):
    def test_field_extraction_only_valid(self):
        args = {'--date': '2017-12-01',
                '--difficulty': 'medium',
                '--tags': 'alice,bob', }
        self.assertTrue(habitica.core.extract_fields(args)
                        == {'date': '2017-12-01',
                            'difficulty': 'medium',
                            'tags': 'alice,bob'})

    def test_field_extraction_valid_and_invalid(self):
        args = {'--date': '2017-12-01',
                '--foo': None,
                '--difficulty': 'medium',
                '--bar': 123,
                '--barfoo': 'abcde',
                '--tags': 'alice,bob', }
        self.assertTrue(habitica.core.extract_fields(args)
                        == {'date': '2017-12-01',
                            'difficulty': 'medium',
                            'tags': 'alice,bob'})

    def test_field_extraction_only_invalid(self):
        args = {'--foo': None,
                '--bar': 123,
                '--barfoo': 'abcde', }
        self.assertFalse(habitica.core.extract_fields(args))


class TestInfoPrintOptions(unittest.TestCase):

    term_output = StringIO()

    def setUp(self):
        self.term_output = StringIO()
        sys.stdout = self.term_output

    def tearDown(self):
        self.term_output.close()

    def callScript(self, *args):
        sys.argv = args
        habitica.cli()
        sys.stdout = sys.__stdout__
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


if __name__ == '__main__':
    unittest.main()
