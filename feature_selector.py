#!/usr/bin/env python3
"""
Feature Selector GUI Panel — Slice TB-011

Extends the image selection GUI with toggle buttons for effects:
Blur, Shadow, Highlight. Saves selection to state object.

Hard gate: GUI must not execute logic directly; only update state.
"""

import argparse
import json
import os
import sys
import tkinter as tk
from tkinter import ttk


class FeatureSelector(tk.Tk):
    """GUI with toggle buttons for image effects."""

    EFFECTS = ["blur", "shadow", "highlight"]

    def __init__(self):
        super().__init__()
        self.title("Feature Selector")
        self.state = {effect: False for effect in self.EFFECTS}
        self.selected_image = None
        self._build_ui()

    def _build_ui(self):
        # Image path selector
        tk.Label(self, text="Image Path:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.img_entry = tk.Entry(self, width=60)
        self.img_entry.grid(row=0, column=1, padx=10, pady=5)

        tk.Button(self, text="Browse...", command=self._browse_image).grid(row=0, column=2, padx=10, pady=5)

        # Effect toggles
        tk.Label(self, text="Effects:").grid(row=1, column=0, padx=10, pady=10, sticky="w")

        self.vars = {}
        for i, effect in enumerate(self.EFFECTS):
            var = tk.BooleanVar(value=False)
            self.vars[effect] = var
            cb = tk.Checkbutton(
                self,
                text=effect.capitalize(),
                variable=var,
                command=self._update_state,
            )
            cb.grid(row=1, column=i + 1, padx=10, pady=5, sticky="w")

        # Save config button
        tk.Button(
            self,
            text="Save Configuration",
            command=self._save_config,
            bg="#4CAF50",
            fg="white",
        ).grid(row=2, column=1, pady=20)

        # State display
        self.state_label = tk.Label(self, text="State: {}", font=("monospace", 10))
        self.state_label.grid(row=3, column=0, columnspan=3, pady=5)

        self._update_state()

    def _browse_image(self):
        from tkinter import filedialog
        path = filedialog.askopenfilename(
            filetypes=[("Images", "*.png *.jpg *.jpeg")]
        )
        if path:
            self.img_entry.delete(0, tk.END)
            self.img_entry.insert(0, path)
            self.selected_image = path

    def _update_state(self):
        self.state = {effect: var.get() for effect, var in self.vars.items()}
        self.state_label.config(text=f"State: {json.dumps(self.state)}")

    def get_config(self) -> dict:
        """Return current effect configuration object."""
        return {
            "image": self.selected_image,
            "effects": self.state,
        }

    def _save_config(self):
        config = self.get_config()
        with open("feature_config.json", "w") as f:
            json.dump(config, f, indent=2)
        print(f"Config saved: {json.dumps(config)}")
        self.state_label.config(text="Configuration saved to feature_config.json", fg="green")


def main():
    parser = argparse.ArgumentParser(description="Feature selector GUI for effect toggling.")
    parser.add_argument("--auto", action="store_true", help="Auto-start GUI (default)")
    args = parser.parse_args()

    app = FeatureSelector()
    app.mainloop()


if __name__ == "__main__":
    main()
