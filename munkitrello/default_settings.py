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
#
# Default Settings 
#

config_file_locations = [
    '/etc/munki-trello/munki-trello.cfg',
    'munki-trello.cfg'
]

date_format='%d/%m/%y'
repo_path='/Volumes/Munki'
makecatalogs='/usr/local/munki/makecatalogs'

#
#
#
DEFAULT_DEV_LIST='Development'
DEFAULT_TO_DEV_LIST='To Development'
DEFAULT_MUNKI_DEV_CATALOG='development'
#
DEFAULT_TEST_LIST='Testing'
DEFAULT_TO_TEST_LIST='To Testing'
DEFAULT_MUNKI_TEST_CATALOG='testing'
#
DEFAULT_PROD_LIST='Production'
DEFAULT_TO_PROD_LIST='To Production'
DEFAULT_MUNKI_PROD_CATALOG='production'

# command line options
# List; contains tuples: ('option', 'help', Default)
cli_options = [
    ("--config", "Name of configuration file; program will try to read '/etc/munki-trello/munki-trello.cfg' and './munki-trello.cfg' by default, appending this configuration file to the end of the list; configuration file values will be overridden by those on the command line and last match wins", None),

    ("--boardid", "Trello board ID.", None),
    ("--key", "Trello API key. See README for details on how to get one.", None),
    ("--token", "Trello application token. See README for details on how to get one.", None),
    ("--repo-path", "Path to your Munki repository. Defaults to '%s'. " % repo_path, repo_path),

    ("--makecatalogs", "Path to makecatalogs. Defaults to '%s'. " % makecatalogs, makecatalogs),
    ("--date-format", "Date format to use when creating dated lists. See strftime(1) for details of formatting options. Defaults to '%%d/%%m/%%y'. ", date_format),

# Dev Catalog/Trello

    ( "--to-dev-list", "Name of the 'To Development' Trello list if none in the configuration file. Defaults to '%s'. " % DEFAULT_DEV_LIST, DEFAULT_DEV_LIST),
    ( "--dev-list", "Name of the 'Development' Trello list. Defaults to '%s'. " % DEFAULT_DEV_LIST, DEFAULT_DEV_LIST),
    ("--dev-catalog", "Name of the Munki development catalog. Defaults to '%s'. " % DEFAULT_MUNKI_DEV_CATALOG, DEFAULT_DEV_LIST),
    ("--dev-stage-days", "The number of days that a package will remain in development before being prompoted to test (if staging is enabled).  Note: this does not enable staging", None),

# Test Catalog/Trello
    ("--to-test-list", "Name of the 'To Testing' Trello list. Defaults to '%s'. " % DEFAULT_TO_TEST_LIST, DEFAULT_TO_TEST_LIST),
    ("--test-list", "Name of the 'Testing' Trello list. Defaults to '%s'. " % DEFAULT_TEST_LIST, DEFAULT_TEST_LIST),
    ("--test-catalog", "Name of the Munki testing catalog. Defaults to '%s'. " % DEFAULT_MUNKI_TEST_CATALOG, DEFAULT_MUNKI_TEST_CATALOG),
    ("--test-stage-days", "The number of days a package will remain in testing before being prompoted to production (if staging is enabled). Note: this does not enable staging", None),
    ("--stage-test", "Automatically promote packages past their due date from development into testing.  Note: this does not enable setting of the due date", None),


# Prod 
    ("--prod-list", "Name of the 'Production' Trello list. Defaults to '%s'. Will only be used if the production suffix is set to the empty string" % DEFAULT_PROD_LIST, DEFAULT_PROD_LIST),

    ("--to-prod-list", "Name of the 'To Production' Trello list. Defaults to '%s'. " % DEFAULT_TO_PROD_LIST, DEFAULT_TO_PROD_LIST),
    ("--suffix", "Suffix that will be added to new 'In Production cards'. Defaults to '%s'. " % DEFAULT_PROD_LIST, DEFAULT_PROD_LIST),

    ("--prod-catalog", "Name of the Munki production catalog. Defaults to '%s'. " % DEFAULT_MUNKI_PROD_CATALOG,DEFAULT_MUNKI_PROD_CATALOG),
    ("--stage-prod", "Automatically promote packages past their due date from testing into production.  Note: this does not enable setting of the due date", None),

]

