from pathlib import Path
import pandas as pd
import subprocess
import plotly.graph_objects as go
from storage_info import parse_datetime


def create_weekly_heatmap(df, ip_label="Unknown", output_dir="heatmaps"):
    df = df.copy()

    # Keep everything — even rows with missing dates or durations
    df["week_start"] = df["s_dates"].dt.to_period("W").apply(lambda r: r.start_time if pd.notna(r) else pd.NaT)
    df["day_name"] = df["s_dates"].dt.day_name()

    # Separate invalid rows (with no date info)
    missing_date_df = df[df["week_start"].isna()]
    valid_df = df[df["week_start"].notna()]

    # Define days of week in order
    week_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    # Create full week/day index
    all_weeks = pd.date_range(valid_df["week_start"].min(), valid_df["week_start"].max(), freq="W-MON")
    full_index = pd.MultiIndex.from_product([all_weeks, week_days], names=["week_start", "day_name"])

    # Create pivot table and reindex to include all combinations
    pivot = valid_df.pivot_table(
        index="week_start",
        columns="day_name",
        values="duration_actual",
        aggfunc="sum"
    )
    pivot = pivot.reindex(index=all_weeks, columns=week_days)  # Fill missing with NaN

    # Convert to hours for display
    heatmap_values = pivot.values / 3600
    y_labels = [week.strftime("%Y-%m-%d") for week in pivot.index]

    fig = go.Figure(data=go.Heatmap(
        z=heatmap_values,
        x=week_days,
        y=y_labels,
        colorscale="Viridis",
        colorbar=dict(title="Duration (hours)"),
        zmin=0,
        hovertemplate="Day: %{x}<br>Week of: %{y}<br>Duration: %{z:.2f}h<extra></extra>",
    ))

    fig.update_layout(
        title=f"Weekly Video Duration Heatmap - {ip_label}",
        xaxis_title="Day of Week",
        yaxis_title="Week Starting",
        yaxis=dict(autorange="reversed"),
    )

    # Save HTML heatmap
    output_path = Path(output_dir) / f"heatmap_{ip_label}.html"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(str(output_path))
    print(f"Saved heatmap to {output_path}")

    # Optionally: save missing rows for review
    if not missing_date_df.empty:
        missing_path = Path(output_dir) / f"missing_dates_{ip_label}.csv"
        missing_date_df.to_csv(missing_path, index=False)
        print(f"Saved rows with missing dates to {missing_path}")


def get_video_duration(file_path):
    """Get the actual duration of a video file using ffprobe."""
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error", "-show_entries",
                "format=duration", "-of",
                "default=noprint_wrappers=1:nokey=1", str(file_path)
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return float(result.stdout.strip())
    except Exception as e:
        print(f"Error reading duration for {file_path}: {e}")
        return None


def main():
    mp4_files = list(Path("/mnt/storage/cctvnet/").rglob("*.mp4"))
    print(f"Found {len(mp4_files)} files.")
    df = pd.DataFrame(mp4_files, columns=['FilePath'])
    df['FileSizeBytes'] = df['FilePath'].apply(lambda x: x.stat().st_size)
    df['FileSizeGB'] = df['FileSizeBytes'] / (1024 ** 3)

    df["dates"] = [x.stem for x in mp4_files]
    df["s_dates"] = [parse_datetime(x.stem.split('_')[0]) for x in mp4_files]
    df["f_dates"] = [parse_datetime(x.stem.split('_')[1]) for x in mp4_files]

    df["duration_expected"] = (df["f_dates"] - df["s_dates"]).dt.total_seconds()
    df["duration_actual"] = df["FilePath"].apply(get_video_duration)

    df["ip"] = [x.parent.parent.parent.name if 'videos' in str(x) else x.parent.parent.name for x in mp4_files]
    df = df.sort_values(by=["s_dates", "f_dates"])
    df.to_csv("cctv_storage_visu.csv", index=False)

    dfs = [group for ip, group in df.groupby('ip')]
    for df_group in dfs:
        ip = df_group['ip'].iloc[0]
        create_weekly_heatmap(df_group, ip_label=ip)


if __name__ == "__main__":
    main()
