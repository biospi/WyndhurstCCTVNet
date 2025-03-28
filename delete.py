from pathlib import Path
from datetime import datetime, timedelta
import time

SKIP = ['66.138', '66.28']

def delete_old_videos(base_path: str):
    """
    Deletes video files in subdirectories older than 7 days from the current date.

    :param base_path: Base directory containing camera subdirectories with timestamped folders.
    """
    base_dir = Path(base_path)
    cutoff_datetime = datetime.now() - timedelta(days=7*2)
    cutoff_datetime = datetime(2025,2,6)

    if not base_dir.exists() or not base_dir.is_dir():
        print(f"Invalid base path: {base_path}")
        return

    # Iterate over camera subdirectories (e.g., "66.139")
    for camera_dir in base_dir.iterdir():
        if not camera_dir.is_dir():
            continue  # Skip non-directory files

        if camera_dir.name in SKIP:
            continue

        # Iterate over timestamped subdirectories (e.g., "04Jan2025")
        for timestamp_dir in camera_dir.iterdir():
            try:
                # Extract and validate timestamp from directory name
                dir_date = datetime.strptime(timestamp_dir.name, "%Y%b%d")
            except ValueError:
                try:
                    dir_date = datetime.strptime(timestamp_dir.name, "%d%b%Y")
                except ValueError:
                    continue

            # Skip directories with dates within the last 7 days
            if dir_date >= cutoff_datetime:
                continue

            # Look for a "videos" folder inside the timestamped directory
            videos_dir = timestamp_dir / "videos"
            if videos_dir.exists() and videos_dir.is_dir():
                for video in videos_dir.glob("*.mp4"):
                    try:
                        print(f"Deleting {video}")
                        video.unlink()  # Delete the video file
                    except Exception as e:
                        print(f"Error deleting file {video}: {e}")
            else:
                for video in timestamp_dir.glob("*.mp4"):
                    try:
                        print(f"Deleting {video}")
                        video.unlink()  # Delete the video file
                    except Exception as e:
                        print(f"Error deleting file {video}: {e}")


if __name__ == "__main__":
    base_path = "/mnt/storage/cctv/"

    # Run the cleanup periodically (every 24 hours)
    while True:
        print(f"Running cleanup at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        delete_old_videos(base_path)
        print("Cleanup completed. Next run in 24 hours.")
        time.sleep(86400)  # Sleep for 24 hours (86400 seconds)

# from pathlib import Path
# from datetime import datetime
#
#
# def delete_old_videos(base_path: str, cutoff_date: str):
#     """
#     Deletes video files in subdirectories with timestamps earlier than the given cutoff date.
#
#     :param base_path: Base directory containing camera subdirectories with timestamped folders.
#     :param cutoff_date: The cutoff date in the format 'DDMMMYYYY' (e.g., '01Jan2025').
#     """
#     base_dir = Path(base_path)
#     cutoff_datetime = datetime.strptime(cutoff_date, "%d%b%Y")
#
#     if not base_dir.exists() or not base_dir.is_dir():
#         print(f"Invalid base path: {base_path}")
#         return
#
#     # Iterate over camera subdirectories (e.g., "66.139")
#     for camera_dir in base_dir.iterdir():
#         if not camera_dir.is_dir():
#             continue  # Skip non-directory files
#
#         # Iterate over timestamped subdirectories (e.g., "04Jan2025")
#         for timestamp_dir in camera_dir.iterdir():
#             try:
#                 # Extract and validate timestamp from directory name
#                 dir_date = datetime.strptime(timestamp_dir.name, "%d%b%Y")
#             except ValueError:
#                 continue  # Skip directories without valid date names
#
#             # Skip directories with dates on or after the cutoff date
#             if dir_date >= cutoff_datetime:
#                 continue
#
#             # Look for a "videos" folder inside the timestamped directory
#             videos_dir = timestamp_dir / "videos"
#             if videos_dir.exists() and videos_dir.is_dir():
#                 for video in videos_dir.glob("*.mp4"):
#                     try:
#                         print(f"Deleting {video}")
#                         video.unlink()  # Delete the video file
#                     except Exception as e:
#                         print(f"Error deleting file {video}: {e}")
#
#
# if __name__ == "__main__":
#     # Example usage:
#     base_path = "/mnt/storage/cctv/"
#     cutoff_date = "23Jan2025"
#     delete_old_videos(base_path, cutoff_date)
