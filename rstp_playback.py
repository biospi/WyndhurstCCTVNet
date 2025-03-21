import json
import sys
import time
import requests
# import xmltodict
from requests.auth import HTTPDigestAuth
from datetime import datetime, timedelta
import subprocess
from pathlib import Path

from storage_info import parse_datetime
from utils import run_cmd, SOURCE_PATH

MAX_ONVIF_RETRY = 5
MAX_DOWNLOAD_RETRIES = 1
# EXPECTED_DURATION_LANDSCAPE = 300
# EXPECTED_DURATION_FISH = 290
USERNAME = "admin"
PASSWORD = "Ocs881212"

HEADERS = {"Content-Type": "text/xml; charset=utf-8"}
AUTH = HTTPDigestAuth(USERNAME, PASSWORD)

def create_output_directory(output_file: str, ip_tag: str):
    """
    Creates an output directory based on the first timestamp of the output file.

    :param output_file: The path to the output file.
    :return: The path to the created directory.
    """
    timestamp_str = output_file.split('_')[0]
    timestamp = datetime.strptime(timestamp_str, '%Y%m%dT%H%M%S')
    date_subfolder = timestamp.strftime('%Y%b%d')
    tag = ip_tag.split('.')[-1]
    output_dir = Path(f'/mnt/storage/cctv/66.{tag}/{date_subfolder}/videos/')
    output_dir.mkdir(parents=True, exist_ok=True)
    #print(output_dir)
    return output_dir

def generate_perfect_5min_ranges(start: str, end: str) -> list:
    """Generate 5-minute aligned recording ranges from start to end timestamps."""

    # Convert input strings to datetime objects
    start_dt = datetime.strptime(start, "%Y-%m-%dT%H:%M:%SZ")
    end_dt = datetime.strptime(end, "%Y-%m-%dT%H:%M:%SZ")

    # Align start time to the nearest 5-minute mark
    aligned_start_dt = start_dt.replace(second=0, microsecond=0)
    if aligned_start_dt.minute % 5 != 0:
        aligned_start_dt += timedelta(minutes=(5 - aligned_start_dt.minute % 5))  # Move up to next 5-minute mark

    step = timedelta(minutes=5, seconds=1)
    ranges = []
    ranges_datetime = []
    current_dt = aligned_start_dt

    while current_dt < end_dt:
        next_dt = current_dt + step
        if next_dt > end_dt:
            break  # Stop if the next step exceeds the end time
        ranges.append([current_dt.strftime('%Y%m%dT%H%M%S'), next_dt.strftime('%Y%m%dT%H%M%S')])
        ranges_datetime.append([current_dt, next_dt])
        current_dt = next_dt  # Move to the next 5-minute interval

    return ranges, ranges_datetime

def get_video_duration(file_path):
    """Get the duration of a video file in seconds using ffprobe."""
    try:
        result = subprocess.run(
            [
                "ffprobe", "-i", file_path, "-show_entries",
                "format=duration", "-v", "quiet", "-of", "csv=p=0"
            ],
            capture_output=True, text=True
        )
        duration = float(result.stdout.strip())
        return int(duration)
    except Exception as e:
        print(f"Failed to get duration: {e}")
        return None

def download_video_(rtsp_url, output_file):
    """Download video via vlc."""
    #-analyzeduration 10000000 -probesize 10000000 \
    #TODO strnage bug need to ue "snap run vlc" to force usage of vlc 3.10.20, 3.10.21 fails rtsp link download
    vlc_command = f"snap run vlc -I dummy {rtsp_url} --sout '#file{{dst={output_file}}}' --run-time=300 --play-and-exit --rtsp-tcp --network-caching=50000 --rtsp-frame-buffer-size=1000000 -v"
    #vlc_command = f"snap run vlc -I dummy {rtsp_url} --sout '#file{{dst={output_file}}}' --run-time=300 --play-and-exit --rtsp-tcp --network-caching=50000 --rtsp-frame-buffer-size=1000000 -v"
    print(f"VLC CMD:{vlc_command}")
    return run_cmd(vlc_command, verbose=True)


def process_raw_video(input_file, output_file):
    """Process raw video and compress to H.264 encoded MP4."""
    # ffmpeg_command = f"ffmpeg -i {input_file} -c:v libx264 -crf 23 -preset fast -an -movflags +faststart {output_file}"
    # ffmpeg_command = f"ffmpeg -i {input_file} -c:v libx264 -crf 28 -preset fast -an -movflags +faststart {output_file}"
    # ffmpeg_command = f"ffmpeg -i {input_file} -c:v libx264 -crf 28 -preset fast -an -movflags +faststart -profile:v baseline -level 3.1 {output_file}"
    ffmpeg_command = f"ffmpeg -hide_banner -i {input_file} -c:v libx264 -crf 28 -preset ultrafast -an -vf \"scale=1280:1280\" -r 30 {output_file}"

    print(f"FFmpeg CMD: {ffmpeg_command}")
    return run_cmd(ffmpeg_command, verbose=True)


def download_video(rtsp_url, output_file):
    output_file.unlink(missing_ok=True)
    """Download video via ffmpeg."""
    #-analyzeduration 10000000 -probesize 10000000 \
    ffmpeg_command = [
        "ffmpeg",
        "-hide_banner",
        "-rtsp_transport", "tcp",
        "-rtbufsize", "100M",
        "-i", rtsp_url,
        "-an",
        "-c:v", "copy",
        "-f", "mp4",
        output_file.as_posix()
    ]
    ffmpeg_command = " ".join(ffmpeg_command).strip()
    print(f"FFMPEG CMD:{ffmpeg_command}")
    return run_cmd(ffmpeg_command, verbose=True)


def check_file_range_exist(file_start, clips_range):
    clips_range = sorted(clips_range, key=lambda x: x[0])
    for start, end in clips_range:
        if start <= file_start <= end:
            return True
    return False


def get_clips_range(out_dir):
    range = []
    for file in out_dir.glob("*.mp4"):
        split = file.name.split('_')
        date_start_str = split[0].replace(".mp4", "")
        dt_start = parse_datetime(date_start_str)
        date_end_str = split[1].replace(".mp4", "")
        dt_end = parse_datetime(date_end_str)
        range.append([dt_start, dt_end])
    return range


def main(ip, is_fisheye, port=0):
    # ssh_tunnel_script = f"{SOURCE_PATH}open_ssh_tunnel_single.sh {ip} {port}"
    # print("Starting SSH tunnels...")
    # print(ssh_tunnel_script)
    # subprocess.run(ssh_tunnel_script, shell=True, check=True)

    now = datetime.now()
    earliest_recording = (now - timedelta(days=2, hours=0, minutes=0)).strftime('%Y-%m-%dT%H:%M:%SZ')
    latest_recording = now.strftime('%Y-%m-%dT%H:%M:%SZ')
    clips, _ = generate_perfect_5min_ranges(earliest_recording, latest_recording)
    print(f"Found {len(clips)} recordings. First clip: [{clips[0]}] Last clip: [{clips[-1]}]")

    for i in range(len(clips)):
        clock = f"{clips[i][0]}-{clips[i][1]}"
        rtsp_url = f"rtsp://{USERNAME}:{PASSWORD}@localhost:{port}/recording/{clock.replace('T','')}/OverlappedID=0/backup.smp"
        #recording/20250305000000-20250305000500/OverlappedID=0/backup.smp
        filename = f"{clock}.mp4".replace("-", '_')
        out_dir = create_output_directory(filename, ip)
        #out_dir = Path("/home/fo18103/Downloads")
        output_file = out_dir / filename

        file_start = datetime.strptime(output_file.name.split('_')[0], "%Y%m%dT%H%M%S")

        clips_range = get_clips_range(out_dir)
        if check_file_range_exist(file_start, clips_range):
            # print(f"File {output_file} already exists. Skipping download.")
            continue

        for attempt in range(1, MAX_DOWNLOAD_RETRIES + 1):
            print(f"Attempt {attempt} to download {filename}")
            p_status = download_video(rtsp_url, output_file)
            # if is_fisheye:
            #     filename = f"{clock}.mp4".replace("-", '_')
            #     output_file = out_dir / filename
            #     p_status = download_video(rtsp_url, output_file)
            #     if p_status == 0:
            #         filename_p = f"{clock}.mp4".replace("-", '_')
            #         output_file_p = out_dir / filename_p
            #         # p_status = process_raw_video(output_file, output_file_p)
            #         # if p_status == 0:
            #         #     output_file.unlink(missing_ok=True)
            #         #     output_file = output_file_p
            # else:
            #     p_status = download_video(rtsp_url, output_file)
            print(f"Download status: {p_status}")

            if output_file.exists():
                duration = get_video_duration(output_file)
                if duration is None: #file does not exist dont waste time trying to re-download
                    output_file.unlink()  # Remove bad file
                    break

                print(f"File duration: {duration}")
            #     if is_fisheye:
            #         exp_dur = EXPECTED_DURATION_FISH
            #     else:
            #         exp_dur = EXPECTED_DURATION_LANDSCAPE
            #
            #     if duration >= exp_dur:
            #         print(f"File {filename} downloaded successfully with correct duration.")
            #         break
            #     else:
            #         print(f"Duration mismatch: Expected {exp_dur}, got {duration}")
            #         output_file.unlink()  # Remove bad file
            # else:
            #     print("File download failed.")

            # if attempt == MAX_DOWNLOAD_RETRIES:
            #     print(f"Failed to download {filename} with correct duration after {MAX_DOWNLOAD_RETRIES} attempts. Skipping.")

if __name__ == "__main__":
    #main("10.70.66.47", 1, port=5582)
    # main("10.70.66.40", 1, port=5575)
    #main("10.70.66.22", 0, 5560)
    #main("10.70.66.25", 0, port=5563)
    if len(sys.argv) > 1:
        ip = sys.argv[1]
        is_fisheye = sys.argv[2]
        port = int(sys.argv[3])
        print("argument:", ip)
        main(ip, is_fisheye, port)
    else:
        print("No argument provided")
