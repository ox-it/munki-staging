#
# Represent the on-disk Munki catalogs
#
# A representation of the on-disk Munki catalogs, as given by
# the 'all' catalog.
#

import os
import plistlib
import subprocess

import sys

class MunkiCatalog:
  
    def __init__(self, munki_path, makecatalogs='/usr/local/munki/bin/makecatalogs'):
        self.munki_path  = munki_path

        self.all_catalog_path = os.path.join(self.munki_path, 'catalogs/all') 
        self.pkgsinfo_path    = os.path.join(self.munki_path, 'pkgsinfo') 

        self.munki_makecatalogs  = makecatalogs
        self.run_makecatalogs = False

        self.read_all_catalog()
        self.find_pkgsinfo()
    
    def name_version(self, name, version):
        return '%s %s' % (name, version)

    def read_all_catalog(self):
        all_catalog = plistlib.readPlist( self.all_catalog_path)

        self.packages = {}
        self.catalogs = {}
        for item in all_catalog:
            name_version = self.name_version(item['name'], item['version'])
            self.packages[name_version] = {}
            self.packages[name_version]['name']     = item['name']
            self.packages[name_version]['version']  = item['version']
            self.packages[name_version]['catalogs']  = item['catalogs']
            for catalog in item['catalogs']:
                if self.catalogs.has_key(catalog):
                    self.catalogs[catalog].append(name_version)
                self.catalogs[catalog] = [name_version]
            self.packages[name_version]['pkgsinfo'] = None

    def find_pkgsinfo(self):

        for root, dirs, files in os.walk( self.pkgsinfo_path ) :
            for file in files:
                # It is conceivable there are broken / non plist files
                # so we try to parse the files, just in case
                pkgsinfo = os.path.join(root, file)
                try: 
                    plist = plistlib.readPlist(pkgsinfo)
                except:
                   continue
  
                key = '%s %s' % (plist['name'], plist['version'] )
                if self.packages.has_key(key):
                    self.packages[key]['pkgsinfo'] = pkgsinfo

    def update_package_catalog(self, name, version, catalog):

        package_key = '%s %s' % (plist['name'], plist['version'] )
        if not self.packages.has_key(package_key):
            return False

        plist = plistlib.readPlist( self.packages[package_key]['pkgsinfo'] )
        plist['catalogs'] = [catalog] 

        plistlib.writePlist(plist, self.packages[package_key]['pkgsinfo'] )
 
        self.update_munki_required(True)

        return True

    def has_pacakge(self, name, version):
        name_version = self.name_version(name, version)
        return self.packages.has_key(name_version)

    def catalog_has_pacakge(self, catalog, name, version):
        if not self.catalogs.has_key(catalog):
            return False

        name_version = self.name_version(name, version)
        if self.catalogs[catalog].count(name_version) > 0:
            return True

        return False

    def package_names(self):
        return self.packages.keys()

    def get_package(self, package_key):
        return self.packages[package_key]

    def get_package_name(self, package_key):
        return self.packages[package_key]['name']

    def get_package_version(self, package_key):
        return self.packages[package_key]['version']

    def get_package_pkgsinfo(self, package_key):
        return self.packages[package_key]['pkgsinfo']

    def get_package_catalogs(self, package_key):
        return self.packages[package_key]['catalogs']

    def update_munki_required(self, flag=False):
        # Can only switch this flag on; this may be a bug
        if flag:
            self.run_makecatalogs = flag

        return self.run_makecatalogs

    def run_update_catalogs(self):
        # Why work if you don't have to ;-)
        if self.run_makecatalogs == False:
            return
        
        makecat = subprocess.Popen(self.munki_makecatalogs,
                                 stdout=subprocess.PIPE)
        lines_iterator = iter(makecat.stdout.readline, b"")
        for line in lines_iterator:
            print(line) # yield line

        return
