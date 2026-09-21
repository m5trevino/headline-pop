#!/usr/bin/env python3
"""
Background Image Blur Engine — Slice TB-004

Applies a Gaussian blur filter to a full-size image.
Original file is never altered — output goes to a separate file.

Usage:
    python3 blur_engine.py <image_path> [--kernel-size 15] [--output <output_path>]

Hard gate: Must not alter any text or overlay logic.
"""

import argparse
import os
import sys

import cv2
import numpy as np


def gaussian_blur(image_path: str, kernel_size: int = 15, output_path: str | None = None) -> str:
    """
    Load an image, apply Gaussian blur, save to file.

    Args:
        image_path: Path to the input image.
        kernel_size: Size of the Gaussian kernel (must be odd, >= 3).
        output_path: Output file path. Defaults to input_blurred.png.

    Returns:
        Path to the blurred image file.
    """
    # Validate kernel size
    if kernel_size < 3 or kernel_size % 2 == 0:
        raise ValueError(f"Kernel size must be odd and >= 3, got {kernel_size}")

    # Read image
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not read image: {image_path}")

    # Apply Gaussian blur
    blurred = cv2.GaussianBlur(img, (kernel_size, kernel_size), 0)

    # Default output path
    if output_path is None:
        base, ext = os.path.splitext(image_path)
        output_path = f"{base}_blurred{ext}"

    # Save blurred image
    cv2.imwrite(output_path, blurred)

    # Verify original is untouched
    original = cv2.imread(image_path)
    if not np.array_equal(img, original):
        print("Warning: Could not verify original integrity.", file=sys.stderr)

    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Apply Gaussian blur filter to an image."
    )
    parser.add_argument(
        "image_path",
        help="Path to the input image",
    )
    parser.add_argument(
        "--kernel-size", "-k",
        type=int,
        default=15,
        help="Gaussian kernel size (odd, >= 3). Default: 15",
    )
    parser.add_argument(
        "--output", "-o",
        help="Output file path (default: <input>_blurred.<ext>)",
        default=None,
    )
    args = parser.parse_args()

    if not os.path.isfile(args.image_path):
        print(f"Error: File not found: {args.image_path}", file=sys.stderr)
        sys.exit(1)

    try:
        result_path = gaussian_blur(
            args.image_path,
            kernel_size=args.kernel_size,
            output_path=args.output,
        )
        print(f"Blurred image saved to: {result_path}", file=sys.stderr)
    except (ValueError, cv2.error) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
