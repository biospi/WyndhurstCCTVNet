from pathlib import Path
from datetime import datetime
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

REMOTE_USER = "fo18103"
REMOTE_HOST = "IT107338.users.bris.ac.uk"
REMOTE_DIR = "/mnt/storage/cctvnet"

print_lock = threading.Lock()

def extract_times_from_filename(filename: Path):
    try:
        name = filename.stem
        start_str, end_str = name.split('_')
        start_time = datetime.strptime(start_str, "%Y%m%dT%H%M%S")
        end_time = datetime.strptime(end_str, "%Y%m%dT%H%M%S")
        return start_time, end_time
    except Exception:
        return None, None

def rsync_file_to_remote(file: Path, base_dir: Path, index: int, total: int):
    try:
        relative_path = file.relative_to(base_dir)
        remote_path = f"{REMOTE_USER}@{REMOTE_HOST}:{REMOTE_DIR}/"
        subprocess.run(
            ["rsync", "-azR", f"./{relative_path}", remote_path],
            cwd=base_dir,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        with print_lock:
            print(f"[{index}/{total}] Synced: {file.name}")
    except subprocess.CalledProcessError:
        with print_lock:
            print(f"[{index}/{total}] FAILED: {file.name}")
    except ValueError:
        with print_lock:
            print(f"[{index}/{total}] PATH ERROR: {file.name}")

def main(input_dir: Path, start_time_str: str, end_time_str: str):
    start_time = datetime.strptime(start_time_str, "%Y%m%dT%H%M%S")
    end_time = datetime.strptime(end_time_str, "%Y%m%dT%H%M%S")

    mp4_files = list(input_dir.rglob("*.mp4"))
    filtered_files = [
        f for f in mp4_files
        if (times := extract_times_from_filename(f)) and
           times[0] and times[1] and
           times[1] >= start_time and times[0] <= end_time
    ]

    total_files = len(filtered_files)
    print(f"Starting transfer of {total_files} video(s)...")

    with ThreadPoolExecutor(max_workers=25) as executor:
        futures = [
            executor.submit(rsync_file_to_remote, file, input_dir, i + 1, total_files)
            for i, file in enumerate(filtered_files)
        ]
        for _ in as_completed(futures):
            pass  # wait for all to finish

if __name__ == "__main__":
    main(
        Path("/mnt/storage/cctvnet"),
        "20250101T000000",
        "20250416T000000"
    )
