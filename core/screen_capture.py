import subprocess
import time
import os
import cv2
import numpy as np
from typing import Optional, Tuple
from .adb_controller import ADBController


class ScreenCapture:
    """Screen Capture cho LDPlayer"""
    
    def __init__(self, adb_controller: ADBController):
        """
        Khởi tạo Screen Capture

        Args:
            adb_controller: Instance của ADBController
        """
        self.adb = adb_controller
        self._cached_frame = None
        self._cache_timestamp = 0
        self._cache_ttl = 0.1  # 100ms TTL cho cache
        self.temp_screenshot = "temp_screenshot.png"
    
    def capture(self, save_path: str = None) -> Optional[str]:
        """
        Chụp màn hình và lưu xuống máy
        
        Args:
            save_path: Đường dẫn lưu ảnh (nếu None, lưu vào temp)
            
        Returns:
            Đường dẫn ảnh hoặc None nếu thất bại
        """
        if save_path is None:
            save_path = self.temp_screenshot
        
        # Chụp màn hình sử dụng screencap
        success, output = self.adb._run_adb_command(
            f"-s {self.adb.device_id} shell screencap -p /sdcard/screenshot.png"
        )
        
        if not success:
            print(f"Lỗi chụp màn hình: {output}")
            return None
        
        # Pull ảnh về máy
        success, output = self.adb._run_adb_command(
            f'-s {self.adb.device_id} pull /sdcard/screenshot.png "{save_path}"'
        )
        
        if success:
            print(f"Đã chụp màn hình: {save_path}")
            return save_path
        else:
            print(f"Lỗi pull ảnh: {output}")
            return None
    
    def capture_to_cv2(self, force_refresh=False) -> Optional[np.ndarray]:
        """
        Chụp màn hình và trả về ảnh dưới dạng numpy array (OpenCV)

        Args:
            force_refresh: Bắt buộc capture mới bỏ qua cache

        Returns:
            Ảnh dưới dạng numpy array hoặc None nếu thất bại
        """
        import time

        current_time = time.time()

        # Check cache nếu không force refresh
        if not force_refresh and self._cached_frame is not None:
            # Check TTL
            if current_time - self._cache_timestamp < self._cache_ttl:
                return self._cached_frame

        # Capture mới
        temp_path = "temp_capture.png"
        if self._capture_internal(temp_path):
            img = cv2.imread(temp_path)
            if img is not None:
                # Cache frame
                self._cached_frame = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                self._cache_timestamp = current_time
                return self._cached_frame

        return None

    def _capture_internal(self, save_path: str) -> Optional[str]:
        """
        Internal capture method without logging
        """
        if save_path is None:
            save_path = self.temp_screenshot

        # Execute screencap
        success, output = self.adb._run_adb_command(
            f'-s {self.adb.device_id} shell screencap -p /sdcard/screenshot.png'
        )

        if not success:
            return None

        # Pull ảnh về máy
        success, output = self.adb._run_adb_command(
            f'-s {self.adb.device_id} pull /sdcard/screenshot.png "{save_path}"'
        )

        if success:
            return save_path
        else:
            return None
    
    def capture_fast(self) -> Optional[np.ndarray]:
        """
        Chụp màn hình nhanh hơn bằng cách stream
        
        Returns:
            Ảnh dưới dạng numpy array hoặc None nếu thất bại
        """
        # Sử dụng minicap nếu có cài đặt, hoặc fallback về screencap
        # Đây là phương pháp tối ưu hơn nhưng cần cài đặt thêm
        return self.capture_to_cv2()
    
    def find_image(self, template_path: str, threshold: float = 0.8) -> Optional[Tuple[int, int]]:
        """
        Tìm hình ảnh template trên màn hình
        
        Args:
            template_path: Đường dẫn đến ảnh template
            threshold: Ngưỡng tương đồng (0-1)
            
        Returns:
            Tọa độ (x, y) của tâm template hoặc None nếu không tìm thấy
        """
        # Chụp màn hình
        screen = self.capture_to_cv2()
        if screen is None:
            return None
        
        # Đọc template
        template = cv2.imread(template_path)
        if template is None:
            print(f"Không thể đọc template: {template_path}")
            return None
        
        # Chuyển sang grayscale
        screen_gray = cv2.cvtColor(screen, cv2.COLOR_RGB2GRAY)
        template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
        
        # Template matching
        result = cv2.matchTemplate(screen_gray, template_gray, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        if max_val >= threshold:
            # Tính tọa độ tâm
            h, w = template_gray.shape
            center_x = max_loc[0] + w // 2
            center_y = max_loc[1] + h // 2
            print(f"Tìm thấy template tại ({center_x}, {center_y}) với độ tin cậy: {max_val:.2f}")
            return center_x, center_y
        else:
            print(f"Không tìm thấy template (max confidence: {max_val:.2f})")
            return None
    
    def find_color(self, color: Tuple[int, int, int], tolerance: int = 30) -> Optional[Tuple[int, int]]:
        """
        Tìm vị trí của màu trên màn hình
        
        Args:
            color: Màu cần tìm (R, G, B)
            tolerance: Độ sai số màu
            
        Returns:
            Tọa độ (x, y) đầu tiên tìm thấy hoặc None
        """
        screen = self.capture_to_cv2()
        if screen is None:
            return None
        
        r, g, b = color
        lower = np.array([max(0, r - tolerance), max(0, g - tolerance), max(0, b - tolerance)])
        upper = np.array([min(255, r + tolerance), min(255, g + tolerance), min(255, b + tolerance)])
        
        mask = cv2.inRange(screen, lower, upper)
        locations = np.where(mask > 0)
        
        if len(locations[0]) > 0:
            # Lấy vị trí đầu tiên
            y = locations[0][0]
            x = locations[1][0]
            print(f"Tìm thấy màu tại ({x}, {y})")
            return x, y
        
        print("Không tìm thấy màu")
        return None
    
    def save_template(self, x: int, y: int, width: int, height: int, save_path: str) -> bool:
        """
        Cắt và lưu một vùng màn hình làm template
        
        Args:
            x, y: Tọa độ góc trên bên trái
            width, height: Kích thước vùng
            save_path: Đường dẫn lưu
            
        Returns:
            True nếu thành công
        """
        screen = self.capture_to_cv2()
        if screen is None:
            return False
        
        # Cắt vùng
        template = screen[y:y+height, x:x+width]
        
        # Lưu
        cv2.imwrite(save_path, cv2.cvtColor(template, cv2.COLOR_RGB2BGR))
        print(f"Đã lưu template: {save_path}")
        return True


if __name__ == "__main__":
    # Test
    adb = ADBController()
    if adb.connect():
        capture = ScreenCapture(adb)
        
        # Chụp màn hình
        img = capture.capture_to_cv2()
        if img is not None:
            print(f"Kích thước ảnh: {img.shape}")
            
            # Lưu ảnh
            cv2.imwrite("test_capture.png", cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
            print("Đã lưu test_capture.png")
