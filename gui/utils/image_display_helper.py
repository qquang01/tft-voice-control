"""Helper class for image display operations on customtkinter canvases"""

import cv2
import numpy as np
from PIL import Image, ImageTk


class ImageDisplayHelper:
    """Helper class for displaying images on customtkinter canvases"""

    @staticmethod
    def display_image_on_canvas(img: np.ndarray, canvas, root, photo_ref=None, 
                               center: bool = True, bg_color: str = "#1a1a1a"):
        """
        Display an image on a customtkinter canvas with proper scaling and centering.
        
        Args:
            img: numpy array image (RGB format)
            canvas: customtkinter canvas widget
            root: root window for retry scheduling
            photo_ref: reference to store PhotoImage (prevents garbage collection)
            center: whether to center the image on canvas
            bg_color: background color for canvas
        """
        if canvas is None:
            return None

        canvas_width = canvas.winfo_width()
        canvas_height = canvas.winfo_height()

        # Check if canvas is ready
        if canvas_width < 100 or canvas_height < 100:
            # Retry after delay
            return None

        h, w = img.shape[:2]

        # Calculate scale to fit canvas
        scale = min(canvas_width / w, canvas_height / h)
        new_w = int(w * scale)
        new_h = int(h * scale)

        img_resized = cv2.resize(img, (new_w, new_h))

        # Convert to PIL Image (img is already RGB)
        pil_img = Image.fromarray(img_resized)
        tk_img = ImageTk.PhotoImage(pil_img)

        # Update canvas
        canvas.delete("all")
        
        if center:
            x_offset = (canvas_width - new_w) // 2
            y_offset = (canvas_height - new_h) // 2
            canvas.create_image(x_offset, y_offset, image=tk_img, anchor="nw")
        else:
            canvas.create_image(0, 0, image=tk_img, anchor="nw")

        return tk_img

    @staticmethod
    def display_image_with_retry(img: np.ndarray, canvas, root, photo_ref_var,
                                 retry_delay: int = 200, center: bool = True):
        """
        Display image on canvas with automatic retry if canvas not ready.
        
        Args:
            img: numpy array image (RGB format)
            canvas: customtkinter canvas widget
            root: root window for retry scheduling
            photo_ref_var: variable to store PhotoImage reference
            retry_delay: delay in ms for retry
            center: whether to center the image
        """
        result = ImageDisplayHelper.display_image_on_canvas(img, canvas, root, center=center)
        
        if result is None:
            # Canvas not ready, retry
            root.after(retry_delay, lambda: ImageDisplayHelper.display_image_with_retry(
                img, canvas, root, photo_ref_var, retry_delay, center
            ))
        else:
            # Store reference to prevent garbage collection
            photo_ref_var.set(result)

    @staticmethod
    def draw_slots(img: np.ndarray, slot_config: dict, scale: float, shop_state_config: dict):
        """
        Draw slot rectangles on image for visualization.
        
        Args:
            img: numpy array image to draw on (will be modified in place)
            slot_config: dict with slot configuration (width, height, spacing, start_x, start_y, count)
            scale: scale factor for drawing
            shop_state_config: dict with shop state box configuration (x, y, width, height)
        """
        # Slot size (scaled)
        slot_width = int(slot_config['width'] * scale)
        slot_height = int(slot_config['height'] * scale)
        slot_spacing = int(slot_config['spacing'] * scale)
        
        # Starting position (scaled)
        start_x = int(slot_config['start_x'] * scale)
        start_y = int(slot_config['start_y'] * scale)
        
        # Draw champion slots
        for i in range(slot_config['count']):
            x = start_x + i * (slot_width + slot_spacing)
            y = start_y
            
            # Draw rectangle (blue color for visibility)
            cv2.rectangle(img, (x, y), (x + slot_width, y + slot_height), (255, 0, 0), 2)
            
            # Draw label
            label = f"{i}"
            cv2.putText(img, label, (x, y - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 0, 0), 1)
        
        # Draw shop state box (6th box) with separate configuration
        shop_state_x = int(shop_state_config['x'] * scale)
        shop_state_y = int(shop_state_config['y'] * scale)
        shop_state_width = int(shop_state_config['width'] * scale)
        shop_state_height = int(shop_state_config['height'] * scale)
        
        # Draw rectangle (green color for visibility - different from champion slots)
        cv2.rectangle(img, (shop_state_x, shop_state_y), 
                    (shop_state_x + shop_state_width, shop_state_y + shop_state_height), 
                    (0, 255, 0), 2)
        
        # Draw label
        label = "State"
        cv2.putText(img, label, (shop_state_x, shop_state_y - 5),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0, 255, 0), 1)
