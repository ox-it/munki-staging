# Introduction

This is a script that utilises a Trello board to manage the promotion of Munki items through development to testing to production catalogs.  You should make five lists on your Trello board:

* To Development: Items placed in this list will be moved to the development catalog when the script next runs.
* Development: Items in here are in the Development list. Do not place items directly in here, the script will manage the addition / removal of items to the list.
* To Testing: Items placed in this list will be moved to the testing catalog when the script next runs.
* Testing: Items here are in testing.
* To Production: Items here will be moved into production on the next run.

When items are moved into production, they are moved to a dated list, so you have a history of when items were placed into production. One list will be made per day.

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

You have two options - you can run the script manually on a machine with the Munki Tools installed (this will run on OS X or Linux, Windows isn't tested), or you can use the [Docker container](https://github.com/grahamgilbert/docker-munki-trello). For more details about the Docker container, see it's [own repository](https://github.com/grahamgilbert/docker-munki-trello) and it's entry on the [Docker Hub](https://registry.hub.docker.com/u/grahamgilbert/munki-trello/).

### Example

```
$ python munki-trello.py --boardid 12345 --key myverylongkey --token myevenlongertoken --repo-path /Volumes/my-repo
```

### Options

* ``--boardid``: Required. The ID of your Trello board.
* ``--key``: Required. Your Trello API key.
* ``--token``: Required. Your Trello User Token.
* ``--config``: Optional. A file to read configuation settings from. 
* ``--to-dev-list``: Optional. The name of your 'To Development' list. Defaults to ``To Development``.
* ``--dev-list``: Optional. The name of your 'Development' list. Defaults to ``Development``.
* ``--to-test-list``: Optional. The name of your 'To Testing' list. Defaults to ``To Testing``.
* ``--test-list``: Optional. The name of your 'Testing' list. Defaults to ``Testing``.
* ``--to-prod-list``: Optional. The name of your 'To Production' list. Defaults to ``To Production``.
* ``--suffix``: The suffix that will be put after the dated 'Production' lists. Defaults to ``Production``.
* ``--repo-path``: The path to your Munki repository. Defaults to ``/Volumes/Munki``.
* ``--makecatalogs``: The path to ``makecatalogs``. Defaults to ``/usr/local/munki/makecatalogs``.

## Configuration file

You can give all of the comamand line options in a configuration file,
which will be read first. The default configuration file
locations are:
    /etc/munki-trello/munki-trello.cfg
    ./munki-trello.cfg
and these will always be checked. You can also add an extra config
file location by using the --config command line option.

N.B. Configuration files will be processed *before* command line options.

Options on the command line will be used in preference to those in the
configuration file. An example configuration file is in
munki-trello.cfg-template.

# Troubleshooting

> I'm seeing items that won't move to the next stage no matter how often I move them.

Make sure the combination of ``name`` and ``version`` is unique. For speed, the initial ingest of Munki data is done via your ``all`` catalog rather than traversing your pkgsinfo files. If you have two pkgsinfo files that have the same version / name combination as anther, this script won't touch anything after the first. Once the duplicate(s) have been removed, the item will be promoted to the next stage.
