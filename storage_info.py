import time
from pathlib import Path
import configparser
import pandas as pd
from datetime import datetime
import seaborn as sns
import subprocess
import matplotlib.pyplot as plt
import matplotlib
from matplotlib.patches import Patch
import calplot
import numpy as np


matplotlib.use("Agg")  # Use a non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from utils import is_float, MAP

tab10 = plt.get_cmap("tab10")
colors = [tab10(i) for i in range(tab10.N)]

location_color_map = {
    "Milking": colors[0],
    "Race Foot Bath": colors[1],
    "Quarantine": colors[2],
    "Transition Pen": colors[3],
    "Back Barn Cubicle": colors[4],
    "Back Barn Feed Face": colors[5]
}

with open("hikvision.txt") as f:
    HIKVISION = [int(line.split()[0].rsplit('.', 1)[-1]) for line in f]

with open("hanwha.txt") as f:
    HANWHA = [int(line.split()[0].rsplit('.', 1)[-1]) for line in f]


LOCAL_DIRS = [
    Path("/mnt/usb_storage/cctvnet"),
    Path("/mnt/storage/cctvnet"),
]

REMOTE_USER = "fo18103"
REMOTE_HOST = "IT107338.users.bris.ac.uk"


def parse_datetime(date_str):
    for fmt in ("%Y%m%dT%H%M%S", "%Y%m%d%H%M%S"):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            pass
    return None

def list_local_mp4s(base_dir: Path):
    return list(base_dir.rglob("*.mp4"))

def list_remote_mp4s():
    """Get list of remote .mp4 files with size via ssh/rsync dry-run."""
    remote_dirs = " ".join(str(d) for d in LOCAL_DIRS)
    cmd = [
        "ssh", f"{REMOTE_USER}@{REMOTE_HOST}",
        f"find {remote_dirs} -type f -name '*.mp4' -printf '%p|%s\\n'"
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        lines = result.stdout.strip().splitlines()
        files = []
        for line in lines:
            path_str, size_str = line.split("|")
            files.append((path_str, int(size_str)))
        return files
    except subprocess.CalledProcessError as e:
        print("Failed to list remote files")
        print(e.stderr)
        return []

def build_dataframe(local_files, remote_files):
    rows = []

    # Local files
    for f in local_files:
        try:
            size = f.stat().st_size  / (1024 ** 3)
        except Exception as e:
            print(e)
            continue
        name = f.stem
        parts = name.split("_")
        if len(parts) < 2:
            continue
        s_time = parts[0]
        e_time = parts[1]
        if not (s_time and e_time):
            continue
        ip = f.parent.parent.parent.name if "videos" in str(f) else f.parent.parent.name
        rows.append({
            "source": "local",
            "ip": ip,
            "FilePath": str(f),
            "FileSizeGB": size,
            "s_dates": s_time,
            "f_dates": e_time
        })

    # Remote files
    for path_str, size in remote_files:
        name = Path(path_str).stem
        parts = name.split("_")
        if len(parts) < 2:
            continue
        s_time = parts[0]
        e_time = parts[1]
        if not (s_time and e_time):
            continue
        ip = Path(path_str).parent.parent.parent.name
        rows.append({
            "source": "remote",
            "ip": ip,
            "FilePath": path_str,
            "FileSizeGB": size / (1024 ** 3),
            "s_dates": s_time,
            "f_dates": e_time,
        })

    return pd.DataFrame(rows)


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
        return 0


def parse_datetime(date_str):
    for fmt in ("%Y%m%dT%H%M%S", "%Y%m%d%H%M%S"):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            pass
    raise ValueError(f"Time data '{date_str}' does not match expected formats.")


def get_ffmpeg_durations(videos):
    durations = []
    for vid in videos:
        duration = get_video_duration(vid)
        durations.append(duration)
    return durations

#
# def main():
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
#     #df["duration_ffmpeg"] = get_ffmpeg_durations(df["FilePath"])
#     df.to_csv("metadata.csv", index=False)
#     df["ip"] = [x.parent.parent.parent.name if 'videos' in str(x) else x.parent.parent.name for x in mp4_files]
#     df = df.sort_values(by=["s_dates", "f_dates"])
#     #df.to_csv("metadata.csv", index=False)
#     dfs = [group for _, group in df.groupby('ip')]
#     data = []
#     for df in dfs:
#         if not is_float(str(df["ip"].values[0])):
#             print(f"skip {df['ip'].values[0]}")
#             continue
#         df = df.drop(columns=['FilePath'])
#         df["dates"] = df['s_dates'].dt.date
#         dfs_days = [group for _, group in df.groupby('dates')]
#         for df_day in dfs_days:
#             day_sum = df_day["FileSizeGB"].sum()
#             data.append({"ip": df_day["ip"].values[0], "storage": day_sum, "date": df_day["dates"].values[0]})
#     df_data = pd.DataFrame(data)
#     print(df_data)
#     df_data["ip_id"] = df_data["ip"].str.split('.').str[1].astype(int)
#     df_data = df_data[df_data["ip_id"].isin(HIKVISION + HANWHA)]
#     df_data['date'] = pd.to_datetime(df_data['date'])
#     #df_data = df_data[df_data['date'] <= '2025-03-29']
#     locations = []
#     for ip in df_data["ip_id"]:
#         loc = MAP[ip]['location']
#         locations.append(loc.title())
#     df_data['location'] = locations
#
#     df_data['brand'] = df_data['ip_id'].apply(lambda x: 'HIKVISION' if x in HIKVISION else 'HANWHA')
#     # df_data = df_data.sort_values(by=["ip_id", "brand"])
#     df_data = df_data.sort_values(by='location')
#     heatmap_data = df_data.pivot_table(index='ip', columns='date', values='storage')
#
#     #heatmap_data.loc["total"] = heatmap_data.sum()
#     plt.figure(figsize=(10, 16))
#     a = HIKVISION + HANWHA
#     ip_order = [f"66.{x}" for x in df_data['ip_id'].unique().tolist()]
#     heatmap_data.index = pd.Categorical(heatmap_data.index, categories=ip_order, ordered=True)
#     heatmap_data = heatmap_data.sort_index()
#
#     ax = sns.heatmap(heatmap_data, annot=True, cmap="viridis", fmt=".0f", cbar_kws={'label': 'Storage (GB)'})
#     ax.set_xticklabels(heatmap_data.columns.strftime('%d-%m-%Y'))
#     plt.title(f'Storage Usage Heatmap | HIKVISION ({len(HIKVISION)}) HANWHA ({len(HANWHA)})')
#     plt.xlabel('Date')
#
#     #ax.get_yticklabels()[-1].set_label("Total")
#     for label in ax.get_yticklabels():
#         ip_id = int(label.get_text().split('.')[1])
#         # if ip_id in HIKVISION:
#         #     label.set_color('blue')
#         # elif ip_id in HANWHA:
#         #     label.set_color('green')
#         location = df_data[df_data["ip_id"] == ip_id]["location"].values[0]
#         label.set_color(location_color_map.get(location, "black"))
#
#     plt.ylabel('IP')
#     plt.xticks(rotation=90)
#
#     legend_labels = df_data["location"].unique().tolist()
#     legend_colors = colors[0:len(legend_labels)]
#     legend_handles = [Patch(facecolor=color, edgecolor='black', label=label) for color, label in
#                       zip(legend_colors, legend_labels)]
#     ax.legend(handles=legend_handles, loc='upper right', ncol=len(legend_labels),
#                frameon=True)
#     legend_labels = ["Back Barn Cubicle (20)", "Milking (5)", "Race Foot bath (7)", "Transition Pen 4 (12)", "Back Barn Feed Face (14)"]
#     legend_colors = [colors[0], colors[1], colors[2], colors[3], colors[4]]
#     legend_handles = [Patch(facecolor=color, edgecolor='black', label=label) for color, label in
#                       zip(legend_colors, legend_labels)]
#     ax.legend(handles=legend_handles, loc='upper center', fontsize=10, frameon=False, ncol=len(legend_labels), bbox_to_anchor=(0.5, 1.05))
#     plt.tight_layout()
#
#     timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#     filename = f"storage_{timestamp}.png"
#     out_dir = Path("storage")
#     out_dir.mkdir(parents=True, exist_ok=True)
#     filepath = out_dir / filename
#     print(f"Writing {filepath}")
#     plt.savefig(filepath, bbox_inches='tight',  dpi=600)
#
#     filename = f"data_storage_{timestamp}.csv"
#     filepath = out_dir / filename
#     df_data.to_csv(filepath, index=False)
#
#     # Compute total storage per date
#     total_storage = heatmap_data.sum()
#
#     # Create a new DataFrame for the single-row heatmap
#     total_df = pd.DataFrame([total_storage], index=["Total"])
#
#     # Plot the single-row heatmap
#     plt.figure(figsize=(10, 3))
#     ax = sns.heatmap(total_df, annot=True, fmt=".0f", cmap="viridis", cbar_kws={'label': 'Total Storage (GB)'})
#     ax.set_xticklabels(total_df.columns.strftime('%d-%m-%Y'))
#     plt.title("Total Storage Usage Heatmap")
#     plt.xlabel("Date")
#     plt.ylabel("")
#     plt.tight_layout()
#     total_filename = f"0_storage_total.png"
#     total_filepath = out_dir / total_filename
#     print(f"Writing {total_filepath}")
#     plt.savefig(total_filepath, bbox_inches='tight', dpi=600)


def main(mp4_files=list(Path("/mnt/usb_storage/cctvnet/").rglob("*.mp4"))):
    # Get local files
    local_files = []
    for d in LOCAL_DIRS:
        local_files.extend(list_local_mp4s(d))

    # Get remote files
    remote_files = list_remote_mp4s()

    # Build dataframe
    df = build_dataframe(local_files, remote_files)

    print(f"Total videos found: {len(df)} "
          f"(local: {len(local_files)}, remote: {len(remote_files)})")

    print(df.head())
    out_dir = Path("/mnt/storage/frontend/")
    out_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv((out_dir / "all_videos.csv").as_posix(), index=False)

    if df is None:
        print(f"Found {len(mp4_files)} files.")
        df = pd.DataFrame(mp4_files, columns=['FilePath'])
        df['FileSizeBytes'] = df['FilePath'].apply(lambda x: x.stat().st_size)
        df['FileSizeGB'] = df['FileSizeBytes'] / (1024 ** 3)

        df["dates"] = [x.stem for x in mp4_files]
        df["s_dates"] = [parse_datetime(x.stem.split('_')[0]) for x in mp4_files]
        df["f_dates"] = [parse_datetime(x.stem.split('_')[1]) for x in mp4_files]

        df["duration"] = (df["f_dates"] - df["s_dates"]).dt.total_seconds()
        df.to_csv("metadata.csv", index=False)
        df["ip"] = [x.parent.parent.parent.name if 'videos' in str(x) else x.parent.parent.name for x in mp4_files]
    else:
        df['s_dates'] = df['s_dates'].apply(parse_datetime)
        df['f_dates'] = df['f_dates'].apply(parse_datetime)
        df["duration"] = (df["f_dates"] - df["s_dates"]).dt.total_seconds()

    df = df.sort_values(by=["s_dates", "f_dates"])
    dfs = [group for _, group in df.groupby('ip')]
    data = []
    for df in dfs:
        if not is_float(str(df["ip"].values[0])):
            print(f"skip {df['ip'].values[0]}")
            continue
        df = df.drop(columns=['FilePath'])
        df["dates"] = df['s_dates'].dt.date
        dfs_days = [group for _, group in df.groupby('dates')]
        for df_day in dfs_days:
            day_sum = df_day["FileSizeGB"].sum()
            data.append({"ip": df_day["ip"].values[0], "storage": day_sum, "date": df_day["dates"].values[0]})

    df_data = pd.DataFrame(data)
    print(df_data)
    df_data["ip_id"] = df_data["ip"].str.split('.').str[1].astype(int)
    df_data = df_data[df_data["ip_id"].isin(HIKVISION + HANWHA)]
    df_data['date'] = pd.to_datetime(df_data['date'])

    locations = [MAP[ip]['location'].title() for ip in df_data["ip_id"]]
    df_data['location'] = locations
    df_data['brand'] = df_data['ip_id'].apply(lambda x: 'HIKVISION' if x in HIKVISION else 'HANWHA')
    df_data = df_data.sort_values(by='location')

    # Transpose heatmap: Dates on Y-axis, IPs on X-axis
    heatmap_data = df_data.pivot_table(index='date', columns='ip', values='storage')

    plt.figure(figsize=(21, 25))  # Swap aspect ratio for landscape format
    ip_order = [f"66.{x}" for x in df_data['ip_id'].unique().tolist()]
    heatmap_data.columns = pd.Categorical(heatmap_data.columns, categories=ip_order, ordered=True)
    heatmap_data = heatmap_data.sort_index(axis=1)
    heatmap_data.index = pd.to_datetime(heatmap_data.index)
    ax = sns.heatmap(heatmap_data, annot=False, cmap="viridis", fmt=".0f", cbar_kws={'label': 'Storage (GB)'})
    # ax.yaxis.set_major_formatter(mdates.DateFormatter('%d-%m-%Y'))
    # #ax.set_yticklabels(heatmap_data.index.strftime('%d-%m-%Y'))
    ax.set_yticks(np.arange(len(heatmap_data.index)) + 0.5)  # center ticks on heatmap cells
    ax.set_yticklabels(heatmap_data.index.strftime('%d-%m-%Y'))
    plt.title(f'Storage Usage Heatmap | HIKVISION ({len(HIKVISION)}) HANWHA ({len(HANWHA)})')
    plt.ylabel('Date')
    plt.xlabel('IP')
    plt.xticks(rotation=90)

    #ax.get_yticklabels()[-1].set_label("Total")
    for label in ax.get_xticklabels():
        ip_id = int(label.get_text().split('.')[1])
        # if ip_id in HIKVISION:
        #     label.set_color('blue')
        # elif ip_id in HANWHA:
        #     label.set_color('green')
        location = df_data[df_data["ip_id"] == ip_id]["location"].values[0]
        label.set_color(location_color_map.get(location, "black"))

        legend_labels = df_data["location"].unique().tolist()
        legend_colors = colors[0:len(legend_labels)]
        legend_handles = [Patch(facecolor=color, edgecolor='black', label=label) for color, label in
                          zip(legend_colors, legend_labels)]
        ax.legend(handles=legend_handles, loc='upper right', ncol=len(legend_labels),
                   frameon=True)
        legend_labels = ["Milking (5)", "Race Foot bath (7)", "Quarantine (2)", "Transition Pen 4 (12)",
                         "Back Barn Cubicle (20)", "Back Barn Feed Face (14)"]
        legend_colors = [colors[0], colors[1], colors[2], colors[3], colors[4], colors[5]]
        legend_handles = [Patch(facecolor=color, edgecolor='black', label=label) for color, label in
                          zip(legend_colors, legend_labels)]
        ax.legend(handles=legend_handles, loc='upper center', fontsize=10, frameon=False, ncol=len(legend_labels), bbox_to_anchor=(0.5, 1.05))

    plt.tight_layout()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"storage_{timestamp}.png"
    out_dir = Path("/mnt/storage/frontend/")
    out_dir.mkdir(parents=True, exist_ok=True)
    filepath = out_dir / filename
    print(f"Writing {filepath}")
    plt.savefig(filepath, bbox_inches='tight', dpi=600)

    filename = f"storage.png"
    filepath = out_dir / filename
    print(f"Writing {filepath}")
    plt.savefig(filepath, bbox_inches='tight', dpi=600)

    # Compute total storage per date
    total_storage = heatmap_data.sum(axis=1)

    # Create a new DataFrame for the single-row heatmap
    total_df = pd.DataFrame([total_storage], index=["Total"])

    # Plot the single-row heatmap
    plt.figure(figsize=(40, 2))
    ax = sns.heatmap(total_df, annot=True, fmt=".0f", cmap="viridis", cbar_kws={'label': 'Total Storage (GB)'})

    # Set tick positions and labels to match your data
    xticks = list(range(len(total_df.columns)))  # 0 to 48
    xtick_labels = [col.strftime('%d-%m-%Y') for col in total_df.columns]

    ax.set_xticks(xticks)
    ax.set_xticklabels(xtick_labels, rotation=45, ha='right')

    plt.title("Total Storage Usage Heatmap")
    plt.xlabel("Date")
    plt.ylabel("")
    plt.tight_layout()

    total_filename = f"0_storage_total.png"
    total_filepath = out_dir / total_filename
    print(f"Writing {total_filepath}")
    plt.savefig(total_filepath, bbox_inches='tight', dpi=600)
    build_calendar(df)


def build_calendar(df):
    # Convert s_dates to datetime
    df["s_dates"] = pd.to_datetime(df["s_dates"], format="%Y%m%dT%H%M%S")

    # Aggregate by day, summing storage
    daily_storage = (
        df.groupby(df["s_dates"].dt.date)["FileSizeGB"]
        .sum()
        .rename_axis("date")
    )

    # Convert index to datetime index (calplot requires it)
    daily_storage.index = pd.to_datetime(daily_storage.index)

    # Plot with calplot
    calplot.calplot(
        daily_storage,
        suptitle="Daily Storage Usage (GB)",
        suptitle_kws={"x": 0.5, "y": 1.0}
    )

    # Save instead of plt.show()
    out_dir = Path("/mnt/storage/frontend/")
    out_dir.mkdir(parents=True, exist_ok=True)
    plt.savefig((out_dir / "daily_storage_calendar.png").as_posix(), dpi=300, bbox_inches="tight")
    plt.close()


if __name__ == "__main__":
    # # Get local files
    # local_files = []
    # for d in LOCAL_DIRS:
    #     local_files.extend(list_local_mp4s(d))
    #
    # # Get remote files
    # remote_files = list_remote_mp4s()
    #
    # # Build dataframe
    # df = build_dataframe(local_files, remote_files)
    #
    # print(f"Total videos found: {len(df)} "
    #       f"(local: {len(local_files)}, remote: {len(remote_files)})")
    #
    # print(df.head())
    # df.to_csv("all_videos.csv", index=False)


    # dir1 = list(Path("/mnt/usb_storage/cctvnet/").rglob("*.mp4"))
    # dir2 = list(Path("/mnt/storage/cctvnet/").rglob("*.mp4"))
    # mp4_files = dir1 + dir2
    # print(f"Found {len(mp4_files)} .mp4 files")
    #

    #build_calendar(df)

    main()