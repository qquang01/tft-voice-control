"""
Shop Reader - Đọc và so sánh 5 vùng ảnh trong cửa hàng TFT

Mỗi cửa hàng TFT hiển thị 5 champions. Module này đọc và so sánh 5 vùng đó
với templates để identify champions.
"""

import cv2
import numpy as np
import time
from typing import List, Dict, Tuple, Optional
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.screen_capture import ScreenCapture
from ocr.pixel_detector import PixelDetector


class ShopReader:
    """Đọc và so sánh 5 vùng ảnh trong shop TFT"""
    
    def __init__(self, screen_capture: ScreenCapture):
        """
        Khởi tạo Shop Reader
        
        Args:
            screen_capture: Instance của ScreenCapture
        """
        self.capture = screen_capture
        self.pixel_detector = PixelDetector(screen_capture)
        
        # Định nghĩa 5 vùng shop (cần tùy chỉnh theo màn hình thực tế)
        # Mặc định cho LDPlayer 1280x720
        self.shop_regions = self._define_shop_regions()
        
        # Templates cho champions
        self.templates = {}
        self.template_dir = "templates/shop_champions"
        
        # Cache
        self.last_frame = None
        self.last_results = None
        self.last_read_time = 0
        self.read_interval = 0.5  # 500ms giữa các lần đọc
    
    def _define_shop_regions(self) -> List[Dict]:
        """
        Định nghĩa 5 vùng shop
        
        Returns:
            List các dict với 'index', 'x', 'y', 'width', 'height'
        """
        # Shop thường nằm ở giữa màn hình, 5 champions ngang
        # Cần tùy chỉnh theo resolution thực tế
        screen_width, screen_height = 960, 540  # Default resolution 960x540

        # Shop region: khoảng giữa màn hình
        shop_y = screen_height - 150  # 150px từ bottom
        shop_height = 120
        shop_width = 680  # Tổng width shop
        shop_x = (screen_width - shop_width) // 2  # Center horizontally

        # Chia thành 5 slot
        slot_width = shop_width // 5
        slot_height = shop_height

        regions = []
        for i in range(5):
            regions.append({
                'index': i,
                'x': shop_x + i * slot_width,
                'y': shop_y,
                'width': slot_width,
                'height': slot_height,
                'name': f'slot_{i}'
            })

        return regions
    
    def update_shop_regions(self, custom_regions: List[Dict]):
        """
        Cập nhật regions tùy chỉnh
        
        Args:
            custom_regions: List dict với 'index', 'x', 'y', 'width', 'height'
        """
        self.shop_regions = custom_regions
        print("✓ Shop regions updated")
    
    def load_templates(self, template_dir: str = None):
        """
        Load templates từ folder
        
        Args:
            template_dir: Đường dẫn đến template folder (default: templates/shop_champions)
        """
        if template_dir:
            self.template_dir = template_dir
        
        if not os.path.exists(self.template_dir):
            print(f"⚠ Template directory không tồn tại: {self.template_dir}")
            print(f"  Tạo directory mới...")
            os.makedirs(self.template_dir, exist_ok=True)
            return
        
        # Load tất cả templates
        for filename in os.listdir(self.template_dir):
            if filename.endswith(('.png', '.jpg', '.jpeg')):
                champion_name = os.path.splitext(filename)[0]
                template_path = os.path.join(self.template_dir, filename)
                self.pixel_detector.load_template(champion_name, template_path)
                print(f"✓ Loaded template: {champion_name}")
    
    def capture_shop_frame(self) -> Optional[np.ndarray]:
        """
        Chụp frame hiện tại của màn hình
        
        Returns:
            Ảnh numpy array hoặc None
        """
        return self.capture.capture_to_cv2()
    
    def extract_slot_images(self, frame: np.ndarray) -> List[np.ndarray]:
        """
        Extract 5 slot images từ frame
        
        Args:
            frame: Full screen frame
            
        Returns:
            List 5 slot images
        """
        slot_images = []
        
        for region in self.shop_regions:
            x, y, w, h = region['x'], region['y'], region['width'], region['height']
            
            # Extract region
            slot_img = frame[y:y+h, x:x+w]
            slot_images.append(slot_img)
        
        return slot_images
    
    def compare_slot_with_templates(self, slot_image: np.ndarray, 
                                   threshold: float = 0.7) -> List[Dict]:
        """
        So sánh slot image với tất cả templates
        
        Args:
            slot_image: Slot image cần so sánh
            threshold: Ngưỡng confidence
            
        Returns:
            List các kết quả match, sorted by confidence
        """
        if not self.pixel_detector.templates:
            print("⚠ Không có templates loaded")
            return []
        
        matches = []
        
        for template_name, template_img in self.pixel_detector.templates.items():
            # Template matching
            result = cv2.matchTemplate(slot_image, template_img, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            if max_val >= threshold:
                matches.append({
                    'champion': template_name,
                    'confidence': max_val,
                    'location': max_loc
                })
        
        # Sort by confidence (descending)
        matches.sort(key=lambda x: x['confidence'], reverse=True)
        
        return matches
    
    def read_shop(self, force_refresh: bool = False) -> Dict:
        """
        Đọc shop và identify 5 champions
        
        Args:
            force_refresh: Bỏ qua cache, đọc mới
            
        Returns:
            Dict với 'timestamp', 'slots': List[Dict]
        """
        current_time = time.time()
        
        # Check cache
        if not force_refresh and (current_time - self.last_read_time < self.read_interval):
            return self.last_results
        
        # Capture frame
        frame = self.capture_shop_frame()
        if frame is None:
            print("✗ Không thể capture frame")
            return {'error': 'capture_failed'}
        
        self.last_frame = frame
        
        # Extract slot images
        slot_images = self.extract_slot_images(frame)
        
        # Compare each slot with templates
        slots = []
        for i, slot_img in enumerate(slot_images):
            matches = self.compare_slot_with_templates(slot_img)
            
            slot_result = {
                'index': i,
                'region': self.shop_regions[i],
                'matches': matches[:3],  # Top 3 matches
                'best_match': matches[0] if matches else None,
                'has_champion': len(matches) > 0
            }
            slots.append(slot_result)
        
        # Cache results
        self.last_results = {
            'timestamp': current_time,
            'slots': slots,
            'frame_shape': frame.shape
        }
        self.last_read_time = current_time
        
        return self.last_results
    
    def get_shop_summary(self, shop_result: Dict) -> str:
        """
        Lấy summary của shop result
        
        Args:
            shop_result: Result từ read_shop()
            
        Returns:
            String summary
        """
        if 'error' in shop_result:
            return f"Error: {shop_result['error']}"
        
        summary_lines = []
        summary_lines.append(f"Shop Reading at {time.strftime('%H:%M:%S', time.localtime(shop_result['timestamp']))}")
        summary_lines.append("-" * 50)
        
        for slot in shop_result['slots']:
            if slot['best_match']:
                champion = slot['best_match']['champion']
                conf = slot['best_match']['confidence']
                summary_lines.append(f"Slot {slot['index']}: {champion} ({conf:.2f})")
            else:
                summary_lines.append(f"Slot {slot['index']}: Empty (no match)")
        
        return "\n".join(summary_lines)
    
    def save_slot_templates(self, slot_index: int, champion_name: str):
        """
        Save slot image làm template cho champion
        
        Args:
            slot_index: Index của slot (0-4)
            champion_name: Tên champion
        """
        if self.last_frame is None:
            print("✗ Không có frame hiện tại")
            return
        
        # Extract slot image
        slot_images = self.extract_slot_images(self.last_frame)
        if slot_index >= len(slot_images):
            print(f"✗ Slot index {slot_index} không hợp lệ")
            return
        
        slot_img = slot_images[slot_index]
        
        # Save template
        os.makedirs(self.template_dir, exist_ok=True)
        template_path = os.path.join(self.template_dir, f"{champion_name}.png")
        
        # Convert RGB to BGR cho OpenCV
        slot_img_bgr = cv2.cvtColor(slot_img, cv2.COLOR_RGB2BGR)
        cv2.imwrite(template_path, slot_img_bgr)
        
        print(f"✓ Saved template: {champion_name} -> {template_path}")
        
        # Reload templates
        self.load_templates()


class ShopVisualizer:
    """Visualizer cho shop reader"""
    
    @staticmethod
    def visualize_shop(frame: np.ndarray, shop_regions: List[Dict], 
                      results: List[Dict]) -> np.ndarray:
        """
        Visualize shop với bounding boxes và labels
        
        Args:
            frame: Original frame
            shop_regions: Shop regions
            results: Slot results
            
        Returns:
            Frame với visualizations
        """
        vis_frame = frame.copy()
        
        for slot in results:
            region = slot['region']
            x, y, w, h = region['x'], region['y'], region['width'], region['height']
            
            # Draw bounding box
            color = (0, 255, 0) if slot['best_match'] else (0, 0, 255)
            cv2.rectangle(vis_frame, (x, y), (x+w, y+h), color, 2)
            
            # Draw label
            if slot['best_match']:
                champion = slot['best_match']['champion']
                conf = slot['best_match']['confidence']
                label = f"{champion} ({conf:.2f})"
            else:
                label = "Empty"
            
            cv2.putText(vis_frame, label, (x, y-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        return vis_frame
    
    @staticmethod
    def save_visualization(vis_frame: np.ndarray, output_path: str):
        """Save visualization"""
        vis_frame_bgr = cv2.cvtColor(vis_frame, cv2.COLOR_RGB2BGR)
        cv2.imwrite(output_path, vis_frame_bgr)
        print(f"✓ Saved visualization: {output_path}")


if __name__ == "__main__":
    # Test
    from core.adb_controller import ADBController
    
    print("=== Shop Reader Test ===")
    
    # Kết nối ADB
    adb = ADBController()
    if not adb.connect():
        print("✗ Không thể kết nối ADB")
        exit(1)
    
    # Khởi tạo
    capture = ScreenCapture(adb)
    shop_reader = ShopReader(capture)
    
    # Load templates
    print("\nLoading templates...")
    shop_reader.load_templates()
    
    # Đọc shop
    print("\nReading shop...")
    result = shop_reader.read_shop(force_refresh=True)
    
    # Print summary
    print("\n" + shop_reader.get_shop_summary(result))
    
    # Visualize
    if shop_reader.last_frame is not None:
        vis_frame = ShopVisualizer.visualize_shop(
            shop_reader.last_frame,
            shop_reader.shop_regions,
            result['slots']
        )
        ShopVisualizer.save_visualization(vis_frame, "shop_visualization.png")
