# Environment Setup - Đường dẫn công cụ

## Đường dẫn quan trọng

### Python (Dành cho dự án TFT)
- **Location:** `F:\Python311\python.exe`
- **Version:** 3.11.9
- **Pip:** `F:\Python311\Scripts\pip.exe`

**Sử dụng:**
```powershell
& "F:\Python311\python.exe" script.py
& "F:\Python311\Scripts\pip.exe" install package
```

### Python (Cho Stable Diffusion)
- **Location:** `F:\SD 1.5\system\python\python.exe`
- **Version:** 3.10.6
- **Lưu ý:** Minimal build, không dùng cho dự án TFT

### LDPlayer
- **Installation:** `F:\LDPlayer\`
- **ADB:** `F:\LDPlayer\LDPlayer9\adb.exe`
- **ADB Port:** 5555 (instance 1), 5557 (instance 2), etc.

**Kết nối ADB:**
```powershell
& "F:\LDPlayer\LDPlayer9\adb.exe" connect 127.0.0.1:5555
& "F:\LDPlayer\LDPlayer9\adb.exe" devices
```

### Cấu hình trong code

**ADB Controller:**
```python
from core.adb_controller import ADBController

adb = ADBController(
    adb_path=r"F:\LDPlayer\LDPlayer9\adb.exe",
    ldplayer_port=5555
)
```

**Test scripts:**
```powershell
cd tests
& "F:\SD 1.5\system\python\python.exe" test_adb.py
& "F:\SD 1.5\system\python\python.exe" test_capture.py
```

## Cài đặt Dependencies

```powershell
# Cài đặt dependencies cơ bản
& "F:\SD 1.5\system\python\Scripts\pip.exe" install -r requirements.txt

# Cài đặt OCR dependencies
& "F:\SD 1.5\system\python\Scripts\pip.exe" install -r requirements_ocr.txt

# Cài đặt LLM dependencies (nếu cần)
& "F:\SD 1.5\system\python\Scripts\pip.exe" install -r requirements_llm.txt
```

## Environment Variables (Optional)

Nếu muốn set environment variables để tiện dùng:

```powershell
# Thêm vào $PROFILE
$env:PYTHON_PATH = "F:\SD 1.5\system\python\python.exe"
$env:ADB_PATH = "F:\LDPlayer\LDPlayer9\adb.exe"
```

## Kiểm tra kết nối

```powershell
# Kiểm tra ADB connection
& "F:\LDPlayer\LDPlayer9\adb.exe" devices

# Kiểm tra Python
& "F:\SD 1.5\system\python\python.exe" --version
```

## Lưu ý

- LDPlayer cần bật ADB trong Settings trước khi kết nối
- Port 5555 là instance đầu tiên, 5557 là instance thứ 2, v.v.
- Python 3.10.6 đã được cài sẵn cho Stable Diffusion
