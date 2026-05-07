import cv2
import numpy as np
from typing import List, Tuple, Optional, Dict
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.screen_capture import ScreenCapture


class ChampionDetector:
    """Nhận diện tướng bằng Template Matching"""
    
    def __init__(self, screen_capture: ScreenCapture, templates_dir: str = "templates/champions"):
        """
        Khởi tạo Champion Detector
        
        Args:
            screen_capture: Instance của ScreenCapture
            templates_dir: Đường dẫn đến thư mục templates
        """
        self.capture = screen_capture
        self.templates_dir = templates_dir
        self.templates: Dict[str, np.ndarray] = {}
        self._load_templates()
    
    def _load_templates(self):
        """Load tất cả champion templates"""
        if not os.path.exists(self.templates_dir):
            os.makedirs(self.templates_dir, exist_ok=True)
            print(f"Đã tạo thư mục templates: {self.templates_dir}")
            return
        
        print(f"Đang load templates từ: {self.templates_dir}")
        for filename in os.listdir(self.templates_dir):
            if filename.endswith('.png') or filename.endswith('.jpg'):
                template_path = os.path.join(self.templates_dir, filename)
                template = cv2.imread(template_path)
                if template is not None:
                    # Extract champion name từ filename
                    champion_name = os.path.splitext(filename)[0]
                    self.templates[champion_name] = cv2.cvtColor(template, cv2.COLOR_BGR2RGB)
                    print(f"  ✓ Loaded: {champion_name}")
        
        print(f"Đã load {len(self.templates)} templates\n")
    
    def add_template(self, champion_name: str, image: np.ndarray):
        """
        Thêm template mới
        
        Args:
            champion_name: Tên tướng
            image: Ảnh template (numpy array)
        """
        self.templates[champion_name] = image
        # Lưu xuống disk
        save_path = os.path.join(self.templates_dir, f"{champion_name}.png")
        cv2.imwrite(save_path, cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
        print(f"Đã lưu template: {champion_name}")
    
    def detect_in_region(self, region: Tuple[int, int, int, int], 
                        threshold: float = 0.8) -> List[Dict]:
        """
        Nhận diện tướng trong vùng cụ thể
        
        Args:
            region: Vùng cần detect (x, y, w, h)
            threshold: Ngưỡng tương đồng
            
        Returns:
            List các dict: {'name': str, 'confidence': float, 'position': (x, y)}
        """
        screenshot = self.capture.capture_to_cv2()
        if screenshot is None:
            return []
        
        x, y, w, h = region
        roi = screenshot[y:y+h, x:x+w]
        
        results = []
        for champion_name, template in self.templates.items():
            # Template matching
            result = cv2.matchTemplate(roi, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            if max_val >= threshold:
                # Tính tọa độ tâm
                h_t, w_t = template.shape[:2]
                center_x = x + max_loc[0] + w_t // 2
                center_y = y + max_loc[1] + h_t // 2
                
                results.append({
                    'name': champion_name,
                    'confidence': float(max_val),
                    'position': (center_x, center_y),
                    'bbox': (x + max_loc[0], y + max_loc[1], w_t, h_t)
                })
        
        # Sort by confidence
        results.sort(key=lambda x: x['confidence'], reverse=True)
        return results
    
    def detect_in_shop(self, threshold: float = 0.8) -> List[Dict]:
        """
        Nhận diện tướng trong shop
        
        Args:
            threshold: Ngưỡng tương đồng
            
        Returns:
            List các tướng trong shop (theo thứ tự slot 1-5)
        """
        # Vùng shop (cần tùy chỉnh theo màn hình)
        shop_region = (400, 600, 400, 150)
        
        # Chia shop thành 5 slots
        slot_width = shop_region[2] // 5
        shop_champions = []
        
        for i in range(5):
            slot_x = shop_region[0] + i * slot_width
            slot_region = (slot_x, shop_region[1], slot_width, shop_region[3])
            
            results = self.detect_in_region(slot_region, threshold)
            if results:
                shop_champions.append(results[0])  # Lấy champion có confidence cao nhất
            else:
                shop_champions.append(None)  # Slot trống
        
        return shop_champions
    
    def detect_on_bench(self, threshold: float = 0.8) -> List[Dict]:
        """
        Nhận diện tướng trên bench
        
        Args:
            threshold: Ngưỡng tương đồng
            
        Returns:
            List các tướng trên bench (9 slots)
        """
        # Vùng bench (cần tùy chỉnh)
        bench_region = (100, 700, 800, 100)
        
        # Chia bench thành 9 slots
        slot_width = bench_region[2] // 9
        bench_champions = []
        
        for i in range(9):
            slot_x = bench_region[0] + i * slot_width
            slot_region = (slot_x, bench_region[1], slot_width, bench_region[3])
            
            results = self.detect_in_region(slot_region, threshold)
            if results:
                bench_champions.append(results[0])
            else:
                bench_champions.append(None)
        
        return bench_champions
    
    def detect_on_board(self, threshold: float = 0.8) -> List[Dict]:
        """
        Nhận diện tướng trên bàn chơi
        
        Args:
            threshold: Ngưỡng tương đồng
            
        Returns:
            List các tướng trên board
        """
        # Vùng bàn chơi (cần tùy chỉnh)
        board_region = (100, 200, 800, 400)
        
        results = self.detect_in_region(board_region, threshold)
        return results
    
    def find_champion(self, champion_name: str, threshold: float = 0.8) -> Optional[Tuple[int, int]]:
        """
        Tìm vị trí của tướng cụ thể trên toàn màn hình
        
        Args:
            champion_name: Tên tướng cần tìm
            threshold: Ngưỡng tương đồng
            
        Returns:
            Tọa độ (x, y) hoặc None
        """
        if champion_name not in self.templates:
            print(f"Không tìm thấy template: {champion_name}")
            return None
        
        screenshot = self.capture.capture_to_cv2()
        if screenshot is None:
            return None
        
        template = self.templates[champion_name]
        result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        if max_val >= threshold:
            h_t, w_t = template.shape[:2]
            center_x = max_loc[0] + w_t // 2
            center_y = max_loc[1] + h_t // 2
            print(f"Tìm thấy {champion_name} tại ({center_x}, {center_y}) với confidence: {max_val:.2f}")
            return center_x, center_y
        else:
            print(f"Không tìm thấy {champion_name} (max confidence: {max_val:.2f})")
            return None
    
    def capture_shop_slot_template(self, slot_index: int, champion_name: str):
        """
        Capture template từ shop slot
        
        Args:
            slot_index: Index slot (0-4)
            champion_name: Tên tướng để lưu
        """
        screenshot = self.capture.capture_to_cv2()
        if screenshot is None:
            return
        
        # Vùng shop
        shop_region = (400, 600, 400, 150)
        slot_width = shop_region[2] // 5
        
        slot_x = shop_region[0] + slot_index * slot_width
        slot_y = shop_region[1]
        
        # Cắt slot (có thể cần tinh chỉnh)
        template = screenshot[slot_y:slot_y+100, slot_x:slot_x+slot_width]
        
        self.add_template(champion_name, template)
    
    def visualize_detection(self, results: List[Dict], save_path: str = "detection_result.png"):
        """
        Visualize kết quả detection
        
        Args:
            results: Kết quả từ detect_in_region
            save_path: Đường dẫn lưu ảnh
        """
        screenshot = self.capture.capture_to_cv2()
        if screenshot is None:
            return
        
        img = screenshot.copy()
        
        for result in results:
            x, y, w, h = result['bbox']
            confidence = result['confidence']
            name = result['name']
            
            # Vẽ bounding box
            cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255, 0), 2)
            
            # Vẽ label
            label = f"{name}: {confidence:.2f}"
            cv2.putText(img, label, (x, y-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        cv2.imwrite(save_path, cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
        print(f"Đã lưu visualization: {save_path}")


class ItemDetector(ChampionDetector):
    """Nhận diện item bằng Template Matching"""
    
    def __init__(self, screen_capture: ScreenCapture, templates_dir: str = "templates/items"):
        super().__init__(screen_capture, templates_dir)
    
    def detect_in_inventory(self, threshold: float = 0.8) -> List[Dict]:
        """
        Nhận diện item trong inventory
        
        Args:
            threshold: Ngưỡng tương đồng
            
        Returns:
            List các item (10 slots)
        """
        # Vùng item inventory (cần tùy chỉnh)
        inv_region = (50, 600, 200, 100)
        
        # Chia thành 10 slots (2 hàng × 5 cột)
        slot_width = inv_region[2] // 5
        slot_height = inv_region[3] // 2
        
        items = []
        for i in range(10):
            row = i // 5
            col = i % 5
            slot_x = inv_region[0] + col * slot_width
            slot_y = inv_region[1] + row * slot_height
            slot_region = (slot_x, slot_y, slot_width, slot_height)
            
            results = self.detect_in_region(slot_region, threshold)
            if results:
                items.append(results[0])
            else:
                items.append(None)
        
        return items


if __name__ == "__main__":
    # Test
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from core.adb_controller import ADBController
    
    adb = ADBController()
    if adb.connect():
        capture = ScreenCapture(adb)
        detector = ChampionDetector(capture)
        
        # Test detect shop
        print("Detecting shop champions...")
        shop_champs = detector.detect_in_shop()
        for i, champ in enumerate(shop_champs):
            if champ:
                print(f"  Slot {i+1}: {champ['name']} ({champ['confidence']:.2f})")
            else:
                print(f"  Slot {i+1}: Empty")
        
        # Test capture template
        print("\nCapture template from slot 0...")
        detector.capture_shop_slot_template(0, "test_champion")
        
        adb.disconnect()
