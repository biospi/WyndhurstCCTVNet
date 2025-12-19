import re
from datetime import datetime
import cv2
import numpy as np
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import pytesseract
import subprocess
from collections import Counter
from datetime import datetime, timedelta
from collections import defaultdict
from typing import List

pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'
print(pytesseract.get_tesseract_version())


def analyze_fps_and_milliseconds(timestamp_list: List[str]):
    """
    Given a list of OCR timestamps (strings), calculate the FPS
    and assign a millisecond-accurate timestamp to each frame.

    Returns:
        fps: float
        frame_timestamps: List[datetime] for each frame
    """
    if not timestamp_list:
        return None, []

    # Convert to datetime objects (ignore milliseconds if OCR doesn't provide)
    dt_list = [datetime.strptime(ts, "%Y-%m-%d %H:%M:%S") for ts in timestamp_list]

    # Count how many frames per second
    second_frame_counts = defaultdict(int)
    for dt in dt_list:
        second_frame_counts[dt.second] += 1

    # Sort seconds in order
    sorted_seconds = sorted(second_frame_counts.keys())
    frame_counts = [second_frame_counts[s] for s in sorted_seconds]

    # Approximate FPS: average frames per second across first second-change intervals
    fps_estimates = []
    for count in frame_counts:
        fps_estimates.append(count)
    fps = sum(fps_estimates) / len(fps_estimates)

    # Assign millisecond timestamp to each frame
    frame_timestamps = []
    second_start_idx = 0
    n = len(dt_list)
    while second_start_idx < n:
        current_second = dt_list[second_start_idx].second
        # Find end of this second
        second_end_idx = second_start_idx
        while second_end_idx < n and dt_list[second_end_idx].second == current_second:
            second_end_idx += 1
        frames_in_this_second = second_end_idx - second_start_idx
        if frames_in_this_second == 0:
            frames_in_this_second = 1

        # Duration per frame in milliseconds
        frame_delta = timedelta(seconds=1) / frames_in_this_second

        for i in range(frames_in_this_second):
            frame_ts = dt_list[second_start_idx] + frame_delta * i
            frame_timestamps.append(frame_ts)

        second_start_idx = second_end_idx

    # Return approximate FPS and per-frame timestamps
    return fps, frame_timestamps



def get_valid_start_timestamp(timestamp_list):
    """
    Analyze OCR timestamps and determine a valid start timestamp.
    If the first one seems wrong, pick the most frequent or earliest valid timestamp.
    """
    valid_timestamps = [ts for ts in timestamp_list if ts is not None]
    if not valid_timestamps:
        raise ValueError("No valid OCR timestamps found.")

    # Count frequency to handle OCR glitches
    counter = Counter(valid_timestamps)
    most_common, count = counter.most_common(1)[0]

    # If the first frame's timestamp matches the most common, use it
    if timestamp_list[0] == most_common:
        return most_common
    else:
        # Otherwise, pick the most common as likely correct start
        print(f"First OCR timestamp '{timestamp_list[0]}' seems inconsistent. Using most common: {most_common}")
        return most_common


def inject_timestamp_to_metadata(video_file: Path, timestamp: str, fps=float):
    """
    Injects a timestamp into the video metadata (creation_time) without re-encoding.
    """
    output_file = video_file.with_name(video_file.stem + "_with_timestamp" + video_file.suffix)

    comment_str = f"start_timestamp={timestamp}, fps={fps:.3f}"

    ffmpeg_cmd = [
        "ffmpeg",
        "-i", str(video_file),
        "-metadata", f"comment={comment_str}",
        "-codec", "copy",
        str(output_file)
    ]

    print("Running FFmpeg command:", " ".join(ffmpeg_cmd))

    result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("FFmpeg error:", result.stderr)
        return None
    print("Timestamp injected successfully:", output_file)
    return output_file


def repair_ocr_timestamp(text):
    """
    Repairs OCR-detected timestamps like '2025-09-12 09:39:50'
    """
    if not text:
        return None

    text = text.strip().replace('\n', '').replace('\r', '')
    text = text.replace('—', '-').replace('_', '-').replace('.', ':').replace(',', ':')
    text = text.replace('O', '0').replace('o', '0').replace('I', '1').replace('l', '1')

    # Try parsing normally first
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y_%m_%d_%H_%M_%S", "%Y/%m/%d %H:%M:%S"):
        try:
            dt = datetime.strptime(text, fmt)
            if 2000 <= dt.year <= 2100:
                return dt
        except ValueError:
            pass

    # Remove any leading junk before plausible year
    m = re.search(r'(20\d{2}[-_/]?\d{1,2}[-_/]?\d{1,2}.*)', text)
    if m:
        text = m.group(1)

    # Extract digits only for fallback parse
    digits = re.sub(r'\D', '', text)
    if len(digits) < 12:
        return None

    # Guess structure
    if len(digits) >= 14:
        y, mo, d, H, M, S = digits[:4], digits[4:6], digits[6:8], digits[8:10], digits[10:12], digits[12:14]
    else:
        # Missing seconds → assume 00
        y, mo, d, H, M, S = digits[:4], digits[4:6], digits[6:8], digits[8:10], digits[10:12], "00"

    try:
        year = int(y)
        # 🔹 Simple fix: if year out of range, assume OCR misread '2' as '5' etc.
        if not (2000 <= year <= 2100):
            if str(year).startswith(('5', '3', '8', '0', '9')):
                year = int('2' + str(year)[1:])  # e.g., 5025 → 2025
            else:
                year = 2025  # fallback to current known range

        # Clamp all other fields
        month = max(1, min(12, int(mo)))
        day = max(1, min(31, int(d)))
        hour = max(0, min(23, int(H)))
        minute = max(0, min(59, int(M)))
        second = max(0, min(59, int(S)))

        return datetime(year, month, day, hour, minute, second)
    except Exception:
        return None


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


def repair_video_timestamp(video_file: Path):
    timestamp_frame_counter = {}  # Dictionary to store counters for each unique timestamp

    print(f"Reading video: {video_file.name}")
    cap = cv2.VideoCapture(str(video_file))

    if not cap.isOpened():
        print(f"Failed to open video: {video_file}")
        return

    frame_count = 0
    timestamp_list = []
    while True:
        ret, frame = cap.read()
        if frame is None:
            continue

        cropped = crop_to_green_text(frame)
        cropped = cropped[:, 0:]

        if not ret:
            break  # End of video

        frame_count += 1
        #gray = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)
        gray = cv2.bitwise_not(cropped)

        cropped = cv2.adaptiveThreshold(gray, 255,
                                       cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                       cv2.THRESH_BINARY, 11, 2)
        cropped = remove_noise_gaussian(cropped)
        #cv2.imshow("Frame", cropped)
        if frame_count > 30:
            break
        print("Image to string...")
        text = pytesseract.image_to_string(cropped, config='--psm 7')
        print(text.replace('\n', ''))
        text_repaired = repair_ocr_timestamp(text)
        text_repaired = text_repaired.strftime("%Y-%m-%d %H:%M:%S")
        print("repaired:", text_repaired)
        timestamp_list.append(text_repaired)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    print(f"Total frames read: {frame_count}")
    print("OCR timestamps:", timestamp_list)
    print(timestamp_list)
    fps, frame_timestamps = analyze_fps_and_milliseconds(timestamp_list)
    print("Estimated FPS:", fps)
    ts = frame_timestamps[0].strftime("%Y-%m-%d %H:%M:%S.%f")
    print("Frame timestamps with milliseconds:", )
    #start_timestamp = get_valid_start_timestamp(timestamp_list)
    print(inject_timestamp_to_metadata(video_file, ts, fps))


if __name__ == "__main__":
    repair_video_timestamp(Path("/mnt/storage/cctvnet/66.26/2025Sep12/videos/20250912T050000_20250912T050500.mp4"))





