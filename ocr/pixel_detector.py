import cv2
import numpy as np
from typing import Tuple, List, Optional, Dict
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.screen_capture import ScreenCapture


class PixelDetector:
    """Phát hiện UI elements bằng pixel analysis"""
    
    def __init__(self, screen_capture: ScreenCapture):
        """
        Khởi tạo Pixel Detector
        
        Args:
            screen_capture: Instance của ScreenCapture
        """
        self.capture = screen_capture
        self.templates = {}
        self.color_thresholds = {}
    
    def load_template(self, name: str, image_path: str):
        """
        Load template image cho detection
        
        Args:
            name: Tên template
            image_path: Đường dẫn ảnh template
        """
        template = cv2.imread(image_path)
        if template is not None:
            self.templates[name] = cv2.cvtColor(template, cv2.COLOR_BGR2RGB)
            print(f"✓ Đã load template: {name}")
        else:
            print(f"✗ Không thể load template: {image_path}")
    
    def find_template(self, name: str, threshold: float = 0.8, 
                     region: Tuple[int, int, int, int] = None) -> Optional[Tuple[int, int]]:
        """
        Tìm template trên màn hình
        
        Args:
            name: Tên template
            threshold: Ngưỡng tương đồng (0-1)
            region: Vùng tìm kiếm (x, y, w, h)
            
        Returns:
            Tọa độ (x, y) tâm template hoặc None
        """
        if name not in self.templates:
            print(f"Template '{name}' không tồn tại")
            return None
        
        template = self.templates[name]
        img = self.capture.capture_to_cv2()
        
        if img is None:
            return None
        
        # Cắt vùng nếu có
        if region:
            x, y, w, h = region
            img = img[y:y+h, x:x+w]
        
        # Template matching
        result = cv2.matchTemplate(img, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        if max_val >= threshold:
            h_t, w_t = template.shape[:2]
            center_x = max_loc[0] + w_t // 2
            center_y = max_loc[1] + h_t // 2
            
            # Điều chỉnh nếu có region
            if region:
                center_x += region[0]
                center_y += region[1]
            
            print(f"Tìm thấy {name} tại ({center_x}, {center_y}) với confidence: {max_val:.2f}")
            return center_x, center_y
        else:
            print(f"Không tìm thấy {name} (max confidence: {max_val:.2f})")
            return None
    
    def find_all_templates(self, name: str, threshold: float = 0.8,
                          region: Tuple[int, int, int, int] = None) -> List[Tuple[int, int]]:
        """
        Tìm tất cả vị trí của template
        
        Args:
            name: Tên template
            threshold: Ngưỡng tương đồng
            region: Vùng tìm kiếm
            
        Returns:
            List các tọa độ (x, y)
        """
        if name not in self.templates:
            return []
        
        template = self.templates[name]
        img = self.capture.capture_to_cv2()
        
        if img is None:
            return []
        
        if region:
            x, y, w, h = region
            img = img[y:y+h, x:x+w]
        
        result = cv2.matchTemplate(img, template, cv2.TM_CCOEFF_NORMED)
        locations = np.where(result >= threshold)
        
        positions = []
        h_t, w_t = template.shape[:2]
        for pt in zip(*locations[::-1]):
            center_x = pt[0] + w_t // 2
            center_y = pt[1] + h_t // 2
            
            if region:
                center_x += region[0]
                center_y += region[1]
            
            positions.append((center_x, center_y))
        
        # Non-maximum suppression để tránh trùng lặp
        return self._non_max_suppression(positions, w_t, h_t)
    
    def _non_max_suppression(self, positions: List[Tuple[int, int]], 
                            w: int, h: int, overlap_threshold: float = 0.5) -> List[Tuple[int, int]]:
        """Loại bỏ các vị trí trùng lặp"""
        if not positions:
            return []
        
        positions = np.array(positions)
        pick = []
        
        x1 = positions[:, 0] - w // 2
        y1 = positions[:, 1] - h // 2
        x2 = positions[:, 0] + w // 2
        y2 = positions[:, 1] + h // 2
        
        area = (x2 - x1 + 1) * (y2 - y1 + 1)
        idxs = np.argsort(y2)
        
        while len(idxs) > 0:
            last = len(idxs) - 1
            i = idxs[last]
            pick.append(i)
            
            xx1 = np.maximum(x1[i], x1[idxs[:last]])
            yy1 = np.maximum(y1[i], y1[idxs[:last]])
            xx2 = np.minimum(x2[i], x2[idxs[:last]])
            yy2 = np.minimum(y2[i], y2[idxs[:last]])
            
            w_area = np.maximum(0, xx2 - xx1 + 1)
            h_area = np.maximum(0, yy2 - yy1 + 1)
            overlap = (w_area * h_area) / area[idxs[:last]]
            
            idxs = np.delete(idxs, np.concatenate(([last], np.where(overlap > overlap_threshold)[0])))
        
        return [tuple(positions[i]) for i in pick]
    
    def find_color(self, color: Tuple[int, int, int], tolerance: int = 30,
                  region: Tuple[int, int, int, int] = None) -> Optional[Tuple[int, int]]:
        """
        Tìm vị trí của màu cụ thể
        
        Args:
            color: Màu cần tìm (R, G, B)
            tolerance: Độ sai số màu
            region: Vùng tìm kiếm
            
        Returns:
            Tọa độ (x, y) đầu tiên hoặc None
        """
        img = self.capture.capture_to_cv2()
        if img is None:
            return None
        
        if region:
            x, y, w, h = region
            img = img[y:y+h, x:x+w]
        
        r, g, b = color
        lower = np.array([max(0, r - tolerance), max(0, g - tolerance), max(0, b - tolerance)])
        upper = np.array([min(255, r + tolerance), min(255, g + tolerance), min(255, b + tolerance)])
        
        mask = cv2.inRange(img, lower, upper)
        locations = np.where(mask > 0)
        
        if len(locations[0]) > 0:
            y_pos = locations[0][0]
            x_pos = locations[1][0]
            
            if region:
                x_pos += region[0]
                y_pos += region[1]
            
            print(f"Tìm thấy màu tại ({x_pos}, {y_pos})")
            return x_pos, y_pos
        
        print("Không tìm thấy màu")
        return None
    
    def find_all_colors(self, color: Tuple[int, int, int], tolerance: int = 30,
                       region: Tuple[int, int, int, int] = None) -> List[Tuple[int, int]]:
        """
        Tìm tất cả vị trí của màu
        
        Args:
            color: Màu cần tìm
            tolerance: Độ sai số
            region: Vùng tìm kiếm
            
        Returns:
            List các tọa độ (x, y)
        """
        img = self.capture.capture_to_cv2()
        if img is None:
            return []
        
        if region:
            x, y, w, h = region
            img = img[y:y+h, x:x+w]
        
        r, g, b = color
        lower = np.array([max(0, r - tolerance), max(0, g - tolerance), max(0, b - tolerance)])
        upper = np.array([min(255, r + tolerance), min(255, g + tolerance), min(255, b + tolerance)])
        
        mask = cv2.inRange(img, lower, upper)
        locations = np.where(mask > 0)
        
        positions = []
        for y_pos, x_pos in zip(locations[0], locations[1]):
            if region:
                x_pos += region[0]
                y_pos += region[1]
            positions.append((x_pos, y_pos))
        
        return positions
    
    def detect_button(self, region: Tuple[int, int, int, int], 
                     expected_color: Tuple[int, int, int] = None) -> bool:
        """
        Phát hiện button trong vùng
        
        Args:
            region: Vùng button (x, y, w, h)
            expected_color: Màu mong muốn (tùy chọn)
            
        Returns:
            True nếu phát hiện button
        """
        img = self.capture.capture_to_cv2()
        if img is None:
            return False
        
        x, y, w, h = region
        roi = img[y:y+h, x:x+w]
        
        # Phát hiện edge
        gray = cv2.cvtColor(roi, cv2.COLOR_RGB2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        edge_count = np.sum(edges > 0)
        
        # Nếu có đủ edge, coi như có button
        if edge_count > w * h * 0.1:  # 10% pixel là edge
            return True
        
        return False
    
    def count_pixels_in_region(self, region: Tuple[int, int, int, int], 
                               color: Tuple[int, int, int], tolerance: int = 30) -> int:
        """
        Đếm số pixel có màu trong vùng
        
        Args:
            region: Vùng đếm (x, y, w, h)
            color: Màu cần đếm
            tolerance: Độ sai số
            
        Returns:
            Số pixel tìm thấy
        """
        img = self.capture.capture_to_cv2()
        if img is None:
            return 0
        
        x, y, w, h = region
        roi = img[y:y+h, x:x+w]
        
        r, g, b = color
        lower = np.array([max(0, r - tolerance), max(0, g - tolerance), max(0, b - tolerance)])
        upper = np.array([min(255, r + tolerance), min(255, g + tolerance), min(255, b + tolerance)])
        
        mask = cv2.inRange(roi, lower, upper)
        return np.sum(mask > 0)


class TFTPixelDetector(PixelDetector):
    """Pixel detector chuyên dụng cho TFT"""
    
    def __init__(self, screen_capture: ScreenCapture):
        super().__init__(screen_capture)
        
        # Màu quan trọng trong TFT (cần tùy chỉnh)
        self.tft_colors = {
            'gold': (255, 215, 0),  # Vàng
            'health_green': (0, 255, 0),  # Xanh lá
            'health_red': (255, 0, 0),  # Đỏ
            'rarity_common': (169, 169, 169),  # Xám
            'rarity_rare': (0, 191, 255),  # Xanh dương
            'rarity_epic': (148, 0, 211),  # Tím
            'rarity_legendary': (255, 215, 0),  # Vàng
        }
    
    def is_shop_open(self) -> bool:
        """Kiểm tra shop có mở không"""
        # Kiểm tra màu hoặc template của shop
        shop_region = (400, 600, 400, 150)
        return self.detect_button(shop_region)
    
    def find_champion_slots(self) -> List[Tuple[int, int]]:
        """Tìm các slot tướng trên bench"""
        # Sử dụng màu hoặc pattern để tìm slot
        bench_region = (100, 700, 800, 100)
        positions = []
        
        # Chia bench thành 9 slot
        for i in range(9):
            slot_x = bench_region[0] + i * (bench_region[2] // 9) + (bench_region[2] // 18)
            slot_y = bench_region[1] + bench_region[3] // 2
            positions.append((slot_x, slot_y))
        
        return positions
    
    def find_item_slots(self) -> List[Tuple[int, int]]:
        """Tìm các slot item"""
        # Vùng item (cần tùy chỉnh)
        item_region = (50, 600, 100, 100)
        positions = []
        
        for i in range(10):  # 10 slot item
            slot_x = item_region[0] + (i % 5) * 60
            slot_y = item_region[1] + (i // 5) * 60
            positions.append((slot_x, slot_y))
        
        return positions
    
    def detect_level_up_available(self) -> bool:
        """Kiểm tra có thể lên cấp không"""
        # Kiểm tra nút level up (cần tùy chỉnh vị trí)
        level_up_region = (900, 700, 50, 50)
        return self.detect_button(level_up_region)
