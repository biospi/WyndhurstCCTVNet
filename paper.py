from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib as mpl

# Set Times New Roman font globally
plt.rcParams.update({
    "axes.titlesize": 14,
    "axes.labelsize": 12,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 10
})
from matplotlib import rcParams

rcParams['font.family'] = 'sans-serif'
rcParams['font.sans-serif'] = ['Times New Roman']


from storage_info import parse_datetime
from utils import is_float


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
    df["ip_id"] = df["ip"].str.split('.').str[1].astype(int)
    print(df)
    df = df.drop(["FilePath"], axis=1)

    # Create a figure
    # Create output directory
    output_dir = Path("plots")
    output_dir.mkdir(exist_ok=True)

    # 1. Boxplot: FileSizeGB by ip_id
    plt.figure(figsize=(16, 8))
    sns.boxplot(data=df, x="ip_id", y="FileSizeGB", palette="Set3")
    plt.title("Boxplot of File Sizes by CCTV IP")
    plt.xlabel("CCTV IP ID")
    plt.ylabel("File Size (GB)")
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.savefig(output_dir / "boxplot_filesize_by_ip.jpg", dpi=300, format='jpeg')
    plt.clf()

    # 2. Violin Plot
    plt.figure(figsize=(16, 8))
    sns.violinplot(data=df, x="ip_id", y="FileSizeGB", palette="Set2")
    plt.title("Violin Plot of File Sizes by CCTV IP")
    plt.xlabel("CCTV IP ID")
    plt.ylabel("File Size (GB)")
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.savefig(output_dir / "violinplot_filesize_by_ip.jpg", dpi=300, format='jpeg')
    plt.clf()

    # 3. Daily total video volume (Time Series)
    df["date_only"] = df["s_dates"].dt.date
    daily_volume = df.groupby("date_only")["FileSizeGB"].sum().reset_index()
    plt.figure(figsize=(14, 6))
    sns.lineplot(data=daily_volume, x="date_only", y="FileSizeGB", marker="o")
    plt.title("Daily Total Video Volume")
    plt.xlabel("Date")
    plt.ylabel("Total File Size (GB)")
    plt.tight_layout()
    plt.savefig(output_dir / "timeseries_daily_volume.jpg", dpi=300, format='jpeg')
    plt.clf()

    # 4. Histogram of video durations
    plt.figure(figsize=(10, 6))
    plt.hist(df["duration"], bins=50, color="steelblue", edgecolor="black")
    plt.title("Histogram of Video Durations")
    plt.xlabel("Duration (seconds)")
    plt.ylabel("Number of Videos")
    plt.tight_layout()
    plt.savefig(output_dir / "histogram_video_duration.jpg", dpi=300, format='jpeg')
    plt.clf()

    # 5. Barplot of average file size per IP
    avg_size = df.groupby("ip_id")["FileSizeGB"].mean().reset_index()
    plt.figure(figsize=(16, 8))
    sns.barplot(data=avg_size, x="ip_id", y="FileSizeGB", palette="coolwarm")
    plt.title("Average File Size per CCTV IP")
    plt.xlabel("CCTV IP ID")
    plt.ylabel("Average File Size (GB)")
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.savefig(output_dir / "barplot_avg_filesize_by_ip.jpg", dpi=300, format='jpeg')
    plt.clf()

    # 6. Scatter plot: Duration vs File Size
    plt.figure(figsize=(10, 6))
    sns.scatterplot(data=df, x="duration", y="FileSizeGB", hue="ip_id", legend=False, palette="hsv")
    plt.title("Scatter Plot: Duration vs File Size")
    plt.xlabel("Duration (seconds)")
    plt.ylabel("File Size (GB)")
    plt.tight_layout()
    plt.savefig(output_dir / "scatter_duration_vs_filesize.jpg", dpi=300, format='jpeg')
    plt.clf()

    # 7. Heatmap: Daily volume by IP
    heat_df = df.pivot_table(index="date_only", columns="ip_id", values="FileSizeGB", aggfunc="sum").fillna(0)
    plt.figure(figsize=(18, 10))
    sns.heatmap(heat_df, cmap="viridis", cbar_kws={"label": "Total GB"})
    plt.title("Heatmap of Daily File Size by CCTV IP")
    plt.xlabel("CCTV IP ID")
    plt.ylabel("Date")
    plt.tight_layout()
    plt.savefig(output_dir / "heatmap_daily_volume_by_ip.jpg", dpi=300, format='jpeg')
    plt.clf()



if __name__ == "__main__":
    main()
