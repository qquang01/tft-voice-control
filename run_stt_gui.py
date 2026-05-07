"""
Run TFT GUI with STT and Shop Visualizer integration
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from gui.tft_gui import TFTGUI


def main():
    try:
        print("Đang khởi tạo TFT GUI...")
        app = TFTGUI()
        print("Mở GUI...")
        app.run()
    except Exception as e:
        print(f"Lỗi: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
