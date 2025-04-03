from pathlib import Path
import subprocess
import pandas as pd
from datetime import datetime
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from PIL.ImageChops import offset
from matplotlib.patches import Patch
# from report_email import get_latest_file
from utils import MAP
import numpy as np
import cv2


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


def build_map():
    image_dir = Path('/mnt/storage/thumbnails/hd')
    fig, ax = plt.subplots(figsize=(60, 5))
    ax.set_xlim(0, 36)
    ax.set_ylim(0, 13)
    ax.axis('off')

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
            img = mpimg.imread("black.jpg")

        tab10 = plt.get_cmap("tab10")
        colors = [tab10(i) for i in range(tab10.N)]

        color = colors[c_id]
        if rot == 1:
            img = np.rot90(img)
        if rot == -1:
            img = np.fliplr(img)

        # if ip in [48, 54, 46, 45, 47, 49, 50, 141, 53, 52]:
        #     offset_c, offset_r = 0.5, -0.3
        #     color = colors[0]
        # if ip in [36, 42, 35, 40, 37, 44, 38, 41, 43, 39]:
        #     offset_c, offset_r = 0.5, 1.1
        #     color = colors[0]
        # if ip in [156, 132, 5, 9, 4]:
        #     offset_c, offset_r = 0.5, 0.6
        #     color = colors[1]
        #     img = np.rot90(img)
        # if ip in [137]:
        #     offset_c, offset_r = 0.5, 0.6
        #     color = colors[1]
        #     img = np.rot90(img)
        # if ip in [28, 34, 138, 29, 30, 31]:
        #     offset_c, offset_r = 0.5, 0.6
        #     color = colors[1]
        #     img_extent = [col, col + 2, row, row + 1]
        #
        # if ip in [137, 28, 34, 138, 29, 30, 31]:
        #     offset_c, offset_r = 0.5, 0.76
        #     color = colors[2]
        # if ip in [17, 18, 20, 22, 24, 26, 16, 19, 21, 23, 25, 27]:
        #     offset_c, offset_r = 0.5, 0.76
        #     color = colors[3]
        # if ip in [128, 133, 1, 3, 33, 130, 139, 8, 11, 125, 6, 131, 136, 126]:
        #     offset_c, offset_r = 0.5, 0.6
        #     color = colors[4]


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
            ax.text(text_position[0], text_position[1], f"{ip}({brand[0:2].upper()})", ha='center', va='bottom', fontsize=5, color=color, weight='bold')

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    map_dir = Path('/mnt/storage/thumbnails/map')
    map_dir.mkdir(parents=True, exist_ok=True)
    output_file = map_dir / f"map_{timestamp}.png"
    #plt.savefig(output_file, bbox_inches='tight', pad_inches=0)
    #plt.title(f"Whyndhurst Farm {datetime.now().strftime('%d/%m/%Y')}\n Hikvision: {cpt_hikvision}, Hanwha: {cpt_hanwha} ", fontsize=14, fontweight='bold', pad=0, color='black')
    fig.suptitle(f"Whyndhurst Farm {datetime.now().strftime('%d/%m/%Y')}| Hikvision: {cpt_hikvision}, Hanwha: {cpt_hanwha} ",
                 fontsize=10,
                 fontweight='bold',
                 y=0.9,  # Moves the title downward (default ~1.0)
                 color='black')

    legend_labels = ["Back Barn Cubicle (20)", "Milking (5)", "Race Foot bath (7)", "Transition Pen 4 (12)", "Back Barn Feed Face (14)"]
    legend_colors = [colors[0], colors[1], colors[2], colors[3], colors[4]]
    legend_handles = [Patch(facecolor=color, edgecolor='black', label=label) for color, label in
                      zip(legend_colors, legend_labels)]
    # ax.legend(handles=legend_handles, loc='lower right', fontsize=8, frameon=False,
    #           bbox_to_anchor=(0.95, 0.12))
    plt.tight_layout()
    plt.savefig(output_file, bbox_inches='tight', pad_inches=0, dpi=600)
    plt.close()
    print(output_file)

# def build_map():
#     image_dir = Path('/mnt/storage/thumbnails/sd')
#     fig, ax = plt.subplots(figsize=(40, 5))
#     ax.set_xlim(0, 16)
#     ax.set_ylim(0, 10)
#     ax.axis('off')
#     for idx, item in enumerate(MAP.items()):
#         ip = item[1]["ip"]
#         location = item[1]["location"]
#         brand = item[1]["brand"]
#         row, col = item[1]["position"]
#         img_path = image_dir / f"{ip}.jpg"
#         try:
#             img = mpimg.imread(img_path)
#         except Exception as e:
#             print(f"Error reading {img_path}: {e}")
#             img = mpimg.imread("black.jpg")
#
#         if row is not None and col is not None:
#             ax.imshow(img, extent=[col, col + 1, row, row + 1])
#     timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#     map_dir = Path('/mnt/storage/thumbnails/map')
#     map_dir.mkdir(parents=True, exist_ok=True)
#     output_file = map_dir / f"map_{timestamp}.png"
#     plt.savefig(output_file, bbox_inches='tight', pad_inches=0)
#     plt.close()

def main():
    # base_folder = Path('/mnt/storage/thumbnails')
    # hd_folder = base_folder / 'hd'
    # sd_folder = base_folder / 'sd'
    #
    # data = get_latest_file(Path("/mnt/storage/cctvnet/"), n=-20)
    #
    # paths = [d.split('last:')[1].strip() for d in data]  # Extract paths properly
    # print("Processing videos:", paths)
    # ips = [d.split('Ip:')[1].strip().split(' ')[0].replace('66.', '') for d in data]
    #
    # for ip, video_path in zip(ips, paths):
    #     extract_thumbnail(ip, video_path, hd_folder, sd_folder)

    build_map()


if __name__ == '__main__':
    main()