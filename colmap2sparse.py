import sys, os
import numpy as np
import cv2
import open3d as o3d
from tqdm import tqdm
from numpy import inf
import argparse

from cvt.geometry import render_point_cloud
from cvt.io import read_cams_sfm, read_point_cloud, write_pfm

parser = argparse.ArgumentParser(description='Script for converting colmap points into sparse depth maps.')
parser.add_argument('--points_file', type=str, help='Path to colmap points3d.txt file.', required=True)
parser.add_argument('--cam_path', type=str, help='Path to scene cameras.', required=True)
parser.add_argument('--image_path', type=str, help='Path to scene images.', required=True)
parser.add_argument('--images_file', type=str, help='Path to colmap images.txt file.', required=True)
parser.add_argument('--output_path', type=str, help='Sparse depth output path.', required=True)
parser.add_argument('--max_error', type=float, help='Maximum point error threshold.', required=True)
parser.add_argument('--min_track_len', type=int, help='Minimum required point track length.', required=True)

ARGS = parser.parse_args()


def load_points(points_file, max_error, min_track_len):
    points = {}
    tracks = {}
    points_per_id = {}
    with open(points_file, 'r') as pf:
        lines = pf.readlines()[3:]

        ind = 0
        for l in lines:
            l = l.strip().split()
            point = np.asarray(l[1:4]).astype(np.float32)
            error = float(l[7])
            track = np.asarray(l[8::2]).astype(np.int16)
            track_len = track.shape[0]
            
            if error <= max_error and track_len >= min_track_len:
                points[ind] = point
                tracks[ind] = track
                ind += 1

                for ind in track:
                    if ind in points_per_id.keys():
                        points_per_id[ind].append(point)
                    else:
                        points_per_id[ind] = [point]

    return points_per_id, points, tracks

def build_index(images_file):
    with open(images_file, 'r') as imf:
        lines = imf.readlines()
        num_images = lines[3]
        lines = lines[4::2]
        image_index = {}

        for line in lines:
            line = line.strip().split()
            database_id = int(line[0])
            image_id = int(line[-1][:-4])
            image_index[image_id] = database_id

    return num_images, image_index


def render_depth(pose, K, points, width, height):
    # create open3d point cloud
    cloud = o3d.geometry.PointCloud()
    cloud.points = o3d.utility.Vector3dVector(points)

    # set up the renderer
    render = o3d.visualization.rendering.OffscreenRenderer(width, height)
    mat = o3d.visualization.rendering.MaterialRecord()
    mat.shader = 'defaultUnlit'
    render.scene.add_geometry("cloud", cloud, mat)
    render.scene.set_background(np.asarray([0,0,0,1])) #r,g,b,a
    intrins = o3d.camera.PinholeCameraIntrinsic(width, height, K[0,0], K[1,1], K[0,2], K[1,2])
    render.setup_camera(intrins, pose)
    depth = np.asarray(render.render_to_depth_image(z_in_view_space=True))

    return depth

def main():
    # get image shape
    images = os.listdir(ARGS.image_path)
    images.sort()
    img = cv2.imread(os.path.join(ARGS.image_path,images[0]))
    h,w,_ = img.shape

    # read in data
    cams = read_cams_sfm(ARGS.cam_path)

    # read point cloud
    _, image_index = build_index(ARGS.images_file)
    points_per_id, _, _ = load_points(ARGS.points_file, ARGS.max_error, ARGS.min_track_len)

    for i,cam in enumerate(cams):
        pose = cam[0]
        K = cam[1]
        
        database_id = image_index[i]
        points = np.asarray(points_per_id[database_id]).astype(np.float64)
        depth = render_depth(pose, K, points, w, h)
        depth = np.nan_to_num(depth)
        depth[depth>=1e5] = 0.0
        write_pfm(os.path.join(ARGS.output_path,f"{i:08d}.pfm"), depth)

if __name__=="__main__":
    main()
