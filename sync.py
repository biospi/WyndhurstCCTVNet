from pathlib import Path
import cv2
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

def add_black_border(image, thickness=10):
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
    mask = mask.astype(np.uint8) * 255  # Convert to binary image
    mask = add_black_border(mask)
    return mask


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

        return image[y:y + h, x:x + w]
    return None  # No green text detected


def show_images_in_column(image_paths, ips, output_path):
    fig, axes = plt.subplots(len(image_paths), 1, figsize=(6, len(image_paths) * 2))
    if len(image_paths) == 1:
        axes = [axes]  # Ensure axes is iterable if only one image

    for ax, image_path, ip in zip(axes, image_paths, ips):
        img = mpimg.imread(image_path)
        ax.imshow(img)
        ax.axis('off')
        ax.set_title(ip, fontsize=10)

    plt.tight_layout()
    print(output_path)
    plt.savefig(output_path, bbox_inches='tight', dpi=300)
    plt.close(fig)


def main(input_dir, output_dir):
    mp4_files = list(input_dir.rglob("*.mp4"))
    images = []
    ips = []
    for video_file in mp4_files:
        date = "20250515"
        time_s = "140000"
        time_e = "140500"
        if f'2025May15/videos/{date}T{time_s}_{date}T{time_e}.mp4' not in video_file.as_posix():
            continue
        ip = video_file.parent.parent.parent.name.split('.')[-1]
        print(f"Reading video: {video_file.name}")
        cap = cv2.VideoCapture(str(video_file))

        if not cap.isOpened():
            print(f"Failed to open video: {video_file}")
            continue

        while True:
            ret, frame = cap.read()
            if not ret or frame is None:
                break

            cropped = crop_to_green_text(frame)
            if cropped is not None:
                cv2.imshow("Cropped Green Text", cropped)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            output_dir.mkdir(parents=True, exist_ok=True)
            filepath = output_dir / f"{ip}_{date}_{time_s}.png"
            cv2.imwrite(filepath.as_posix(), cropped)
            images.append(filepath.as_posix())
            ips.append(ip)
            break

    #create figure with subplot
    if len(images) == 0:
        print(f"No videos found in {input_dir}")
        return
    output_figure = output_dir / f"{date}_{time_s}.png"
    show_images_in_column(images, ips, output_figure)


if __name__ == "__main__":
    input_dir = Path("/mnt/storage/cctvnet")
    output_dir = Path("/home/fo18103/Pictures/output")
    main(input_dir, output_dir)
