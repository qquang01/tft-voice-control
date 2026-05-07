"""
Run Shop Visualizer GUI

Script này khởi động GUI để hiển thị template images và shop regions.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from labeling.shop_visualizer_gui import ShopVisualizerGUI


if __name__ == "__main__":
    try:
        print("Starting Shop Visualizer GUI...")
        app = ShopVisualizerGUI()
        app.run()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
