from pathlib import Path
import pandas as pd
import shutil
import os
hostname = os.uname().nodename

from storage_info import parse_datetime


def get_disk_space(path):
    """Return free space, total space, and used percentage for a given mount path"""
    total, used, free = shutil.disk_usage(path)
    free_gb = free / (1024 ** 3)
    total_gb = total / (1024 ** 3)
    used_pct = (used / total) * 100
    return free_gb, total_gb, used_pct


def process_videos(input_dir):
    mp4_files = list(input_dir.rglob("*.mp4"))
    print(f"{hostname.upper()} [{input_dir}] Found {len(mp4_files)} video files.")

    if not mp4_files:
        return

    df = pd.DataFrame(mp4_files, columns=['FilePath'])
    df['FileSizeBytes'] = df['FilePath'].apply(lambda x: x.stat().st_size)
    df['FileSizeGB'] = df['FileSizeBytes'] / (1024 ** 3)

    df["dates"] = [x.stem for x in mp4_files]
    df["s_dates"] = [parse_datetime(x.stem.split('_')[0]) for x in mp4_files]
    df["f_dates"] = [parse_datetime(x.stem.split('_')[1]) for x in mp4_files]
    df["duration"] = (df["f_dates"] - df["s_dates"]).dt.total_seconds()
    df["ip"] = [x.parent.parent.parent.name if 'videos' in str(x) else x.parent.parent.name for x in mp4_files]
    df = df.sort_values(by=["s_dates", "f_dates"])

    # Save metadata per input_dir name
    label = input_dir.parent.name
    df.to_csv(f"metadata_{label}.csv", index=False)
    return len(mp4_files)


def main():
    paths = [Path("/mnt/storage/cctvnet/"), Path("/mnt/usb_storage/cctvnet/")]
    for p in paths:
        if not p.exists():
            print(f"{p} does not exist or is not mounted.")
            continue
        root_mount = p.parent
        free_gb, total_gb, used_pct = get_disk_space(root_mount)
        print(f"{hostname.upper()} [{root_mount}] Free space: {free_gb:.2f} GB / {total_gb:.2f} GB ({used_pct:.1f}% used)")
        file_count = process_videos(p)
        df = pd.DataFrame([[hostname, free_gb, total_gb, used_pct, file_count, root_mount.name]],
                          columns=["hostname", "free_gb", "total_gb", "used_pct", "file_count", "root_mount"])
        print(df)


if __name__ == "__main__":
    main()
