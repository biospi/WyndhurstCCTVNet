import os
import subprocess
import smtplib
import re

import pandas as pd
import schedule
import time
from pathlib import Path
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import yagmail

import farm_map
import storage_info
from utils import get_latest_file
import configparser
config = configparser.ConfigParser()
config.read("config.cfg")

# Email Configuration
SMTP_SERVER = "smtp.gmail.com"  # Replace with your SMTP server
SMTP_PORT = 587
EMAIL_RECEIVER = [config["EMAIL"]["receiver_0"], config["EMAIL"]["receiver_1"]]
EMAIL_SENDER = config["EMAIL"]["sender"]
EMAIL_PASSWORD = config["EMAIL"]["password"]

# Folder Path
FOLDER_PATH = Path("/mnt/storage/cctvnet")

def get_disk_space():
    """Returns detailed disk space info using 'df -h'."""
    try:
        result = subprocess.run(["df", "-h"], capture_output=True, text=True, check=True)
        return f"Disk Space Report:\n{result.stdout}"
    except subprocess.CalledProcessError as e:
        return f"Error retrieving disk space info: {e}"


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
                subject=f"Workstation {hostname} report",
                contents=body,
                attachments=attachment_path
            )
        else:
            yag.send(EMAIL_RECEIVER, subject=f"Workstation {hostname} report", contents=body)

        print("Email sent successfully!")
    except Exception as e:
        print(f"Error sending email: {str(e)}")


def report_status():
    """Generates and sends the report via email."""
    print(f"Running report at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    disk_space = get_disk_space()
    print(f"Disk space: {disk_space}")
    latest_file = get_latest_file(FOLDER_PATH)
    latest_file = "".join(latest_file)
    print(f"Latest file: {latest_file}")

    email_body = f"{disk_space}\n\n{latest_file}"
    storage_info.main()
    folder_path = Path("/home/fo18103/PycharmProjects/WhyndhurstVideoTransfer/storage")
    heatmap_storage_files = list(folder_path.rglob("*.png"))
    heatmap_storage_files.sort()
    farm_map.main()
    map_files = list(Path("/mnt/storage/thumbnails/map").rglob("*.png"))
    map_files.sort()
    send_email("Daily Storage Report", email_body, attachment_path=[heatmap_storage_files[-1], map_files[-1], folder_path / "0_storage_total.png"])

# Schedule the script to run daily at 1 PM
schedule.every().day.at("08:00").do(report_status)
schedule.every().day.at("17:00").do(report_status)

def main():
    print("Scheduler started")
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    report_status()
    main()
