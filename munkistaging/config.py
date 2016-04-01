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

import re

from ConfigParser import RawConfigParser, _default_dict

from . import default_settings

import argparse

from datetime import datetime

have_dateutil=0
try:
    from dateutil import parser
    have_dateutil=1
except ImportError:
    pass

def _list_cmp(a,b):
    if a[0] < b[0]:
        return -1

    if a[0] > b[0]:
        return 1

    if a[0] == b[0]: # We could be more precise here,
                     # and sort on [1], but it is not necessary
       return 0 

class MunkiSchedule:

    # We assume that schedule_list is the result of
    # RawConfigParser.items(section) i.e. a list of key,value tuples

    def __init__(self, schedule_list):
       
        self.periods = {}

        for day,periods in schedule_list:

            # NOTE: Monday == 0, Sunday == 6
            # (according to parser)
            dow=parser.parse('%s' % day).weekday()
            allowed = []
            for period in periods.split(','):
                start,end = period.split('-')

                s=parser.parse('%s' % start)
                e=parser.parse('%s' % end)

                period_start = s.hour * 3600 + s.minute * 60
                period_end   = e.hour * 3600 + e.minute * 60
                if period_end < period_start:
                    raise ValueError('End of period must be later than start of period - are you using the 24 hour clock ?  (start: %s, end %s)' % (period_start, period_end) )
                if period_end == period_start:
                    raise ValueError('End of period must be different to start of period (start: %s, end %s)' % (period_start , period_end) )
         
                allowed.append( [ period_start, period_end ] )

            self.periods[ dow ] = allowed

    def stage_now(self, now=None, debug=False):
        if now is None:
            now = datetime.now()
        dow = now.weekday()

        if self.periods.has_key(dow):
            now_int = now.hour * 3600 + now.minute * 60 + now.second
            for period in self.periods[dow]:
                if debug:
                   print '%s %s %s %s' % (period[0], now_int, period[1], now)
                if period[0] <= now_int and now_int <= period[1]:
                    return True
                if now_int < period[0]: # stop working when we can
                   break 

        return False
        
class MunkiStagingConfig(RawConfigParser):

    # Note: set allow_no_value=True here as the default
    # (which is what we want, but not he RawConfigParser default)
    def __init__(self, defaults=None, dict_type=_default_dict,
                 allow_no_value=True):

        RawConfigParser.__init__(self,defaults, dict_type, allow_no_value)
        self.read_config_files = -1
        self.repositories = {}

    def configured_munki_repositories(self):

        # If we have read a config file, then use it and 
        # don't allow any other overrides in for the catalogs
        if self.read_config_files >= 1:
            return MunkiStagingRepositories(self)

        # Otherwise, we only have a single catalog:
        repo_path = self._get_option('main', 'repo_path',
                          default_value=default_settings.repo_path)

        return { 'repo_name': 'production', 'repo_path': repo_path }

    def add_munki_repo(self, repo):
        self.repositories[repo.name] = repo

    def munki_catalogs(self):
        # If we have read a config file, then use it and 
        # don't allow any other overrides in for the catalogs
        if self.read_config_files >= 1:
            return MunkiStagingConfigCatalogs(self)
   
        print "No configuration file"
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

    def get_makecatalogs(self):
        makecatalogs = self._get_option('main', 'makecatalogs',
                                default_value=default_settings.makecatalogs)

        return makecatalogs

    def cli_parse(self):

        self.opts = argparse.ArgumentParser(description='Stage packages in Munki based on a trello board')

        for tuple in default_settings.cli_options:
            arg = tuple[0]
            help = tuple[1]
            defvalue = tuple[2]
            self.opts.add_argument(arg, help=help, default=defvalue)

        self.cli_args = self.opts.parse_args()

    def read_config(self, configfiles=None):
       cfgfiles = default_settings.config_file_locations
       if self.cli_args.config:  
           cfgfiles.append(self.cli_args.config)

       # This allows us to override the config file settings for
       # things like testing; it should not normally be used
       if configfiles is not None:
           self.read_config_files = self.read(configfiles)
           return
 
       self.read_config_files = self.read(cfgfiles)

    # Strips quotes form the begining and end of option values
    # mainly to ensure that these are not present on the key, token
    # and boardids
    def _get_unquoted_option(self, section, key):
        value = self._get_option(section, key)
        value = re.sub('^(\'|")', '', value)
        value = re.sub('(\'|")$', '', value)
        return value

    def get_app_key(self):
        return self._get_unquoted_option('main', 'key')

    def get_app_token(self):
        return self._get_unquoted_option('main', 'token')

    def get_boardid(self):
        return self._get_unquoted_option('main', 'boardid')

    def get_date_format(self):
        return self._get_option('main', 'date_format')

    def _get_option(self, section, option_name,
                       cli_name=None, default_value=None):

        rv = default_value

        if self.has_option(section, option_name):
            rv = self.get(section, option_name)
   
        if cli_name is None:
            cli_name = option_name

        # Only look at cmd line if no config file
        if self.read_config_files <= 0 and self.cli_args.__contains__(cli_name):
            cli = self.cli_args.__getattribute__(cli_name)
            if cli is not None:
                rv = cli

        return rv
   
    def get_rssdirectory(self):
       return self._get_option('rssfeeds', 'rssdir')

    def get_rss_link_template(self):
       return self._get_option('rssfeeds', 'rss_link_template')

    def get_rss_icon_url_template(self):
       return self._get_option('rssfeeds', 'icon_url_template')

    def get_catalog_link_template(self):
       return self._get_option('rssfeeds', 'catalog_link_template')

    def get_guid_link_template(self):
       return self._get_option('rssfeeds', 'guid_link_template')

    def get_description_template(self):
       return self._get_option('rssfeeds', 'get_description_template',
           default_value = 'Software packages in %s catalog')

    def autostage_schedule(self, catalog=None):
        if have_dateutil == 0:
            print 'python module dateutil is not installed'
            print 'it is not possible to control scheduling'
            return None

        if catalog is None:
            if self.has_section('schedule'):
                return MunkiSchedule( self.items('schedule')  )
        elif self.has_section('schedule_%s' % catalog ):
            return MunkiSchedule( self.items('schedule_%s' % catalog ) )

        return None

class MunkiStagingConfigCatalogs:

    catalog_re = re.compile('munki_catalog_(\w+)')

    def __init__(self, munki_staging_config):
        self.config = munki_staging_config
        self.sections = munki_staging_config.sections()
    
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

# Um ... this is basically the same as the above; do we need it ?
class MunkiStagingRepositories:

    mrepo_re = re.compile('munki_repo_(\w+)')

    def __init__(self, munki_staging_config):
        self.config = munki_staging_config
        self.sections = munki_staging_config.sections()
    
    def __iter__(self):
        return self
   
    def next(self):
        while len(self.sections) > 0:
            section = self.sections.pop()
            rv = self.mrepo_re.match(section)
            if rv:
               repo_config = {}
               name = rv.group(1)
               repo_config['repo_name'] = name
               for opt in self.config.options(section):
                   repo_config[opt] = self.config.get(section, opt)

               return repo_config

        raise StopIteration() 

