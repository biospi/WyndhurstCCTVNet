import paramiko
import os
import time
from pathlib import Path
import configparser
import pandas as pd
from datetime import datetime



SOURCE_PATH = "/home/fo18103/PycharmProjects/WhyndhurstVideoTransfer/"


MAP = {
    156: {"brand": "hikvision", "ip": 156, "location": "other", "position": (1, 30, 1, 1, 1, 0.5, 1.8, 0)},
    132: {"brand": "hikvision", "ip": 132, "location": "other", "position": (1, 29, 1, 1, 1, 0.5, 1.8, 0)},
    5: {"brand": "hikvision", "ip": 5, "location": "other", "position": (1, 28, 1, 1, 1, 0.5, 1.8, 0)},
    9: {"brand": "hikvision", "ip": 9, "location": "other", "position": (1, 27, 1, 1, 1, 0.5, 1.8, 0)},
    4: {"brand": "hikvision", "ip": 4, "location": "other", "position": (1, 26, 1, 1, 1, 0.5, 1.8, 0)},

    137: {"brand": "hikvision", "ip": 137, "location": "other", "position": (5, 32, 2, 1, 1, 2.5, 1.8, 1)},
    28: {"brand": "hanwa", "ip": 28, "location": "race", "position": (5, 30, 2, 0, 0, 1, 1.15, 1)},
    29: {"brand": "hanwa", "ip": 29, "location": "race", "position": (5, 28, 2, 0, 0, 1, 1.6, 1)},
    30: {"brand": "hanwa", "ip": 30, "location": "race", "position": (5, 26, 2, 0, 0, 1, 1.6, 1)},
    31: {"brand": "hanwa", "ip": 31, "location": "race", "position": (5, 24, 2, 0, 0, 1, 1.6, 1)},

    34: {"brand": "hikvision", "ip": 34, "location": "mobility", "position": (3.5, 28, 2, 0, 0, 1, 1.15, 1)},
    138: {"brand": "hikvision", "ip": 138, "location": "id", "position": (3.5, 32, 2, 0, 0, 1, 1.15, 1)},

    127: {"brand": "hikvision", "ip": 127, "location": "Quarantine", "position": (7, 30, 2, 0, 0, 1, 1.15, 2)},
    129: {"brand": "hikvision", "ip": 129, "location": "Quarantine", "position": (3.5, 30, 2, 0, 0, 1, 1.15, 2)},

    17: {"brand": "hanwa", "ip": 17, "location": "transition pen", "position": (9, 33, 2, 1, -1, 1, 1.55, 3)},
    18: {"brand": "hanwa", "ip": 18, "location": "transition pen", "position": (9, 31, 2, 1, -1, 1, 1.55, 3)},
    20: {"brand": "hanwa", "ip": 20, "location": "transition pen", "position": (9, 29, 2, 1, -1, 1, 1.55, 3)},
    22: {"brand": "hanwa", "ip": 22, "location": "transition pen", "position": (9, 27, 2, 1, -1, 1, 1.55, 3)},
    24: {"brand": "hanwa", "ip": 24, "location": "transition pen", "position": (9, 25, 2, 1, -1, 1, 1.55, 3)},
    26: {"brand": "hanwa", "ip": 26, "location": "transition pen", "position": (9, 23, 2, 1, -1, 1, 1.55, 3)},

    16: {"brand": "hanwa", "ip": 16, "location": "transition pen", "position": (11, 33, 2, 1, -1, 1, 1.55, 3)},
    19: {"brand": "hanwa", "ip": 19, "location": "transition pen", "position": (11, 31, 2, 1, -1, 1, 1.55, 3)},
    21: {"brand": "hanwa", "ip": 21, "location": "transition pen", "position": (11, 29, 2, 1, -1, 1, 1.55, 3)},
    23: {"brand": "hanwa", "ip": 23, "location": "transition pen", "position": (11, 27, 2, 1, -1, 1, 1.55, 3)},
    25: {"brand": "hanwa", "ip": 25, "location": "transition pen", "position": (11, 25, 2, 1, -1, 1, 1.55, 3)},
    27: {"brand": "hanwa", "ip": 27, "location": "transition pen", "position": (11, 23, 2, 1, -1, 1, 1.55, 3)},

    52: {"brand": "hanwa 360", "ip": 52, "location": "backbarn down cubicles", "position": (11, 2, 2, 1, 0, 1, 2.05, 4)},
    53: {"brand": "hanwa 360", "ip": 53, "location": "backbarn down cubicles", "position": (11, 4, 2, 1, 0, 1, 2.05, 4)},
    141: {"brand": "hanwa 360", "ip": 141, "location": "backbarn down cubicles", "position": (11, 6, 2, 1, 0, 1, 2.05, 4)},
    50: {"brand": "hanwa 360", "ip": 50, "location": "backbarn down cubicles", "position": (11, 8, 2, 1, 0, 1, 2.05, 4)},
    49: {"brand": "hanwa 360", "ip": 49, "location": "backbarn down cubicles", "position": (11, 10, 2, 1, 0, 1, 2.05, 4)},
    47: {"brand": "hanwa 360", "ip": 47, "location": "backbarn down cubicles", "position": (11, 12, 2, 1, 0, 1, 2.05, 4)},
    45: {"brand": "hanwa 360", "ip": 45, "location": "backbarn down cubicles", "position": (11, 14, 2, 1, 0, 1, 2.05, 4)},
    46: {"brand": "hanwa 360", "ip": 46, "location": "backbarn down cubicles", "position": (11, 16, 2, 1, 0, 1, 2.05, 4)},
    54: {"brand": "hanwa 360", "ip": 54, "location": "backbarn down cubicles", "position": (11, 18, 2, 1, 0, 1, 2.05, 4)},
    48: {"brand": "hanwa 360", "ip": 48, "location": "backbarn down cubicles", "position": (11, 20, 2, 1, 0, 1, 2.05, 4)},

    39: {"brand": "hanwa 360", "ip": 39, "location": "backbarn up cubicles", "position": (4.5, 2, 2, 1, 0, 1, 2.05, 4)},
    43: {"brand": "hanwa 360", "ip": 43, "location": "backbarn up cubicles", "position": (4.5, 4, 2, 1, 0, 1, 2.05, 4)},
    41: {"brand": "hanwa 360", "ip": 41, "location": "backbarn up cubicles", "position": (4.5, 6, 2, 1, 0, 1, 2.05, 4)},
    38: {"brand": "hanwa 360", "ip": 38, "location": "backbarn up cubicles", "position": (4.5, 8, 2, 1, 0, 1, 2.05, 4)},
    44: {"brand": "hanwa 360", "ip": 44, "location": "backbarn up cubicles", "position": (4.5, 10, 2, 1, 0, 1, 2.05, 4)},
    37: {"brand": "hanwa 360", "ip": 37, "location": "backbarn up cubicles", "position": (4.5, 12, 2, 1, 0, 1, 2.05, 4)},
    40: {"brand": "hanwa 360", "ip": 40, "location": "backbarn up cubicles", "position": (4.5, 14, 2, 1, 0, 1, 2.05, 4)},
    35: {"brand": "hanwa 360", "ip": 35, "location": "backbarn up cubicles", "position": (4.5, 16, 2, 1, 0, 1, 2.05, 4)},
    42: {"brand": "hanwa 360", "ip": 42, "location": "backbarn up cubicles", "position": (4.5, 18, 2, 1, 0, 1, 2.05, 4)},
    36: {"brand": "hanwa 360", "ip": 36, "location": "backbarn up cubicles", "position": (4.5, 20, 2, 1, 0, 1, 2.05, 4)},

    8: {"brand": "hikvision", "ip": 8, "location": "backbarn bottom", "position": (9, 19, 3, 1, -1, 1.5, 1.7, 5)},
    11: {"brand": "hikvision", "ip": 11, "location": "backbarn bottom", "position": (9, 16, 3, 1, -1, 1.5, 1.7, 5)},
    125: {"brand": "hikvision", "ip": 125, "location": "backbarn bottom", "position": (9, 13, 3, 1, -1, 1, 1.7, 5)},
    6: {"brand": "hikvision", "ip": 6, "location": "backbarn bottom", "position": (9, 10, 3, 1, -1, 1, 1.7, 5)},
    131: {"brand": "hikvision", "ip": 131, "location": "backbarn bottom", "position": (9, 7, 3, 1, -1, 1, 1.7, 5)},
    136: {"brand": "hikvision", "ip": 136, "location": "backbarn bottom", "position": (9, 4, 3, 1, -1, 1, 1.7, 5)},
    126: {"brand": "hikvision", "ip": 126, "location": "backbarn bottom", "position": (9, 1, 3, 1, -1, 1, 1.7, 5)},

    128: {"brand": "hikvision", "ip": 128, "location": "backbarn top", "position": (7, 19, 3, 1, -2, 1.5, 1.7, 5)},
    133: {"brand": "hikvision", "ip": 133, "location": "backbarn top", "position": (7, 16, 3, 1, -2, 1.5, 1.7, 5)},
    1: {"brand": "hikvision", "ip": 1, "location": "backbarn top", "position": (7, 13, 3, 1, -2, 1.5, 1.7, 5)},
    3: {"brand": "hikvision", "ip": 3, "location": "backbarn top", "position": (7, 10, 3, 1, -2, 1.5, 1.7, 5)},
    33: {"brand": "hikvision", "ip": 33, "location": "backbarn top", "position": (7, 7, 3, 1, -2, 1.5, 1.7, 5)},
    130: {"brand": "hikvision", "ip": 130, "location": "backbarn top", "position": (7, 4, 3, 1, -2, 1.5, 1.7, 5)},
    139: {"brand": "hikvision", "ip": 139, "location": "backbarn top", "position": (7, 1, 3, 1, -2, 1.5, 1.7, 5)},


}


def is_float(string):
    try:
        float(string)
        if '.' not in string:
            return False
        return True
    except ValueError:
        return False

from pathlib import Path
import subprocess
from datetime import datetime
import subprocess as sp


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
    # if verbose:
    #     print(f"[{i}/{tot}] status-> {p_status} output-> {output} err-> {err}")


def format_curl(cmd, out_dir, format_output=False, ip_address=""):
    out_dir.mkdir(parents=True, exist_ok=True)
    old_path = cmd.split("--output")[-1].strip()
    subfolder = "images"
    end_time = cmd.split("endtime=")[1].split('Z&')[0]
    end_time = datetime.strptime(end_time, "%Y%m%dT%H%M%S")
    formatted_end_time = end_time.strftime("%Y%m%dT%H%M%S")

    start_time = cmd.split("starttime=")[1].split('Z&')[0]
    start_time = datetime.strptime(start_time, "%Y%m%dT%H%M%S")
    formatted_start_time = start_time.strftime("%Y%m%dT%H%M%S")

    if "mp4" in old_path:
        subfolder = "videos"

    if format_output:
        new_path = format_dst(out_dir, old_path, ip_address)
        (new_path.parent / subfolder).mkdir(parents=True, exist_ok=True)
        new_path = new_path.parent / subfolder / f"{formatted_start_time}_{formatted_end_time}{new_path.suffix}"
    else:
        (out_dir / subfolder).mkdir(parents=True, exist_ok=True)
        new_path = out_dir / subfolder/ old_path
    new_cmd = cmd.replace(old_path, str(new_path))
    return new_cmd, new_path, start_time, end_time


def format_dst(folder, video, ip_address):
    cam_id = ".".join(ip_address.split(".")[-2:])
    date = datetime.strptime(video.split(".")[0], "%Y-%m-%dT%H-%M-%S")
    date_ = date.strftime("%Y%b%d")
    out_dir = folder / cam_id / date_
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / video
    return path

#rstp://admin:Ocs881212@10.70.66.28/profile1/media.smp
#rtsp://10.70.66.24:1024/multicast/profile1/media.smp
#rtsp://239.1.1.1:1024/multicast/profile1/media.smp
#rtsp://239.1.1.1:1024/1/multicast/profile1/media.smp
#rtsp://10.70.66.24:554/profile1/media.smp
#rtsp://admin:Ocs881212@10.70.66.24:554/profile2/media.smp