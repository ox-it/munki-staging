#!/usr/bin/python

import munkitrello.default_settings as default_settings

from munkitrello.config import MunkiTrelloConfig

from munkitrello import PackageList, Package
from munkitrello.munki_repo import MunkiRepository
from munkitrello.munki_trelloboard import MunkiTrelloBoard

import os
import datetime
import sys

try:
    import PyRSS2Gen
except:
    pass

print "Reading configuration .... "

config = MunkiTrelloConfig(allow_no_value=True)
config.cli_parse()
config.read_config()

app_key = config.get_app_key()

print "Building Munki repository data .... "

munki_repo = MunkiRepository(config.get_repo_path(),
                             config.get_makecatalogs() ) 

print "Building Trello board data .... "

munki_trello = MunkiTrelloBoard(config)

# Build a list of all packages we know about

packagelist = PackageList()

print "Building Pacakge list from Munki Repo .... "
for package in munki_repo.packages():
    packagelist.add_or_update_package(package)

print "Building Pacakge list from Trello .... "
for package in munki_trello.packages():
    if packagelist.has_key( package.key() ):
        packagelist.update_package(package)
    else:
       print "Deleting card without a package %s " % package.key()
       munki_trello.delete_package(package)

# At this point, we want to
#   * find any packages missing a trello card a create the card
#   * move packages in the 'To' trello lists into the correct catalog
#   * auto stage (if auto staging)
#   * Remove any trello cards without packages
#

print "Finding missing packages .... "

# Find packages not in the trello boards
# N.B. Will add packages according to underlying munki catalog
# (and hence into production if that is where it says)
# This is a change from the upstream behaviour, and may be a bug
for pkg in packagelist.missing_trello_card():
   print "Missing: ", pkg
   pkg.add_trello_card(munki_trello)

print "Migrating To lists .... "

# Call setup just in case this hasn't happened yet 
# (XXX) Todo: fix this inelegance
munki_trello.setup_catalog_lists()
# Migrate the packages from the 'To' trello list into the main list,
# updating the Munki information as we go
#
# (XXX) Todo: is there a right way to do this, or don't we
#             care ? Origingally this went prod, testing, unstable
for catalog_name in munki_trello.catalog_lists.keys():

   catalog = munki_trello.catalog_lists[catalog_name] 
   to_id = catalog.to_list['id']
  
   for package in packagelist.in_list(to_id):
      print "Moving package %s" % package
      package.move_munki_catalog(catalog)
      package.move_trello_list(catalog)

# Note: no package is currently in a 'To' list, 
# so we can autostage if desired

for package in packagelist.auto_stage():
    package.auto_stage()   

# Use run_makecatalogs as a flag to signify if things have changed
# and thus we need to update the RSS feeds
# (we need to check this before run_update_catalogs as this should
# reset the flag)
update_rssfeeds = munki_repo.run_makecatalogs
#
munki_repo.run_update_catalogs()

if update_rssfeeds and config.has_section('rssfeeds'):

    print "Building RSS feed items ..."

    rssdir = config.get_rssdirectory()
    rssfeeds = {}
    rss_link_template = config.get_rss_link_template()

    for pkg in packagelist.keys():
        package = packagelist[pkg]
        catalog = package.munki_catalogs[0]
        if not rssfeeds.has_key(catalog):
            rssfeeds[catalog] = []
        rssfeeds[catalog].append( package.rss_item(rss_link_template) )

    if not os.path.isdir(rssdir):
        os.mkdir(rssdir)

    catalog_link_template = config.get_catalog_link_template()
    description_template = config.get_description_template()
    for feed in rssfeeds.keys():
        items = rssfeeds[feed]
        rss = PyRSS2Gen.RSS2(
                 title = '%s Catalog' % feed, 
                 link  = catalog_link_template % feed,
                 description = description_template % feed,
                 lastBuildDate = datetime.datetime.now(),
                 items = items )
        
        feedfile = '%s.xml' % feed
        rss.write_xml( open( os.path.join(rssdir, feedfile), 'w') ) 


sys.exit(0)

