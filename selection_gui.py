#!/usr/bin/env python3
"""
Selection GUI Scaffold — Slice TB-002

Displays an image in a window and captures click-to-select.
Clicking on a word returns its X,Y coordinates to the console.
No processing logic attached — pure selection UI.

Usage:
    python3 selection_gui.py <image_path>

Hard gate: No integration with OCR output yet.
"""

import argparse
import sys
import tkinter as tk
from tkinter import filedialog, messagebox

from PIL import Image, ImageTk


class ImageSelector:
    """Displays an image and captures click-to-select.
    Closes immediately after the first left-click, printing coordinates to stdout."""

    def __init__(self, image_path: str):
        self.image_path = image_path
        self.image = Image.open(image_path)
        self.original_image = self.image.copy()

        # Scale image to fit window if needed (max 1400x900)
        max_w, max_h = 1400, 900
        img_w, img_h = self.image.size
        scale = min(max_w / img_w, max_h / img_h, 1.0)
        if scale < 1.0:
            self.image = self.image.resize(
                (int(img_w * scale), int(img_h * scale)), Image.LANCZOS
            )
            self.scale_factor = scale
        else:
            self.scale_factor = 1.0

        self.selected_coord = None
        self._closed = False

        self.root = tk.Tk()
        self.root.title(f"Image Selector — {image_path}")
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self._build_ui()
        self._bind_events()

    def _on_close(self):
        """Handle window close — print nothing if no click was made."""
        self.root.destroy()

    def _build_ui(self):
        """Build the GUI layout."""
        # Header label
        header = tk.Label(
            self.root,
            text="Click once on a word to select it.\n"
            "This window will close automatically.",
            font=("Segoe UI", 10),
            justify="center",
        )
        header.pack(pady=(8, 4))

        # Canvas to display image
        canvas_w = self.image.size[0]
        canvas_h = self.image.size[1]
        self.canvas = tk.Canvas(
            self.root,
            width=canvas_w,
            height=canvas_h,
            bg="#1a1a1a",
            highlightthickness=0,
        )
        self.canvas.pack(fill="both", expand=True)

        # Render image
        self.tk_image = ImageTk.PhotoImage(self.image)
        self.canvas.create_image(0, 0, anchor="nw", image=self.tk_image)

        # Coordinate display (live)
        self.coord_label = tk.Label(
            self.root,
            text="Waiting for click...",
            font=("monospace", 11),
            bg="#222",
            fg="#0f0",
            padx=10,
            pady=4,
        )
        self.coord_label.pack(fill="x")

    def _bind_events(self):
        """Bind mouse events to canvas."""
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<Motion>", self._on_mouse_move)

    def _on_mouse_move(self, event):
        """Update live coordinate display on mouse move."""
        raw_x = int(event.x / self.scale_factor)
        raw_y = int(event.y / self.scale_factor)
        self.coord_label.config(text=f"X: {raw_x}  Y: {raw_y}  |  Click to confirm")

    def _on_click(self, event):
        """Capture first click, print coordinates, close window."""
        raw_x = int(event.x / self.scale_factor)
        raw_y = int(event.y / self.scale_factor)
        self.selected_coord = (raw_x, raw_y)

        # Print to stdout for the Dashboard to read
        print(json.dumps({"x": raw_x, "y": raw_y}), flush=True)

        self.coord_label.config(
            text=f"Selected: ({raw_x}, {raw_y})"
        )

        # Close immediately after click
        self._closed = True
        self.root.after(500, self.root.destroy)

    def run(self):
        """Start the GUI event loop."""
        self.root.mainloop()

    def get_selection(self):
        """Return the captured coordinate or None."""
        return self.selected_coord


def main():
    parser = argparse.ArgumentParser(
        description="Display an image and capture click coordinates."
    )
    parser.add_argument(
        "image_path",
        help="Path to the image to display",
    )
    args = parser.parse_args()

    if not os.path.isfile(args.image_path):
        print(f"Error: File not found: {args.image_path}", file=sys.stderr)
        sys.exit(1)

    app = ImageSelector(args.image_path)
    app.run()


if __name__ == "__main__":
    import json
    import os
    main()
