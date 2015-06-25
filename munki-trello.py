#!/usr/bin/python
import trello as trellomodule
import plistlib
import subprocess
import os
import sys
from datetime import date
import requests
import json
import optparse

from ConfigParser import SafeConfigParser

# Default settings (overridden by config file and command line options)
DEFAULT_CONFIG_FILE_LOCATIONS= [
    '/etc/munki-trello/munki-trello.cfg',
    'munki-trello.cfg'
]
DEFAULT_DEV_LIST = "Development"
DEFAULT_TEST_LIST = "Testing"
DEFAULT_TO_DEV_LIST = "To Development"
DEFAULT_TO_TEST_LIST = "To Testing"
DEFAULT_TO_PROD_LIST = "To Production"
DEFAULT_PRODUCTION_SUFFIX = "Production"
DEFAULT_MUNKI_PATH = "/Volumes/Munki"
DEFAULT_MAKECATALOGS = "/usr/local/munki/makecatalogs"
DEFAULT_MUNKI_DEV_CATALOG = "development"
DEFAULT_MUNKI_TEST_CATALOG = "testing"
DEFAULT_MUNKI_PROD_CATALOG = "production"

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

def get_next_position(lists, to_dev_id, dev_id, to_test_id, test_id, to_prod_id):
    # exclude the five 'system' lists and the one we just made
    max_id = 0
    for list in lists:
        if list['id'] == dev_id or list['id'] == to_dev_id or list['id'] == test_id or list['id'] == to_prod_id or list['id'] == to_test_id:
            continue
        if list['pos'] > max_id:
            max_id = list['pos']

    # we should now have the highest position
    if max_id == 0:
        return 1000000
    else:
        return max_id - 1

def get_app_version(card_id):
    cards = trello.cards.get_action(card_id)
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
                             dest_list_id, dest_catalog_name):

    run_makecatalogs = 0
  
    # create a list of pkgsinfo files
    pkgsinfo_dirwalk = os.walk(os.path.join(MUNKI_PATH,'pkgsinfo'),
                                                            topdown=False)

    # Find items from the source list, update pkginfo, and change trello
    # card to dest
    for card in source_cards:
        app_name, version = get_app_version(card['id'])
        
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

               if plist['name'] == app_name \
                   and plist['version'] == version:

                   plist['catalogs'] = [dest_catalog_name]

                   plistlib.writePlist(plist, pkgsinfo)

                   print 'UPDATING'
                   trello_connection.cards.update_idList(card['id'], dest_list_id)
                   run_makecatalogs = run_makecatalogs + 1
                   break
           if plist != None:
              break

    return run_makecatalogs

def read_config(cmdopts):

    config = SafeConfigParser(allow_no_value=True)

    # Setr up defaults 
    config.add_section('main')
    config.set('main', 'boardid', None)
    config.set('main', 'key', None)
    config.set('main', 'token', None)
    config.set('main', 'makecatalogs', DEFAULT_MAKECATALOGS)
    config.set('main', 'repo_path', DEFAULT_MUNKI_PATH)

    config.add_section('development')
    config.set('development', 'list', DEFAULT_DEV_LIST)
    config.set('development', 'catalog', DEFAULT_MUNKI_DEV_CATALOG)
    config.set('development', 'to_list', DEFAULT_TO_DEV_LIST)

    config.add_section('testing')
    config.set('testing', 'list', DEFAULT_TEST_LIST)
    config.set('testing', 'catalog', DEFAULT_MUNKI_TEST_CATALOG)
    config.set('testing', 'to_list', DEFAULT_TO_PROD_LIST)

    config.add_section('production')
    config.set('production', 'catalog', DEFAULT_MUNKI_PROD_CATALOG)
    config.set('production', 'to_list', DEFAULT_TO_PROD_LIST)
    config.set('production', 'suffix', DEFAULT_PRODUCTION_SUFFIX)

    config_file_locations = DEFAULT_CONFIG_FILE_LOCATIONS

    if cmdopts.config:
        config_file_locations.append(cmdopts.config)
   
    rc = config.read(config_file_locations)
    print rc
    #print config_file_locations

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

    if not cmdopts.to_dev_list:
        cmdopts.to_dev_list = config.get('development', 'to_list')

    if not cmdopts.dev_list:
        cmdopts.dev_list = config.get('development', 'list')

    if not cmdopts.dev_catalog:
        cmdopts.dev_catalog = config.get('development', 'catalog')

    if not cmdopts.to_test_list:
        cmdopts.to_test_list = config.get('testing', 'to_list')

    if not cmdopts.test_list:
        cmdopts.test_list = config.get('testing', 'list')

    if not cmdopts.test_catalog:
        cmdopts.test_catalog = config.get('testing', 'catalog')

    if not cmdopts.to_prod_list:
        cmdopts.to_prod_list = config.get('production', 'to_list')

    if not cmdopts.prod_catalog:
        cmdopts.prod_catalog = config.get('production', 'catalog')

    if not cmdopts.suffix:
        cmdopts.suffix = config.get('production', 'suffix')

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

o.add_option("--to-prod-list",
    help=("Name of the 'To Production' Trello list. Defaults to '%s'. "
              % DEFAULT_TO_PROD_LIST))

o.add_option("--suffix",
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
DEV_CATALOG = opts.dev_catalog
TEST_CATALOG = opts.test_catalog
PROD_CATALOG = opts.prod_catalog
PRODUCTION_SUFFIX = opts.suffix
MUNKI_PATH = opts.repo_path
MAKECATALOGS = opts.makecatalogs

if not os.path.exists(MUNKI_PATH):
    fail('Munki path not accessible')

trello = trellomodule.TrelloApi(KEY)
trello.set_token(TOKEN)

lists = trello.boards.get_list(BOARD_ID)

for list in lists:

    if list['name'] == TO_DEV_LIST:
        to_dev_id = list['id']

    if list['name'] == DEV_LIST:
        dev_id = list['id']

    if list['name'] == TEST_LIST:
        test_id = list['id']

    if list['name'] == TO_TEST_LIST:
        to_test_id = list['id']

    if list['name'] == TO_PROD_LIST:
        to_prod_id = list['id']
        

all_catalog = plistlib.readPlist(os.path.join(MUNKI_PATH, 'catalogs/all'))

to_development = trello.lists.get_card(to_dev_id)
development = trello.lists.get_card(dev_id)
testing = trello.lists.get_card(test_id)
to_testing = trello.lists.get_card(to_test_id)
to_production = trello.lists.get_card(to_prod_id)

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


moved_to_prod = []
if len(to_production):
    list_title = date.today().strftime("%d/%m/%y")
    list_title = str(list_title) + " " + PRODUCTION_SUFFIX
    found = False
    for list in lists:
        if list['name'] == list_title:
            found = True
            new_list = list
            break

    if found == False:
        position = get_next_position(lists, to_dev_id, dev_id, to_test_id, test_id, to_prod_id)
        new_list = trello.boards.new_list(BOARD_ID, list_title)
        update_pos(new_list['id'], position)

run_makecatalogs = 0 
# Find the items that are in To Production and change the pkginfo
if len(to_production):
    rc = migrate_packages(trello, to_production, new_list['id'], PROD_CATALOG)
    run_makecatalogs = run_makecatalogs + rc

# Move cards in to_testing to testing. Update the pkginfo
if len(to_testing):
    rc = migrate_packages(trello, to_testing, test_id, TEST_CATALOG)
    run_makecatalogs = run_makecatalogs + rc

# Move cards in to_development to development. Update the pkginfo
if len(to_development):
    rc = migrate_packages(trello, to_development, dev_id, DEV_CATALOG)
    run_makecatalogs = run_makecatalogs + rc

# Have a look at development and find any items that aren't in the all catalog anymore
for card in development:
    app_name, version = get_app_version(card['id'])
    found = False
    for item in all_catalog:
        if item['name'] == app_name and item['version'] == version:
            found = True
    if not found:
        trello.cards.delete(card['id'])
        
# Have a look at testing and find any items that aren't in the all catalog anymore
for card in testing:
    app_name, version = get_app_version(card['id'])
    found = False
    for item in all_catalog:
        if item['name'] == app_name and item['version'] == version:
            found = True
    if not found:
        trello.cards.delete(card['id'])
# Holy crap, we're done, run makecatalogs
if run_makecatalogs:
    task = execute([MAKECATALOGS, MUNKI_PATH])
