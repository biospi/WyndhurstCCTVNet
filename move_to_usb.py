import shutil
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm


def extract_times_from_filename(filename: Path):
    try:
        name = filename.stem
        split = name.split('_')
        start_str, end_str = split[0], split[1]
        start_time = datetime.strptime(start_str, "%Y%m%dT%H%M%S")
        end_time = datetime.strptime(end_str, "%Y%m%dT%H%M%S")
        return start_time, end_time
    except Exception as e:
        print(e)
        return None, None


def move_file(file: Path, input_dir: Path, output_root: Path):
    try:
        relative_path = file.relative_to(input_dir)
        destination_file = output_root / relative_path
        destination_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(file), str(destination_file))
        return True
    except Exception as e:
        print(e)
        return False


def main(input_dir: Path, start_time_str: str, end_time_str: str, output_root: Path):
    start_time = datetime.strptime(start_time_str, "%Y%m%dT%H%M%S")
    end_time = datetime.strptime(end_time_str, "%Y%m%dT%H%M%S")

    mp4_files = list(input_dir.rglob("*.mp4"))

    filtered_files = []
    for f in mp4_files:
        start, end = extract_times_from_filename(f)
        if start and end and end >= start_time and start <= end_time:
            filtered_files.append(f)

    total_files = len(filtered_files)
    print(f"Moving {total_files} video(s)...")

    # Progress bar
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {
            executor.submit(move_file, f, input_dir, output_root): f
            for f in filtered_files
        }
        for _ in tqdm(as_completed(futures), total=total_files, desc="Moving files"):
            pass


if __name__ == "__main__":
    main(
        input_dir=Path("/mnt/storage/cctvnet"),
        start_time_str="20250101T000000",
        end_time_str="20250730T000000",
        output_root=Path("/mnt/usb_storage/cctvnet")
    )
