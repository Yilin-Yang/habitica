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
import logging
import os.path
import sys
from webbrowser import open_new_tab

from docopt import docopt

from . import argparse
from . import api
from . import taskmanip

try:
    import ConfigParser as configparser
except ImportError:
    import configparser


VERSION = 'habitica version 0.0.16'
TASK_VALUE_BASE = 0.9747  # http://habitica.wikia.com/wiki/Task_Value
HABITICA_REQUEST_WAIT_TIME = 0.5  # time to pause between concurrent requests
HABITICA_TASKS_PAGE = '/#/tasks'
AUTH_CONF = os.path.expanduser('~') + '/.config/habitica/auth.cfg'
TEST_AUTH_CONF = os.path.expanduser('~') + '/.config/habitica/test_auth.cfg'
CACHE_CONF = os.path.expanduser('~') + '/.config/habitica/cache.cfg'


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


def cl_done_count(task):
    items = task['checklist']
    count = 0
    for li in items:
        if li['completed']:
            count = count + 1
    return count


def cl_item_count(task):
    if 'checklist' in task:
        return len(task['checklist'])
    else:
        return 0


def print_tags_list(tags):
    for i, tag in enumerate(tags):
        tag_line = '[#] %s %s' % (i + 1,
                                  tag['name'])
        print(tag_line)


def print_task_list(tasks):
    for i, task in enumerate(tasks):
        if 'completed' in task and task['completed']:
            completed = 'x'
        else:
            completed = ' '
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


def print_status(hbt, cache):
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


# TODO: DRY the manipulable objects
def cli():
    """
    Habitica command-line interface.

    Usage: habitica (habits | dailies | todos | tags | status | server | home)
                    [options]
           habitica (habits | dailies | todos | tags) add [options]
           habitica (habits | dailies | todos | tags) edit <task-ids> [options]
           habitica (habits | dailies | todos | tags) delete <task-ids>
                    [options]
           habitica (dailies | todos) (done | undo) <task-ids> [options]
           habitica habits (up | down) <task-ids> [options]
           habitica reset [options]
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
      reset                   Restarts account from scratch, deleting
                              everything.

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

    # Reset user account
    if args['reset']:
        print_status(hbt, cache)
        print("========================================"
              "========================================\n")
        print(" WARNING: All tags and tasks for the user above "
              "will be deleted!\n")
        print("========================================"
              "========================================\n\n")

        while True:
            decision = raw_input("Are you sure you want to proceed? (Y\\n)")
            if decision == 'N' or decision == 'n':
                print("Exiting.")
                sys.exit(1)
            elif decision == 'Y' or decision == 'y':
                break
            else:
                print("Invalid input! Please type 'Y' or 'n', "
                      " without the quotes.")
        hbt.user.reset(_method='post')

    # GET server status
    elif args['server']:
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
        print_status(hbt, cache)

    # Manipulating task objects
    elif args['todos'] or args['habits'] or args['dailies']:
        # Singleton task manipulation
        if args['add']:
            taskmanip.add_task(hbt, args)

        # Bulk task manipulation
        elif args['delete']:
            taskmanip.bulk_edit_tasks(hbt, 'delete', args)

        elif args['done'] or args['up']:
            taskmanip.bulk_edit_tasks(hbt, 'up', args)

        elif args['undo'] or args['down']:
            taskmanip.bulk_edit_tasks(hbt, 'down', args)

        elif args['edit']:
            taskmanip.bulk_edit_tasks(hbt, 'edit', args)

        print_task_list(
            taskmanip.get_tasks(hbt,
                                argparse.task_type_from_args(args, 'plural'))
        )

    # Manipulating tags
    elif args['tags']:
        # TODO: expand

        if args['add']:
            taskmanip.add_tag(hbt, args)

        # Bulk tag manipulation
        elif args['delete']:
            taskmanip.delete_tags(hbt, args)

        elif args['edit']:
            taskmanip.rename_tag(hbt, args)

        print_tags_list(taskmanip.get_tags(hbt))


if __name__ == '__main__':
    cli()
