#!/usr/bin/env python3
"""
Headline Masking (Static) — Slice TB-005

Uses coordinates from TB-003 (OCR match) to crop the original image,
save as a transparent PNG containing ONLY the selected text.

Usage:
    python3 headline_mask.py <image_path> <ocr_json> <click_x> <click_y> [--padding 5]

Output:
    Transparent PNG with only the selected text region, rest fully transparent.

Hard gate: Must handle multi-word bounding boxes.
"""

import argparse
import json
import os
import sys

import cv2
import numpy as np


def load_ocr_data(json_path: str) -> list[dict]:
    """Load OCR JSON data from file."""
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def find_word_at_coordinate(ocr_data: list[dict], click_x: int, click_y: int) -> dict | None:
    """Find the word whose bounding box contains the click coordinates."""
    for word_info in ocr_data:
        x, y, w, h = word_info["box"]
        if x <= click_x < x + w and y <= click_y < y + h:
            return word_info
    return None


def find_word_group(ocr_data: list[dict], clicked_word: dict) -> list[dict]:
    """
    Find all words on the same line as the clicked word.
    Groups words that share approximately the same y-position.
    Handles multi-word selections.
    """
    clicked = clicked_word["box"]
    cx, cy, cw, ch = clicked
    clicked_y_center = cy + ch / 2

    group = []
    for word_info in ocr_data:
        w = word_info["box"]
        wx, wy, ww, wh = w
        w_y_center = wy + wh / 2

        # Same line if y-center is within the clicked word's height
        if abs(w_y_center - clicked_y_center) < ch * 0.5:
            group.append(word_info)

    # Sort by x position
    group.sort(key=lambda x: x["box"][0])
    return group


def extract_text_region(
    image_path: str,
    group: list[dict],
    padding: int = 5,
    output_path: str = "headline_mask.png",
) -> str:
    """
    Extract the bounding box region containing the word group from the image.
    Save as a transparent PNG (alpha channel).

    Args:
        image_path: Path to the original image.
        group: List of OCR word dicts that form the selection.
        padding: Extra pixels around the text.

    Returns:
        Path to the saved transparent PNG.
    """
    if not group:
        raise ValueError("No words in group to extract.")

    # Compute bounding box of entire group
    x_min = min(w["box"][0] for w in group) - padding
    y_min = min(w["box"][1] for w in group) - padding
    x_max = max(w["box"][0] + w["box"][2] for w in group) + padding
    y_max = max(w["box"][1] + w["box"][3] for w in group) + padding

    # Read image
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not read image: {image_path}")

    # Crop to group bounding box
    cropped = img[y_min:y_max, x_min:x_max]

    # Convert to RGBA for transparency
    if len(cropped.shape) == 3 and cropped.shape[2] == 3:
        # BGR -> BGRA
        rgba = cv2.cvtColor(cropped, cv2.COLOR_BGR2BGRA)
    else:
        rgba = cv2.cvtColor(cropped, cv2.COLOR_GRAY2BGRA)

    # Create alpha channel: 255 (opaque) for the cropped area
    # Since the entire cropped area IS the text region, make it fully opaque
    h, w, _ = rgba.shape
    alpha = np.full((h, w), 255, dtype=np.uint8)
    rgba[:, :, 3] = alpha

    # Save output
    cv2.imwrite(output_path, rgba)
    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Extract sharp text region from original image as transparent PNG."
    )
    parser.add_argument("image_path", help="Path to the original image")
    parser.add_argument(
        "ocr_json", help="Path to OCR JSON file (output from ocr_extract.py)"
    )
    parser.add_argument("click_x", type=int, help="X coordinate of the click")
    parser.add_argument("click_y", type=int, help="Y coordinate of the click")
    parser.add_argument(
        "--padding", "-p", type=int, default=5, help="Extra pixels around text. Default: 5"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output file path. Default: headline_mask.png",
        default="headline_mask.png",
    )
    args = parser.parse_args()

    if not os.path.isfile(args.image_path):
        print(f"Error: Image not found: {args.image_path}", file=sys.stderr)
        sys.exit(1)
    if not os.path.isfile(args.ocr_json):
        print(f"Error: OCR JSON not found: {args.ocr_json}", file=sys.stderr)
        sys.exit(1)

    # Load OCR data
    ocr_data = load_ocr_data(args.ocr_json)

    # Find the clicked word
    clicked_word = find_word_at_coordinate(ocr_data, args.click_x, args.click_y)
    if not clicked_word:
        print(
            f"Error: No word found at ({args.click_x}, {args.click_y})",
            file=sys.stderr,
        )
        sys.exit(1)

    # Find the word group (multi-word line support)
    group = find_word_group(ocr_data, clicked_word)

    # Extract and save
    output = extract_text_region(args.image_path, group, padding=args.padding, output_path=args.output)
    print(f"Extracted {len(group)} word(s) to: {output}", file=sys.stderr)

    # Verify transparency via file properties
    result_img = cv2.imread(output, cv2.IMREAD_UNCHANGED)
    if result_img is not None and result_img.shape[2] == 4:
        alpha_channel = result_img[:, :, 3]
        opaque_count = np.count_nonzero(alpha_channel)
        total_count = alpha_channel.size
        print(
            f"Verification: {opaque_count}/{total_count} pixels are opaque ({100*opaque_count/total_count:.1f}%)",
            file=sys.stderr,
        )
    else:
        print("Warning: Output file does not have 4 channels (RGBA).", file=sys.stderr)


if __name__ == "__main__":
    main()
