# Template Matching vs OCR cho Nhận diện Tướng TFT

## Câu hỏi quan trọng

**Tướng có hình ảnh cố định không thay đổi?**

## Đánh giá chi tiết

### Template Matching (So sánh ảnh)

**Ưu điểm:**
- ✅ **Nhanh hơn nhiều** - ~10-30ms vs 50-150ms OCR
- ✅ **Chính xác hơn** cho hình ảnh - không phụ thuộc font/size
- ✅ **Không cần OCR engine** - giảm dependencies
- ✅ **Hoạt động offline hoàn toàn** - không cần download model
- ✅ **Dễ debug** - có thể visualize matches
- ✅ **Ít CPU hơn** - chỉ cần OpenCV

**Nhược điểm:**
- ❌ **Cần template cho mỗi tướng** - phải capture và lưu
- ❌ **Phụ thuộc resolution** - template phải cùng resolution với màn hình
- ❌ **UI thay đổi = phải update** - patch game mới
- ❌ **Không đọc được text** - gold, health, level vẫn cần OCR
- ❌ **Chromatic aberration** - màu có thể thay đổi nhẹ

### OCR (Đọc text)

**Ưu điểm:**
- ✅ **Đọc được text** - gold, health, level, round
- ✅ **Flexible** - không cần template
- ✅ **Có thể đọc bất kỳ text nào** - không chỉ tên tướng

**Nhược điểm:**
- ❌ **Chậm hơn** - 50-150ms
- ❌ **Phụ thuộc font** - font thay đổi = lỗi
- ❌ **Accuracy thấp hơn** cho hình ảnh
- ❌ **Cần OCR engine** - EasyOCR/Tesseract
- ❌ **CPU cao hơn** - đặc biệt với EasyOCR

---

## Đánh giá thực tế cho TFT

### Hình ảnh tướng trong TFT

**Thực tế:**
- ✅ **Hình ảnh champion là cố định** - Riot dùng assets giống nhau
- ✅ **Portrait art không thay đổi** - mỗi tướng có 1 portrait
- ✅ **Icon trong shop là cố định** - nhỏ nhưng nhất quán
- ⚠️ **Có thể có variants** - skin khác nhau (rare)
- ⚠️ **Star level khác nhau** - 1★, 2★, 3★ có icon khác

**Kết luận:** Template Matching là **TỐI Ưu** cho nhận diện tướng

### Khi nào dùng Template Matching

**Dùng cho:**
- ✅ Nhận diện tướng trong shop
- ✅ Nhận diện tướng trên bench
- ✅ Nhận diện tướng trên board
- ✅ Nhận diện item icons
- ✅ Nhận diện trait icons
- ✅ Nhận diện class icons

**KHÔNG dùng cho:**
- ❌ Đọc số (gold, health, level) - dùng OCR
- ❌ Đọc tên tướng nếu không có icon - dùng OCR
- ❌ Đọc round info - dùng OCR

---

## Phương án Hybrid Khuyên dùng

### Architecture đề xuất

```
┌─────────────────────────────────────────┐
│   Screen Capture (50ms)                 │
└─────────────────────────────────────────┘
              │
              ├──► Template Matching (10-30ms)
              │     - Champion detection
              │     - Item detection
              │     - Trait detection
              │
              └──► OCR (50-100ms)
                    - Gold, Health, Level
                    - Round info
                    - Shop prices
```

### Workflow

1. **Chụp màn hình** - 50ms
2. **Template Matching** - 10-30ms (champions, items)
3. **OCR** - 50-100ms (chỉ cho text: gold, health, level)
4. **Total Latency** - ~110-180ms (vẫn tốt)

### Tối ưu

```python
# Chỉ OCR khi cần thiết
if need_gold_info:
    gold = ocr.read_gold()  # 50ms
else:
    gold = cached_gold

# Template matching cho tất cả champions
champions = template_match_all()  # 20ms
```

---

## Implementation Plan

### Phase 1: Template Matching cho Champions

**Bước 1: Capture templates**
```python
# Chụp màn hình shop
capture.capture("shop_screenshot.png")

# Cắt từng slot champion (5 slots)
for i in range(5):
    template = crop_slot(i)
    save_template(f"champion_slot_{i}.png")
```

**Bước 2: Tạo template database**
```
templates/
├── champions/
│   ├── ahri_1star.png
│   ├── ahri_2star.png
│   ├── ahri_3star.png
│   ├── syndra_1star.png
│   └── ...
├── items/
│   ├── infinity_edge.png
│   ├── rabadons.png
│   └── ...
└── traits/
    ├── sorcerer.png
    ├── assassin.png
    └── ...
```

**Bước 3: Template matching module**
```python
class ChampionDetector:
    def __init__(self):
        self.templates = load_templates("templates/champions/")
    
    def detect_in_shop(self, screenshot):
        results = []
        for slot in get_shop_slots():
            slot_img = crop(screenshot, slot)
            for champ_name, template in self.templates.items():
                if match(slot_img, template) > 0.85:
                    results.append(champ_name)
                    break
        return results
```

### Phase 2: OCR cho Text

```python
class TextReader:
    def __init__(self):
        self.ocr = OCRReader()
    
    def read_game_stats(self, screenshot):
        # Chỉ OCR các vùng text
        gold = self.ocr.read_text(region=gold_region)
        health = self.ocr.read_text(region=health_region)
        level = self.ocr.read_text(region=level_region)
        return gold, health, level
```

### Phase 3: Integration

```python
class TFTGameReader:
    def __init__(self):
        self.champion_detector = ChampionDetector()
        self.text_reader = TextReader()
    
    def get_game_state(self):
        screenshot = self.capture.capture()
        
        # Template matching - nhanh
        shop_champions = self.champion_detector.detect_in_shop(screenshot)
        bench_champions = self.champion_detector.detect_on_bench(screenshot)
        
        # OCR - chỉ khi cần
        gold, health, level = self.text_reader.read_game_stats(screenshot)
        
        return {
            'shop': shop_champions,
            'bench': bench_champions,
            'gold': gold,
            'health': health,
            'level': level
        }
```

---

## So sánh Performance

### Pure OCR Approach
```
Screen Capture: 50ms
OCR Champions: 150ms (5 champions × 30ms)
OCR Stats: 50ms
Total: ~250ms
```

### Template Matching Only
```
Screen Capture: 50ms
Template Match: 30ms (5 champions × 6ms)
Stats: Cannot read
Total: ~80ms
```

### Hybrid Approach (Khuyên dùng)
```
Screen Capture: 50ms
Template Match Champions: 30ms
OCR Stats: 50ms
Total: ~130ms
```

---

## Kết luận

### Khuyến nghị: **HYBRID APPROACH**

**Template Matching cho:**
- ✅ Champion detection (shop, bench, board)
- ✅ Item detection
- ✅ Trait/Class detection

**OCR cho:**
- ✅ Gold, Health, Level
- ✅ Round info
- ✅ Shop prices

**Lý do:**
1. Hình ảnh champion là cố định → Template matching tối ưu
2. Template matching nhanh hơn 5-10x
3. OCR chỉ dùng khi cần thiết (text)
4. Total latency vẫn thấp (~130ms)
5. Accuracy cao hơn cho hình ảnh

### Setup Time

- **Template Matching:** 1-2 giờ (capture templates)
- **OCR:** Đã có sẵn
- **Integration:** 2-3 giờ

**Total:** 4-6 giờ cho MVP

### Maintenance

- **Template Matching:** Cần update khi patch game (2-4 tuần/lần)
- **OCR:** Ít thay đổi hơn
- **Hybrid:** Dễ maintain hơn pure OCR

---

## Next Steps

1. ✅ Đánh giá xong
2. ⏳ Tạo ChampionDetector module
3. ⏳ Capture champion templates
4. ⏳ Tạo template database
5. ⏳ Integrate với OCR controller
6. ⏳ Test performance
