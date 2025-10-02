import time
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import subprocess
from datetime import datetime, timedelta

from masks import MASKS
from utils import run_cmd, SOURCE_PATH
import configparser
config = configparser.ConfigParser()
config.read("config.cfg")
USERNAME = "admin"
PASSWORD = config['AUTH']['password_hanwha']

# import seaborn as sns
# import matplotlib as mpl
#
# # Set Times New Roman font globally
# plt.rcParams.update({
#     "axes.titlesize": 14,
#     "axes.labelsize": 12,
#     "xtick.labelsize": 10,
#     "ytick.labelsize": 10,
#     "legend.fontsize": 10
# })
# from matplotlib import rcParams
#
# rcParams['font.family'] = 'sans-serif'
# rcParams['font.sans-serif'] = ['Times New Roman']
#
#
# from storage_info import parse_datetime
# from utils import is_float
#
#
# def basic_visu():
#     mp4_files = list(Path("/mnt/storage/cctvnet/").rglob("*.mp4"))
#     print(f"Found {len(mp4_files)} files.")
#     df = pd.DataFrame(mp4_files, columns=['FilePath'])
#     df['FileSizeBytes'] = df['FilePath'].apply(lambda x: x.stat().st_size)
#     df['FileSizeGB'] = df['FileSizeBytes'] / (1024 ** 3)
#
#     df["dates"] = [x.stem for x in mp4_files]
#     df["s_dates"] = [parse_datetime(x.stem.split('_')[0]) for x in mp4_files]
#     df["f_dates"] = [parse_datetime(x.stem.split('_')[1]) for x in mp4_files]
#
#     df["duration"] = (df["f_dates"] - df["s_dates"]).dt.total_seconds()
#     df.to_csv("metadata.csv", index=False)
#     df["ip"] = [x.parent.parent.parent.name if 'videos' in str(x) else x.parent.parent.name for x in mp4_files]
#     df = df.sort_values(by=["s_dates", "f_dates"])
#     df["ip_id"] = df["ip"].str.split('.').str[1].astype(int)
#     print(df)
#     df = df.drop(["FilePath"], axis=1)
#
#     # Create a figure
#     # Create output directory
#     output_dir = Path("plots")
#     output_dir.mkdir(exist_ok=True)
#
#     # 1. Boxplot: FileSizeGB by ip_id
#     plt.figure(figsize=(16, 8))
#     sns.boxplot(data=df, x="ip_id", y="FileSizeGB", palette="Set3")
#     plt.title("Boxplot of File Sizes by CCTV IP")
#     plt.xlabel("CCTV IP ID")
#     plt.ylabel("File Size (GB)")
#     plt.xticks(rotation=90)
#     plt.tight_layout()
#     plt.savefig(output_dir / "boxplot_filesize_by_ip.jpg", dpi=300, format='jpeg')
#     plt.clf()
#
#     # 2. Violin Plot
#     plt.figure(figsize=(16, 8))
#     sns.violinplot(data=df, x="ip_id", y="FileSizeGB", palette="Set2")
#     plt.title("Violin Plot of File Sizes by CCTV IP")
#     plt.xlabel("CCTV IP ID")
#     plt.ylabel("File Size (GB)")
#     plt.xticks(rotation=90)
#     plt.tight_layout()
#     plt.savefig(output_dir / "violinplot_filesize_by_ip.jpg", dpi=300, format='jpeg')
#     plt.clf()
#
#     # 3. Daily total video volume (Time Series)
#     df["date_only"] = df["s_dates"].dt.date
#     daily_volume = df.groupby("date_only")["FileSizeGB"].sum().reset_index()
#     plt.figure(figsize=(14, 6))
#     sns.lineplot(data=daily_volume, x="date_only", y="FileSizeGB", marker="o")
#     plt.title("Daily Total Video Volume")
#     plt.xlabel("Date")
#     plt.ylabel("Total File Size (GB)")
#     plt.tight_layout()
#     plt.savefig(output_dir / "timeseries_daily_volume.jpg", dpi=300, format='jpeg')
#     plt.clf()
#
#     # 4. Histogram of video durations
#     plt.figure(figsize=(10, 6))
#     plt.hist(df["duration"], bins=50, color="steelblue", edgecolor="black")
#     plt.title("Histogram of Video Durations")
#     plt.xlabel("Duration (seconds)")
#     plt.ylabel("Number of Videos")
#     plt.tight_layout()
#     plt.savefig(output_dir / "histogram_video_duration.jpg", dpi=300, format='jpeg')
#     plt.clf()
#
#     # 5. Barplot of average file size per IP
#     avg_size = df.groupby("ip_id")["FileSizeGB"].mean().reset_index()
#     plt.figure(figsize=(16, 8))
#     sns.barplot(data=avg_size, x="ip_id", y="FileSizeGB", palette="coolwarm")
#     plt.title("Average File Size per CCTV IP")
#     plt.xlabel("CCTV IP ID")
#     plt.ylabel("Average File Size (GB)")
#     plt.xticks(rotation=90)
#     plt.tight_layout()
#     plt.savefig(output_dir / "barplot_avg_filesize_by_ip.jpg", dpi=300, format='jpeg')
#     plt.clf()
#
#     # 6. Scatter plot: Duration vs File Size
#     plt.figure(figsize=(10, 6))
#     sns.scatterplot(data=df, x="duration", y="FileSizeGB", hue="ip_id", legend=False, palette="hsv")
#     plt.title("Scatter Plot: Duration vs File Size")
#     plt.xlabel("Duration (seconds)")
#     plt.ylabel("File Size (GB)")
#     plt.tight_layout()
#     plt.savefig(output_dir / "scatter_duration_vs_filesize.jpg", dpi=300, format='jpeg')
#     plt.clf()
#
#     # 7. Heatmap: Daily volume by IP
#     heat_df = df.pivot_table(index="date_only", columns="ip_id", values="FileSizeGB", aggfunc="sum").fillna(0)
#     plt.figure(figsize=(18, 10))
#     sns.heatmap(heat_df, cmap="viridis", cbar_kws={"label": "Total GB"})
#     plt.title("Heatmap of Daily File Size by CCTV IP")
#     plt.xlabel("CCTV IP ID")
#     plt.ylabel("Date")
#     plt.tight_layout()
#     plt.savefig(output_dir / "heatmap_daily_volume_by_ip.jpg", dpi=300, format='jpeg')
#     plt.clf()

def create_output_directory(output_file: str, ip_tag: str, sub_dir: str):
    """
    Creates an output directory based on the first timestamp of the output file.

    :param output_file: The path to the output file.
    :return: The path to the created directory.
    """
    timestamp_str = output_file.split('_')[0]
    timestamp = datetime.strptime(timestamp_str, '%Y%m%dT%H%M%S')
    date_subfolder = timestamp.strftime('%Y%b%d')
    tag = ip_tag.split('.')[-1]
    output_dir = Path(f'/mnt/storage/paper/crf/{sub_dir}/cctvnet/66.{tag}/{date_subfolder}/videos/')
    output_dir.mkdir(parents=True, exist_ok=True)
    #print(output_dir)
    return output_dir


def run_cmd(cmd, i=0, tot=0, verbose=True):
    if verbose:
        print(cmd)
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, text=True)
    (output, err) = p.communicate()
    p_status = p.wait()
    print(err)
    if err is not None and "does not contain any stream" in err:
        return -1
    return p_status


def download_video(rtsp_url, output_file, crf = 28, raw=False, metadata_str=None):
    output_file.unlink(missing_ok=True)
    """Download video via ffmpeg."""
    base_cmd = [
        "ffmpeg",
        "-hide_banner",
        "-rtsp_transport", "tcp",
        "-buffer_size", "10485760",
    ]

    # Add common options for both modes
    if raw:
        ffmpeg_command = base_cmd + [
            "-rtbufsize", "100M",
            "-i", rtsp_url,
            "-an",
            "-c:v", "copy",
        ]
    else:
        ffmpeg_command = base_cmd + [
            "-i", rtsp_url,
            "-an",
            "-c:v", "libx264",
            "-crf", str(crf),
            "-preset", "veryfast",
            "-vsync", "0",
        ]

    # Optional metadata
    if metadata_str:
        ffmpeg_command += ["-metadata", f"comment={metadata_str}"]

    ffmpeg_command += ["-f", "mp4", output_file.as_posix()]

    ffmpeg_command = " ".join(ffmpeg_command).strip()
    print(f"FFMPEG CMD:{ffmpeg_command}")
    start_time = time.time()
    res = run_cmd(ffmpeg_command, verbose=True)
    end_time = time.time()
    duration_seconds = end_time - start_time  # Compute duration
    duration_minutes = duration_seconds / 60  # Convert to minutes
    print(f"Download completed in {duration_minutes:.2f} minutes ({duration_seconds:.2f} seconds). {rtsp_url}")
    return res

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
            if (11 <= current_dt.hour < 12):
                ranges.append([current_dt.strftime('%Y%m%dT%H%M%S'), next_dt.strftime('%Y%m%dT%H%M%S')])
                ranges_offset.append(
                    [(current_dt - timedelta(seconds=0)).strftime('%Y%m%dT%H%M%S'), next_dt.strftime('%Y%m%dT%H%M%S')])
                ranges_datetime.append([current_dt, next_dt])
        current_dt = next_dt  # Move to the next 5-minute interval
    return ranges, ranges_offset, ranges_datetime


def create_sample(ip, port=0, mask=None):
    ssh_tunnel_script = f"{SOURCE_PATH}/open_ssh_tunnel_single.sh {ip} {port}"
    print("Starting SSH tunnels...")
    print(ssh_tunnel_script)
    subprocess.run(ssh_tunnel_script, shell=True, check=True)

    now = datetime.now()
    start = (now - timedelta(days=1, hours=now.hour, minutes=now.minute, seconds=now.second))
    earliest_recording = start.strftime('%Y-%m-%dT%H:%M:%SZ')
    latest_recording = (start + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%SZ')
    clips, clips_offset, _ = generate_perfect_5min_ranges_(earliest_recording, latest_recording)
    print(f"Found {len(clips)} recordings. First clip: [{clips[0]}] Last clip: [{clips[-1]}]")

    i = 0
    while i < len(clips):
        clock = f"{clips[i][0]}-{clips[i][1]}"
        i += 1
        rtsp_url = f"rtsp://{USERNAME}:{PASSWORD}@localhost:{port}/recording/{clock.replace('T','')}/OverlappedID=0/backup.smp"
        #recording/20250305000000-20250305000500/OverlappedID=0/backup.smp
        filename = f"{clock}.mp4".replace("-", '_')

        out_dir_raw = create_output_directory(filename, ip, "raw")
        output_file_raw = out_dir_raw / filename
        if output_file_raw.exists():
            print(f"File {output_file_raw} already exists. Skipping download.")
            continue
        download_video(rtsp_url, output_file_raw, raw=True)

        for crf in [28, 36, 50]:
            out_dir_transcode = create_output_directory(filename, ip, f"transcode_{crf}")
            output_file_transcode = out_dir_transcode / filename
            if output_file_transcode.exists():
                print(f"File {output_file_transcode} already exists. Skipping download.")
                continue
            download_video(rtsp_url, output_file_transcode, crf=crf, raw=False, metadata_str=mask)


if __name__ == "__main__":
    ip = "10.70.66.44"
    mask = MASKS[ip.split('.')[-1]]
    print(mask)
    create_sample(ip, port=5595, mask=mask)