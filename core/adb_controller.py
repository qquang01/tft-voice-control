import subprocess
import time
import os
from typing import Tuple, Optional

class ADBController:
    """ADB Controller cho LDPlayer"""
    
    def __init__(self, adb_path: str = None, ldplayer_port: int = 5555):
        """
        Khởi tạo ADB Controller
        
        Args:
            adb_path: Đường dẫn đến adb.exe (mặc định: LDPlayer/adb.exe)
            ldplayer_port: Port của LDPlayer (mặc định: 5555 cho instance đầu tiên)
        """
        if adb_path is None:
            # Tự động tìm adb trong LDPlayer
            possible_paths = [
                r"F:\LDPlayer\LDPlayer9\adb.exe",
                r"C:\LDPlayer\LDPlayer9\adb.exe",
                r"C:\LDPlayer\LDPlayer4\adb.exe",
                r"D:\LDPlayer\LDPlayer9\adb.exe",
                r"D:\LDPlayer\LDPlayer4\adb.exe",
                r"E:\LDPlayer\LDPlayer9\adb.exe",
                r"E:\LDPlayer\LDPlayer4\adb.exe",
            ]
            adb_path = self._find_adb(possible_paths)
        
        self.adb_path = adb_path
        self.port = ldplayer_port
        self.device_id = f"127.0.0.1:{ldplayer_port}"
        self.connected = False
        
    def _find_adb(self, paths: list) -> str:
        """Tìm đường dẫn adb.exe"""
        for path in paths:
            if os.path.exists(path):
                return path
        raise FileNotFoundError("Không tìm thấy adb.exe trong LDPlayer. Vui lòng chỉ định đường dẫn.")
    
    def _run_adb_command(self, command: str, timeout: int = 10) -> Tuple[bool, str]:
        """
        Thực thi lệnh ADB
        
        Args:
            command: Lệnh ADB (không bao gồm 'adb')
            timeout: Thời gian timeout
            
        Returns:
            Tuple (success, output)
        """
        try:
            full_command = f'"{self.adb_path}" {command}'
            result = subprocess.run(
                full_command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding='utf-8',
                errors='ignore'
            )
            success = result.returncode == 0
            return success, result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            return False, "Command timeout"
        except Exception as e:
            return False, str(e)
    
    def connect(self) -> bool:
        """Kết nối đến LDPlayer"""
        success, output = self._run_adb_command(f"connect {self.device_id}")
        if success and "connected" in output.lower():
            self.connected = True
            print(f"Đã kết nối đến LDPlayer: {self.device_id}")
            return True
        else:
            print(f"Lỗi kết nối: {output}")
            return False
    
    def disconnect(self) -> bool:
        """Ngắt kết nối"""
        success, output = self._run_adb_command(f"disconnect {self.device_id}")
        self.connected = False
        return success
    
    def tap(self, x: int, y: int) -> bool:
        """
        Tap vào vị trí trên màn hình
        
        Args:
            x: Tọa độ X
            y: Tọa độ Y
        """
        success, output = self._run_adb_command(f"-s {self.device_id} shell input tap {x} {y}")
        if success:
            print(f"Tap tại ({x}, {y})")
        else:
            print(f"Lỗi tap: {output}")
        return success
    
    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration: int = 300) -> bool:
        """
        Swipe từ vị trí này sang vị trí khác
        
        Args:
            x1, y1: Tọa độ bắt đầu
            x2, y2: Tọa độ kết thúc
            duration: Thời gian swipe (ms)
        """
        success, output = self._run_adb_command(
            f"-s {self.device_id} shell input swipe {x1} {y1} {x2} {y2} {duration}"
        )
        if success:
            print(f"Swipe từ ({x1}, {y1}) đến ({x2}, {y2})")
        else:
            print(f"Lỗi swipe: {output}")
        return success
    
    def press_key(self, keycode: int) -> bool:
        """
        Nhấn phím
        
        Args:
            keycode: Android keycode (ví dụ: 3 = HOME, 4 = BACK)
        """
        success, output = self._run_adb_command(f"-s {self.device_id} shell input keyevent {keycode}")
        if success:
            print(f"Nhấn phím keycode: {keycode}")
        else:
            print(f"Lỗi nhấn phím: {output}")
        return success
    
    def press_back(self) -> bool:
        """Nhấn nút Back"""
        return self.press_key(4)
    
    def press_home(self) -> bool:
        """Nhấn nút Home"""
        return self.press_key(3)
    
    def get_screen_size(self) -> Optional[Tuple[int, int]]:
        """Lấy kích thước màn hình"""
        success, output = self._run_adb_command(f"-s {self.device_id} shell wm size")
        if success and "Physical size:" in output:
            size_str = output.split("Physical size: ")[1].strip()
            width, height = map(int, size_str.split("x"))
            print(f"Kích thước màn hình: {width}x{height}")
            return width, height
        return None
    
    def start_app(self, package_name: str, activity: str = None) -> bool:
        """
        Mở ứng dụng
        
        Args:
            package_name: Tên package (ví dụ: com.riotgames.league.wildrift)
            activity: Tên activity (tùy chọn)
        """
        if activity:
            cmd = f"-s {self.device_id} shell am start -n {package_name}/{activity}"
        else:
            cmd = f"-s {self.device_id} shell monkey -p {package_name} -c android.intent.category.LAUNCHER 1"
        
        success, output = self._run_adb_command(cmd)
        if success:
            print(f"Đã mở ứng dụng: {package_name}")
        else:
            print(f"Lỗi mở ứng dụng: {output}")
        return success
    
    def close_app(self, package_name: str) -> bool:
        """Đóng ứng dụng"""
        success, output = self._run_adb_command(f"-s {self.device_id} shell am force-stop {package_name}")
        if success:
            print(f"Đã đóng ứng dụng: {package_name}")
        else:
            print(f"Lỗi đóng ứng dụng: {output}")
        return success
    
    def is_device_connected(self) -> bool:
        """Kiểm tra thiết bị có kết nối không"""
        success, output = self._run_adb_command("devices")
        return self.device_id in output


# Keycodes thường dùng
KEYCODE_HOME = 3
KEYCODE_BACK = 4
KEYCODE_MENU = 82
KEYCODE_VOLUME_UP = 24
KEYCODE_VOLUME_DOWN = 25
KEYCODE_ENTER = 66
KEYCODE_DEL = 67
