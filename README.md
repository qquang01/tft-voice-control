# TFT Mobile Voice Control Tool

Công cụ hỗ trợ chơi TFT Mobile trên LDPlayer bằng voice control và OCR, dành cho người khuyết tật.

## 📁 Cấu trúc dự án

```
tooltft/
├── architecture/          # Tài liệu kiến trúc
│   └── ARCHITECTURE_EVALUATION.md
├── core/                 # Core modules
│   ├── adb_controller.py # Điều khiển ADB
│   └── screen_capture.py # Chụp màn hình
├── voice/                # Voice control modules
│   ├── tft_voice_controller.py # Voice controller cơ bản
│   └── intent_parser.py  # Rule-based intent parser
├── ocr/                  # OCR modules
│   ├── ocr_reader.py     # Đọc text từ màn hình
│   ├── pixel_detector.py # Phát hiện UI bằng pixel
│   └── tft_ocr_controller.py # Controller OCR + ADB
├── tests/                # Test scripts
│   ├── test_adb.py
│   ├── test_capture.py
│   ├── test_ocr.py
│   ├── test_pixel_detector.py
│   └── test_ocr_controller.py
├── docs/                 # Documentation
│   ├── README.md         # Hướng dẫn voice control
│   └── README_OCR.md     # Hướng dẫn OCR method
├── requirements.txt      # Dependencies cơ bản
├── requirements_ocr.txt  # Dependencies OCR
└── whisper.cpp/          # Whisper STT engine
```

## 🚀 Quick Start

### Cài đặt dependencies

```bash
pip install -r requirements.txt
pip install -r requirements_ocr.txt
```

### Test kết nối ADB

```bash
cd tests
python test_adb.py
```

### Test OCR

```bash
python test_ocr.py
python test_pixel_detector.py
```

## 📖 Documentation

- **[Voice Control Guide](docs/README.md)** - Hướng dẫn voice control cơ bản
- **[OCR Method Guide](docs/README_OCR.md)** - Hướng dẫn phương án OCR + Pixel
- **[Architecture Evaluation](architecture/ARCHITECTURE_EVALUATION.md)** - Đánh giá kiến trúc 4 lớp Enterprise

## 🔧 Các phương án triển khai

### 1. Voice-only (Cơ bản)
- Sử dụng Whisper + ADB
- Latency: 1-3s
- Đơn giản, dễ setup

### 2. OCR + Pixel (Khuyên dùng cho MVP)
- Sử dụng OCR để đọc game state
- Latency: 50-150ms
- Offline hoàn toàn
- Accuracy cao

### 3. Enterprise 4-Layer (Advanced)
- Voice Input → AI Processing → Game Bridge → Action Execution
- Context-aware commands
- Phức tạp hơn, cần nhiều resources

## 🎯 Khuyến nghị

**Cho MVP (Minimum Viable Product):**
```
Whisper (Voice) → Rule-based Intent → OCR State → ADB Action
```

**Lý do:**
- Offline hoàn toàn
- Latency chấp nhận được (~200ms total)
- Đã có foundation (whisper.cpp, OCR modules)
- Dễ bảo trì
- Không tốn chi phí

## 🛠️ Sử dụng

### Voice Control cơ bản

```python
from voice.tft_voice_controller import TFTVoiceController

controller = TFTVoiceController()
controller.connect()
controller.process_voice_command("mua Ahri")
```

### OCR-based Control

```python
from ocr.tft_ocr_controller import TFTOCRController

controller = TFTOCRController(use_easyocr=True)
controller.connect()

# Lấy game state
state = controller.get_game_state()
print(f"Gold: {state['gold']}")

# Mua tướng
controller.buy_champion("Ahri")
```

### Intent Parser

```python
from voice.intent_parser import RuleBasedIntentParser

parser = RuleBasedIntentParser()
intent = parser.parse("mua Ahri")
# intent.action = "BUY"
# intent.parameters = {"champion": "Ahri"}
```

## 🧪 Testing

```bash
# Test từng module
cd tests
python test_adb.py
python test_capture.py
python test_ocr.py
python test_pixel_detector.py
python test_ocr_controller.py
```

## ⚙️ Cấu hình

### ADB Path
Mặc định tìm trong:
- `C:\LDPlayer\LDPlayer9\adb.exe`
- `C:\LDPlayer\LDPlayer4\adb.exe`

Hoặc chỉ định:
```python
adb = ADBController(adb_path="path/to/adb.exe")
```

### LDPlayer Port
- Instance 1: 5555 (mặc định)
- Instance 2: 5557
- Instance 3: 5559

```python
controller = TFTOCRController(ldplayer_port=5557)
```

### OCR Engine
```python
# EasyOCR (khuyên dùng)
controller = TFTOCRController(use_easyocr=True)

# Tesseract
controller = TFTOCRController(use_easyocr=False)
```

## 📝 License

MIT License

## ❤️ Dành cho người khuyết tật

Tool này được phát triển để hỗ trợ người khuyết tật chơi TFT Mobile dễ dàng hơn thông qua voice control và automation.
