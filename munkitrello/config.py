
import re

from ConfigParser import RawConfigParser, _default_dict

from . import default_settings

import argparse

class MunkiTrelloConfig(RawConfigParser):

    def __init__(self, defaults=None, dict_type=_default_dict,
                 allow_no_value=False):

        RawConfigParser.__init__(self,defaults, dict_type, allow_no_value)
        self.read_config_files = -1

    def munki_catalogs(self):
        # If we have read a config file, then use it and 
        # don't allow any other overrides in for the catalogs
        if self.read_config_files >= 1:
            return MunkiTrelloConfigCatalogs(self)
   
        print "No configu"
        # If we haven't then use the CLI options (or the defaults)
        dev_config  = {}
        test_config = {}
        prod_config = {}

        dev_config['section_name'] = 'development'
        dev_config['list']         = self.cli_args.dev_list
        dev_config['to_list']      = self.cli_args.to_dev_list
        dev_config['catalog']      = self.cli_args.dev_catalog
        dev_config['stage_days']   = self.cli_args.dev_stage_days

        print dev_config
        test_config['list']        = self.cli_args.test_list
        test_config['to_list']     = self.cli_args.to_test_list
        test_config['catalog']     = self.cli_args.test_catalog
        test_config['stage_days']  = self.cli_args.test_stage_days
        test_config['autostage']   = self.cli_args.stage_test

        prod_config['list']        = self.cli_args.prod_list
        prod_config['to_list']     = self.cli_args.to_prod_list
        prod_config['catalog']     = self.cli_args.prod_catalog
        prod_config['autostage']   = self.cli_args.stage_prod

        if self.cli_args.suffix:
            prod_config['list']        = self.cli_args.suffix
            prod_config['dated_lists'] = 1

        return [ dev_config, test_config, prod_config ]

    def get_repo_path(self):
        path = default_settings.repo_path
        if self.has_option('main', 'repo_path'):
            path = self.get('main', 'repo_path')

        if self.cli_args.repo_path:
            path = self.cli_args.repo_path

        return path

    def get_makecatalogs(self):
        makecatalogs = default_settings.makecatalogs
        if self.has_option('main', 'makecatalogs'):
            makecatalogs = self.get('main', 'makecatalogs')
   
        if self.cli_args.makecatalogs:
            makecatalogs = self.cli_args.makecatalogs

        return makecatalogs

    def cli_parse(self):

        self.opts = argparse.ArgumentParser(description='Stage packages in Munki based on a trello board')

        for tuple in default_settings.cli_options:
            arg = tuple[0]
            help = tuple[1]
            defvalue = tuple[2]
            self.opts.add_argument(arg, help=help, default=defvalue)

        self.cli_args = self.opts.parse_args()

    def read_config(self):
       cfgfiles = default_settings.config_file_locations
       if self.cli_args.config:  
           cfgfiles.append(self.cli_args.config)

       self.read_config_files = self.read(cfgfiles)

    def get_app_key(self):
        return self._get_option('main', 'key')

    def get_app_token(self):
        return self._get_option('main', 'token')

    def get_boardid(self):
        return self._get_option('main', 'boardid')

    def get_date_format(self):
        return self._get_option('main', 'date_format')

    def _get_option(self, section, option_name, cli_name=None):
        rv = None

        if self.has_option(section, option_name):
            rv = self.get(section, option_name)
   
        if cli_name is None:
            cli_name = option_name

        if self.cli_args.__contains__(cli_name):
            cli = self.cli_args.__getattribute__(cli_name)
            if cli is not None:
                rv = cli

        return rv
   

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
               name = rv.group(1)
               section_config['section_name'] = name
               for opt in self.config.options(section):
                   section_config[opt] = self.config.get(section, opt)

               return section_config

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
               name = rv.group(1)
               section_config['section_name'] = name
               for opt in self.config.options(section):
                   section_config[opt] = self.config.get(section, opt)

               return section_config

        raise StopIteration() 

