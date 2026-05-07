"""Shop preview component for live shop display"""

import cv2
import numpy as np
import customtkinter as ctk
import time
import threading
from typing import Optional

from core.adb_controller import ADBController
from core.screen_capture import ScreenCapture
from labeling.shop_reader import ShopReader
from gui.utils.debug_logger import DebugLogger
from gui.utils.image_display_helper import ImageDisplayHelper


class ShopPreview:
    """Handles shop preview functionality"""

    def __init__(self, logger: DebugLogger, tabview, root):
        self.logger = logger
        self.tabview = tabview
        self.root = root

        # Components
        self.adb = ADBController()
        self.capture = None
        self.shop_reader = None

        # Canvas and image references
        self.shop_canvas = None
        self.shop_photo = None
        self.shop_current_frame = None
        self.shop_scale_factor = 1.0
        self.shop_background_image = None

        # UI components
        self.shop_start_btn = None
        self.shop_read_btn = None
        self.shop_refresh_bg_btn = None
        self.shop_info_label = None

        # State
        self.shop_preview_running = False

        # Slot configuration
        self.slot_width = 64
        self.slot_height = 64
        self.slot_spacing = 104
        self.slot_start_x = 170
        self.slot_start_y = 50
        self.slot_count = 5

        # Shop state box configuration
        self.shop_state_x = 880
        self.shop_state_y = 500
        self.shop_state_width = 40
        self.shop_state_height = 20

    def create_tab(self):
        """Create Shop Visualizer tab with canvas preview and controls"""
        self.tabview.add("Shop Visualizer")
        shop_tab = self.tabview.tab("Shop Visualizer")

        # Preview canvas frame
        self.shop_canvas_frame = ctk.CTkFrame(shop_tab)
        self.shop_canvas_frame.pack(fill="both", expand=True, padx=5, pady=5)

        self.shop_canvas = ctk.CTkCanvas(
            self.shop_canvas_frame,
            bg="#1a1a1a",
            width=960,
            height=540
        )
        self.shop_canvas.pack(padx=5, pady=5)
        self.logger.log("INFO", f"Shop canvas created: {self.shop_canvas is not None}, id: {id(self.shop_canvas)}")

        # Force update to ensure canvas is rendered
        self.shop_canvas.update()

        # Controls frame
        shop_controls = ctk.CTkFrame(shop_tab)
        shop_controls.pack(fill="x", padx=5, pady=(0, 5))

        # Start/Stop button
        self.shop_start_btn = ctk.CTkButton(
            shop_controls,
            text="Start Preview",
            command=self.toggle_shop_preview,
            width=120
        )
        self.shop_start_btn.pack(side="left", padx=(0, 10))

        # Read shop button
        self.shop_read_btn = ctk.CTkButton(
            shop_controls,
            text="Read Shop",
            command=self.read_shop_once,
            width=120
        )
        self.shop_read_btn.pack(side="left", padx=(0, 10))

        # Refresh Background button
        self.shop_refresh_bg_btn = ctk.CTkButton(
            shop_controls,
            text="Refresh BG",
            command=self.display_shop_background,
            width=100
        )
        self.shop_refresh_bg_btn.pack(side="left", padx=(0, 10))

        # Shop info label
        self.shop_info_label = ctk.CTkLabel(
            shop_controls,
            text="Connect ADB to start",
            font=("Arial", 10)
        )
        self.shop_info_label.pack(side="right", padx=(10, 0))

        # Initialize shop reader if possible
        self.init_shop_reader()

        # Load background image (delayed to ensure GUI is ready)
        self.root.after(100, self.load_shop_background)

    def init_shop_reader(self):
        """Initialize shop reader components"""
        try:
            if self.adb.connect():
                self.capture = ScreenCapture(self.adb)
                self.shop_reader = ShopReader(self.capture)
                self.shop_reader.load_templates()
                self.shop_info_label.configure(text="Shop reader initialized")
                self.logger.log("INFO", "Shop reader initialized")
            else:
                self.shop_info_label.configure(text="ADB not connected")
                self.logger.log("WARNING", "ADB not connected")
        except Exception as e:
            self.logger.log("ERROR", f"Failed to initialize shop reader: {e}")
            self.shop_info_label.configure(text="Initialization failed")

    def load_shop_background(self):
        """Load temp_capture.png as background image for shop preview"""
        import os
        background_path = "temp_capture.png"
        try:
            if os.path.exists(background_path):
                bg_img = cv2.imread(background_path)
                if bg_img is not None:
                    self.shop_background_image = cv2.cvtColor(bg_img, cv2.COLOR_BGR2RGB)
                    self.logger.log("INFO", f"Loaded shop background image: {self.shop_background_image.shape}")
                    # Display background after GUI is fully rendered
                    self.root.after(1000, self.display_shop_background)
                else:
                    self.logger.log("ERROR", "Failed to read background image")
            else:
                self.logger.log("WARNING", f"Background image not found: {background_path}")
        except Exception as e:
            self.logger.log("ERROR", f"Error loading background: {e}")

    def display_shop_background(self):
        """Display background image on shop canvas"""
        self.logger.log("INFO", "Refresh BG button clicked")
        self.logger.log("INFO", f"Background image exists: {self.shop_background_image is not None}")
        self.logger.log("INFO", f"Canvas exists: {self.shop_canvas is not None}")

        if self.shop_background_image is None:
            self.logger.log("WARNING", "No background image to display")
            return

        # Try to get canvas from tabview if reference is lost
        canvas = self.shop_canvas
        if canvas is None:
            # Try to get canvas from tabview
            try:
                shop_tab = self.tabview.tab("Shop Visualizer")
                # Find canvas in tab
                for widget in shop_tab.winfo_children():
                    if isinstance(widget, ctk.CTkFrame):
                        for child in widget.winfo_children():
                            if isinstance(child, ctk.CTkCanvas):
                                canvas = child
                                self.shop_canvas = canvas  # Update reference
                                self.logger.log("INFO", f"Found canvas from tabview, id: {id(canvas)}")
                                break
            except Exception as e:
                self.logger.log("ERROR", f"Failed to get canvas from tabview: {e}")

        if canvas:
            self.logger.log("INFO", f"Canvas size: {canvas.winfo_width()}x{canvas.winfo_height()}")
            self.logger.log("INFO", "Displaying background on canvas")
            self._display_image_on_canvas(self.shop_background_image, canvas)
        else:
            self.logger.log("ERROR", "Canvas is None, cannot display background")

    def _display_image_on_canvas(self, img, canvas):
        """Helper to display image on canvas with aspect ratio preserved"""
        self.logger.log("INFO", f"_display_image_on_canvas called")

        # Draw slots on image before displaying
        scale = 1.0  # Will be calculated by helper
        slot_config = {
            'width': self.slot_width,
            'height': self.slot_height,
            'spacing': self.slot_spacing,
            'start_x': self.slot_start_x,
            'start_y': self.slot_start_y,
            'count': self.slot_count
        }
        shop_state_config = {
            'x': self.shop_state_x,
            'y': self.shop_state_y,
            'width': self.shop_state_width,
            'height': self.shop_state_height
        }
        
        # Draw slots on a copy of the image
        img_with_slots = img.copy()
        canvas_width = canvas.winfo_width()
        canvas_height = canvas.winfo_height()
        if canvas_width > 0 and canvas_height > 0:
            h, w = img.shape[:2]
            scale = min(canvas_width / w, canvas_height / h)
            ImageDisplayHelper.draw_slots(img_with_slots, slot_config, scale, shop_state_config)

        # Use ImageDisplayHelper for display
        class PhotoRef:
            def __init__(self):
                self.photo = None
            def set(self, photo):
                self.photo = photo
        
        photo_ref = PhotoRef()
        ImageDisplayHelper.display_image_with_retry(
            img_with_slots, canvas, self.root, photo_ref,
            retry_delay=200, center=True
        )
        self.shop_photo = photo_ref.photo
        self.logger.log("INFO", "Canvas updated with background image")

    def toggle_shop_preview(self):
        """Toggle shop preview"""
        if not self.shop_preview_running:
            self.start_shop_preview()
        else:
            self.stop_shop_preview()

    def start_shop_preview(self):
        """Start shop preview"""
        try:
            if self.capture is None:
                self.shop_info_label.configure(text="Capture not initialized")
                self.logger.log("WARNING", "Capture not initialized for preview")
                return

            self.shop_preview_running = True
            self.shop_start_btn.configure(text="Stop Preview")
            self.shop_info_label.configure(text="Preview running...")

            # Start preview thread
            threading.Thread(target=self.shop_preview_worker, daemon=True).start()
        except Exception as e:
            self.logger.log("ERROR", f"Failed to start preview: {e}")
            self.shop_info_label.configure(text="Failed to start preview")

    def stop_shop_preview(self):
        """Stop shop preview"""
        self.shop_preview_running = False
        self.shop_start_btn.configure(text="Start Preview")
        self.shop_info_label.configure(text="Preview stopped")

    def shop_preview_worker(self):
        """Worker thread for shop preview"""
        try:
            while self.shop_preview_running:
                # Capture frame
                frame = self.capture.capture_to_cv2()
                if frame is None:
                    time.sleep(0.1)
                    continue

                self.shop_current_frame = frame

                # Update canvas on main thread
                self.root.after(0, self.update_shop_canvas)

                time.sleep(0.1)  # 10 FPS
        except Exception as e:
            self.logger.log("ERROR", f"Preview worker error: {e}")
            self.shop_preview_running = False
            self.root.after(0, lambda: self.shop_start_btn.configure(text="Start Preview"))

    def update_shop_canvas(self):
        """Update shop canvas with frame and overlay"""
        if self.shop_current_frame is None or self.shop_canvas is None:
            return

        frame = self.shop_current_frame.copy()
        
        # Draw slots on frame
        canvas_width = self.shop_canvas.winfo_width()
        canvas_height = self.shop_canvas.winfo_height()
        
        if canvas_width < 100 or canvas_height < 100:
            return
        
        h, w = frame.shape[:2]
        scale = min(canvas_width / w, canvas_height / h)
        self.shop_scale_factor = scale
        
        slot_config = {
            'width': self.slot_width,
            'height': self.slot_height,
            'spacing': self.slot_spacing,
            'start_x': self.slot_start_x,
            'start_y': self.slot_start_y,
            'count': self.slot_count
        }
        shop_state_config = {
            'x': self.shop_state_x,
            'y': self.shop_state_y,
            'width': self.shop_state_width,
            'height': self.shop_state_height
        }
        
        ImageDisplayHelper.draw_slots(frame, slot_config, scale, shop_state_config)

        # Use ImageDisplayHelper for display
        tk_img = ImageDisplayHelper.display_image_on_canvas(
            frame, self.shop_canvas, self.root, center=False
        )
        if tk_img:
            self.shop_photo = tk_img

    def read_shop_once(self):
        """Read shop once and display results"""
        if self.shop_reader is None:
            self.shop_info_label.configure(text="Shop reader not initialized")
            return

        result = self.shop_reader.read_shop(force_refresh=True)

        # Log results
        detected_count = len([s for s in result['slots'] if s['best_match']])
        self.logger.log("INFO", f"Shop read: {detected_count} champions detected")
        self.shop_info_label.configure(text=f"Detected {detected_count} champions")

    def update_slot_config(self, width, height, spacing, start_x, start_y, count):
        """Update slot configuration"""
        self.slot_width = width
        self.slot_height = height
        self.slot_spacing = spacing
        self.slot_start_x = start_x
        self.slot_start_y = start_y
        self.slot_count = count

    def update_shop_state_config(self, x, y, width, height):
        """Update shop state box configuration"""
        self.shop_state_x = x
        self.shop_state_y = y
        self.shop_state_width = width
        self.shop_state_height = height
