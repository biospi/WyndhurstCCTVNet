from pathlib import Path
import re


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
    for seq in continuous_sequences:
        print([str(p) for p in seq])

    print("\nNon-Continuous Files:")
    for p in non_continuous:
        print(str(p))

    return continuous_sequences, non_continuous


if __name__ == "__main__":
    input_dir = Path("/mnt/storage/cctvnet/66.1/2025Mar30")
    main(input_dir)
