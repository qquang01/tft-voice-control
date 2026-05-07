import sys
import os
import time
import threading
from typing import Dict, Callable
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.adb_controller import ADBController, KEYCODE_BACK, KEYCODE_HOME
from core.screen_capture import ScreenCapture


class TFTVoiceController:
    """Voice Controller cho TFT Mobile"""
    
    def __init__(self, adb_path: str = None, ldplayer_port: int = 5555):
        """
        Khởi tạo TFT Voice Controller
        
        Args:
            adb_path: Đường dẫn đến adb.exe
            ldplayer_port: Port của LDPlayer
        """
        self.adb = ADBController(adb_path, ldplayer_port)
        self.capture = ScreenCapture(self.adb)
        self.voice_commands: Dict[str, Callable] = {}
        self.listening = False
        
        # Đăng ký các lệnh mặc định
        self._register_default_commands()
    
    def _register_default_commands(self):
        """Đăng ký các lệnh voice mặc định"""
        commands = {
            "trở về": self.cmd_back,
            "quay lại": self.cmd_back,
            "về nhà": self.cmd_home,
            "home": self.cmd_home,
            "mở game": self.cmd_open_game,
            "đóng game": self.cmd_close_game,
            "chụp màn hình": self.cmd_screenshot,
            "kiểm tra": self.cmd_check_status,
            "tìm tướng": self.cmd_find_champion,
            "mua tướng": self.cmd_buy_champion,
            "lên đồ": self.cmd_buy_item,
            "bán tướng": self.cmd_sell_champion,
            "lên cấp": self.cmd_level_up,
            "làm mới": self.cmd_refresh,
            "kéo tướng": self.cmd_drag_champion,
            "đặt tướng": self.cmd_place_champion,
        }
        
        for cmd, func in commands.items():
            self.register_command(cmd, func)
    
    def register_command(self, command: str, callback: Callable):
        """
        Đăng ký lệnh voice mới
        
        Args:
            command: Lệnh voice (tiếng Việt hoặc tiếng Anh)
            callback: Hàm callback khi nhận lệnh
        """
        self.voice_commands[command.lower()] = callback
        print(f"Đã đăng ký lệnh: {command}")
    
    def connect(self) -> bool:
        """Kết nối đến LDPlayer"""
        return self.adb.connect()
    
    def disconnect(self):
        """Ngắt kết nối"""
        self.adb.disconnect()
    
    # --- Commands ---
    
    def cmd_back(self):
        """Lệnh: Quay lại"""
        print("Thực hiện: Quay lại")
        self.adb.press_back()
    
    def cmd_home(self):
        """Lệnh: Về màn hình chính"""
        print("Thực hiện: Về màn hình chính")
        self.adb.press_home()
    
    def cmd_open_game(self):
        """Lệnh: Mở game TFT"""
        print("Thực hiện: Mở game TFT")
        # Package name của TFT Mobile (cần kiểm tra lại)
        self.adb.start_app("com.riotgames.league.wildrift")
    
    def cmd_close_game(self):
        """Lệnh: Đóng game"""
        print("Thực hiện: Đóng game")
        self.adb.close_app("com.riotgames.league.wildrift")
    
    def cmd_screenshot(self):
        """Lệnh: Chụp màn hình"""
        print("Thực hiện: Chụp màn hình")
        img = self.capture.capture_to_cv2()
        if img is not None:
            import cv2
            cv2.imwrite(f"screenshot_{int(time.time())}.png", 
                       cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
            print("Đã lưu screenshot")
    
    def cmd_check_status(self):
        """Lệnh: Kiểm tra trạng thái"""
        print("Thực hiện: Kiểm tra trạng thái")
        screen_size = self.adb.get_screen_size()
        if screen_size:
            print(f"Kích thước màn hình: {screen_size}")
        print(f"Kết nối: {'Có' if self.adb.is_device_connected() else 'Không'}")
    
    def cmd_find_champion(self):
        """Lệnh: Tìm tướng (cần tùy chỉnh tọa độ)"""
        print("Thực hiện: Tìm tướng")
        # Tọa độ nút tìm tướng - cần tùy chỉnh theo màn hình
        self.adb.tap(500, 300)  # Ví dụ, cần thay đổi
    
    def cmd_buy_champion(self):
        """Lệnh: Mua tướng"""
        print("Thực hiện: Mua tướng")
        self.adb.tap(500, 400)  # Cần tùy chỉnh
    
    def cmd_buy_item(self):
        """Lệnh: Lên đồ"""
        print("Thực hiện: Lên đồ")
        self.adb.tap(800, 600)  # Cần tùy chỉnh
    
    def cmd_sell_champion(self):
        """Lệnh: Bán tướng"""
        print("Thực hiện: Bán tướng")
        self.adb.tap(200, 400)  # Cần tùy chỉnh
    
    def cmd_level_up(self):
        """Lệnh: Lên cấp"""
        print("Thực hiện: Lên cấp")
        self.adb.tap(900, 700)  # Cần tùy chỉnh
    
    def cmd_refresh(self):
        """Lệnh: Làm mới shop"""
        print("Thực hiện: Làm mới shop")
        self.adb.tap(700, 500)  # Cần tùy chỉnh
    
    def cmd_drag_champion(self):
        """Lệnh: Kéo tướng"""
        print("Thực hiện: Kéo tướng")
        # Ví dụ swipe
        self.adb.swipe(300, 500, 600, 500, 500)
    
    def cmd_place_champion(self):
        """Lệnh: Đặt tướng xuống bàn"""
        print("Thực hiện: Đặt tướng")
        self.adb.tap(400, 300)  # Cần tùy chỉnh
    
    # --- Voice Recognition Integration ---
    
    def process_voice_command(self, command: str):
        """
        Xử lý lệnh voice
        
        Args:
            command: Lệnh voice đã được nhận dạng
        """
        command = command.lower().strip()
        print(f"Nhận lệnh: {command}")
        
        # Tìm lệnh phù hợp
        for cmd_name, callback in self.voice_commands.items():
            if cmd_name in command:
                try:
                    callback()
                except Exception as e:
                    print(f"Lỗi thực hiện lệnh: {e}")
                return
        
        print(f"Không hiểu lệnh: {command}")
    
    def start_voice_loop(self, voice_recognition_callback):
        """
        Bắt đầu loop nhận voice
        
        Args:
            voice_recognition_callback: Hàm callback trả về text từ voice
        """
        self.listening = True
        print("Bắt đầu lắng nghe voice commands...")
        
        while self.listening:
            try:
                # Lấy text từ voice recognition
                text = voice_recognition_callback()
                if text:
                    self.process_voice_command(text)
                time.sleep(0.1)
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Lỗi voice loop: {e}")
                time.sleep(1)
        
        self.listening = False
        print("Đã dừng lắng nghe")


if __name__ == "__main__":
    # Test
    controller = TFTVoiceController()
    
    if controller.connect():
        print("Đã kết nối thành công!")
        print("Các lệnh có sẵn:", list(controller.voice_commands.keys()))
        
        # Test manual command
        while True:
            cmd = input("Nhập lệnh (hoặc 'exit' để thoát): ")
            if cmd.lower() == 'exit':
                break
            controller.process_voice_command(cmd)
        
        controller.disconnect()
