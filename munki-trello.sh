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

DEVLIST='Unstable'
TESTLIST='Testing'
PRODLIST='Stable'

DEVCAT='unstable'
TESTCAT='testing'
PRODCAT='stable'

python ${MTRELLO} --boardid ${BOARDID}  --key ${KEY} --token=${TOKEN} \
    --dev-cat="${DEVCAT}"  \
    --dev-list="${DEVLIST}"  \
    --to-dev-list="To ${DEVLIST}" \
    --test-cat="${TESTCAT}"  \
    --test-list="${TESTLIST}"  \
    --to-test-list="To ${TESTLIST}" \
    --prod-cat="${PRODCAT}"  \
    --to-prod-list="To ${PRODLIST}" \
    --repo-path=${MUNKI_REPO} \
