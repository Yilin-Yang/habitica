#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Phil Adams http://philadams.net

habitica: commandline interface for http://habitica.com
http://github.com/philadams/habitica

TODO:philadams add logging to .api
TODO:philadams get logger named, like requests!
"""


from bisect import bisect
import json
import logging
import os.path
from time import sleep
from webbrowser import open_new_tab

from docopt import docopt

from . import api

from pprint import pprint

try:
    import ConfigParser as configparser
except:
    import configparser


VERSION = 'habitica version 0.0.16'
TASK_VALUE_BASE = 0.9747  # http://habitica.wikia.com/wiki/Task_Value
HABITICA_REQUEST_WAIT_TIME = 0.5  # time to pause between concurrent requests
HABITICA_TASKS_PAGE = '/#/tasks'
# https://trello.com/c/4C8w1z5h/17-task-difficulty-settings-v2-priority-multiplier
PRIORITY = {'easy': 1,
            'medium': 1.5,
            'hard': 2}
AUTH_CONF = os.path.expanduser('~') + '/.config/habitica/auth.cfg'
TEST_AUTH_CONF = os.path.expanduser('~') + '/.config/habitica/test_auth.cfg'
CACHE_CONF = os.path.expanduser('~') + '/.config/habitica/cache.cfg'

# Dictionary between user arguments and corresponding
# field in a JSON Habitica API request.
TASK_FIELDS = {'--text': 'text',
               '--notes': 'notes',
               '--checklist': 'collapseChecklist',
               '--difficulty': 'priority',
               '--date': 'date', }

SECTION_CACHE_QUEST = 'Quest'
checklists_on = False

DEFAULT_PARTY = 'Not currently in a party'
DEFAULT_QUEST = 'Not currently on a quest'
DEFAULT_PET = 'No pet currently'
DEFAULT_MOUNT = 'Not currently mounted'


def load_auth(configfile):
    """Get authentication data from the AUTH_CONF file."""

    logging.debug('Loading habitica auth data from %s' % configfile)

    try:
        cf = open(configfile)
    except IOError:
        logging.error("Unable to find '%s'." % configfile)
        exit(1)

    config = configparser.SafeConfigParser({'checklists': False})
    config.readfp(cf)

    cf.close()

    # Get data from config
    rv = {}
    try:
        rv = {'url': config.get('Habitica', 'url'),
              'checklists': config.get('Habitica', 'checklists'),
              'x-api-user': config.get('Habitica', 'login'),
              'x-api-key': config.get('Habitica', 'password')}

    except configparser.NoSectionError:
        logging.error("No 'Habitica' section in '%s'" % configfile)
        exit(1)

    except configparser.NoOptionError as e:
        logging.error("Missing option in auth file '%s': %s"
                      % (configfile, e.message))
        exit(1)

    # Return auth data as a dictionnary
    return rv


def load_cache(configfile):
    logging.debug('Loading cached config data (%s)...' % configfile)

    defaults = {'quest_key': '',
                'quest_s': 'Not currently on a quest'}

    cache = configparser.SafeConfigParser(defaults)
    cache.read(configfile)

    if not cache.has_section(SECTION_CACHE_QUEST):
        cache.add_section(SECTION_CACHE_QUEST)

    return cache


def update_quest_cache(configfile, **kwargs):
    logging.debug('Updating (and caching) config data (%s)...' % configfile)

    cache = load_cache(configfile)

    for key, val in kwargs.items():
        cache.set(SECTION_CACHE_QUEST, key, val)

    with open(configfile, 'wb') as f:
        cache.write(f)

    cache.read(configfile)

    return cache


def parse_list_indices(tids):
    """
    handle task-id formats such as:
        habitica todos done 3
        habitica todos done 1,2,3
        habitica todos done 1-3,5
        habitica tags delete 1-3

    `tids` is a string consisting of comma-separated tokens that can be:
    - A single number (e.g. '3')
    - A range of numbers (e.g. '1-3')
    """
    logging.debug('raw task ids: %s' % tids)
    task_ids = []
    for token in tids.split(','):
        if '-' in token:
            start, stop = [int(e) for e in token.split('-')]
            if start > stop:
                start, stop = stop, start
            task_ids.extend(range(start, stop + 1))
        elif token == '':
            return []
        else:
            task_ids.append(int(token))

    return [e - 1 for e in set(task_ids)]


def parse_list_strings(tstrs):
    """
    handle task/tag names such as:
        habitica tags delete Work,School
        habitica tags rename Home --text="Housekeeping"

    `tstrs` is a string of comma-separated strings.
    """
    logging.debug('raw task names: %s' % tstrs)
    if tstrs == '':
        return []
    return tstrs.split(',')


def cl_done_count(task):
    items = task['checklist']
    count = 0
    for li in items:
        if li['completed'] == True:
            count = count + 1
    return count


def cl_item_count(task):
    if 'checklist' in task:
        return len(task['checklist'])
    else:
        return 0


def print_tags_list(tags):
    for i, tag in enumerate(tags):
        tag_line = '[*] %s %s' % (i + 1,
                                  tag['name'])
        print(tag_line)


def print_task_list(tasks):
    for i, task in enumerate(tasks):
        completed = 'x' if task['completed'] else ' '
        task_line = '[%s] %s %s' % (completed,
                                    i + 1,
                                    task['text'])
        checklist_available = cl_item_count(task) > 0
        if checklist_available:
            task_line += ' (%s/%s)' % (str(cl_done_count(task)),
                                       str(cl_item_count(task)))
        print(task_line)
        if checklists_on and checklist_available:
            for c, check in enumerate(task['checklist']):
                completed = 'x' if check['completed'] else ' '
                print('    [%s] %s' % (completed,
                                       check['text']))


def qualitative_task_score_from_value(value):
    # task value/score info: http://habitica.wikia.com/wiki/Task_Value
    scores = ['*', '**', '***', '****', '*****', '******', '*******']
    breakpoints = [-20, -10, -1, 1, 5, 10]
    return scores[bisect(breakpoints, value)]


def set_checklists_status(auth, args):
    """Set display_checklist status, toggling from cli flag"""
    global checklists_on

    if auth['checklists'] == "true":
        checklists_on = True
    else:
        checklists_on = False

    # reverse the config setting if specified by the CLI option
    if args['--checklists']:
        checklists_on = not checklists_on

    return


def fields_from_args(args):
    """
    Extract the fields from user-supplied arguments

    Takes in user-supplied arguments from docopt and grabs any task fields
    it contains. Stores them in a dictionary whose keys are the names
    of those fields as they would be given in a request to the Habitica
    API.

    Does NOT retrieve the type of task being modified (e.g. 'todo', 'habit',
    etc.). See `task_type_from_args(args)`.

    e.g.
    Possible Input:

        {'--date': None,
         '--debug': False,
         '--difficulty': 'easy',
         '--help': False,
         '--notes': None,
         '--tags': 'foo,bar',
         '--text': 'Count to three',
         '--verbose': False,
         '--version': False, }

    Output:
        {'difficulty': 'easy',
         'tags': 'foo,bar',
         'text': 'Count to three', }
    """

    fields_and_values = {}
    for arg, field in TASK_FIELDS.items():
        if arg in args:
            if arg == '--difficulty':
                # Needs to be converted to a numerical value
                new_val = PRIORITY[args[arg]]
            else:
                new_val = args[arg]
            fields_and_values[field] = new_val

    return fields_and_values


def task_type_from_args(args, grammatical_number):
    """
    Return the user's requested task type from command-line args.

    Habitica names these fields differently depending on what type of
    API call you're making, e.g. when creating a task, these strings
    should be singular; but when getting all tasks of a particular type,
    these strings should be plural.

    Valid `grammatical_number` values are 'singular' and 'plural'.
    """

    if grammatical_number == 'singular':
        if args['todos']:
            return 'todo'
        if args['habits']:
            return 'habit'
        if args['dailies']:
            return 'daily'
        raise Exception("No task type provided!")
    elif grammatical_number == 'plural':
        if args['todos']:
            return 'todos'
        if args['habits']:
            return 'habits'
        if args['dailies']:
            return 'dailys'
        raise Exception("No task type provided!")

    raise Exception("Bad grammatical number! Accepted values are "
                    "'singular' and 'plural'.")


def get_tags(hbt):
    """Return all of the user's tags."""
    return hbt.user.tags()


def get_these_tags(hbt, args):
    """Return the tags corresponding to these indices or names."""
    cur_tags = get_tags(hbt)
    ret_tags = []
    try:
        # parse_list_indices fails if given tag names
        tids = parse_list_indices(args['<task-ids>'])
        for i in tids:
            ret_tags.append(cur_tags[i])

    except ValueError:
        if ret_tags:
            raise Exception("Combined numerical and string-based indexing!")
        tstrs = parse_list_strings(args['<task-ids>'])
        for s in tstrs:
            for tag in cur_tags:
                if s == tag['name']:
                    ret_tags.append(tag)
                    break

    #for t in ret_tags:
    #    t['_id'] = t['id']

    return ret_tags


def add_tag(hbt, args):
    """Construct a tag of the given type and then publish it."""
    hbt.user.tags(name=args['--text'],
                  _method='post')


def delete_tags(hbt, args):
    """Apply the user-requested changes to all of the given tags."""

    # Populate a list with JSON API requests
    to_delete = get_these_tags(hbt, args)

    for t in to_delete:
        t['_method'] = 'delete'
        hbt.user.tags(**t)


def rename_tag(hbt, args):
    tags = get_these_tags(hbt, args)
    if len(tags) > 1:
        raise ValueError("Can't rename multiple tags at once!")
    tag_fields = tags[0]
    tag_fields['_method'] = 'put'
    tag_fields['name'] = args['--text']
    hbt.user.tags(**tag_fields)


def get_tasks(hbt, task_type):
    """
    Return a list of tasks, from Habitica, of the requested type.

    e.g.
        get_tasks(hbt, 'habits')    # returns list of JSON habits for user
        get_tasks(hbt, 'todos')     # ditto, for todos
        get_tasks(hbt, 'dailys')    # ditto, for dailies
    """
    tasks = hbt.user.tasks(type=task_type)
    return tasks


def write_new_fields(task_json, new_vals):
    """Write new field values to a JSON file and return it"""
    for field, new_val in new_vals.items():
        task_json[field] = new_val
    return task_json


def add_task(hbt, args):
    """Construct a new task of the given type and publish it."""

    # Build a JSON API request as we go.
    task_fields = {}

    task_fields['text'] = args['--text']
    task_fields['type'] = task_type_from_args(args, 'singular')
    write_new_fields(task_fields, fields_from_args(args))
    task_fields['_method'] = 'post'

    hbt.user.tasks(**task_fields)


# TODO: figure out a more elegant way to implement this
def bulk_edit_tasks(hbt, action, args):
    """Apply the user-requested changes to all of the given tasks."""

    task_type = task_type_from_args(args, 'plural')
    cur_tasks = get_tasks(hbt, task_type)

    tids = parse_list_indices(args['<task-ids>'])
    for tid in tids:
        task_fields = cur_tasks[tid]
        if action == 'delete':
            task_fields['_method'] = 'delete'
        elif action == 'up' or action == 'down':
            # Habits, dailies, and todos are all checked with "up"
            # and unchecked/decremented with "down"
            task_fields['direction'] = action
            task_fields['_method'] = 'post'
        elif action == 'edit':
            write_new_fields(task_fields, fields_from_args(args))
            task_fields['_method'] = 'put'

        hbt.user.tasks(**task_fields)


# TODO: DRY the manipulable objects
def cli():
    """Habitica command-line interface.

    Usage: habitica (habits | dailies | todos | tags | status | server | home)
                    [options]
           habitica (habits | dailies | todos | tags) add [options]
           habitica (habits | dailies | todos | tags) edit <task-ids> [options]
           habitica (habits | dailies | todos | tags) delete <task-ids> [options]
           habitica (dailies | todos) (done | undo) <task-ids> [options]
           habitica habits (up | down) <task-ids> [options]
           habitica --help
           habitica --version

    Options:
      -h --help         Show this screen
      --version         Show version
      --text=<txt>      Quoted string holding the name of the task
      --notes=<n>       Quoted string holding the task's notes
      --tags=<tg>       Comma-separated list of the task's tags
      --difficulty=<d>  (easy | medium | hard) [default: easy]
      --date=<dd>       Task's due date, given as YYYY-MM-DD
      --verbose         Show some logging information
      --debug           Some all logging information
      -c --checklists   Toggle displaying checklists on or off
      -t --test         Use test_auth credentials, not regular credentials

    The habitica commands are:
      status                  Show HP, XP, GP, and more
      edit                    Change task fields, see below
      habits                  List habit tasks
      habits up <task-id>     Up (+) habit <task-id>
      habits down <task-id>   Down (-) habit <task-id>
      dailies                 List daily tasks
      dailies done            Mark daily <task-id> complete
      dailies undo            Mark daily <task-id> incomplete
      todos                   List todo tasks
      todos done <task-id>    Mark one or more todo <task-id> completed
      todos add <task>        Add todo with description <task>
      todos delete <task-id>  Delete one or more todo <task-id>
      server                  Show status of Habitica service
      home                    Open tasks page in default browser

    For `habits up|down`, `dailies done|undo`, `todos done`, and `todos
    delete`, you can pass one or more <task-id> parameters, using either
    comma-separated lists or ranges or both. For example, `todos done
    1,3,6-9,11`.

    For `tags delete` or `[TASK_TYPE] edit --tags=`, you can pass
    in (a comma-separated list of) the name(s) of the tags to delete or apply.
    This is case-sensitive.

    *Be warned that Habitica allows you to create multiple tags with the
    exact same namestring. If your account has multiple tags with the same
    name string, manipulating tags by name will produce undefined behavior.*

    Editing existing tasks is done with the `edit` command. To edit a
    task, specify the task's type (habit, daily, or todo) and all of the
    fields you want to change. For example,

        # Fix typo
        habitica todos add Tautn English pig-dogs
        habitica edit todos 1 --name="Taunt English pig-dogs"

        # Bulk add tags
        habitica edit todos 3,9,15-20 --tags=housechores,simple

        # Bulk remove tags
        habitica edit dailies 1,2,3 --tags=""

        # Set due dates
        habitica edit todos 5-9 --date=2000-01-01

    To show checklists with "todos" and "dailies" permanently, set
    'checklists' in your auth.cfg file to `checklists = true`.
    """

    # set up args
    args = docopt(cli.__doc__, version=VERSION)

    # set up logging
    if args['--verbose']:
        logging.basicConfig(level=logging.INFO)
    if args['--debug']:
        logging.basicConfig(level=logging.DEBUG)

    logging.debug('Command line args: {%s}' %
                  ', '.join("'%s': '%s'" % (k, v) for k, v in args.items()))

    # Set up auth
    if args['--test']:  # TODO: does this work with the short option?
        auth = load_auth(TEST_AUTH_CONF)
    else:
        auth = load_auth(AUTH_CONF)

    # Prepare cache
    cache = load_cache(CACHE_CONF)

    # instantiate api service
    hbt = api.Habitica(auth=auth)

    # Flag checklists as on if true in the config
    set_checklists_status(auth, args)

    # GET server status
    if args['server']:
        server = hbt.status()
        if server['status'] == 'up':
            print('Habitica server is up')
        else:
            print('Habitica server down... or your computer cannot connect')

    # open HABITICA_TASKS_PAGE
    elif args['home']:
        home_url = '%s%s' % (auth['url'], HABITICA_TASKS_PAGE)
        print('Opening %s' % home_url)
        open_new_tab(home_url)

    # GET user
    elif args['status']:

        # gather status info
        user = hbt.user()
        stats = user.get('stats', '')
        items = user.get('items', '')
        food_count = sum(items['food'].values())
        group = hbt.groups(type='party')
        party = DEFAULT_PARTY
        quest = DEFAULT_QUEST
        mount = DEFAULT_MOUNT

        # if in a party, grab party info
        if group:
            party_id = group[0]['id']
            party_title = group[0]['name']

            # if on a quest with the party, grab quest info
            quest_data = getattr(hbt.groups, party_id)()['quest']
            if quest_data and quest_data['active']:
                quest_key = quest_data['key']

                if cache.get(SECTION_CACHE_QUEST, 'quest_key') != quest_key:
                    # we're on a new quest, update quest key
                    logging.info('Updating quest information...')
                    content = hbt.content()
                    quest_type = ''
                    quest_max = '-1'
                    quest_title = content['quests'][quest_key]['text']

                    # if there's a content/quests/<quest_key/collect,
                    # then drill into .../collect/<whatever>/count and
                    # .../collect/<whatever>/text and get those values
                    if content.get('quests', {}).get(quest_key,
                                                     {}).get('collect'):
                        logging.debug("\tOn a collection type of quest")
                        qt = 'collect'
                        clct = content['quests'][quest_key][qt].values()[0]
                        quest_max = clct['count']
                    # else if it's a boss, then hit up
                    # content/quests/<quest_key>/boss/hp
                    elif content.get('quests', {}).get(quest_key,
                                                       {}).get('boss'):
                        logging.debug("\tOn a boss/hp type of quest")
                        qt = 'hp'
                        quest_max = content['quests'][quest_key]['boss'][qt]

                    # store repr of quest info from /content
                    cache = update_quest_cache(CACHE_CONF,
                                               quest_key=str(quest_key),
                                               quest_type=str(qt),
                                               quest_max=str(quest_max),
                                               quest_title=str(quest_title))

                # now we use /party and quest_type to figure out our progress!
                quest_type = cache.get(SECTION_CACHE_QUEST, 'quest_type')
                if quest_type == 'collect':
                    qp_tmp = quest_data['progress']['collect']
                    quest_progress = qp_tmp.values()[0]
                else:
                    quest_progress = quest_data['progress']['hp']

                quest = '%s/%s "%s"' % (
                        str(int(quest_progress)),
                        cache.get(SECTION_CACHE_QUEST, 'quest_max'),
                        cache.get(SECTION_CACHE_QUEST, 'quest_title'))

        # prepare and print status strings
        title = 'Level %d %s' % (stats['lvl'], stats['class'].capitalize())
        health = '%d/%d' % (stats['hp'], stats['maxHealth'])
        xp = '%d/%d' % (int(stats['exp']), stats['toNextLevel'])
        mana = '%d/%d' % (int(stats['mp']), stats['maxMP'])
        currentPet = items.get('currentPet', '')
        if not currentPet:
            currentPet = DEFAULT_PET
        pet = '%s (%d food items)' % (currentPet, food_count)
        mount = items.get('currentMount', '')
        if not mount:
            mount = DEFAULT_MOUNT
        summary_items = ('health', 'xp', 'mana', 'quest', 'pet', 'mount')
        len_ljust = max(map(len, summary_items)) + 1
        print('-' * len(title))
        print(title)
        print('-' * len(title))
        print('%s %s' % ('Health:'.rjust(len_ljust, ' '), health))
        print('%s %s' % ('XP:'.rjust(len_ljust, ' '), xp))
        print('%s %s' % ('Mana:'.rjust(len_ljust, ' '), mana))
        print('%s %s' % ('Pet:'.rjust(len_ljust, ' '), pet))
        print('%s %s' % ('Mount:'.rjust(len_ljust, ' '), mount))
        print('%s %s' % ('Party:'.rjust(len_ljust, ' '), party))
        print('%s %s' % ('Quest:'.rjust(len_ljust, ' '), quest))

    # Manipulating task objects
    elif args['todos'] or args['habits'] or args['dailies']:
        # Singleton task manipulation
        if args['add']:
            add_task(hbt, args)

        # Bulk task manipulation
        elif args['delete']:
            bulk_edit_tasks(hbt, 'delete', args)

        elif args['done'] or args['up']:
            bulk_edit_tasks(hbt, 'up', args)

        elif args['undo'] or args['down']:
            bulk_edit_tasks(hbt, 'down', args)

        elif args['edit']:
            bulk_edit_tasks(hbt, 'edit', args)

        print_task_list(get_tasks(hbt,
                                  task_type_from_args(args, 'plural')
                                  )
                        )

    # Manipulating tags
    elif args['tags']:
        # TODO: expand

        if args['add']:
            add_tag(hbt, args)  # TODO: implement

        # Bulk tag manipulation
        elif args['delete']:
            delete_tags(hbt, args)

        elif args['edit']:
            rename_tag(hbt, args)

        print_tags_list(get_tags(hbt))


if __name__ == '__main__':
    cli()
