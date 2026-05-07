"""
Test script cho OCR Reader
"""
import cv2
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.adb_controller import ADBController
from core.screen_capture import ScreenCapture
from ocr.ocr_reader import OCRReader, TFTUIReader


def test_ocr():
    print("=== Test OCR Reader ===\n")
    
    # Khởi tạo
    print("1. Khởi tạo controller...")
    try:
        adb = ADBController()
        capture = ScreenCapture(adb)
        ocr = OCRReader(capture, use_easyocr=True)
        ui_reader = TFTUIReader(ocr)
        print("✓ Đã khởi tạo\n")
    except Exception as e:
        print(f"✗ Lỗi: {e}")
        return
    
    # Kết nối
    print("2. Kết nối...")
    if not adb.connect():
        print("✗ Không thể kết nối")
        return
    print("✓ Đã kết nối\n")
    
    # Chụp màn hình
    print("3. Chụp màn hình...")
    img = capture.capture_to_cv2()
    if img is None:
        print("✗ Chụp thất bại")
        return
    print(f"✓ Kích thước: {img.shape}\n")
    
    # Đọc text toàn màn hình
    print("4. Đọc text toàn màn hình...")
    results = ocr.read_text()
    print(f"Tìm thấy {len(results)} text:")
    for i, result in enumerate(results[:10]):  # Hiển thị 10 kết quả đầu
        print(f"  {i+1}. '{result['text']}' tại {result['bbox']} (conf: {result['conf']:.2f})")
    print()
    
    # Tìm text cụ thể
    print("5. Tìm text 'Gold'...")
    pos = ocr.find_text("Gold")
    if pos:
        print(f"✓ Tìm thấy tại: {pos}\n")
    else:
        print("✗ Không tìm thấy\n")
    
    # Đọc số
    print("6. Đọc các số từ màn hình...")
    numbers = ocr.read_numbers()
    print(f"Tìm thấy các số: {numbers}\n")
    
    # Test TFT UI Reader
    print("7. Đọc gold từ UI...")
    gold = ui_reader.read_gold()
    if gold is not None:
        print(f"✓ Gold: {gold}\n")
    else:
        print("✗ Không đọc được gold\n")
    
    # Lưu screenshot với text boxes
    print("8. Lưu screenshot với text boxes...")
    img_annotated = img.copy()
    for result in results:
        x, y, w, h = result['bbox']
        cv2.rectangle(img_annotated, (x, y), (x+w, y+h), (0, 255, 0), 2)
        cv2.putText(img_annotated, result['text'], (x, y-10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
    
    cv2.imwrite("ocr_annotated.png", cv2.cvtColor(img_annotated, cv2.COLOR_RGB2BGR))
    print("✓ Đã lưu: ocr_annotated.png\n")
    
    # Ngắt kết nối
    adb.disconnect()
    print("=== Test hoàn tất ===")


if __name__ == "__main__":
    test_ocr()
