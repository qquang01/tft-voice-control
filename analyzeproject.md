# Phân tích & Theo dõi vấn đề dự án ToolTFT

> File này dùng để theo dõi các vấn đề trong dự án.
> Quy tắc: tick checkbox `[x]` khi đã fix, xóa dòng hoặc chuyển sang mục "Đã giải quyết".

---

## 🔴 Critical Bugs (Cần fix ngay trước khi chạy)

| # | Vấn đề | File | Dòng | Trạng thái |
|---|--------|------|------|------------|
| 1 | **Typo `self.cr` không tồn tại** — phải là `self.ocr` | `ocr/ocr_reader.py` | 260 | [ ] |
| 2 | **Slice syntax lỗi `x:x:w`** — phải là `x:x+w` | `ocr/pixel_detector.py` | 111, 185, 227, 263 | [ ] |
| 3 | **Slice syntax lỗi `x:x:w`** — phải là `x:x+w` | `ocr/champion_detector.py` | (nếu có) | [ ] |
| 4 | **Sai package name TFT Mobile** — đang dùng `com.riotgames.league.wildrift` (Wild Rift), đúng là `com.riotgames.league.teamfighttactics` | `voice/tft_voice_controller.py`, `ocr/tft_ocr_controller.py` | 89, 94, 502, 510 | [ ] |
| 5 | **Import path thiếu sys.path** — `from llm_engine import ...` sẽ fail khi chạy standalone | `ai/tft_decision_engine.py` | 3 | [ ] |

### Chi tiết fix nhanh

#### Bug 1: Typo `self.cr` → `self.ocr`
```python
# ocr/ocr_reader.py dòng 260
results = self.ocr.read_text(self.ui_regions['level'])  # sửa từ self.cr
```

#### Bug 2 & 3: Slice syntax `x:x:w` → `x:x+w`
```python
# Trong pixel_detector.py và champion_detector.py
# Sửa tất cả: img[y:y+h, x:x:w] → img[y:y+h, x:x+w]
```

#### Bug 4: Package name
```python
# Sửa trong tft_voice_controller.py và tft_ocr_controller.py
"com.riotgames.league.wildrift" → "com.riotgames.league.teamfighttactics"
```

#### Bug 5: Import path
```python
# ai/tft_decision_engine.py
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from llm_engine import BaseLLM, LLMFactory  # hoặc dùng from .llm_engine import ...
```

---

## 🟡 Code Quality / Refactor

| # | Vấn đề | File liên quan | Ghi chú | Trạng thái |
|---|--------|----------------|---------|------------|
| 6 | **Hardcoded UI coordinates** khắp nơi | `ocr/tft_ocr_controller.py`, `voice/tft_voice_controller.py`, `ocr/pixel_detector.py`, `ocr/champion_detector.py` | Nên tách thành `config/regions.json` hoặc class `UIConfig` | [ ] |
| 7 | **Duplicate code ghi âm** | `voice/stt_engine.py` | `WhisperPython.transcribe_live`, `VoiceInputCLI.record_and_transcribe`, `VoiceInputGUI.toggle_recording` đều chứa logic pyaudio/wave giống nhau → tách thành `AudioRecorder` class | [ ] |
| 8 | **`wave` là built-in module** | `requirements_stt.txt` dòng 8 | Xóa `wave>=0.0.2` khỏi requirements | [ ] |
| 9 | **Tests chỉ là smoke test** | `tests/test_*.py` | Không có `assert`, không mock ADB → không thể chạy CI nếu không có LDPlayer | [ ] |
| 10 | **`__init__.py` trống hoặc thiếu public API** | `core/__init__.py`, `ocr/__init__.py`, `voice/__init__.py`, `ai/__init__.py` | Nên expose `ADBController`, `ScreenCapture`, `TFTVoiceController`, v.v. | [ ] |
| 11 | **ChampionDetector chưa handle multi-resolution** | `ocr/champion_detector.py` | Template matching cần resize hoặc multi-scale nếu LDPlayer đổi độ phân giải | [ ] |

---

## 🟠 Missing Features (so với Architecture Docs)

| # | Feature | Mô tả | Phase | Trạng thái |
|---|---------|-------|-------|------------|
| 12 | **Wake Word Detection** | Theo `ARCHITECTURE_EVALUATION.md` Phase 2 | Phase 2 | [ ] |
| 13 | **CLI Feedback module** | Hiển thị trạng thái game trên terminal realtime | Phase 2 | [ ] |
| 14 | **Context Resolver integration** | `ContextResolver` đã có trong `intent_parser.py` nhưng chưa được dùng trong controller chính | Phase 2 | [ ] |
| 15 | **Fine-tuned Whisper** | Theo `ARCHITECTURE_EVALUATION.md` Phase 3 — fine-tune cho TFT vocabulary | Phase 3 | [ ] |
| 16 | **Overlay UI** | Đã đánh giá là "không cần cho MVP" trong docs → có thể bỏ qua | Phase 3 | N/A |
| 17 | **RAG Knowledge Base** | `LLM_EVALUATION.md` đề xuất nhưng chưa có module riêng | Phase 3 | [ ] |

---

## 🟢 Đã hoàn thành tốt (Giữ nguyên)

- [x] Kiến trúc 4 lớp: Voice Input → AI Processing → Game Bridge → Action Execution
- [x] ADB Controller với auto-discovery path
- [x] Screen Capture (screencap + pull)
- [x] OCR Reader (EasyOCR + Tesseract fallback)
- [x] Champion Detector (Template Matching)
- [x] Pixel Detector (color + edge detection)
- [x] Rule-based Intent Parser đầy đủ 13 actions
- [x] Action Planner với context resolver
- [x] LLM Engine (Gemini/Groq/Local factory)
- [x] TFT Decision Engine (auto-play loop)
- [x] STT Factory (Whisper Python / Whisper.cpp)
- [x] Tách requirements theo module (`requirements.txt`, `requirements_ocr.txt`, `requirements_llm.txt`, `requirements_stt.txt`)

---

## 📋 Checklist trước khi test lần đầu

```
[ ] Fix Bug 1: self.cr → self.ocr
[ ] Fix Bug 2: x:x:w → x:x+w (pixel_detector.py, 4 vị trí)
[ ] Fix Bug 3: x:x:w → x:x+w (champion_detector.py)
[ ] Fix Bug 4: wildrift → teamfighttactics (2 file)
[ ] Fix Bug 5: import path trong ai/tft_decision_engine.py
[ ] Xóa wave>=0.0.2 khỏi requirements_stt.txt
[ ] Chạy test_adb.py để verify ADB connection
[ ] Chụp 1 screenshot từ LDPlayer để xác định độ phân giải
[ ] Cập nhật ui_regions trong ocr_reader.py theo độ phân giải thực tế
[ ] Chạy test_ocr.py để verify OCR
```

---

## 📝 Ghi chú thêm

- **Mục tiêu MVP**: `Whisper (Voice) → Rule-based Intent → OCR State → ADB Action`
- **Độ phân giải khuyên dùng**: 1280x720 hoặc 1920x1080 (để template matching ổn định)
- **Ngôn ngữ voice**: Tiếng Việt (`language="vi"` đã set trong WhisperPython)
- **Tối ưu latency**: Có thể tắt `auto_play` loop, chỉ trigger OCR khi có voice command
