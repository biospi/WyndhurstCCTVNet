from pathlib import Path
from datetime import datetime
import subprocess

REMOTE_USER = "fo18103"
REMOTE_HOST = "IT107338.users.bris.ac.uk"
REMOTE_DIR = "/mnt/storage/cctvnet"

def extract_times_from_filename(filename: Path):
    try:
        name = filename.stem
        start_str, end_str = name.split('_')
        start_time = datetime.strptime(start_str, "%Y%m%dT%H%M%S")
        end_time = datetime.strptime(end_str, "%Y%m%dT%H%M%S")
        return start_time, end_time
    except Exception as e:
        print(f"Failed to parse times from: {filename}, error: {e}")
        return None, None

def rsync_file_to_remote(file: Path, base_dir: Path):
    try:
        relative_path = file.relative_to(base_dir)
        remote_path = f"{REMOTE_USER}@{REMOTE_HOST}:{REMOTE_DIR}/"
        print(f"Sending {file} to {remote_path} with relative path preserved")
        subprocess.run(
            ["rsync", "-avzR", f"./{relative_path}", remote_path],
            cwd=base_dir,
            check=True
        )
    except subprocess.CalledProcessError as e:
        print(f"Failed to rsync {file}: {e}")
    except ValueError as e:
        print(f"Error computing relative path for {file}: {e}")

def main(input_dir: Path, start_time_str: str, end_time_str: str):
    start_time = datetime.strptime(start_time_str, "%Y%m%dT%H%M%S")
    end_time = datetime.strptime(end_time_str, "%Y%m%dT%H%M%S")

    mp4_files = list(input_dir.rglob("*.mp4"))
    print(f"Found {len(mp4_files)} mp4 files")

    filtered_files = []
    for file in mp4_files:
        file_start, file_end = extract_times_from_filename(file)
        if file_start and file_end and file_end >= start_time and file_start <= end_time:
            filtered_files.append(file)

    print(f"Found {len(filtered_files)} videos in time range. Starting transfer...")
    for f in filtered_files:
        rsync_file_to_remote(f, input_dir)

if __name__ == "__main__":
    main(
        Path("/mnt/storage/cctvnet"),
        "20250101T000000",
        "20250416T000000"
    )
