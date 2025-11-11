#!/bin/bash

SCENES=(Sequoia_1 Sequoia_2 Sequoia_4 Sequoia_5 Yosemite_1 Yosemite_2 Yosemite_3 Yosemite_4)
MAX_ERROR=(1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0)
MIN_TRACK_LEN=(2 2 2 2 2 2 2 2)

NUM_SCENES=${#SCENES[@]}

for (( i=0; i<NUM_SCENES; i++ ))
do
    SCENE=${SCENES[$i]}
    ERROR=${MAX_ERROR[$i]}
    TRACK_LEN=${MIN_TRACK_LEN[$i]}
    ./run.sh \
        "/mnt/Drive2/Trees" \
        "${SCENE}" \
        "/mnt/Drive2/Trees/${SCENE}/${SCENE}.MOV" \
        $ERROR \
        $TRACK_LEN
done
