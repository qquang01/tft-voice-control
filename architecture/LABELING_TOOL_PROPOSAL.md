# Labeling Tool với Realtime Reader - Phương án kiến trúc

## 1. Mục tiêu

Xây dựng tool dán nhãn dữ liệu TFT với khả năng đọc realtime để:
- Dán nhãn tướng, UI elements trên màn hình TFT
- Hỗ trợ training cho champion detector, OCR models
- Tự động hóa việc thu thập dữ liệu training

## 2. Kiến trúc đề xuất

### 2.1 Tổng quan (4 lớp)

```
┌─────────────────────────────────────────────────┐
│         Labeling GUI (CustomTkinter)            │
│  - Image viewer with realtime preview           │
│  - Bounding box drawing                         │
│  - Label classification                         │
│  - Realtime OCR overlay                         │
└────────────────┬────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────┐
│      Labeling Controller                        │
│  - Manage labeling state                        │
│  - Coordinate capture + OCR + GUI              │
│  - Save/load labels                             │
└────────────────┬────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────┐
│      Realtime Reader Engine                     │
│  - ScreenCapture (threaded)                     │
│  - OCRReader (async)                            │
│  - ChampionDetector                             │
│  - PixelDetector                                │
└────────────────┬────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────┐
│      Data Layer                                 │
│  - Labels storage (JSON/YAML)                   │
│  - Image cache                                  │
│  - Template storage                             │
└─────────────────────────────────────────────────┘
```

### 2.2 Module chi tiết

#### A. Realtime Reader Engine (`labeling/realtime_reader.py`)

```python
class RealtimeReader:
    """Engine đọc realtime từ màn hình"""
    
    def __init__(self, screen_capture: ScreenCapture, 
                 ocr_reader: OCRReader,
                 champion_detector: ChampionDetector):
        self.capture = screen_capture
        self.ocr = ocr_reader
        self.detector = champion_detector
        self.running = False
        self.frame_rate = 10  # FPS
        self.callbacks = []
    
    def start(self):
        """Bắt đầu stream realtime"""
        self.running = True
        threading.Thread(target=self._stream_loop, daemon=True).start()
    
    def _stream_loop(self):
        """Loop chụp + OCR trong thread riêng"""
        while self.running:
            frame = self.capture.capture_to_cv2()
            if frame:
                # Chạy OCR async
                ocr_results = self.ocr.read_text()
                # Chạy detection
                champions = self.detector.detect_champions(frame)
                
                # Callback với kết quả
                for callback in self.callbacks:
                    callback(frame, ocr_results, champions)
            
            time.sleep(1.0 / self.frame_rate)
    
    def register_callback(self, callback):
        """Đăng ký callback nhận frame + OCR results"""
        self.callbacks.append(callback)
```

#### B. Labeling Controller (`labeling/labeling_controller.py`)

```python
class LabelingController:
    """Controller quản lý labeling workflow"""
    
    def __init__(self, realtime_reader: RealtimeReader):
        self.reader = realtime_reader
        self.current_labels = []
        self.current_image = None
        self.labeling_mode = "bbox"  # bbox, point, polygon
        self.label_classes = ["champion", "ui_element", "text", "button"]
    
    def add_label(self, bbox: Tuple[int, int, int, int], 
                  label_class: str, 
                  label_text: str = ""):
        """Thêm label mới"""
        self.current_labels.append({
            "bbox": bbox,
            "class": label_class,
            "text": label_text,
            "timestamp": time.time()
        })
    
    def save_labels(self, save_path: str):
        """Lưu labels xuống file (JSON/COCO/YOLO format)"""
        import json
        with open(save_path, 'w') as f:
            json.dump({
                "image": self.current_image_path,
                "labels": self.current_labels
            }, f, indent=2)
    
    def load_labels(self, load_path: str):
        """Load labels từ file"""
        import json
        with open(load_path, 'r') as f:
            data = json.load(f)
            self.current_labels = data["labels"]
```

#### C. Labeling GUI (`labeling/labeling_gui.py`)

```python
class LabelingGUI:
    """GUI cho labeling tool"""
    
    def __init__(self, controller: LabelingController):
        self.controller = controller
        self.root = ctk.CTk()
        self.setup_ui()
        
        # Register callback từ realtime reader
        self.controller.reader.register_callback(self.on_new_frame)
    
    def setup_ui(self):
        """Setup UI layout"""
        # Left: Canvas hiển thị ảnh + bounding boxes
        self.canvas_frame = ctk.CTkFrame(self.root)
        self.canvas_frame.pack(side="left", fill="both", expand=True)
        
        self.image_canvas = ctk.CTkCanvas(self.canvas_frame)
        self.image_canvas.pack(fill="both", expand=True)
        self.image_canvas.bind("<Button-1>", self.on_canvas_click)
        self.image_canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.image_canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        
        # Right: Controls
        self.controls_frame = ctk.CTkFrame(self.root)
        self.controls_frame.pack(side="right", fill="y", padx=10)
        
        # Label class selector
        self.class_selector = ctk.CTkOptionMenu(
            self.controls_frame,
            values=self.controller.label_classes,
            command=self.on_class_change
        )
        self.class_selector.pack(pady=5)
        
        # OCR overlay toggle
        self.ocr_overlay_var = ctk.BooleanVar(value=True)
        self.ocr_toggle = ctk.CTkCheckBox(
            self.controls_frame,
            text="Show OCR overlay",
            variable=self.ocr_overlay_var
        )
        self.ocr_toggle.pack(pady=5)
        
        # Realtime toggle
        self.realtime_btn = ctk.CTkButton(
            self.controls_frame,
            text="Start Realtime",
            command=self.toggle_realtime
        )
        self.realtime_btn.pack(pady=5)
        
        # Save/Load buttons
        self.save_btn = ctk.CTkButton(
            self.controls_frame,
            text="Save Labels",
            command=self.save_labels
        )
        self.save_btn.pack(pady=5)
    
    def on_new_frame(self, frame, ocr_results, champions):
        """Callback khi có frame mới từ realtime reader"""
        self.current_frame = frame
        self.ocr_results = ocr_results
        self.detected_champions = champions
        
        # Update canvas trên main thread
        self.root.after(0, self.update_canvas)
    
    def update_canvas(self):
        """Update canvas với frame mới + overlays"""
        if not self.current_frame:
            return
        
        # Convert frame to PIL Image
        from PIL import Image, ImageTk
        img = Image.fromarray(self.current_frame)
        self.photo = ImageTk.PhotoImage(img)
        
        # Clear và vẽ lại
        self.image_canvas.delete("all")
        self.image_canvas.create_image(0, 0, image=self.photo, anchor="nw")
        
        # Vẽ OCR overlay nếu enabled
        if self.ocr_overlay_var.get():
            self.draw_ocr_overlay()
        
        # Vẽ detected champions
        self.draw_champion_detections()
        
        # Vẽ user labels
        self.draw_user_labels()
    
    def draw_ocr_overlay(self):
        """Vẽ kết quả OCR lên canvas"""
        for result in self.ocr_results:
            x, y, w, h = result['bbox']
            text = result['text']
            conf = result['conf']
            
            # Vẽ bounding box màu xanh lá
            self.image_canvas.create_rectangle(
                x, y, x+w, y+h,
                outline="#00FF00", width=2
            )
            
            # Vẽ text
            self.image_canvas.create_text(
                x, y-10,
                text=f"{text} ({conf:.2f})",
                fill="#00FF00", anchor="nw"
            )
```

## 3. Image-based Comparison thay vì OCR (UI tĩnh)

### 3.1 Tại sao ưu tiên image comparison?

**Vấn đề với OCR:**
- OCR chậm (50-150ms mỗi lần)
- Accuracy không cao cho icons, buttons
- Tốn resources cho text không cần thiết

**Lợi ích của Image Comparison:**
- Template matching: ~5-10ms (10-20x nhanh hơn OCR)
- Pixel detection: ~1-3ms
- Accuracy cao cho UI tĩnh
- Reuse `PixelDetector` đã có trong project

### 3.2 Hybrid Detection Strategy

```
┌─────────────────────────────────────────────┐
│  Detection Decision Tree                    │
└─────────────────────────────────────────────┘
                    │
        ┌───────────▼───────────┐
        │  Element type?        │
        └───────────┬───────────┘
                    │
     ┌──────────────┼──────────────┐
     │              │              │
     ▼              ▼              ▼
 Static UI      Dynamic Text   Champion
 (buttons,      (gold, health,  (icons)
  icons, UI)    level)         │
     │              │              │
     ▼              ▼              ▼
Template        OCR          Template
Matching        (EasyOCR)    Matching
(5-10ms)        (50-150ms)   (5-10ms)
```

### 3.3 Image Hashing để Detect Thay đổi

```python
class ImageHashCache:
    """Cache image hashes để detect thay đổi nhanh"""
    
    def __init__(self):
        self.last_hash = None
        self.hash_threshold = 5  # Hamming distance threshold
    
    def compute_hash(self, image: np.ndarray) -> str:
        """Compute perceptual hash của image"""
        import imagehash
        from PIL import Image
        
        img = Image.fromarray(image)
        return str(imagehash.phash(img))
    
    def has_changed(self, current_image: np.ndarray) -> bool:
        """Kiểm tra image có thay đổi không"""
        current_hash = self.compute_hash(current_image)
        
        if self.last_hash is None:
            self.last_hash = current_hash
            return True
        
        # Compute Hamming distance
        distance = sum(c1 != c2 for c1, c2 in zip(self.last_hash, current_hash))
        
        if distance > self.hash_threshold:
            self.last_hash = current_hash
            return True
        
        return False
```

### 3.4 Template Matching Workflow

```python
class TemplateMatcher:
    """Template matching engine cho UI tĩnh"""
    
    def __init__(self, pixel_detector: PixelDetector):
        self.detector = pixel_detector
        self.template_cache = {}  # Cache template images
        self.match_cache = {}    # Cache matching results
        self.cache_ttl = 60  # Cache TTL in seconds
    
    def load_templates_from_folder(self, folder_path: str):
        """Load tất cả templates từ folder"""
        for filename in os.listdir(folder_path):
            if filename.endswith(('.png', '.jpg')):
                name = os.path.splitext(filename)[0]
                path = os.path.join(folder_path, filename)
                self.detector.load_template(name, path)
                print(f"Loaded template: {name}")
    
    def find_element(self, element_name: str, 
                     region: Tuple[int, int, int, int] = None,
                     force_refresh: bool = False) -> Optional[Tuple[int, int]]:
        """
        Tìm element với caching
        
        Args:
            element_name: Tên template
            region: Vùng tìm kiếm
            force_refresh: Bypass cache
            
        Returns:
            Tọa độ (x, y) hoặc None
        """
        cache_key = f"{element_name}_{region}"
        
        # Check cache
        if not force_refresh and cache_key in self.match_cache:
            cached_result, cached_time = self.match_cache[cache_key]
            if time.time() - cached_time < self.cache_ttl:
                return cached_result
        
        # Perform matching
        result = self.detector.find_template(element_name, region=region)
        
        # Update cache
        self.match_cache[cache_key] = (result, time.time())
        
        return result
    
    def batch_find_elements(self, element_names: List[str],
                           region: Tuple[int, int, int, int] = None) -> Dict[str, Optional[Tuple[int, int]]]:
        """
        Tìm nhiều elements cùng lúc
        
        Args:
            element_names: List tên elements
            region: Vùng tìm kiếm
            
        Returns:
            Dict mapping element_name -> position
        """
        results = {}
        for name in element_names:
            results[name] = self.find_element(name, region)
        return results
```

### 3.5 Caching Strategy

```python
class DetectionCache:
    """Multi-level cache cho detection results"""
    
    def __init__(self):
        # Level 1: In-memory cache (fastest)
        self.l1_cache = {}  # {key: (result, timestamp)}
        self.l1_ttl = 5  # 5 seconds
        
        # Level 2: Disk cache (persistent)
        self.l2_cache_dir = "cache/detection"
        os.makedirs(self.l2_cache_dir, exist_ok=True)
        self.l2_ttl = 3600  # 1 hour
    
    def get(self, key: str) -> Optional[Any]:
        """Get từ cache với multi-level lookup"""
        # Check L1
        if key in self.l1_cache:
            result, timestamp = self.l1_cache[key]
            if time.time() - timestamp < self.l1_ttl:
                return result
            else:
                del self.l1_cache[key]
        
        # Check L2
        l2_path = os.path.join(self.l2_cache_dir, f"{key}.pkl")
        if os.path.exists(l2_path):
            import pickle
            with open(l2_path, 'rb') as f:
                data = pickle.load(f)
                if time.time() - data['timestamp'] < self.l2_ttl:
                    # Promote to L1
                    self.l1_cache[key] = (data['result'], time.time())
                    return data['result']
        
        return None
    
    def set(self, key: str, result: Any):
        """Set vào cache (cả L1 và L2)"""
        # L1 cache
        self.l1_cache[key] = (result, time.time())
        
        # L2 cache
        import pickle
        l2_path = os.path.join(self.l2_cache_dir, f"{key}.pkl")
        with open(l2_path, 'wb') as f:
            pickle.dump({
                'result': result,
                'timestamp': time.time()
            }, f)
```

### 3.6 Updated Realtime Reader với Hybrid Detection

```python
class HybridRealtimeReader:
    """Realtime reader với hybrid detection (template + OCR)"""
    
    def __init__(self, screen_capture: ScreenCapture,
                 pixel_detector: PixelDetector,
                 ocr_reader: OCRReader):
        self.capture = screen_capture
        self.pixel_detector = pixel_detector
        self.ocr = ocr_reader
        
        self.template_matcher = TemplateMatcher(pixel_detector)
        self.hash_cache = ImageHashCache()
        self.detection_cache = DetectionCache()
        
        # Element classification
        self.static_elements = {
            'shop_button', 'level_up_button', 'reroll_button',
            'buy_button', 'sell_button', 'item_slot',
            'bench_slot', 'board_slot'
        }
        
        self.dynamic_elements = {
            'gold', 'health', 'level', 'champion_name'
        }
    
    def detect_element(self, element_name: str,
                       region: Tuple[int, int, int, int] = None) -> Dict:
        """
        Detect element với chiến lược hybrid
        
        Returns:
            Dict với 'method', 'result', 'latency'
        """
        cache_key = f"{element_name}_{region}"
        
        # Check cache trước
        cached = self.detection_cache.get(cache_key)
        if cached:
            return {
                'method': 'cache',
                'result': cached,
                'latency': 0.001
            }
        
        start_time = time.time()
        
        # Static UI elements → Template matching
        if element_name in self.static_elements:
            result = self.template_matcher.find_element(element_name, region)
            method = 'template_matching'
            latency = time.time() - start_time
        
        # Dynamic text elements → OCR
        elif element_name in self.dynamic_elements:
            result = self.ocr.find_text(element_name, region)
            method = 'ocr'
            latency = time.time() - start_time
        
        # Unknown → Fallback to template
        else:
            result = self.template_matcher.find_element(element_name, region)
            method = 'template_fallback'
            latency = time.time() - start_time
        
        # Cache result
        self.detection_cache.set(cache_key, result)
        
        return {
            'method': method,
            'result': result,
            'latency': latency
        }
    
    def get_detection_stats(self) -> Dict:
        """Get statistics về detection methods"""
        return {
            'cache_hit_rate': self.detection_cache.get_hit_rate(),
            'avg_template_latency': self.template_matcher.get_avg_latency(),
            'avg_ocr_latency': self.ocr.get_avg_latency()
        }
```

## 4. Workflow sử dụng

### 3.1 Realtime Labeling Mode

1. **Bắt đầu realtime capture**
   - User click "Start Realtime"
   - RealtimeReader bắt đầu chụp màn hình @ 10 FPS
   - OCR + Champion detection chạy async

2. **Dán nhãn trên frame live**
   - User vẽ bounding box trên canvas
   - Chọn label class (champion, ui_element, etc.)
   - Label được lưu vào controller

3. **OCR assist**
   - OCR text hiển thị overlay trên canvas
   - User có thể click vào OCR text để auto-label
   - Tự động điền text vào label

4. **Save labels**
   - Labels được lưu cùng với screenshot
   - Format: JSON với COCO/YOLO compatibility

### 3.2 Batch Labeling Mode

1. **Load dataset từ folder**
   - Load tất cả ảnh từ folder
   - Auto-detect champions + OCR

2. **Review & correct labels**
   - User review từng ảnh
   - Edit/delete/add labels
   - Navigation giữa các ảnh

3. **Export**
   - Export sang format training (COCO, YOLO, Pascal VOC)

## 4. Integration với modules hiện có

### 4.1 Reuse existing modules

```python
# Từ core/
from core.screen_capture import ScreenCapture
from core.adb_controller import ADBController

# Từ ocr/
from ocr.ocr_reader import OCRReader
from ocr.champion_detector import ChampionDetector
from ocr.pixel_detector import PixelDetector

# Từ gui/
from gui.utils.debug_logger import DebugLogger
```

### 4.2 Cấu trúc thư mục mới

```
tooltft/
├── labeling/                    # NEW: Labeling tool module
│   ├── __init__.py
│   ├── realtime_reader.py       # Realtime capture + OCR engine
│   ├── labeling_controller.py   # Label management
│   ├── labeling_gui.py          # CustomTkinter GUI
│   ├── label_formats.py         # Export formats (COCO, YOLO, etc.)
│   └── label_storage.py         # Database/file storage
├── labels/                      # NEW: Lưu labels
│   ├── champion_labels/         # Labels cho champion detection
│   ├── ui_labels/               # Labels cho UI elements
│   └── text_labels/             # Labels cho OCR training
└── screenshots/                  # Đã có: lưu screenshots
```

## 5. Features ưu tiên

### Phase 1 (MVP)
- [ ] Realtime screen capture @ 10 FPS
- [ ] OCR overlay trên canvas
- [ ] Manual bounding box drawing
- [ ] Label class selection
- [ ] Save/load labels (JSON)
- [ ] Integration với ScreenCapture + OCRReader hiện có

### Phase 2
- [ ] Auto-detection assist (ChampionDetector)
- [ ] Batch labeling mode
- [ ] Export sang COCO/YOLO format
- [ ] Keyboard shortcuts
- [ ] Undo/redo labels

### Phase 3
- [ ] Multi-class labeling
- [ ] Polygon labeling
- [ ] Keypoint labeling
- [ ] Label statistics dashboard
- [ ] Training pipeline integration

## 6. Tech Stack

- **GUI**: CustomTkinter (đã có trong project)
- **Image processing**: OpenCV (đã có)
- **OCR**: EasyOCR/Tesseract (đã có)
- **Storage**: JSON/YAML
- **Threading**: Python threading (đã có pattern trong tft_gui.py)

## 7. Performance considerations

- **Realtime capture**: 10 FPS (tối ưu cho labeling)
- **OCR latency**: Async processing, không block GUI
- **Memory**: Cache tối đa 50 frames gần nhất
- **Storage**: Incremental save mỗi 5 labels

## 8. Dependencies mới

```txt
# requirements_labeling.txt
Pillow>=10.0.0  # Image processing cho GUI
labelme>=5.0.0  # Optional: import/export labelme format
pycocotools>=2.0.0  # Optional: COCO format support
ImageHash>=4.3.0  # Perceptual hashing cho image comparison
```

## 9. Timeline đề xuất

- **Tuần 1**: Implement RealtimeReader + LabelingController
- **Tuần 2**: Implement basic GUI (canvas, bbox drawing)
- **Tuần 3**: Integration OCR overlay + save/load
- **Tuần 4**: Testing + refinement
