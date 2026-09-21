#!/usr/bin/env python3
"""
Highlight Rectangle Engine — Slice TB-010

Draws semi-transparent highlight rectangles behind text at specified coordinates.

Usage:
    python3 highlight_rect.py <image_path> <ocr_json> <click_x> <click_y> [--padding 20] [--color 255,255,0] [--output output.png]

Output:
    Layered image with highlight rectangle centered on text.

Hard gate: Must not affect foreground text sharpness.
"""

import argparse
import json
import os
import sys

import cv2
import numpy as np


def load_ocr_data(json_path: str) -> list[dict]:
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def find_word_at_coordinate(ocr_data, click_x, click_y):
    for word_info in ocr_data:
        x, y, w, h = word_info["box"]
        if x <= click_x < x + w and y <= click_y < y + h:
            return word_info
    return None


def find_word_group(ocr_data, clicked_word):
    clicked = clicked_word["box"]
    cx, cy, cw, ch = clicked
    clicked_y_center = cy + ch / 2
    group = []
    for word_info in ocr_data:
        w = word_info["box"]
        wx, wy, ww, wh = w
        w_y_center = wy + wh / 2
        if abs(w_y_center - clicked_y_center) < ch * 0.5:
            group.append(word_info)
    group.sort(key=lambda x: x["box"][0])
    return group


def draw_highlight(
    image_path: str,
    group: list[dict],
    padding: int = 20,
    color: tuple = (255, 255, 0),
    opacity: float = 0.5,
    output_path: str = "highlighted.png",
) -> str:
    """Draw a semi-transparent highlight rectangle around text group."""
    img = cv2.imread(image_path).copy()
    if img is None:
        raise ValueError(f"Cannot read image: {image_path}")

    x_min = min(w["box"][0] for w in group) - padding
    y_min = min(w["box"][1] for w in group) - padding
    x_max = max(w["box"][0] + w["box"][2] for w in group) + padding
    y_max = max(w["box"][1] + w["box"][3] for w in group) + padding

    # Ensure positive dimensions
    x_min = max(0, x_min)
    y_min = max(0, y_min)
    x_max = min(img.shape[1], x_max)
    y_max = min(img.shape[0], y_max)

    if x_max <= x_min or y_max <= y_min:
        raise ValueError("Bounding box has zero or negative dimensions.")

    # Create highlight overlay
    overlay = img.copy()
    # BGR color for OpenCV
    overlay[y_min:y_max, x_min:x_max] = color

    # Blend with original
    result = cv2.addWeighted(overlay, opacity, img, 1 - opacity, 0)

    cv2.imwrite(output_path, result)
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Draw highlight rectangle around selected text.")
    parser.add_argument("image_path", help="Input image path")
    parser.add_argument("ocr_json", help="OCR JSON file")
    parser.add_argument("click_x", type=int, help="Click X coordinate")
    parser.add_argument("click_y", type=int, help="Click Y coordinate")
    parser.add_argument("--padding", "-p", type=int, default=20, help="Padding around text. Default: 20")
    parser.add_argument("--color", "-c", type=str, default="255,255,0", help="Highlight color RGB. Default: 255,255,0")
    parser.add_argument("--opacity", type=float, default=0.5, help="Overlay opacity 0-1. Default: 0.5")
    parser.add_argument("--output", "-o", default="highlighted.png", help="Output file path")
    args = parser.parse_args()

    if not os.path.isfile(args.image_path):
        print(f"Error: Image not found: {args.image_path}", file=sys.stderr)
        sys.exit(1)
    if not os.path.isfile(args.ocr_json):
        print(f"Error: OCR JSON not found: {args.ocr_json}", file=sys.stderr)
        sys.exit(1)

    color = tuple(int(x) for x in args.color.split(","))
    if len(color) != 3 or not all(0 <= c <= 255 for c in color):
        print("Error: Color must be RGB values 0-255.", file=sys.stderr)
        sys.exit(1)

    try:
        ocr_data = load_ocr_data(args.ocr_json)
        clicked_word = find_word_at_coordinate(ocr_data, args.click_x, args.click_y)
        if not clicked_word:
            print(f"Error: No word found at ({args.click_x}, {args.click_y})", file=sys.stderr)
            sys.exit(1)

        group = find_word_group(ocr_data, clicked_word)
        out = draw_highlight(args.image_path, group, args.padding, color, args.opacity, args.output)
        print(f"Highlight saved to: {out}", file=sys.stderr)
        print(f"Group: {len(group)} word(s)", file=sys.stderr)
    except (ValueError, cv2.error) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
