from pathlib import Path
import subprocess
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

from report_email import get_latest_file

MAP = {

    17: {"brand": "hanwa", "ip": 17, "location": "transition pen", "position": (1, 1)},
    18: {"brand": "hanwa", "ip": 18, "location": "transition pen", "position": (1, 2)},
    20: {"brand": "hanwa", "ip": 20, "location": "transition pen", "position": (1, 3)},
    22: {"brand": "hanwa", "ip": 22, "location": "transition pen", "position": (1, 4)},
    24: {"brand": "hanwa", "ip": 24, "location": "transition pen", "position": (1, 5)},
    26: {"brand": "hanwa", "ip": 26, "location": "transition pen", "position": (1, 6)},
    16: {"brand": "hanwa", "ip": 16, "location": "transition pen", "position": (2, 1)},
    19: {"brand": "hanwa", "ip": 19, "location": "transition pen", "position": (2, 2)},
    21: {"brand": "hanwa", "ip": 21, "location": "transition pen", "position": (2, 3)},
    23: {"brand": "hanwa", "ip": 23, "location": "transition pen", "position": (2, 4)},
    25: {"brand": "hanwa", "ip": 25, "location": "transition pen", "position": (2, 5)},
    27: {"brand": "hanwa", "ip": 27, "location": "transition pen", "position": (2, 6)},

    8: {"brand": "hikvision", "ip": 8, "location": "backbarn bottom", "position": (1, 8)},
    11: {"brand": "hikvision", "ip": 11, "location": "backbarn bottom", "position": (1, 9)},
    125: {"brand": "hikvision", "ip": 125, "location": "backbarn bottom", "position": (1, 10)},
    6: {"brand": "hikvision", "ip": 6, "location": "backbarn bottom", "position": (1, 11)},
    131: {"brand": "hikvision", "ip": 131, "location": "backbarn bottom", "position": (1, 12)},
    136: {"brand": "hikvision", "ip": 136, "location": "backbarn bottom", "position": (1, 13)},
    126: {"brand": "hikvision", "ip": 126, "location": "backbarn bottom", "position": (1, 14)},

    128: {"brand": "hikvision", "ip": 128, "location": "backbarn top", "position": (2, 8)},
    133: {"brand": "hikvision", "ip": 133, "location": "backbarn top", "position": (2, 9)},
    1: {"brand": "hikvision", "ip": 1, "location": "backbarn top", "position": (2, 10)},
    3: {"brand": "hikvision", "ip": 3, "location": "backbarn top", "position": (2, 11)},
    33: {"brand": "hikvision", "ip": 33, "location": "backbarn top", "position": (2, 12)},
    130: {"brand": "hikvision", "ip": 130, "location": "backbarn top", "position": (2, 13)},
    139: {"brand": "hikvision", "ip": 139, "location": "backbarn top", "position": (2, 14)},



    # 137: {"brand": "hikvision", "ip": 137, "location": "other", "position": (0, 0)},
    # 138: {"brand": "hikvision", "ip": 138, "location": "other", "position": (0, 0)},
    # 156: {"brand": "hikvision", "ip": 156, "location": "other", "position": (0, 0)},
    # 132: {"brand": "hikvision", "ip": 132, "location": "other", "position": (0, 0)},
    # 5: {"brand": "hikvision", "ip": 5, "location": "other", "position": (0, 0)},
    # 9: {"brand": "hikvision", "ip": 9, "location": "other", "position": (0, 0)},
    # 4: {"brand": "hikvision", "ip": 4, "location": "other", "position": (0, 0)},
    # 34: {"brand": "hikvision", "ip": 34, "location": "mobility", "position": (0, 0)},

    # 39: {"brand": "hanwa 360", "ip": 39, "location": "backbarn up cubicles", "position": (0, 0)},
    # 43: {"brand": "hanwa 360", "ip": 43, "location": "backbarn up cubicles", "position": (0, 0)},
    # 41: {"brand": "hanwa 360", "ip": 41, "location": "backbarn up cubicles", "position": (0, 0)},
    # 38: {"brand": "hanwa 360", "ip": 38, "location": "backbarn up cubicles", "position": (0, 0)},
    # 44: {"brand": "hanwa 360", "ip": 44, "location": "backbarn up cubicles", "position": (0, 0)},
    # 37: {"brand": "hanwa 360", "ip": 37, "location": "backbarn up cubicles", "position": (0, 0)},
    # 40: {"brand": "hanwa 360", "ip": 40, "location": "backbarn up cubicles", "position": (0, 0)},
    # 35: {"brand": "hanwa 360", "ip": 35, "location": "backbarn up cubicles", "position": (0, 0)},
    # 42: {"brand": "hanwa 360", "ip": 42, "location": "backbarn up cubicles", "position": (0, 0)},
    # 36: {"brand": "hanwa 360", "ip": 36, "location": "backbarn up cubicles", "position": (0, 0)},
    # 52: {"brand": "hanwa 360", "ip": 52, "location": "backbarn down cubicles", "position": (0, 0)},
    # 53: {"brand": "hanwa 360", "ip": 53, "location": "backbarn down cubicles", "position": (0, 0)},
    # 141: {"brand": "hanwa 360", "ip": 141, "location": "backbarn down cubicles", "position": (0, 0)},
    # 50: {"brand": "hanwa 360", "ip": 50, "location": "backbarn down cubicles", "position": (0, 0)},
    # 49: {"brand": "hanwa 360", "ip": 49, "location": "backbarn down cubicles", "position": (0, 0)},
    # 47: {"brand": "hanwa 360", "ip": 47, "location": "backbarn down cubicles", "position": (0, 0)},
    # 45: {"brand": "hanwa 360", "ip": 45, "location": "backbarn down cubicles", "position": (0, 0)},
    # 46: {"brand": "hanwa 360", "ip": 46, "location": "backbarn down cubicles", "position": (0, 0)},
    # 54: {"brand": "hanwa 360", "ip": 54, "location": "backbarn down cubicles", "position": (0, 0)},
    # 48: {"brand": "hanwa 360", "ip": 48, "location": "backbarn down cubicles", "position": (0, 0)},

    # 28: {"brand": "hanwa", "ip": 28, "location": "race", "position": (0, 0)},
    # 29: {"brand": "hanwa", "ip": 29, "location": "race", "position": (0, 0)},
    # 30: {"brand": "hanwa", "ip": 30, "location": "race", "position": (0, 0)},
    # 31: {"brand": "hanwa", "ip": 31, "location": "race", "position": (0, 0)}





}


def extract_thumbnail(ip, video_path, hd_folder, sd_folder):
    hd_folder.mkdir(parents=True, exist_ok=True)
    sd_folder.mkdir(parents=True, exist_ok=True)

    #filename = f"{MAP[int(ip)]['location']}_{ip}.jpg"
    filename = f"{ip}.jpg"
    hd_path = hd_folder / filename
    sd_path = sd_folder / filename

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
    image_dir = Path('/mnt/storage/thumbnails/sd')
    fig, ax = plt.subplots(figsize=(60, 5))
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 10)
    ax.axis('off')

    for idx, item in enumerate(MAP.items()):
        ip = item[1]["ip"]
        location = item[1]["location"]
        brand = item[1]["brand"]
        row, col = item[1]["position"]
        img_path = image_dir / f"{ip}.jpg"

        try:
            img = mpimg.imread(img_path)
        except Exception as e:
            print(f"Error reading {img_path}: {e}")
            img = mpimg.imread("black.jpg")

        if row is not None and col is not None:
            # Get the aspect ratio of the image
            img_height, img_width, _ = img.shape
            aspect_ratio = img_width / img_height

            # Adjust extent to preserve the aspect ratio
            img_extent = [col, col + 1, row, row + 1]
            img_width_extent = img_extent[1] - img_extent[0]
            img_height_extent = img_width_extent / aspect_ratio
            img_extent[3] = img_extent[2] + img_height_extent

            ax.imshow(img, extent=img_extent)
            text_position = [col + 0.5, row + 0.7]  # Adjust position above the image
            ax.text(text_position[0], text_position[1], ip, ha='center', va='bottom', fontsize=5, color='black', weight='bold')

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    map_dir = Path('/mnt/storage/thumbnails/map')
    map_dir.mkdir(parents=True, exist_ok=True)
    output_file = map_dir / f"map_{timestamp}.png"
    #plt.savefig(output_file, bbox_inches='tight', pad_inches=0)
    plt.savefig(output_file, bbox_inches='tight', pad_inches=0, dpi=600)
    plt.close()

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


if __name__ == '__main__':
    build_map()
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
