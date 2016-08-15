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
# Represent an on-disk Munki Repository
#

import os
import plistlib
import subprocess

import sys

from . import Package, PackageList

class MunkiRepository:
  
    def __init__(self, repo_config, makecatalogs='/usr/local/munki/bin/makecatalogs'):

        self.name        = repo_config['repo_name']
        self.munki_path  = repo_config['repo_path']

        self.all_catalog_path = os.path.join(self.munki_path, 'catalogs/all') 
        self.pkgsinfo_path    = os.path.join(self.munki_path, 'pkgsinfo') 

        self.munki_makecatalogs  = makecatalogs
        self.run_makecatalogs = False

        self.package_list = None

    # Find all pkgsinfo files (and thus all packages)
    def packages(self):

        if self.package_list is not None:
            return self.package_list

        self.package_list = []
        for root, dirs, files in os.walk( self.pkgsinfo_path ) :
            for file in files:
                # Ingore invisible files
                if file.startswith('.'):
                  print 'Ignoring hidden file %s' % (file)
                  continue
                # It is conceivable there are broken / non plist files
                # so we try to parse the files, just in case
                pkgsinfo = os.path.join(root, file)
                try: 
                    plist = plistlib.readPlist(pkgsinfo)
                except Exception as e:
                   print 'Ignoring invalid pkgsinfo file %s' % (pkgsinfo)
                   print '(Error: %s)' % (e)
                   continue

                package = Package( plist['name'], plist['version'],
                                     pkgsinfo=pkgsinfo,
                                     munki_catalogs=plist['catalogs'],
                                     munki_repo=self)

                self.package_list.append(package)
                
        return self.package_list


    def update_munki_required(self, flag=False):
        # Can only switch this flag on; this may be a bug
        if flag:
            self.run_makecatalogs = flag

        return self.run_makecatalogs

    def run_update_catalogs(self):
        # Why work if you don't have to ;-)
        if self.run_makecatalogs == False:
            return
        
        makecat = subprocess.Popen([self.munki_makecatalogs, self.munki_path],
                                 stdout=subprocess.PIPE)
        lines_iterator = iter(makecat.stdout.readline, b"")
        for line in lines_iterator:
            print(line) # yield line

        return

    def update_pkgsinfo_catalog(self, pkgsinfo, catalog):
        
        plist = plistlib.readPlist(pkgsinfo)
        plist['catalogs'] = [catalog]
        plistlib.writePlist(plist, pkgsinfo)
  
        self.update_munki_required(True)
        
        return

    def read_pkgsinfo(self, pkgsinfo):
        return plistlib.readPlist(pkgsinfo)

    def get_icon(self, pkgsinfo):

       pkgsinfo = self.read_pkgsinfo(pkgsinfo)
       if pkgsinfo.has_key('icon_name'):
           icon_name = os.path.join('icons', pkgsinfo['icon_name'])
       else:
           icon_name = os.path.join('icons', pkgsinfo['name'] + '.png')

       icon_path = os.path.join(self.munki_path, icon_name)
       if os.path.isfile(icon_path):
           return icon_name
       if os.path.isfile(icon_path + '.png'):
           return icon_name
     
       return None 
