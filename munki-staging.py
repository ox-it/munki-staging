#!/usr/bin/python
#
# This software is Copyright (c) 2015 University of Oxford
# 
# This work is made avaiable to you under the terms of the Apache
# License, Version 2.0; you may not use this source code except in
# compliance with the License. You may obtain a copy of the License at
# 
# http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied. See the License for the specific language governing
# permissions and limitations under the License.
#

import munkistaging.default_settings as default_settings

from munkistaging.config import MunkiStagingConfig

from munkistaging import PackageList, Package
from munkistaging.munki_repo import MunkiRepository
from munkistaging.munki_trelloboard import MunkiTrelloBoard

import os
import datetime
import sys

try:
    from munkistaging.rssfeed import MunkiStagingRSSFeed
except:
    pass

print "Reading configuration .... "

config = MunkiStagingConfig(allow_no_value=True)
config.cli_parse()
config.read_config()

# Build a list of all packages we know about
packagelist = PackageList()

makecatalogs = config.get_makecatalogs()
repo_count = 0
for mrepo_cfg in config.configured_munki_repositories():
    munki_repo = MunkiRepository(mrepo_cfg, makecatalogs)
    print "Finding packages in repository", munki_repo.name, "..."
    repo_count = repo_count + 1
    for package in munki_repo.packages():
        packagelist.add_or_update_package(package)

    # Remember for future use
    config.add_munki_repo( munki_repo )

if repo_count == 0:
    print "No munki repositories configured"
    print "  if you are using a configuration file you must specify at least"
    print "  one munki_repo_<name> section"
    sys.exit(1)

print "Building Trello board data .... "
munki_trello = MunkiTrelloBoard(config)

print "Building Munki repository data and packages .... "
# Build the catalog lists
# (to allow us to only consisder cards in the relevant lists)
munki_trello.setup_catalog_lists()
# XXX(aaron): calling this here is probably a bug, as it shouldn't need to
#             be here other things should call this before they need it;
#             this was on line 66, but again, I'm not sure if it needed to
#             be there, as it should be called by the time it
#             gets there.

print "Building Package list from Trello .... "
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

# Migrate the packages from the 'To' trello list into the main list,
# updating the Munki in formation as we go
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

autostage_schedule = config.autostage_schedule()
if autostage_schedule is None or autostage_schedule.stage_now():
    print "About to autostage ... "
    for package in packagelist.auto_stage():
        package.auto_stage()   


# Use run_makecatalogs as a flag to signify if things have changed
# and thus we need to update the RSS feeds
# (we need to check this before run_update_catalogs as this should
# reset the flag)
#
update_rssfeeds = False

for key in config.repositories.keys():
  
    if config.repositories[key].run_makecatalogs:
        update_rssfeeds = True

    print "Updating munki catalogs in", key
    config.repositories[key].run_update_catalogs()

if update_rssfeeds and config.has_section('rssfeeds'):
    print "Building RSS feed items ..."

    rssdir = config.get_rssdirectory()
    rssfeeds = {}
    rss_link_template = config.get_rss_link_template()
    guid_template     = config.get_guid_link_template()
    icon_url_template = config.get_rss_icon_url_template()

    for pkg in packagelist.keys():
        package = packagelist[pkg]
        catalog = package.munki_catalogs[0]
        if not rssfeeds.has_key(catalog):
            rssfeeds[catalog] = []
        rssfeeds[catalog].append( package.rss_item(rss_link_template, guid_template, icon_url_template) )

    if not os.path.isdir(rssdir):
        os.mkdir(rssdir)

    catalog_link_template = config.get_catalog_link_template()
    description_template = config.get_description_template()
    for feed in rssfeeds.keys():
        items = rssfeeds[feed]
        rss = MunkiStagingRSSFeed(
                 title = '%s Catalog' % feed,
                 link  = catalog_link_template % { 'catalog': feed },
                 description = description_template % { 'catalog': feed },
                 lastBuildDate = datetime.datetime.now(),
                 items = items )
        
        feedfile = '%s.xml' % feed
        rss.write_xml( open( os.path.join(rssdir, feedfile), 'w') ) 

for pkg in packagelist.keys():
    package = packagelist[pkg]
#    print package.munki_repo.name

sys.exit(0)
