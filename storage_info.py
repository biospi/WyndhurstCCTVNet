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


matplotlib.use("Agg")  # Use a non-interactive backend
import matplotlib.pyplot as plt

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


def main():
    mp4_files = list(Path("/mnt/storage/cctvnet/").rglob("*.mp4"))
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

    plt.figure(figsize=(18, 10))  # Swap aspect ratio for landscape format
    ip_order = [f"66.{x}" for x in df_data['ip_id'].unique().tolist()]
    heatmap_data.columns = pd.Categorical(heatmap_data.columns, categories=ip_order, ordered=True)
    heatmap_data = heatmap_data.sort_index(axis=1)

    ax = sns.heatmap(heatmap_data, annot=True, cmap="viridis", fmt=".0f", cbar_kws={'label': 'Storage (GB)'})
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
        ax.legend(handles=legend_handles, loc='upper center', fontsize=10, frameon=False, ncol=len(legend_labels), bbox_to_anchor=(0.5, 1.25))

    plt.tight_layout()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"storage_{timestamp}.png"
    out_dir = Path("storage")
    out_dir.mkdir(parents=True, exist_ok=True)
    filepath = out_dir / filename
    print(f"Writing {filepath}")
    plt.savefig(filepath, bbox_inches='tight', dpi=600)

    # Compute total storage per date
    total_storage = heatmap_data.sum(axis=1)

    # Create a new DataFrame for the single-row heatmap
    total_df = pd.DataFrame([total_storage], index=["Total"])

    # Plot the single-row heatmap
    # plt.figure(figsize=(10, 3))
    # ax = sns.heatmap(total_df, annot=True, fmt=".0f", cmap="viridis", cbar_kws={'label': 'Total Storage (GB)'})
    # ax.set_xticklabels(total_df.columns.strftime('%d-%m-%Y'))
    # plt.title("Total Storage Usage Heatmap")
    # plt.xlabel("Date")
    # plt.ylabel("")
    # plt.tight_layout()
    # total_filename = f"0_storage_total.png"
    # total_filepath = out_dir / total_filename
    # print(f"Writing {total_filepath}")
    # plt.savefig(total_filepath, bbox_inches='tight', dpi=600)

if __name__ == "__main__":
    main()