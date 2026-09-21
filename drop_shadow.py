#!/usr/bin/env python3
"""
Drop Shadow Generator — Slice TB-007

Adds a depth effect to a sharp text PNG by creating an offset, blurred,
semi-transparent black layer behind the text.

Usage:
    python3 drop_shadow.py <input_png> [--offset-x 3] [--offset-y 3] [--blur 5] [--opacity 0.5] [--output <output>]

Output:
    Image with drop shadow behind the text layer.

Hard gate: Shadow must not obscure the text.
"""

import argparse
import os
import sys

import cv2
import numpy as np


def add_drop_shadow(
    image_path: str,
    offset_x: int = 3,
    offset_y: int = 3,
    blur_kernel: int = 5,
    opacity: float = 0.5,
    output_path: str = "shadowed.png",
) -> str:
    """
    Apply a drop shadow to a transparent PNG.

    Args:
        image_path: Path to input PNG (must have alpha channel).
        offset_x: Shadow offset in x direction (px).
        offset_y: Shadow offset in y direction (px).
        blur_kernel: Gaussian blur kernel size for shadow softness (odd, >= 3).
        opacity: Shadow darkness (0.0 = transparent, 1.0 = solid black).
        output_path: Output file path.

    Returns:
        Path to the shadowed image.
    """
    if blur_kernel < 3 or blur_kernel % 2 == 0:
        raise ValueError(f"Blur kernel must be odd and >= 3, got {blur_kernel}")

    img = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    if img is None:
        raise ValueError(f"Cannot read image: {image_path}")
    if img.shape[2] != 4:
        raise ValueError(f"Image must have alpha channel, got {img.shape[2]} channels")

    h, w, _ = img.shape
    b, g, r = img[:, :, 0], img[:, :, 1], img[:, :, 2]
    a = img[:, :, 3].astype(np.float32) / 255.0

    # Create shadow by shifting alpha channel
    shadow = np.zeros_like(a)
    cy = min(offset_y, h - 1)
    cy_src = max(-offset_y, 0)
    cy_end = cy + min(h - cy, h - cy_src)
    shadow[cy:cy_end, :] = a[cy_src:cy_src + (cy_end - cy), :]

    # Normalize shadow alpha
    shadow = np.clip(shadow, 0, 255)

    # Blur the shadow for softness
    shadow_blur = cv2.GaussianBlur(shadow, (blur_kernel, blur_kernel), 0)
    shadow_blur = shadow_blur / 255.0

    # Create shadow layer (black with opacity)
    shadow_layer = np.full_like(img, 0, dtype=np.uint8)
    shadow_mask = (shadow_blur * opacity * 255).astype(np.uint8)
    shadow_mask = np.clip(shadow_mask, 0, 255)
    shadow_layer[:, :, 3] = shadow_mask

    # Expand canvas if offset pushes content outside
    pad_x = abs(min(offset_x, 0))
    pad_y = abs(min(offset_y, 0))
    new_h = h + pad_y
    new_w = w + pad_x

    # Build final image with padding
    final = np.zeros((new_h, new_w, 4), dtype=np.uint8)

    # Place shadow in padded canvas
    shadow_offset_x = max(offset_x, 0)
    shadow_offset_y = max(offset_y, 0)
    final[pad_y:pad_y + h, pad_x:pad_x + w] = shadow_layer

    # Place original text on top
    final[pad_y:pad_y + h, pad_x:pad_x + w, :3] = img[:, :, :3]
    final[pad_y:pad_y + h, pad_x:pad_x + w, 3] = img[:, :, 3]

    cv2.imwrite(output_path, final)
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Add drop shadow to a transparent PNG.")
    parser.add_argument("image_path", help="Input PNG with alpha channel")
    parser.add_argument("--offset-x", "-ox", type=int, default=3, help="X offset in px. Default: 3")
    parser.add_argument("--offset-y", "-oy", type=int, default=3, help="Y offset in px. Default: 3")
    parser.add_argument("--blur", "-b", type=int, default=5, help="Blur kernel size. Default: 5")
    parser.add_argument("--opacity", type=float, default=0.5, help="Shadow opacity 0-1. Default: 0.5")
    parser.add_argument("--output", "-o", default="shadowed.png", help="Output file path")
    args = parser.parse_args()

    if not os.path.isfile(args.image_path):
        print(f"Error: Image not found: {args.image_path}", file=sys.stderr)
        sys.exit(1)

    try:
        out = add_drop_shadow(args.image_path, args.offset_x, args.offset_y,
                              args.blur, args.opacity, args.output)
        print(f"Shadowed image saved to: {out}", file=sys.stderr)
    except (ValueError, cv2.error) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
