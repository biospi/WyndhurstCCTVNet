import time

import paramiko
import json
from pathlib import Path
from datetime import datetime
import yagmail
import farm_map
import storage_info
import os
from utils import get_latest_file

import configparser
config = configparser.ConfigParser()
config.read("config.cfg")

# Config for Farm PC
farm_server_ip = "10.70.66.2"
remote_log_path = "/mnt/camera_logs/"
local_download_dir = Path("/tmp/camera_status_download")
farm_server_user = config["SSH"]["farm_server_user"]
farm_server_password = config["SSH"]["farm_server_password"]
# Email Configuration
SMTP_SERVER = "smtp.gmail.com"  # Replace with your SMTP server
SMTP_PORT = 587
EMAIL_SENDER = config["EMAIL"]["sender"]
EMAIL_PASSWORD = config["EMAIL"]["password"]
EMAIL_RECEIVER = config["EMAIL"]["receiver_0"]


local_download_dir.mkdir(exist_ok=True)

def get_latest_json_filename(ssh):
    """Runs a remote command to get the latest JSON log file path."""
    cmd = f"ls -t {remote_log_path}*.json | head -n 1"
    stdin, stdout, stderr = ssh.exec_command(cmd)
    result = stdout.read().decode().strip()
    if result:
        return result
    else:
        print("[ERROR] No .json files found or cannot access remote path.")
        print(stderr.read().decode().strip())
        return None

def download_file(sftp, remote_file):
    """Downloads the remote file to local temp directory."""
    local_file = local_download_dir / Path(remote_file).name
    sftp.get(remote_file, str(local_file))
    return local_file

def parse_and_check(local_file):
    """Checks JSON content and logs if any camera is not recording."""
    try:
        with open(local_file, 'r') as f:
            data = json.load(f)
        timestamp = data.get("timestamp", "N/A")
        camera_status = data.get("camera_status", {})

        non_recording = [ip for ip, status in camera_status.items() if not status]

        if non_recording:
            print(f"\nIssue Detected at {timestamp}:")
            for ip in non_recording:
                print(f"{ip} is NOT recording")
                send_email(f"{ip} is NOT recording", f"\nIssue Detected at {timestamp}:", attachment_path=[local_file])
        else:
            print("All cameras recording")
            print(data)
    except Exception as e:
        print(f"[ERROR] Could not read/parse file: {e}")

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(farm_server_ip, username=farm_server_user, password=farm_server_password)
        sftp = ssh.open_sftp()

        remote_file = get_latest_json_filename(ssh)
        if not remote_file:
            return

        local_file = download_file(sftp, remote_file)
        parse_and_check(local_file)

    except Exception as e:
        print(f"[ERROR] SSH/SFTP operation failed: {e}")
    finally:
        ssh.close()


def send_email(subject, body, attachment_path=None):
    """Sends an email with the given subject, body, and optional attachment."""
    print(f"attachment: {attachment_path}")
    try:
        yag = yagmail.SMTP(EMAIL_SENDER, EMAIL_PASSWORD)
        hostname = os.uname().nodename
        print("Computer Name:", hostname)

        # If an attachment is provided, send the email with it
        if attachment_path:
            yag.send(
                EMAIL_RECEIVER,
                subject=subject,
                contents=body,
                attachments=attachment_path
            )
        else:
            yag.send(EMAIL_RECEIVER, subject=subject, contents=body)

        print("Email sent successfully!")
    except Exception as e:
        print(f"Error sending email: {str(e)}")


if __name__ == "__main__":
    while True:
        main()
        print("sleeping...")
        time.sleep(1800)