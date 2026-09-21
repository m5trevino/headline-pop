#!/usr/bin/env python3
"""
Full Orchestrator (The Controller) — Slice TB-012

Bridges selection, effect logic, and final rendering.
Imports all modules and orchestrates the pipeline based on effect configuration.

Usage:
    python3 orchestrator.py --image image.png --ocr json.json --click-x 50 --click-y 30
        [--blur] [--shadow] [--highlight] [--frames 60] [--fps 30]

Output:
    Final MP4 with selected effects applied.

Hard gate: Controller has zero knowledge of how effects are rendered internally.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile


class PipelineController:
    """
    Orchestrator that coordinates effect modules.
    Has zero knowledge of how effects are rendered internally.
    Only knows input types and output types for each module.
    """

    EFFECTS = {
        "blur": {
            "module": "blur_engine",
            "input": "image",
            "output": "blurred_image",
        },
        "shadow": {
            "module": "drop_shadow",
            "input": "text_png",
            "output": "shadowed_png",
        },
        "highlight": {
            "module": "highlight_rect",
            "input": "image",
            "output": "highlighted_image",
        },
    }

    def __init__(
        self,
        image_path: str,
        ocr_json: str,
        click_x: int,
        click_y: int,
        effects: list[str] | None = None,
        num_frames: int = 60,
        fps: int = 30,
    ):
        self.image_path = image_path
        self.ocr_json = ocr_json
        self.click_x = click_x
        self.click_y = click_y
        self.effects = effects or []
        self.num_frames = num_frames
        self.fps = fps
        self.tmpdir = tempfile.mkdtemp(prefix="headline_pop_")
        self._state: dict[str, str] = {}

    @property
    def output_path(self) -> str:
        return os.path.join(self.tmpdir, "final_output.mp4")

    def _run_module(self, module_name: str, **kwargs) -> str:
        """Run an effect module and return output path."""
        module_path = os.path.join(os.path.dirname(__file__), f"{module_name}.py")
        if not os.path.isfile(module_path):
            raise FileNotFoundError(f"Module not found: {module_name} ({module_path})")

        cmd = ["python3", module_path]

        # Add keyword arguments as CLI flags
        for key, value in kwargs.items():
            flag = f"--{key.replace('_', '-')}"
            if isinstance(value, bool):
                if value:
                    cmd.append(flag)
            elif isinstance(value, list):
                cmd.append(flag)
                for item in value:
                    cmd.append(item)
            else:
                cmd.extend([flag, str(value)])

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            print(f"Module {module_name} error: {result.stderr}", file=sys.stderr)
            raise RuntimeError(f"Module {module_name} failed: {result.stderr}")

        # Extract output path from stderr
        lines = result.stderr.strip().split("\n")
        for line in lines:
            if "saved to:" in line or "Written to:" in line:
                return line.split(":", 1)[1].strip()

        return self.output_path

    def _run_blur(self, image_path: str) -> str:
        out = os.path.join(self.tmpdir, "blurred.png")
        return self._run_module("blur_engine", image_path=image_path, kernel_size=15, output=out)

    def _run_highlight(self, image_path: str) -> str:
        return self._run_module(
            "highlight_rect",
            image_path=image_path,
            ocr_json=self.ocr_json,
            click_x=self.click_x,
            click_y=self.click_y,
            output=os.path.join(self.tmpdir, "highlighted.png"),
        )

    def _run_text_effects(self, image_path: str) -> str:
        """Run shadow on extracted text and return shadowed PNG path."""
        sharp_path = os.path.join(self.tmpdir, "sharp.png")
        out_path = os.path.join(self.tmpdir, "shadowed.png")

        # Extract text region first
        subprocess.run(
            ["python3", os.path.join(os.path.dirname(__file__), "headline_mask.py"),
             image_path, self.ocr_json, str(self.click_x), str(self.click_y),
             "-o", sharp_path],
            capture_output=True, text=True, timeout=60,
        )

        # Apply shadow if selected
        if "shadow" in self.effects:
            return self._run_module(
                "drop_shadow",
                image_path=sharp_path,
                output=out_path,
            )
        return sharp_path

    def _assemble_video(self, frames_dir: str) -> str:
        """Assemble frames into final MP4."""
        return self._run_module(
            "video_assembler",
            frame_dir=frames_dir,
            fps=self.fps,
            output=self.output_path,
        )

    def run(self) -> str:
        """Execute the full pipeline."""
        print(f"Pipeline: effects={self.effects}", file=sys.stderr)

        # Step 1: Run background effects
        bg_path = self.image_path
        if "blur" in self.effects:
            bg_path = self._run_blur(self.image_path)

        # Step 2: Run text effects
        text_path = self._run_text_effects(self.image_path)

        # Step 3: Spotlight composition
        composite_path = os.path.join(self.tmpdir, "composite.png")
        subprocess.run(
            ["python3", os.path.join(os.path.dirname(__file__), "spotlight.py"),
             bg_path, text_path, "-o", composite_path],
            capture_output=True, text=True, timeout=60,
        )

        # Step 4: Generate frames
        frames_dir = os.path.join(self.tmpdir, "frames")
        subprocess.run(
            ["python3", os.path.join(os.path.dirname(__file__), "frame_generator.py"),
             composite_path, "-n", str(self.num_frames), "-o", frames_dir],
            capture_output=True, text=True, timeout=120,
        )

        # Step 5: Assemble video
        video_out = self._assemble_video(frames_dir)

        # Copy to current directory
        final = "headline_pop.mp4"
        shutil.copy2(video_out, final)
        print(f"Final video saved to: {final}", file=sys.stderr)

        return final

    def cleanup(self):
        """Remove temporary files."""
        shutil.rmtree(self.tmpdir, ignore_errors=True)


def main():
    parser = argparse.ArgumentParser(description="Orchestrate the full headline spotlight pipeline.")
    parser.add_argument("--image", "-i", required=True, help="Input image path")
    parser.add_argument("--ocr", "-o", required=True, help="OCR JSON file")
    parser.add_argument("--click-x", type=int, default=50, help="Click X coordinate")
    parser.add_argument("--click-y", type=int, default=30, help="Click Y coordinate")
    parser.add_argument("--blur", action="store_true", help="Enable blur effect")
    parser.add_argument("--shadow", action="store_true", help="Enable shadow effect")
    parser.add_argument("--highlight", action="store_true", help="Enable highlight effect")
    parser.add_argument("--frames", type=int, default=60, help="Number of animation frames")
    parser.add_argument("--fps", type=int, default=30, help="Video frame rate")
    args = parser.parse_args()

    effects = []
    if args.blur:
        effects.append("blur")
    if args.shadow:
        effects.append("shadow")
    if args.highlight:
        effects.append("highlight")

    controller = PipelineController(
        image_path=args.image,
        ocr_json=args.ocr,
        click_x=args.click_x,
        click_y=args.click_y,
        effects=effects,
        num_frames=args.frames,
        fps=args.fps,
    )

    try:
        controller.run()
    except Exception as e:
        print(f"Pipeline error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        controller.cleanup()


if __name__ == "__main__":
    main()
