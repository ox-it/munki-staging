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

from .rssfeed import MediaContentImage, MunkiStagingRSSItem
from datetime import datetime

from shutil import copy2
import os
from string import join,atoi
from datetime import date, datetime, timedelta

# From http://stackoverflow.com/questions/3167154/how-to-split-a-dos-path-into-its-components-in-python
def split_path(p):
    a,b = os.path.split(p)
    return (split_path(a) if len(a) and len(b) else []) + [b]

class PackageList(dict):
 
   def add_package(self,package):
       self[package.key()] = package

   def add_or_update_package(self,package):
       if self.has_key(package.key()):
           self.update_package(package)
       else:
           self.add_package(package)

   def update_package(self, source_package):
       pkey = source_package.key()
       dest_package = self[pkey]
       
       if source_package.pkgsinfo is not None:
           dest_package.pkgsinfo = source_package.pkgsinfo 

       if source_package.munki_repo is not None:
           dest_package.munki_repo = source_package.munki_repo 

       if source_package.trelloboard is not None:
           dest_package.trelloboard = source_package.trelloboard 

       if source_package.trello_card_id is not None:
           dest_package.trello_card_id = source_package.trello_card_id 

       if source_package.trello_catalog is not None:
           dest_package.trello_catalog = source_package.trello_catalog 

       if source_package.trello_list_id is not None:
           dest_package.trello_list_id = source_package.trello_list_id 

       if source_package.trello_due_date is not None:
           dest_package.trello_due_date = source_package.trello_due_date 

   def missing_trello_card(self):
        return PackageListMissing(self)

   def in_list(self, trello_list_id):
        return PackageListInTrelloList(trello_list_id, self)

   def auto_stage(self):
        return PackageListAutoStageList(self)
      

class PackageListAutoStageList:

   def __init__(self, package_list):
       self.package_list = package_list
       self.key_list = package_list.keys()
       self.now = datetime.utcnow()

   def __iter__(self):
       return self

   def next(self):
       while len(self.key_list) > 0:
           pkg = self.key_list.pop()
           package = self.package_list[pkg]

           if package.trello_due_date is None:
               continue
        
           if package.trello_catalog.autostage == False:
               continue

           # Schedule for this catalog
           if package.trello_catalog.autostage_schedule is not None:
               # There is a schedule, so we check it
               if package.trello_catalog.autostage_schedule.stage_now() == False:
                   continue
           
           difference = self.now - package.trello_due_date 
           if difference.total_seconds() > 0:
               return package
       
       raise StopIteration()

class PackageListInTrelloList:

   def __init__(self, trello_list_id, package_list):

       self.trello_list_id = trello_list_id
       self.package_list = package_list
       self.key_list = package_list.keys()

   def __iter__(self):
       return self

   def next(self):
       while len(self.key_list) > 0:
           pkg = self.key_list.pop()
           if      self.package_list[pkg].trello_list_id is not None \
              and  self.package_list[pkg].trello_list_id \
                       == self.trello_list_id:
               return self.package_list[pkg]
       
       raise StopIteration()
      
    
class PackageListMissing:
   def __init__(self, package_list):
       self.package_list = package_list
       self.key_list = package_list.keys()

       self.key_list.reverse() # pop takes the last element of the list

   def __iter__(self):
       return self

   def next(self):
       while len(self.key_list) > 0:
           pkg = self.key_list.pop()
           if self.package_list[pkg].trello_card_id is None:
               return self.package_list[pkg]
       
       raise StopIteration()
      
       
class Package:
   
    def __init__(self, name, version, 
                  pkgsinfo=None,
                  munki_catalogs=None, 
                  munki_repo=None, # Might not need this
                  trelloboard=None,
                  trello_card_id=None,
                  trello_catalog=None, # Might not need this
                  trello_list_id=None, # Might not need this
                  trello_due_date=None, # Might not need this
                 ):

        self.name    = name
        self.version = version
              
        self.munki_repo = munki_repo
        self.munki_catalogs = munki_catalogs

        self.pkgsinfo = pkgsinfo
        self.trelloboard = trelloboard
        self.trello_card_id = trello_card_id
        self.trello_catalog = trello_catalog
        self.trello_list_id = trello_list_id

        self.trello_due_date = trello_due_date

    def __unicode__(self):
        return self.__str__()

    def __str__(self):
        return 'package: %s %s' % (self.name, self.version)

    def key(self):
        return '%s %s' % (self.name, self.version)
 
    def add_trello_card(self, trelloboard):
        self.trelloboard = trelloboard
        self.trelloboard.add_card_for_package(self)

        self.set_trello_due_date()
        # Flag for update (to regenerate RSS feeds if any)
        # This is a bit gratitous, but the only other way
        # is to add a seperate flag for this ... 
        self.munki_repo.update_munki_required(flag=True)

    def move_trello_list(self, trello_catalog):

       # In order to move we must already exist in trello
       if self.trelloboard is None:
           raise ValueError('Package %s does not belong to a trello board'\
                              % self.key() )

       if trello_catalog.create_list is None:
           trello_catalog.create_new_list()

       # Move card: if autostaging must set due date
       # Move card: if stage_days must set due date

       card_id = self.trello_card_id
       list_id = trello_catalog.create_list['id']
       self.trelloboard.trello.cards.update_idList(card_id, list_id)

       self.trello_catalog = trello_catalog
       self.trello_list_id = list_id

       # If people aren't autostaging, then resetting the due date
       # might be unhelpful:
       self.reset_due_date()

       # Set the due date (if autostaging is on)
       self.set_trello_due_date()

       # Check to see if we need to move the package to a different
       # repository
       migrate_packages = 1
       if self.munki_repo is None:
           print "ERROR: package %s does not have a munki repository" % self
           migrate_packages = 0

       if self.trello_catalog.munki_repo is None:
           print "ERROR: trello catalog %s does not have a munki repository" % self.trello_catalog.list_name
           migrate_packages = 0

       if migrate_packages == 0:
           raise ValueError('Missing munki repository before migration check for package %s' % self) 

       if self.munki_repo.name != self.trello_catalog.munki_repo.name:
           self.migrate_package()

    def migrate_package(self):
       
          print "Migrating package from", \
                self.munki_repo.name,"to",\
                self.trello_catalog.munki_repo_name

          if self.trello_catalog.munki_repo is None:
             import sys
             print "CAN'T MIGRATE to empty repo !"
             sys.exit(1)
          
          old_repo_base = self.munki_repo.munki_path
          new_repo_base = self.trello_catalog.munki_repo.munki_path

          # Move: 
          #   pkgsinfo file
          #   installer items
          #   icons
          # but in the reverse order (as the repository may not work
          # if there is a valid pkgsinfo file and no package)

          # XXX CHECK FOR ERRORS !!!!

          # icon file (may not exist)
          icon_path = self.get_munki_icon()
          if icon_path is not None:
              old_icon_path = os.path.join(old_repo_base, icon_path)
              new_icon_path = os.path.join(new_repo_base, icon_path)
              new_icon_dir  = os.path.dirname(new_icon_path)
              if not os.path.isdir(new_icon_dir):
                  os.makedirs(new_icon_dir)

              if not os.path.isfile(new_icon_path):  # May exist already
                  copy2(old_icon_path, new_icon_path)    # Copy old -> new

          #   installer_item_location (aka .dmg file)
          pkgsinfo = self.munki_repo.read_pkgsinfo(self.pkgsinfo)
          installer_item_location = pkgsinfo['installer_item_location']
          old_installer_path = os.path.join(old_repo_base, 'pkgs',
                                            installer_item_location)
          new_installer_path = os.path.join(new_repo_base, 'pkgs',
                                            installer_item_location)
          # MAKE PATH TO PKG FILE
          new_basedir = os.path.dirname(new_installer_path)
          if not os.path.isdir(new_basedir):
              os.makedirs(new_basedir)
          copy2(old_installer_path, new_installer_path)
          
          new_pkgsinfo = self.get_new_pkgsinfo( old_repo_base, new_repo_base )

          new_pkgdir = os.path.dirname(new_pkgsinfo)
          if not os.path.isdir(new_pkgdir):
              os.makedirs(new_pkgdir)

          copy2(self.pkgsinfo, new_pkgsinfo)
 
          # Clean up *empty dirs* ?
          os.unlink(old_installer_path)
          os.unlink(self.pkgsinfo)

          # Update repo related meta data and flag for updates
          self.pkgsinfo   = new_pkgsinfo
          #
          self.munki_repo.update_munki_required(flag=True)
          self.trello_catalog.munki_repo.update_munki_required(flag=True)
          #
          self.munki_repo = self.trello_catalog.munki_repo


    def get_new_pkgsinfo(self, oldroot, newroot):

        pkgpath_array      = split_path( os.path.normpath(self.pkgsinfo) )
        pkgpath_array_loop = split_path( os.path.normpath(self.pkgsinfo) )
        oldroot_array      = split_path( os.path.normpath(oldroot) )

        for dir in pkgpath_array_loop:
            if len(oldroot_array) > 0 and dir == oldroot_array[0]:
                pkgpath_array.pop(0)
                oldroot_array.pop(0)
            else:
                break

        newpkgs = join(pkgpath_array, os.sep)
        return os.path.join(newroot,newpkgs)

    def move_munki_catalog(self, trello_catalog):
        catalog = trello_catalog.catalog_name
        self.munki_repo.update_pkgsinfo_catalog(self.pkgsinfo, catalog)
        self.munki_catalogs = [catalog]

    def reset_due_date(self):
        self.trelloboard.trello.cards.update_due(self.trello_card_id, None)
        self.trello_due_date = None

    def get_due_date(self, default_due):
        pkgsinfo = self.munki_repo.read_pkgsinfo(self.pkgsinfo)
        if pkgsinfo.has_key('munki_staging'):
            pkgsinfo_mstagingcfg = pkgsinfo['munki_staging']
            if pkgsinfo_mstagingcfg.has_key('stage_days'): 
                days = atoi(pkgsinfo_mstagingcfg['stage_days'])
                delta = timedelta(days=days)
                now = datetime.utcnow()
                due_date = now + delta
                due_date_epoch = due_date
                due_date_str   = due_date.strftime('%Y-%m-%dT%H:%M:%S.000Z')
                return due_date_str

        return default_due

    def set_trello_due_date(self):
       # Get the default from the catalog
       due_date = self.trello_catalog.due_date()
       # If there is a due date we  consult the pkgsinfo file to see
       # if an override has been set
       # If there is no due date we assume we are not autostaging, and
       # thus do not set a date
       if due_date:
           due_date = self.get_due_date(due_date) 
           self.trelloboard.trello.cards.update_due(self.trello_card_id,
                                                    due_date)

           self.trello_due_date = self.trello_catalog.due_date_epoch

    def add_trello_comment(self, message):
        self.trelloboard.trello.cards.new_action_comment(self.trello_card_id, message)

    def auto_stage(self):

        # Find out where we are moving
        try:
            dest_catalog = self.trello_catalog.stage_to()
        except ValueError, msg:
           print 'Cannot stage %s from %s (%s)' %  (self, self.trello_catalog , msg)
           return
 
        # Comment to add to trello card
        message = 'Auto staged from %s to %s (as past due date %s)' \
            % (self.trello_catalog.catalog_name, dest_catalog.catalog_name, self.trello_due_date)

        # Reset trello due date
        self.reset_due_date()

        # Move trello list (after reset, as date may get set when we 
        # migrate
        self.move_trello_list(dest_catalog)

        # Update munki catalog
        self.move_munki_catalog(dest_catalog)

        self.add_trello_comment(message)

    def rss_item(self, link_template, guid_template, icon_url_template):
        title = self.get_display_name()
        description = self.get_description()
        # XXX todo: fix link to be a nice link, but guid unchanging per version
        link = link_template % { 'name': self.name,
                                 'version': self.version,
                                 'catalog': self.munki_catalogs[0] }
        guid = guid_template % { 'name': self.name,
                                 'version': self.version,
                                 'catalog': self.munki_catalogs[0] }
        pubdate = self.trelloboard.get_last_move(self.trello_card_id,
                                                 self.trello_catalog)

        icon_path = self.get_munki_icon()
        icon_url = None
        if icon_path is not None:
            icon_url = icon_url_template % { 'icon_path': icon_path }

        return MunkiStagingRSSItem( title       = title,
                                   link        = link,
                                   description = description,
                                   guid        = guid,
                                   pubDate     = pubdate,
                                   icon_url    = icon_url,
                                  )

    def get_description(self):
       # open 
       pkgsinfo = self.munki_repo.read_pkgsinfo(self.pkgsinfo)
       try:
           descr =  pkgsinfo['description']
       except KeyError:
           print 'Package %s has no description' % (self,)
           descr='No description in pkgsinfo file'

       return descr

    def get_munki_icon(self):
       icon = self.munki_repo.get_icon(self.pkgsinfo)
       return icon

    def get_display_name(self):
       pkgsinfo = self.munki_repo.read_pkgsinfo(self.pkgsinfo)
       return pkgsinfo.get('display_name') or pkgsinfo.get('name')

    def card_name(self):
        title = self.get_display_name()
        return '%s %s' % (title, self.version)
  


