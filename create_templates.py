"""
Template Creation Tool - Tạo template images từ screenshot

Công cụ này cho phép:
1. Load screenshot từ file hoặc capture từ ADB
2. Select regions bằng mouse để tạo champion templates
3. Save templates vào templates/shop_champions/
"""

import cv2
import numpy as np
import os
import sys
from typing import List, Tuple

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from core.adb_controller import ADBController
from core.screen_capture import ScreenCapture


class TemplateCreator:
    """Tool để tạo template images từ screenshot"""

    def __init__(self):
        self.image = None
        self.display_image = None
        self.selection_start = None
        self.selection_end = None
        self.selecting = False
        self.regions = []  # List of (x, y, w, h, champion_name)
        self.current_champion_name = ""

    def load_image(self, image_path: str) -> bool:
        """Load image từ file"""
        if not os.path.exists(image_path):
            print(f"✗ File không tồn tại: {image_path}")
            return False

        self.image = cv2.imread(image_path)
        if self.image is None:
            print(f"✗ Không thể load image: {image_path}")
            return False

        self.display_image = self.image.copy()
        print(f"✓ Loaded image: {image_path} ({self.image.shape})")
        return True

    def capture_from_adb(self) -> bool:
        """Capture image từ ADB"""
        try:
            adb = ADBController()
            if not adb.connect():
                print("✗ Không thể kết nối ADB")
                return False

            capture = ScreenCapture(adb)
            frame = capture.capture_to_cv2()
            
            if frame is None:
                print("✗ Không thể capture frame")
                return False

            self.image = frame
            self.display_image = self.image.copy()
            print(f"✓ Captured from ADB: {self.image.shape}")
            return True
        except Exception as e:
            print(f"✗ Error capturing from ADB: {e}")
            return False

    def mouse_callback(self, event, x, y, flags, param):
        """Mouse callback cho selection"""
        if event == cv2.EVENT_LBUTTONDOWN:
            self.selection_start = (x, y)
            self.selection_end = (x, y)
            self.selecting = True

        elif event == cv2.EVENT_MOUSEMOVE:
            if self.selecting:
                self.selection_end = (x, y)
                # Update display
                temp_image = self.image.copy()
                # Draw all existing regions
                for (rx, ry, rw, rh, name) in self.regions:
                    cv2.rectangle(temp_image, (rx, ry), (rx + rw, ry + rh), (0, 255, 0), 2)
                    cv2.putText(temp_image, name, (rx, ry - 5),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                # Draw current selection
                cv2.rectangle(temp_image, self.selection_start, self.selection_end, (255, 0, 0), 2)
                self.display_image = temp_image

        elif event == cv2.EVENT_LBUTTONUP:
            if self.selecting:
                self.selecting = False
                # Calculate region
                x1, y1 = self.selection_start
                x2, y2 = self.selection_end
                
                # Ensure x1 < x2 and y1 < y2
                x = min(x1, x2)
                y = min(y1, y2)
                w = abs(x2 - x1)
                h = abs(y2 - y1)
                
                if w > 5 and h > 5:  # Minimum size
                    # Ask for champion name
                    print(f"\nSelected region: ({x}, {y}, {w}, {h})")
                    champion_name = input("Nhập tên champion (hoặc Enter để hủy): ").strip()
                    
                    if champion_name:
                        self.regions.append((x, y, w, h, champion_name))
                        print(f"✓ Added region: {champion_name}")
                    
                    # Redraw
                    temp_image = self.image.copy()
                    for (rx, ry, rw, rh, name) in self.regions:
                        cv2.rectangle(temp_image, (rx, ry), (rx + rw, ry + rh), (0, 255, 0), 2)
                        cv2.putText(temp_image, name, (rx, ry - 5),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                    self.display_image = temp_image

    def run_selection(self):
        """Chạy selection interface"""
        if self.image is None:
            print("✗ Không có image loaded")
            return

        cv2.namedWindow('Template Creator')
        cv2.setMouseCallback('Template Creator', self.mouse_callback)

        print("\n=== Template Creator ===")
        print("Instructions:")
        print("- Click và drag để select region")
        print("- Nhập tên champion khi được hỏi")
        print("- Press 's' để save tất cả templates")
        print("- Press 'c' để clear tất cả selections")
        print("- Press 'r' để redraw")
        print("- Press 'q' hoặc ESC để quit")
        print("- Press 'a' để capture từ ADB")

        while True:
            cv2.imshow('Template Creator', self.display_image)
            key = cv2.waitKey(1) & 0xFF

            if key == ord('q') or key == 27:  # q or ESC
                break
            elif key == ord('s'):  # save
                self.save_templates()
            elif key == ord('c'):  # clear
                self.regions = []
                self.display_image = self.image.copy()
                print("✓ Cleared all selections")
            elif key == ord('r'):  # redraw
                temp_image = self.image.copy()
                for (rx, ry, rw, rh, name) in self.regions:
                    cv2.rectangle(temp_image, (rx, ry), (rx + rw, ry + rh), (0, 255, 0), 2)
                    cv2.putText(temp_image, name, (rx, ry - 5),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                self.display_image = temp_image
                print("✓ Redrawn")
            elif key == ord('a'):  # capture from ADB
                if self.capture_from_adb():
                    self.regions = []  # Clear selections for new image

        cv2.destroyAllWindows()

    def save_templates(self, output_dir: str = "templates/shop_champions"):
        """Save tất cả selected regions làm templates"""
        if not self.regions:
            print("✗ Không có regions để save")
            return

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        for (x, y, w, h, name) in self.regions:
            # Extract region
            region_img = self.image[y:y+h, x:x+w]
            
            # Save
            output_path = os.path.join(output_dir, f"{name}.png")
            cv2.imwrite(output_path, region_img)
            print(f"✓ Saved: {name} -> {output_path}")

        print(f"\n✓ Saved {len(self.regions)} templates to {output_dir}")


def main():
    """Main function"""
    print("=== TFT Template Creator ===")
    
    creator = TemplateCreator()
    
    # Ask user for input source
    print("\nChọn nguồn image:")
    print("1. Load từ file")
    print("2. Capture từ ADB")
    
    choice = input("Nhập lựa chọn (1/2): ").strip()
    
    if choice == "1":
        image_path = input("Nhập đường dẫn image: ").strip()
        if not creator.load_image(image_path):
            return
    elif choice == "2":
        if not creator.capture_from_adb():
            return
    else:
        print("✗ Lựa chọn không hợp lệ")
        return
    
    # Run selection
    creator.run_selection()


if __name__ == "__main__":
    main()
