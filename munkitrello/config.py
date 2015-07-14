

import re

from ConfigParser import RawConfigParser

class MunkiTrelloConfig(RawConfigParser):

    def munki_catalogs(self):
        return MunkiTrelloConfigCatalogs(self)

class MunkiTrelloConfigCatalogs:

    catalog_re = re.compile('munki_catalog_(\w+)')

    def __init__(self, munki_trello_config):
        self.config = munki_trello_config
        self.sections = munki_trello_config.sections()
    
    def __iter__(self):
        return self
   
    def next(self):
        while len(self.sections) > 0:
            section = self.sections.pop()
            rv = self.catalog_re.match(section)
            if rv:
               section_config = {}
               section_config['section_name'] = rv.group(1)
               for opt in self.config.options(section):
                   section_config[opt] = self.config.get(section, opt)
               return section_config

        raise StopIteration() 

