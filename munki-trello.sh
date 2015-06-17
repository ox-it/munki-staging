#!/bin/bash
#
# A wrapper around munki-trello.py to save having to type all the options
# 

set -x

SECRETS_FILE=/srv/autopkg/munki-trello/munki-trello/secrets.txt
BOARDID=$(awk '/Trello Staging Board ID:/ {print $NF}' ${SECRETS_FILE})
KEY=$(awk '/Trello API Key/ {print $NF}' ${SECRETS_FILE})
TOKEN=$(awk '/Trello User Token/ {print $NF}' ${SECRETS_FILE})

MUNKI_REPO='/srv/munki/test_repo_aaron'

MTRELLO=/srv/autopkg/munki-trello/munki-trello/munki-trello.py

# Because I don't like unpackaged installs 
export PYTHONPATH=/srv/autopkg/munki-trello

python ${MTRELLO} --boardid ${BOARDID} --key ${KEY} --token=${TOKEN} \
    --repo-path=${MUNKI_REPO} \
