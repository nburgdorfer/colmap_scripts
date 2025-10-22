#!/bin/bash

SCENES=(Sequoia_1 Sequoia_2 Sequoia_3 Sequoia_4 Yosemite_1 Yosemite_2 Yosemite_3 Yosemite_4)
for SCENE in ${SCENES[@]}
do
    ./run.sh \
        "/mnt/Drive2/Trees" \
        "${SCENE}" \
        "/mnt/Drive2/Trees/${SCENE}/${SCENE}.MOV"
done
