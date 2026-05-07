"""
Test script cho ADB Controller
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.adb_controller import ADBController


def test_adb():
    print("=== Test ADB Controller ===\n")
    
    # Khởi tạo controller
    print("1. Khởi tạo ADB Controller...")
    try:
        adb = ADBController()
        print("✓ Đã khởi tạo thành công\n")
    except FileNotFoundError as e:
        print(f"✗ Lỗi: {e}")
        print("Vui lòng chỉ định đường dẫn adb.exe")
        return
    
    # Kết nối
    print("2. Kết nối đến LDPlayer...")
    if adb.connect():
        print("✓ Đã kết nối thành công\n")
    else:
        print("✗ Không thể kết nối")
        return
    
    # Kiểm tra thiết bị
    print("3. Kiểm tra thiết bị...")
    if adb.is_device_connected():
        print("✓ Thiết bị đang kết nối\n")
    else:
        print("✗ Thiết bị không kết nối\n")
    
    # Lấy kích thước màn hình
    print("4. Lấy kích thước màn hình...")
    size = adb.get_screen_size()
    if size:
        print(f"✓ Kích thước: {size[0]}x{size[1]}\n")
    
    # Test tap
    print("5. Test tap (tap vào giữa màn hình)...")
    if size:
        x, y = size[0] // 2, size[1] // 2
        if adb.tap(x, y):
            print(f"✓ Tap thành công tại ({x}, {y})\n")
        else:
            print("✗ Tap thất bại\n")
    
    # Test swipe
    print("6. Test swipe...")
    if size:
        if adb.swipe(size[0]//2, size[1]//2, size[0]//2 + 100, size[1]//2):
            print("✓ Swipe thành công\n")
        else:
            print("✗ Swipe thất bại\n")
    
    # Test phím Back
    print("7. Test phím Back...")
    if adb.press_back():
        print("✓ Nhấn Back thành công\n")
    else:
        print("✗ Nhấn Back thất bại\n")
    
    # Ngắt kết nối
    print("8. Ngắt kết nối...")
    adb.disconnect()
    print("✓ Đã ngắt kết nối\n")
    
    print("=== Test hoàn tất ===")


if __name__ == "__main__":
    test_adb()
