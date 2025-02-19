#!/bin/bash

DATA_PATH=$1
SCENE=$2

# create sparse model output paths
if [ ! -d "$DATA_PATH/colmap/${SCENE}/dense" ]; then
  mkdir -p "$DATA_PATH/colmap/${SCENE}/dense"
fi

colmap image_undistorter \
    --image_path ${DATA_PATH}/Images/${SCENE} \
    --input_path "${DATA_PATH}/colmap/${SCENE}/sparse/0" \
    --output_path ${DATA_PATH}/colmap/${SCENE}/dense \
	--output_type COLMAP \
    --max_image_size 2000

colmap patch_match_stereo \
    --workspace_path ${DATA_PATH}/colmap/${SCENE}/dense \
    --workspace_format COLMAP \
    --PatchMatchStereo.geom_consistency true

if [ ! -d "${DATA_PATH}/Dense_Points" ]; then
  mkdir -p "${DATA_PATH}/Dense_Points"
fi

colmap stereo_fusion \
    --workspace_path ${DATA_PATH}/colmap/${SCENE}/dense \
    --workspace_format COLMAP \
    --input_type geometric \
    --output_path ${DATA_PATH}/Dense_Points/${SCENE}.ply
