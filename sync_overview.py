from pathlib import Path
import cv2
import numpy as np
import pandas as pd
import pytesseract
from datetime import datetime


def remove_noise_gaussian(image):
    return cv2.GaussianBlur(image, (5, 5), 0)  # (5, 5) is the kernel size


def downscale_by(factor, image: np.ndarray) -> np.ndarray:
    height, width = image.shape[:2]
    new_size = (width // factor, height // factor)
    downscaled = cv2.resize(image, new_size, interpolation=cv2.INTER_AREA)
    return downscaled


# def extract_green_text(image):
#     b, g, r = cv2.split(image)
#     mask = (g > 150) & (r < 50) & (b < 50)
#     result = np.zeros_like(image)
#     result[mask] = image[mask]
#     return result

def add_black_border(image, thickness=0):
    return cv2.copyMakeBorder(
        image,
        thickness,
        thickness,
        thickness,
        thickness,
        cv2.BORDER_CONSTANT,
        value=(0, 0, 0)
    )


def extract_green_text(image):
    b, g, r = cv2.split(image)
    mask = (g > 150) & (r < 50) & (b < 50)
    result = np.zeros_like(image)
    result[mask] = image[mask]
    mask = mask.astype(np.uint8) * 255  # Convert to binary image
    #mask = add_black_border(mask)
    kernel = np.ones((3, 3), np.uint8)
    dilated_mask = cv2.dilate(mask, kernel, iterations=1)
    eroded_mask = cv2.erode(dilated_mask, kernel, iterations=1)
    return eroded_mask


def crop_to_green_text(image):
    mask = extract_green_text(image)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if contours:
        # Merge all character bounding boxes into one
        x_min = min(cv2.boundingRect(c)[0] for c in contours)
        y_min = min(cv2.boundingRect(c)[1] for c in contours)
        x_max = max(cv2.boundingRect(c)[0] + cv2.boundingRect(c)[2] for c in contours)
        y_max = max(cv2.boundingRect(c)[1] + cv2.boundingRect(c)[3] for c in contours)

        # Optionally add padding
        pad = 10
        x = max(0, x_min - pad)
        y = max(0, y_min - pad)
        w = min(image.shape[1] - x, (x_max - x_min) + 2 * pad)
        h = min(image.shape[0] - y, (y_max - y_min) + 2 * pad)

        return mask[y:y + h, x:x + w]
    return None  # No green text detected


def read_videos_from_folder(input_folder: Path):
    video_files = list(input_folder.glob("*.mp4"))
    if not video_files:
        print(f"No .mp4 files found in {input_folder}")
        return

    timestamp_frame_counter = {}  # Dictionary to store counters for each unique timestamp

    for video_file in video_files:
        # if "20250521T100000_20250521T100500.mp4" not in video_file.as_posix():
        #     continue

        print(f"Reading video: {video_file.name}")
        cap = cv2.VideoCapture(str(video_file))

        if not cap.isOpened():
            print(f"Failed to open video: {video_file}")
            continue

        frame_count = 0
        while True:
            ret, frame = cap.read()
            if frame is None:
                continue

            cropped = crop_to_green_text(frame)
            cropped = cropped[:, 60:]

            if not ret:
                break  # End of video

            frame_count += 1
            #gray = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)
            gray = cv2.bitwise_not(cropped)

            cropped = cv2.adaptiveThreshold(gray, 255,
                                           cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                           cv2.THRESH_BINARY, 11, 2)
            cropped = remove_noise_gaussian(cropped)
            cv2.imshow("Frame", cropped)
            if frame_count > 1000:
                break
            print("Image to string...")
            text = pytesseract.image_to_string(cropped, config='--psm 7')
            print(text.replace('\n', ''))

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            # Use the timestamp as the base of the filename
            timestamp = text.replace(':', '_').replace('-', '_').replace(' ', 'T').strip()
            frame_dir = input_folder / "frames"
            frame_dir.mkdir(exist_ok=True, parents=True)

            # Update the counter for the timestamp
            if timestamp not in timestamp_frame_counter:
                timestamp_frame_counter[timestamp] = 0  # Initialize counter for the new timestamp
            timestamp_frame_counter[timestamp] += 1  # Increment counter for each new frame with the same timestamp

            # Use the timestamp and frame counter to create the filename
            filename = f"{timestamp}_{timestamp_frame_counter[timestamp]:03}.png"
            filepath = frame_dir / filename

            # Downscale and save the frame
            frame = downscale_by(2, frame)
            print(filepath)
            cv2.imwrite(filepath.as_posix(), frame)

        cap.release()
        print(f"Total frames read: {frame_count}")

    # cv2.destroyAllWindows()  # Uncomment if using cv2.imshow


def parse_datetime(date_str):
    for fmt in ("%Y%m%dT%H%M%S", "%Y%m%d%H%M%S"):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            pass
    raise ValueError(f"Time data '{date_str}' does not match expected formats.")


def main():
    mp4_files = list(Path("/mnt/storage/cctvnet/").rglob("*.mp4"))
    print(f"Found {len(mp4_files)} files.")
    for file in mp4_files:
        print(f"{file}")
        break
    df = pd.DataFrame(mp4_files, columns=['FilePath'])

    df["dates"] = [x.stem for x in mp4_files]
    df["s_dates"] = [parse_datetime(x.stem.split('_')[0]) for x in mp4_files]
    df["f_dates"] = [parse_datetime(x.stem.split('_')[1]) for x in mp4_files]

    df["ip"] = [x.parent.parent.parent.name if 'videos' in str(x) else x.parent.parent.name for x in mp4_files]
    print(df)
    # Group by start timestamp and collect file paths
    grouped = df.groupby("s_dates")["FilePath"].apply(list).reset_index()

    grouped = grouped.sort_values("s_dates")

    # Example: iterate over synchronized groups
    for _, row in grouped.iterrows():
        timestamp = row["s_dates"]
        video_paths = row["FilePath"]
        if len(video_paths) < 10:
            continue
        print(f"\nTimestamp: {timestamp}")
        for path in video_paths:
            print(f"  {path}")
    # read_videos_from_folder( Path("C:/Users/fo18103/Downloads/synchronisation test/23/2025May21/videos"))
    # read_videos_from_folder( Path("C:/Users/fo18103/Downloads/synchronisation test/24/2025May21/videos"))
    # read_videos_from_folder( Path("C:/Users/fo18103/Downloads/synchronisation test/27/2025May21/videos"))
    # read_videos_from_folder( Path("C:/Users/fo18103/Downloads/synchronisation test/25/2025May21/videos"))


if __name__ == "__main__":
    main()
