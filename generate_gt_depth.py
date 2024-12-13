import sys, os
import numpy as np
import cv2
import open3d as o3d
import argparse

from utils import read_cams_sfm, write_pfm

parser = argparse.ArgumentParser(description='Script for generating dense ground-truth depth maps from a mesh.')
parser.add_argument('--cam_path', type=str, help='Path to scene cameras.', required=True)
parser.add_argument('--image_path', type=str, help='Path to scene images.', required=True)
parser.add_argument('--mesh_path', type=str, help='Path to scene gt mesh.', required=True)
parser.add_argument('--output_path', type=str, help='Dense GT Depth output path.', required=True)
ARGS = parser.parse_args()

def main():
    # create output directory
    os.makedirs(ARGS.output_path, exist_ok=True)

    # get image shape
    images = os.listdir(ARGS.image_path)
    images.sort()
    img = cv2.imread(os.path.join(ARGS.image_path,images[0]))
    h,w,_ = img.shape

    # read in data
    cams = read_cams_sfm(ARGS.cam_path)

    # read triangle mesh
    mesh = o3d.io.read_triangle_mesh(ARGS.mesh_path)

    # set up the renderer
    render = o3d.visualization.rendering.OffscreenRenderer(w, h)
    mat = o3d.visualization.rendering.MaterialRecord()
    mat.shader = 'defaultUnlit'
    render.scene.add_geometry("mesh", mesh, mat)
    render.scene.set_background(np.asarray([0,0,0,1])) #r,g,b,a

    for i,cam in enumerate(cams):
        pose = cam[0]
        K = cam[1]
        intrins = o3d.camera.PinholeCameraIntrinsic(w, h, K[0,0], K[1,1], K[0,2], K[1,2])

        render.setup_camera(intrins, pose)
        depth = np.asarray(render.render_to_depth_image(z_in_view_space=True))
        depth = np.nan_to_num(depth)
        depth[depth>=1e5] = 0.0

        # pfm version
        write_pfm(os.path.join(ARGS.output_path,f"{i:08d}.pfm"), depth)

        # display version
        nz_depth = depth[np.nonzero(depth > 0)]
        disp_depth = 255 * (depth-nz_depth.min()) / (nz_depth.max()-nz_depth.min()+1e-15)
        os.makedirs(os.path.join(ARGS.output_path,"disp"), exist_ok=True)
        cv2.imwrite(os.path.join(ARGS.output_path,"disp",f"{i:08d}.png"), disp_depth)
        

if __name__=="__main__":
    main()
