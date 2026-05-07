import cv2
import os

# Load the screenshot
screenshot_path = "screenshots/shopimagescaned/screenshot_20260507_200120.png"
img = cv2.imread(screenshot_path)

if img is None:
    print(f"Failed to load image: {screenshot_path}")
    exit(1)

img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

# Slot configuration (current defaults from shop_visualizer.py)
slot_width = 32
slot_height = 32
slot_spacing = 135
slot_start_x = 200
slot_start_y = 50
slot_count = 5

# Shop state box configuration
shop_state_x = 880
shop_state_y = 500
shop_state_width = 40
shop_state_height = 20

# Create output directory
output_dir = "extracted_regions"
os.makedirs(output_dir, exist_ok=True)

# Extract champion slots
for i in range(slot_count):
    x = slot_start_x + i * (slot_width + slot_spacing)
    y = slot_start_y
    
    # Extract region
    region_img = img_rgb[y:y+slot_height, x:x+slot_width]
    
    # Save
    output_path = os.path.join(output_dir, f"champion_{i}.png")
    cv2.imwrite(output_path, cv2.cvtColor(region_img, cv2.COLOR_RGB2BGR))
    print(f"Saved champion_{i} to {output_path}")

# Extract shop state box
region_img = img_rgb[shop_state_y:shop_state_y+shop_state_height, shop_state_x:shop_state_x+shop_state_width]
output_path = os.path.join(output_dir, "shop_state.png")
cv2.imwrite(output_path, cv2.cvtColor(region_img, cv2.COLOR_RGB2BGR))
print(f"Saved shop_state to {output_path}")

print(f"\nExtracted {slot_count + 1} regions to {output_dir}/")
