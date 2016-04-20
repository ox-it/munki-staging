#!/usr/bin/python
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

import plistlib
import argparse
import os
import sys

options = argparse.ArgumentParser(description='Configure the optional munki_staging section in a pkgsinfo file')

options.add_argument('--stagedays', help='number of days to stage a package by', default=None, type=int)

options.add_argument('--removestagedays', help='remove the override of the number of days to stage a package by', action='store_true' )

options.add_argument('pkgsinfo', help='pkgsinfo files to operate on',
 nargs='+')

args = options.parse_args()


stagedays = -1
if args.__contains__('stagedays') and args.stagedays is not None:
    stagedays = args.stagedays
    if stagedays < 0:
        print "Can only set stagedays to be a positive integer"
        sys.exit(1)

if args.removestagedays == True:
    if stagedays >= 0:
        print "Cannot both set (stagedays >=0) and remove stagedays"
        sys.exit(1)

for pkgsinfo_file in args.pkgsinfo:
    if not os.path.exists(pkgsinfo_file):
        print "Skippking pkgsinfo file: %s (not found)" % pkgsinfo_file
        continue
    
    try:
        pkgsinfo = plistlib.readPlist(pkgsinfo_file)
    except Exception as e:
        print 'Unable to load file %s: %s' % (pkgsinfo_file, e)
        continue
    
    munkistaging = {}
    if pkgsinfo.has_key('munki_staging'):
        munkistaging = pkgsinfo['munki_staging']

    days = '(unset)'
    if munkistaging.has_key('stage_days'):
        days = munkistaging['stage_days']
        if args.removestagedays == True:
            del munkistaging['stage_days']
            if len(munkistaging) == 0 and pkgsinfo.has_key('munki_staging'):
               del pkgsinfo['munki_staging'] 
            else:
                pkgsinfo['munki_staging'] = munkistaging
            plistlib.writePlist(pkgsinfo,pkgsinfo_file)
            print 'Removing staging days from %s (was: %d)' % (pkgsinfo_file, days)
            continue

    if stagedays >=0:
        munkistaging['stage_days'] = stagedays
        pkgsinfo['munki_staging'] = munkistaging
        plistlib.writePlist(pkgsinfo,pkgsinfo_file)
        print 'Changing %s staging days from %s to %d' % (pkgsinfo_file, days, stagedays)
        continue


    print '%s has staging days %s' % (pkgsinfo_file, days)

