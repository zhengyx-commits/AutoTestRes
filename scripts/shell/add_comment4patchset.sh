#!/bin/bash
BIN_PATH=$1
MSG=$(cat $2)
CHANGEID_PATCHSET=$3

for commit in $CHANGEID_PATCHSET
do
    echo "Add comment for $commit"
    ${BIN_PATH}/gerrit_rest_api -i $commit -m post_review_message -M "${MSG}"
done