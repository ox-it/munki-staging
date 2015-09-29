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

from . import Package

import trello
import re
import requests
import json

from datetime import date, datetime, timedelta
from string import atoi

class MunkiTrelloBoard:

    card_comment = '**System Info**\nName: %s\nVersion: %s'
    name_version_re = re.compile('^\*\*System Info\*\*\sName: (.*)\sVersion: (.*)$', flags=re.MULTILINE)

    def __init__(self, config):

        self.config = config

        self.app_key   = self.config.get_app_key()
        self.app_token = self.config.get_app_token()
        self.board_id  = self.config.get_boardid()
      
        self.trello =  trello.TrelloApi(self.app_key)
        self.trello.set_token(self.app_token)
   
        self.trello_boards = trello.Boards(self.app_key, self.app_token)

        # We map Trello lists into Munki catalogs
        #
        # Each Munki Catalog will have multiple lists:
        #   * a 'To' list
        #   * Either:
        #       * a list representing the munki catalog
        #       * a dated set of lists representing the munki catalog
        #
        self.catalog_lists = None
        self.list_id_catalog = None

        self.trello_id_list   = None
        self.trello_name_list = None

        self.cards = None # List ... currently

    def setup_catalog_lists(self):

       if self.catalog_lists is not None:
           return

       self.catalog_lists = {}
       self.list_id_catalog = {}
       for catalog_config in self.config.munki_catalogs():
          name = catalog_config['catalog']
          date_format = self.config.get_date_format()
          rc =  self.setup_catalog(catalog_config, date_format)
          self.catalog_lists[name] = rc
          for list_id in rc.get_list_ids():
              self.list_id_catalog[list_id] = rc

       return 

    def packages(self):

        if self.cards is not None:
            return self.cards

        self.setup_catalog_lists()

        self.cards = []
        for card in self.trello_boards.get_card(self.board_id):

            listid = card['idList']
            if self.list_id_catalog.has_key(listid):
                trello_catalog = self.list_id_catalog[ card['idList'] ]
            else:
                print "XXX card %s not in recognised list\n" % card['name']
                continue

            try:
                name, version = self.get_name_version_from_card( card['id'] )
            except Exception, e:
                raise ValueError('Got exception %s trying to find version from card %s' % (e, card['name']) )

            due = None 
            if card['due'] is not None:
                # Assumptions here:
                # Trello will always return UTC dates in an ISO standard format
                # Due dates are not going to be accurate to more than a second
                # (hence the .000 in the format)
                due = datetime.strptime(card['due'], '%Y-%m-%dT%H:%M:%S.000Z')
      
            package = Package(name, version,
                              trelloboard=self,
                              trello_card_id=card['id'],
                              trello_list_id=card['idList'],
                              trello_catalog=trello_catalog,
                              trello_due_date=due)

            self.cards.append(package)

        return self.cards
   
    def get_name_version_from_card(self, cardid):

        actions = self.trello.cards.get_action(cardid, filter='commentCard')
        actions.reverse() # Look at ealier comments first

        for action in actions:
            match = self.name_version_re.match(action['data']['text'])
            if match:
               return match.group(1,2)

        raise ValueError('Could not find name and version in card id %s' %cardid
)

    def add_card_for_package(self, package):

        card_action_comment = self.card_comment % ( package.name, package.version)

        catalog_list = self.list_from_catalog( package.munki_catalogs[0] )
        new_card = catalog_list.new_card( package.card_name(), card_action_comment )

        package.trello_card_id = new_card['id']
        package.trello_list_id = new_card['idList']
        package.trello_catalog = catalog_list

        return
   
    def list_from_catalog(self, catalog_list ):
        # The assumption that is made is that each card (package version) 
        # belongs to a single (munki) catalog. This is an assumption that
        # is not necessarily true of the underlying Munki repository.
        #
        # We work around this by only using the first item in the catalog
        # list.
        # 
        # This may be considered a bug, or a feature

        if self.catalog_lists is None:
            self.setup_catalog_lists()

        return self.catalog_lists[catalog_list]

    def setup_catalog(self, config_dict, date_format):

         list_name = config_dict['list']
         catalog_name = config_dict['catalog']

         to_list_name = config_dict.get('to_list', 'To %s' % list_name)
         stage_days = atoi(config_dict.get('stage_days', '0'))
         autostage  = config_dict.get('autostage', False)
         if autostage == 1 or autostage == '1':
             autostage = True
         if autostage == 0 or autostage == '0':
             autostage = False
         stage_to = config_dict.get('stage_to', None)
         stage_from = config_dict.get('stage_from', None)
         dated_lists = config_dict.get('dated_lists', False)
         munki_repo_name = config_dict.get('munki_repo', None)
         munki_repo = None
         if munki_repo_name is not None:
            if self.config.repositories.has_key(munki_repo_name):
               munki_repo = self.config.repositories[munki_repo_name]
            
  
         return MunkiTrelloBoardCatalogList(self,
             list_name, catalog_name, to_list_name, stage_days, autostage,
             stage_to, stage_from, dated_lists, date_format,
             munki_repo_name, munki_repo)

    def get_lists(self):

        if self.trello_id_list is not None:
            return

        self.trello_id_list   = {}
        self.trello_name_list = {}
    
        tlists = self.trello.boards.get_list(self.board_id)
        for list in tlists:
            name = list['name']
            id   = list['id']

            self.trello_id_list[id]     = list
            self.trello_name_list[name] = list
 
        return
 
    def get_list_name(self, name):
        self.get_lists() 

        if self.trello_name_list.has_key(name):
            return self.trello_name_list[name]

        raise KeyError('Trello Board id %s has no list of name %s' %( self.board_id, name) ) 

    def find_list(self, name):
        self.get_lists() 

        if self.trello_name_list.has_key(name):
            return self.trello_name_list[name]
 
        return None

    def get_list_name_match(self, pattern):

        self.get_lists() 

        # Pattern is expected to be: 'date_format name'
        # where date_format is a date as used by strftime
        # we convert this into a regex by substituting '%X' with '\d+'
        # Although not prefect by any means, this should allow us
        # some scope to have custom date formats

        list_name_re = re.compile( re.sub('%\w+', '\d+', pattern) )
        rv = []
        for key in self.trello_name_list.keys():
            if list_name_re.match(key):
                rv.append(self.trello_name_list[key])

        # N.B: no check for the empty list; is this a bug ?
        return rv

    def update_postion(self, listid, position):
        url = "https://trello.com/1/lists/%s/pos" % (listid)
        put_params = { 'key': self.app_key, 'token': self.app_token }
        data_params = { 'value': position }

        resp = requests.put( url, params=put_params, data = data_params )
 
        resp.raise_for_status()
        return json.loads(resp.content)

    def create_new_list(self, list_name, position):
        list = self.trello.boards.new_list(self.board_id, list_name)
        listid = list['id']

        self.update_postion(listid, position)

        self.trello_id_list[listid]      = list
        self.trello_name_list[list_name] = list

    def get_last_move(self, cardid, catalog):
        updates = self.trello.cards.get_action(cardid, filter='updateCard')
        for update in updates:

           if not update.has_key('data'):
               next
        
           data = update['data']

           if     data.has_key('listAfter') \
              and data['listAfter']['name'] == catalog.list_name:
               return datetime.strptime(update['date'], '%Y-%m-%dT%H:%M:%S.%fZ')

        return None

    def delete_package(self, package):
        cardid = package.trello_card_id
        self.trello.cards.delete( cardid ) 


class MunkiTrelloBoardCatalogList:
    
    def __init__(self, trelloboard,  list_name, catalog_name, to_list_name,
                      stage_days, autostage, stage_to_name, stage_from_name,
                      dated_lists, date_format, munki_repo_name, munki_repo):

        self.trelloboard  = trelloboard

        self.list_name    = list_name
        self.catalog_name = catalog_name
        self.to_list_name = to_list_name
        self.stage_days   = stage_days
        self.due_date_str = None
        self.autostage    = autostage
        self.stage_to_name     = stage_to_name
        self._stage_to    = None
        self.stage_from_name   = stage_from_name
        self._stage_from  = None
        self.dated_lists  = dated_lists
        self.date_format  = date_format
        self.munki_repo_name = munki_repo_name
        self.munki_repo      = munki_repo
     
        # To list (as it is easiest being not dated)
        self.to_list = trelloboard.get_list_name(self.to_list_name)
     
        self.create_list = None
        if self.dated_lists:
            pattern = '%s %s' % ( self.date_format, self.list_name )
            self.lists = trelloboard.get_list_name_match(pattern)
            # N.B delibrately do not set create_list here
        else: 
            self.lists = [trelloboard.get_list_name(self.list_name),]
            self.create_list = self.lists[0]

        self.lists.append(self.to_list) 

        return 

    def __str__(self):
       return self.__unicode__()

    def __unicode__(self):
        return 'Catalog list for %s' % self.list_name

    def get_list_ids(self):
        return map(lambda list: list['id'], self.lists)

    def new_card(self, card_title, action_comment ):
        if self.create_list is None:
            self.create_new_list()

        listid = self.create_list['id']
        card_dict = self.trelloboard.trello.lists.new_card(listid, card_title)
        self.trelloboard.trello.cards.new_action_comment(card_dict['id'], action_comment)
        return card_dict
    
 
        raise ValueError('Not implemented yet')

    def create_new_list(self):

        prefix = date.today().strftime(self.date_format)
        create_name = '%s %s' % ( prefix, self.list_name )  
      
        clist = self.trelloboard.find_list(create_name)
        if clist != None:
            self.create_list = clist
 
            return

        position = self.to_list['pos']
        self.trelloboard.create_new_list(create_name, position)
        self.create_list = self.trelloboard.get_list_name(create_name)

    def due_date(self):

        if self.due_date_str is not None:
            return  self.due_date_str

        if self.stage_days is None or self.stage_days <= 0:
            return None
    
        # By this point stage_days is a positive integer
        delta = timedelta(days=self.stage_days)
        now = datetime.utcnow()
        due_date = now + delta
        self.due_date_epoch = due_date
        self.due_date_str   = due_date.strftime('%Y-%m-%dT%H:%M:%S.000Z')

        return self.due_date_str

    def stage_to(self):
         if self._stage_to is not None:
             return self._stage_to
      
         if self.trelloboard.catalog_lists.has_key(self.stage_to_name):
             self._stage_to = self.trelloboard.catalog_lists[self.stage_to_name]
             return self._stage_to

         raise ValueError('Cannot find catalog %s to stage_to' % self.stage_to_name)

    def stage_from(self):
         if self._stage_from is not None:
             return self._stage_from
      
         if self.trelloboard.catalog_lists.has_key(self.stage_from_name):
             self._stage_from = self.trelloboard.catalog_lists[self.stage_from_name]
             return self.stage_from

         raise ValueError('Cannot find catalog %s to stage from' % self.stage_from_name)
