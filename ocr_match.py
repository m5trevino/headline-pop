#!/usr/bin/env python3
"""
Selection-to-OCR Matcher — Slice TB-003

Ingests OCR JSON (from TB-001) and click coordinates (from TB-002),
returns the word at the clicked location.

Usage:
    python3 ocr_match.py <ocr_json> <click_x> <click_y>

Hard gate: Only supports single-word selection.
"""

import argparse
import json
import sys
import os


def find_word_at_coordinate(ocr_data: list[dict], click_x: int, click_y: int) -> dict | None:
    """
    Find the OCR word whose bounding box contains the given coordinates.

    A hit occurs when:
        box[0] <= click_x < box[0] + box[2]
        box[1] <= click_y < box[1] + box[3]

    Args:
        ocr_data: List of {"text": ..., "box": [x, y, w, h]} dicts
        click_x: X coordinate of click
        click_y: Y coordinate of click

    Returns:
        The matching word dict, or None if no word found.
    """
    for word_info in ocr_data:
        text = word_info["text"]
        x, y, w, h = word_info["box"]

        if x <= click_x < x + w and y <= click_y < y + h:
            return {"text": text, "box": word_info["box"]}

    return None


def build_hitboxes(ocr_data: list[dict]) -> list[dict]:
    """
    Return a list of all words with their full hitbox info.
    Useful for testing and debugging.
    """
    return [
        {
            "text": item["text"],
            "hitbox": {
                "x_min": item["box"][0],
                "x_max": item["box"][0] + item["box"][2],
                "y_min": item["box"][1],
                "y_max": item["box"][1] + item["box"][3],
            },
        }
        for item in ocr_data
    ]


def main():
    parser = argparse.ArgumentParser(
        description="Match a click coordinate to OCR text from a JSON file."
    )
    parser.add_argument(
        "ocr_json",
        help="Path to OCR JSON file (output from ocr_extract.py)",
    )
    parser.add_argument(
        "click_x",
        type=int,
        help="X coordinate of the click",
    )
    parser.add_argument(
        "click_y",
        type=int,
        help="Y coordinate of the click",
    )
    parser.add_argument(
        "--show-all-hitboxes",
        action="store_true",
        help="Show all hitboxes for debugging",
    )
    args = parser.parse_args()

    # Validate input file
    if not os.path.isfile(args.ocr_json):
        print(f"Error: OCR JSON file not found: {args.ocr_json}", file=sys.stderr)
        sys.exit(1)

    # Load OCR data
    with open(args.ocr_json, "r", encoding="utf-8") as f:
        ocr_data = json.load(f)

    if not isinstance(ocr_data, list):
        print("Error: OCR JSON must be a list of {text, box} objects.", file=sys.stderr)
        sys.exit(1)

    # Show hitboxes if requested
    if args.show_all_hitboxes:
        hitboxes = build_hitboxes(ocr_data)
        print(json.dumps(hitboxes, indent=2))

    # Find word at click
    result = find_word_at_coordinate(ocr_data, args.click_x, args.click_y)

    if result:
        print(json.dumps(result, indent=2))
    else:
        print(f"No word found at ({args.click_x}, {args.click_y})", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
