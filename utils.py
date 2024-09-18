import cv2, sys
import os
import numpy as np
import open3d as o3d

def render_point_cloud(render, intrins, pose):
    """Renders a point cloud into a 2D image plane.

    Parameters:

    Returns:
    """
    render.setup_camera(intrins, pose)

    # render image
    image = np.asarray(render.render_to_image())
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    depth = np.asarray(render.render_to_depth_image(z_in_view_space=True))

    return image, depth

def read_cams_sfm(camera_path: str, extension: str = "cam.txt") -> np.ndarray:
    """Reads an entire directory of camera files in SFM format.

    Parameters:
        camera_path: Path to the directory of camera files.
        extension: File extension being used for the camera files.

    Returns:
        Array of camera extrinsics, intrinsics, and view metadata (Nx2x4x4).
    """
    cam_files = os.listdir(camera_path)
    cam_files.sort()

    cams = []

    for cf in cam_files:
        if (cf[-7:] != extension):
            continue

        cam_path = os.path.join(camera_path,cf)
        #with open(cam_path,'r') as f:
        cam = read_single_cam_sfm(cam_path, 256)
        cams.append(cam)

    return np.asarray(cams)

def read_single_cam_sfm(cam_file: str, depth_planes: int = 256) -> np.ndarray:
    """Reads a single camera file in SFM format.

    Parameters:
        cam_file: Input camera file to be read.
        depth_planes: Number of depth planes to store in the view metadata.

    Returns:
        Camera extrinsics, intrinsics, and view metadata (2x4x4).
    """
    cam = np.zeros((2, 4, 4))

    with open(cam_file, 'r') as cam_file:
        words = cam_file.read().split()

    words_len = len(words)

    # read extrinsic
    for i in range(0, 4):
        for j in range(0, 4):
            extrinsic_index = 4 * i + j + 1
            cam[0,i,j] = float(words[extrinsic_index])

    # read intrinsic
    for i in range(0, 3):
        for j in range(0, 3):
            intrinsic_index = 3 * i + j + 18
            cam[1,i,j] = float(words[intrinsic_index])

    if words_len == 29:
        cam[1,3,0] = float(words[27])
        cam[1,3,1] = float(words[28])
        cam[1,3,2] = depth_planes
        cam[1,3,3] = cam[1][3][0] + (cam[1][3][1] * cam[1][3][2])
    elif words_len == 30:
        cam[1,3,0] = float(words[27])
        cam[1,3,1] = float(words[28])
        cam[1,3,2] = float(words[29])
        cam[1,3,3] = cam[1][3][0] + (cam[1][3][1] * cam[1][3][2])
    elif words_len == 31:
        cam[1,3,0] = words[27]
        cam[1,3,1] = float(words[28])
        cam[1,3,2] = float(words[29])
        cam[1,3,3] = float(words[30])
    else:
        cam[1,3,0] = 0
        cam[1,3,1] = 0
        cam[1,3,2] = 0
        cam[1,3,3] = 1

    return cam

def read_point_cloud(point_cloud_file: str) -> o3d.geometry.PointCloud:
    """Reads a point cloud from a file.

    Parameters:
        point_cloud_file: Input point cloud file.

    Returns:
        The point cloud stored in the given file.
    """
    return o3d.io.read_point_cloud(point_cloud_file)

def write_pfm(pfm_file: str, data_map: np.ndarray, scale: float = 1.0) -> None:
    """Writes a data map to a file in *.pfm format.

    Parameters:
        pfm_file: Output *.pfm file to store the data map.
        data_map: Data map to be stored.
        scale: Value used to scale the data map.
    """
    with open(pfm_file, 'wb') as pfm_file:
        color = None

        if data_map.dtype.name != 'float32':
            raise Exception('Image dtype must be float32.')

        data_map = np.flipud(data_map)

        if len(data_map.shape) == 3 and data_map.shape[2] == 3: # color data_map
            color = True
        elif len(data_map.shape) == 2 or (len(data_map.shape) == 3 and data_map.shape[2] == 1): # greyscale
            color = False
        else:
            raise Exception('Image must have H x W x 3, H x W x 1 or H x W dimensions.')

        a = 'PF\n' if color else 'Pf\n'
        b = '%d %d\n' % (data_map.shape[1], data_map.shape[0])

        pfm_file.write(a.encode('iso8859-15'))
        pfm_file.write(b.encode('iso8859-15'))

        endian = data_map.dtype.byteorder

        if endian == '<' or endian == '=' and sys.byteorder == 'little':
            scale = -scale

        c = '%f\n' % scale
        pfm_file.write(c.encode('iso8859-15'))

        data_map_string = data_map.tostring()
        pfm_file.write(data_map_string)
