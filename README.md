# Wyndhurst Farm CCTV Network Utils

This project contains the source code for managing the **Wyndhurst Farm CCTV network**.
It includes scripts for:

* Downloading videos from Hanwha cameras
* Transferring videos from the farm PC to the workstation
* Sending email reports for storage usage and farm overview visualisation
* Video post-processing (e.g. cropping)


Below is a **simple, clean overview table** suitable for an **intro section**.
It briefly describes each repository and provides the link, without operational detail.

---

## Repository Overview
| Repository                | Description                                                                                             | Link                                                                                               |
| ------------------------- | ------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| **WyndhurstCCTVNetDev**   | Workstation-side tools: Streamlit dashboard, storage monitoring, timelapses, thumbnails, and data sync. | [https://github.com/biospi/WyndhurstCCTVNetDev](https://github.com/biospi/WyndhurstCCTVNetDev)     |
| **WyndhurstFarmFrontEnd** | Simple GUI to open an SSH tunnel and access the CCTV Streamlit dashboard locally.                       | [https://github.com/biospi/WyndhurstFarmFrontEnd](https://github.com/biospi/WyndhurstFarmFrontEnd) |
| **WyndhurstCCTVNet**      | Downloads CCTV video from Wyndhurst Farm to the JOC1 workstation.                                       | [https://github.com/biospi/WyndhurstCCTVNet](https://github.com/biospi/WyndhurstCCTVNet)           |
| **WyndhurstCCTVNetFarm**  | Farm PC-side video download and management.                                                             | [https://github.com/biospi/WyndhurstCCTVNetFarm](https://github.com/biospi/WyndhurstCCTVNetFarm)   |
| **UoBDewarp**             | GUI tool to dewarp fisheye CCTV videos.                                                                 | [https://github.com/biospi/UoBDewarp](https://github.com/biospi/UoBDewarp)                         |
| **OCRSync**               | OCR-based timestamp extraction and multi-camera video synchronisation.                                  | [https://github.com/biospi/OCRSync](https://github.com/biospi/OCRSync)                             |

---

## Prerequisites
An **existing, configured workstation** is required.
Please follow the internal guide to install and configure a new workstation before proceeding.

## Sanity check

Before proceeding, verify that you have the **required access permissions** to all relevant machines.
If any connection fails, contact **IT Services** to request access.

Use the commands below to quickly confirm connectivity and port forwarding.

### 1) Connect to **JOC1 workstation**

This establishes SSH access and forwards ports to the farm network.

```bash
ssh -L 30022:10.70.66.2:22 -L 33389:localhost:3389 uobusername@IT106570.users.bris.ac.uk
```

### 2) Connect to the **Development workstation**

This forwards RDP access for development and maintenance.

```bash
ssh -L 33391:localhost:3389 uobusername@IT107338.users.bris.ac.uk
```

### 3) Connect to the **Farm PC** (via JOC1 tunnel)

This uses the forwarded SSH port from the JOC1 connection.

```bash
ssh -L 33390:localhost:3389 -p 30022 uobusername@localhost
```

### 4) Password-less SSH Login to the Farm PC from JOC1

On JOC1, generate a SSH Key (if you don’t already have one).
Keep all prompt to default.

```bash
ssh-keygen -t rsa -b 4096 -C "$USER@it106570"

ssh-copy-id username@10.70.66.2
```

Check ssh access from JOC1 to Farm PC with:

```bash
ssh username@10.70.66.2
```

**Expected outcome:**
All commands should connect without permission errors. Successful connections confirm that your SSH access and port forwarding are correctly configured.

> [!NOTE]
> Replace **uobusername** with your username for example: fo18103.




---

## How to Install

1. Clone the repository:

```bash
git clone https://github.com/biospi/WyndhurstCCTVNet.git
```

2. Change directory:

```bash
cd Wyndhurst/
```

3. Create a Python virtual environment:

```bash
python3 -m venv venv
```

4. Activate the environment:

```bash
source venv/bin/activate
```

5. Install dependencies:

```bash
pip install --upgrade pip
make environment
```

---

## Project Structure

```bash
Project Structure
.
├── start_recording.py              # Main orchestration script
├── hanwha_rtsp_multi.py             # Record videos from selected Hanwha cameras
├── rtsp_playback.py                 # Main recording worker
├── transfer_from_farm_pc.py         # Download Hikvision videos from the farm PC
├── open_ssh_tunnel.sh               # SSH tunnels for Hanwha cameras
├── open_ssh_tunnel_hikvision.sh     # SSH tunnels for Hikvision cameras
├── hanwha_ip_study.txt              # List of Hanwha camera IPs to be recorded
├── hanwha.txt                       # List of all Hanwha camera IPs (reference)
├── hikvision.txt                    # List of Hikvision camera IPs (for tunnels)
├── config.cfg                       # SSH credentials & configuration
├── storage_info.py                  # Video duration & storage helpers
```

---

## How to Use

A configuration file named `config.cfg` is required and must be placed in the project root directory.
Edit the file and format it as shown below:

```ini
[SSH]
farm_server_user = fo18103
farm_server_password =

[EMAIL]
receiver_0 = xxxxx@bristol.ac.uk
receiver_1 = xxxxx@bristol.ac.uk
sender = xxxxx@gmail.com
password = xxxx exfy cxyt wrud

[AUTH]
password_hikvision = password
password_hanwha = password
login = admin
```

To start video recording across the farm and enable error and storage reporting:

```bash
python start_recording.py
```
---

* **JOC1 workstation**

  * Downloads **Hanwha** videos directly via RTSP
  * Orchestrates everything
  * Pulls **Hikvision** videos *from* the Farm PC
* **Farm PC**

  * Downloads/stores **Hikvision** recordings only
* **Development workstation**

  * Connects to JOC1 for development and maintenance

This is designed to be **README-friendly**, readable in plain text, and printable.

---


## Script Overview

### `start_recording.py` — **Main Entry Point**

This is the **orchestration script** that coordinates the entire CCTV pipeline.

**Responsibilities:**

* Opens SSH tunnels to remote CCTV cameras (Hanwha & Hikvision)
* Starts background services for:

  * Email reporting
  * File transfer from the farm PC
* Launches the Hanwha RTSP (SD card) recording pipeline

**Execution flow:**

1. Opens SSH tunnels using shell scripts
2. Starts `report_email.py` (background)
3. Starts `transfer_from_farm_pc.py` (background)
4. Runs `hanwha_rtsp_multi.py` (foreground)

This script brings the entire system online.

---

### `open_ssh_tunnel.sh` — **Hanwha Camera SSH Tunnels**

Creates SSH port-forwarding tunnels for **Hanwha cameras** hosted behind the farm PC.

**What it does:**

* Reads camera IPs and local ports from `hanwha.txt`
* Opens one SSH tunnel per camera:

  ```
  local_port → camera_ip:554 (RTSP)
  ```
* Launches each tunnel in a separate GNOME terminal
* Uses a dedicated SSH key for authentication

This enables secure local access to remote RTSP streams.

---

### `open_ssh_tunnel_hikvision.sh` — **Hikvision Camera SSH Tunnels**

Provides the same functionality as `open_ssh_tunnel.sh`, but for **Hikvision cameras**.

**Differences:**

* Reads configuration from `hikvision.txt`

---

### `hanwha_rtsp_multi.py` — **Multi-Camera RTSP Processing**

Handles **parallel RTSP recording** from Hanwha cameras.

**Key features:**

* Reads camera metadata from `hanwha_ip_study.txt`
* Each line specifies:

  ```
  IP_ADDRESS  IS_FISHEYE  LOCAL_PORT
  ```
* Uses a `ThreadPoolExecutor` to process up to 35 cameras concurrently
* Calls `rtsp_playback.main()` for each camera
* Logs iteration duration to CSV files under `metadata/`

This script runs continuously and performs the actual CCTV video recording.

---

### `rtsp_playback.py` — **RTSP Playback, Download & Quality Control**

This script retrieves **historical RTSP recordings** from CCTV cameras, downloads them in aligned 5-minute segments, validates their integrity, and organises them into a structured storage layout.

It is the **core recording worker** invoked by `hanwha_rtsp_multi.py` for each camera.

#### Main Responsibilities

* Connects to CCTV cameras via **RTSP over SSH tunnels**
* Downloads **5-minute aligned video segments** from the camera archive
* Stores recordings in a **date- and camera-based directory structure**
* Verifies downloaded video duration and integrity
* Repairs corrupted or missing timestamps using OCR
* Handles motion-detection cameras differently where required

#### Key Features

**Time-Aligned Recording**

* Generates perfectly aligned **5-minute recording windows**
* Ensures consistent filenames:

  ```
  YYYYMMDDTHHMMSS_YYYYMMDDTHHMMSS.mp4
  ```
* Excludes night-time hours (00:00–04:00) unless explicitly enabled
  *(RTSP protocol limitation)*

**RTSP Archive Playback**

* Builds RTSP archive URLs in the form:

  ```
  rtsp://<user>:<password>@localhost:<port>/recording/<start>-<end>/backup.smp
  ```
* Uses **FFmpeg** for downloading and optional transcoding
* Supports raw stream copy or H.264 compression

**Storage Organisation**

* Automatically creates output directories:

  ```
  /mnt/storage/cctvnet/<camera_id>/<date>/videos/
  ```
* Preserves camera identity and recording date

**Quality Control & Repair**

* Verifies video duration against expected values
* Detects truncated or corrupted clips
* Repairs embedded timestamps using OCR (`repair_video_timestamp`)
* Skips duration checks for motion-detection cameras

**Gap Detection & Recovery**

* Scans existing recordings to identify missing time ranges
* Automatically re-downloads missing clips
* Splits long gaps into valid 5-minute segments

#### How It Is Used

* Called **once per camera** by `hanwha_rtsp_multi.py`
* Runs continuously as part of the multi-camera processing pipeline
* Can also be executed manually for a single camera:

```bash
python3 rtsp_playback.py <CAMERA_IP> <IS_FISHEYE> <LOCAL_PORT>
```

Example:

```bash
python3 rtsp_playback.py 10.70.66.27 0 5565
```

---

### `transfer_from_farm_pc.py` — **Video Transfer & Cleanup Service**

Periodically transfers recorded **Hikvision videos** from the farm server to the receiving server.

**Main responsibilities:**

* Connects to the farm PC via SSH/SFTP
* Scans CCTV media directories
* Transfers only files that:

  * Are older than a minimum age
  * Have not already been transferred
* Preserves directory structure during transfer
* Deletes files from the farm PC after successful transfer
* Optionally cleans up old or corrupted files

**Runtime behavior:**

* Runs in an infinite loop
* Executes every 30 minutes
* Ensures storage remains manageable on the farm PC

---

### `storage_info.py`

Provides storage-related helper functions, including:

* Video duration calculations
* File metadata utilities

---

## Typical Usage

```bash
python3 start_recording.py
```

This single command:

* Establishes SSH tunnels
* Starts background services
* Begins multi-camera RTSP recording
* Enables automatic video transfer and cleanup

---

> [!IMPORTANT]
> Use `sudo crontab -e` to configure `start_recording.py` to start automatically at system boot.

#### Example: sudo crontab -e
```bash
# HEADER: This file was autogenerated at 2025-11-26 12:16:11 +0000 by puppet.
# HEADER: While it can still be managed manually, it is definitely not recommended.
# HEADER: Note particularly that the comments starting with 'Puppet Name' should
# HEADER: not be deleted, as doing so could cause duplicate cron jobs.
# Puppet Name: mcollective_facts_yaml_refresh
0,10,20,30,40,50 * * * * '/opt/puppetlabs/puppet/bin/ruby' '/opt/puppetlabs/mcollective/plugins/mcollective/refresh_facts.rb' -o '/etc/puppetlabs/mcollective/generated-facts.yaml' -p '/var/run/puppetlabs/mcollective-facts_refre>
# Puppet Name: oom_score_adj sshd for user root by value -1000
48 * * * * /bin/bash -c 'for pid in $(/usr/bin/pgrep -u root sshd) ; do echo "-1000" > /proc/"${pid}"/oom_score_adj ; done' > /dev/null 2>&1
# Puppet Name: oom_score_adj winbindd for user root by value -1000
53 * * * * /bin/bash -c 'for pid in $(/usr/bin/pgrep -u root winbindd) ; do echo "-1000" > /proc/"${pid}"/oom_score_adj ; done' > /dev/null 2>&1
# Puppet Name: winbind network race condition workaround
*/15 * * * * /bin/bash -c 'wbinfo -t || ( systemctl stop winbind ; sleep 2 ; systemctl start winbind )' > /dev/null 2>&1
# Puppet Name: fix icinga2 log group ownership
11 23 * * * /bin/chown -R nagios:adm /var/log/icinga2
#@reboot /usr/bin/python3.10 /home/fo18103/PycharmProjects/WhyndhurstVideoTransfer/start_hanwha_recording.py >> /home/fo18103/logs/cron_start.log 2>&1
#@reboot /usr/bin/python3.10 /home/fo18103/PycharmProjects/WhyndhurstVideoTransfer/transfer_from_farm_pc.py >> /home/fo18103/logs/cron_transfer_from_farm.log 2>&1
#@reboot /usr/bin/python3.10 /home/fo18103/PycharmProjects/WhyndhurstVideoTransfer/report_email.py >> /home/fo18103/logs/cron_report_email.log 2>&1
@reboot /usr/bin/python3.10 /home/fo18103/PycharmProjects/WhyndhurstVideoTransfer/update_meta.py >> /home/fo18103/logs/update_meta.log 2>&1
```

---


## System Architecture (Text-Based Diagram)

```text
┌────────────────────────────────────────────────────────────────────────┐
│                          JOC1 WORKSTATION                              │
│        (Main Processing & Storage Node – this repository runs here)    │
│                                                                        │
│  ┌──────────────────────────────┐                                      │
│  │ start_recording.py           │                                      │
│  │ (System Orchestrator)        │                                      │
│  └─────────────┬────────────────┘                                      │
│                │                                                       │
│                ▼                                                       │
│  ┌──────────────────────────────┐                                      │
│  │ hanwha_rtsp_multi.py         │                                      │
│  │ (Multi-camera controller)    │                                      │
│  └─────────────┬────────────────┘                                      │
│                │ calls                                                 │
│                ▼                                                       │
│  ┌──────────────────────────────┐                                      │
│  │ rtsp_playback.py             │                                      │
│  │ (RTSP playback & QC worker)  │                                      │
│  │                              │                                      │
│  │  - Downloads Hanwha videos   │                                      │
│  │  - 5-minute aligned clips    │                                      │
│  │  - Timestamp repair          │                                      │
│  │  - Gap detection             │                                      │
│  └─────────────┬────────────────┘                                      │
│                │ RTSP over SSH tunnels                                 │
│                ▼                                                       │
│  ┌──────────────────────────────┐                                      │
│  │ Local Storage                │                                      │
│  │ /mnt/storage/cctvnet         |                                      |
|  | /mnt/usb_storage/cctvnet     │                                      │
│  └──────────────────────────────┘                                      │
│                                                                        │
│  ┌──────────────────────────────┐                                      │
│  │ transfer_from_farm_pc.py     │                                      │
│  │                              │                                      │
│  │  - Pulls Hikvision videos    │                                      │
│  │  - SSH / SFTP                │                                      │
│  │  - Deletes source files      │                                      │
│  └─────────────┬────────────────┘                                      │
└────────────────┼───────────────────────────────────────────────────────┘
                 │ SSH / SFTP (pull)
                 ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        WYNDHURST FARM PC                               │
│          (Farm manager office – CCTV network access)                   │
│                                                                        │
│  ┌──────────────────────────────┐     ┌──────────────────────────────┐ │
│  │ Hikvision Cameras            │     │ Hanwha Cameras               │ │
│  │                              │     │                              │ │
│  │  - Record continuously(https)│     │  - Record via(rtsp)          │ │
│  │  - Downloaded by Farm PC     │     │  - Downloaded by JOC1 PC     │ │
│  └─────────────┬────────────────┘     └─────────────┬────────────────┘ │
│                │ local recording                    │ RTSP exposure    │
│                ▼                                    ▼                  │
│  ┌──────────────────────────────┐     ┌──────────────────────────────┐ │
│  │ Farm PC Storage              │     │ SSH Tunnel Endpoints         │ │
│  │ /media/.../hikvision/media   │     │                              │ │
│  └──────────────────────────────┘     └──────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────┘
```


---

## Collaborators

[![Bristol Veterinary School](http://www.bristol.ac.uk/media-library/protected/images/uob-logo-full-colour-largest-2.png)](http://www.bristol.ac.uk/vetscience/)

---
