"""
Test script cho Screen Capture
"""
import cv2
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.adb_controller import ADBController
from core.screen_capture import ScreenCapture


def test_capture():
    print("=== Test Screen Capture ===\n")
    
    # Khởi tạo
    print("1. Khởi tạo controller...")
    try:
        adb = ADBController()
        capture = ScreenCapture(adb)
        print("✓ Đã khởi tạo\n")
    except FileNotFoundError as e:
        print(f"✗ Lỗi: {e}")
        return
    
    # Kết nối
    print("2. Kết nối...")
    if not adb.connect():
        print("✗ Không thể kết nối")
        return
    print("✓ Đã kết nối\n")
    
    # Chụp màn hình
    print("3. Chụp màn hình...")
    img = capture.capture_to_cv2()
    if img is not None:
        print(f"✓ Đã chụp, kích thước: {img.shape}\n")
        
        # Lưu ảnh
        filename = "test_screenshot.png"
        cv2.imwrite(filename, cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
        print(f"✓ Đã lưu: {filename}\n")
    else:
        print("✗ Chụp thất bại\n")
        return
    
    # Test tìm màu
    print("4. Test tìm màu...")
    color_pos = capture.find_color((255, 255, 255), tolerance=50)
    if color_pos:
        print(f"✓ Tìm thấy màu trắng tại: {color_pos}\n")
    else:
        print("✗ Không tìm thấy màu\n")
    
    # Test lưu template
    print("5. Test lưu template...")
    if img is not None:
        h, w = img.shape[:2]
        # Lưu vùng giữa màn hình làm template
        if capture.save_template(w//2 - 50, h//2 - 50, 100, 100, "test_template.png"):
            print("✓ Đã lưu template\n")
        else:
            print("✗ Lỗi lưu template\n")
    
    # Ngắt kết nối
    adb.disconnect()
    print("=== Test hoàn tất ===")


if __name__ == "__main__":
    test_capture()
