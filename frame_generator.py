#!/usr/bin/env python3
"""
Frame-by-Frame Motion Generator — Slice TB-008

Generates a sequence of images with scaling (1% per frame) to create
a smooth zoom effect when viewed sequentially.

Usage:
    python3 frame_generator.py <image_path> [--frames 60] [--start-scale 1.0] [--end-scale 1.6] [--output-dir frames]

Output:
    Folder of sequential PNG images (0001.png, 0002.png, ...).

Hard gate: Do not include audio or video encoding yet.
"""

import argparse
import os
import sys

import cv2
import numpy as np


def generate_frames(
    image_path: str,
    num_frames: int = 60,
    start_scale: float = 1.0,
    end_scale: float = 1.6,
    output_dir: str = "frames",
) -> list[str]:
    """
    Generate scaled frames from an input image.

    Args:
        image_path: Input image path.
        num_frames: Number of frames to generate.
        start_scale: Starting scale factor.
        end_scale: Ending scale factor.
        output_dir: Output directory for frames.

    Returns:
        List of output file paths.
    """
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Cannot read image: {image_path}")

    os.makedirs(output_dir, exist_ok=True)

    orig_h, orig_w = img.shape[:2]
    frames = []

    for i in range(num_frames):
        t = i / max(num_frames - 1, 1)  # 0.0 to 1.0
        scale = start_scale + (end_scale - start_scale) * t

        # Calculate new dimensions
        new_w = int(orig_w * scale)
        new_h = int(orig_h * scale)

        # Resize with interpolation
        resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_LINEAR)

        # Frame filename with zero-padded numbering
        filename = f"{output_dir}/{i + 1:04d}.png"
        cv2.imwrite(filename, resized)
        frames.append(filename)

    return frames


def main():
    parser = argparse.ArgumentParser(description="Generate scaled frames for zoom animation.")
    parser.add_argument("image_path", help="Input image path")
    parser.add_argument("--frames", "-n", type=int, default=60, help="Number of frames. Default: 60")
    parser.add_argument("--start-scale", type=float, default=1.0, help="Starting scale. Default: 1.0")
    parser.add_argument("--end-scale", type=float, default=1.6, help="Ending scale. Default: 1.6")
    parser.add_argument("--output-dir", "-o", default="frames", help="Output directory. Default: frames")
    args = parser.parse_args()

    if not os.path.isfile(args.image_path):
        print(f"Error: Image not found: {args.image_path}", file=sys.stderr)
        sys.exit(1)

    try:
        frame_paths = generate_frames(
            args.image_path, args.frames, args.start_scale, args.end_scale, args.output_dir
        )
        print(f"Generated {len(frame_paths)} frames in '{args.output_dir}/'", file=sys.stderr)
        print(f"First: {frame_paths[0]}", file=sys.stderr)
        print(f"Last:  {frame_paths[-1]}", file=sys.stderr)

        # Verify dimensions
        first = cv2.imread(frame_paths[0])
        last = cv2.imread(frame_paths[-1])
        print(f"First frame: {first.shape[1]}x{first.shape[0]}", file=sys.stderr)
        print(f"Last frame:  {last.shape[1]}x{last.shape[0]}", file=sys.stderr)
    except (ValueError, cv2.error) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
