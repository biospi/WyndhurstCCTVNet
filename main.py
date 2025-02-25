import paramiko
import os
import time
from pathlib import Path
import configparser
import pandas as pd
from datetime import datetime

from utils import is_float

# Load configuration
config = configparser.ConfigParser()
config.read("config.cfg")

# Configuration
farm_server_ip = "10.70.66.2"
farm_media_paths = ["/media/fo18103/Storage/CCTV/hanwha/", "/media/fo18103/Storage/CCTV/hikvision/media/"]

receiving_server_path = "/mnt/storage/scratch/cctv/"
farm_server_user = config["SSH"]["farm_server_user"]
farm_server_password = config["SSH"]["farm_server_password"]

MIN_FILE_AGE = 60*15


def is_file_old_enough(ssh, file_path):
    cmd = f"stat -c %Y {file_path}"  # Get the last modification time in epoch seconds
    stdin, stdout, stderr = ssh.exec_command(cmd)
    last_modified = int(stdout.read().decode().strip())
    current_time = time.time()
    return current_time - last_modified >= MIN_FILE_AGE


def get_sorted_files(ssh, path):
    stdin, stdout, stderr = ssh.exec_command(f"find {path} -type f -printf '%T@ %p\n' | sort -n")
    #stdin, stdout, stderr = ssh.exec_command(f"find {path} -type f -size +200M -printf '%T@ %p\n' | sort -n")
    files = [line.strip().split(maxsplit=1)[1] for line in stdout]
    return files


def ensure_directory_exists(local_path):
    local_path = Path(local_path)
    if not local_path.exists():
        print(f"Creating directory: {local_path}")
        local_path.mkdir(parents=True, exist_ok=True)


def transfer_files(files, sftp, remote_path, ssh, farm_media_path):
    for file in files:
        print(f"Checking age for file: {file}")
        if not is_file_old_enough(ssh, file):
            print(f"Skipping {file}, not old enough yet.")
            continue

        # Preserve the folder structure
        relative_path = Path(file).relative_to(farm_media_path)  # Get relative path of the file
        local_directory = Path(remote_path) / relative_path.parent  # Local directory in the receiving server
        local_file = local_directory / relative_path.name  # Full local file path

        # Ensure the directory exists on the receiving server
        ensure_directory_exists(local_directory)

        print(f"Transferring {file} to {local_file}...")
        sftp.get(file, str(local_file))  # Transfer the file
        print(f"Deleting {file}...")
        ssh.exec_command(f"rm -f {file}")  # Delete the file from the farm server



def perform_transfer():
    try:
        # Connect to the farm server via SSH
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            farm_server_ip,
            username=farm_server_user,
            password=farm_server_password
        )

        for farm_media_path in farm_media_paths:
            print(f"Fetching file list {farm_media_path} ...")
            sorted_files = get_sorted_files(ssh, farm_media_path)
            print(f"Found {len(sorted_files)} files to check and transfer.")

            # Setup SFTP for file transfer
            with ssh.open_sftp() as sftp:
                transfer_files(sorted_files, sftp, receiving_server_path, ssh, farm_media_path)

        print("File transfer and cleanup completed successfully.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        ssh.close()


def main():
    while True:
        print(f"Starting file transfer at {time.strftime('%Y-%m-%d %H:%M:%S')}")
        perform_transfer()
        clean()
        print("Waiting for the next cycle...")
        time.sleep(3600)  # Wait for 1 hour

def clean():
    mp4_files = list(Path("/mnt/storage/scratch/cctv/").rglob("*.mp4"))
    print(f"Found {len(mp4_files)} files.")
    df = pd.DataFrame(mp4_files)

    df["dates"] = [x.stem for x in mp4_files]
    dt_format = "%Y%m%dT%H%M%S"
    df["s_dates"] = [datetime.strptime(x.stem.split('_')[0], dt_format) for x in mp4_files]
    df["f_dates"] = [datetime.strptime(x.stem.split('_')[1], dt_format) for x in mp4_files]
    df["ip"] = [x.parent.parent.parent.name for x in mp4_files]
    df = df.sort_values(by=["s_dates", "f_dates"])
    dfs = [group for _, group in df.groupby('ip')]
    for df in dfs:
        if not is_float(str(df["ip"].values[0])):
            continue
        df_last = df.groupby('s_dates', as_index=False).last()
        #print(df)
        to_keep = df_last[0].values
        to_rm = [item for item in df[0].values if item not in df_last[0].values]
        for f in to_rm:
            print(f"Removing file {f}...")
            if f.exists():
                f.unlink()

if __name__ == "__main__":
    main()

