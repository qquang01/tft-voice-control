# Đánh giá Kiến trúc 4 Lớp Enterprise cho TFT Voice Control

## Tổng quan

Kiến trúc đề xuất gồm 4 lớp:
1. **Voice Input Layer** - Nhận giọng nói
2. **AI Processing Layer** - Xử lý intent và context
3. **Game Bridge Layer** - Kết nối game
4. **Action Execution Layer** - Thực thi action

---

## 🎙 Lớp 1: Voice Input Layer

### Components
- **Web Speech API** - Browser-based STT
- **Whisper / Deepgram** - Advanced STT
- **Noise Filter** - Lọc tiếng ồn
- **Wake Word** - Phát hiện từ khóa kích hoạt
- **Transcript** - Chuyển giọng thành text

### Đánh giá từng option

#### Web Speech API
**Ưu điểm:**
- Miễn phí, built-in browser
- Không cần setup
- Latency thấp (~200-500ms)
- Không cần GPU

**Nhược điểm:**
- Phụ thuộc browser
- Không offline
- Accuracy thấp với tiếng Việt
- Không tùy chỉnh được

**Khuyến nghị:** Không dùng cho production, chỉ cho prototype

#### Whisper (đã có trong dự án)
**Ưu điểm:**
- Đã có whisper.cpp trong dự án
- Offline hoàn toàn
- Accuracy cao với đa ngôn ngữ
- Tùy chỉnh được model size
- Có thể fine-tune

**Nhược điểm:**
- Cần GPU để real-time (model lớn)
- Latency cao nếu CPU (~1-3s)
- Cài đặt phức tạp

**Khuyến nghị:** **Khuyên dùng** cho production offline

#### Deepgram
**Ưu điểm:**
- Accuracy rất cao
- Latency thấp (~300ms)
- Streaming real-time
- Support tiếng Việt tốt

**Nhược điểm:**
- Phải trả phí (có free tier giới hạn)
- Phụ thuộc internet
- Không offline

**Khuyến nghị:** Dùng nếu có budget và chấp nhận online

#### Noise Filter
**Options:**
- RNNoise (lightweight)
- NoiseTorch (Python)
- WebRTC VAD

**Khuyến nghị:** RNNoise + WebRTC VAD (đã có trong whisper.cpp)

#### Wake Word
**Options:**
- Porcupine (paid)
- OpenWakeWord (open source)
- Custom VAD-based

**Khuyến nghị:** OpenWakeWord hoặc custom VAD threshold

---

## 🧠 Lớp 2: AI Processing Layer

### Components
- **NLP Intent Recognition** - Nhận diện ý định
- **Intent Parser** - Parse lệnh
- **LLM / Fine-tuned Model** - Model AI
- **Game State Reader** - Đọc trạng thái game
- **Context Resolver** - Giải quyết context

### Đánh giá

#### Intent Recognition
**Options:**
1. **Rule-based** (Regex/Pattern matching)
   - Ưu: Đơn giản, nhanh, dễ debug
   - Nhược: Giới hạn, không flexible
   - Khuyên dùng: Bắt đầu với rule-based

2. **Slot Filling** (rasa nlu, spaCy)
   - Ưu: Extract entities tốt
   - Nhược: Cần training data
   - Khuyên dùng: Nếu có nhiều commands phức tạp

3. **LLM-based** (GPT, Claude)
   - Ưu: Flexible, hiểu context tốt
   - Nhược: Chậm, phải trả phí
   - Khuyên dùng: Chỉ cho complex queries

#### Game State Reader
**Options:**
1. **OCR-based** (đã implement)
   - Ưu: Không phụ thuộc API
   - Nhược: Latency ~50-150ms
   - Khuyên dùng: **Khuyên dùng**

2. **API-based** (Riot API)
   - Ưu: Chính xác, real-time
   - Nhược: Không hỗ trợ TFT Mobile, chỉ PC
   - Khuyên dùng: Không khả dụng

3. **Memory Reading** (LeagueClientUx hook)
   - Ưu: Real-time, chính xác
   - Nhược: Phức tạp, dễ bị detect
   - Khuyên dùng: Không dùng cho LDPlayer

#### Context Resolver
**Ví dụ:** "put Darius on 4"
- Cần biết: Darius ở đâu? Position 4 là gì?
- Solution: Track champion positions + OCR

**Khuyến nghị:** Implement state machine để track game state

---

## 🔗 Lớp 3: Game Bridge Layer

### Components
- **Overlay (Electron)** - HUD trên màn hình
- **Screen Reader** - Đọc màn hình
- **API / Riot Plugin** - Kết nối API
- **LeagueClientUx Hook** - Hook vào client

### Đánh giá

#### Overlay (Electron)
**Ưu điểm:**
- UI đẹp, customizable
- Có thể hiển thị feedback
- Cross-platform

**Nhược điểm:**
- Phức tạp để implement
- Resource heavy
- Có thể bị game anti-cheat detect

**Khuyến nghị:** Không cần cho MVP, chỉ cần CLI feedback

#### Screen Reader
**Đã implement với OCR-based approach**

**Khuyên dùng:** **Khuyên dùng** - đã có sẵn

#### API / Riot Plugin
**Nhược điểm:**
- Không hỗ trợ TFT Mobile
- Chỉ có cho PC version
- Cần authentication

**Khuyến nghị:** Không khả dụng

#### LeagueClientUx Hook
**Nhược điểm:**
- Không hoạt động trên LDPlayer
- High risk of ban
- Phức tạp

**Khuyến nghị:** Không dùng

---

## ⚡ Lớp 4: Action Execution Layer

### Components
- **Mouse / Keyboard Simulation** → TFT
- **Buy / Sell Champion**
- **Move on Board**
- **Roll / Level Up**
- **Equip Item**

### Đánh giá

#### Mouse / Keyboard Simulation
**Options:**
1. **ADB Input** (đã implement)
   - Ưu: Works trên LDPlayer, stable
   - Nhược: Latency ~100ms
   - Khuyên dùng: **Khuyên dùng**

2. **PyAutoGUI**
   - Ưu: Đơn giản, cross-platform
   - Nhược: Không work trên LDPlayer
   - Khuyên dùng: Không dùng

3. **Windows Input API**
   - Ưu: Latency thấp
   - Nhược: Không work trên LDPlayer
   - Khuyên dùng: Không dùng

#### Action Implementation
**Đã implement:**
- Tap (adb tap)
- Swipe (adb swipe)
- Key press (adb keyevent)

**Cần thêm:**
- Champion position tracking
- Item management
- Board coordinate mapping

---

## So sánh 3 Phương án

| Feature | Voice-only | OCR+Pixel | 4-Layer Enterprise |
|---------|-----------|-----------|-------------------|
| **Setup Time** | 1-2 giờ | 4-8 giờ | 2-4 tuần |
| **Dependencies** | Python + Whisper | Python + OCR | Python + OCR + LLM + Overlay |
| **Latency** | 1-3s | 50-150ms | 200-500ms (voice) + 50-150ms (OCR) |
| **CPU Usage** | Thấp | Thấp | Trung bình (LLM) |
| **Accuracy** | Trung bình | Cao (UI ổn định) | Rất cao (context-aware) |
| **Flexibility** | Giới hạn | Cao | Rất cao |
| **Maintenance** | Ít | Trung bình | Cao |
| **Cost** | Miễn phí | Miễn phí | $0-100/tháng (LLM API) |
| **Offline** | Có | Có | Một phần (LLM online) |
| **Learning Curve** | Dễ | Trung bình | Khó |

---

## Đề xuất Triển khai cho Người Khuyết Tật

### MVP (Minimum Viable Product)
**Sử dụng:** OCR + Pixel + Whisper (Rule-based Intent)

**Lý do:**
1. Offline hoàn toàn - không phụ thuộc internet
2. Latency chấp nhận được (~200ms total)
3. Accuracy cao với context-aware rules
4. Dễ bảo trì
5. Không tốn chi phí

**Architecture:**
```
Voice (Whisper) → Rule-based Intent → OCR State → ADB Action
```

### Phase 2 (Enhancement)
**Thêm:**
- LLM cho complex queries (optional)
- Simple CLI feedback (không cần Overlay)
- Wake word detection

### Phase 3 (Advanced)
**Nếu cần:**
- Overlay UI cho visual feedback
- Fine-tune model cho TFT-specific vocabulary
- Context-aware state machine

---

## Implementation Plan

### Phase 1: Core (1-2 tuần)
1. ✅ ADB Controller
2. ✅ Screen Capture
3. ✅ OCR Reader
4. ✅ Pixel Detector
5. ✅ Basic Voice (Whisper)
6. ⏳ Rule-based Intent Parser
7. ⏳ Game State Tracker

### Phase 2: Enhancement (1 tuần)
8. ⏳ Wake Word Detection
9. ⏳ Context Resolver
10. ⏳ Action Planner
11. ⏳ CLI Feedback

### Phase 3: Advanced (Optional)
12. ⏳ LLM Integration
13. ⏳ Overlay UI
14. ⏳ Fine-tuning

---

## Chi tiết Rule-based Intent Parser

### Intent Categories
1. **BUY** - "mua Ahri", "buy Syndra"
2. **SELL** - "bán tướng 1", "sell slot 3"
3. **MOVE** - "để Darius lên bàn", "put Ahri on 4"
4. **ROLL** - "làm mới", "roll shop"
5. **LEVEL** - "lên cấp", "level up"
6. **ITEM** - "lên đồ", "buy item"
7. **INFO** - "kiểm tra gold", "what's my health"

### Example Rules
```python
rules = {
    r"mua\s+(\w+)": ("BUY", {"champion": group1}),
    r"bán\s+(\d+)": ("SELL", {"slot": int(group1)}),
    r"đặt\s+(\w+)\s+trên\s+(\d+)": ("MOVE", {"champion": group1, "position": group2}),
    r"làm mới": ("ROLL", {}),
    r"lên cấp": ("LEVEL", {}),
}
```

---

## Kết luận

**Khuyến nghị:** Bắt đầu với **OCR + Pixel + Whisper (Rule-based)**

**Lý do:**
1. Đã có foundation (whisper.cpp, OCR, ADB)
2. Offline hoàn toàn - quan trọng cho người khuyết tật
3. Latency chấp nhận được
4. Dễ debug và bảo trì
5. Có thể scale lên LLM sau nếu cần

**Không cần:**
- Overlay (phức tạp, không cần thiết)
- Riot API (không hỗ trợ TFT Mobile)
- LeagueClientUx hook (không work trên LDPlayer)
- LLM cho MVP (rule-based đủ cho basic commands)

**Next Steps:**
1. Implement Rule-based Intent Parser
2. Integrate với OCR State Reader
3. Test với real TFT gameplay
4. Tinh chỉnh rules và OCR regions
