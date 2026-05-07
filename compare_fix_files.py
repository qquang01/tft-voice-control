import cv2
import os

templates_dir = "templates/shop_champions"

# Load all templates
templates = {}
for filename in os.listdir(templates_dir):
    if filename.endswith('.png'):
        label = os.path.splitext(filename)[0]
        template_path = os.path.join(templates_dir, filename)
        template_img = cv2.imread(template_path)
        if template_img is not None:
            templates[label] = cv2.cvtColor(template_img, cv2.COLOR_BGR2RGB)

# Compare fix0 files with original files
print("=" * 80)
print("COMPARISON: fix0 files vs original files")
print("=" * 80)

fix0_files = [f for f in templates.keys() if f.startswith('fix0')]

for fix0_label in fix0_files:
    original_label = fix0_label.replace('fix0', '')
    
    if original_label in templates:
        fix0_img = templates[fix0_label]
        original_img = templates[original_label]
        
        # Resize if sizes don't match
        if fix0_img.shape != original_img.shape:
            original_img = cv2.resize(original_img, (fix0_img.shape[1], fix0_img.shape[0]))
        
        # Template matching
        result = cv2.matchTemplate(fix0_img, original_img, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        print(f"{fix0_label} vs {original_label}:")
        print(f"  Match score: {max_val:.4f}")
        print(f"  Fix0 size: {fix0_img.shape}")
        print(f"  Original size: {templates[original_label].shape}")
        print(f"  Resized: {fix0_img.shape != templates[original_label].shape}")
        print()
    else:
        print(f"{fix0_label}: No original file found ({original_label})")
        print()

print("=" * 80)
print(f"Total fix0 files: {len(fix0_files)}")
print("=" * 80)
