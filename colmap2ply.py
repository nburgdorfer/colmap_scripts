import sys, os
import numpy as np
import argparse

parser = argparse.ArgumentParser(description='Script for converting colmap points into sparse depth maps.')
parser.add_argument('--points_file', type=str, help='Path to colmap points3d.txt file.', required=True)
parser.add_argument('--output_file', type=str, help='Output PLY file.', required=True)
parser.add_argument('--max_error', type=float, help='Maximum point error threshold.', required=True)
parser.add_argument('--min_track_len', type=int, help='Minimum required point track length.', required=True)

ARGS = parser.parse_args()

def load_points(points_file, output_file, max_error, min_track_len):
    points = []
    with open(points_file, 'r') as pf:
        lines = pf.readlines()[3:]

        for i, l in enumerate(lines):
            l = l.strip().split()
            point = l[1:7]
            error = float(l[7])
            track = l[8:]
            track_len = len(track) // 2
            
            if error <= max_error and track_len >= min_track_len:
                points.append(np.asarray(point))

    # write header meta-data
    ply_str = ""
    ply_str += "ply\n"
    ply_str += "format ascii 1.0\n"
    ply_str += "comment Right-Handed System\n"
    ply_str += f"element vertex {len(points)}\n"
    ply_str += "property float x\n"
    ply_str += "property float y\n"
    ply_str += "property float z\n"
    ply_str += "property uchar red\n"
    ply_str += "property uchar green\n"
    ply_str += "property uchar blue\n"
    ply_str += "end_header\n"

    for point in points:
        ply_str += f"{point[0]} {point[1]} {point[2]} {point[3]} {point[4]} {point[5]}\n"

    with open(output_file, 'w') as of:
        of.write(ply_str)


def main():
    points = load_points(ARGS.points_file, ARGS.output_file, ARGS.max_error, ARGS.min_track_len)


if __name__=="__main__":
    main()
