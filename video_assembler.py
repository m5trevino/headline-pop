#!/usr/bin/env python3
"""
Video Assembler (Encoder) — Slice TB-009

Compiles a sequence of images into an MP4 video using FFmpeg.

Usage:
    python3 video_assembler.py <frame_dir> [--fps 30] [--output output.mp4]

Output:
    MP4 video file.

Hard gate: Only raw visual assembly; no text overlays during encode.
"""

import argparse
import os
import subprocess
import sys
import tempfile


def assemble_video(
    frame_dir: str,
    fps: int = 30,
    output_path: str = "output.mp4",
) -> str:
    """
    Compile sequential frames into an MP4 video.

    Args:
        frame_dir: Directory containing sequential PNG frames.
        fps: Frames per second. Default: 30.
        output_path: Output MP4 path.

    Returns:
        Path to the compiled MP4.
    """
    # Validate frame directory
    if not os.path.isdir(frame_dir):
        raise ValueError(f"Frame directory not found: {frame_dir}")

    # Find frame files
    frame_files = sorted(
        f for f in os.listdir(frame_dir)
        if f.endswith(('.png', '.jpg', '.jpeg'))
    )
    if not frame_files:
        raise ValueError(f"No image files found in: {frame_dir}")

    # Get first frame dimensions
    import cv2
    first_frame = cv2.imread(os.path.join(frame_dir, frame_files[0]))
    if first_frame is None:
        raise ValueError(f"Cannot read first frame: {frame_files[0]}")
    h, w = first_frame.shape[:2]

    # Create temp file for frame list
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as lf:
        for f in frame_files:
            lf.write(f"file '{os.path.join(frame_dir, f)}'\n")
        list_file = lf.name

    try:
        # Build FFmpeg command
        cmd = [
            'ffmpeg', '-y',
            '-f', 'concat', '-safe', '0',
            '-r', str(fps),
            '-i', list_file,
            '-c:v', 'libx264',
            '-pix_fmt', 'yuv420p',
            '-vf', f'scale={w}:{h}',
            output_path,
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
        )

        if result.returncode != 0:
            print(f"FFmpeg stderr: {result.stderr}", file=sys.stderr)
            raise RuntimeError(f"FFmpeg failed with code {result.returncode}")

    finally:
        os.unlink(list_file)

    # Verify output
    if not os.path.isfile(output_path):
        raise RuntimeError(f"Output file was not created: {output_path}")

    return output_path


def main():
    parser = argparse.ArgumentParser(description="Compile frames into an MP4 video.")
    parser.add_argument("frame_dir", help="Directory containing sequential frames")
    parser.add_argument("--fps", type=int, default=30, help="Frames per second. Default: 30")
    parser.add_argument("--output", "-o", default="output.mp4", help="Output MP4 path")
    args = parser.parse_args()

    if not os.path.isdir(args.frame_dir):
        print(f"Error: Frame directory not found: {args.frame_dir}", file=sys.stderr)
        sys.exit(1)

    try:
        out = assemble_video(args.frame_dir, args.fps, args.output)
        print(f"Video saved to: {out}", file=sys.stderr)

        # Verify video properties
        import cv2
        cap = cv2.VideoCapture(out)
        if cap.isOpened():
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            video_fps = cap.get(cv2.CAP_PROP_FPS)
            vw, vh = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            cap.release()
            print(f"Video: {frame_count} frames, {video_fps:.1f} FPS, {vw}x{vh}", file=sys.stderr)
    except (ValueError, RuntimeError, subprocess.TimeoutExpired) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
