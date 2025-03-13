import paramiko
import os
import time
from pathlib import Path
import configparser
import pandas as pd
from datetime import datetime


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
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    (output, err) = p.communicate()
    p_status = p.wait()
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