"""Batch labeling component for processing multiple screenshots"""

import os
import cv2
import numpy as np
import customtkinter as ctk
from typing import Optional

from gui.utils.debug_logger import DebugLogger
from gui.utils.image_display_helper import ImageDisplayHelper


class BatchLabeling:
    """Handles batch labeling workflow for processing multiple screenshots"""

    def __init__(self, logger: DebugLogger, tabview, root):
        self.logger = logger
        self.tabview = tabview
        self.root = root

        # Directories
        self.screenshot_dir = "screenshots/shopimage"
        self.scanned_images_dir = "screenshots/shopimagescaned"
        self.templates_dir = "templates/shop_champions"
        os.makedirs(self.scanned_images_dir, exist_ok=True)

        # Scan region configuration
        self.scan_regions = []
        self.batch_labeling_current_image = None
        self.batch_labeling_extracted_images = []
        self.batch_labeling_labels = {}

        # UI components
        self.batch_mode = False
        self.batch_original_canvas = None
        self.batch_original_photo = None
        self.batch_region_canvases = []
        self.batch_region_inputs = []
        self.batch_next_btn = None

        # Slot configuration (will be set externally)
        self.slot_width = 64
        self.slot_height = 64
        self.slot_spacing = 104
        self.slot_start_x = 170
        self.slot_start_y = 50
        self.slot_count = 5
        self.shop_state_x = 880
        self.shop_state_y = 500
        self.shop_state_width = 40
        self.shop_state_height = 20

    def set_slot_config(self, width, height, spacing, start_x, start_y, count):
        """Set slot configuration"""
        self.slot_width = width
        self.slot_height = height
        self.slot_spacing = spacing
        self.slot_start_x = start_x
        self.slot_start_y = start_y
        self.slot_count = count
        self._update_scan_regions()

    def set_shop_state_config(self, x, y, width, height):
        """Set shop state box configuration"""
        self.shop_state_x = x
        self.shop_state_y = y
        self.shop_state_width = width
        self.shop_state_height = height
        self._update_scan_regions()

    def _update_scan_regions(self):
        """Update scan regions based on current slot and shop state configuration"""
        self.scan_regions = []
        
        # Champion slots
        for i in range(self.slot_count):
            x = self.slot_start_x + i * (self.slot_width + self.slot_spacing)
            y = self.slot_start_y
            self.scan_regions.append({
                'name': f'champion_{i}',
                'x': x,
                'y': y,
                'width': self.slot_width,
                'height': self.slot_height
            })
        
        # Shop state box (6th box)
        self.scan_regions.append({
            'name': 'shop_state',
            'x': self.shop_state_x,
            'y': self.shop_state_y,
            'width': self.shop_state_width,
            'height': self.shop_state_height
        })

    def start_batch_labeling(self):
        """Start batch labeling workflow"""
        # Get list of images to process
        if not os.path.exists(self.screenshot_dir):
            self.logger.log("WARNING", f"Screenshot directory not found: {self.screenshot_dir}")
            return

        image_files = [f for f in os.listdir(self.screenshot_dir) if f.endswith(('.png', '.jpg', '.jpeg'))]
        
        if not image_files:
            self.logger.log("INFO", "No images to process in screenshots/shopimage")
            return

        self.logger.log("INFO", f"Found {len(image_files)} images to process")
        
        # Process first image
        self.process_batch_image(image_files[0], image_files)

    def process_batch_image(self, image_filename: str, all_files: list):
        """Process a single image in batch labeling workflow"""
        self.logger.log("INFO", f"Processing image: {image_filename}")
        
        # Load image
        image_path = os.path.join(self.screenshot_dir, image_filename)
        img = cv2.imread(image_path)
        if img is None:
            self.logger.log("ERROR", f"Failed to load image: {image_filename}")
            return
        
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.batch_labeling_current_image = {
            'filename': image_filename,
            'path': image_path,
            'image': img_rgb,
            'all_files': all_files
        }

        # Extract regions based on scan_regions
        self.batch_labeling_extracted_images = []
        for region in self.scan_regions:
            x, y, w, h = region['x'], region['y'], region['width'], region['height']
            
            # Extract region
            region_img = img_rgb[y:y+h, x:x+w]
            self.batch_labeling_extracted_images.append({
                'name': region['name'],
                'image': region_img,
                'region': region,
                'auto_label': None  # Will be filled by auto-labeling
            })

        # Auto-label by comparing with existing templates
        self._auto_label_extracted_regions()

        # Display in template labeling tab
        self.display_batch_labeling_ui()

    def _auto_label_extracted_regions(self):
        """Auto-label extracted regions by comparing with existing templates"""
        # Load existing templates
        if not os.path.exists(self.templates_dir):
            self.logger.log("INFO", "Templates directory not found, skipping auto-labeling")
            return

        template_files = [f for f in os.listdir(self.templates_dir) if f.endswith('.png')]
        if not template_files:
            self.logger.log("INFO", "No templates found, skipping auto-labeling")
            return

        # Load templates into memory
        templates = {}
        for template_file in template_files:
            label = os.path.splitext(template_file)[0]
            template_path = os.path.join(self.templates_dir, template_file)
            template_img = cv2.imread(template_path)
            if template_img is not None:
                templates[label] = cv2.cvtColor(template_img, cv2.COLOR_BGR2RGB)
        
        self.logger.log("INFO", f"Loaded {len(templates)} templates for auto-labeling")

        # Compare each extracted region with templates
        match_threshold = 0.5  # Threshold for auto-labeling
        for extracted in self.batch_labeling_extracted_images:
            region_img = extracted['image']
            best_match = None
            best_score = 0

            for label, template_img in templates.items():
                # Resize if sizes don't match
                if region_img.shape != template_img.shape:
                    template_img = cv2.resize(template_img, (region_img.shape[1], region_img.shape[0]))

                # Template matching
                result = cv2.matchTemplate(region_img, template_img, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

                if max_val > best_score:
                    best_score = max_val
                    best_match = label

            # Auto-label if match score is above threshold
            if best_score >= match_threshold:
                extracted['auto_label'] = best_match
                self.logger.log("INFO", f"Auto-labeled {extracted['name']} as {best_match} (score: {best_score:.3f})")
            else:
                extracted['auto_label'] = None
                self.logger.log("INFO", f"No match found for {extracted['name']} (best score: {best_score:.3f})")

    def display_batch_labeling_ui(self):
        """Display batch labeling UI with original image and extracted regions"""
        self.batch_mode = True
        
        # Clear template canvas and show original image
        template_tab = self.tabview.tab("Template Labeling")
        
        # Remove existing widgets
        for widget in template_tab.winfo_children():
            widget.destroy()
        
        # Create main container
        main_frame = ctk.CTkFrame(template_tab)
        main_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Split: left side for original image, right side for extracted regions
        left_frame = ctk.CTkFrame(main_frame)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        right_frame = ctk.CTkFrame(main_frame)
        right_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))
        
        # Display original image
        original_label = ctk.CTkLabel(left_frame, text="Original Image", font=("Arial", 12, "bold"))
        original_label.pack(pady=5)
        
        self.batch_original_canvas = ctk.CTkCanvas(
            left_frame,
            bg="#1a1a1a",
            width=400,
            height=400
        )
        self.batch_original_canvas.pack(padx=5, pady=5)
        
        # Display original image
        self.root.after(100, lambda: self._display_original_image_on_canvas())
        
        # Display extracted regions with inputs
        regions_label = ctk.CTkLabel(right_frame, text="Extracted Regions", font=("Arial", 12, "bold"))
        regions_label.pack(pady=5)
        
        scroll_frame = ctk.CTkScrollableFrame(right_frame)
        scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.batch_region_canvases = []
        self.batch_region_inputs = []
        
        for i, extracted in enumerate(self.batch_labeling_extracted_images):
            region_frame = ctk.CTkFrame(scroll_frame)
            region_frame.pack(fill="x", padx=5, pady=5)
            
            # Region name label
            name_label = ctk.CTkLabel(region_frame, text=extracted['name'], font=("Arial", 10, "bold"))
            name_label.pack(side="left", padx=5)
            
            # Canvas for region image
            region_canvas = ctk.CTkCanvas(
                region_frame,
                bg="#1a1a1a",
                width=50,
                height=50
            )
            region_canvas.pack(side="left", padx=5)
            self.batch_region_canvases.append(region_canvas)
            
            # Display region image
            self._display_region_image_on_canvas(extracted['image'], region_canvas, i)
            
            # Input for label
            input_field = ctk.CTkEntry(
                region_frame,
                placeholder_text="Label...",
                width=150
            )
            input_field.pack(side="left", padx=5)
            self.batch_region_inputs.append(input_field)
            
            # Pre-fill with auto-label if found
            if extracted['auto_label']:
                input_field.insert(0, extracted['auto_label'])
                input_field.configure(state="disabled")  # Disable for auto-labeled
                # Add indicator for auto-labeled
                auto_label = ctk.CTkLabel(
                    region_frame,
                    text="✓ Auto",
                    text_color="#00FF00",
                    font=("Arial", 9, "bold")
                )
                auto_label.pack(side="left", padx=5)
            else:
                input_field.configure(state="normal")  # Enable for manual labeling
        
        # Save & Next button
        button_frame = ctk.CTkFrame(template_tab)
        button_frame.pack(fill="x", padx=5, pady=5)
        
        self.batch_next_btn = ctk.CTkButton(
            button_frame,
            text="Save & Next",
            command=self.save_and_next_batch_image,
            width=150
        )
        self.batch_next_btn.pack(side="left", padx=5)
        
        # Cancel button
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self.cancel_batch_labeling,
            width=100
        )
        cancel_btn.pack(side="left", padx=5)
        
        self.logger.log("INFO", f"Batch labeling UI displayed with {len(self.batch_labeling_extracted_images)} regions")

    def _display_original_image_on_canvas(self):
        """Display original image on canvas"""
        if self.batch_original_canvas is None or self.batch_labeling_current_image is None:
            return

        img = self.batch_labeling_current_image['image']

        # Use ImageDisplayHelper for display
        tk_img = ImageDisplayHelper.display_image_on_canvas(
            img, self.batch_original_canvas, self.root, center=True
        )
        if tk_img:
            self.batch_original_photo = tk_img

    def _display_region_image_on_canvas(self, img: np.ndarray, canvas, index: int):
        """Display region image on canvas"""
        if canvas is None:
            return

        # Use ImageDisplayHelper for display
        tk_img = ImageDisplayHelper.display_image_on_canvas(
            img, canvas, self.root, center=True
        )
        
        # Store reference
        if tk_img:
            if not hasattr(self, 'batch_region_photos'):
                self.batch_region_photos = []
            while len(self.batch_region_photos) <= index:
                self.batch_region_photos.append(None)
            self.batch_region_photos[index] = tk_img

    def save_and_next_batch_image(self):
        """Save labels and process next image"""
        # Collect labels from inputs (including auto-labeled)
        self.batch_labeling_labels = {}
        for i, input_field in enumerate(self.batch_region_inputs):
            # Check if index is valid
            if i >= len(self.batch_labeling_extracted_images):
                self.logger.log("WARNING", f"Index {i} out of range for extracted_images, skipping")
                continue
            
            # Get label from input (auto-labeled or manual)
            label = input_field.get().strip()
            if label:
                region_name = self.batch_labeling_extracted_images[i]['name']
                self.batch_labeling_labels[region_name] = label
            # Also check auto_label if input is disabled
            elif self.batch_labeling_extracted_images[i]['auto_label']:
                region_name = self.batch_labeling_extracted_images[i]['name']
                self.batch_labeling_labels[region_name] = self.batch_labeling_extracted_images[i]['auto_label']
        
        # Save and move
        self.save_batch_labeled_image()

    def cancel_batch_labeling(self):
        """Cancel batch labeling and return to normal mode"""
        self.batch_mode = False
        self.batch_labeling_current_image = None
        self.batch_labeling_extracted_images = []
        self.batch_labeling_labels = {}
        return True  # Signal to recreate template labeling tab

    def save_batch_labeled_image(self):
        """Save batch labeled image and move files"""
        if self.batch_labeling_current_image is None:
            self.logger.log("WARNING", "No current image to save")
            return False

        # Save labeled extracted regions to templates
        for extracted in self.batch_labeling_extracted_images:
            region_name = extracted['name']
            if region_name in self.batch_labeling_labels:
                label = self.batch_labeling_labels[region_name]
                output_path = os.path.join(self.templates_dir, f"{label}.png")
                
                # Save image
                cv2.imwrite(output_path, cv2.cvtColor(extracted['image'], cv2.COLOR_RGB2BGR))
                self.logger.log("INFO", f"Saved {region_name} as {label}.png")

        # Move original image to scanned directory
        original_filename = self.batch_labeling_current_image['filename']
        original_path = self.batch_labeling_current_image['path']
        scanned_path = os.path.join(self.scanned_images_dir, original_filename)
        
        import shutil
        shutil.move(original_path, scanned_path)
        self.logger.log("INFO", f"Moved {original_filename} to scanned directory")

        # Process next image
        all_files = self.batch_labeling_current_image['all_files']
        current_index = all_files.index(original_filename)
        
        if current_index + 1 < len(all_files):
            next_image = all_files[current_index + 1]
            self.process_batch_image(next_image, all_files)
        else:
            self.logger.log("INFO", "Batch labeling complete!")
            return True  # Signal to recreate template labeling tab
        
        return False
