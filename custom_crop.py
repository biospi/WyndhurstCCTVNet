import time
from pathlib import Path
import cv2
import subprocess

def crop_with_ffmpeg(input_path: Path, output_path: Path, fps: float):
    cmd = [
        "ffmpeg",
        "-i", str(input_path),
        "-vf", "crop=1640:1520:0:0",     # Crop 1640 wide from the left
        "-r", f"{fps:.3f}",
        "-map_metadata", "0",            # Preserve metadata
        "-c:v", "libx264",               # Video codec
        "-crf", "32",                    # Quality (lower is better)
        "-preset", "slow",               # Encoding speed/efficiency tradeoff
        "-c:a", "copy",                  # Copy audio without re-encoding
        str(output_path)
    ]
    print(f"Running FFmpeg on: {input_path.name}")
    try:
        subprocess.run(cmd, check=True)
        return output_path.exists()
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg failed for {input_path.name}: {e}")
        return False

def main(input_dir):
    mp4_files = list(input_dir.rglob("*.mp4"))
    print(f"Found {len(mp4_files)} .mp4 files")

    for i, video in enumerate(mp4_files):
        print(f"Processing {i}/{len(mp4_files)}...")
        if "_cropped" in video.name:
            print(f"Skipping {video.name}")
            continue
        cap = cv2.VideoCapture(str(video))
        if not cap.isOpened():
            print(f"Failed to open {video}")
            continue

        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        cap.release()

        print(f"{video}: {width}x{height} @ {fps:.3f} fps")
        if 2 > fps > 30:
            print("Input fps is wrong!")
            print(f"Skipping {video}")
            continue

        if width == 2688 and height == 1520:
            output_path = video.with_stem(video.stem + "_cropped")
            if crop_with_ffmpeg(video, output_path, fps):
                print(f"Cropping succeeded: {output_path.name}")
                try:
                    video.unlink()
                    print(f"Deleted original: {video.name}")
                except Exception as e:
                    print(f"Failed to delete {video.name}: {e}")
            else:
                print(f"Cropping failed: {video.name}")

if __name__ == "__main__":
    while True:
        main(Path("/mnt/storage/cctvnet/66.137"))
        time.sleep(86400)
