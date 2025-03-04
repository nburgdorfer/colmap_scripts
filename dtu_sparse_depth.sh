#!/bin/bash

DATA_PATH=$1
SCENE=$2

# point threshold parameters
MAX_ERROR=1.0
MIN_TRACK_LEN=3

# create sparse model output paths
if [ ! -d "$DATA_PATH/colmap/${SCENE}/sparse/0/text" ]; then
  mkdir -p "$DATA_PATH/colmap/${SCENE}/sparse/0/text"
fi

# create database.db file
if [ -f "$DATA_PATH/colmap/${SCENE}/database.db" ]; then
    rm "$DATA_PATH/colmap/${SCENE}/database.db"
fi
touch "$DATA_PATH/colmap/${SCENE}/database.db"

# create cameras file encoding the calibrated intrinsics for our camera
python database.py \
    --cam_path ${DATA_PATH}/Cameras \
    --image_path ${DATA_PATH}/Images/${SCENE} \
    --database_file ${DATA_PATH}/colmap/${SCENE}/database.db \
    --output_path "${DATA_PATH}/colmap/${SCENE}/sparse/0/text"

colmap feature_extractor \
    --database_path ${DATA_PATH}/colmap/${SCENE}/database.db \
    --image_path ${DATA_PATH}/Images/${SCENE}

colmap exhaustive_matcher \
    --database_path ${DATA_PATH}/colmap/${SCENE}/database.db

colmap point_triangulator \
    --database_path ${DATA_PATH}/colmap/${SCENE}/database.db \
    --image_path ${DATA_PATH}/Images/${SCENE} \
    --input_path ${DATA_PATH}/colmap/${SCENE}/sparse/0/text \
    --output_path ${DATA_PATH}/colmap/${SCENE}/sparse/0

colmap point_filtering \
    --input_path "${DATA_PATH}/colmap/${SCENE}/sparse/0" \
    --output_path "${DATA_PATH}/colmap/${SCENE}/sparse/0" \
 	--min_track_len ${MIN_TRACK_LEN} \
  	--max_reproj_error ${MAX_ERROR}

colmap model_converter \
    --input_path "${DATA_PATH}/colmap/${SCENE}/sparse/0" \
    --output_path "${DATA_PATH}/colmap/${SCENE}/sparse/0/text" \
    --output_type TXT 
 
# create sparse depth maps from sparse model
if [ ! -d "${DATA_PATH}/Sparse_Depths/${SCENE}" ]; then
  mkdir -p "${DATA_PATH}/Sparse_Depths/${SCENE}"
fi

python colmap2sparse.py \
    --points_file "${DATA_PATH}/colmap/${SCENE}/sparse/0/text/points3D.txt" \
    --cam_path ${DATA_PATH}/Cameras \
    --image_path ${DATA_PATH}/Images/${SCENE} \
    --images_file "${DATA_PATH}/colmap/${SCENE}/sparse/0/text/images.txt" \
    --output_path ${DATA_PATH}/Sparse_Depths/${SCENE} \
    --max_error ${MAX_ERROR} \
    --min_track_len ${MIN_TRACK_LEN}

# convert colmap points to ply file
if [ ! -d "${DATA_PATH}/Sparse_Points" ]; then
  mkdir -p "${DATA_PATH}/Sparse_Points"
fi

python colmap2ply.py \
    --points_file "${DATA_PATH}/colmap/${SCENE}/sparse/0/text/points3D.txt" \
    --output_file ${DATA_PATH}/Sparse_Points/${SCENE}_sparse.ply \
    --max_error ${MAX_ERROR} \
    --min_track_len ${MIN_TRACK_LEN}
