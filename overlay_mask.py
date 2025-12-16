from pathlib import Path
import cv2
import numpy as np

def overlay_mask_on_image(image_path, mask_path, output_path, alpha=0.5, contour_thickness=3):
    # Read image (BGR)
    image = cv2.imread(str(image_path))
    if image is None:
        print(f"Could not read image: {image_path}")
        return

    # Read mask (grayscale)
    mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
    if mask is None:
        print(f"Could not read mask: {mask_path}")
        return
    # Resize mask to match image size
    mask = cv2.resize(mask, (image.shape[1], image.shape[0]), interpolation=cv2.INTER_NEAREST)

    # Ensure mask is binary (0 or 255)
    _, mask_bin = cv2.threshold(mask, 127, 255, cv2.THRESH_BINARY)

    # Create a yellow overlay (BGR = (0, 255, 255))
    overlay = image.copy()
    overlay[mask_bin == 255] = (0, 255, 255)

    # Blend overlay with image
    blended = cv2.addWeighted(overlay, alpha, image, 1 - alpha, 0)

    # Find and draw contours (borders)
    contours, _ = cv2.findContours(mask_bin, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(blended, contours, -1, (0, 0, 255), contour_thickness)

    # Save output
    cv2.imwrite(str(output_path), blended)
    print(f"Saved overlay: {output_path}")


def main(input_dir):
    print("Start overlay generation...")
    images = sorted(input_dir.rglob("*.jpg"))
    masks = sorted(input_dir.rglob("*.png"))

    for image, mask in zip(images, masks):
        print(f"Processing image: {image.name}, mask: {mask.name}")
        out_file = image.parent / f"{image.stem}_overlay.png"
        overlay_mask_on_image(image, mask, out_file)


if __name__ == "__main__":
    main(Path("dewarp"))
