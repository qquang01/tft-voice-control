import cv2
import numpy as np
import time
from typing import List, Tuple, Optional, Dict
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.screen_capture import ScreenCapture


class OCRReader:
    """Đọc text từ màn hình sử dụng OCR"""
    
    def __init__(self, screen_capture: ScreenCapture, use_easyocr: bool = True):
        """
        Khởi tạo OCR Reader
        
        Args:
            screen_capture: Instance của ScreenCapture
            use_easyocr: True để dùng EasyOCR, False để dùng Tesseract
        """
        self.capture = screen_capture
        self.use_easyocr = use_easyocr
        self.reader = None
        
        if use_easyocr:
            self._init_easyocr()
        else:
            self._init_tesseract()
    
    def _init_easyocr(self):
        """Khởi tạo EasyOCR"""
        try:
            import easyocr
            print("Đang khởi tạo EasyOCR...")
            self.reader = easyocr.Reader(['en', 'vi'], gpu=False)
            print("✓ EasyOCR đã khởi tạo")
        except ImportError:
            print("✗ Chưa cài đặt EasyOCR. Cài đặt: pip install easyocr")
            raise
        except Exception as e:
            print(f"✗ Lỗi khởi tạo EasyOCR: {e}")
            raise
    
    def _init_tesseract(self):
        """Khởi tạo Tesseract OCR"""
        try:
            import pytesseract
            print("Đang khởi tạo Tesseract...")
            # Kiểm tra Tesseract đã cài
            pytesseract.get_tesseract_version()
            self.reader = pytesseract
            print("✓ Tesseract đã khởi tạo")
        except ImportError:
            print("✗ Chưa cài đặt pytesseract. Cài đặt: pip install pytesseract")
            raise
        except Exception as e:
            print(f"✗ Lỗi khởi tạo Tesseract: {e}")
            raise
    
    def read_text(self, region: Tuple[int, int, int, int] = None) -> List[Dict]:
        """
        Đọc text từ màn hình
        
        Args:
            region: Vùng cần đọc (x, y, width, height), None để đọc toàn màn hình
            
        Returns:
            List các dict chứa thông tin text: {'text': str, 'bbox': (x, y, w, h), 'conf': float}
        """
        # Chụp màn hình
        img = self.capture.capture_to_cv2()
        if img is None:
            return []
        
        # Cắt vùng nếu có
        if region:
            x, y, w, h = region
            img = img[y:y+h, x:x+w]
        
        # Đọc text
        if self.use_easyocr:
            return self._read_easyocr(img, region)
        else:
            return self._read_tesseract(img, region)
    
    def _read_easyocr(self, img: np.ndarray, region: Tuple[int, int, int, int] = None) -> List[Dict]:
        """Đọc text bằng EasyOCR"""
        results = self.reader.readtext(img)
        
        output = []
        for bbox, text, conf in results:
            # bbox là 4 điểm: [(x1,y1), (x2,y2), (x3,y3), (x4,y4)]
            x_coords = [p[0] for p in bbox]
            y_coords = [p[1] for p in bbox]
            x, y = min(x_coords), min(y_coords)
            w, h = max(x_coords) - x, max(y_coords) - y
            
            # Điều chỉnh tọa độ nếu có region
            if region:
                x += region[0]
                y += region[1]
            
            output.append({
                'text': text,
                'bbox': (int(x), int(y), int(w), int(h)),
                'conf': float(conf)
            })
        
        return output
    
    def _read_tesseract(self, img: np.ndarray, region: Tuple[int, int, int, int] = None) -> List[Dict]:
        """Đọc text bằng Tesseract"""
        # Chuyển sang grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        
        # Lấy text và bounding boxes
        data = self.reader.image_to_data(gray, output_type=self.reader.Output.DICT)
        
        output = []
        n_boxes = len(data['text'])
        for i in range(n_boxes):
            text = data['text'][i].strip()
            conf = int(data['conf'][i])
            
            if text and conf > 0:
                x, y = data['left'][i], data['top'][i]
                w, h = data['width'][i], data['height'][i]
                
                # Điều chỉnh tọa độ nếu có region
                if region:
                    x += region[0]
                    y += region[1]
                
                output.append({
                    'text': text,
                    'bbox': (int(x), int(y), int(w), int(h)),
                    'conf': conf / 100.0
                })
        
        return output
    
    def find_text(self, text: str, region: Tuple[int, int, int, int] = None, 
                  threshold: float = 0.5) -> Optional[Tuple[int, int]]:
        """
        Tìm text cụ thể trên màn hình
        
        Args:
            text: Text cần tìm
            region: Vùng tìm kiếm
            threshold: Ngưỡng tương đồng (chỉ cho EasyOCR)
            
        Returns:
            Tọa độ (x, y) của text hoặc None
        """
        results = self.read_text(region)
        
        for result in results:
            if text.lower() in result['text'].lower():
                x, y, w, h = result['bbox']
                center_x = x + w // 2
                center_y = y + h // 2
                print(f"Tìm thấy '{text}' tại ({center_x}, {center_y})")
                return center_x, center_y
        
        print(f"Không tìm thấy '{text}'")
        return None
    
    def find_all_text(self, text: str, region: Tuple[int, int, int, int] = None) -> List[Tuple[int, int]]:
        """
        Tìm tất cả vị trí của text
        
        Args:
            text: Text cần tìm
            region: Vùng tìm kiếm
            
        Returns:
            List các tọa độ (x, y)
        """
        results = self.read_text(region)
        positions = []
        
        for result in results:
            if text.lower() in result['text'].lower():
                x, y, w, h = result['bbox']
                center_x = x + w // 2
                center_y = y + h // 2
                positions.append((center_x, center_y))
        
        return positions
    
    def read_numbers(self, region: Tuple[int, int, int, int] = None) -> List[int]:
        """
        Đọc các số từ màn hình
        
        Args:
            region: Vùng cần đọc
            
        Returns:
            List các số tìm thấy
        """
        results = self.read_text(region)
        numbers = []
        
        for result in results:
            text = result['text']
            # Extract numbers
            import re
            nums = re.findall(r'\d+', text)
            for num in nums:
                numbers.append(int(num))
        
        return numbers


class TFTUIReader:
    """Đọc UI cụ thể của TFT"""
    
    def __init__(self, ocr_reader: OCRReader):
        """
        Khởi tạo TFT UI Reader
        
        Args:
            ocr_reader: Instance của OCRReader
        """
        self.ocr = ocr_reader
        
        # Các vùng UI quan trọng của TFT (cần tùy chỉnh theo màn hình)
        self.ui_regions = {
            'gold': (50, 50, 100, 30),  # Vùng hiển thị gold
            'health': (150, 50, 100, 30),  # Vùng hiển thị health
            'level': (250, 50, 50, 30),  # Vùng hiển thị level
            'shop': (400, 600, 400, 150),  # Vùng shop
            'bench': (100, 700, 800, 100),  # Vùng bench
            'board': (100, 200, 800, 400),  # Vùng bàn chơi
        }
    
    def read_gold(self) -> Optional[int]:
        """Đọc số gold hiện tại"""
        results = self.ocr.read_text(self.ui_regions['gold'])
        for result in results:
            try:
                return int(result['text'])
            except ValueError:
                continue
        return None
    
    def read_health(self) -> Optional[int]:
        """Đọc số health hiện tại"""
        results = self.ocr.read_text(self.ui_regions['health'])
        for result in results:
            try:
                return int(result['text'])
            except ValueError:
                continue
        return None
    
    def read_level(self) -> Optional[int]:
        """Đọc level hiện tại"""
        results = self.ocr.read_text(self.ui_regions['level'])
        for result in results:
            try:
                return int(result['text'])
            except ValueError:
                continue
        return None
    
    def read_shop_champions(self) -> List[str]:
        """Đọc tên tướng trong shop"""
        results = self.ocr.read_text(self.ui_regions['shop'])
        champions = []
        for result in results:
            text = result['text'].strip()
            if text and len(text) > 2:  # Filter noise
                champions.append(text)
        return champions
    
    def find_champion_in_shop(self, champion_name: str) -> Optional[Tuple[int, int]]:
        """Tìm tướng cụ thể trong shop"""
        return self.ocr.find_text(champion_name, self.ui_regions['shop'])
    
    def update_ui_regions(self, new_regions: Dict[str, Tuple[int, int, int, int]]):
        """
        Cập nhật vùng UI
        
        Args:
            new_regions: Dict mapping tên vùng -> (x, y, w, h)
        """
        self.ui_regions.update(new_regions)
