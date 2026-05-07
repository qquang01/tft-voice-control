"""Template labeling component for champion template management"""

import os
import cv2
import numpy as np
import customtkinter as ctk
from PIL import Image, ImageTk
from typing import Optional

from gui.utils.debug_logger import DebugLogger
from gui.utils.image_display_helper import ImageDisplayHelper


class TemplateLabeling:
    """Handles template labeling workflow"""

    def __init__(self, logger: DebugLogger, tabview, root):
        self.logger = logger
        self.tabview = tabview
        self.root = root

        # Folders for labeling workflow
        self.images_to_label_dir = "images_to_label"
        self.templates_dir = "templates/shop_champions"
        os.makedirs(self.images_to_label_dir, exist_ok=True)
        os.makedirs(self.templates_dir, exist_ok=True)

        # Template labeling components
        self.template_canvas = None
        self.template_images = []
        self.template_labels = {}
        self.label_input = None
        self.selected_template_index = None

    def create_tab(self):
        """Create Template Labeling tab"""
        # Check if tab already exists
        try:
            self.tabview.add("Template Labeling")
        except ValueError:
            # Tab already exists, just clear it
            pass
        template_tab = self.tabview.tab("Template Labeling")

        # Template display frame (scrollable)
        template_scroll_frame = ctk.CTkScrollableFrame(template_tab, label_text="Template Images")
        template_scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Canvas for displaying templates
        self.template_canvas = ctk.CTkCanvas(
            template_scroll_frame,
            bg="#1a1a1a",
            width=800,
            height=400
        )
        self.template_canvas.pack(padx=5, pady=5)

        # Load and display templates
        self.root.after(200, self.load_and_display_templates)

        # Label input frame
        label_frame = ctk.CTkFrame(template_tab)
        label_frame.pack(fill="x", padx=5, pady=(0, 5))

        # Label input
        label_label = ctk.CTkLabel(
            label_frame,
            text="Label:",
            font=("Arial", 10)
        )
        label_label.pack(side="left", padx=(0, 5))

        self.label_input = ctk.CTkEntry(
            label_frame,
            placeholder_text="Enter champion name...",
            width=300
        )
        self.label_input.pack(side="left", padx=(0, 10))

        # Assign label button
        assign_btn = ctk.CTkButton(
            label_frame,
            text="Assign Label",
            command=self.assign_label,
            width=120
        )
        assign_btn.pack(side="left", padx=(0, 10))

        # Save templates button
        save_btn = ctk.CTkButton(
            label_frame,
            text="Save Templates",
            command=self.save_labeled_templates,
            width=120
        )
        save_btn.pack(side="left", padx=(0, 10))

        # Refresh button
        refresh_btn = ctk.CTkButton(
            label_frame,
            text="Refresh",
            command=self.load_and_display_templates,
            width=80
        )
        refresh_btn.pack(side="left", padx=(0, 10))

        # Info label
        info_label = ctk.CTkLabel(
            label_frame,
            text="Click on template to select, then enter label",
            font=("Arial", 9),
            text_color="gray"
        )
        info_label.pack(side="right", padx=(10, 0))

    def load_and_display_templates(self):
        """Load and display template images on canvas from both templates and images_to_label folders"""
        self.template_images = []
        self.template_labels = {}
        
        # Load from templates folder (already labeled)
        if os.path.exists(self.templates_dir):
            for filename in os.listdir(self.templates_dir):
                if filename.endswith(('.png', '.jpg', '.jpeg')):
                    template_path = os.path.join(self.templates_dir, filename)
                    template_name = os.path.splitext(filename)[0]
                    
                    try:
                        img = cv2.imread(template_path)
                        if img is not None:
                            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                            self.template_images.append({
                                'name': template_name,
                                'image': img_rgb,
                                'path': template_path,
                                'source': 'templates',
                                'labeled': True
                            })
                            self.logger.log("INFO", f"Loaded template: {template_name}")
                    except Exception as e:
                        self.logger.log("ERROR", f"Failed to load template {filename}: {e}")
        
        # Load from images_to_label folder (unlabeled)
        if os.path.exists(self.images_to_label_dir):
            unlabeled_count = 0
            for filename in os.listdir(self.images_to_label_dir):
                if filename.endswith(('.png', '.jpg', '.jpeg')):
                    template_path = os.path.join(self.images_to_label_dir, filename)
                    template_name = os.path.splitext(filename)[0]
                    
                    try:
                        img = cv2.imread(template_path)
                        if img is not None:
                            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                            self.template_images.append({
                                'name': template_name,
                                'image': img_rgb,
                                'path': template_path,
                                'source': 'images_to_label',
                                'labeled': False
                            })
                            unlabeled_count += 1
                            self.logger.log("INFO", f"Loaded unlabeled image: {template_name}")
                    except Exception as e:
                        self.logger.log("ERROR", f"Failed to load unlabeled image {filename}: {e}")
            
            self.logger.log("INFO", f"Loaded {unlabeled_count} unlabeled images")

        # Display templates on canvas
        self.display_templates_on_canvas()

    def display_templates_on_canvas(self):
        """Display template images on canvas in a grid"""
        if not self.template_images or self.template_canvas is None:
            return

        self.template_canvas.delete("all")
        
        # Grid layout: 4 columns
        cols = 4
        padding = 10
        thumb_size = 100
        
        for i, template in enumerate(self.template_images):
            row = i // cols
            col = i % cols
            
            x = padding + col * (thumb_size + padding)
            y = padding + row * (thumb_size + padding + 30)  # Extra space for label
            
            # Resize image to thumbnail
            img = template['image']
            h, w = img.shape[:2]
            scale = min(thumb_size / w, thumb_size / h)
            new_w = int(w * scale)
            new_h = int(h * scale)
            img_resized = cv2.resize(img, (new_w, new_h))
            
            # Convert to PIL and display
            img_pil = Image.fromarray(img_resized)
            img_tk = ImageTk.PhotoImage(img_pil)
            
            # Store reference to prevent garbage collection
            template['tk_image'] = img_tk
            
            # Draw rectangle (highlight if selected, red if unlabeled)
            if self.selected_template_index == i:
                color = "#00FF00"  # Green for selected
            elif not template['labeled']:
                color = "#FF0000"  # Red for unlabeled
            else:
                color = "#FFFFFF"  # White for labeled
            
            self.template_canvas.create_rectangle(
                x - 2, y - 2, x + new_w + 2, y + new_h + 2,
                outline=color, width=2
            )
            
            # Display image
            self.template_canvas.create_image(x, y, image=img_tk, anchor="nw")
            
            # Display label (if assigned)
            label_text = template['name']
            if template['name'] in self.template_labels:
                label_text = f"{self.template_labels[template['name']]} ({template['name']})"
            
            self.template_canvas.create_text(
                x + new_w // 2, y + new_h + 15,
                text=label_text,
                fill="white",
                font=("Arial", 8)
            )

        # Bind click event
        self.template_canvas.bind("<Button-1>", self.on_template_click)

    def on_template_click(self, event):
        """Handle click on template image"""
        cols = 4
        padding = 10
        thumb_size = 100
        
        for i, template in enumerate(self.template_images):
            row = i // cols
            col = i % cols
            
            x = padding + col * (thumb_size + padding)
            y = padding + row * (thumb_size + padding + 30)
            
            img = template['image']
            h, w = img.shape[:2]
            scale = min(thumb_size / w, thumb_size / h)
            new_w = int(w * scale)
            new_h = int(h * scale)
            
            # Check if click is within this template's bounds
            if x <= event.x <= x + new_w and y <= event.y <= y + new_h:
                self.selected_template_index = i
                self.display_templates_on_canvas()
                
                # Auto-fill input with existing label
                template_name = template['name']
                if template_name in self.template_labels:
                    self.label_input.delete(0, "end")
                    self.label_input.insert(0, self.template_labels[template_name])
                else:
                    self.label_input.delete(0, "end")
                
                self.logger.log("INFO", f"Selected template: {template_name}")
                break

    def assign_label(self):
        """Assign label to selected template and move to templates folder if unlabeled"""
        if self.selected_template_index is None:
            self.logger.log("WARNING", "No template selected")
            return
        
        label = self.label_input.get().strip()
        if not label:
            self.logger.log("WARNING", "Label is empty")
            return
        
        template = self.template_images[self.selected_template_index]
        template_name = template['name']
        source = template['source']
        
        # If image is from images_to_label, move it to templates folder
        if source == 'images_to_label':
            old_path = template['path']
            new_path = os.path.join(self.templates_dir, f"{label}.png")
            
            try:
                # Move the file
                import shutil
                shutil.move(old_path, new_path)
                
                # Update template info
                template['path'] = new_path
                template['source'] = 'templates'
                template['name'] = label
                template['labeled'] = True
                
                self.logger.log("INFO", f"Moved '{template_name}' to templates as '{label}.png'")
            except Exception as e:
                self.logger.log("ERROR", f"Failed to move file: {e}")
                return
        
        self.template_labels[template['name']] = label
        self.logger.log("INFO", f"Assigned label '{label}' to template '{template_name}'")
        
        # Refresh display
        self.load_and_display_templates()

    def save_labeled_templates(self):
        """Save labeled templates with new filenames"""
        output_dir = "templates/shop_champions_labeled"
        os.makedirs(output_dir, exist_ok=True)
        
        saved_count = 0
        for template in self.template_images:
            template_name = template['name']
            if template_name in self.template_labels:
                label = self.template_labels[template_name]
                output_path = os.path.join(output_dir, f"{label}.png")
                
                # Save with new label name
                cv2.imwrite(output_path, cv2.cvtColor(template['image'], cv2.COLOR_RGB2BGR))
                saved_count += 1
                self.logger.log("INFO", f"Saved: {template_name} -> {label}.png")
        
        self.logger.log("INFO", f"Saved {saved_count} labeled templates to {output_dir}")
