#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    import habitica
except ImportError:
    import sys
    import os
    sys.path.insert(0, os.path.abspath('..'))
    import habitica


def test_field_extraction_only_valid():
    args = {'--date': '2017-12-01',
            '--difficulty': 'medium',
            '--tags': 'alice,bob', }
    assert(habitica.core.extract_fields(args)
           == {'date': '2017-12-01',
               'difficulty': 'medium',
               'tags': 'alice,bob'})


def test_field_extraction_valid_and_invalid():
    args = {'--date': '2017-12-01',
            '--foo': None,
            '--difficulty': 'medium',
            '--bar': 123,
            '--barfoo': 'abcde',
            '--tags': 'alice,bob', }
    assert(habitica.core.extract_fields(args)
           == {'date': '2017-12-01',
               'difficulty': 'medium',
               'tags': 'alice,bob'})


def test_field_extraction_only_invalid():
    args = {'--foo': None,
            '--bar': 123,
            '--barfoo': 'abcde', }
    assert(habitica.core.extract_fields(args).empty())


if __name__ == '__main__':
    test_field_extraction_only_valid()
    test_field_extraction_valid_and_invalid()
    print("All tests passed!")
