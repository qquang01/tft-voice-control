"""
Test script cho Pixel Detector
"""
import cv2
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.adb_controller import ADBController
from core.screen_capture import ScreenCapture
from ocr.pixel_detector import PixelDetector, TFTPixelDetector


def test_pixel_detector():
    print("=== Test Pixel Detector ===\n")
    
    # Khởi tạo
    print("1. Khởi tạo controller...")
    try:
        adb = ADBController()
        capture = ScreenCapture(adb)
        detector = PixelDetector(capture)
        tft_detector = TFTPixelDetector(capture)
        print("✓ Đã khởi tạo\n")
    except Exception as e:
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
    if img is None:
        print("✗ Chụp thất bại")
        return
    h, w = img.shape[:2]
    print(f"✓ Kích thước: {w}x{h}\n")
    
    # Tìm màu
    print("4. Tìm màu vàng (Gold)...")
    gold_pos = detector.find_color((255, 215, 0), tolerance=50)
    if gold_pos:
        print(f"✓ Tìm thấy tại: {gold_pos}\n")
    else:
        print("✗ Không tìm thấy\n")
    
    # Đếm pixel trong vùng
    print("5. Đếm pixel vàng trong vùng shop...")
    shop_region = (400, 600, 400, 150)
    count = detector.count_pixels_in_region(shop_region, (255, 215, 0), tolerance=50)
    print(f"Tìm thấy {count} pixel vàng\n")
    
    # Detect button
    print("6. Detect button trong vùng shop...")
    is_button = detector.detect_button(shop_region)
    print(f"✓ Button detected: {is_button}\n")
    
    # Tạo template từ màn hình
    print("7. Tạo template từ màn hình...")
    # Cắt vùng giữa màn hình làm template mẫu
    template_region = (w//2 - 50, h//2 - 50, 100, 100)
    x, y, tw, th = template_region
    template = img[y:y+th, x:x+tw]
    cv2.imwrite("test_template.png", cv2.cvtColor(template, cv2.COLOR_RGB2BGR))
    print(f"✓ Đã lưu template: test_template.png\n")
    
    # Load và tìm template
    print("8. Load và tìm template...")
    detector.load_template("test", "test_template.png")
    pos = detector.find_template("test", threshold=0.8)
    if pos:
        print(f"✓ Tìm thấy template tại: {pos}\n")
    else:
        print("✗ Không tìm thấy template\n")
    
    # Test TFT detector
    print("9. Test TFT specific detection...")
    print(f"  Shop open: {tft_detector.is_shop_open()}")
    print(f"  Level up available: {tft_detector.detect_level_up_available()}")
    
    champion_slots = tft_detector.find_champion_slots()
    print(f"  Champion slots: {len(champion_slots)}")
    print(f"  Vị trí đầu tiên: {champion_slots[0] if champion_slots else 'None'}\n")
    
    # Ngắt kết nối
    adb.disconnect()
    print("=== Test hoàn tất ===")


if __name__ == "__main__":
    test_pixel_detector()
