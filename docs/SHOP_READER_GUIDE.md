# Shop Reader - Hướng Dẫn Sử Dụng

## Tổng quan

Shop Reader là module để đọc và so sánh 5 vùng ảnh trong cửa hàng TFT. Mỗi cửa hàng hiển thị 5 champions, module này sẽ identify từng champion bằng template matching.

## Cấu trúc

```
labeling/
├── __init__.py
└── shop_reader.py          # Module chính

tests/
└── test_shop_reader.py     # Test script

templates/
└── shop_champions/         # Folder chứa templates cho champions
    ├── ahri.png
    ├── yasuo.png
    └── ...

screenshots/
└── shop_slots/             # Folder lưu slot images khi test
    ├── slot_0.png
    ├── slot_1.png
    └── ...
```

## Cài đặt

Không cần dependencies mới - sử dụng các modules hiện có:
- `opencv-python` (đã có)
- `numpy` (đã có)
- `core.screen_capture` (đã có)
- `ocr.pixel_detector` (đã có)

## Sử dụng

### Bước 1: Tạo Templates

Trước khi sử dụng, bạn cần tạo templates cho các champions:

```bash
cd tests
python test_shop_reader.py create
```

Script sẽ:
1. Chụp màn hình hiện tại
2. Extract 5 slot images từ shop
3. Lưu vào `screenshots/shop_slots/`
4. Hỏi tên champion cho mỗi slot
5. Lưu templates vào `templates/shop_champions/`

**Lưu ý:** Đảm bảo shop đang mở trong game trước khi chạy script.

### Bước 2: Test Shop Reader

```bash
cd tests
python test_shop_reader.py
```

Script sẽ:
1. Kết nối ADB
2. Load templates
3. Capture frame
4. Extract 5 slot images
5. So sánh với templates
6. Print kết quả
7. Lưu visualization

### Bước 3: Đọc Liên Tục (Debug)

```bash
cd tests
python test_shop_reader.py continuous
```

Script sẽ đọc shop liên tục mỗi 2 giây. Nhấn Ctrl+C để dừng.

## API Reference

### ShopReader Class

```python
from labeling.shop_reader import ShopReader
from core.screen_capture import ScreenCapture
from core.adb_controller import ADBController

# Khởi tạo
adb = ADBController()
adb.connect()
capture = ScreenCapture(adb)
shop_reader = ShopReader(capture)

# Load templates
shop_reader.load_templates()

# Đọc shop
result = shop_reader.read_shop(force_refresh=True)

# Get summary
print(shop_reader.get_shop_summary(result))
```

### Methods

#### `__init__(screen_capture: ScreenCapture)`

Khởi tạo Shop Reader.

**Parameters:**
- `screen_capture`: Instance của ScreenCapture

#### `load_templates(template_dir: str = None)`

Load templates từ folder.

**Parameters:**
- `template_dir`: Đường dẫn đến template folder (default: `templates/shop_champions`)

#### `read_shop(force_refresh: bool = False) -> Dict`

Đọc shop và identify 5 champions.

**Parameters:**
- `force_refresh`: Bỏ qua cache, đọc mới

**Returns:**
```python
{
    'timestamp': float,
    'slots': [
        {
            'index': int,
            'region': {'x': int, 'y': int, 'width': int, 'height': int},
            'matches': List[Dict],  # Top 3 matches
            'best_match': Dict or None,
            'has_champion': bool
        },
        ...
    ],
    'frame_shape': Tuple[int, int, int]
}
```

#### `update_shop_regions(custom_regions: List[Dict])`

Cập nhật regions tùy chỉnh.

**Parameters:**
- `custom_regions`: List dict với `index`, `x`, `y`, `width`, `height`

**Ví dụ:**
```python
custom_regions = [
    {'index': 0, 'x': 100, 'y': 500, 'width': 180, 'height': 150},
    {'index': 1, 'x': 280, 'y': 500, 'width': 180, 'height': 150},
    # ... 5 slots
]
shop_reader.update_shop_regions(custom_regions)
```

#### `save_slot_templates(slot_index: int, champion_name: str)`

Save slot image làm template.

**Parameters:**
- `slot_index`: Index của slot (0-4)
- `champion_name`: Tên champion

#### `get_shop_summary(shop_result: Dict) -> str`

Lấy summary của shop result.

**Parameters:**
- `shop_result`: Result từ `read_shop()`

**Returns:** String summary

### ShopVisualizer Class

```python
from labeling.shop_reader import ShopVisualizer

# Visualize shop
vis_frame = ShopVisualizer.visualize_shop(
    frame,
    shop_reader.shop_regions,
    result['slots']
)

# Save visualization
ShopVisualizer.save_visualization(vis_frame, "output.png")
```

## Cấu Hình

### Shop Regions

Mặc định cho LDPlayer 1280x720:
- Shop nằm ở giữa màn hình, 200px từ bottom
- 5 slots ngang, mỗi slot 180x150 pixels

Để tùy chỉnh:
```python
custom_regions = [
    {'index': 0, 'x': 190, 'y': 520, 'width': 180, 'height': 150},
    {'index': 1, 'x': 370, 'y': 520, 'width': 180, 'height': 150},
    {'index': 2, 'x': 550, 'y': 520, 'width': 180, 'height': 150},
    {'index': 3, 'x': 730, 'y': 520, 'width': 180, 'height': 150},
    {'index': 4, 'x': 910, 'y': 520, 'width': 180, 'height': 150},
]
shop_reader.update_shop_regions(custom_regions)
```

### Template Matching Threshold

Mặc định: 0.7 (70% confidence)

Để thay đổi:
```python
# Trong compare_slot_with_templates()
matches = shop_reader.compare_slot_with_templates(slot_img, threshold=0.8)
```

### Cache Interval

Mặc định: 500ms giữa các lần đọc

Để thay đổi:
```python
shop_reader.read_interval = 1.0  # 1 giây
```

## Workflow Đề Xuất

### Workflow 1: Tạo Templates Một Lần

1. Mở game, mở shop
2. Reroll shop nhiều lần để thu thập nhiều champions
3. Chạy `python test_shop_reader.py create`
4. Nhập tên champion cho mỗi slot
5. Lặp lại bước 2-4 cho nhiều shop khác nhau

### Workflow 2: Sử dụng trong Labeling Tool

```python
from labeling.shop_reader import ShopReader

# Khởi tạo
shop_reader = ShopReader(screen_capture)
shop_reader.load_templates()

# Trong labeling loop
while labeling:
    # Đọc shop
    result = shop_reader.read_shop()
    
    # Auto-label champions
    for slot in result['slots']:
        if slot['best_match']:
            champion = slot['best_match']['champion']
            add_label(slot['region'], champion)
```

### Workflow 3: Continuous Monitoring

```python
import time

shop_reader = ShopReader(screen_capture)
shop_reader.load_templates()

while True:
    result = shop_reader.read_shop(force_refresh=True)
    
    # Process result
    for slot in result['slots']:
        if slot['best_match']:
            print(f"Slot {slot['index']}: {slot['best_match']['champion']}")
    
    time.sleep(2)
```

## Troubleshooting

### Không tìm thấy templates

**Problem:** `⚠ Không có templates nào được load`

**Solution:**
1. Chạy `python test_shop_reader.py create` để tạo templates
2. Kiểm tra folder `templates/shop_champions/` có chứa file PNG không
3. Đảm bảo shop đang mở trong game

### Không match được champions

**Problem:** Tất cả slots hiển thị "Empty (no match)"

**Solution:**
1. Kiểm tra slot images trong `screenshots/shop_slots/`
2. Đảm bảo templates đúng với champion hiện tại
3. Giảm threshold: `compare_slot_with_templates(slot_img, threshold=0.6)`
4. Tạo thêm templates với các góc độ/scale khác nhau

### Regions không đúng

**Problem:** Slot images không chứa champions

**Solution:**
1. Kiểm tra `screenshots/shop_slots/slot_*.png`
2. Điều chỉnh regions với `update_shop_regions()`
3. Sử dụng tool chỉnh regions (có thể implement sau)

### Performance chậm

**Problem:** Đọc shop quá chậm

**Solution:**
1. Giảm cache interval: `shop_reader.read_interval = 1.0`
2. Giảm số templates (chỉ giữ champions thường gặp)
3. Sử dụng grayscale templates để tăng tốc độ

## Tips

1. **Template Quality:** Cắt template chính xác, không bao gồm background
2. **Multiple Templates:** Tạo nhiều templates cho cùng champion (khác góc/scale)
3. **Naming:** Sử dụng tên champion chuẩn (ví dụ: "ahri", "yasuo", không "Ahri", "Yasuo")
4. **Resolution:** Templates nên 48x48 hoặc 64x64 pixels
5. **Testing:** Test với nhiều shop khác nhau trước khi production

## Integration với Labeling Tool

Shop Reader có thể tích hợp vào labeling tool:

```python
from labeling.shop_reader import ShopReader

class LabelingTool:
    def __init__(self):
        self.shop_reader = ShopReader(screen_capture)
        self.shop_reader.load_templates()
    
    def auto_label_shop(self):
        """Auto-label champions trong shop"""
        result = self.shop_reader.read_shop()
        
        for slot in result['slots']:
            if slot['best_match']:
                champion = slot['best_match']['champion']
                region = slot['region']
                
                # Thêm label
                self.add_label({
                    'bbox': (region['x'], region['y'], region['width'], region['height']),
                    'class': 'champion',
                    'text': champion
                })
```

## Future Enhancements

- [ ] Multi-scale template matching
- [ ] Feature matching fallback khi template matching fail
- [ ] Auto-generate templates từ champion database
- [ ] GUI tool để chỉnh shop regions
- [ ] Support cho nhiều resolutions
- [ ] OCR fallback khi không có template
