"""Screenshot capture component for ADB screen capture"""

import os
import cv2
import numpy as np
import customtkinter as ctk
import datetime
from typing import Optional

from core.screen_capture import ScreenCapture
from gui.utils.debug_logger import DebugLogger
from gui.utils.image_display_helper import ImageDisplayHelper


class ScreenshotCapture:
    """Handles screenshot capture from ADB and display"""

    def __init__(self, logger: DebugLogger, tabview, root, capture: Optional[ScreenCapture]):
        self.logger = logger
        self.tabview = tabview
        self.root = root
        self.capture = capture
        
        # Screenshot directory
        self.screenshot_dir = "screenshots/shopimage"
        os.makedirs(self.screenshot_dir, exist_ok=True)
        
        # UI components
        self.screenshot_canvas = None
        self.screenshot_photo = None
        self.capture_info_label = None

    def create_tab(self):
        """Create Screenshot Capture tab"""
        self.tabview.add("Screenshot Capture")
        capture_tab = self.tabview.tab("Screenshot Capture")

        # Canvas for displaying screenshot
        self.screenshot_canvas = ctk.CTkCanvas(
            capture_tab,
            bg="#1a1a1a",
            width=960,
            height=540
        )
        self.screenshot_canvas.pack(fill="both", expand=True, padx=5, pady=5)

        # Controls frame
        capture_controls = ctk.CTkFrame(capture_tab)
        capture_controls.pack(fill="x", padx=5, pady=(0, 5))

        # Capture button
        capture_btn = ctk.CTkButton(
            capture_controls,
            text="Capture from ADB",
            command=self.capture_and_save_screenshot,
            width=150
        )
        capture_btn.pack(side="left", padx=(0, 10))

        # Info label
        self.capture_info_label = ctk.CTkLabel(
            capture_controls,
            text="Click capture to save screenshot",
            font=("Arial", 10)
        )
        self.capture_info_label.pack(side="right", padx=(10, 0))

    def capture_and_save_screenshot(self):
        """Capture screenshot from ADB and save to screenshots/shopimage"""
        try:
            # Capture from ADB
            if self.capture is None:
                self.capture_info_label.configure(text="Capture not initialized")
                self.logger.log("WARNING", "Capture not initialized for screenshot")
                return

            frame = self.capture.capture_to_cv2()
            if frame is None:
                self.capture_info_label.configure(text="Capture failed")
                self.logger.log("ERROR", "Failed to capture screenshot")
                return

            # Generate filename with timestamp
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"
            output_path = os.path.join(self.screenshot_dir, filename)

            # Save screenshot
            cv2.imwrite(output_path, cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
            self.logger.log("INFO", f"Saved screenshot: {output_path}")

            # Display on canvas
            self.display_screenshot_on_canvas(frame)

            self.capture_info_label.configure(text=f"Saved: {filename}")

        except Exception as e:
            self.capture_info_label.configure(text=f"Error: {str(e)}")
            self.logger.log("ERROR", f"Screenshot capture error: {e}")

    def display_screenshot_on_canvas(self, frame: np.ndarray):
        """Display screenshot on canvas"""
        if self.screenshot_canvas is None:
            return

        # Use ImageDisplayHelper for display logic
        class PhotoRef:
            def __init__(self):
                self.photo = None
            def set(self, photo):
                self.photo = photo
        
        photo_ref = PhotoRef()
        ImageDisplayHelper.display_image_with_retry(
            frame, self.screenshot_canvas, self.root, photo_ref,
            retry_delay=200, center=False
        )
        self.screenshot_photo = photo_ref.photo

    def set_capture(self, capture: ScreenCapture):
        """Set the capture instance"""
        self.capture = capture
