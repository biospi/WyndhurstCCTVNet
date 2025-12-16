import json

import cv2
import base64
import io
from PIL import Image
import numpy as np
from pathlib import Path

drawing = False
points = []
selected_point_idx = None
point_radius = 6

def click_event(event, x, y, flags, param):
    global points, selected_point_idx

    if event == cv2.EVENT_LBUTTONDOWN:
        # Check if user clicked near an existing point to drag
        for i, pt in enumerate(points):
            if (pt[0] - x) ** 2 + (pt[1] - y) ** 2 < point_radius ** 2:
                selected_point_idx = i
                return
        # Else, add a new point
        points.append((x, y))

    elif event == cv2.EVENT_MOUSEMOVE and selected_point_idx is not None:
        # While dragging, update the selected point
        points[selected_point_idx] = (x, y)

    elif event == cv2.EVENT_LBUTTONUP:
        selected_point_idx = None  # Stop dragging

def draw_polygon(img, points):
    if len(points) > 1:
        for i in range(len(points) - 1):
            cv2.line(img, points[i], points[i+1], (0, 255, 0), 2)
        if len(points) > 2:
            cv2.line(img, points[-1], points[0], (0, 255, 0), 2)  # close polygon
    for pt in points:
        cv2.circle(img, pt, point_radius, (0, 0, 255), -1)

def mask_to_base64(mask):
    # Convert mask to PIL Image and encode as PNG
    pil_mask = Image.fromarray(mask)
    buffer = io.BytesIO()
    pil_mask.save(buffer, format="PNG")

    # Encode to base64
    b64_str = base64.b64encode(buffer.getvalue()).decode("utf-8")
    print(f"Base64 mask string:\n{b64_str}")


def mask_path_to_base64(mask_path: Path) -> str:
    """
    Reads a mask image from the given path and returns its Base64-encoded PNG string.
    """
    # Open mask as grayscale (L mode) to ensure consistent encoding
    mask_image = Image.open(mask_path).convert("L")

    # Save to an in-memory buffer as PNG
    buffer = io.BytesIO()
    mask_image.save(buffer, format="PNG")

    # Encode to base64 string
    b64_str = base64.b64encode(buffer.getvalue()).decode("utf-8")
    #print(f"Base64 mask string:\n{b64_str}")
    return b64_str


def main(input_dir: Path, mask_dir: Path):
    data = {}
    mask_files = sorted(list(mask_dir.rglob("*.png")))
    for mask_file in mask_files:
        encoded_str = mask_path_to_base64(mask_file)
        ip = mask_file.stem.split("_")[0]
        data[ip] = encoded_str
    print(data)

    global points
    image_files = sorted(list(input_dir.rglob("*.jpg")))
    print(f"Found {len(image_files)} .jpg files")

    for image_file in image_files:

        mask_dir = input_dir.parent / "masks"
        relative_path = image_file.relative_to(input_dir)
        mask_output_path = mask_dir / relative_path.with_name(image_file.stem + "_mask.png")
        # if mask_output_path.exists():
        #     print(f"Skipping {image_file}")
        #     continue
        # if "44" not in image_file.stem:
        #     continue
        img = cv2.imread(str(image_file))
        img = cv2.resize(img, (img.shape[1] // 2, img.shape[0] // 2))
        clone = img.copy()
        points = []

        cv2.namedWindow("Draw ROI")
        cv2.setMouseCallback("Draw ROI", click_event)
        mask = None

        while True:
            display_img = clone.copy()
            draw_polygon(display_img, points)
            cv2.imshow("Draw ROI", display_img)
            key = cv2.waitKey(1) & 0xFF

            if key == 13:  # Enter key
                if len(points) >= 3:
                    mask = np.zeros(img.shape[:2], dtype=np.uint8)
                    cv2.fillPoly(mask, [np.array(points, dtype=np.int32)], 255)
                    cv2.imshow("Mask", mask)
                else:
                    print("Need at least 3 points for ROI.")

            elif key == ord('s'):
                if mask is not None:
                    # New mask path in a sibling 'masks/' directory
                    mask_dir = input_dir.parent / "masks"
                    relative_path = image_file.relative_to(input_dir)
                    mask_output_path = mask_dir / relative_path.with_name(image_file.stem + "_mask.png")

                    # Ensure directory exists
                    mask_output_path.parent.mkdir(parents=True, exist_ok=True)

                    # Save
                    cv2.imwrite(str(mask_output_path), mask)
                    print(f"Saved mask: {mask_output_path}")

                    # Convert mask to PIL Image and encode as PNG
                    pil_mask = Image.fromarray(mask)
                    buffer = io.BytesIO()
                    pil_mask.save(buffer, format="PNG")

                    # Encode to base64
                    b64_str = base64.b64encode(buffer.getvalue()).decode("utf-8")
                    print(f"Base64 mask string:\n{b64_str}")

                    decode_base64_mask(b64_str)
                    break

            elif key == ord('r'):
                points.clear()
                mask = None
                print("ROI reset.")

            elif key == ord('n'):
                print("Skipping to next image.")
                break

            elif key == ord('q'):
                print("Quitting.")
                cv2.destroyAllWindows()
                return

        cv2.destroyAllWindows()
        print(data)
        return data


def decode_base64_mask(b64_string: str, show: bool = True):
    """Decode a base64 PNG mask string to a NumPy array and optionally display it."""
    # Decode base64 to bytes
    image_data = base64.b64decode(b64_string)
    image = Image.open(io.BytesIO(image_data)).convert("L")  # Ensure grayscale
    mask_np = np.array(image)

    if show:
        cv2.imshow("Decoded Mask", mask_np)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    return mask_np


def export_all_masks_to_json(mask_dir: Path, output_json: Path):
    """
    Finds all binary mask images inside mask_dir and creates a JSON file
    mapping base64 strings to their respective file names (without extension).

    Example format:
    {
        "123": "<base64string>",
        "456": "<base64string>"
    }
    """
    mask_files = sorted(list(mask_dir.rglob("*.png")))
    data = {}

    for mask_file in mask_files:
        b64_str = mask_path_to_base64(mask_file)
        key = mask_file.stem                       # e.g. "123_mask" or "123"
        data[key] = b64_str

    # Save JSON
    output_json.parent.mkdir(parents=True, exist_ok=True)
    with open(output_json, "w") as f:
        json.dump(data, f, indent=4)

    print(f"Saved JSON: {output_json}")
    return data



if __name__ == "__main__":
    # main(Path("/mnt/storage/thumbnails/360"), Path("/mnt/storage/thumbnails/masks_360"))
    mask_dir = Path("/mnt/storage/thumbnails/masks")
    output_json = Path("/mnt/storage/thumbnails/masks/base64_masks.json")

    export_all_masks_to_json(mask_dir, output_json)
