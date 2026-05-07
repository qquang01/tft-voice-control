"""
Test script cho Shop Reader

Script này test việc đọc và so sánh 5 vùng ảnh trong shop TFT.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.adb_controller import ADBController
from core.screen_capture import ScreenCapture
from labeling.shop_reader import ShopReader, ShopVisualizer


def test_shop_reader():
    """Test Shop Reader cơ bản"""
    
    print("=" * 60)
    print("Shop Reader Test")
    print("=" * 60)
    
    # Kết nối ADB
    print("\n1. Kết nối ADB...")
    adb = ADBController()
    if not adb.connect():
        print("✗ Không thể kết nối ADB")
        return False
    
    print("✓ Đã kết nối ADB")
    
    # Khởi tạo Screen Capture
    print("\n2. Khởi tạo Screen Capture...")
    capture = ScreenCapture(adb)
    print("✓ Screen Capture đã khởi tạo")
    
    # Khởi tạo Shop Reader
    print("\n3. Khởi tạo Shop Reader...")
    shop_reader = ShopReader(capture)
    print(f"✓ Shop Reader đã khởi tạo")
    print(f"  Shop regions: {len(shop_reader.shop_regions)} slots")
    for region in shop_reader.shop_regions:
        print(f"    Slot {region['index']}: ({region['x']}, {region['y']}, {region['width']}x{region['height']})")
    
    # Load templates
    print("\n4. Load templates...")
    shop_reader.load_templates()
    print(f"✓ Đã load {len(shop_reader.pixel_detector.templates)} templates")
    
    if len(shop_reader.pixel_detector.templates) == 0:
        print("⚠ Không có templates nào được load")
        print("  Bạn cần tạo templates trước:")
        print("  1. Chụp màn hình khi shop mở")
        print("  2. Sử dụng save_slot_templates() để lưu từng slot")
        print("  3. Templates sẽ được lưu trong templates/shop_champions/")
    
    # Test capture frame
    print("\n5. Test capture frame...")
    frame = shop_reader.capture_shop_frame()
    if frame is None:
        print("✗ Không thể capture frame")
        return False
    
    print(f"✓ Đã capture frame: {frame.shape}")
    
    # Extract slot images
    print("\n6. Extract slot images...")
    slot_images = shop_reader.extract_slot_images(frame)
    print(f"✓ Đã extract {len(slot_images)} slot images")
    for i, slot_img in enumerate(slot_images):
        print(f"  Slot {i}: {slot_img.shape}")
    
    # Lưu slot images để kiểm tra
    print("\n7. Lưu slot images để kiểm tra...")
    os.makedirs("screenshots/shop_slots", exist_ok=True)
    for i, slot_img in enumerate(slot_images):
        import cv2
        slot_img_bgr = cv2.cvtColor(slot_img, cv2.COLOR_RGB2BGR)
        cv2.imwrite(f"screenshots/shop_slots/slot_{i}.png", slot_img_bgr)
        print(f"  ✓ Saved slot_{i}.png")
    
    # Đọc shop (nếu có templates)
    if len(shop_reader.pixel_detector.templates) > 0:
        print("\n8. Đọc shop với templates...")
        result = shop_reader.read_shop(force_refresh=True)
        
        # Print summary
        print("\n" + shop_reader.get_shop_summary(result))
        
        # Visualize
        print("\n9. Visualize shop...")
        vis_frame = ShopVisualizer.visualize_shop(
            frame,
            shop_reader.shop_regions,
            result['slots']
        )
        ShopVisualizer.save_visualization(vis_frame, "screenshots/shop_visualization.png")
    else:
        print("\n8. Bỏ qua đọc shop (không có templates)")
    
    print("\n" + "=" * 60)
    print("Test hoàn tất!")
    print("=" * 60)
    
    return True


def test_create_templates():
    """
    Script để tạo templates từ shop hiện tại
    
    Usage:
        1. Mở shop trong game
        2. Chạy script này
        3. Nhập tên champion cho mỗi slot
    """
    
    print("=" * 60)
    print("Create Shop Templates")
    print("=" * 60)
    
    # Kết nối ADB
    print("\n1. Kết nối ADB...")
    adb = ADBController()
    if not adb.connect():
        print("✗ Không thể kết nối ADB")
        return
    
    # Khởi tạo
    capture = ScreenCapture(adb)
    shop_reader = ShopReader(capture)
    
    # Capture frame
    print("\n2. Capture frame...")
    frame = shop_reader.capture_shop_frame()
    if frame is None:
        print("✗ Không thể capture frame")
        return
    
    print("✓ Đã capture frame")
    
    # Extract và show slot images
    print("\n3. Extract slot images...")
    slot_images = shop_reader.extract_slot_images(frame)
    
    # Lưu slot images
    os.makedirs("screenshots/shop_slots", exist_ok=True)
    for i, slot_img in enumerate(slot_images):
        import cv2
        slot_img_bgr = cv2.cvtColor(slot_img, cv2.COLOR_RGB2BGR)
        cv2.imwrite(f"screenshots/shop_slots/slot_{i}.png", slot_img_bgr)
        print(f"  ✓ Saved slot_{i}.png")
    
    print("\n4. Nhập tên champion cho mỗi slot:")
    print("   (Nhập 'skip' để bỏ qua slot, 'done' để kết thúc)")
    
    for i in range(5):
        print(f"\nSlot {i}:")
        print(f"  Xem ảnh tại: screenshots/shop_slots/slot_{i}.png")
        
        champion_name = input(f"  Nhập tên champion: ").strip()
        
        if champion_name.lower() == 'done':
            break
        if champion_name.lower() == 'skip':
            continue
        
        # Save template
        shop_reader.save_slot_templates(i, champion_name)
    
    print("\n" + "=" * 60)
    print("Đã tạo xong templates!")
    print("=" * 60)


def test_continuous_reading():
    """
    Test đọc shop liên tục để debug
    """
    
    print("=" * 60)
    print("Continuous Shop Reading Test")
    print("=" * 60)
    print("Nhấn Ctrl+C để dừng\n")
    
    # Kết nối ADB
    adb = ADBController()
    if not adb.connect():
        print("✗ Không thể kết nối ADB")
        return
    
    # Khởi tạo
    capture = ScreenCapture(adb)
    shop_reader = ShopReader(capture)
    shop_reader.load_templates()
    
    try:
        iteration = 0
        while True:
            iteration += 1
            print(f"\n--- Iteration {iteration} ---")
            
            # Đọc shop
            result = shop_reader.read_shop(force_refresh=True)
            
            # Print summary
            print(shop_reader.get_shop_summary(result))
            
            # Wait
            import time
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\n\nĐã dừng bởi user")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        mode = sys.argv[1]
        
        if mode == "create":
            test_create_templates()
        elif mode == "continuous":
            test_continuous_reading()
        else:
            print(f"Unknown mode: {mode}")
            print("Usage:")
            print("  python test_shop_reader.py          # Test cơ bản")
            print("  python test_shop_reader.py create   # Tạo templates")
            print("  python test_shop_reader.py continuous # Đọc liên tục")
    else:
        test_shop_reader()
