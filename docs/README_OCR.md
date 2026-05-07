# TFT OCR + Pixel Coordinate Method

Phương án tự đọc màn hình sử dụng OCR + Pixel Coordinate, hoàn toàn độc lập chỉ dùng Python.

## Đặc điểm

- **Setup time**: vài giờ
- **Dependency**: Chỉ Python + thư viện (opencv, numpy, easyocr/pytesseract)
- **Dùng cá nhân**: Không cần publish
- **Latency**: ~50-150ms (poll)
- **CPU overhead**: Thấp nếu poll đúng cách
- **Bảo trì**: Cần fix nếu UI thay đổi

## Cài đặt

### Cài đặt dependencies

```bash
pip install -r requirements_ocr.txt
```

### Cài đặt OCR Engine

**Option 1: EasyOCR (Khuyên dùng)**
```bash
pip install easyocr
# Tự động download model khi chạy lần đầu
```

**Option 2: Tesseract OCR**
```bash
# Windows: Download từ https://github.com/UB-Mannheim/tesseract/wiki
# Cài đặt và thêm vào PATH
pip install pytesseract
```

## Cấu trúc Module

### 1. `ocr_reader.py` - Đọc text từ màn hình

```python
from ocr_reader import OCRReader, TFTUIReader

# Khởi tạo
ocr = OCRReader(screen_capture, use_easyocr=True)

# Đọc text từ màn hình
results = ocr.read_text()
for result in results:
    print(f"Text: {result['text']}, Vị trí: {result['bbox']}")

# Tìm text cụ thể
pos = ocr.find_text("Gold")
if pos:
    print(f"Tìm thấy tại: {pos}")
```

### 2. `pixel_detector.py` - Phát hiện bằng pixel

```python
from pixel_detector import PixelDetector, TFTPixelDetector

# Khởi tạo
detector = PixelDetector(screen_capture)

# Load template
detector.load_template("buy_button", "templates/buy_button.png")

# Tìm template
pos = detector.find_template("buy_button", threshold=0.8)

# Tìm màu
pos = detector.find_color((255, 215, 0), tolerance=30)  # Tìm màu vàng
```

### 3. `tft_ocr_controller.py` - Controller chính

```python
from tft_ocr_controller import TFTOCRController

# Khởi tạo
controller = TFTOCRController(use_easyocr=True)
controller.connect()

# Lấy game state
state = controller.get_game_state()
print(f"Gold: {state['gold']}, Level: {state['level']}")

# Mua tướng
controller.buy_champion("Ahri")

# Lên cấp
controller.level_up()

# Monitor game state
def on_update(state):
    print(f"Health: {state['health']}")

controller.register_callback('game_state', on_update)
controller.start_monitoring(interval=1.0)
```

## Cấu hình UI Regions

Các vùng UI cần tùy chỉnh theo màn hình trong `ocr_reader.py`:

```python
self.ui_regions = {
    'gold': (50, 50, 100, 30),      # (x, y, width, height)
    'health': (150, 50, 100, 30),
    'level': (250, 50, 50, 30),
    'shop': (400, 600, 400, 150),
    'bench': (100, 700, 800, 100),
    'board': (100, 200, 800, 400),
}
```

### Cách xác định tọa độ

1. Chụp màn hình: `controller.capture.capture("screenshot.png")`
2. Mở ảnh và đo tọa độ các vùng
3. Cập nhật vào `ui_regions`

## Tạo Templates

1. Chụp màn hình khi UI hiển thị
2. Cắt vùng cần detect (ví dụ: nút Buy)
3. Lưu vào thư mục `templates/`
4. Load trong code:

```python
detector.load_template("buy_button", "templates/buy_button.png")
```

## Auto-play Examples

### Tự động mua tướng

```python
target_champions = ["Ahri", "Syndra", "Ashe"]
controller.auto_buy_champions(target_champions, max_gold=50)
```

### Tự động lên cấp

```python
controller.auto_level_up(target_level=8)
```

### Tự động refresh shop

```python
controller.auto_refresh(min_gold=4)
```

## Performance Optimization

### Polling Interval

```python
# Mặc định 100ms
controller.poll_interval = 0.1

# Tăng lên nếu CPU cao
controller.poll_interval = 0.2  # 200ms
```

### Region-based Detection

Chỉ đọc vùng cần thiết thay vì toàn màn hình:

```python
# Chỉ đọc vùng shop
results = ocr.read_text(region=(400, 600, 400, 150))
```

### Template Matching Threshold

```python
# Tăng threshold để giảm false positive
pos = detector.find_template("button", threshold=0.9)

# Giảm threshold để tăng sensitivity
pos = detector.find_template("button", threshold=0.7)
```

## Troubleshooting

### OCR không đọc được text

- Kiểm tra độ phân giải màn hình LDPlayer (khuyên dùng 1280x720 hoặc 1920x1080)
- Tăng độ tương phản UI trong game settings
- Thử cả EasyOCR và Tesseract, chọn cái tốt hơn

### Template không tìm thấy

- Template cần giống hệt với màn hình (cùng resolution)
- Threshold quá cao -> giảm xuống
- UI thay đổi -> tạo template mới

### Latency cao

- Tăng poll_interval
- Sử dụng region-based detection thay vì toàn màn hình
- Giảm số lượng operation trong mỗi poll

### CPU usage cao

- Tăng poll_interval
- Giảm số lượng template matching
- Sử dụng threading cho các operation nặng

## Integration với Voice Control

Kết hợp với `tft_voice_controller.py`:

```python
from tft_voice_controller import TFTVoiceController
from tft_ocr_controller import TFTOCRController

voice_ctrl = TFTVoiceController()
ocr_ctrl = TFTOCRController()

voice_ctrl.connect()
ocr_ctrl.connect()

# Voice command triggers OCR action
def cmd_buy_ahri():
    ocr_ctrl.buy_champion("Ahri")

voice_ctrl.register_command("mua ahri", cmd_buy_ahri)
```

## Workflow Khuyến nghị

1. **Setup**: Cài đặt dependencies, cấu hình ADB
2. **Calibration**: Chụp màn hình, xác định tọa độ UI regions
3. **Template Creation**: Tạo templates cho các UI elements
4. **Testing**: Test từng function riêng lẻ
5. **Integration**: Tích hợp với voice control nếu cần
6. **Optimization**: Tunning polling interval và thresholds

## So sánh với Voice-only Method

| Feature | Voice-only | OCR + Pixel |
|---------|-----------|-------------|
| Setup | Đơn giản | Phức tạp hơn |
| Accuracy | Phụ thuộc voice recognition | Phụ thuộc UI stability |
| Latency | ~1-2s | ~50-150ms |
| CPU | Thấp (chỉ khi voice) | Thấp (polling) |
| Bảo trì | Ít thay đổi | Cần update khi UI thay đổi |
| Flexibility | Giới hạn | Cao (có thể đọc bất kỳ text) |
