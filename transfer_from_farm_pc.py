import paramiko
import os
import time
from pathlib import Path

import pandas as pd
from datetime import datetime, timedelta


from storage_info import get_video_duration
from utils import is_float

# Load configuration
import configparser
config = configparser.ConfigParser()
config.read("config.cfg")

# Configuration
farm_server_ip = "10.70.66.2"
farm_media_paths = ["/media/fo18103/Storage/CCTV/hikvision/media/"]

receiving_server_path = "/mnt/storage/cctvnet/"
farm_server_user = config["SSH"]["farm_server_user"]
farm_server_password = config["SSH"]["farm_server_password"]

MIN_FILE_AGE = 60*15

import paramiko
from pathlib import Path
from datetime import datetime, timedelta


def delete_old_files(ssh):
    try:
        # ssh = paramiko.SSHClient()
        # ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        # ssh.connect(
        #     farm_server_ip,
        #     username=farm_server_user,
        #     password=farm_server_password
        # )
        delete_script = "delete_files.sh"
        with open(delete_script, "r") as file:
            lines = file.readlines()
        cutoff_date = datetime.now() - timedelta(days=5)
        for line in lines:
            file_path = line.strip().replace("rm -f ", "")
            file_name = Path(file_path).name
            parts = file_name.split("_")
            if len(parts) < 2:
                print(f"Skipping {file_path} (Invalid filename format)")
                continue
            start_timestamp = parts[0]
            try:
                file_date = datetime.strptime(start_timestamp, "%Y%m%dT%H%M%S")
            except ValueError:
                print(f"Skipping {file_path} (Invalid timestamp format)")
                continue
            if file_date < cutoff_date:
                print(f"Deleting: {file_path} (Older than 5 days)")
                ssh.exec_command(f"{line}")
            else:
                print(f"Skipping: {file_path} (Not old enough)")

        print("Old file cleanup completed.")

    except Exception as e:
        print(f"An error occurred while deleting old files: {e}")


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

        mp4_files = list(Path("/mnt/storage/cctvnet").rglob("*.mp4"))
        if local_file in mp4_files:
            print(f"Skipping {file}, already transfered.")
            print(f"Deleting from remote {file}...")
            ssh.exec_command(f"rm -f {file}")
            continue

        print(f"Transferring {file} to {local_file}...")
        sftp.get(file, str(local_file))  # Transfer the file
        time.sleep(5)
        if local_file.exists() and get_file_size_mb(local_file) > 0:
            print(f"Deleting {file}...")
            ssh.exec_command(f"rm -f {file}")  # Delete the file from the farm server
        # delete_script = "delete_files.sh"
        # with open(delete_script, "a") as delete_file:
        #     delete_file.write(f"rm -f {file}\n")
        #     print(f"Saved delete command for {file} in {delete_script}.")


def delete_files_one_by_one():
    try:
        # Connect to the farm server via SSH
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            farm_server_ip,
            username=farm_server_user,
            password=farm_server_password
        )

        delete_script = "delete_files.sh"

        # Read the delete script line by line
        with open(delete_script, "r") as file:
            lines = file.readlines()

        for line in lines:
            command = line.strip()
            if command.startswith("rm -f"):
                print(f"Executing: {command}")
                stdin, stdout, stderr = ssh.exec_command(command)

                # Print any errors
                error = stderr.read().decode().strip()
                if error:
                    print(f"Error deleting file: {error}")

        print("All files deleted one by one.")

        # Optionally remove the script file after execution
        #ssh.exec_command(f"rm -f {delete_script}")

    except Exception as e:
        print(f"An error occurred while deleting files: {e}")
    finally:
        ssh.close()


def perform_transfer():
    print("perform_transfer...")
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
        #delete_old_files(ssh)
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        ssh.close()


def main():
    while True:
        print(f"Starting file transfer at {time.strftime('%Y-%m-%d %H:%M:%S')}")
        perform_transfer()
        #clean()
        print("Waiting for the next cycle...")
        time.sleep(1800)  # Wait for 1 hour

# def clean():
#     mp4_files = list(Path("/mnt/storage/cctvnet/").rglob("*.mp4"))
#     print(f"Found {len(mp4_files)} files.")
#     df = pd.DataFrame(mp4_files)
#
#     df["dates"] = [x.stem for x in mp4_files]
#     dt_format = "%Y%m%dT%H%M%S"
#     df["s_dates"] = [datetime.strptime(x.stem.split('_')[0], dt_format) for x in mp4_files]
#     df["f_dates"] = [datetime.strptime(x.stem.split('_')[1], dt_format) for x in mp4_files]
#     df["ip"] = [x.parent.parent.parent.name for x in mp4_files]
#     df = df.sort_values(by=["s_dates", "f_dates"])
#     dfs = [group for _, group in df.groupby('ip')]
#     for df in dfs:
#         if not is_float(str(df["ip"].values[0])):
#             continue
#         df_last = df.groupby('s_dates', as_index=False).last()
#         #print(df)
#         to_keep = df_last[0].values
#         to_rm = [item for item in df[0].values if item not in df_last[0].values]
#         for f in to_rm:
#             print(f"Removing file {f}...")
#             if f.exists():
#                 f.unlink()

def get_file_size_mb(file_path):
    """Return the file size in megabytes (MB) as a float."""
    file = Path(file_path)
    if not file.exists():
        return -1  # Return -1 if the file does not exist

    size_mb = file.stat().st_size / (1024 ** 2)  # Convert bytes to MB
    return round(size_mb, 2)


def delete_corrupted_files():
    mp4_files = list(Path("/mnt/storage/cctvnet").rglob("*.mp4"))
    for video_path in mp4_files:
        s = get_file_size_mb(video_path)
        if s > 0.9:
            continue
        print(f"Video size: {s} {video_path}")
        video_path.unlink()


if __name__ == "__main__":
    #delete_files_one_by_one()
    #delete_corrupted_files()
    main()

