from pathlib import Path
import subprocess
import pandas as pd
from datetime import datetime
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib.patches import Patch
from utils import MAP, get_latest_file, get_first_file_after
import numpy as np
import cv2
import matplotlib.patches as patches


def extract_thumbnail(ip, video_path, hd_folder, sd_folder):
    hd_folder.mkdir(parents=True, exist_ok=True)
    sd_folder.mkdir(parents=True, exist_ok=True)

    #filename = f"{MAP[int(ip)]['location']}_{ip}.jpg"
    filename = f"{ip}.jpg"
    hd_path = hd_folder / filename
    sd_path = sd_folder / filename

    if hd_path.exists():
        hd_path.unlink()

    if sd_path.exists():
        sd_path.unlink()

    hd_command = [
        "ffmpeg",
        "-i", video_path,  # Input video
        "-ss", "00:00:05",  # Seek to 5 seconds
        "-vframes", "1",  # Extract only 1 frame
        "-q:v", "2",  # High quality
        str(hd_path)  # Output HD path
    ]

    sd_command = [
        "ffmpeg",
        "-i", video_path,  # Input video
        "-ss", "00:00:05",  # Seek to 5 seconds
        "-vframes", "1",  # Extract only 1 frame
        "-vf", "scale=iw/4:-1",  # Reduce width to 1/4, height auto-adjusted
        "-q:v", "2",  # High quality
        str(sd_path)  # Output SD path
    ]

    try:
        subprocess.run(hd_command, check=True)
        print(f"HD Thumbnail saved: {hd_path}")
        subprocess.run(sd_command, check=True)
        print(f"SD Thumbnail saved: {sd_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error extracting thumbnail for {video_path}: {e}")


def build_map(raw=False, diagram=False):
    image_dir = Path('/mnt/storage/thumbnails/hd')
    fig, ax = plt.subplots(figsize=(60, 5))
    ax.set_xlim(0, 36)
    ax.set_ylim(0, 15)
    ax.axis('off')

    # Preprocess top 2 visual rows (highest row values)
    all_rows = sorted({item[1]["position"][0] for item in MAP.items()}, reverse=True)
    top_rows = all_rows[:2]
    # Collect all thumbnails in top 2 rows
    all_top_thumbs = []
    for item in MAP.items():
        row, col, w, h, *_ = item[1]["position"]
        if row in top_rows:
            all_top_thumbs.append((col, row, w, h))

    # Sort left to right (by col), take first 12
    group1_boxes = sorted(all_top_thumbs, key=lambda x: x[0])[:12]
    group2_boxes = sorted(all_top_thumbs, key=lambda x: x[0])[:12]

    cpt_hanwha = 0
    cpt_hikvision = 0

    for idx, item in enumerate(MAP.items()):

        ip = item[1]["ip"]
        location = item[1]["location"]
        brand = item[1]["brand"]
        if "hikvision" in brand.lower():
            cpt_hikvision += 1
        if "hanwa" in brand.lower():
            cpt_hanwha += 1
        row, col, w, h , rot, offset_c, offset_r, c_id= item[1]["position"]
        img_extent = [col, col + w, row, row + h]
        img_path = image_dir / f"{ip}.jpg"

        try:
            img = mpimg.imread(img_path)
        except Exception as e:
            print(f"Error reading {img_path}: {e}")
            img = mpimg.imread("gray.jpg")

        tab10 = plt.get_cmap("tab10")
        colors = [tab10(i) for i in range(tab10.N)]

        color = colors[c_id]
        if not raw:
            if rot == 1:
                img = np.rot90(img)
                if diagram:
                    img_path = image_dir / "rot90.png"
                    img = mpimg.imread(img_path)

            if rot == -1:
                img = np.fliplr(img)
                img = np.flipud(img)
                if diagram:
                    img_path = image_dir / "flipud_lr.png"
                    img = mpimg.imread(img_path)

            if rot == -3:
                #img = np.fliplr(img)
                img = np.flipud(img)
                if diagram:
                    img_path = image_dir / "flipud.png"
                    img = mpimg.imread(img_path)

            if rot == -4:
                img = np.fliplr(img)
                if diagram:
                    img_path = image_dir / "fliplr.png"
                    img = mpimg.imread(img_path)

            if rot == -5:
                img = np.rot90(img, k=2)
                if diagram:
                    img_path = image_dir / "rot180.png"
                    img = mpimg.imread(img_path)

        if row is not None and col is not None:
            # Get the aspect ratio of the image
            img_height, img_width, _ = img.shape
            aspect_ratio = img_width / img_height

            # Adjust extent to preserve the aspect ratio

            img_width_extent = img_extent[1] - img_extent[0]
            img_height_extent = img_width_extent / aspect_ratio
            img_extent[3] = img_extent[2] + img_height_extent
            ax.imshow(img, extent=img_extent)
            text_position = [col + offset_c, row + offset_r]  # Adjust position above the image
            label = f"{ip}({brand[0:2].upper()})"
            if "*" in brand:
                label = f"{label}*"
            ax.text(text_position[0], text_position[1], label, ha='center', va='bottom', fontsize=5, color=color, weight='bold')

        # Track thumbnails in the top 2 rows, limit to first 12
        if col >=2 and col <= 27 and row >= 9 and  row <= 11 :
            img_box = (col, row, w, h+1)
            group1_boxes.append(img_box)

        if col >=2 and col <= 20 and row >= 4.5 and row < 7 :
            img_box = (col, row, w, h)
            group2_boxes.append(img_box)

    if group1_boxes:
        lefts = [col for col, row, w, h in group1_boxes]
        rights = [col + w for col, row, w, h in group1_boxes]
        bottoms = [row for col, row, w, h in group1_boxes]
        tops = [row + h for col, row, w, h in group1_boxes]

        min_col = min(lefts)
        max_col = max(rights)
        min_row = min(bottoms)
        max_row = max(tops)

        # Draw dashed rectangle
        rect = patches.Rectangle((min_col, min_row), max_col - min_col, max_row - min_row,
                                 linewidth=1.5, edgecolor='c', facecolor='none', linestyle='--')
        ax.add_patch(rect)

        # Add label above
        ax.text(2.3, max_row + 0.5, 'Group 1',
                ha='center', va='bottom', fontsize=10, color='c', weight='bold')

    if group2_boxes:
        lefts = [col for col, row, w, h in group2_boxes]
        rights = [col + w for col, row, w, h in group2_boxes]
        bottoms = [row for col, row, w, h in group2_boxes]
        tops = [row + h for col, row, w, h in group2_boxes]

        min_col = min(lefts)
        max_col = max(rights)
        min_row = min(bottoms)
        max_row = max(tops)
        print(min_col, max_col, min_row, max_row)
        max_row = 8.7

        # Draw dashed rectangle
        rect = patches.Rectangle((min_col, min_row), max_col - min_col, max_row - min_row,
                                 linewidth=1.5, edgecolor='m', facecolor='none', linestyle='--')
        ax.add_patch(rect)

        # Add label above
        ax.text(2.3, min_row - 0.9, 'Group 2',
                ha='center', va='bottom', fontsize=10, color='m', weight='bold')

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    map_dir = Path('/mnt/storage/thumbnails/map')
    map_dir.mkdir(parents=True, exist_ok=True)
    output_file = map_dir / f"map_{timestamp}.png"
    #plt.savefig(output_file, bbox_inches='tight', pad_inches=0)
    #plt.title(f"Wyndhurst Farm {datetime.now().strftime('%d/%m/%Y')}\n Hikvision: {cpt_hikvision}, Hanwha: {cpt_hanwha} ", fontsize=14, fontweight='bold', pad=0, color='black')
    fig.suptitle(f"Wyndhurst Farm {datetime.now().strftime('%d/%m/%Y %H:%M')}| Hikvision: {cpt_hikvision}, Hanwha: {cpt_hanwha}, Total {cpt_hikvision + cpt_hanwha} ",
                 fontsize=10,
                 fontweight='bold',
                 y=0.9,  # Moves the title downward (default ~1.0)
                 color='black')

    legend_labels = ["Milking (5)", "Race (7)", "Other (3)", "Transition Pen (6)", "Main Barn Cubicle 1 (6)",
                     "Back Barn Cubicle 1 (10)", "Back Barn Cubicles 2 (10)", "Back Barn Feed Face 2 (7)",
                     "Back Barn Feed Face 1 (10)"]
    legend_colors = [colors[0], colors[1], colors[2], colors[3], colors[4], colors[5], colors[6], colors[7], colors[8]]
    legend_handles = [Patch(facecolor=color, edgecolor=color, label=label) for color, label in
                      zip(legend_colors, legend_labels)]
    ax.legend(handles=legend_handles, loc='lower left', fontsize=8, frameon=False, ncol=3, bbox_to_anchor=(0.1, 0.1))
    plt.tight_layout()
    plt.savefig(output_file, bbox_inches='tight', pad_inches=0.1, dpi=600)
    plt.close()
    print(output_file)


def update_thumbnails_from_storage():
    base_folder = Path('/mnt/storage/thumbnails')
    hd_folder = base_folder / 'hd'
    sd_folder = base_folder / 'sd'

    data = get_first_file_after(Path("/mnt/storage/cctvnet/"))

    paths = [d.split('last:')[1].strip() for d in data]  # Extract paths properly
    print("Processing videos:", paths)
    ips = [d.split('Ip:')[1].strip().split(' ')[0].replace('66.', '') for d in data]

    for ip, video_path in zip(ips, paths):
        extract_thumbnail(ip, video_path, hd_folder, sd_folder)


def update_thumbnails_from_rstp():
    with Path("hikvision.txt").open("r") as file:
        camera_ips = [line.strip() for line in file if line.strip()]

    for idx, camera_ip in enumerate(camera_ips):
        ip, fisheye, port = camera_ip.split()
        rtsp_url = f"rtsp://admin:ocs881212@localhost:{port}/Streaming/channels/101"
        print(f"Downloading {rtsp_url}")
        filename = f"{ip.split('.')[-1]}.jpg"
        out_dir = Path('/mnt/storage/thumbnails/hd/')
        out_dir.mkdir(parents=True, exist_ok=True)
        filepath = out_dir / filename
        if filepath.exists():
            filepath.unlink()

        ffmpeg_command = [
            "ffmpeg",
            "-y",
            "-rtsp_transport", "tcp",
            "-i", rtsp_url,
            "-frames:v", "1",
            "-q:v", "2",
            filepath.as_posix()
        ]
        try:
            print("Running:", " ".join(ffmpeg_command))
            subprocess.run(ffmpeg_command, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error extracting thumbnail for {rtsp_url}: {e}")


    with Path("hanwha.txt").open("r") as file:
        camera_ips = [line.strip() for line in file if line.strip()]
    for idx, camera_ip in enumerate(camera_ips):
        ip, fisheye, port = camera_ip.split()
        rtsp_url = f"rtsp://admin:Ocs881212@localhost:{port}/profile2/media.smp"
        print(f"Downloading {rtsp_url}")
        filename = f"{ip.split('.')[-1]}.jpg"
        out_dir = Path('/mnt/storage/thumbnails/hd/')
        out_dir.mkdir(parents=True, exist_ok=True)
        filepath = out_dir / filename
        if filepath.exists():
            filepath.unlink()

        ffmpeg_command = [
            "ffmpeg",
            "-y",
            "-rtsp_transport", "tcp",
            "-i", rtsp_url,
            "-frames:v", "1",
            "-q:v", "2",
            filepath.as_posix()
        ]
        try:
            print("Running:", " ".join(ffmpeg_command))
            subprocess.run(ffmpeg_command, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error extracting thumbnail for {rtsp_url}: {e}")


def main():
    update_thumbnails_from_storage()
    #update_thumbnails_from_rstp()
    build_map()


if __name__ == '__main__':
    main()