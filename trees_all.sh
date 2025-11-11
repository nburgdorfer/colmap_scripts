#!/bin/bash

SCENES=(Sequoia_1 Sequoia_2 Sequoia_3 Sequoia_4 Sequoia_5 Yosemite_1 Yosemite_2 Yosemite_3 Yosemite_4)
MAX_ERROR=(0.5 0.5 0.5 0.5 0.5 0.5 0.5 0.5 0.5)
MIN_TRACK_LEN=(3 3 3 3 3 3 3 3 3)

NUM_SCENES=${#SCENES[@]}

for (( i=0; i<NUM_SCENES; i++ ))
do
    SCENE=${SCENES[$i]}
    ERROR=${MAX_ERROR[$i]}
    TRACK_LEN=${MIN_TRACK_LEN[$i]}
    ./run.sh \
        "/mnt/Drive2/Trees" \
        "${SCENE}" \
        "/mnt/Drive2/Trees/${SCENE}/${SCENE}.MOV"
  echo "Element at index $i: ${my_array[$i]}"
done
