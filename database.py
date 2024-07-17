import sys, os
import sqlite3
import numpy as np
from scipy.spatial.transform import Rotation as R
import cv2
from cvt.io import read_cams_sfm
import argparse

parser = argparse.ArgumentParser(description='Script for initializing colmap sparse model from a known trajectory.')
parser.add_argument('--cam_path', type=str, help='Path to scene cameras.', required=True)
parser.add_argument('--image_path', type=str, help='Path to scene images.', required=True)
parser.add_argument('--database_file', type=str, help='Path to desired colmap database.db file.', required=True)
parser.add_argument('--output_path', type=str, help='Sparse depth output path.', required=True)
ARGS = parser.parse_args()



IS_PYTHON3 = sys.version_info[0] >= 3

MAX_IMAGE_ID = 2 ** 31 - 1

CREATE_CAMERAS_TABLE = """CREATE TABLE IF NOT EXISTS cameras (
    camera_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    model INTEGER NOT NULL,
    width INTEGER NOT NULL,
    height INTEGER NOT NULL,
    params BLOB,
    prior_focal_length INTEGER NOT NULL)"""

CREATE_DESCRIPTORS_TABLE = """CREATE TABLE IF NOT EXISTS descriptors (
    image_id INTEGER PRIMARY KEY NOT NULL,
    rows INTEGER NOT NULL,
    cols INTEGER NOT NULL,
    data BLOB,
    FOREIGN KEY(image_id) REFERENCES images(image_id) ON DELETE CASCADE)"""

CREATE_IMAGES_TABLE = """CREATE TABLE IF NOT EXISTS images (
    image_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    name TEXT NOT NULL UNIQUE,
    camera_id INTEGER NOT NULL,
    prior_qw FLOAT,
    prior_qx FLOAT,
    prior_qy FLOAT,
    prior_qz FLOAT,
    prior_tx FLOAT,
    prior_ty FLOAT,
    prior_tz FLOAT,
    CONSTRAINT image_id_check CHECK(image_id >= 0 and image_id < {}),
    FOREIGN KEY(camera_id) REFERENCES cameras(camera_id))
""".format(
    MAX_IMAGE_ID
)

CREATE_POSE_PRIORS_TABLE = """CREATE TABLE IF NOT EXISTS pose_priors (
    image_id INTEGER PRIMARY KEY NOT NULL,
    position BLOB,
    coordinate_system INTEGER NOT NULL,
    FOREIGN KEY(image_id) REFERENCES images(image_id) ON DELETE CASCADE)"""

CREATE_TWO_VIEW_GEOMETRIES_TABLE = """
CREATE TABLE IF NOT EXISTS two_view_geometries (
    pair_id INTEGER PRIMARY KEY NOT NULL,
    rows INTEGER NOT NULL,
    cols INTEGER NOT NULL,
    data BLOB,
    config INTEGER NOT NULL,
    F BLOB,
    E BLOB,
    H BLOB,
    qvec BLOB,
    tvec BLOB)
"""

CREATE_KEYPOINTS_TABLE = """CREATE TABLE IF NOT EXISTS keypoints (
    image_id INTEGER PRIMARY KEY NOT NULL,
    rows INTEGER NOT NULL,
    cols INTEGER NOT NULL,
    data BLOB,
    FOREIGN KEY(image_id) REFERENCES images(image_id) ON DELETE CASCADE)
"""

CREATE_MATCHES_TABLE = """CREATE TABLE IF NOT EXISTS matches (
    pair_id INTEGER PRIMARY KEY NOT NULL,
    rows INTEGER NOT NULL,
    cols INTEGER NOT NULL,
    data BLOB)"""

CREATE_NAME_INDEX = (
    "CREATE UNIQUE INDEX IF NOT EXISTS index_name ON images(name)"
)

CREATE_ALL = "; ".join(
    [
        CREATE_CAMERAS_TABLE,
        CREATE_IMAGES_TABLE,
        CREATE_KEYPOINTS_TABLE,
        CREATE_DESCRIPTORS_TABLE,
        CREATE_MATCHES_TABLE,
        CREATE_TWO_VIEW_GEOMETRIES_TABLE,
        CREATE_NAME_INDEX,
    ]
)


def image_ids_to_pair_id(image_id1, image_id2):
    if image_id1 > image_id2:
        image_id1, image_id2 = image_id2, image_id1
    return image_id1 * MAX_IMAGE_ID + image_id2


def pair_id_to_image_ids(pair_id):
    image_id2 = pair_id % MAX_IMAGE_ID
    image_id1 = (pair_id - image_id2) / MAX_IMAGE_ID
    return image_id1, image_id2


def array_to_blob(array):
    if IS_PYTHON3:
        return array.tobytes()
    else:
        return np.getbuffer(array)


def blob_to_array(blob, dtype, shape=(-1,)):
    if IS_PYTHON3:
        return np.fromstring(blob, dtype=dtype).reshape(*shape)
    else:
        return np.frombuffer(blob, dtype=dtype).reshape(*shape)


class COLMAPDatabase(sqlite3.Connection):
    @staticmethod
    def connect(database_path):
        return sqlite3.connect(database_path, factory=COLMAPDatabase)

    def __init__(self, *args, **kwargs):
        super(COLMAPDatabase, self).__init__(*args, **kwargs)

        self.create_tables = lambda: self.executescript(CREATE_ALL)
        self.create_cameras_table = lambda: self.executescript(
            CREATE_CAMERAS_TABLE
        )
        self.create_descriptors_table = lambda: self.executescript(
            CREATE_DESCRIPTORS_TABLE
        )
        self.create_images_table = lambda: self.executescript(
            CREATE_IMAGES_TABLE
        )
        self.create_pose_priors_table = lambda: self.executescript(
            CREATE_POSE_PRIORS_TABLE
        )
        self.create_two_view_geometries_table = lambda: self.executescript(
            CREATE_TWO_VIEW_GEOMETRIES_TABLE
        )
        self.create_keypoints_table = lambda: self.executescript(
            CREATE_KEYPOINTS_TABLE
        )
        self.create_matches_table = lambda: self.executescript(
            CREATE_MATCHES_TABLE
        )
        self.create_name_index = lambda: self.executescript(CREATE_NAME_INDEX)

    def add_camera(
        self,
        model,
        width,
        height,
        params,
        prior_focal_length=False,
        camera_id=None,
    ):
        params = np.asarray(params, np.float64)
        cursor = self.execute(
            "INSERT INTO cameras VALUES (?, ?, ?, ?, ?, ?)",
            (
                camera_id,
                model,
                width,
                height,
                array_to_blob(params),
                prior_focal_length,
            ),
        )
        return cursor.lastrowid

    def add_image(
        self,
        name,
        camera_id,
        prior_q=np.full(4, np.NaN),
        prior_t=np.full(3, np.NaN),
        image_id=None,
    ):
        cursor = self.execute(
            "INSERT INTO images VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                image_id,
                name,
                camera_id,
                prior_q[0],
                prior_q[1],
                prior_q[2],
                prior_q[3],
                prior_t[0],
                prior_t[1],
                prior_t[2],
            ),
        )
        return cursor.lastrowid

    def add_pose_prior(self, image_id, position, coordinate_system=-1):
        position = np.asarray(position, dtype=np.float64)
        self.execute(
            "INSERT INTO pose_priors VALUES (?, ?, ?)",
            (image_id, array_to_blob(position), coordinate_system),
        )

    def add_keypoints(self, image_id, keypoints):
        assert len(keypoints.shape) == 2
        assert keypoints.shape[1] in [2, 4, 6]

        keypoints = np.asarray(keypoints, np.float32)
        self.execute(
            "INSERT INTO keypoints VALUES (?, ?, ?, ?)",
            (image_id,) + keypoints.shape + (array_to_blob(keypoints),),
        )

    def add_descriptors(self, image_id, descriptors):
        descriptors = np.ascontiguousarray(descriptors, np.uint8)
        self.execute(
            "INSERT INTO descriptors VALUES (?, ?, ?, ?)",
            (image_id,) + descriptors.shape + (array_to_blob(descriptors),),
        )

    def add_matches(self, image_id1, image_id2, matches):
        assert len(matches.shape) == 2
        assert matches.shape[1] == 2

        if image_id1 > image_id2:
            matches = matches[:, ::-1]

        pair_id = image_ids_to_pair_id(image_id1, image_id2)
        matches = np.asarray(matches, np.uint32)
        self.execute(
            "INSERT INTO matches VALUES (?, ?, ?, ?)",
            (pair_id,) + matches.shape + (array_to_blob(matches),),
        )

    def add_two_view_geometry(
        self,
        image_id1,
        image_id2,
        matches,
        F=np.eye(3),
        E=np.eye(3),
        H=np.eye(3),
        qvec=np.array([1.0, 0.0, 0.0, 0.0]),
        tvec=np.zeros(3),
        config=2,
    ):
        assert len(matches.shape) == 2
        assert matches.shape[1] == 2

        if image_id1 > image_id2:
            matches = matches[:, ::-1]

        pair_id = image_ids_to_pair_id(image_id1, image_id2)
        matches = np.asarray(matches, np.uint32)
        F = np.asarray(F, dtype=np.float64)
        E = np.asarray(E, dtype=np.float64)
        H = np.asarray(H, dtype=np.float64)
        qvec = np.asarray(qvec, dtype=np.float64)
        tvec = np.asarray(tvec, dtype=np.float64)
        self.execute(
            "INSERT INTO two_view_geometries VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (pair_id,)
            + matches.shape
            + (
                array_to_blob(matches),
                config,
                array_to_blob(F),
                array_to_blob(E),
                array_to_blob(H),
                array_to_blob(qvec),
                array_to_blob(tvec),
            ),
        )


def gen_database(database_file, cam_params, height, width, image_files, model=1):
    # Open the database.
    db = COLMAPDatabase.connect(database_file)

    # For convenience, try creating all the tables upfront.
    db.create_tables()

    # add camera
    camera_id = db.add_camera(model, width, height, cam_params)

    # Create dummy images.
    for i,img in enumerate(image_files):
        _ = db.add_image(name=img, camera_id=camera_id, image_id=int(i+1))

    # Commit the data to the file.
    db.commit()

    # Clean up.
    db.close()

def gen_cameras_file(cams, h, w, output_path, cam_file="cameras.txt"):
    cam_str = "# Camera list with one line of data per camera:\n"
    cam_str += "# CAMERA_ID, MODEL, WIDTH, HEIGHT, PARAMS[]\n"
    cam_str += "# Number of cameras: 1\n"
    cam_str += f"1 PINHOLE {w} {h} {cams[0,1,0,0]} {cams[0,1,1,1]} {cams[0,1,0,2]} {cams[0,1,1,2]}\n"
    cam_params = np.asarray([cams[0,1,0,0], cams[0,1,1,1], cams[0,1,0,2], cams[0,1,1,2]])

    with open(os.path.join(output_path,cam_file),'w') as of:
        of.write(cam_str)

    return cam_params

def gen_images_file(cams, image_files, num_cams, output_path, image_file="images.txt"):
    img_str = "# Image list with two lines of data per image:\n"
    img_str += "#   IMAGE_ID, QW, QX, QY, QZ, TX, TY, TZ, CAMERA_ID, NAME\n"
    img_str += "#   POINTS2D[] as (X, Y, POINT3D_ID)\n"
    img_str += f"# Number of images: {num_cams}, mean observations per image: \n"
    for i, img in enumerate(image_files):
        qx,qy,qz,qw = (R.from_matrix(cams[i,0,:3,:3])).as_quat()
        tx,ty,tz = cams[i,0,:3,3]
        img_str += f"{int(i+1)} {qw} {qx} {qy} {qz} {tx} {ty} {tz} 1 {img}\n\n"

    with open(os.path.join(output_path,image_file),'w') as of:
        of.write(img_str)

def main():
    if os.path.exists(ARGS.database_file):
        os.remove(ARGS.database_file)

    # read in data
    cams = read_cams_sfm(ARGS.cam_path)
    num_cams = cams.shape[0]
    image_files = os.listdir(ARGS.image_path)
    image_files = [img for img in image_files if img[-3:] == "png" ]
    image_files.sort()

    # create cameras file
    img = cv2.imread(os.path.join(ARGS.image_path,image_files[0]))
    height, width, _ = img.shape
    cam_params = gen_cameras_file(cams, height, width, ARGS.output_path)

    # create images file
    gen_images_file(cams, image_files, num_cams, ARGS.output_path)

    # create points3D file
    fp = open(os.path.join(ARGS.output_path,"points3D.txt"),'w')
    fp.close()

    # generate the database.db file
    gen_database(ARGS.database_file, cam_params, height, width, image_files)

if __name__=="__main__":
    main()
