"""
Test script cho TFT OCR Controller
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ocr.tft_ocr_controller import TFTOCRController


def test_ocr_controller():
    print("=== Test TFT OCR Controller ===\n")
    
    # Khởi tạo
    print("1. Khởi tạo controller...")
    try:
        controller = TFTOCRController(use_easyocr=True)
        print("✓ Đã khởi tạo\n")
    except Exception as e:
        print(f"✗ Lỗi: {e}")
        return
    
    # Kết nối
    print("2. Kết nối...")
    if not controller.connect():
        print("✗ Không thể kết nối")
        return
    print("✓ Đã kết nối\n")
    
    # Lấy game state
    print("3. Lấy game state...")
    state = controller.get_game_state()
    print(f"  Gold: {state['gold']}")
    print(f"  Health: {state['health']}")
    print(f"  Level: {state['level']}")
    print(f"  Shop open: {state['shop_open']}")
    print(f"  Shop champions: {state['shop_champions']}")
    print(f"  Level up available: {state['level_up_available']}\n")
    
    # Test callback
    print("4. Test callback...")
    call_count = [0]
    
    def on_state_update(s):
        call_count[0] += 1
        print(f"  Callback #{call_count[0]}: Gold={s['gold']}, Health={s['health']}")
    
    controller.register_callback('game_state', on_state_update)
    
    # Monitor trong 10 giây
    print("5. Monitor game state trong 10 giây...")
    controller.start_monitoring(interval=2.0)
    
    import time
    try:
        time.sleep(10)
    except KeyboardInterrupt:
        pass
    
    controller.stop_monitoring()
    print(f"✓ Đã trigger callback {call_count[0]} lần\n")
    
    # Test actions
    print("6. Test actions (nhấn Enter để skip từng action)...")
    
    input("Press Enter để test refresh shop...")
    if controller.refresh_shop():
        print("✓ Refresh shop thành công")
    
    input("Press Enter để test level up...")
    if controller.level_up():
        print("✓ Level up thành công")
    
    input("Press Enter để test buy champion at slot 0...")
    if controller.buy_champion_at_slot(0):
        print("✓ Buy champion tại slot 0 thành công")
    
    print()
    
    # Ngắt kết nối
    controller.disconnect()
    print("=== Test hoàn tất ===")


if __name__ == "__main__":
    test_ocr_controller()
