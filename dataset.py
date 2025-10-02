from pathlib import Path
import pandas as pd
import matplotlib
import subprocess
import cv2
import numpy as np
from datetime import datetime
import os
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def save_before_after_frames(df, raw_root, trans_root, out_dir="output/frames"):
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    for idx, row in df.iterrows():
        filename = row['filename']
        raw_file = Path(raw_root).rglob(f"**/{filename}")
        trans_file = Path(trans_root).rglob(f"**/{filename}")

        try:
            raw_fp = next(raw_file)
            trans_fp = next(trans_file)

            # Temporary output frames
            raw_frame = out_path / f"raw_{idx}.jpg"
            trans_frame = out_path / f"trans_{idx}.jpg"

            # Extract first frame using ffmpeg
            subprocess.run([
                "ffmpeg", "-y", "-i", str(raw_fp), "-frames:v", "1", str(raw_frame)
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            subprocess.run([
                "ffmpeg", "-y", "-i", str(trans_fp), "-frames:v", "1", str(trans_frame)
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            # Read both frames
            img1 = cv2.imread(str(raw_frame))
            img2 = cv2.imread(str(trans_frame))

            if img1 is None or img2 is None:
                print(f"Failed to read frame from {filename}")
                continue

            # Resize to same height if needed
            h = min(img1.shape[0], img2.shape[0])
            img1 = cv2.resize(img1, (int(img1.shape[1] * h / img1.shape[0]), h))
            img2 = cv2.resize(img2, (int(img2.shape[1] * h / img2.shape[0]), h))

            # Concatenate side by side
            combined = np.hstack((img1, img2))
            out_file = out_path / f"before_after_{str(filename).split('.')[0]}_{idx:03d}.jpg"
            cv2.imwrite(str(out_file), combined)

        except StopIteration:
            print(f"File {filename} not found in one of the folders.")
            continue


def collect_file_sizes(raw_root, trans_root):
    raw_files = list(Path(raw_root).rglob("*.mp4"))
    trans_files = list(Path(trans_root).rglob("*.mp4"))

    raw_dict = {f.name: f.stat().st_size / (1024**2) for f in raw_files}  # size in MB
    trans_dict = {f.name: f.stat().st_size / (1024**2) for f in trans_files}

    records = []
    for fname in raw_dict:
        if fname in trans_dict:
            records.append({
                "filename": fname,
                "raw_size_mb": raw_dict[fname],
                "transcoded_size_mb": trans_dict[fname],
                "compression_ratio": trans_dict[fname] / raw_dict[fname] if raw_dict[fname] != 0 else None
            })

    return pd.DataFrame(records)

def plot_graphs(df):
    output_dir = Path(f"output_{datetime.now().strftime('%Y%m%d')}")
    output_dir.mkdir(exist_ok=True)

    # Bar chart
    df_sample = df.sample(100)
    #df_sample = df
    x = range(len(df_sample))
    plt.figure(figsize=(14, 6))
    plt.bar(x, df_sample['raw_size_mb'], label='Raw', alpha=0.7)
    plt.bar(x, df_sample['transcoded_size_mb'], label='Transcoded', alpha=0.7)
    plt.xticks(x, [str(x) for x in range(len(df_sample['filename']))], rotation=45, fontsize=6)
    plt.ylabel("Size (MB)")
    plt.title(f"Raw vs Transcoded File Sizes (n_file={len(df_sample)})")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_dir / "barplot_raw_vs_transcoded.jpg", dpi=300)
    plt.close()

    # Boxplot
    plt.figure(figsize=(6, 5))
    plt.boxplot([df['raw_size_mb'], df['transcoded_size_mb']], labels=["Raw", "Transcoded"])
    plt.ylabel("File Size (MB)")
    plt.title(f"Distribution of File Sizes (n_file={len(df_sample)})")
    plt.tight_layout()
    plt.savefig(output_dir / "boxplot_raw_vs_transcoded.jpg", dpi=300)
    plt.close()

    # Scatter plot with color-coded compression ratio
    plt.figure(figsize=(6, 5))
    scatter = plt.scatter(df['raw_size_mb'], df['transcoded_size_mb'],
                          c=df['compression_ratio'], cmap='viridis', alpha=0.8)
    plt.plot([df['raw_size_mb'].min(), df['raw_size_mb'].max()],
             [df['raw_size_mb'].min(), df['raw_size_mb'].max()],
             'r--', label='y = x')
    plt.xlabel("Raw Size (MB)")
    plt.ylabel("Transcoded Size (MB)")
    plt.title(f"Raw vs Transcoded File Sizes (n_file={len(df_sample)})")
    cbar = plt.colorbar(scatter)
    cbar.set_label("Compression Ratio (compression_ratio = transcoded_size / raw_size)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_dir / "scatter_raw_vs_transcoded.jpg", dpi=300)
    plt.close()

    # Histogram
    plt.figure(figsize=(8, 5))
    plt.hist(df['raw_size_mb'], bins=30, alpha=0.5, label='Raw')
    plt.hist(df['transcoded_size_mb'], bins=30, alpha=0.5, label='Transcoded')
    plt.xlabel("Size (MB)")
    plt.ylabel("Count")
    plt.title(f"Histogram of File Sizes (n_file={len(df_sample)})")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_dir / "histogram_file_sizes.jpg", dpi=300)
    plt.close()
    return output_dir

def main():
    raw_root = "/mnt/storage/paper/raw/cctvnet/"
    trans_root = "/mnt/storage/paper/transcode/cctvnet/"

    df = collect_file_sizes(raw_root=raw_root, trans_root=trans_root)
    print(df.describe())
    out_dir = plot_graphs(df)
    save_before_after_frames(df, raw_root, trans_root, out_dir=(out_dir / "frames").as_posix())

if __name__ == "__main__":
    main()
