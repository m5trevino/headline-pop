#!/usr/bin/env python3
"""
OCR Coordinate Extraction — Slice TB-001

CLI tool that loads an image, runs Tesseract OCR, and outputs
structured JSON with every detected word and its bounding box
(x, y, width, height) in pixel space.

Usage:
    python3 ocr_extract.py <image_path> [--output <output_path>]
    python3 ocr_extract.py image.png

Output:
    - JSON file (same name as input, .json extension)
    - JSON also printed to stdout
"""

import argparse
import json
import os
import sys

import pytesseract
from PIL import Image


def extract_ocr_data(image_path: str) -> list[dict]:
    """Run Tesseract OCR on an image and return structured word+box data."""
    img = Image.open(image_path)
    data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)

    results = []
    num_words = len(data["text"])

    for i in range(num_words):
        text = data["text"][i].strip()
        if not text or text.isspace():
            continue  # skip blank detections

        box = [
            int(data["left"][i]),
            int(data["top"][i]),
            int(data["width"][i]),
            int(data["height"][i]),
        ]

        results.append({"text": text, "box": box})

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Extract OCR text with bounding box coordinates from an image."
    )
    parser.add_argument(
        "image_path",
        help="Path to the input image (PNG/JPG)",
    )
    parser.add_argument(
        "--output", "-o",
        help="Output JSON file path (default: same name as input with .json extension)",
        default=None,
    )
    args = parser.parse_args()

    if not os.path.isfile(args.image_path):
        print(f"Error: File not found: {args.image_path}", file=sys.stderr)
        sys.exit(1)

    try:
        results = extract_ocr_data(args.image_path)
    except pytesseract.TesseractError as e:
        print(f"Error: Tesseract OCR failed: {e}", file=sys.stderr)
        sys.exit(1)

    if not results:
        print("Warning: No text detected in image.", file=sys.stderr)

    # Default output path
    if args.output is None:
        base, _ = os.path.splitext(args.image_path)
        args.output = base + ".json"

    # Write JSON file
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    # Also print to stdout
    print(json.dumps(results, indent=2, ensure_ascii=False))
    print(f"\n[{len(results)} words] Written to: {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
