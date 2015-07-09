#!/usr/bin/python
import trello as trellomodule
import plistlib
import subprocess
import os
import sys
from datetime import date, datetime, timedelta
import requests
import json
import optparse
from string import atoi

from ConfigParser import RawConfigParser

# Default settings (overridden by config file and command line options)
DEFAULT_CONFIG_FILE_LOCATIONS= [
    '/etc/munki-trello/munki-trello.cfg',
    'munki-trello.cfg'
]
DEFAULT_DEV_LIST = "Development"
DEFAULT_TEST_LIST = "Testing"
DEFAULT_PROD_LIST = "Production"
DEFAULT_TO_DEV_LIST = "To Development"
DEFAULT_TO_TEST_LIST = "To Testing"
DEFAULT_TO_PROD_LIST = "To Production"
DEFAULT_PRODUCTION_SUFFIX = "Production"
DEFAULT_MUNKI_PATH = "/Volumes/Munki"
DEFAULT_MAKECATALOGS = "/usr/local/munki/makecatalogs"
DEFAULT_MUNKI_DEV_CATALOG = "development"
DEFAULT_MUNKI_TEST_CATALOG = "testing"
DEFAULT_MUNKI_PROD_CATALOG = "production"
DEFAULT_DATE_FORMAT = '%d/%m/%y'
DEFAULT_AUTO_STAGE_TO_TEST=False
DEFAULT_AUTO_STAGE_TO_PROD=False
DEFAULT_DEV_STAGE_DAYS='0'
DEFAULT_TEST_STAGE_DAYS='0'

def fail(message):
    sys.stderr.write(message)
    sys.exit(1)

def execute(command):
    popen = subprocess.Popen(command, stdout=subprocess.PIPE)
    lines_iterator = iter(popen.stdout.readline, b"")
    for line in lines_iterator:
        print(line) # yield line

def update_pos(list_id, value):
    resp = requests.put("https://trello.com/1/lists/%s/pos" % (list_id), params=dict(key=KEY, token=TOKEN), data=dict(value=value))
    resp.raise_for_status()
    return json.loads(resp.content)

def name_in_list(name, to_development, development, testing, to_testing, to_production):
    found = False
    for card in to_development:
        if card['name'] == name:
            return True

    for card in development:
        if card['name'] == name:
            return True

    for card in testing:
        if card['name'] == name:
            return True

    for card in to_testing:
        if card['name'] == name:
            return True

    for card in to_production:
        if card['name'] == name:
            return True

    return False

def get_app_version(card_id):
    cards = trello.cards.get_action(card_id)
    cards.reverse() 
    for action in cards:
        if action['type']=="commentCard":
            comment_data = action['data']['text'].split("\n")

            if comment_data[0] != "**System Info**":
                continue

            for fragment in comment_data:
                if str(fragment).startswith('Name: '):
                    app_name = fragment[6:]
                if str(fragment).startswith('Version: '):
                    version = fragment[9:]
    return app_name, version

def migrate_packages(trello_connection, source_cards,
                         dest_list_id, dest_catalog_name,
                         due=0, message=None, auto_move=False):

    run_makecatalogs = 0

    due_date_str = None 
    if due > 0:
        delta = timedelta(days=due)
        now = datetime.utcnow()
        due_date = now + delta
        due_date_str = due_date.strftime('%Y-%m-%dT%H:%M:%S.000Z')

    # Find items from the source list, update pkginfo, and change trello
    # card to dest
    for card in source_cards:
        app_name, version = get_app_version(card['id'])

        # create a list of pkgsinfo files
        pkgsinfo_dirwalk = os.walk(os.path.join(MUNKI_PATH,'pkgsinfo'),
                                                            topdown=False)

        plist = None
        for root, dirs, files in pkgsinfo_dirwalk:
           for file in files:
               # It is conceivable there are broken / non plist files
               # so we try to parse the files, just in case
               pkgsinfo = os.path.join(root, file)
               try:
                   plist = plistlib.readPlist(pkgsinfo)
               except:
                   plist = None # Just in case
                   continue

               if plist['name'] == app_name and plist['version'] == version:

                   plist['catalogs'] = [dest_catalog_name]

                   plistlib.writePlist(plist, pkgsinfo)

                   trello_connection.cards.update_idList(card['id'], dest_list_id)
                   # If we are automatically moving cards, reset their
                   # due date
                   if auto_move:
                       trello_connection.cards.update_due(card['id'], None)

                   if message != None:
                       trello_connection.cards.new_action_comment(card['id'], message)
                   if due_date_str != None:
                       trello_connection.cards.update_due(card['id'], due_date_str)
         
                   run_makecatalogs = run_makecatalogs + 1
               else:
                   plist = None

           if plist != None:
                break

    return run_makecatalogs

def read_config(cmdopts):

    config = RawConfigParser(allow_no_value=True)

    # Set up defaults
    config.add_section('main')
    config.set('main', 'boardid', None)
    config.set('main', 'key', None)
    config.set('main', 'token', None)
    config.set('main', 'makecatalogs', DEFAULT_MAKECATALOGS)
    config.set('main', 'repo_path', DEFAULT_MUNKI_PATH)
    config.set('main', 'date_format', DEFAULT_DATE_FORMAT)

    config.add_section('development')
    config.set('development', 'list', DEFAULT_DEV_LIST)
    config.set('development', 'catalog', DEFAULT_MUNKI_DEV_CATALOG)
    config.set('development', 'to_list', DEFAULT_TO_DEV_LIST)
    config.set('development', 'stage_days', DEFAULT_DEV_STAGE_DAYS)

    config.add_section('testing')
    config.set('testing', 'list', DEFAULT_TEST_LIST)
    config.set('testing', 'catalog', DEFAULT_MUNKI_TEST_CATALOG)
    config.set('testing', 'to_list', DEFAULT_TO_PROD_LIST)
    config.set('testing', 'stage_days', DEFAULT_TEST_STAGE_DAYS)
    config.set('testing', 'autostage', DEFAULT_AUTO_STAGE_TO_TEST)

    config.add_section('production')
    config.set('production', 'list', DEFAULT_PROD_LIST)
    config.set('production', 'catalog', DEFAULT_MUNKI_PROD_CATALOG)
    config.set('production', 'to_list', DEFAULT_TO_PROD_LIST)
    config.set('production', 'suffix', DEFAULT_PRODUCTION_SUFFIX)
    config.set('production', 'autostage', DEFAULT_AUTO_STAGE_TO_PROD)

    config_file_locations = DEFAULT_CONFIG_FILE_LOCATIONS

    if cmdopts.config:
        config_file_locations.append(cmdopts.config)

    rc = config.read(config_file_locations)

    if not cmdopts.boardid:
        cmdopts.boardid = config.get('main', 'boardid')

    if not cmdopts.key:
        cmdopts.key = config.get('main', 'key')

    if not cmdopts.token:
        cmdopts.token = config.get('main', 'token')

    if not cmdopts.repo_path:
        cmdopts.repo_path = config.get('main', 'repo_path')

    if not cmdopts.makecatalogs:
        cmdopts.makecatalogs = config.get('main', 'makecatalogs')

    if not cmdopts.date_format:
        cmdopts.date_format = config.get('main', 'date_format')

    if not cmdopts.to_dev_list:
        cmdopts.to_dev_list = config.get('development', 'to_list')

    if not cmdopts.dev_list:
        cmdopts.dev_list = config.get('development', 'list')

    if not cmdopts.dev_catalog:
        cmdopts.dev_catalog = config.get('development', 'catalog')

    if cmdopts.dev_stage_days == None:
        val = atoi(config.get('development', 'stage_days'))
        cmdopts.dev_stage_days = val
    else:
        cmdopts.dev_stage_days == atoi(cmdopts.dev_stage_days)

    if not cmdopts.to_test_list:
        cmdopts.to_test_list = config.get('testing', 'to_list')

    if not cmdopts.test_list:
        cmdopts.test_list = config.get('testing', 'list')

    if not cmdopts.test_catalog:
        cmdopts.test_catalog = config.get('testing', 'catalog')

    if cmdopts.test_stage_days == None:
        val = atoi(config.get('testing', 'stage_days'))
        cmdopts.test_stage_days = val
    else: 
        cmdopts.test_stage_days == atoi(cmdopts.test_stage_days)

    if cmdopts.stage_test == None:
        cmdopts.test_autostage = config.get('testing', 'autostage')

    if not cmdopts.prod_list:
        cmdopts.prod_list = config.get('production', 'list')

    if not cmdopts.to_prod_list:
        cmdopts.to_prod_list = config.get('production', 'to_list')

    if not cmdopts.prod_catalog:
        cmdopts.prod_catalog = config.get('production', 'catalog')

    # We check for None here, as the only way to override this
    # on the command line is to set --suffix=
    if cmdopts.prod_suffix == None:
        cmdopts.prod_suffix = config.get('production', 'suffix')

    if cmdopts.stage_prod == None:
        cmdopts.prod_autostage = config.get('production', 'autostage')

def find_or_create_list(trello, board_id, name_id_dict, required_name, position):

    if name_id_dict.has_key(required_name):
        return name_id_dict[required_name]

    new_list = trello.boards.new_list(board_id, required_name)

    if position == 0:
        position = 1000001
    update_pos(new_list['id'], position-1)

    return new_list['id']

def update_card_list(trello, app_cards, app_catalog):

    for card in app_cards:
        app_name, version = get_app_version(card['id'])
        found = False
        for item in app_catalog:
            if item['name'] == app_name and item['version'] == version:
                found = True
        if not found:
            trello.cards.delete(card['id'])

def find_auto_migrations(card_list):

    migrate_cards = []

    now = datetime.utcnow()

    for card in card_list:
       if card['due'] == None:
           continue
       # Assumptions here:
       # Trello will always return UTC dates in an ISO standard format
       # Due dates are not going to be accurate to more than a second
       # (hence the .000 in the format)
       due = datetime.strptime(card['due'], '%Y-%m-%dT%H:%M:%S.000Z')
       difference = now - due
       if (now - due).total_seconds() > 0:
           migrate_cards.append(card)
 
    return migrate_cards

def get_dated_board_id(trello, board_id, list_prefix, suffix, list_name,
                                   list_names, list_positions ):
    
    if suffix:
        prod_title = '%s %s' % (list_prefix, suffix)
  
        # Find the maximun list id from the remaining list_names:
        positions = list_positions.values()
        positions.sort()
        max_position = positions[-1]

        return find_or_create_list(trello, board_id,
                                    list_names, prod_title, max_position)
    else:
        prod_title = list_name
        if not list_names.has_key(prod_title):
            fail("No '%s' list found\n" % prod_title)

        return list_names[prod_title]

        
usage = "%prog [options]"
o = optparse.OptionParser(usage=usage)

# Required options

o.add_option("--boardid", help=("Trello board ID."))

o.add_option("--key", help=("Trello API key. See README for details on how to get one."))

o.add_option("--token", help=("Trello application token. See README for details on how to get one."))

# Optional Options

o.add_option("--config",
    help=("Name of configuration file; program will try to read '/etc/munki-trello/munki-trello.cfg' and './munki-trello.cfg' by default, appending this configuration file to the end of the list; configuration file values will be overridden by those on the command line and last match wins") )


o.add_option("--to-dev-list",
    help=("Name of the 'To Development' Trello list. Defaults to '%s'. "
              % DEFAULT_DEV_LIST))

o.add_option("--dev-list",
    help=("Name of the 'Development' Trello list. Defaults to '%s'. "
              % DEFAULT_DEV_LIST))

o.add_option("--to-test-list",
    help=("Name of the 'To Testing' Trello list. Defaults to '%s'. "
              % DEFAULT_TO_TEST_LIST))

o.add_option("--test-list",
    help=("Name of the 'Testing' Trello list. Defaults to '%s'. "
              % DEFAULT_TEST_LIST))

o.add_option("--prod-list",
    help=("Name of the 'Production' Trello list. Defaults to '%s'. Will only be used if the production suffix is set to the empty string"
              % DEFAULT_PROD_LIST))

o.add_option("--to-prod-list",
    help=("Name of the 'To Production' Trello list. Defaults to '%s'. "
              % DEFAULT_TO_PROD_LIST))

o.add_option("--prod-suffix","--suffix",
    help=("Suffix that will be added to new 'In Production cards'. Defaults to '%s'. "
              % DEFAULT_PRODUCTION_SUFFIX))

o.add_option("--dev-catalog",
    help=("Name of the Munki development catalog. Defaults to '%s'. "
              % DEFAULT_MUNKI_DEV_CATALOG))

o.add_option("--test-catalog",
    help=("Name of the Munki testing catalog. Defaults to '%s'. "
              % DEFAULT_MUNKI_TEST_CATALOG))

o.add_option("--prod-catalog",
    help=("Name of the Munki production catalog. Defaults to '%s'. "
              % DEFAULT_MUNKI_PROD_CATALOG))

o.add_option("--repo-path",
    help=("Path to your Munki repository. Defaults to '%s'. "
              % DEFAULT_MUNKI_PATH))

o.add_option("--makecatalogs",
    help=("Path to makecatalogs. Defaults to '%s'. "
              % DEFAULT_MAKECATALOGS))

o.add_option("--date-format",
    help=("Date format to use when creating dated lists. See strftime(1) for details of formatting options. Defaults to '%s'. "
              % DEFAULT_DATE_FORMAT))

o.add_option("--dev-stage-days",
    help=("The number of days that a package will remain in development before being prompoted to test (if staging is enabled). Note: this does not enable staging"))
    
o.add_option("--test-stage-days",
    help=("The number of days a package will remain in testing before being prompoted to production (if staging is enabled). Note: this does not enable staging"))

o.add_option("--stage-test",
    help=("Automatically promote packages past their due date from development into testing.  Note: this does not enable setting of the due date"))

o.add_option("--stage-prod",
    help=("Automatically promote packages past their due date from testing into production.  Note: this does not enable setting of the due date"))


opts, args = o.parse_args()

# Read configuration file (either given on command line or
# from default locactions

read_config(opts)

if not opts.boardid or not opts.key or not opts.token:
    fail("Board ID, API key and application token are required.")

BOARD_ID = opts.boardid
KEY = opts.key
TOKEN = opts.token
TO_DEV_LIST = opts.to_dev_list
DEV_LIST = opts.dev_list
TO_TEST_LIST = opts.to_test_list
TEST_LIST = opts.test_list
TO_PROD_LIST = opts.to_prod_list
PROD_LIST = opts.prod_list
DEV_CATALOG = opts.dev_catalog
TEST_CATALOG = opts.test_catalog
PROD_CATALOG = opts.prod_catalog
PRODUCTION_SUFFIX = opts.prod_suffix
MUNKI_PATH = opts.repo_path
MAKECATALOGS = opts.makecatalogs
DATE_FORMAT=opts.date_format
# These need to be options:
AUTO_STAGE_TO_TEST=opts.test_autostage
AUTO_STAGE_TO_PROD=opts.prod_autostage

if not os.path.exists(MUNKI_PATH):
    fail('Munki path not accessible')

trello = trellomodule.TrelloApi(KEY)
trello.set_token(TOKEN)

lists = trello.boards.get_list(BOARD_ID)

# Build up list of names and list ids for quick reference
list_names = {}
list_positions = {}
for list in lists:
    list_names[ list['name'] ] = list['id']
    list_positions[   list['name'] ] = list['pos']

# Check that the lists we require exist
for name in [TO_DEV_LIST, TO_TEST_LIST, TO_PROD_LIST, DEV_LIST, TEST_LIST]:
    if not list_names.has_key(name):
        fail("No '%s' list found\n" % name)

# get the 'To' lists, removing these items from the dictionary
# (so that when we find max_id below, we will ignore these entries)
# Note that we *should* not get a key error due to the checks above
id = list_names[TO_DEV_LIST]
list_positions.pop(TO_DEV_LIST)
to_development = trello.lists.get_card(id)

id = list_names[TO_TEST_LIST]
list_positions.pop(TO_TEST_LIST)
to_testing     = trello.lists.get_card(id)

id = list_names[TO_PROD_LIST]
list_positions.pop(TO_PROD_LIST)
to_production  = trello.lists.get_card(id)

dev_id      = list_names[DEV_LIST]
list_positions.pop(DEV_LIST)
development = trello.lists.get_card(dev_id)

test_id     = list_names[TEST_LIST]
list_positions.pop(TEST_LIST)
testing     = trello.lists.get_card(test_id)

all_catalog = plistlib.readPlist(os.path.join(MUNKI_PATH, 'catalogs/all'))

missing = []
for item in all_catalog:
    name = item['name'] + ' '+item['version']
    found = name_in_list(name, to_development, development, testing, to_testing, to_production)
    if not found:
        missing.append(item)

# Any item that isn't in any board needs to go in to the right one
for item in missing:
    name = item['name'] + ' '+item['version']
    comment = '**System Info**\nName: %s\nVersion: %s' % (item['name'], item['version'])
    for catalog in item['catalogs']:
        if catalog == TEST_CATALOG:
            card = trello.lists.new_card(test_id, name)
            trello.cards.new_action_comment(card['id'], comment)

        if catalog == DEV_CATALOG:
            card = trello.lists.new_card(dev_id, name)
            trello.cards.new_action_comment(card['id'], comment)


run_makecatalogs = 0

# Automatically migrate packages from testing to production
# based on their due date.
# N.B this will honour manually set due dates
automigrations = []
if AUTO_STAGE_TO_PROD:
   automigrations =  find_auto_migrations(testing)

if len(to_production) or len(automigrations):
# For production we either use date + suffix or the production list.
# However, we only need check these lists if there are things to move
# into production:
    prod_title = None
    list_prefix = date.today().strftime(DATE_FORMAT)

    prod_id = get_dated_board_id(trello, BOARD_ID, list_prefix,
       PRODUCTION_SUFFIX, PROD_LIST,list_names, list_positions)

    if not prod_id:
        fail('No id found (or created) for %s\n' % prod_title)

# Note that automigrations will be empty if AUTO_STAGE_TO_PROD is false
if len(automigrations):
    msg = 'Auto migrated from %s to production as past due date' % TEST_LIST
    rc = migrate_packages(trello, automigrations, prod_id, PROD_CATALOG,
                               message=msg, auto_move=True)
    run_makecatalogs = run_makecatalogs + rc

# Find the items that are in To Production and change the pkginfo
if len(to_production):

    rc = migrate_packages(trello, to_production, prod_id, PROD_CATALOG)
    run_makecatalogs = run_makecatalogs + rc

# Automatically migrate packages from development to test
# based on their due date.
# N.B this will honour manually set due dates
if AUTO_STAGE_TO_TEST:
   automigrations =  find_auto_migrations(development)
   if len(automigrations):
       msg = 'Auto migrated from %s to %s as past due date' % (DEV_LIST, TEST_LIST)
       rc = migrate_packages(trello, automigrations, test_id, TEST_CATALOG, message=msg, auto_move=True)
       run_makecatalogs = run_makecatalogs + rc

# Move cards in to_testing to testing. Update the pkginfo
if len(to_testing):
    due_days=0
    if opts.test_stage_days:
        due_days=opts.test_stage_days

    rc = migrate_packages(trello, to_testing, test_id, TEST_CATALOG, due=due_days)
    run_makecatalogs = run_makecatalogs + rc

# Move cards in to_development to development. Update the pkginfo
if len(to_development):
    due_days=0
    print "DUE:", opts.dev_stage_days
    if opts.dev_stage_days:
        due_days=opts.dev_stage_days

    rc = migrate_packages(trello, to_development, dev_id, DEV_CATALOG, due=due_days)
    run_makecatalogs = run_makecatalogs + rc

# Have a look at development and find any items that aren't in the all
# catalog anymore
# XXX(TODO): if staging check this list as it may have changed
update_card_list(trello, development, all_catalog)

# Have a look at testing and find any items that aren't in the all
# catalog anymore
# XXX(TODO): if staging check this list as it may have changed
update_card_list(trello, testing, all_catalog)

# Holy crap, we're done, run makecatalogs
if run_makecatalogs:
    task = execute([MAKECATALOGS, MUNKI_PATH])
