# Đề xuất Kiến trúc cho TFT Voice Control Tool

## Tổng quan

Tool hiện tại đã có cấu trúc cơ bản với các module: ADB, Screen Capture, OCR, Voice Control, và GUI. Sau khi refactoring shop_visualizer thành component-based architecture, tôi đề xuất kiến trúc **Clean Architecture với Component-based Design** phù hợp cho tool này.

---

## Kiến trúc Đề xuất

```
┌─────────────────────────────────────────────────────────────┐
│                     Presentation Layer                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   GUI App    │  │   CLI App    │  │  Web/Remote  │      │
│  │ (CustomTkinter)│  │  (Commands)  │  │   (Optional)  │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
└─────────┼──────────────────┼──────────────────┼──────────────┘
          │                  │                  │
┌─────────▼──────────────────▼──────────────────▼──────────────┐
│                    Application Layer                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ GUI Manager  │  │ Voice Flow   │  │ Game Flow    │      │
│  │ (Coordinator)│  │  Controller  │  │  Controller  │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
└─────────┼──────────────────┼──────────────────┼──────────────┘
          │                  │                  │
┌─────────▼──────────────────▼──────────────────▼──────────────┐
│                    Domain Layer                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Intent     │  │   Game       │  │   Champion   │      │
│  │   Parser     │  │   State     │  │   Manager    │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Action     │  │   Board      │  │   Shop       │      │
│  │   Planner    │  │   Manager    │  │   Manager    │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
└─────────┼──────────────────┼──────────────────┼──────────────┘
          │                  │                  │
┌─────────▼──────────────────▼──────────────────▼──────────────┐
│                   Infrastructure Layer                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   ADB        │  │   Screen     │  │   OCR        │      │
│  │  Controller  │  │   Capture    │  │   Reader     │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   STT        │  │   Pixel      │  │   LLM        │      │
│  │   Engine     │  │   Detector   │  │   (Optional) │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

---

## Chi tiết từng Layer

### 1. Presentation Layer (UI Layer)

**Mục đích:** Giao tiếp với người dùng

**Components:**
- **GUI App** (CustomTkinter)
  - `ShopVisualizer` - Coordinator đã refactor
  - Components: `ShopPreview`, `TemplateLabeling`, `ScreenshotCapture`, `BatchLabeling`, `SlotConfigPanel`
  - `ChatPanel` - Voice chat interface
  - `AudioManager` - Audio feedback

- **CLI App** (Commands)
  - Voice commands trực tiếp
  - Batch processing
  - Debug/testing tools

- **Web/Remote** (Optional - tương lai)
  - Web interface cho remote control
  - Mobile app companion

---

### 2. Application Layer

**Mục đích:** Orchestrate business logic và flows

**Components:**

#### GUI Manager
- `ShopVisualizer` - Đã refactor thành coordinator pattern
- `VoiceController` - Quản lý voice input/output
- `DebugLogger` - Logging và debugging

#### Voice Flow Controller
```python
class VoiceFlowController:
    """Quản lý flow từ voice input đến action execution"""
    def __init__(self):
        self.stt_engine = STTEngine()
        self.intent_parser = IntentParser()
        self.action_planner = ActionPlanner()
        self.action_executor = ActionExecutor()
    
    def process_voice_command(self, audio_input):
        # 1. Transcribe audio
        text = self.stt_engine.transcribe(audio_input)
        
        # 2. Parse intent
        intent = self.intent_parser.parse(text)
        
        # 3. Get game state
        game_state = self.get_game_state()
        
        # 4. Plan action
        action_plan = self.action_planner.plan(intent, game_state)
        
        # 5. Execute action
        result = self.action_executor.execute(action_plan)
        
        return result
```

#### Game Flow Controller
```python
class GameFlowController:
    """Quản lý game state và automation flows"""
    def __init__(self):
        self.game_state = GameState()
        self.board_manager = BoardManager()
        self.shop_manager = ShopManager()
        self.champion_manager = ChampionManager()
    
    def auto_play_round(self):
        # Auto-play logic cho từng round
        pass
```

---

### 3. Domain Layer (Business Logic)

**Mục đích:** Core business logic, không phụ thuộc infrastructure

**Components:**

#### Intent Parser
- **Rule-based Parser** (Hiện tại)
  - Regex patterns cho commands
  - Entity extraction
  - Intent classification

- **LLM Parser** (Optional - tương lai)
  - GPT/Claude integration
  - Context-aware parsing
  - Natural language understanding

```python
class IntentParser:
    def parse(self, text: str) -> Intent:
        """Parse text thành Intent object"""
        # Rule-based parsing
        if self.matches_rule(text, "BUY"):
            return self.parse_buy_intent(text)
        elif self.matches_rule(text, "SELL"):
            return self.parse_sell_intent(text)
        # ... more rules
```

#### Game State
```python
class GameState:
    """Track trạng thái game hiện tại"""
    def __init__(self):
        self.gold: int
        self.health: int
        self.level: int
        self.xp: int
        self.board: List[Champion]
        self.shop: List[Champion]
        self.items: List[Item]
    
    def update_from_ocr(self, ocr_result):
        """Update state từ OCR result"""
        pass
```

#### Action Planner
```python
class ActionPlanner:
    """Plan actions dựa trên intent và game state"""
    def plan(self, intent: Intent, game_state: GameState) -> ActionPlan:
        """Tạo action plan"""
        if intent.action == "BUY":
            return self.plan_buy(intent, game_state)
        elif intent.action == "SELL":
            return self.plan_sell(intent, game_state)
        # ... more actions
```

#### Champion Manager
- Champion database
- Synergy calculator
- Build optimizer

#### Board Manager
- Board position tracking
- Champion placement logic
- Formation optimizer

#### Shop Manager
- Shop reading (đã có ShopReader)
- Champion detection
- Shop refresh logic

---

### 4. Infrastructure Layer

**Mục đích:** External dependencies và low-level operations

**Components:**

#### ADB Controller (đã có)
- `ADBController` - Kết nối ADB
- Tap, swipe, keyevent operations

#### Screen Capture (đã có)
- `ScreenCapture` - Chụp màn hình từ LDPlayer
- Frame caching
- Performance optimization

#### OCR Reader (đã có)
- `OCRReader` - Đọc text từ màn hình
- EasyOCR/Tesseract integration
- Region-based OCR

#### Pixel Detector (đã có)
- `PixelDetector` - Phát hiện UI bằng pixel
- Color matching
- Pattern detection

#### STT Engine (đã có)
- `STTEngine` - Whisper integration
- Noise filtering
- Wake word detection

#### LLM Engine (đã có - optional)
- `LLMEngine` - GPT/Claude integration
- Decision engine
- Context-aware reasoning

---

## Cấu trúc Thư mục Đề xuất

```
tooltft/
├── presentation/              # Presentation Layer
│   ├── gui/
│   │   ├── main_window.py         # Main GUI window
│   │   ├── components/            # GUI components (đã có)
│   │   │   ├── shop_preview.py
│   │   │   ├── template_labeling.py
│   │   │   ├── screenshot_capture.py
│   │   │   ├── batch_labeling.py
│   │   │   └── slot_config_panel.py
│   │   ├── chat_panel.py
│   │   └── audio_manager.py
│   └── cli/
│       └── commands.py
│
├── application/              # Application Layer
│   ├── coordinators/
│   │   ├── shop_visualizer.py      # Đã refactor
│   │   ├── voice_flow_controller.py
│   │   └── game_flow_controller.py
│   └── services/
│       ├── debug_logger.py
│       └── config_service.py
│
├── domain/                   # Domain Layer
│   ├── intents/
│   │   ├── intent_parser.py
│   │   ├── rule_based_parser.py
│   │   └── llm_parser.py (optional)
│   ├── game/
│   │   ├── game_state.py
│   │   ├── board_manager.py
│   │   ├── shop_manager.py
│   │   └── champion_manager.py
│   ├── actions/
│   │   ├── action_planner.py
│   │   └── action_executor.py
│   └── models/
│       ├── champion.py
│       ├── item.py
│       └── intent.py
│
├── infrastructure/           # Infrastructure Layer
│   ├── adb/
│   │   └── adb_controller.py
│   ├── capture/
│   │   └── screen_capture.py
│   ├── ocr/
│   │   ├── ocr_reader.py
│   │   └── pixel_detector.py
│   ├── voice/
│   │   ├── stt_engine.py
│   │   └── tts_engine.py (optional)
│   └── ai/
│       ├── llm_engine.py
│       └── decision_engine.py
│
├── shared/                   # Shared utilities
│   ├── utils/
│   │   ├── image_display_helper.py (đã có)
│   │   └── debug_logger.py
│   └── config/
│       └── config.py (đã có)
│
└── tests/                    # Tests
    ├── presentation/
    ├── application/
    ├── domain/
    └── infrastructure/
```

---

## Lợi ích của Kiến trúc Đề xuất

### 1. **Separation of Concerns**
- Mỗi layer có trách nhiệm rõ ràng
- Dễ test từng component
- Dễ maintain và debug

### 2. **Dependency Inversion**
- Domain layer không phụ thuộc infrastructure
- Dễ swap implementation (ví dụ: thay OCR engine)
- Dễ mock cho testing

### 3. **Scalability**
- Dễ thêm feature mới
- Dễ mở rộng sang platform khác (Web, Mobile)
- Dễ tích hợp LLM hoặc AI features

### 4. **Reusability**
- Domain logic có thể dùng cho CLI, GUI, hoặc Web
- Components có thể tái sử dụng
- Dễ tạo batch processing tools

### 5. **Testability**
- Mỗi layer có thể test độc lập
- Dễ mock dependencies
- Dễ viết integration tests

---

## Migration Plan

### Phase 1: Restructure (1-2 tuần)
1. Tạo folder structure mới
2. Di chuyển existing code vào appropriate folders
3. Update imports
4. Ensure tests still pass

### Phase 2: Domain Layer (1 tuần)
1. Extract domain logic từ existing code
2. Create domain models (Champion, Item, Intent, GameState)
3. Implement Intent Parser (rule-based)
4. Implement Action Planner
5. Unit tests

### Phase 3: Application Layer (1 tuần)
1. Create VoiceFlowController
2. Create GameFlowController
3. Integrate with domain layer
4. Integration tests

### Phase 4: Infrastructure Layer (1 tuần)
1. Ensure all infrastructure components clean
2. Add interfaces/abstractions
3. Implement dependency injection
4. Tests

### Phase 5: Presentation Layer (1 tuần)
1. GUI already refactored ✓
2. Create CLI app
3. Integration testing
4. Documentation

---

## Ví dụ Implementation

### Domain Layer - Intent Parser

```python
# domain/intents/intent_parser.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class Intent:
    action: str
    parameters: dict
    confidence: float

class IntentParser:
    def parse(self, text: str) -> Intent:
        """Parse text thành intent"""
        # Implementation
        pass

class RuleBasedIntentParser(IntentParser):
    def __init__(self):
        self.rules = {
            r"mua\s+(\w+)": self._parse_buy,
            r"bán\s+(\d+)": self._parse_sell,
            # ... more rules
        }
    
    def parse(self, text: str) -> Intent:
        for pattern, handler in self.rules.items():
            if match := re.match(pattern, text):
                return handler(match)
        return Intent("UNKNOWN", {}, 0.0)
```

### Application Layer - Voice Flow Controller

```python
# application/coordinators/voice_flow_controller.py
from domain.intents.intent_parser import IntentParser
from domain.actions.action_planner import ActionPlanner
from infrastructure.voice.stt_engine import STTEngine
from infrastructure.ocr.ocr_reader import OCRReader

class VoiceFlowController:
    def __init__(self):
        self.stt_engine = STTEngine()
        self.intent_parser = IntentParser()
        self.action_planner = ActionPlanner()
        self.ocr_reader = OCRReader()
    
    def process_voice_command(self, audio_input):
        text = self.stt_engine.transcribe(audio_input)
        intent = self.intent_parser.parse(text)
        game_state = self.ocr_reader.get_game_state()
        action_plan = self.action_planner.plan(intent, game_state)
        return action_plan
```

---

## Kết luận

Kiến trúc đề xuất:
- **Clean Architecture** với 4 layer rõ ràng
- **Component-based design** cho GUI (đã implement)
- **Dependency Inversion** để dễ test và maintain
- **Scalable** cho future features (LLM, Web, Mobile)
- **Practical** cho mục tiêu hiện tại (help disabled people play TFT)

**Khuyến nghị:**
1. Bắt đầu với Phase 1: Restructure
2. Tận dụng GUI components đã refactor
3. Duy trì OCR + Pixel approach (đã có và hoạt động tốt)
4. Rule-based intent parser cho MVP
5. LLM integration sau khi core stable

**Next Steps:**
1. Review và approve architecture
2. Bắt đầu Phase 1 migration
3. Update documentation
4. Create implementation timeline
