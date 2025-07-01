import re
import subprocess
from datetime import datetime, timedelta

import pandas as pd

SOURCE_PATH = "//"


MAP = {
    156: {"brand": "hikvision*", "ip": 156, "location": "Milking", "position": (0, 30, 1, 1, 1, 0.5, 1.8, 0)},
    132: {"brand": "hikvision", "ip": 132, "location": "Milking", "position": (0, 29, 1, 1, 1, 0.5, 1.8, 0)},
    5: {"brand": "hikvision", "ip": 5, "location": "Milking", "position": (0, 28, 1, 1, 1, 0.5, 1.8, 0)},
    9: {"brand": "hikvision", "ip": 9, "location": "Milking", "position": (0, 27, 1, 1, 1, 0.5, 1.8, 0)},
    4: {"brand": "hikvision*", "ip": 4, "location": "Milking", "position": (0, 26, 1, 1, 1, 0.5, 1.8, 0)},

    137: {"brand": "hikvision*", "ip": 137, "location": "Race Foot Bath", "position": (5, 32, 2, 1, -10, 2.5, 1.8, 1)},
    28: {"brand": "hanwa*", "ip": 28, "location": "Race Foot Bath", "position": (5, 30, 2, 0, -5, 1, 1.2, 1)},
    29: {"brand": "hanwa*", "ip": 29, "location": "Race Foot Bath", "position": (5, 28, 2, 0, -5, 1, 1.2, 1)},
    30: {"brand": "hanwa*", "ip": 30, "location": "Race Foot Bath", "position": (5, 26, 2, 0, -5, 1, 1.2, 1)},
    31: {"brand": "hanwa*", "ip": 31, "location": "Race Foot Bath", "position": (5, 24, 2, 0, -5, 1, 1.2, 1)},

    34: {"brand": "hikvision*", "ip": 34, "location": "Race Foot bath", "position": (3.5, 28, 2, 0, 0, 1, 1.15, 1)},
    138: {"brand": "hikvision*", "ip": 138, "location": "Race Foot bath", "position": (2.3, 29, 2, 0, 0, 2.5, 0.5, 1)},

    127: {"brand": "hikvision", "ip": 127, "location": "Quarantine", "position": (7, 28, 2, 0, -1, 1, 1.15, 2)},
    15: {"brand": "hikvision", "ip": 15, "location": "Quarantine", "position": (7, 30, 2, 0, -1, 1, 1.15, 2)},
    129: {"brand": "hikvision", "ip": 129, "location": "Quarantine", "position": (3.5, 30, 2, 0, -1, 1, 1.15, 2)},

    17: {"brand": "hanwa*", "ip": 17, "location": "Transition Pen", "position": (9, 33, 2, 1, -4, 1, 1.55, 3)},
    18: {"brand": "hanwa*", "ip": 18, "location": "Transition Pen", "position": (9, 31, 2, 1, -4, 1, 1.55, 3)},
    20: {"brand": "hanwa*", "ip": 20, "location": "Transition Pen", "position": (9, 29, 2, 1, -4, 1, 1.55, 3)},
    16: {"brand": "hanwa*", "ip": 16, "location": "Transition Pen", "position": (11, 33, 2, 1, -4, 1, 1.55, 3)},
    19: {"brand": "hanwa*", "ip": 19, "location": "Transition Pen", "position": (11, 31, 2, 1, -4, 1, 1.55, 3)},
    21: {"brand": "hanwa*", "ip": 21, "location": "Transition Pen", "position": (11, 29, 2, 1, -4, 1, 1.55, 3)},

    22: {"brand": "hanwa*", "ip": 22, "location": "Main Barn Cubicle 1", "position": (9, 27, 2, 1, -4, 1, 1.55, 4)},
    24: {"brand": "hanwa*", "ip": 24, "location": "Main Barn Cubicle 1", "position": (9, 25, 2, 1, -4, 1, 1.55, 4)},
    26: {"brand": "hanwa*", "ip": 26, "location": "Main Barn Cubicle 1", "position": (9, 23, 2, 1, -4, 1, 1.55, 4)},
    23: {"brand": "hanwa*", "ip": 23, "location": "Main Barn Cubicle 1", "position": (11, 27, 2, 1, -4, 1, 1.55, 4)},
    25: {"brand": "hanwa*", "ip": 25, "location": "Main Barn Cubicle 1", "position": (11, 25, 2, 1, -4, 1, 1.55, 4)},
    27: {"brand": "hanwa*", "ip": 27, "location": "Main Barn Cubicle 1", "position": (11, 23, 2, 1, -4, 1, 1.55, 4)},

    52: {"brand": "hanwa 360*", "ip": 52, "location": "Back Barn Cubicle 1", "position": (11, 2, 2, 1, 0, 1, 2.05, 5)},
    53: {"brand": "hanwa 360*", "ip": 53, "location": "Back Barn Cubicle 1", "position": (11, 4, 2, 1, 0, 1, 2.05, 5)},
    141: {"brand": "hanwa 360*", "ip": 141, "location": "Back Barn Cubicle 1", "position": (11, 6, 2, 1, 0, 1, 2.05, 5)},
    50: {"brand": "hanwa 360*", "ip": 50, "location": "Back Barn Cubicle 1", "position": (11, 8, 2, 1, 0, 1, 2.05, 5)},
    49: {"brand": "hanwa 360*", "ip": 49, "location": "Back Barn Cubicle 1", "position": (11, 10, 2, 1, 0, 1, 2.05, 5)},
    47: {"brand": "hanwa 360*", "ip": 47, "location": "Back Barn Cubicle 1", "position": (11, 12, 2, 1, 0, 1, 2.05, 5)},
    45: {"brand": "hanwa 360*", "ip": 45, "location": "Back Barn Cubicle 1", "position": (11, 14, 2, 1, 0, 1, 2.05, 5)},
    46: {"brand": "hanwa 360*", "ip": 46, "location": "Back Barn Cubicle 1", "position": (11, 16, 2, 1, 0, 1, 2.05, 5)},
    54: {"brand": "hanwa 360*", "ip": 54, "location": "Back Barn Cubicle 1", "position": (11, 18, 2, 1, 0, 1, 2.05, 5)},
    48: {"brand": "hanwa 360*", "ip": 48, "location": "Back Barn Cubicle 1", "position": (11, 20, 2, 1, 0, 1, 2.05, 5)},

    39: {"brand": "hanwa 360", "ip": 39, "location": "Back Barn Cubicle 2", "position": (4.5, 2, 2, 1, 0, 1, 2.05, 6)},
    43: {"brand": "hanwa 360", "ip": 43, "location": "Back Barn Cubicle 2", "position": (4.5, 4, 2, 1, 0, 1, 2.05, 6)},
    41: {"brand": "hanwa 360", "ip": 41, "location": "Back Barn Cubicle 2", "position": (4.5, 6, 2, 1, 0, 1, 2.05, 6)},
    38: {"brand": "hanwa 360", "ip": 38, "location": "Back Barn Cubicle 2", "position": (4.5, 8, 2, 1, 0, 1, 2.05, 6)},
    44: {"brand": "hanwa 360", "ip": 44, "location": "Back Barn Cubicle 2", "position": (4.5, 10, 2, 1, 0, 1, 2.05, 6)},
    37: {"brand": "hanwa 360", "ip": 37, "location": "Back Barn Cubicle 2", "position": (4.5, 12, 2, 1, 0, 1, 2.05, 6)},
    40: {"brand": "hanwa 360", "ip": 40, "location": "Back Barn Cubicle 2", "position": (4.5, 14, 2, 1, 0, 1, 2.05, 6)},
    35: {"brand": "hanwa 360", "ip": 35, "location": "Back Barn Cubicle 2", "position": (4.5, 16, 2, 1, 0, 1, 2.05, 6)},
    42: {"brand": "hanwa 360", "ip": 42, "location": "Back Barn Cubicle 2", "position": (4.5, 18, 2, 1, 0, 1, 2.05, 6)},
    36: {"brand": "hanwa 360", "ip": 36, "location": "Back Barn Cubicle 2", "position": (4.5, 20, 2, 1, 0, 1, 2.05, 6)},

    8: {"brand": "hikvision", "ip": 8, "location": "Back Barn Feed Face 2", "position": (7, 19, 3, 1, -1, 1.5, 1.7, 7)},
    11: {"brand": "hikvision", "ip": 11, "location": "Back Barn Feed Face 2", "position": (7, 16, 3, 1, -1, 1.5, 1.7, 7)},
    125: {"brand": "hikvision", "ip": 125, "location": "Back Barn Feed Face 2", "position": (7, 13, 3, 1, -1, 1, 1.7, 7)},
    6: {"brand": "hikvision", "ip": 6, "location": "Back Barn Feed Face 2", "position": (7, 10, 3, 1, -1, 1, 1.7, 7)},
    131: {"brand": "hikvision", "ip": 131, "location": "Back Barn Feed Face 2", "position": (7, 7, 3, 1, -1, 1, 1.7, 7)},
    136: {"brand": "hikvision", "ip": 136, "location": "Back Barn Feed Face 2", "position": (7, 4, 3, 1, -1, 1, 1.7, 7)},
    126: {"brand": "hikvision", "ip": 126, "location": "Back Barn Feed Face 2", "position": (7, 1, 3, 1, -1, 1, 1.7, 7)},

    128: {"brand": "hikvision*", "ip": 128, "location": "Back Barn Feed Face 1", "position": (9, 19, 3, 1, -10, 1.5, 1.7, 8)},
    133: {"brand": "hikvision*", "ip": 133, "location": "Back Barn Feed Face 1", "position": (9, 16, 3, 1, -10, 1.5, 1.7, 8)},
    1: {"brand": "hikvision*", "ip": 1, "location": "Back Barn Feed Face 1", "position": (9, 13, 3, 1, -10, 1.5, 1.7, 8)},
    3: {"brand": "hikvision*", "ip": 3, "location": "Back Barn Feed Face 1", "position": (9, 10, 3, 1, -10, 1.5, 1.7, 8)},
    33: {"brand": "hikvision*", "ip": 33, "location": "Back Barn Feed Face 1", "position": (9, 7, 3, 1, -10, 1.5, 1.7, 8)},
    130: {"brand": "hikvision*", "ip": 130, "location": "Back Barn Feed Face 1", "position": (9, 4, 3, 1, -10, 1.5, 1.7, 8)},
    139: {"brand": "hikvision*", "ip": 139, "location": "Back Barn Feed Face 1", "position": (9, 1, 3, 1, -10, 1.5, 1.7, 8)}
}


def extract_ip(path):
    match = re.search(r"66\.\d+", str(path))  # Extract "66.xxx"
    return match.group(0) if match else None


def extract_timestamp(path):
    """Extracts start timestamp from filename (e.g., '20250410T122926_...')."""
    try:
        name = path.name
        timestamp_str = name.split("_")[0]
        return datetime.strptime(timestamp_str, "%Y%m%dT%H%M%S")
    except Exception:
        return None


def get_first_file_after(folder_path, days_offset=5, target_hour=4):
    """Returns the first .mp4 file per IP after a future datetime."""
    mp4_files = list(folder_path.rglob("*.mp4"))
    df = pd.DataFrame(mp4_files, columns=["path"])

    df["ip"] = df["path"].apply(extract_ip)
    df["start_time"] = df["path"].apply(extract_timestamp)
    df = df.dropna(subset=["start_time"])

    now = datetime.now()
    target_dt = now.replace(hour=target_hour, minute=now.minute, second=0, microsecond=0) - timedelta(days=days_offset)

    logs = []
    grouped_dfs = {ip: group.drop(columns="ip") for ip, group in df.groupby("ip")}

    for ip, group_df in grouped_dfs.items():
        filtered = group_df[group_df["start_time"] >= target_dt].sort_values("start_time")
        print(f"IP: {ip}\n{filtered}\n")
        try:
            first_file = filtered.iloc[0]["path"]
            log = f"Ip:{ip} last:{first_file.as_posix()}"
        except IndexError:
            log = f"Ip:{ip} No file after {target_dt}"
            print(log)
            continue
        logs.append(log)

    return logs


def get_latest_file(folder_path, n=-1):
    """Finds the most recent file in the given folder."""

    mp4_files = list(folder_path.rglob("*.mp4"))
    df = pd.DataFrame(mp4_files, columns=["path"])

    df["ip"] = df["path"].apply(extract_ip)
    grouped_dfs = {ip: group.drop(columns="ip") for ip, group in df.groupby("ip")}
    last_files = []
    logs = []
    for ip, group_df in grouped_dfs.items():
        print(f"IP: {ip}")
        print(group_df, "\n")
        last_files.append(group_df.values[n])
        log = "unknown"
        try:
            log = f"Ip:{ip} last:{group_df.values[n][0].as_posix()}\n"
        except Exception as e:
            print(e)
        logs.append(log)
    return logs


def is_float(string):
    try:
        float(string)
        if '.' not in string:
            return False
        return True
    except ValueError:
        return False


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

if __name__ == "__main__":
    # Mapping of rotation codes to human-readable transformations
    rotation_map = {
        1: "Rotate 90°",
        -1: "Flip horizontally & vertically",
        -2: "Flip horizontally twice (no net change)",
        -3: "Flip vertically",
        -4: "Flip horizontally",
        -5: "Rotate 180°"
    }

    # Build DataFrame
    rows = []
    for ip, info in sorted(MAP.items()):
        rot = info["position"][4]
        rows.append({
            "Camera IP": ip,
            "Brand": info["brand"],
            "Location": info["location"],
            "Transformation": rotation_map.get(rot, "None")
        })

    df = pd.DataFrame(rows)
    df.to_csv("cctv_frame_transforms.csv", index=False)