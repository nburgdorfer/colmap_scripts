#!/bin/bash

DATA_PATH=$1
SCENE=$2

# point threshold parameters
MAX_ERROR=2.0
MIN_TRACK_LEN=3

# create sparse model output paths
if [ ! -d "$DATA_PATH/${SCENE}/colmap/sparse/0/text" ]; then
  mkdir -p "$DATA_PATH/${SCENE}/colmap/sparse/0/text"
fi

# create database.db file
if [ -f "$DATA_PATH/${SCENE}/colmap/database.db" ]; then
    rm "$DATA_PATH/${SCENE}/colmap/database.db"
fi
touch "$DATA_PATH/${SCENE}/colmap/database.db"

# create cameras file encoding the calibrated intrinsics for our camera
python database.py \
    --cam_path ${DATA_PATH}/${SCENE}/Cameras \
    --image_path ${DATA_PATH}/${SCENE}/Images \
    --database_file ${DATA_PATH}/${SCENE}/colmap/database.db \
    --output_path "${DATA_PATH}/${SCENE}/colmap/sparse/0/text"

colmap feature_extractor \
    --database_path ${DATA_PATH}/${SCENE}/colmap/database.db \
    --image_path ${DATA_PATH}/${SCENE}/Images

colmap exhaustive_matcher \
    --database_path ${DATA_PATH}/${SCENE}/colmap/database.db

colmap mapper \
    --database_path ${DATA_PATH}/${SCENE}/colmap/database.db \
    --image_path ${DATA_PATH}/${SCENE}/Images \
    --output_path ${DATA_PATH}/${SCENE}/colmap/sparse

colmap point_filtering \
    --input_path "${DATA_PATH}/${SCENE}/colmap/sparse/0" \
    --output_path "${DATA_PATH}/${SCENE}/colmap/sparse/0" \
 	--min_track_len ${MIN_TRACK_LEN} \
  	--max_reproj_error ${MAX_ERROR}

colmap model_converter \
    --input_path "${DATA_PATH}/${SCENE}/colmap/sparse/0" \
    --output_path "${DATA_PATH}/${SCENE}/colmap/sparse/0/text" \
    --output_type TXT 
 
# create sparse depth maps from sparse model
if [ ! -d "${DATA_PATH}/${SCENE}/Sparse_Depths" ]; then
  mkdir -p "${DATA_PATH}/${SCENE}/Sparse_Depths"
fi
python colmap2sparse.py \
    --points_file "${DATA_PATH}/${SCENE}/colmap/sparse/0/text/points3D.txt" \
    --cam_path ${DATA_PATH}/${SCENE}/Cameras \
    --image_path ${DATA_PATH}/${SCENE}/Images \
    --images_file "${DATA_PATH}/${SCENE}/colmap/sparse/0/text/images.txt" \
    --output_path ${DATA_PATH}/${SCENE}/Sparse_Depths \
    --max_error ${MAX_ERROR} \
    --min_track_len ${MIN_TRACK_LEN}

python colmap2ply.py \
    --points_file "${DATA_PATH}/${SCENE}/colmap/sparse/0/text/points3D.txt" \
    --output_file ${DATA_PATH}/${SCENE}/${SCENE}_sparse.ply \
    --max_error ${MAX_ERROR} \
    --min_track_len ${MIN_TRACK_LEN}
