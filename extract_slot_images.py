"""
Extract Slot Images Tool - Trích xuất images từ 5 box 32x32

Script này:
1. Capture screenshot từ ADB hoặc load từ file
2. Extract 5 images từ các box 32x32 (theo cấu hình trong shop_visualizer)
3. Save vào images_to_label/ folder để gán nhãn
"""

import cv2
import numpy as np
import os
import sys
from typing import List

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from core.adb_controller import ADBController
from core.screen_capture import ScreenCapture


class SlotImageExtractor:
    """Tool để extract images từ 5 box 32x32"""

    def __init__(self):
        # Slot configuration (phải khớp với shop_visualizer.py)
        self.slot_width = 32
        self.slot_height = 32
        self.slot_spacing = 120
        self.slot_start_x = 200
        self.slot_start_y = 50
        self.slot_count = 5

        # Output folder
        self.output_dir = "images_to_label"
        os.makedirs(self.output_dir, exist_ok=True)

    def get_slot_regions(self) -> List[dict]:
        """Lấy danh sách 5 regions cho các slot"""
        regions = []
        for i in range(self.slot_count):
            x = self.slot_start_x + i * (self.slot_width + self.slot_spacing)
            y = self.slot_start_y
            
            regions.append({
                'index': i,
                'x': x,
                'y': y,
                'width': self.slot_width,
                'height': self.slot_height
            })
        
        return regions

    def capture_from_adb(self) -> np.ndarray:
        """Capture screenshot từ ADB"""
        try:
            adb = ADBController()
            if not adb.connect():
                print("✗ Không thể kết nối ADB")
                return None

            capture = ScreenCapture(adb)
            frame = capture.capture_to_cv2()
            
            if frame is None:
                print("✗ Không thể capture frame")
                return None

            print(f"✓ Captured from ADB: {frame.shape}")
            return frame
        except Exception as e:
            print(f"✗ Error capturing from ADB: {e}")
            return None

    def load_from_file(self, filepath: str) -> np.ndarray:
        """Load screenshot từ file"""
        if not os.path.exists(filepath):
            print(f"✗ File không tồn tại: {filepath}")
            return None

        img = cv2.imread(filepath)
        if img is None:
            print(f"✗ Không thể load image: {filepath}")
            return None

        print(f"✓ Loaded image: {filepath} ({img.shape})")
        return img

    def extract_slot_images(self, frame: np.ndarray) -> List[np.ndarray]:
        """Extract 5 slot images từ frame"""
        regions = self.get_slot_regions()
        slot_images = []

        for region in regions:
            x, y, w, h = region['x'], region['y'], region['width'], region['height']
            
            # Extract region
            slot_img = frame[y:y+h, x:x+w]
            
            # Check if region is valid
            if slot_img.shape[0] == 0 or slot_img.shape[1] == 0:
                print(f"✗ Slot {region['index']}: Invalid region ({x}, {y}, {w}, {h})")
                continue
            
            slot_images.append({
                'index': region['index'],
                'image': slot_img,
                'region': region
            })
            print(f"✓ Extracted slot {region['index']}: {slot_img.shape}")

        return slot_images

    def save_slot_images(self, slot_images: List[dict], prefix: str = "slot"):
        """Save slot images vào output folder"""
        saved_count = 0
        
        for slot in slot_images:
            index = slot['index']
            img = slot['image']
            
            # Generate filename
            filename = f"{prefix}_{index}.png"
            output_path = os.path.join(self.output_dir, filename)
            
            # Save image
            cv2.imwrite(output_path, img)
            saved_count += 1
            print(f"✓ Saved: {filename} -> {output_path}")

        print(f"\n✓ Saved {saved_count} slot images to {self.output_dir}")

    def visualize_extraction(self, frame: np.ndarray, slot_images: List[dict]):
        """Hiển thị frame với các box được extract"""
        vis_frame = frame.copy()

        for slot in slot_images:
            region = slot['region']
            x, y, w, h = region['x'], region['y'], region['width'], region['height']
            
            # Draw rectangle
            cv2.rectangle(vis_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            
            # Draw label
            cv2.putText(vis_frame, f"Slot {slot['index']}", (x, y - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # Save visualization
        vis_path = os.path.join(self.output_dir, "extraction_visualization.png")
        cv2.imwrite(vis_path, vis_frame)
        print(f"✓ Saved visualization: {vis_path}")

    def run(self, source: str = "adb"):
        """Chạy extraction process"""
        print("=== Slot Image Extractor ===")
        print(f"Slot configuration:")
        print(f"  - Width: {self.slot_width}px")
        print(f"  - Height: {self.slot_height}px")
        print(f"  - Spacing: {self.slot_spacing}px")
        print(f"  - Start X: {self.slot_start_x}px")
        print(f"  - Start Y: {self.slot_start_y}px")
        print(f"  - Count: {self.slot_count}")
        print()

        # Get frame
        if source == "adb":
            frame = self.capture_from_adb()
        else:
            frame = self.load_from_file(source)

        if frame is None:
            print("✗ Không thể lấy frame")
            return

        # Extract slot images
        print("\nExtracting slot images...")
        slot_images = self.extract_slot_images(frame)

        if not slot_images:
            print("✗ Không extract được slot images nào")
            return

        # Save images
        print("\nSaving slot images...")
        self.save_slot_images(slot_images)

        # Visualize
        print("\nCreating visualization...")
        self.visualize_extraction(frame, slot_images)

        print("\n✓ Extraction complete!")


def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description="Extract slot images from 32x32 boxes")
    parser.add_argument(
        "--source",
        choices=["adb", "file"],
        default="adb",
        help="Source: adb capture or file path"
    )
    parser.add_argument(
        "--filepath",
        help="Image file path (if source=file)"
    )

    args = parser.parse_args()

    extractor = SlotImageExtractor()

    if args.source == "file":
        if not args.filepath:
            print("✗ --filepath required when source=file")
            return
        extractor.run(args.filepath)
    else:
        extractor.run("adb")


if __name__ == "__main__":
    main()
