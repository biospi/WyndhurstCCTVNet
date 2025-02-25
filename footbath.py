from pathlib import Path
import shutil
import time

# List of source folders to copy from
source_folders = [
    "/mnt/storage/scratch/cctv/66.28/",
    "/mnt/storage/scratch/cctv/66.29/",
    "/mnt/storage/scratch/cctv/66.30/",
    "/mnt/storage/scratch/cctv/66.31/",
    "/mnt/storage/scratch/cctv/66.138/",
    "/mnt/storage/scratch/cctv/66.137/",
]

# Destination folder
destination_folder = Path("/mnt/storage/scratch/footbath/")

# Ensure the destination folder exists
destination_folder.mkdir(parents=True, exist_ok=True)

# Function to copy entire folders from source to destination
def copy_folders(src, dest):
    src_path = Path(src)
    if not src_path.exists() or not src_path.is_dir():
        print(f"Source folder does not exist or is not a directory: {src}")
        return

    dest_path = dest / src_path.name
    if dest_path.exists():
        # If the destination folder exists, merge contents
        shutil.copytree(src_path, dest_path, dirs_exist_ok=True)
    else:
        # Copy the entire folder
        shutil.copytree(src_path, dest_path)

def run_hourly_copy():
    while True:
        print(f"Starting copy process at {time.strftime('%Y-%m-%d %H:%M:%S')}")
        # Copy each source folder into the destination folder
        for folder in source_folders:
            print(f"Copying folder {folder} to {destination_folder}")
            copy_folders(folder, destination_folder)
        print("Copying complete. Waiting for the next cycle...\n")
        # Sleep for one hour
        time.sleep(3600)

if __name__ == "__main__":
    run_hourly_copy()
