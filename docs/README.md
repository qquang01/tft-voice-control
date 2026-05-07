# TFT Mobile Voice Control Tool

Công cụ hỗ trợ chơi TFT Mobile trên LDPlayer bằng voice control, dành cho người khuyết tật.

## Yêu cầu

- LDPlayer (đã cài đặt)
- Python 3.8+
- ADB (được tích hợp trong LDPlayer)

## Cài đặt

1. Cài đặt dependencies:
```bash
pip install -r requirements.txt
```

2. Kiểm tra đường dẫn ADB:
   - LDPlayer 9: `C:\LDPlayer\LDPlayer9\adb.exe`
   - LDPlayer 4: `C:\LDPlayer\LDPlayer4\adb.exe`
   - Hoặc chỉnh đường dẫn trong code

## Sử dụng

### Cấu trúc file

- `adb_controller.py`: Điều khiển ADB kết nối với LDPlayer
- `screen_capture.py`: Chụp và xử lý màn hình
- `tft_voice_controller.py`: Điều khiển game bằng voice
- `requirements.txt`: Dependencies Python

### Kết nối ADB

```python
from adb_controller import ADBController

# Kết nối với LDPlayer (port mặc định 5555)
adb = ADBController()
if adb.connect():
    print("Đã kết nối!")
```

### Chụp màn hình

```python
from screen_capture import ScreenCapture
from adb_controller import ADBController

adb = ADBController()
adb.connect()
capture = ScreenCapture(adb)

# Chụp và lưu ảnh
img = capture.capture_to_cv2()
if img is not None:
    import cv2
    cv2.imwrite("screenshot.png", cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
```

### Voice Control cơ bản

```python
from tft_voice_controller import TFTVoiceController

controller = TFTVoiceController()
if controller.connect():
    # Xử lý lệnh voice
    controller.process_voice_command("trở về")
    controller.process_voice_command("chụp màn hình")
```

## Các lệnh voice mặc định

- "trở về" / "quay lại": Nhấn nút Back
- "về nhà" / "home": Nhấn nút Home
- "mở game": Mở game TFT
- "đóng game": Đóng game
- "chụp màn hình": Chụp và lưu màn hình
- "kiểm tra": Kiểm tra trạng thái kết nối
- "tìm tướng": Tìm tướng trong shop
- "mua tướng": Mua tướng
- "lên đồ": Mua đồ
- "bán tướng": Bán tướng
- "lên cấp": Lên cấp độ
- "làm mới": Làm mới shop
- "kéo tướng": Kéo tướng
- "đặt tướng": Đặt tướng xuống bàn

## Tùy chỉnh tọa độ

Các tọa độ trong `tft_voice_controller.py` cần được tùy chỉnh theo màn hình của bạn:

1. Chụp màn hình: `controller.cmd_screenshot()`
2. Mở ảnh và xác định tọa độ cần thiết
3. Cập nhật tọa độ trong các function tương ứng

## Tích hợp Voice Recognition

Để tích hợp với Whisper hoặc engine voice recognition khác:

```python
from tft_voice_controller import TFTVoiceController

def my_voice_callback():
    # Trả về text từ voice recognition
    return "lệnh voice đã nhận dạng"

controller = TFTVoiceController()
controller.connect()
controller.start_voice_loop(my_voice_callback)
```

## Port LDPlayer

- Instance 1: 5555
- Instance 2: 5557
- Instance 3: 5559
- ...

Khi khởi tạo controller, chỉ định port:
```python
controller = TFTVoiceController(ldplayer_port=5557)
```

## Troubleshooting

### Không kết nối được ADB

1. Kiểm tra LDPlayer đang chạy
2. Kiểm tra port đúng chưa
3. Enable ADB trong LDPlayer Settings

### Chụp màn hình chậm

Sử dụng method `capture_fast()` hoặc cài đặt minicap để tối ưu.

### Tọa độ không đúng

Tùy chỉnh tọa độ theo kích thước màn hình thực tế của bạn.

## License

MIT License
