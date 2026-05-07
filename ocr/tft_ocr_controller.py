import time
import threading
from typing import Optional, Callable, Dict, List
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.adb_controller import ADBController
from core.screen_capture import ScreenCapture
from .ocr_reader import OCRReader, TFTUIReader
from .pixel_detector import PixelDetector, TFTPixelDetector


class TFTOCRController:
    """Controller TFT sử dụng OCR + Pixel Coordinate"""
    
    def __init__(self, adb_path: str = None, ldplayer_port: int = 5555, use_easyocr: bool = True):
        """
        Khởi tạo TFT OCR Controller
        
        Args:
            adb_path: Đường dẫn đến adb.exe
            ldplayer_port: Port của LDPlayer
            use_easyocr: True dùng EasyOCR, False dùng Tesseract
        """
        self.adb = ADBController(adb_path, ldplayer_port)
        self.capture = ScreenCapture(self.adb)
        self.ocr = OCRReader(self.capture, use_easyocr)
        self.ui_reader = TFTUIReader(self.ocr)
        self.pixel_detector = TFTPixelDetector(self.capture)
        
        self.running = False
        self.poll_interval = 0.1  # 100ms
        self.callbacks = {}
    
    def connect(self) -> bool:
        """Kết nối đến LDPlayer"""
        return self.adb.connect()
    
    def disconnect(self):
        """Ngắt kết nối"""
        self.adb.disconnect()
    
    def register_callback(self, event: str, callback: Callable):
        """
        Đăng ký callback cho event
        
        Args:
            event: Tên event
            callback: Hàm callback
        """
        self.callbacks[event] = callback
    
    # --- Game State Monitoring ---
    
    def get_game_state(self) -> Dict:
        """
        Lấy trạng thái game hiện tại
        
        Returns:
            Dict chứa thông tin game state
        """
        state = {
            'gold': self.ui_reader.read_gold(),
            'health': self.ui_reader.read_health(),
            'level': self.ui_reader.read_level(),
            'shop_open': self.pixel_detector.is_shop_open(),
            'shop_champions': self.ui_reader.read_shop_champions(),
            'level_up_available': self.pixel_detector.detect_level_up_available(),
            'timestamp': time.time()
        }
        return state
    
    def monitor_game_state(self, interval: float = 1.0):
        """
        Monitor game state liên tục
        
        Args:
            interval: Thời gian giữa các lần check (giây)
        """
        self.running = True
        print(f"Bắt đầu monitor game state mỗi {interval}s...")
        
        while self.running:
            try:
                state = self.get_game_state()
                
                # Trigger callbacks
                if 'game_state' in self.callbacks:
                    self.callbacks['game_state'](state)
                
                # Specific events
                if state['shop_open'] and 'shop_open' in self.callbacks:
                    self.callbacks['shop_open'](state)
                
                if state['level_up_available'] and 'level_up' in self.callbacks:
                    self.callbacks['level_up'](state)
                
                time.sleep(interval)
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Lỗi monitor: {e}")
                time.sleep(1)
        
        self.running = False
    
    def start_monitoring(self, interval: float = 1.0):
        """Bắt đầu monitoring trong thread riêng"""
        monitor_thread = threading.Thread(target=self.monitor_game_state, args=(interval,))
        monitor_thread.daemon = True
        monitor_thread.start()
    
    def stop_monitoring(self):
        """Dừng monitoring"""
        self.running = False
    
    # --- Actions ---
    
    def buy_champion(self, champion_name: str) -> bool:
        """
        Mua tướng từ shop
        
        Args:
            champion_name: Tên tướng cần mua
            
        Returns:
            True nếu thành công
        """
        print(f"Đang tìm tướng: {champion_name}")
        
        # Tìm tướng trong shop
        pos = self.ui_reader.find_champion_in_shop(champion_name)
        if pos:
            x, y = pos
            print(f"Tìm thấy tại ({x}, {y}), đang mua...")
            self.adb.tap(x, y)
            time.sleep(0.5)
            return True
        else:
            print(f"Không tìm thấy {champion_name} trong shop")
            return False
    
    def buy_champion_at_slot(self, slot_index: int) -> bool:
        """
        Mua tướng tại slot cụ thể trong shop (0-4)
        
        Args:
            slot_index: Index slot (0-4)
            
        Returns:
            True nếu thành công
        """
        shop_slots = self.pixel_detector.find_champion_slots()
        if 0 <= slot_index < len(shop_slots):
            x, y = shop_slots[slot_index]
            self.adb.tap(x, y)
            return True
        return False
    
    def sell_champion(self, slot_index: int) -> bool:
        """
        Bán tướng trên bench
        
        Args:
            slot_index: Index slot trên bench (0-8)
            
        Returns:
            True nếu thành công
        """
        bench_slots = self.pixel_detector.find_champion_slots()
        if 0 <= slot_index < len(bench_slots):
            x, y = bench_slots[slot_index]
            # Drag và thả vào icon bán
            self.adb.swipe(x, y, x, y + 200, 500)
            return True
        return False
    
    def level_up(self) -> bool:
        """Lên cấp nếu có thể"""
        if self.pixel_detector.detect_level_up_available():
            # Tap nút level up (cần tùy chỉnh tọa độ)
            self.adb.tap(925, 725)
            return True
        return False
    
    def refresh_shop(self) -> bool:
        """Làm mới shop"""
        # Tap nút refresh (cần tùy chỉnh tọa độ)
        self.adb.tap(850, 725)
        return True
    
    def place_champion(self, from_slot: int, to_position: tuple) -> bool:
        """
        Đặt tướng từ bench xuống bàn
        
        Args:
            from_slot: Slot trên bench
            to_position: Vị trí trên bàn (x, y)
            
        Returns:
            True nếu thành công
        """
        bench_slots = self.pixel_detector.find_champion_slots()
        if 0 <= from_slot < len(bench_slots):
            from_x, from_y = bench_slots[from_slot]
            to_x, to_y = to_position
            self.adb.swipe(from_x, from_y, to_x, to_y, 500)
            return True
        return False
    
    # --- Auto-play Logic ---
    
    def auto_buy_champions(self, target_champions: List[str], max_gold: int = 50):
        """
        Tự động mua tướng từ danh sách target
        
        Args:
            target_champions: List tên tướng cần mua
            max_gold: Gold tối đa để mua
        """
        while self.running:
            state = self.get_game_state()
            
            if state['gold'] < max_gold and state['shop_open']:
                for champion in target_champions:
                    if self.buy_champion(champion):
                        time.sleep(0.5)
                        break
            
            time.sleep(self.poll_interval)
    
    def auto_level_up(self, target_level: int = 8):
        """
        Tự động lên cấp đến target level
        
        Args:
            target_level: Level mục tiêu
        """
        while self.running:
            state = self.get_game_state()
            
            if state['level'] < target_level and state['level_up_available']:
                if self.level_up():
                    print(f"Đã lên cấp lên {state['level'] + 1}")
                    time.sleep(1)
            
            time.sleep(self.poll_interval)
    
    def auto_refresh(self, min_gold: int = 4):
        """
        Tự động làm mới shop khi có đủ gold
        
        Args:
            min_gold: Gold tối thiểu để refresh
        """
        while self.running:
            state = self.get_game_state()
            
            if state['gold'] >= min_gold and state['shop_open']:
                self.refresh_shop()
                print("Đã refresh shop")
                time.sleep(0.5)
            
            time.sleep(self.poll_interval)


if __name__ == "__main__":
    # Test
    controller = TFTOCRController(use_easyocr=True)
    
    if controller.connect():
        print("Đã kết nối!")
        
        # Test đọc game state
        state = controller.get_game_state()
        print(f"Game state: {state}")
        
        # Test monitor
        def on_state_update(state):
            print(f"Gold: {state['gold']}, Health: {state['health']}, Level: {state['level']}")
        
        controller.register_callback('game_state', on_state_update)
        
        try:
            controller.start_monitoring(interval=2.0)
            time.sleep(10)  # Monitor trong 10 giây
            controller.stop_monitoring()
        except KeyboardInterrupt:
            controller.stop_monitoring()
        
        controller.disconnect()
