import cv2
import os
import argparse

parser = argparse.ArgumentParser(description='Script for converting colmap camera parameters into sfm format.')
parser.add_argument('--video_path', type=str, help='Path to input video.', required=True)
parser.add_argument('--output_path', type=str, help='Path to output scene data.', required=True)
parser.add_argument('--frame_freq', default=20, type=int, help='The frequency in which to store frames.')
ARGS=parser.parse_args()

def main():
    output_images_path = os.path.join(ARGS.output_path, "Images")
    os.makedirs(output_images_path, exist_ok=True)

    vidcap = cv2.VideoCapture(ARGS.video_path)
    total_count = 0
    frame_count = 0
    success = True

    while success:
        success, image = vidcap.read()
        if success:
            h, w, _ = image.shape
            dsize = (int(w*0.5), int(h*0.5))
            image = cv2.resize(image, dsize=dsize)
            if total_count % ARGS.frame_freq == 0:
                frame_filename = os.path.join(output_images_path, f"{frame_count:06d}.png")
                cv2.imwrite(frame_filename, image)
                frame_count += 1
        else:
            break
        total_count += 1

    vidcap.release()
    cv2.destroyAllWindows()
    print(f"Extracted {frame_count} frames from '{ARGS.video_path}' to '{output_images_path}'")

if __name__ == "__main__":
    main()