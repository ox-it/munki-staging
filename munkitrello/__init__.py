
from .rssfeed import MediaContentImage, MunkiTrelloRSSItem
from datetime import datetime

class PackageList(dict):
 
   def add_package(self,package):
       self[package.key()] = package

   def add_or_update_package(self,package):
       print package
       if self.has_key(package.key()):
           print 'Updating %s' % package
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
               next
           
           print package.trello_due_date
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

       self.set_trello_due_date()


    def set_trello_due_date(self):
       due_date = self.trello_catalog.due_date()
       if due_date:
           self.trelloboard.trello.cards.update_due(self.trello_card_id,
                                                    due_date)

           self.trello_due_date = self.trello_catalog.due_date_epoch

    def move_munki_catalog(self, trello_catalog):
        catalog = trello_catalog.catalog_name
        self.munki_repo.update_pkgsinfo_catalog(self.pkgsinfo, catalog)
        self.munki_catalogs = [catalog]

    def reset_due_date(self):
        self.trelloboard.trello.cards.update_due(self.trello_card_id, None)
        self.trello_due_date = None

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

    def rss_item(self, link_template, icon_url_template):
        title = self.key()
        description = self.get_description()
        # XXX todo: fix link to be a nice link, but guid unchanging per version
        link = link_template % { 'name': self.name,
                                 'version': self.version,
                                 'catalog': self.munki_catalogs[0] }
        guid = link
        pubdate = self.trelloboard.get_last_move(self.trello_card_id,
                                                 self.trello_catalog)

        icon_path = self.get_munki_icon()
        icon_url = None
        if icon_path is not None:
            icon_url = icon_url_template % { 'icon_path': icon_path }

        return MunkiTrelloRSSItem( title       = title,
                                   link        = link,
                                   description = description,
                                   guid        = guid,
                                   pubDate     = pubdate,
                                   icon_url    = icon_url,
                                  )

    def get_description(self):
       # open 
       pkgsinfo = self.munki_repo.read_pkgsinfo(self.pkgsinfo)
       return pkgsinfo['description']

    def get_munki_icon(self):
       icon = self.munki_repo.get_icon(self.pkgsinfo)
       return icon


