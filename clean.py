from pathlib import Path
import re
import numpy as np
from datetime import datetime
from collections import defaultdict


def extract_timestamps(filename):
    match = re.search(r"(\d{8}T\d{6})_(\d{8}T\d{6})", filename)
    if match:
        return match.groups()
    return None, None


def find_continuous_sequences(mp4_files):
    sorted_files = sorted(mp4_files, key=lambda f: f.name)
    continuous_sequences = []
    non_continuous = []
    current_sequence = []

    for i in range(len(sorted_files)):
        file_path = sorted_files[i]
        start, end = extract_timestamps(file_path.name)

        if not start or not end:
            continue

        if not current_sequence:
            current_sequence.append(file_path)
        else:
            prev_start, prev_end = extract_timestamps(current_sequence[-1].name)
            if prev_end == start:
                current_sequence.append(file_path)
            else:
                if len(current_sequence) > 1:
                    continuous_sequences.append(current_sequence)
                else:
                    non_continuous.extend(current_sequence)
                current_sequence = [file_path]

    if len(current_sequence) > 1:
        continuous_sequences.append(current_sequence)
    else:
        non_continuous.extend(current_sequence)

    return continuous_sequences, non_continuous


def main(input_dir):
    mp4_files = list(input_dir.rglob("*.mp4"))
    print(f"Found {len(mp4_files)} mp4 files in {input_dir}")

    continuous_sequences, non_continuous = find_continuous_sequences(mp4_files)

    print("\nContinuous Sequences:")
    to_keep = []
    for seq in continuous_sequences:
        for f in seq:
            print(f)
            to_keep.append(f)

    # print("\nNon-Continuous Files:")
    # for p in non_continuous:
    #     print(str(p))

    non_conti_no_dup = remove_overlap(non_continuous)
    print("LAST:")
    if len(non_continuous) > 0:
        last = non_continuous[-1]
        print(last, get_filesize(last))
        to_keep.append( non_continuous[-2])
        to_keep.append(last)

    to_keep_no_dup = remove_overlap(to_keep)
    print("TO KEEP:")
    for f in to_keep_no_dup:
        print(f, get_filesize(f))

    cpt_keep = 0
    cpt_move = 0
    for video in mp4_files:
        if video in to_keep_no_dup:
            print(f"keep {video} {get_filesize(video)}")
            cpt_keep += 1
            continue
        print(f"move {video}")
        cpt_move += 1
        move_path =  Path(video.as_posix().replace('cctvnet', 'archive'))
        out_dir = move_path.parent
        out_dir.mkdir(parents=True, exist_ok=True)
        video.rename(move_path)

    print(f"cpt_keep={cpt_keep} cpt_move={cpt_move}")

    return continuous_sequences, non_continuous

def get_filesize(file_path):
    size_in_bytes = file_path.stat().st_size
    size_in_mb = size_in_bytes / (1024 * 1024)
    return size_in_mb

def parse_times(filename):
    name = filename.stem
    start_str, end_str = name.split('_')
    fmt = "%Y%m%dT%H%M%S"
    start = datetime.strptime(start_str, fmt)
    end = datetime.strptime(end_str, fmt)
    duration = (end - start).total_seconds()
    return start_str, duration, filename


def remove_overlap(file_list):
    # Group by start time and pick the longest duration
    grouped = defaultdict(list)
    for f in file_list:
        start_str, duration, path = parse_times(f)
        grouped[start_str].append((duration, path))

    # Select the longest duration file per start time
    longest_files = []
    for start_str, entries in grouped.items():
        longest = max(entries, key=lambda x: x[0])  # max by duration
        longest_files.append(longest[1])

    return longest_files


if __name__ == "__main__":

    dates = ["2025Apr02", "2025Apr03", "2025Apr04", "2025Apr05", "2025Apr06", "2025Apr07", "2025Apr08", "2025Apr09",
             "2025Apr10", "2025Apr11", "2025Apr12", "2025Apr13", "2025Apr14", "2025Apr15"]
    #ips = ['66.33', '66.1', '66.139', '66.133', '66.130', '66.128']
    ips = ["66.34"]
    for ip in ips:
        for date in dates:
            main(Path(f"/mnt/storage/cctvnet/{ip}/{date}"))
