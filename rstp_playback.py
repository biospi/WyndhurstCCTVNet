import json
import sys
import time
import requests
# import xmltodict
from requests.auth import HTTPDigestAuth
from datetime import datetime, timedelta
import subprocess
from pathlib import Path

from ocr_timestamp import repair_video_timestamp
from storage_info import parse_datetime
from utils import run_cmd, SOURCE_PATH
import configparser
config = configparser.ConfigParser()
config.read("config.cfg")

MAX_ONVIF_RETRY = 5
MAX_DOWNLOAD_RETRIES = 1
EXPECTED_DURATION_LANDSCAPE = 298
EXPECTED_DURATION_FISH = 298
USERNAME = "admin"
PASSWORD = config['AUTH']['password_hanwha']

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
    output_dir = Path(f'/mnt/storage/cctvnet/66.{tag}/{date_subfolder}/videos/')
    output_dir.mkdir(parents=True, exist_ok=True)
    #print(output_dir)
    return output_dir

def generate_perfect_5min_ranges_(start: str, end: str, footbath=False) -> list:
    """Generate 5-minute aligned recording ranges from start to end timestamps,
    discarding any time between 00:00 and 04:00."""

    # Convert input strings to datetime objects
    start_dt = datetime.strptime(start, "%Y-%m-%dT%H:%M:%SZ")
    end_dt = datetime.strptime(end, "%Y-%m-%dT%H:%M:%SZ")

    # Align start time to the nearest 5-minute mark
    aligned_start_dt = start_dt.replace(second=0, microsecond=0)
    if aligned_start_dt.minute % 5 != 0:
        aligned_start_dt += timedelta(minutes=(5 - aligned_start_dt.minute % 5))  # Move up to next 5-minute mark

    step = timedelta(minutes=5)
    ranges = []
    ranges_offset = []
    ranges_datetime = []
    current_dt = aligned_start_dt

    while current_dt < end_dt:
        next_dt = current_dt + step
        if next_dt > end_dt:
            break  # Stop if the next step exceeds the end time

        if footbath:
            ranges.append([current_dt.strftime('%Y%m%dT%H%M%S'), next_dt.strftime('%Y%m%dT%H%M%S')])
            ranges_offset.append(
                [(current_dt - timedelta(seconds=10)).strftime('%Y%m%dT%H%M%S'), next_dt.strftime('%Y%m%dT%H%M%S')])
            ranges_datetime.append([current_dt, next_dt])
        else:
            # Discard intervals between 00:00 and 04:00
            if not (0 <= current_dt.hour < 5):
                ranges.append([current_dt.strftime('%Y%m%dT%H%M%S'), next_dt.strftime('%Y%m%dT%H%M%S')])
                ranges_offset.append(
                    [(current_dt - timedelta(seconds=10)).strftime('%Y%m%dT%H%M%S'), next_dt.strftime('%Y%m%dT%H%M%S')])
                ranges_datetime.append([current_dt, next_dt])

        current_dt = next_dt  # Move to the next 5-minute interval

    # ranges = ranges[1:]
    # ranges_datetime = ranges_datetime[1:]

    return ranges, ranges_offset, ranges_datetime

def generate_perfect_5min_ranges(start: str, end: str) -> list:
    """Generate 5-minute aligned recording ranges from start to end timestamps."""

    # Convert input strings to datetime objects
    start_dt = datetime.strptime(start, "%Y-%m-%dT%H:%M:%SZ")
    end_dt = datetime.strptime(end, "%Y-%m-%dT%H:%M:%SZ")

    # Align start time to the nearest 5-minute mark
    aligned_start_dt = start_dt.replace(second=0, microsecond=0)
    if aligned_start_dt.minute % 5 != 0:
        aligned_start_dt += timedelta(minutes=(5 - aligned_start_dt.minute % 5))  # Move up to next 5-minute mark

    step = timedelta(minutes=5, seconds=0)
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


def get_fps(rtsp_url):
    """Extract FPS from RTSP stream using FFmpeg."""
    cmd = [
        "ffmpeg",
        "-rtsp_transport", "tcp",
        "-i", rtsp_url,
        "-hide_banner",
        "-select_streams", "v:0",
        "-show_entries", "stream=r_frame_rate",
        "-of", "csv=p=0"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    fps = result.stdout.strip()
    if fps and "/" in fps:  # Convert fractional FPS (e.g., 50/3) to float
        num, den = map(int, fps.split("/"))
        return str(num / den)
    return "16"  # Default fallback if detection fails


def download_video(rtsp_url, output_file, raw=False):
    output_file.unlink(missing_ok=True)
    """Download video via ffmpeg."""
    #-analyzeduration 10000000 -probesize 10000000 \
    if raw:
        ffmpeg_command = [
            "ffmpeg",
            "-hide_banner",
            "-rtsp_transport", "tcp",
            "-buffer_size", "10485760",
            "-rtbufsize", "100M",
            "-i", rtsp_url,
            "-an",
            "-c:v", "copy",
            "-f", "mp4",
            output_file.as_posix()
        ]
    else:
        # ffmpeg_command = [
        #     "ffmpeg",
        #     "-hide_banner",
        #     "-rtsp_transport", "tcp",
        #     "-buffer_size", "10485760",
        #     "-rtbufsize", "300M",
        #     "-i", rtsp_url,
        #     "-an",
        #     "-c:v", "libx264",
        #     "-crf", "28",
        #     "-preset", "veryfast",
        #     "-vsync", "0",  # Preserves original timing
        #     "-f", "mp4",
        #     output_file.as_posix()
        # ]
        ffmpeg_command = [
            "ffmpeg",
            "-hide_banner",
            "-rtsp_transport", "tcp",
            "-buffer_size", "10485760",
            "-i", rtsp_url,
            "-an",
            "-c:v", "libx264",
            "-crf", "28",
            "-preset", "veryfast",
            "-vsync", "0",
            "-f", "mp4",
            output_file.as_posix()
        ]

    ffmpeg_command = " ".join(ffmpeg_command).strip()
    print(f"FFMPEG CMD:{ffmpeg_command}")
    start_time = time.time()
    res = run_cmd(ffmpeg_command, verbose=True)
    end_time = time.time()
    duration_seconds = end_time - start_time  # Compute duration
    duration_minutes = duration_seconds / 60  # Convert to minutes
    print(f"Download completed in {duration_minutes:.2f} minutes ({duration_seconds:.2f} seconds). {rtsp_url}")
    return res


def find_missing_ranges(clips_range, min_gap=timedelta(minutes=5), max_gap=timedelta(minutes=5, seconds=6)):
    missing_ranges = []
    missing_ranges_str = []

    for i in range(len(clips_range) - 1):
        end = clips_range[i][1]
        next_start = clips_range[i + 1][0]

        # Ensure the missing range is at least `min_gap` long
        if next_start > end + min_gap:
            missing_start = end + timedelta(seconds=1)
            missing_end = next_start - timedelta(seconds=1)

            # If the gap is larger than max_gap, split it into 5-minute chunks
            while missing_start + max_gap < missing_end:
                split_end = missing_start + min_gap  # Ensure 5 min chunk
                missing_ranges.append([missing_start, split_end])
                missing_ranges_str.append([
                    missing_start.strftime("%Y%m%dT%H%M%S"),
                    split_end.strftime("%Y%m%dT%H%M%S")
                ])
                missing_start = split_end + timedelta(seconds=1)

            # Add the last chunk if remaining time is between min_gap and max_gap
            if missing_start < missing_end:
                missing_ranges.append([missing_start, missing_end])
                missing_ranges_str.append([
                    missing_start.strftime("%Y%m%dT%H%M%S"),
                    missing_end.strftime("%Y%m%dT%H%M%S")
                ])

    return missing_ranges, missing_ranges_str

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
    range = sorted(range, key=lambda x: x[0])
    return range

def check_gaps(clips_range, port, ip):
    missing_ranges, missing_clips = find_missing_ranges(clips_range)
    if len(missing_ranges) > 0:
        print(f"Found {len(missing_ranges)} recordings missing ranges.")
    for j in range(len(missing_ranges)):
        clock = f"{missing_clips[j][0]}-{missing_clips[j][1]}"
        rtsp_url = f"rtsp://{USERNAME}:{PASSWORD}@localhost:{port}/recording/{clock.replace('T', '')}/OverlappedID=0/backup.smp"
        filename = f"{clock}.mp4".replace("-", '_')
        out_dir = create_output_directory(filename, ip)
        output_file = out_dir / filename
        for attempt in range(1, MAX_DOWNLOAD_RETRIES + 1):
            print(f"Attempt {attempt} to download {ip} {filename}")
            p_status = download_video(rtsp_url, output_file)
            print(f"Download status: {p_status} | {ip} {filename}")
            if p_status <= 0:
                break

def main(ip, is_fisheye, port=0):
    # ssh_tunnel_script = f"{SOURCE_PATH}open_ssh_tunnel_single.sh {ip} {port}"
    # print("Starting SSH tunnels...")
    # print(ssh_tunnel_script)
    # subprocess.run(ssh_tunnel_script, shell=True, check=True)

    now = datetime.now()
    earliest_recording = (now - timedelta(days=5, hours=now.hour, minutes=now.minute, seconds=now.second)).strftime('%Y-%m-%dT%H:%M:%SZ')
    latest_recording = now.strftime('%Y-%m-%dT%H:%M:%SZ')
    clips, clips_offset, _ = generate_perfect_5min_ranges_(earliest_recording, latest_recording)
    print(f"Found {len(clips)} recordings. First clip: [{clips[0]}] Last clip: [{clips[-1]}]")
    if ip in ["10.70.66.31", "10.70.66.30", "10.70.66.29", "10.70.66.28"]:
        print(f"Motion detection enabled. {ip}.")
        clips, clips_offset, _ = generate_perfect_5min_ranges_(earliest_recording, latest_recording, footbath=True)

    # clock = f"{clips[0][0]}-{clips[0][1]}"
    # filename = f"{clock}.mp4".replace("-", '_')
    # out_dir = create_output_directory(filename, ip)
    # clips_range = get_clips_range(out_dir)
    # check_gaps(clips_range, port, ip)
    out_dir = None
    i = 0
    while i < len(clips):
        clock = f"{clips[i][0]}-{clips[i][1]}"
        clock_offset = f"{clips_offset[i][0]}-{clips_offset[i][1]}"
        i += 1
        #clock = "20250328T175400-20250328T175500"
        rtsp_url = f"rtsp://{USERNAME}:{PASSWORD}@localhost:{port}/recording/{clock_offset.replace('T','')}/OverlappedID=0/backup.smp"
        #recording/20250305000000-20250305000500/OverlappedID=0/backup.smp
        filename = f"{clock}.mp4".replace("-", '_')
        out_dir = create_output_directory(filename, ip)
        #out_dir = Path("/home/fo18103/Downloads")
        output_file = out_dir / filename

        # file_start = datetime.strptime(output_file.name.split('_')[0], "%Y%m%dT%H%M%S")
        # clips_range = get_clips_range(out_dir)

        if output_file.exists():
            print(f"File {output_file} already exists. Skipping download.")
            continue
        # if check_file_range_exist(file_start, clips_range):
        #     # print(f"File {output_file} already exists. Skipping download.")
        #     continue

        for attempt in range(1, MAX_DOWNLOAD_RETRIES + 1):
            print(f"Attempt {attempt} to download {ip} {filename}")
            p_status = download_video(rtsp_url, output_file)
            if p_status < 0:
                print(f"Data does not exist. Skipping download.")
                break
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
                    print("Duration is not valid")
                    #output_file.unlink()  # Remove bad file
                    continue

                print(f"File duration: {duration}")
                #repair timestamp:
                repair_video_timestamp(output_file)
                #skip duration check for camera with motion detection
                if ip in ["10.70.66.31", "10.70.66.30", "10.70.66.29", "10.70.66.28"]:
                    print(f"Motion detection enabled. Skipping duration check for {ip}.")
                    continue

                if is_fisheye:
                    exp_dur = EXPECTED_DURATION_FISH
                else:
                    exp_dur = EXPECTED_DURATION_LANDSCAPE

                if duration >= exp_dur:
                    print(f"File {ip} {filename} downloaded successfully with correct duration.")
                    break
                else:
                    print(f"Duration mismatch {ip} {filename}: Expected {exp_dur}, got {duration}")
                    i+= 12 #move to the next hour
                    # if attempt != MAX_DOWNLOAD_RETRIES:
                    #     output_file.unlink()  # Remove bad file
            else:
                print(f"File {ip} {filename} download failed.")

            if attempt == MAX_DOWNLOAD_RETRIES:
                print(f"Failed to download {ip} {filename} with correct duration after {MAX_DOWNLOAD_RETRIES} attempts. Skipping.")
    if out_dir is not None:
        print("Quality check...")
        clips_range = get_clips_range(out_dir)
        check_gaps(clips_range, port, ip)

if __name__ == "__main__":
    #main("10.70.66.27", 0, port=5565)
    #main("10.70.66.44", 1, port=5579)
    #main("10.70.66.40", 1, port=5575)
    #main("10.70.66.22", 0, 5560)
    # main("10.70.66.48", 0, 5583)
    # main("10.70.66.28", 0, 5566)
    #main("10.70.66.24", 0, 5562)
    #main("10.70.66.50", 0, 5585)
    #main("10.70.66.28", 0, port=5566)
    #main("10.70.66.39", 1, port=5574)
    #main("10.70.66.16", 0, port=5554)
    if len(sys.argv) > 1:
        ip = sys.argv[1]
        is_fisheye = sys.argv[2]
        port = int(sys.argv[3])
        print("argument:", ip)
        main(ip, is_fisheye, port)
    else:
        print("No argument provided")
