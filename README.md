#Munki-Staging update - 16-04-2024 

Please note we are no longer developing or maintaining this repo. Please consider alternatives to this script should you wish to utilise the munki staging process.

Thanks,

Orchard Team


# Introduction


This is a script that utilises a Trello board to manage the promotion of
Munki items through development to production and then, if desired to
archival.  You can use any number of steps between development and
production, but by default the script will expect 3 Munki Catalogs:

* development
* testing
* production

and this introduction will focus on this example. Taking these
catalogs as a basis, you would create 5 Trello boards:

* To Development: Items placed in this list will be moved to the development catalog when the script next runs.
* Development: Items in here are in the Development list. Do not place items directly in here, the script will manage the addition / removal of items to the list.
* To Testing: Items placed in this list will be moved to the testing catalog when the script next runs.
* Testing: Items here are in testing.
* To Production: Items here will be moved into production on the next run.

When items are moved into production, they are (by default) moved to a
dated list, so you can have a history of when items were placed into
production. One list will be made per day. However, you can turn off
this behaviour if you wish. This dated behaviour can also be enabled on
development and production.

![](https://github.com/ox-it/munki-staging/wiki/images/oxford-trello-board.png)

# Usage

## Setup

It is recommended that this script is run under a service Trello account rather than a real persons, so you can separate the changes made by the script from normal users. This user will need to have access to the Trello board you're using. You will need to know the board ID - the board ID is the part after ``/b`` and before the name of your board (with a URL or https://trello.com/b/AbCdEfGh/my-trello-board, __AbCdEfGh__ would be the board ID.)

You will need an [API key](https://trello.com/app-key). Make note of the key and then head over to [Trello's instructions](https://trello.com/docs/gettingstarted/#token) for creating a user token. Choose how long you want to issue to token for - using the value of 'never' will stop the token from expiring. The only required option is read and write access to the Trello account. The name can be anything you like, it's how you will identify the token in future.

```
https://trello.com/1/authorize?key=substitutewithyourapplicationkey&name=munki-trello&expiration=never&response_type=token&scope=read,write
```

You will be given a 64 character string that you will need to take note of.

You will also need to install the trello module:

```
$ sudo easy_install trello
```

## Running the script

You can run the script manually on a machine that has the Munki makecatalogs command installed (this will run on OS X or Linux, Windows isn't tested).
Note that unlike the upstream version, there is no Docker setup.

In order to get the maximum flexibility from the script, you will need
to use a configuration file; however most options for the development,
testing and production setup above are available on the command line.

Note that if you use a configuration file you will need to specify
a Munki repository section; this is because using the configuration file
allows more than one repository to be used, overriding the default
option from the command line.

### Example

```
$ python munki-staging.py --boardid 12345 --key myverylongkey --token myevenlongertoken --repo-path /Volumes/my-repo
```

### Command line Options

* ``--boardid``: Required. The ID of your Trello board.
* ``--key``: Required. Your Trello API key.
* ``--token``: Required. Your Trello User Token.
* ``--config``: Optional. A file to read configuration settings from. 
* ``--to-dev-list``: Optional. The name of your 'To Development' list. Defaults to ``To Development``.
* ``--dev-list``: Optional. The name of your 'Development' list. Defaults to ``Development``.
* ``--to-test-list``: Optional. The name of your 'To Testing' list. Defaults to ``To Testing``.
* ``--test-list``: Optional. The name of your 'Testing' list. Defaults to ``Testing``.
* ``--to-prod-list``: Optional. The name of your 'To Production' list. Defaults to ``To Production``.
* ``--prod-suffix`` or ``--suffix``: Optional. The suffix that will be put after the dated 'Production' lists. Defaults to ``Production``; if unset packages will be added to the production list.
* ``--prod-list``: Optional. The name of your 'Production' list. Defaults to ``Production``; only used when ``--prod-suffix`` is unset.
* ``--repo-path``: Optional. The path to your Munki repository. Defaults to ``/Volumes/Munki``.
* ``--makecatalogs``: Optional. The path to ``makecatalogs``. Defaults to ``/usr/local/munki/makecatalogs``.
* ``--date-format``: Optional. The date format to use when creating dated lists. See strftime(1) for details of the formating options.  Defaults to ``%d/%m/%y``.
* ``--dev-stage-days``: Optional. Set the due date for autostaging; as packages are added into development, this will set the card due date to the current time plus the about of time given. You will need to seperately turn on staging, which is independent of this option.  Default: 0 (no due date set).
* ``--stage-test``: Optional. Automatically promote packages with a due date set from the development list into the testing list. Note: there is a separate option to enable the setting of the due date.  Default: False (no auto promotion to test).
* ``--test-stage-dates``: Optional. Set the due date for autostaging; as packages are added into test, this will set the card due date to the current time plus the about of time given. You will need to separately turn on staging, which is independent of this option.  Default: 0 (no due date set).
* ``--stage-prod``: Optional. Automatically promote packages with a due date set from the testing list into the production list. Note: there is a separate option to enable the setting of the due date.  Default: False (no auto promotion to test).

## Configuration file

You can give all of the command line options in a configuration file,
which will be read first. The default configuration file
locations are:
    /etc/munki-staging/munki-staging.cfg
    ./munki-staging.cfg
and these will always be checked. You can also add an extra config
file location by using the --config command line option.

N.B. Configuration files will be processed *before* command line options,
and not all configuration items have a command line equivalent.

Configuration files will be read in the order:

 0. `/etc/munki-staging/munki-staging.cfg`
 0. `./munki-staging.cfg`
 0. the configuration file give on the command line

All configuration files that exist and are readable will be processed; if a
file is missing or unreadable it will not be processed and will not
cause an error. Configuration file sections found in multiple sections
will be folded together, with duplicated settings taking the latest
value found. Details of the processing are give in the section below.

Options on the command line will be used in preference to those in the
configuration file. An example configuration file is in
munki-staging.cfg-template.

The configuration file has several sections:
  * the `[main]` section with some global defaults
  * the optional `[rssfeeds]` section 
  * Munki repository sections (`[munki_repo_<name>]`)
  * Munki catalog sections (`[munki_catalog_<name>]`)
  * Auto staging schedule sections (`[schedule]` and/or `[schedule_<name>]`)

Note that if you use a configuration file you must provide at least
the sections:
  * main
  * a Munki repository
(any number of munki repositories can be used, but there must be at
least one given as using the configuration file removes the default
value for this setting)

#### The `[main]` section

The main section contains global configuration items; the data about
the Trello board, the path to makecatalogs and the date_format to be
used.

The full options are:

* ``boardid``: The ID of your Trello board.
* ``key``:  Your Trello API key.
* ``token``:  Your Trello User Token.
* ``makecatalogs``: the path to the munki makecatalogs script. Defaults to ``/usr/local/munki/makecatalogs``.
* ``date-format``: The date format to use when creating dated lists. See strftime(1) for details of the formatting options (note that the script assumes use of numeric options only).  Defaults to ``%d/%m/%y``.

Note that the script requires that `boardid`, `key` and `token are set
either in the configuration file or on the command line.

In the configuration file, these values should be the unquoted tokens
from trello; if there are quotes present at the start and end of these
three options they will be stripped. 

As an example, a minimal main configuration is below; N.B. the values
have been randomly generated, so are **NOT** valid for trello.

```
[main]
boardid=ua6oor0oL
key=cf3e10a51fd05ef4a1944c7ccd713aa6
token=6b8a8177589e02994c5183a881b6c91f6709f6dcc6711591c05eb3def190e04e
```

#### The `[rssfeeds]` section

If present, this section configures the output of RSSFeeds of packages
in each catalog, that you can publish so that people know which
version of a package is in a catalog, and when the software available
changes. 

In order to use RSSfeeds you will need to install:
```
$ sudo easy_install PyRSS2Gen
```
You will also need to configure the following; there are no defaults:

* ``rssdir``: the directory to publish the RSSFeeds to (one file per catalog, named after the catalog)
* ``rss_link_template``: the link in the RSSFeeds for the item; can use the following templates: `%(name)s`, `%(version)s`, `%(catalog)s`
* ``guid_link_template``: a unique link to this version of the package (this will be used by RSS Readers to track the package entry) ; can use the following templates: `%(name)s`, `%(version)s`, `%(catalog)s`
* ``catalog_link_template``: a link to information about the catalog; can use the following template: `%(catalog)s`
* ``description_template``: the description of the RSS Channel; can use the following template: `%(catalog)s`
* ``icon_url_template``: a link to the Munki icons;  can use the following template: `%(icon_path)s` - the on disk path to the Munki icon

As an example, a complete RSS Feed configuration is:

```
[rssfeeds]
rssdir=/srv/www/site.orchard.ox.ac.uk/htdocs/rssfeeds
rss_link_template=https://site.orchard.ox.ac.uk/packages/%(name)s
guid_link_template=https://site.orchard.ox.ac.uk/packages/%(name)s/%(version)s
catalog_link_template=https://site.orchard.ox.ac.uk/catalogs/%(catalog)s
description_template='Software packages in Orchard %(catalog)s catalog'
icon_url_template=https://site.orchard.ox.ac.uk/munki/%(icon_path)s
```

#### The Munki catalog sections `[munki_catalog_<name>]`

The Munki catalog sections contain information about different Munki
catalogs and their related Trello lists. This information includes any
configuration of autostaging, and the setting of due dates.

The name in the section title is not used, but it is suggested that
this follow the name of the Munki catalog, as this will aid
readability of the configuration file.

The full options are:

* ``list``: ''Required''. The name of the list in the trello board; when using dated lists this is also the suffix used after the date.
* ``to_list``: The name of the list in trello in which to put packages to be migrated into this catalog; defaults to 'To <list>'.
* ``catalog``: ''Required''. The name of the Munki catalog that this list is used for.
* ``stage_days``: Default: unset. The number of days that a package remains in this catalog before being autostaged/promoted to the stage_to catalog.  Note: autostaging must be enabled in order for package staging to occur.
* ``stage_to``: The name of the munki repository/config section to stage packages to (if auto staging).
* ``autostage``: Default: 0 (off). Whether or not to automatically promote packages based on the Trello card due date.
* ``munki_repo``: The name of the underlying Munki repository (if using more than one Munki repository.
* ``dated_lists``: Default: 0 (off). If new Trello lists are created when packages are moved into this catalog, based on the date the packages are moved.

Note that the ``stage_days`` parameter can be overridden in individual
``pkgsinfo`` files on a per-package basis; see the section on
autostaging for more details.

#### The Munki repository sections `[munki_catalog_<name>]`

These sections document the Munki repository or repositories that
packages live in. You will require at least one repository. However,
you can have as may repositories as you would like; an use case for
this is to have a 'main' repository and a 'retired' repository, and
migrate older versions of packages into the 'retired' repository,
which could be on slower storage.

There is one required parameter:

* ``repo_path``: The path to the Munki repository

#### Auto stating schedule sections (`[schedule]`) and/or `[schedule_<name>]`)

These sections allows you to control when autostaging happens.

__NOTE__ You need to install dateutil in order to use this; if you
do not install this python module, the schedule section will be
ignored.

Clearly, if you have not configured autostaging, then these sections will
have no effect.

If autostaging is configured, by default, staging will happen every
time the script is run, if packages meet the criteria to be staged.

If you add the optional section `[schedule]`, then autostaging will only
happen if the script is running in one of the periods defined.

If you add the optional section `[schedule_<name>]`, then autostaging 
for the catalog `<name> will only happen if the script is running in
one of the periods defined in this section.

Note: if you define both `[schedule]` and `[schedule_<name>]`, the
global section takes precedence: staging will only happen if you are
in a period defined in both the global section `[schedule]` *and* the 
catalog section `[schedule_<name>]`.

The optional parameters have the format:

* ``<Day of Week>=timeperiod[,timeperiod]+``

where <Day of the week> is the long name of the day of the week in the
current locale and time periods are start ``time-end time`` where each
time is specified by HH:MM. For example, to only stage on Monday to Thursday
between 09:00 and 17:00 you have the section:
```
[schedule]
Monday=09:00-17:00
Tuesday=09:00-17:00
Wednesday=09:00-17:00
Thursday=09:00-17:00
```
Note: specifying an empty section will turn off staging.

#### Configuration file processing

As we mentioned in the section introduction, munki-staging will
attempt to read the configuration files in the following order:
 0. `/etc/munki-staging/munki-staging.cfg`
 0. `./munki-staging.cfg`
 0. the configuration file give on the command line

Files not present, or not readable will be ignored and no error will
be given in these cases.  If a file is present and readable it will be
processed, with later configuration adding to (in the case of a
`[section]`) or replacing (in the case of a `setting=value`) earlier
ones. 

As an example of configuration file processing, imagine we have the
configuration file in `/etc/munki-staging/munki-staging.cfg` and no
other configuration files. The file
`/etc/munki-staging/munki-staging.cfg`
contains the line:
```
[example_section]
value_one=1
value_two=2
```
munki-staging would then run with the configuration:
```
    example_section.value_one   = 1
    example_section.value_two   = 1
```

If the two configuration files `/etc/munki-staging/munki-staging.cfg`
and `./munki-staging.cfg` were present and readable with
`/etc/munki-staging/munki-staging.cfg` as above and
`./munki-staging.cfg` containing:
```
[example_section]
value_three=3
value_four=4
```
munki-staging would then run with the configuration:
```
    example_section.value_one   = 1
    example_section.value_two   = 2
    example_section.value_three = 3
    example_section.value_four  = 4
```

Finally, if there was a configuration file on the command line, say
`--config extra.cfg`, with the two other files present as above and
`extra.cfg` containing:
```
[example_section]
value_one=100
```
munki-staging would then run with the configuration:
```
    example_section.value_one   = 100
    example_section.value_two   = 2
    example_section.value_three = 3
    example_section.value_four  = 4
```


## Autostaging

As described above, you can turn on autostaging on a
per-trello list basis. A package will auto stage if all of the
following are true:
  
  * If an autostaging period is defined, the script is run in this period
   * If no period is defined autostaging will always run
  * If the current package catalog has autostaging enabled
  * If the current package due date is in the past

Thus if you have 3 catalogs:

* development
* testing
* production

then in order to stage packages into production you need to turn on
auto staging for testing. In order to stage packages into testing, you
need to turn on autostaging for development.

### Staging Speed

If you use autostaging, you will need to set the number of days in
which a package get staged. This is set on the Munki catalog using the
``stage_days`` setting for all packages in a catalog. However, there
may be some packages that you wish to stage faster than the default
(e.g. a security release).

For this reason, there is a feature to allow you to change the staging
days on a per-package basis. To do this you will need to edit the
``pkgsinfo`` file for the package, adding a munki_staging key which
has a dictionary value. Within this dictionary you can set a
stage_days parameter which overrides the default number of days.

For example, to stage a package with 1 days worth of testing you would
add the following to the pkginfo file:
```
       <key>munki_staging</key>
       <dict>
               <key>stage_days</key>
               <string>1</string>
       </dict>

```
This would then override the setting for the catalog, if autostaging
is enabled.

In order to help with this, there is a python script that you can use
to set the number of staging days for a package; this script
``munkistaging-pkgsinfo.py`` in the ``bin`` directory can be run as
below to set the staging days or to remove this key from the plist
file. For example, to set the staging days to be 1 day (as in the above
pkgsinfo file) you would run:
```
$ python bin/munkistaging-pkgsinfo.py --stagedays 1 /path/to/pkgsinfo/file
```
To remove this (note that setting stagedays to 0 means that the
package will staged at the next run), you would run:
```
$ python bin/munkistaging-pkgsinfo.py --removestagedays /path/to/pkgsinfo/file
```
The full usage is:
```
$ munkistaging-pkgsinfo.py [--stagedays <n>] [--removestagedays] <pkgsinfo_file>+
```
where 
* ``--stagedays``:  optional; the number of days to stage 
* ``--removestagedays``:  optional; removes the key (if present) from
the pkgsinfo file
* ``<pkgsinfo_file>``: is a path to a pkgsinfo file

If run without an argument will report on the number of staging days
that are configured within each of the pkgsinfo files listed.

*NB* The munki staging configuration file is *not* read by this helper
file.

# Troubleshooting

> I'm seeing items that won't move to the next stage no matter how often I move them.

Make sure the combination of ``name`` and ``version`` is unique. For speed, the initial ingest of Munki data is done via your ``all`` catalog rather than traversing your pkgsinfo files. If you have two pkgsinfo files that have the same version / name combination as anther, this script won't touch anything after the first. Once the duplicate(s) have been removed, the item will be promoted to the next stage.

# Copyright 

Copyright (c) 2015 University of Oxford

This is based on an original script by Graham Gilbert
<graham@grahamgilbert.com> with significant rewriting by the Unix
Services Team within IT Services, University of Oxford.


