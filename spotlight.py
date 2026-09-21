#!/usr/bin/env python3
"""
Spotlight Composition Layering — Slice TB-006

Combines a blurred background image with a sharp text PNG overlay
into a single composited frame.

Usage:
    python3 spotlight.py <blurred_bg> <sharp_text_png> [--output <output>] [--position center]

Output:
    Single composited image with blurred background and sharp text on top.

Hard gate: No movement or animation logic.
"""

import argparse
import os
import sys

import cv2
import numpy as np


def load_blurred_background(path: str) -> np.ndarray:
    """Load the blurred background image."""
    img = cv2.imread(path)
    if img is None:
        raise ValueError(f"Cannot load blurred background: {path}")
    return img


def load_sharp_text(path: str) -> np.ndarray:
    """Load the sharp text PNG (must have alpha channel)."""
    img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if img is None:
        raise ValueError(f"Cannot load sharp text: {path}")
    if img.shape[2] != 4:
        raise ValueError(f"Sharp text PNG must have alpha channel, got {img.shape[2]} channels")
    return img


def center_text_on_bg(
    bg: np.ndarray,
    text_overlay: np.ndarray,
) -> np.ndarray:
    """
    Center the sharp text overlay on the blurred background.
    Handles size mismatch by scaling text if needed.

    Returns:
        Composite image (BGRA).
    """
    bg_h, bg_w, _ = bg.shape
    text_h, text_w, _ = text_overlay.shape

    # Create output the same size as background
    composite = bg.copy()

    # Calculate center position
    center_y = bg_h // 2
    center_x = bg_w // 2

    # Position text so its center aligns with background center
    y_start = center_y - text_h // 2
    x_start = center_x - text_w // 2

    # Clip to bounds
    y_start = max(0, y_start)
    x_start = max(0, x_start)

    # Determine overlapping region
    y_end = min(y_start + text_h, bg_h)
    x_end = min(x_start + text_w, bg_w)

    # Text region to render
    text_y_start = y_start - (center_y - text_h // 2)
    text_y_end = text_y_start + (y_end - y_start)

    text_x_start = x_start - (center_x - text_w // 2)
    text_x_end = text_x_start + (x_end - x_start)

    # Blend using alpha
    bg_region = composite[y_start:y_end, x_start:x_end]
    text_region = text_overlay[
        max(0, center_y - text_h // 2) : max(0, center_y - text_h // 2) + (y_end - y_start),
        max(0, center_x - text_w // 2) : max(0, center_x - text_w // 2) + (x_end - x_start),
    ]

    # Ensure regions match
    text_region = text_region[: y_end - y_start, : x_end - x_start]

    if text_region.shape[0] == 0 or text_region.shape[1] == 0:
        return composite

    # Split channels
    text_bgra = cv2.split(text_region)
    text_alpha = text_bgra[3].astype(np.float32) / 255.0

    # Blend
    bg_region_float = bg_region.astype(np.float32)
    text_region_float = cv2.merge(text_bgra[:3]).astype(np.float32)

    composite_region = bg_region_float * (1 - text_alpha[..., np.newaxis]) + text_region_float * text_alpha[..., np.newaxis]

    composite[y_start:y_end, x_start:x_end] = np.clip(composite_region, 0, 255).astype(np.uint8)

    return composite


def save_composite(image: np.ndarray, output_path: str) -> str:
    """Save the composited image."""
    cv2.imwrite(output_path, image)
    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Combine blurred background with sharp text overlay."
    )
    parser.add_argument(
        "blurred_bg",
        help="Path to the blurred background image",
    )
    parser.add_argument(
        "sharp_text",
        help="Path to the sharp text PNG (with alpha)",
    )
    parser.add_argument(
        "--output", "-o",
        help="Output file path. Default: spotlight_composite.png",
        default="spotlight_composite.png",
    )
    args = parser.parse_args()

    if not os.path.isfile(args.blurred_bg):
        print(f"Error: Blurred background not found: {args.blurred_bg}", file=sys.stderr)
        sys.exit(1)
    if not os.path.isfile(args.sharp_text):
        print(f"Error: Sharp text not found: {args.sharp_text}", file=sys.stderr)
        sys.exit(1)

    try:
        bg = load_blurred_background(args.blurred_bg)
        text = load_sharp_text(args.sharp_text)
    except (ValueError, cv2.error) as e:
        print(f"Error loading images: {e}", file=sys.stderr)
        sys.exit(1)

    composite = center_text_on_bg(bg, text)
    output_path = save_composite(composite, args.output)

    print(f"Composited image saved to: {output_path}", file=sys.stderr)
    h, w, _ = composite.shape
    print(f"Output dimensions: {w}x{h}", file=sys.stderr)


if __name__ == "__main__":
    main()
