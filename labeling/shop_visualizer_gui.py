"""
Shop Visualizer GUI - Cửa sổ hiển thị template và khung vùng shop

GUI này hiển thị:
1. Template images của các champions
2. Khung vùng (bounding boxes) cho 5 slot shop
3. Real-time preview với overlay
"""

import customtkinter as ctk
import cv2
import numpy as np
from PIL import Image, ImageTk
import os
import threading
import time
from typing import List, Dict, Optional
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.screen_capture import ScreenCapture
from core.adb_controller import ADBController
from labeling.shop_reader import ShopReader


class ShopVisualizerGUI:
    """GUI cho Shop Visualizer"""
    
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Shop Visualizer - Template & Regions")
        self.root.geometry("1400x800")
        
        # Configure theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Initialize components
        self.adb = ADBController()
        self.capture = None
        self.shop_reader = None
        self.templates = {}
        
        # State
        self.running = False
        self.current_frame = None
        self.shop_regions = []
        self.selected_region_index = -1
        
        # Create UI
        self.create_widgets()
        
        # Load templates
        self.load_templates()
        
        # Initialize shop reader
        self.init_shop_reader()
    
    def create_widgets(self):
        """Tạo widgets cho GUI"""
        
        # Main container
        self.main_container = ctk.CTkFrame(self.root)
        self.main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Split into 2 columns: Left (Templates), Right (Preview)
        self.paned_window = ctk.CTkFrame(self.main_container)
        self.paned_window.pack(fill="both", expand=True)
        
        # Left column - Templates
        self.templates_frame = ctk.CTkFrame(self.paned_window)
        self.templates_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        # Templates header
        self.templates_header = ctk.CTkLabel(
            self.templates_frame,
            text="Template Images",
            font=("Arial", 16, "bold")
        )
        self.templates_header.pack(pady=10)
        
        # Templates scrollable frame
        self.templates_scroll = ctk.CTkScrollableFrame(
            self.templates_frame,
            label_text=""
        )
        self.templates_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Template grid
        self.template_widgets = []
        
        # Right column - Preview
        self.preview_frame = ctk.CTkFrame(self.paned_window)
        self.preview_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))
        
        # Preview header
        self.preview_header = ctk.CTkLabel(
            self.preview_frame,
            text="Shop Preview with Regions",
            font=("Arial", 16, "bold")
        )
        self.preview_header.pack(pady=10)
        
        # Preview canvas
        self.canvas_frame = ctk.CTkFrame(self.preview_frame)
        self.canvas_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        self.preview_canvas = ctk.CTkCanvas(
            self.canvas_frame,
            bg="#1a1a1a"
        )
        self.preview_canvas.pack(fill="both", expand=True)
        
        # Enable mouse interaction for regions
        self.preview_canvas.bind("<Button-1>", self.on_canvas_click)
        self.preview_canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.preview_canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        
        # Controls frame
        self.controls_frame = ctk.CTkFrame(self.preview_frame)
        self.controls_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        # Start/Stop button
        self.start_btn = ctk.CTkButton(
            self.controls_frame,
            text="Start Preview",
            command=self.toggle_preview,
            width=120
        )
        self.start_btn.pack(side="left", padx=(0, 10))
        
        # Refresh templates button
        self.refresh_btn = ctk.CTkButton(
            self.controls_frame,
            text="Refresh Templates",
            command=self.load_templates,
            width=150
        )
        self.refresh_btn.pack(side="left", padx=(0, 10))
        
        # Save regions button
        self.save_btn = ctk.CTkButton(
            self.controls_frame,
            text="Save Regions",
            command=self.save_regions,
            width=120
        )
        self.save_btn.pack(side="left", padx=(0, 10))
        
        # Region info label
        self.region_info = ctk.CTkLabel(
            self.controls_frame,
            text="Click on canvas to select region",
            font=("Arial", 10)
        )
        self.region_info.pack(side="right", padx=(10, 0))
        
        # Status bar
        self.status_bar = ctk.CTkLabel(
            self.main_container,
            text="Ready",
            anchor="w"
        )
        self.status_bar.pack(fill="x", pady=(10, 0))
    
    def load_templates(self):
        """Load templates từ folder"""
        template_dir = "templates/shop_champions"
        
        # Clear existing widgets
        for widget in self.template_widgets:
            widget.destroy()
        self.template_widgets = []
        self.templates = {}
        
        if not os.path.exists(template_dir):
            self.update_status(f"Template directory không tồn tại: {template_dir}")
            return
        
        # Load templates
        for filename in os.listdir(template_dir):
            if filename.endswith(('.png', '.jpg', '.jpeg')):
                champion_name = os.path.splitext(filename)[0]
                template_path = os.path.join(template_dir, filename)
                
                # Load image
                template_img = cv2.imread(template_path)
                if template_img is not None:
                    self.templates[champion_name] = template_img
                    
                    # Create widget
                    self.create_template_widget(champion_name, template_img)
        
        self.update_status(f"Loaded {len(self.templates)} templates")
    
    def create_template_widget(self, name: str, img: np.ndarray):
        """Tạo widget hiển thị template"""
        
        # Frame cho template
        template_frame = ctk.CTkFrame(self.templates_scroll)
        template_frame.pack(fill="x", padx=5, pady=5)
        
        # Resize image cho display
        h, w = img.shape[:2]
        max_size = 80
        if h > max_size or w > max_size:
            scale = min(max_size / h, max_size / w)
            new_h, new_w = int(h * scale), int(w * scale)
            img = cv2.resize(img, (new_w, new_h))
        
        # Convert to PIL Image
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(img_rgb)
        tk_img = ImageTk.PhotoImage(pil_img)
        
        # Image label
        img_label = ctk.CTkLabel(
            template_frame,
            image=tk_img,
            text=""
        )
        img_label.image = tk_img  # Keep reference
        img_label.pack(side="left", padx=5)
        
        # Name label
        name_label = ctk.CTkLabel(
            template_frame,
            text=name,
            font=("Arial", 12)
        )
        name_label.pack(side="left", padx=5)
        
        # Delete button
        delete_btn = ctk.CTkButton(
            template_frame,
            text="×",
            width=30,
            command=lambda n=name: self.delete_template(n)
        )
        delete_btn.pack(side="right", padx=5)
        
        self.template_widgets.append(template_frame)
    
    def delete_template(self, name: str):
        """Xóa template"""
        if name in self.templates:
            del self.templates[name]
            
            # Delete file
            template_path = os.path.join("templates/shop_champions", f"{name}.png")
            if os.path.exists(template_path):
                os.remove(template_path)
            
            # Reload
            self.load_templates()
            self.update_status(f"Deleted template: {name}")
    
    def init_shop_reader(self):
        """Khởi tạo shop reader"""
        if not self.adb.connect():
            self.update_status("Không thể kết nối ADB")
            return
        
        self.capture = ScreenCapture(self.adb)
        self.shop_reader = ShopReader(self.capture)
        self.shop_regions = self.shop_reader.shop_regions
        
        self.update_status("Shop reader initialized")
    
    def toggle_preview(self):
        """Bắt/dừng preview"""
        if not self.running:
            self.start_preview()
        else:
            self.stop_preview()
    
    def start_preview(self):
        """Bắt đầu preview"""
        if self.capture is None:
            self.update_status("Capture chưa khởi tạo")
            return
        
        self.running = True
        self.start_btn.configure(text="Stop Preview")
        self.update_status("Starting preview...")
        
        # Start preview thread
        threading.Thread(target=self.preview_worker, daemon=True).start()
    
    def stop_preview(self):
        """Dừng preview"""
        self.running = False
        self.start_btn.configure(text="Start Preview")
        self.update_status("Preview stopped")
    
    def preview_worker(self):
        """Worker thread cho preview"""
        while self.running:
            # Capture frame
            frame = self.capture.capture_to_cv2()
            if frame is None:
                time.sleep(0.1)
                continue
            
            self.current_frame = frame
            
            # Update canvas on main thread
            self.root.after(0, self.update_canvas)
            
            time.sleep(0.1)  # 10 FPS
    
    def update_canvas(self):
        """Update canvas với frame và overlay"""
        if self.current_frame is None:
            return
        
        # Resize frame để fit canvas
        canvas_width = self.preview_canvas.winfo_width()
        canvas_height = self.preview_canvas.winfo_height()
        
        if canvas_width < 100 or canvas_height < 100:
            return
        
        frame = self.current_frame.copy()
        h, w = frame.shape[:2]
        
        # Calculate scale
        scale = min(canvas_width / w, canvas_height / h)
        new_w = int(w * scale)
        new_h = int(h * scale)
        
        frame_resized = cv2.resize(frame, (new_w, new_h))
        
        # Draw shop regions
        for i, region in enumerate(self.shop_regions):
            # Scale region coordinates
            x = int(region['x'] * scale)
            y = int(region['y'] * scale)
            rw = int(region['width'] * scale)
            rh = int(region['height'] * scale)
            
            # Color based on selection
            if i == self.selected_region_index:
                color = (0, 255, 0)  # Green for selected
                thickness = 3
            else:
                color = (255, 0, 0)  # Blue for normal
                thickness = 2
            
            # Draw rectangle
            cv2.rectangle(frame_resized, (x, y), (x + rw, y + rh), color, thickness)
            
            # Draw label
            label = f"Slot {i}"
            cv2.putText(frame_resized, label, (x, y - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        # Convert to PIL Image
        img_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_RGB2BGR)
        pil_img = Image.fromarray(img_rgb)
        tk_img = ImageTk.PhotoImage(pil_img)
        
        # Update canvas
        self.preview_canvas.delete("all")
        self.preview_canvas.create_image(0, 0, image=tk_img, anchor="nw")
        self.preview_canvas.image = tk_img  # Keep reference
        
        # Store scale for mouse interaction
        self.scale_factor = scale
    
    def on_canvas_click(self, event):
        """Xử lý click trên canvas"""
        if self.current_frame is None:
            return
        
        # Convert canvas coordinates to image coordinates
        if not hasattr(self, 'scale_factor'):
            return
        
        img_x = event.x / self.scale_factor
        img_y = event.y / self.scale_factor
        
        # Check if click inside any region
        for i, region in enumerate(self.shop_regions):
            x, y, w, h = region['x'], region['y'], region['width'], region['height']
            
            if x <= img_x <= x + w and y <= img_y <= y + h:
                self.selected_region_index = i
                self.region_info.configure(
                    text=f"Selected: Slot {i} ({x}, {y}, {w}x{h})"
                )
                self.update_canvas()
                return
        
        # Click outside - deselect
        self.selected_region_index = -1
        self.region_info.configure(text="No region selected")
        self.update_canvas()
    
    def on_canvas_drag(self, event):
        """Xử lý drag trên canvas (cho resize regions)"""
        # Implement drag to resize logic here
        pass
    
    def on_canvas_release(self, event):
        """Xử lý release trên canvas"""
        # Implement final resize logic here
        pass
    
    def save_regions(self):
        """Lưu shop regions vào file"""
        import json
        
        regions_file = "config/shop_regions.json"
        os.makedirs("config", exist_ok=True)
        
        with open(regions_file, 'w') as f:
            json.dump(self.shop_regions, f, indent=2)
        
        self.update_status(f"Saved regions to {regions_file}")
    
    def update_status(self, message: str):
        """Cập nhật status bar"""
        self.status_bar.configure(text=message)
    
    def run(self):
        """Chạy GUI"""
        self.root.mainloop()


if __name__ == "__main__":
    app = ShopVisualizerGUI()
    app.run()
