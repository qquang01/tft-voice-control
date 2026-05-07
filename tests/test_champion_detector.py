"""
Test script cho Champion Detector
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.adb_controller import ADBController
from core.screen_capture import ScreenCapture
from ocr.champion_detector import ChampionDetector


def test_champion_detector():
    print("=== Test Champion Detector ===\n")
    
    # Khởi tạo
    print("1. Khởi tạo controller...")
    try:
        adb = ADBController()
        capture = ScreenCapture(adb)
        detector = ChampionDetector(capture)
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
    print(f"✓ Kích thước: {img.shape}\n")
    
    # Load templates
    print("4. Load templates...")
    print(f"  Số lượng templates: {len(detector.templates)}\n")
    
    # Test detect shop
    print("5. Detect champions trong shop...")
    shop_champs = detector.detect_in_shop()
    print(f"  Tìm thấy {len([c for c in shop_champs if c])} tướng:")
    for i, champ in enumerate(shop_champs):
        if champ:
            print(f"    Slot {i+1}: {champ['name']} (conf: {champ['confidence']:.2f})")
    print()
    
    # Test detect bench
    print("6. Detect champions trên bench...")
    bench_champs = detector.detect_on_bench()
    print(f"  Tìm thấy {len([c for c in bench_champs if c])} tướng trên bench\n")
    
    # Test capture template
    print("7. Capture template từ shop slot 0...")
    print("  (Đang capture template 'test_champion'...)")
    detector.capture_shop_slot_template(0, "test_champion")
    print()
    
    # Visualize
    print("8. Visualize detection...")
    detector.visualize_detection(shop_champs, "shop_detection.png")
    print()
    
    # Ngắt kết nối
    adb.disconnect()
    print("=== Test hoàn tất ===")


if __name__ == "__main__":
    test_champion_detector()
