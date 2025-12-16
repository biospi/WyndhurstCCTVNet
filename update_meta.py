# Load configuration
import configparser
import json
import stat
import subprocess
import time

config = configparser.ConfigParser()
config.read("config.cfg")

# Configuration
farm_server_ip = "10.70.66.2"

farm_server_user = config["SSH"]["farm_server_user"]
farm_server_password = config["SSH"]["farm_server_password"]

dev_server_ip = "IT107338.users.bris.ac.uk"
dev_server_user = config["SSH"]["farm_server_user"]
dev_server_password = config["SSH"]["farm_server_password"]


import paramiko
from pathlib import Path
from datetime import datetime, timedelta


def get_local_df():
    """Get local df -h output."""
    return subprocess.getoutput("df -h")


def get_remote_df(ip, user, password):
    """Get df -h output from a remote server via SSH."""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, username=user, password=password)
    stdin, stdout, stderr = ssh.exec_command("df -h")
    result = stdout.read().decode()
    ssh.close()
    return result


def main():
    print("Connecting to remote server...")

    # Local folders
    LOCAL_HD = Path("/mnt/storage/frontend/hd")
    LOCAL_SENSE = Path("/mnt/storage/frontend/sense")
    LOCAL_MAP = Path("/mnt/storage/frontend/map")
    LOCAL_TIMELAPSE = Path("/mnt/storage/frontend/timelapse")
    LOGS = Path("/mnt/storage/frontend/logs")
    for folder in [LOCAL_HD, LOCAL_SENSE, LOCAL_MAP, LOCAL_TIMELAPSE, LOGS]:
        folder.mkdir(parents=True, exist_ok=True)

    # --- Collect disk usage ---
    disk_usage = {
        "joc1_server": get_local_df(),
        "farm_server": get_remote_df(farm_server_ip, farm_server_user, farm_server_password),
        "dev_server": get_remote_df(dev_server_ip, dev_server_user, dev_server_password),
    }

    # --- Save to JSON ---
    log_file = LOGS / "disk_usage.json"
    with open(log_file, "w") as f:
        json.dump(disk_usage, f, indent=4)

    print(f"[INFO] Disk usage saved to {log_file}")


    # Connect to remote server
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(farm_server_ip, username=farm_server_user, password=farm_server_password)
    sftp = ssh.open_sftp()

    # --- Helper: recursive file search ---
    def recursive_files(remote_path, ext):
        found_files = []
        for entry in sftp.listdir_attr(remote_path):
            remote_entry = f"{remote_path}/{entry.filename}"
            # Check if entry is a directory
            if stat.S_ISDIR(entry.st_mode):
                found_files.extend(recursive_files(remote_entry, ext))
            elif entry.filename.lower().endswith(ext):
                found_files.append((remote_entry, entry.st_mtime))
        return found_files

    # --- 1. Download all .jpg from HD folder ---
    hd_path = "/mnt/storage/thumbnails/hd"
    try:
        for file_attr in sftp.listdir_attr(hd_path):
            if file_attr.filename.lower().endswith(".jpg"):
                remote_file = f"{hd_path}/{file_attr.filename}"
                local_file = LOCAL_HD / file_attr.filename
                sftp.get(remote_file, str(local_file))
                print(f"Downloaded {remote_file} → {local_file}")
    except FileNotFoundError:
        print(f"HD folder not found: {hd_path}")

    # --- 2. Download most recent .jpg from MAP folder ---
    map_path = "/mnt/storage/thumbnails/map"
    jpg_files = recursive_files(map_path, ".jpg")
    if jpg_files:
        latest_jpg = max(jpg_files, key=lambda x: x[1])[0]
        for f in LOCAL_MAP.iterdir():
            if f.is_file():
                f.unlink()
        local_file = LOCAL_MAP / Path(latest_jpg).name
        sftp.get(latest_jpg, str(local_file))
        print(f"Downloaded latest jpg {latest_jpg} → {local_file}")

    # --- 3. Download most recent .mp4 from MAP folder ---
    mp4_files = recursive_files(map_path, ".mp4")
    if mp4_files:
        latest_mp4 = max(mp4_files, key=lambda x: extract_date_from_filename(Path(x[0]).name))[0]
        local_file = LOCAL_TIMELAPSE / "timelapse.mp4"
        sftp.get(latest_mp4, str(local_file))
        print(f"Downloaded latest mp4 {latest_mp4} → {local_file}")

    # --- 1. Download all .json from HD folder ---
    sense_path = "/mnt/storage/sense"
    try:
        for file_attr in sftp.listdir_attr(sense_path):
            if file_attr.filename.lower().endswith(".json"):
                remote_file = f"{sense_path}/{file_attr.filename}"
                local_file = LOCAL_SENSE / file_attr.filename
                sftp.get(remote_file, str(local_file))
                print(f"Downloaded {remote_file} → {local_file}")
    except FileNotFoundError:
        print(f"SENSE folder not found: {sense_path}")

    sftp.close()
    ssh.close()
    print("Done!")

def extract_date_from_filename(filename: str):
    # filename looks like Timelapse_20250728.mp4
    date_str = Path(filename).stem.split("_")[1]   # "20250728"
    return int(date_str)


if __name__ == "__main__":
    while True:
        try:
            main()
            time.sleep(60)
        except paramiko.ssh_exception.SSHException as e:
            print(e)
