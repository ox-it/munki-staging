#
# Represent an on-disk Munki Repository
#

import os
import plistlib
import subprocess

import sys

from . import Package, PackageList

class MunkiRepository:
  
    def __init__(self, munki_path, makecatalogs='/usr/local/munki/bin/makecatalogs'):
        print "P:", munki_path
        self.munki_path  = munki_path

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
                # It is conceivable there are broken / non plist files
                # so we try to parse the files, just in case
                pkgsinfo = os.path.join(root, file)
                try: 
                    plist = plistlib.readPlist(pkgsinfo)
                except:
                   continue
  
                package = Package( plist['name'], plist['version'],
                                   pkgsinfo=pkgsinfo,
                                   munki_catalogs=plist['catalogs'],
                                   munki_repo=self)
                print "found %s %s" % ( plist['name'], plist['version'])

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
