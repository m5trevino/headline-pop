#!/usr/bin/env python3
"""
Dashboard Shell — Slice UI-001

Persistent, non-blocking control window. Pure UI skeleton — no
rendering logic, no OCR, no pipeline. Extensible placeholder
architecture for UI-002 through UI-005 to plug in.

Usage:
    python3 dashboard.py
"""

import json
import os
import subprocess
import sys
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk


class ErrorHandler:
    """Captures and surfaces pipeline errors entirely within the UI.
    The user must never see a terminal error.
    
    Tracks errors in a log and displays user-friendly messages via messagebox.
    """

    def __init__(self, status_var: tk.StringVar):
        self._status_var = status_var
        self._log: list[str] = []

    def _log_entry(self, level: str, message: str):
        """Append an entry to the error log."""
        self._log.append(f"[{level}] {message}")

    def capture_subprocess(self, result: subprocess.CompletedProcess, context: str) -> tuple[bool, str]:
        """Check a subprocess result and return (success, friendly_message).
        
        If the subprocess failed, logs the error and returns a user-friendly message.
        The technical details are saved to the log for the user to view.
        """
        if result.returncode == 0:
            return True, ""

        error_text = result.stderr.strip() or result.stdout.strip() or f"Exit code {result.returncode}"
        self._log_entry("ERROR", f"{context}: {error_text[:500]}")

        # Map common error patterns to user-friendly messages
        friendly = self._map_error(context, error_text)
        return False, friendly

    def _map_error(self, context: str, error_text: str) -> str:
        """Convert technical error messages to user-friendly format."""
        lower = error_text.lower()

        if "cannot read" in lower or "unable to open" in lower or "no such file" in lower:
            return f"Could not read the selected image. Please try a different file.\n\nDetails: {error_text[:200]}"

        if "tesseract" in lower:
            return f"OCR engine error. The image may not contain readable text.\n\nDetails: {error_text[:200]}"

        if "cannot parse" in lower or "invalid" in lower:
            return f"Invalid image format. Please select a valid PNG or JPG file.\n\nDetails: {error_text[:200]}"

        if "timeout" in lower:
            return f"Operation timed out. The pipeline took too long.\n\nDetails: {error_text[:200]}"

        if "no module named" in lower:
            return f"A required library is missing. Please check your Python environment.\n\nDetails: {error_text[:200]}"

        # Generic fallback
        return f"An error occurred in {context}.\n\nTechnical details: {error_text[:300]}"

    def show_error(self, title: str, user_message: str):
        """Show an error dialog with the full error log as an expandable detail."""
        log_text = "\n".join(self._log[-20:]) if self._log else "(empty log)"
        messagebox.showerror(title, f"{user_message}\n\n--- Error Log ---\n{log_text}")

    def show_warning(self, title: str, message: str):
        """Show a warning dialog."""
        messagebox.showwarning(title, message)

    def clear(self):
        """Clear the error log."""
        self._log.clear()


class EffectStateManager:
    """Maps UI checkboxes to pipeline parameters for orchestrator.py.
    
    Acceptable effects: blur, shadow, highlight
    Produces a config dict ready for PipelineController constructor.
    """

    EFFECT_MAP = {
        "Blur": "blur",
        "Shadow": "shadow",
        "Highlight": "highlight",
    }

    def __init__(self, effect_vars: dict[str, tk.BooleanVar]):
        self._effect_vars = effect_vars

    def get_config(self) -> dict:
        """Return effect state dictionary matching orchestrator.py expectations.
        
        Returns:
            {"blur": bool, "shadow": bool, "highlight": bool}
        """
        return {
            ui_name: var.get()
            for ui_name, var in self._effect_vars.items()
        }

    def get_effect_names(self) -> list[str]:
        """Return list of active effect names for orchestrator effects parameter."""
        state = self.get_config()
        return [
            self.EFFECT_MAP[name]
            for name, active in state.items()
            if active
        ]

    def validate(self) -> tuple[bool, str]:
        """Check that all required fields are populated.
        
        Returns:
            (is_valid, error_message)
        """
        if not self.get_effect_names():
            return False, "At least one effect must be selected"
        return True, ""


class DashboardApp:
    """Dashboard application shell — no rendering logic."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Headline Spotlight")
        self.root.geometry("420x340")
        self.root.resizable(True, True)
        self.root.configure(bg="#1e1e2e")

        # State holders (populated by UI-002, UI-003)
        self.image_path: str | None = None
        self.selected_coords: tuple[int, int] | None = None

        # Process monitor (UI-004)
        self._render_process: subprocess.Popen | None = None
        self._is_rendering = False

        # Error handler (UI-005)
        self.error_handler = ErrorHandler(self.status_var)

        self._apply_theme()
        self._build_layout()

    def _apply_theme(self):
        """Apply clean, focused dark theme."""
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("TFrame", background="#1e1e2e")
        style.configure("TLabel", background="#1e1e2e", foreground="#cdd6f4", font=("Segoe UI", 11))
        style.configure("TButton", background="#89b4fa", foreground="#1e1e2e",
                        font=("Segoe UI", 11), padding=(20, 8))
        style.map("TButton",
                  background=[("active", "#74c7ec"), ("pressed", "#587577")])
        style.configure("TCheckbutton", background="#1e1e2e", foreground="#cdd6f4",
                        font=("Segoe UI", 11))
        style.configure("TLabelFrame", background="#1e1e2e", foreground="#cdd6f4",
                        font=("Segoe UI", 11, "bold"))

    def _build_layout(self):
        """Build the main layout container — no rendering logic here."""
        # Main frame
        main = ttk.Frame(self.root, padding=24)
        main.pack(fill="both", expand=True)

        # Title
        title = ttk.Label(main, text="Headline Spotlight",
                          font=("Segoe UI", 18, "bold"), foreground="#89b4fa")
        title.pack(pady=(0, 24))

        # Section: Image Selection
        sel_frame = ttk.LabelFrame(main, text="Image Selection", padding=12)
        sel_frame.pack(fill="x", pady=(0, 12))

        self.img_path_var = tk.StringVar()
        ttk.Entry(sel_frame, textvariable=self.img_path_var, state="readonly").pack(
            fill="x", pady=(0, 8)
        )
        ttk.Button(sel_frame, text="Browse...", command=self._on_browse).pack()

        # Coordinate display (set by UI-002 Selection Bridge)
        self.coord_var = tk.StringVar(value="No selection yet")
        ttk.Label(sel_frame, textvariable=self.coord_var,
                  font=("monospace", 9), foreground="#a6adc8").pack(pady=(6, 0))

        # Section: Effects (connected to EffectStateManager)
        effects_frame = ttk.LabelFrame(main, text="Effects", padding=12)
        effects_frame.pack(fill="x", pady=(0, 12))

        self.effect_vars = {}
        for name in ["Blur", "Shadow", "Highlight"]:
            var = tk.BooleanVar(value=False)
            self.effect_vars[name] = var
            ttk.Checkbutton(effects_frame, text=name, variable=var).pack(anchor="w")

        # UI-003: Connect checkboxes to state manager
        self.effect_state = EffectStateManager(self.effect_vars)

        # Section: Render Trigger (placeholder)
        ttk.Button(main, text="Render", command=self._on_render).pack(
            fill="x", pady=(12, 0)
        )

        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status = ttk.Label(main, textvariable=self.status_var,
                           font=("monospace", 9), foreground="#a6adc8")
        status.pack(pady=(16, 0), fill="x")

    def _on_browse(self):
        """UI-002: Open file dialog, launch Selection GUI, capture coordinates."""
        from tkinter import filedialog
        path = filedialog.askopenfilename(
            title="Select an image for headline selection",
            filetypes=[("Images", "*.png *.jpg *.jpeg")],
        )
        if not path:
            return

        # Set the image path in the UI
        self.img_path_var.set(path)
        self.status_var.set(f"Image loaded: {os.path.basename(path)}")

        # Launch Selection GUI as a subprocess to capture coordinates
        self.status_var.set("Opening selection window...")
        self.root.update()

        try:
            result = subprocess.run(
                [sys.executable, "selection_gui.py", path],
                capture_output=True,
                text=True,
                timeout=120,
            )

            if result.returncode == 0 and result.stdout.strip():
                # Parse JSON output: {"x": 50, "y": 30}
                data = json.loads(result.stdout.strip())
                self.selected_coords = (data["x"], data["y"])
                self.coord_var.set(f"Selected: ({data['x']}, {data['y']})")
                self.status_var.set(f"Coordinates captured: ({data['x']}, {data['y']})")
            else:
                self.coord_var.set("No selection captured")
                self.status_var.set("Selection window closed without click")

        except subprocess.TimeoutExpired:
            self.status_var.set("Selection window timed out")
        except (json.JSONDecodeError, KeyError) as e:
            self.status_var.set(f"Error parsing selection: {e}")

    def _on_render(self):
        """UI-004: Launch pipeline in background, alert on completion."""
        # Validate prerequisites
        if not self.image_path_var.get():
            messagebox.showerror("Error", "Please select an image first.")
            return

        if not self.selected_coords:
            messagebox.showerror("Error", "Please select text coordinates first.")
            return

        if not self.effect_state.get_effect_names():
            messagebox.showerror("Error", "Please select at least one effect.")
            return

        # Prevent double-click
        if self._is_rendering:
            messagebox.showwarning("Warning", "Rendering is already in progress.")
            return

        self._is_rendering = True
        self.status_var.set("Rendering... this may take a moment.")

        # Disable the render button while processing
        render_btn = self.root.nametowidget(self.root.children[list(self.root.children.keys())[-2]])
        render_btn.config(state="disabled")

        # Launch orchestrator in a background thread to keep UI responsive
        def run_pipeline():
            try:
                image = self.image_path_var.get()
                ocr_json = image.replace(".png", ".json").replace(".jpg", ".json").replace(".jpeg", ".json")

                if not os.path.isfile(ocr_json):
                    # Auto-generate OCR data if not present
                    self.root.after(0, lambda: self.status_var.set(f"Generating OCR data for {os.path.basename(image)}..."))
                    ocr_result = subprocess.run(
                        [sys.executable, "ocr_extract.py", image, "-o", ocr_json],
                        capture_output=True, text=True, timeout=60,
                    )
                    ok, msg = self.error_handler.capture_subprocess(ocr_result, "OCR extraction")
                    if not ok:
                        self.root.after(0, lambda m=msg: self.error_handler.show_error("OCR Error", m))
                        return

                effects = self.effect_state.get_effect_names()
                cx, cy = self.selected_coords

                cmd = [
                    sys.executable, "orchestrator.py",
                    "--image", image,
                    "--ocr", ocr_json,
                    "--click-x", str(cx),
                    "--click-y", str(cy),
                    "--frames", "60",
                    "--fps", "30",
                ]
                for effect in effects:
                    cmd.extend(["--" + effect])

                self.root.after(0, lambda: self.status_var.set("Running pipeline..."))

                proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

                ok, msg = self.error_handler.capture_subprocess(proc, "rendering pipeline")
                if ok:
                    self.root.after(0, lambda: self.status_var.set("Rendering complete! Output: headline_pop.mp4"))
                    self.root.after(0, lambda: messagebox.showinfo("Success", "Rendering complete!\nOutput: headline_pop.mp4"))
                else:
                    self.root.after(0, lambda m=msg: self.error_handler.show_error("Render Failed", m))

            except subprocess.TimeoutExpired:
                self.error_handler._log_entry("ERROR", "Pipeline exceeded 10-minute timeout")
                self.root.after(0, lambda: self.error_handler.show_error("Timeout", "Pipeline exceeded 10-minute timeout."))
            except Exception as e:
                self.error_handler._log_entry("ERROR", f"Unexpected error: {e}")
                self.root.after(0, lambda e=e: self.error_handler.show_error("Unexpected Error", f"An unexpected error occurred:\n{str(e)}"))
            finally:
                self.root.after(0, self._render_done)

        import threading
        thread = threading.Thread(target=run_pipeline, daemon=True)
        thread.start()

    def _render_done(self):
        """Restore UI state after rendering finishes."""
        self._is_rendering = False
        render_btn = self.root.nametowidget(self.root.children[list(self.root.children.keys())[-2]])
        render_btn.config(state="normal")
        self.status_var.set("Ready")

    def run(self):
        """Start the event loop."""
        self.root.mainloop()


if __name__ == "__main__":
    app = DashboardApp()
    app.run()
