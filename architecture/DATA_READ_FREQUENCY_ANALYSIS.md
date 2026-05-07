# Đánh Giá Tần Suất Đọc Dữ Liệu Phù Hợp

## 1. Tổng quan

Tần suất đọc data ảnh hưởng trực tiếp đến:
- **Latency**: Thời gian phản hồi
- **Resource usage**: CPU, RAM, battery
- **Accuracy**: Không bỏ sót thay đổi quan trọng
- **User experience**: Smoothness của GUI

## 2. Các thành phần đọc data

### 2.1 Screen Capture

**Methods:**
- `screencap` (ADB): 50-100ms per capture
- `minicap` (nếu có): 10-30ms per capture
- `scrcpy` stream: Realtime nhưng tốn bandwidth

**Tần suất đề xuất:**

| Use Case | FPS | Latency | Resource | Rationale |
|----------|-----|---------|----------|-----------|
| Realtime labeling | 10-15 FPS | 67-100ms | Medium | Balance smoothness vs CPU |
| Batch labeling | 1-5 FPS | 200-1000ms | Low | Không cần realtime |
| Change detection | 2-5 FPS | 200-500ms | Low | Chỉ detect khi thay đổi |
| Debug/Development | 30 FPS | 33ms | High | Maximum smoothness |

**Phân tích chi tiết:**

```python
class AdaptiveFrameRate:
    """Tự động điều chỉnh FPS dựa trên system load"""
    
    def __init__(self):
        self.current_fps = 10
        self.min_fps = 5
        self.max_fps = 30
        self.target_latency_ms = 100  # Target 100ms total latency
        self.cpu_threshold = 80  # CPU% threshold
    
    def calculate_optimal_fps(self, capture_latency_ms: float, 
                              detection_latency_ms: float,
                              cpu_usage: float) -> int:
        """
        Tính FPS tối ưu dựa trên latency và CPU load
        
        Args:
            capture_latency_ms: Latency của screen capture
            detection_latency_ms: Latency của detection (OCR/template)
            cpu_usage: CPU usage hiện tại (%)
            
        Returns:
            FPS tối ưu
        """
        # Total latency per frame
        total_latency = capture_latency_ms + detection_latency_ms
        
        # Max FPS dựa trên latency
        max_fps_by_latency = 1000 / total_latency
        
        # Adjust dựa trên CPU
        if cpu_usage > self.cpu_threshold:
            # Reduce FPS nếu CPU cao
            adjusted_fps = max_fps_by_latency * 0.5
        else:
            adjusted_fps = max_fps_by_latency
        
        # Clamp trong range
        optimal_fps = max(self.min_fps, min(self.max_fps, int(adjusted_fps)))
        
        return optimal_fps
```

**Ví dụ thực tế:**

```
Scenario 1: ADB screencap (80ms) + Template matching (5ms)
- Total latency: 85ms
- Max FPS: 1000/85 = 11.7 FPS
- Recommended: 10 FPS

Scenario 2: ADB screencap (80ms) + OCR (100ms)
- Total latency: 180ms
- Max FPS: 1000/180 = 5.5 FPS
- Recommended: 5 FPS

Scenario 3: minicap (20ms) + Template matching (5ms)
- Total latency: 25ms
- Max FPS: 1000/25 = 40 FPS
- Recommended: 15-20 FPS (cap để tiết kiệm resource)
```

### 2.2 OCR / Template Matching

**Tần suất đề xuất:**

| Element Type | Method | Frequency | Rationale |
|--------------|--------|-----------|-----------|
| Static UI (buttons) | Template matching | Mỗi frame | Rất nhanh (5-10ms) |
| Champion icons | Template matching | Mỗi frame | Rất nhanh (5-10ms) |
| Gold/Health | OCR | 2-5 FPS | Chậm (50-150ms) |
| Champion names | OCR | 2-5 FPS | Chậm (50-150ms) |
| Shop items | Template matching | Mỗi frame | Nhanh, cần realtime |

**Strategy: Conditional Reading**

```python
class ConditionalReader:
    """Chỉ đọc khi cần thiết"""
    
    def __init__(self):
        self.last_read_time = {}
        self.read_intervals = {
            'gold': 500,  # 500ms = 2 FPS
            'health': 500,
            'level': 1000,  # 1 FPS
            'champion_name': 300,
            'static_ui': 0,  # Mỗi frame
        }
        self.hash_cache = ImageHashCache()
    
    def should_read(self, element_type: str, current_image: np.ndarray) -> bool:
        """
        Quyết định có nên đọc element này không
        
        Returns:
            True nếu nên đọc
        """
        interval = self.read_intervals.get(element_type, 100)
        
        # Check time-based interval
        last_time = self.last_read_time.get(element_type, 0)
        if time.time() - last_time < interval / 1000:
            return False
        
        # Check image change (cho dynamic elements)
        if element_type in ['gold', 'health', 'level']:
            if not self.hash_cache.has_changed(current_image):
                return False
        
        return True
    
    def read(self, element_type: str, reader_func, *args, **kwargs):
        """Đọc với conditional logic"""
        if self.should_read(element_type, kwargs.get('image')):
            result = reader_func(*args, **kwargs)
            self.last_read_time[element_type] = time.time()
            return result
        return None  # Return cached hoặc skip
```

### 2.3 Image Hashing (Change Detection)

**Tần suất:** Mỗi frame (1-3ms latency)

```python
class ChangeDetectionStrategy:
    """Strategy cho change detection"""
    
    def __init__(self):
        self.hasher = ImageHasher()
        self.last_hash = None
        self.change_threshold = 5  # Hamming distance
        self.consecutive_changes = 0
        self.min_changes_to_trigger = 2  # Cần 2 frame liên tiếp thay đổi
    
    def detect_change(self, current_image: np.ndarray) -> bool:
        """
        Detect nếu có thay đổi đáng kể
        
        Returns:
            True nếu có thay đổi
        """
        current_hash = self.hasher.perceptual_hash(current_image)
        
        if self.last_hash is None:
            self.last_hash = current_hash
            return True
        
        distance = self.hasher.hamming_distance(self.last_hash, current_hash)
        
        if distance > self.change_threshold:
            self.consecutive_changes += 1
            self.last_hash = current_hash
            
            # Chỉ trigger nếu có đủ consecutive changes
            if self.consecutive_changes >= self.min_changes_to_trigger:
                self.consecutive_changes = 0
                return True
        else:
            self.consecutive_changes = 0
        
        return False
```

## 3. Trade-off Analysis

### 3.1 Latency vs Resource

```
High FPS (30)          Low FPS (5)
├─ Low latency         ├─ High latency
├─ High CPU            ├─ Low CPU
├─ High RAM            ├─ Low RAM
├─ Smooth UI           ├─ Choppy UI
└─ Better UX           └─ Worse UX
```

**Formula:**
```
Resource Usage ∝ FPS × (Capture_Latency + Detection_Latency)
```

**Ví dụ tính toán:**

```
Configuration A: 10 FPS
- Capture: 80ms
- Template matching: 5ms
- Total per frame: 85ms
- CPU time per second: 10 × 85ms = 850ms = 85% CPU core

Configuration B: 5 FPS
- Capture: 80ms
- OCR: 100ms
- Total per frame: 180ms
- CPU time per second: 5 × 180ms = 900ms = 90% CPU core

→ Configuration A tốt hơn dù FPS cao hơn vì detection nhanh hơn
```

### 3.2 Accuracy vs Frequency

```
High Frequency              Low Frequency
├─ Không bỏ sót changes    ├─ Có thể miss changes
├─ Redundant data          ├─ Efficient data
├─ Better for fast UI     ├─ OK cho slow UI
└─ Higher storage         └─ Lower storage
```

**Rule of thumb:**
- **Fast-changing UI** (shop reroll, champion moving): 10-15 FPS
- **Slow-changing UI** (gold, health): 2-5 FPS
- **Static UI** (buttons, icons): 1-5 FPS (hoặc event-driven)

## 4. Use Case-Specific Recommendations

### 4.1 Realtime Labeling Mode

**Goal:** User dán nhãn trên frame live

**Recommended:**
```
Screen capture: 10 FPS (100ms interval)
Template matching: Mỗi frame (static UI)
OCR: 2-5 FPS (dynamic text)
Image hashing: Mỗi frame (change detection)
```

**Rationale:**
- 10 FPS đủ smooth cho human eye
- Template matching nhanh nên có thể chạy mỗi frame
- OCR chậm nên giảm frequency
- Hashing rất nhanh nên chạy mỗi frame

**Code:**

```python
class RealtimeLabelingReader:
    """Reader cho realtime labeling mode"""
    
    def __init__(self, screen_capture, template_matcher, ocr_reader):
        self.capture = screen_capture
        self.template_matcher = template_matcher
        self.ocr = ocr_reader
        self.target_fps = 10
        self.frame_interval = 1.0 / self.target_fps
        self.last_frame_time = 0
        
        # Conditional readers
        self.conditional_reader = ConditionalReader()
        self.change_detector = ChangeDetectionStrategy()
    
    def read_loop(self, callback):
        """Main read loop"""
        while True:
            current_time = time.time()
            
            # Rate limiting
            if current_time - self.last_frame_time < self.frame_interval:
                time.sleep(0.001)
                continue
            
            self.last_frame_time = current_time
            
            # Capture frame
            frame = self.capture.capture_to_cv2()
            if frame is None:
                continue
            
            # Detect change
            has_changed = self.change_detector.detect_change(frame)
            
            # Template matching (mỗi frame)
            static_results = self.template_matcher.batch_find_elements(
                ['shop_button', 'level_up_button', 'reroll_button']
            )
            
            # OCR (conditional)
            gold_result = None
            if has_changed:
                gold_result = self.conditional_reader.read(
                    'gold',
                    self.ocr.find_text,
                    frame,
                    region=(50, 50, 100, 30)
                )
            
            # Callback với results
            callback(frame, static_results, gold_result, has_changed)
```

### 4.2 Batch Labeling Mode

**Goal:** Label nhiều ảnh offline

**Recommended:**
```
Screen capture: N/A (load từ file)
Template matching: 1 FPS (hoặc on-demand)
OCR: 1 FPS (hoặc on-demand)
Image hashing: N/A (không cần detect change)
```

**Rationale:**
- Không cần realtime
- User control khi nào detect
- Tối ưu resource

**Code:**

```python
class BatchLabelingReader:
    """Reader cho batch labeling mode"""
    
    def __init__(self, template_matcher, ocr_reader):
        self.template_matcher = template_matcher
        self.ocr = ocr_reader
    
    def load_image(self, image_path: str) -> np.ndarray:
        """Load image từ file"""
        return cv2.imread(image_path)
    
    def detect_on_demand(self, image: np.ndarray, 
                        element_types: List[str]) -> Dict:
        """
        Detect chỉ khi user request
        
        Args:
            image: Ảnh cần detect
            element_types: List elements cần detect
            
        Returns:
            Dict kết quả
        """
        results = {}
        
        for element_type in element_types:
            if element_type in ['shop_button', 'level_up_button']:
                # Template matching
                results[element_type] = self.template_matcher.find_element(
                    element_type, image
                )
            elif element_type in ['gold', 'health']:
                # OCR
                results[element_type] = self.ocr.find_text(
                    element_type, image
                )
        
        return results
```

### 4.3 Change Detection Mode

**Goal:** Chỉ detect khi có thay đổi

**Recommended:**
```
Screen capture: 5 FPS (200ms interval)
Image hashing: Mỗi frame
Template matching: Chỉ khi change detected
OCR: Chỉ khi change detected
```

**Rationale:**
- Tiết kiệm resource tối đa
- Chỉ xử lý khi cần thiết
- Phù hợp cho idle monitoring

**Code:**

```python
class ChangeDetectionReader:
    """Reader với change detection"""
    
    def __init__(self, screen_capture, template_matcher, ocr_reader):
        self.capture = screen_capture
        self.template_matcher = template_matcher
        self.ocr = ocr_reader
        self.hasher = ImageHashCache()
        self.target_fps = 5
    
    def read_loop(self, callback):
        """Read loop với change detection"""
        while True:
            frame = self.capture.capture_to_cv2()
            if frame is None:
                continue
            
            # Check change
            if self.hasher.has_changed(frame):
                # Có thay đổi → detect
                results = {
                    'static': self.template_matcher.batch_find_elements(
                        ['shop_button', 'level_up_button']
                    ),
                    'dynamic': self.ocr.find_text('gold', frame)
                }
                callback(frame, results, changed=True)
            else:
                # Không thay đổi → skip detection
                callback(frame, {}, changed=False)
            
            time.sleep(1.0 / self.target_fps)
```

## 5. Performance Benchmarks

### 5.1 Measured Latencies (LDPlayer + ADB)

| Operation | Latency (ms) | Notes |
|-----------|--------------|-------|
| ADB screencap | 80-100 | Default method |
| ADB pull | 20-30 | Transfer time |
| Total capture | 100-130 | screencap + pull |
| Template matching | 5-10 | 640x480 image |
| Multi-scale template | 15-25 | 5 scales |
| OCR (EasyOCR) | 50-150 | Text length dependent |
| OCR (Tesseract) | 30-80 | Faster but less accurate |
| Image hashing (pHash) | 1-3 | Perceptual hash |
| Feature matching (ORB) | 20-40 | 1000 keypoints |

### 5.2 Resource Usage at Different FPS

| FPS | CPU Usage | RAM Usage | Battery Impact |
|-----|-----------|-----------|----------------|
| 5 | 30-40% | 200MB | Low |
| 10 | 50-60% | 250MB | Medium |
| 15 | 70-80% | 300MB | High |
| 30 | 90-100% | 400MB | Very High |

## 6. Adaptive Strategy

```python
class AdaptiveDataReader:
    """Tự động điều chỉnh tần suất dựa trên conditions"""
    
    def __init__(self):
        self.current_fps = 10
        self.cpu_history = []
        self.latency_history = []
        self.adjustment_interval = 5  # Adjust mỗi 5 giây
    
    def monitor_and_adjust(self, capture_latency, detection_latency, cpu_usage):
        """Monitor và adjust FPS"""
        # Lưu history
        self.cpu_history.append(cpu_usage)
        self.latency_history.append(capture_latency + detection_latency)
        
        # Giữ history ngắn
        if len(self.cpu_history) > 60:
            self.cpu_history.pop(0)
            self.latency_history.pop(0)
        
        # Adjust mỗi interval
        if len(self.cpu_history) % self.adjustment_interval == 0:
            avg_cpu = sum(self.cpu_history[-self.adjustment_interval:]) / self.adjustment_interval
            avg_latency = sum(self.latency_history[-self.adjustment_interval:]) / self.adjustment_interval
            
            # CPU quá cao → giảm FPS
            if avg_cpu > 80:
                self.current_fps = max(5, self.current_fps - 2)
                print(f"Reducing FPS to {self.current_fps} (CPU: {avg_cpu:.1f}%)")
            
            # CPU thấp, latency tốt → tăng FPS
            elif avg_cpu < 50 and avg_latency < 50:
                self.current_fps = min(30, self.current_fps + 2)
                print(f"Increasing FPS to {self.current_fps} (CPU: {avg_cpu:.1f}%)")
    
    def get_current_fps(self) -> int:
        return self.current_fps
```

## 7. Final Recommendations

### 7.1 Cho TFT Labeling Tool

**Default Configuration:**
```
Screen capture: 10 FPS
Template matching: Mỗi frame (static UI)
OCR: 3 FPS (dynamic text)
Image hashing: Mỗi frame (change detection)
```

**Why:**
- Balance giữa smoothness và resource
- Template matching đủ nhanh để chạy mỗi frame
- OCR giảm frequency để tiết kiệm CPU
- Hashing rất nhanh nên không ảnh hưởng performance

### 7.2 Adaptive Configuration

```python
# Tự động adjust dựa trên mode
CONFIGURATIONS = {
    'performance': {
        'fps': 15,
        'ocr_fps': 5,
        'template_every_frame': True
    },
    'balanced': {
        'fps': 10,
        'ocr_fps': 3,
        'template_every_frame': True
    },
    'battery_saver': {
        'fps': 5,
        'ocr_fps': 2,
        'template_every_frame': False  # Conditional
    }
}
```

### 7.3 User Override

Cho phép user override FPS trong GUI:
```
[Performance Mode ▼]  Balanced
[Custom FPS: □] 10
[OCR FPS: □] 3
```

## 8. Monitoring & Debugging

```python
class PerformanceMonitor:
    """Monitor performance metrics"""
    
    def __init__(self):
        self.metrics = {
            'fps': [],
            'capture_latency': [],
            'detection_latency': [],
            'cpu_usage': [],
            'cache_hit_rate': []
        }
    
    def record(self, fps, capture_latency, detection_latency, cpu_usage, cache_hit_rate):
        """Record metrics"""
        self.metrics['fps'].append(fps)
        self.metrics['capture_latency'].append(capture_latency)
        self.metrics['detection_latency'].append(detection_latency)
        self.metrics['cpu_usage'].append(cpu_usage)
        self.metrics['cache_hit_rate'].append(cache_hit_rate)
    
    def get_summary(self) -> Dict:
        """Get summary statistics"""
        return {
            'avg_fps': np.mean(self.metrics['fps']),
            'avg_capture_latency': np.mean(self.metrics['capture_latency']),
            'avg_detection_latency': np.mean(self.metrics['detection_latency']),
            'avg_cpu_usage': np.mean(self.metrics['cpu_usage']),
            'avg_cache_hit_rate': np.mean(self.metrics['cache_hit_rate'])
        }
```

## 9. Conclusion

**Key takeaways:**
1. **Không phải越高 FPS càng tốt** - balance với resource
2. **Conditional reading** - chỉ đọc khi cần thiết
3. **Hybrid approach** - template matching mỗi frame, OCR giảm frequency
4. **Adaptive strategy** - tự động adjust dựa trên system load
5. **User control** - cho phép override configuration

**Recommended default:** 10 FPS capture, 3 FPS OCR, template matching mỗi frame
