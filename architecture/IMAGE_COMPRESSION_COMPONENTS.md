# Các Thành Phần Cần Thiết Của Image Comparison

## 1. Tổng quan

Image comparison trong context TFT labeling tool cần các thành phần sau:

```
Input Image → Preprocessing → Feature Extraction → Similarity Metric → Decision
```

## 2. Các thành phần chi tiết

### 2.1 Preprocessing (Xử lý trước)

**Mục đích:** Chuẩn hóa ảnh để so sánh chính xác hơn

```python
import cv2
import numpy as np

class ImagePreprocessor:
    """Preprocessing cho image comparison"""
    
    def __init__(self):
        self.target_size = (640, 480)  # Resize về size cố định
    
    def resize(self, image: np.ndarray, size: Tuple[int, int] = None) -> np.ndarray:
        """Resize ảnh về size cố định"""
        if size is None:
            size = self.target_size
        return cv2.resize(image, size)
    
    def grayscale(self, image: np.ndarray) -> np.ndarray:
        """Chuyển sang grayscale"""
        return cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    
    def normalize(self, image: np.ndarray) -> np.ndarray:
        """Normalize pixel values về [0, 1]"""
        return image.astype(np.float32) / 255.0
    
    def denoise(self, image: np.ndarray) -> np.ndarray:
        """Khử noise"""
        return cv2.fastNlMeansDenoisingColored(image, None, 10, 10, 7, 21)
    
    def enhance_contrast(self, image: np.ndarray) -> np.ndarray:
        """Tăng contrast (CLAHE)"""
        lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        lab = cv2.merge([l, a, b])
        return cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
    
    def pipeline(self, image: np.ndarray) -> np.ndarray:
        """Full preprocessing pipeline"""
        img = self.resize(image)
        img = self.denoise(img)
        img = self.enhance_contrast(img)
        return img
```

**Khi nào cần preprocessing:**
- Template matching: Resize, grayscale
- Feature matching: Denoise, enhance contrast
- Image hashing: Resize nhỏ (32x32 hoặc 64x64)

### 2.2 Template Matching (Khớp mẫu)

**Mục đích:** Tìm template trong ảnh lớn

```python
class TemplateMatcher:
    """Template matching với OpenCV"""
    
    def __init__(self):
        self.methods = {
            'sqdiff': cv2.TM_SQDIFF,
            'sqdiff_normed': cv2.TM_SQDIFF_NORMED,
            'ccorr': cv2.TM_CCORR,
            'ccorr_normed': cv2.TM_CCORR_NORMED,
            'ccoef': cv2.TM_CCOEFF,
            'ccoef_normed': cv2.TM_CCOEFF_NORMED  # Khuyên dùng
        }
    
    def match(self, image: np.ndarray, template: np.ndarray, 
              method: str = 'ccoef_normed',
              threshold: float = 0.8) -> List[Dict]:
        """
        Template matching
        
        Args:
            image: Ảnh lớn cần tìm
            template: Template cần tìm
            method: Phương pháp matching
            threshold: Ngưỡng confidence
            
        Returns:
            List các kết quả: {'bbox': (x,y,w,h), 'confidence': float}
        """
        method_code = self.methods[method]
        result = cv2.matchTemplate(image, template, method_code)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        matches = []
        
        if method in ['sqdiff', 'sqdiff_normed']:
            # Lower is better
            if min_val <= (1.0 - threshold):
                h, w = template.shape[:2]
                matches.append({
                    'bbox': (min_loc[0], min_loc[1], w, h),
                    'confidence': 1.0 - min_val
                })
        else:
            # Higher is better
            if max_val >= threshold:
                h, w = template.shape[:2]
                matches.append({
                    'bbox': (max_loc[0], max_loc[1], w, h),
                    'confidence': max_val
                })
        
        return matches
    
    def multi_scale_match(self, image: np.ndarray, template: np.ndarray,
                          scales: List[float] = [0.8, 0.9, 1.0, 1.1, 1.2],
                          threshold: float = 0.8) -> List[Dict]:
        """
        Multi-scale template matching (khi template có thể khác scale)
        """
        all_matches = []
        
        for scale in scales:
            # Resize template
            h, w = template.shape[:2]
            new_w = int(w * scale)
            new_h = int(h * scale)
            resized_template = cv2.resize(template, (new_w, new_h))
            
            # Match
            matches = self.match(image, resized_template, threshold=threshold)
            for match in matches:
                match['scale'] = scale
                all_matches.append(match)
        
        # Non-maximum suppression
        return self._nms(all_matches)
    
    def _nms(self, matches: List[Dict], iou_threshold: float = 0.5) -> List[Dict]:
        """Non-maximum suppression để loại bỏ trùng lặp"""
        if not matches:
            return []
        
        # Sort by confidence
        matches = sorted(matches, key=lambda x: x['confidence'], reverse=True)
        
        keep = []
        while matches:
            best = matches.pop(0)
            keep.append(best)
            
            # Remove matches with high IoU
            matches = [m for m in matches 
                      if self._iou(best['bbox'], m['bbox']) < iou_threshold]
        
        return keep
    
    def _iou(self, bbox1: Tuple, bbox2: Tuple) -> float:
        """Compute Intersection over Union"""
        x1, y1, w1, h1 = bbox1
        x2, y2, w2, h2 = bbox2
        
        # Intersection
        xi1 = max(x1, x2)
        yi1 = max(y1, y2)
        xi2 = min(x1 + w1, x2 + w2)
        yi2 = min(y1 + h1, y2 + h2)
        
        if xi2 < xi1 or yi2 < yi1:
            return 0.0
        
        inter_area = (xi2 - xi1) * (yi2 - yi1)
        
        # Union
        area1 = w1 * h1
        area2 = w2 * h2
        union_area = area1 + area2 - inter_area
        
        return inter_area / union_area
```

**Ưu điểm:**
- Nhanh (5-10ms)
- Dễ implement
- Hoạt động tốt cho UI tĩnh

**Nhược điểm:**
- Không scale-invariant (cần multi-scale)
- Không rotation-invariant
- Nhạy cảm với illumination changes

### 2.3 Feature Matching (Khớp đặc điểm)

**Mục đích:** Tìm keypoint và descriptors để matching robust hơn

```python
class FeatureMatcher:
    """Feature matching với ORB/SIFT"""
    
    def __init__(self, method: str = 'ORB'):
        self.method = method
        
        if method == 'ORB':
            self.detector = cv2.ORB_create(nfeatures=1000)
            self.matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
        elif method == 'SIFT':
            self.detector = cv2.SIFT_create()
            self.matcher = cv2.BFMatcher(cv2.NORM_L2, crossCheck=False)
        elif method == 'AKAZE':
            self.detector = cv2.AKAZE_create()
            self.matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
    
    def detect_and_compute(self, image: np.ndarray) -> Tuple[List, np.ndarray]:
        """Detect keypoints và compute descriptors"""
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        keypoints, descriptors = self.detector.detectAndCompute(gray, None)
        return keypoints, descriptors
    
    def match(self, img1: np.ndarray, img2: np.ndarray,
              ratio_threshold: float = 0.75) -> Tuple[List, float]:
        """
        Match features giữa 2 ảnh
        
        Returns:
            (good_matches, match_ratio)
        """
        kp1, des1 = self.detect_and_compute(img1)
        kp2, des2 = self.detect_and_compute(img2)
        
        if des1 is None or des2 is None:
            return [], 0.0
        
        # Match descriptors
        if self.method == 'ORB':
            matches = self.matcher.knnMatch(des1, des2, k=2)
        else:
            matches = self.matcher.knnMatch(des1, des2, k=2)
        
        # Lowe's ratio test
        good_matches = []
        for match_pair in matches:
            if len(match_pair) == 2:
                m, n = match_pair
                if m.distance < ratio_threshold * n.distance:
                    good_matches.append(m)
        
        match_ratio = len(good_matches) / min(len(kp1), len(kp2)) if kp1 and kp2 else 0
        
        return good_matches, match_ratio
    
    def find_homography(self, img1: np.ndarray, img2: np.ndarray,
                        min_matches: int = 10) -> Optional[np.ndarray]:
        """
        Tìm homography matrix giữa 2 ảnh
        
        Returns:
            Homography matrix hoặc None
        """
        kp1, des1 = self.detect_and_compute(img1)
        kp2, des2 = self.detect_and_compute(img2)
        
        if des1 is None or des2 is None:
            return None
        
        matches = self.matcher.knnMatch(des1, des2, k=2)
        good_matches = []
        for m, n in matches:
            if m.distance < 0.75 * n.distance:
                good_matches.append(m)
        
        if len(good_matches) < min_matches:
            return None
        
        src_pts = np.float32([kp1[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
        dst_pts = np.float32([kp2[m.trainIdx].pt for m in good_matches]).reshape(-1, +1, 2)
        
        H, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
        return H
```

**Ưu điểm:**
- Scale-invariant
- Rotation-invariant
- Robust với illumination changes

**Nhược điểm:**
- Chậm hơn template matching (20-50ms)
- Cần nhiều keypoints để hoạt động tốt
- Không hoạt động tốt với UI đơn giản ( ít texture)

### 2.4 Image Hashing (Băm ảnh)

**Mục đích:** Tạo fingerprint nhanh để detect thay đổi

```python
class ImageHasher:
    """Perceptual hashing cho image comparison"""
    
    def __init__(self):
        self.hash_size = 8
    
    def average_hash(self, image: np.ndarray) -> str:
        """Average Hash (aHash) - đơn giản nhất"""
        # Resize nhỏ
        resized = cv2.resize(image, (self.hash_size, self.hash_size))
        gray = cv2.cvtColor(resized, cv2.COLOR_RGB2GRAY)
        
        # Compute average
        avg = gray.mean()
        
        # Create hash
        hash_str = ''.join(['1' if pixel > avg else '0' for row in gray for pixel in row])
        return hash_str
    
    def perceptual_hash(self, image: np.ndarray) -> str:
        """Perceptual Hash (pHash) - robust hơn"""
        import imagehash
        from PIL import Image
        
        img = Image.fromarray(image)
        return str(imagehash.phash(img, hash_size=self.hash_size))
    
    def difference_hash(self, image: np.ndarray) -> str:
        """Difference Hash (dHash) - nhanh"""
        resized = cv2.resize(image, (self.hash_size + 1, self.hash_size))
        gray = cv2.cvtColor(resized, cv2.COLOR_RGB2GRAY)
        
        hash_str = ''
        for row in range(self.hash_size):
            for col in range(self.hash_size):
                if gray[row, col] > gray[row, col + 1]:
                    hash_str += '1'
                else:
                    hash_str += '0'
        
        return hash_str
    
    def hamming_distance(self, hash1: str, hash2: str) -> int:
        """Compute Hamming distance giữa 2 hashes"""
        if len(hash1) != len(hash2):
            raise ValueError("Hashes must have same length")
        
        return sum(c1 != c2 for c1, c2 in zip(hash1, hash2))
    
    def is_similar(self, image1: np.ndarray, image2: np.ndarray,
                   method: str = 'perceptual',
                   threshold: int = 5) -> bool:
        """
        Kiểm tra 2 ảnh có similar không
        
        Args:
            method: 'average', 'perceptual', 'difference'
            threshold: Hamming distance threshold
        """
        if method == 'average':
            h1 = self.average_hash(image1)
            h2 = self.average_hash(image2)
        elif method == 'perceptual':
            h1 = self.perceptual_hash(image1)
            h2 = self.perceptual(image2)
        elif method == 'difference':
            h1 = self.difference_hash(image1)
            h2 = self.difference_hash(image2)
        else:
            raise ValueError(f"Unknown method: {method}")
        
        distance = self.hamming_distance(h1, h2)
        return distance <= threshold
```

**Ưu điểm:**
- Rất nhanh (<1ms)
- Fixed-size hash (64 bits)
- Tốt cho detect thay đổi lớn

**Nhược điểm:**
- Không thể locate object
- Hash collision có thể xảy ra
- Không robust với scale/rotation

### 2.5 Similarity Metrics (Độ đo tương đồng)

```python
class SimilarityMetrics:
    """Các metrics để đo độ tương đồng ảnh"""
    
    @staticmethod
    def mse(image1: np.ndarray, image2: np.ndarray) -> float:
        """Mean Squared Error"""
        return np.mean((image1.astype(np.float32) - image2.astype(np.float32)) ** 2)
    
    @staticmethod
    def ssim(image1: np.ndarray, image2: np.ndarray) -> float:
        """Structural Similarity Index"""
        from skimage.metrics import structural_similarity as ssim
        
        # Convert to grayscale
        gray1 = cv2.cvtColor(image1, cv2.COLOR_RGB2GRAY)
        gray2 = cv2.cvtColor(image2, cv2.COLOR_RGB2GRAY)
        
        return ssim(gray1, gray2, multichannel=False)
    
    @staticmethod
    def psnr(image1: np.ndarray, image2: np.ndarray) -> float:
        """Peak Signal-to-Noise Ratio"""
        mse_val = SimilarityMetrics.mse(image1, image2)
        if mse_val == 0:
            return float('inf')
        
        max_pixel = 255.0
        return 20 * np.log10(max_pixel / np.sqrt(mse_val))
    
    @staticmethod
    def histogram_correlation(image1: np.ndarray, image2: np.ndarray) -> float:
        """Histogram correlation"""
        hist1 = cv2.calcHist([image1], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
        hist2 = cv2.calcHist([image2], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
        
        hist1 = cv2.normalize(hist1, hist1).flatten()
        hist2 = cv2.normalize(hist2, hist2).flatten()
        
        return cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
```

### 2.6 Pixel-based Comparison

```python
class PixelComparator:
    """So sánh dựa trên pixel patterns"""
    
    def color_matching(self, image: np.ndarray, 
                      target_color: Tuple[int, int, int],
                      tolerance: int = 30) -> np.ndarray:
        """Tìm pixel khớp màu"""
        r, g, b = target_color
        lower = np.array([max(0, r - tolerance), max(0, g - tolerance), max(0, b - tolerance)])
        upper = np.array([min(255, r + tolerance), min(255, g + tolerance), min(255, b + tolerance)])
        
        mask = cv2.inRange(image, lower, upper)
        return mask
    
    def edge_detection(self, image: np.ndarray) -> np.ndarray:
        """Detect edges (Canny)"""
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        return edges
    
    def edge_similarity(self, image1: np.ndarray, image2: np.ndarray) -> float:
        """So sánh edge patterns"""
        edges1 = self.edge_detection(image1)
        edges2 = self.edge_detection(image2)
        
        # Compute overlap
        overlap = cv2.bitwise_and(edges1, edges2)
        overlap_count = np.sum(overlap > 0)
        
        total_edges = np.sum(edges1 > 0) + np.sum(edges2 > 0)
        
        if total_edges == 0:
            return 1.0
        
        return 2.0 * overlap_count / total_edges
```

## 3. Chiến lược cho TFT Labeling Tool

### 3.1 Decision Tree

```
┌─────────────────────────────────────────┐
│  Element type?                           │
└────────────┬────────────────────────────┘
             │
   ┌─────────┼─────────┐
   │         │         │
   ▼         ▼         ▼
Static UI  Dynamic   Champion
(buttons,  text      icons
icons)     (gold,    │
   │       health)   │
   │         │         │
   ▼         ▼         ▼
Template   OCR      Template
Matching  (EasyOCR) Matching
+ Hash     + Hash    + Hash
```

### 3.2 Pipeline đề xuất

```python
class TFTImageComparator:
    """Image comparator chuyên dụng cho TFT"""
    
    def __init__(self):
        self.preprocessor = ImagePreprocessor()
        self.template_matcher = TemplateMatcher()
        self.feature_matcher = FeatureMatcher(method='ORB')
        self.hasher = ImageHasher()
        self.metrics = SimilarityMetrics()
        self.pixel_comparator = PixelComparator()
        
        # Cache
        self.hash_cache = {}
        self.template_cache = {}
    
    def compare_static_ui(self, image: np.ndarray, 
                         template: np.ndarray) -> Dict:
        """
        So sánh static UI elements (buttons, icons)
        
        Returns:
            Dict với 'method', 'confidence', 'latency'
        """
        start_time = time.time()
        
        # Preprocess
        img_proc = self.preprocessor.resize(image)
        template_proc = self.preprocessor.resize(template)
        
        # Template matching
        matches = self.template_matcher.match(img_proc, template_proc)
        
        latency = time.time() - start_time
        
        if matches:
            return {
                'method': 'template_matching',
                'confidence': matches[0]['confidence'],
                'bbox': matches[0]['bbox'],
                'latency': latency
            }
        else:
            return {
                'method': 'template_matching',
                'confidence': 0.0,
                'bbox': None,
                'latency': latency
            }
    
    def detect_change(self, image1: np.ndarray, 
                     image2: np.ndarray) -> bool:
        """
        Detect nếu ảnh có thay đổi
        
        Returns:
            True nếu có thay đổi đáng kể
        """
        # Sử dụng perceptual hash
        h1 = self.hasher.perceptual_hash(image1)
        h2 = self.hasher.perceptual_hash(image2)
        
        distance = self.hasher.hamming_distance(h1, h2)
        
        # Threshold: 5 bits khác nhau = thay đổi
        return distance > 5
```

## 4. Performance Comparison

| Method | Latency | Accuracy | Use Case |
|--------|---------|----------|----------|
| Template Matching | 5-10ms | High (static UI) | Buttons, icons |
| Feature Matching | 20-50ms | High (complex) | Champions with rotation |
| Image Hashing | <1ms | Medium | Change detection |
| OCR | 50-150ms | Medium (text) | Gold, health, level |
| Pixel Matching | 1-3ms | High (color) | Color-based UI |

## 5. Dependencies

```txt
opencv-python>=4.8.0
numpy>=1.24.0
Pillow>=10.0.0
imagehash>=4.3.0
scikit-image>=0.21.0  # Cho SSIM
```

## 6. Best Practices cho TFT

1. **Cache templates:** Load templates 1 lần, reuse nhiều lần
2. **Multi-scale matching:** TFT UI có thể khác scale giữa devices
3. **Hash-based change detection:** Chỉ re-detect khi ảnh thay đổi
4. **Hybrid approach:** Template matching优先, OCR fallback
5. **Region-based search:** Giới hạn vùng tìm kiếm để tăng tốc
