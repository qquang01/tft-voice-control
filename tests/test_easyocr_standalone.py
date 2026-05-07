"""
Test script độc lập cho EasyOCR
Không cần ADB/emulator, chỉ test với ảnh có sẵn
"""
import cv2
import numpy as np
import sys
import os

def test_easyocr():
    print("=== Test EasyOCR Standalone ===\n")
    
    # Cài đặt EasyOCR nếu chưa có
    print("1. Kiểm tra EasyOCR...")
    try:
        import easyocr
        print("✓ EasyOCR đã cài đặt\n")
    except ImportError:
        print("✗ Chưa cài đặt EasyOCR")
        print("  Cài đặt: pip install easyocr")
        return
    
    # Khởi tạo EasyOCR reader
    print("2. Khởi tạo EasyOCR reader...")
    try:
        reader = easyocr.Reader(['en', 'vi'], gpu=False)
        print("✓ Đã khởi tạo reader\n")
    except Exception as e:
        print(f"✗ Lỗi khởi tạo: {e}")
        return
    
    # Test với ảnh có sẵn hoặc tạo ảnh test
    print("3. Chuẩn bị ảnh test...")
    
    # Kiểm tra có screenshot có sẵn không
    test_images = [
        'temp_capture.png',
        'test_screenshot.png',
        'test_template.png',
        'screenshots/shop_regions_visualization.png'
    ]
    
    test_img = None
    for img_path in test_images:
        if os.path.exists(img_path):
            test_img = cv2.imread(img_path)
            if test_img is not None:
                print(f"✓ Sử dụng ảnh: {img_path}")
                break
    
    # Nếu không có ảnh, tạo ảnh test đơn giản
    if test_img is None:
        print("⚠ Không tìm thấy ảnh test, tạo ảnh test đơn giản...")
        test_img = np.ones((200, 400, 3), dtype=np.uint8) * 255
        cv2.putText(test_img, "Hello World", (50, 100), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        cv2.putText(test_img, "Test 123", (50, 150), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        print("✓ Đã tạo ảnh test\n")
    
    # Chuyển sang RGB (EasyOCR dùng RGB)
    test_img_rgb = cv2.cvtColor(test_img, cv2.COLOR_BGR2RGB)
    
    # Đọc text
    print("4. Đọc text từ ảnh...")
    try:
        results = reader.readtext(test_img_rgb)
        print(f"✓ Tìm thấy {len(results)} text:\n")
        
        for i, (bbox, text, conf) in enumerate(results):
            print(f"  {i+1}. Text: '{text}'")
            print(f"     Confidence: {conf:.2f}")
            print(f"     Bounding box: {bbox}\n")
    except Exception as e:
        print(f"✗ Lỗi đọc text: {e}")
        return
    
    # Visualize kết quả
    print("5. Lưu kết quả visualized...")
    vis_img = test_img.copy()
    
    for bbox, text, conf in results:
        # bbox là 4 điểm: [(x1,y1), (x2,y2), (x3,y3), (x4,y4)]
        x_coords = [p[0] for p in bbox]
        y_coords = [p[1] for p in bbox]
        x, y = int(min(x_coords)), int(min(y_coords))
        w, h = int(max(x_coords) - x), int(max(y_coords) - y)
        
        # Vẽ bounding box
        cv2.rectangle(vis_img, (x, y), (x+w, y+h), (0, 255, 0), 2)
        # Vẽ label
        cv2.putText(vis_img, f"{text} ({conf:.2f})", (x, y-10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    
    output_path = "easyocr_test_result.png"
    cv2.imwrite(output_path, vis_img)
    print(f"✓ Đã lưu: {output_path}\n")
    
    print("=== Test hoàn tất ===")


if __name__ == "__main__":
    test_easyocr()
