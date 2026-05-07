import cv2
import os
import time

templates_dir = "templates/shop_champions"

# Load templates
templates = {}
for filename in os.listdir(templates_dir):
    if filename.endswith('.png'):
        label = os.path.splitext(filename)[0]
        template_path = os.path.join(templates_dir, filename)
        template_img = cv2.imread(template_path)
        if template_img is not None:
            templates[label] = cv2.cvtColor(template_img, cv2.COLOR_BGR2RGB)

print(f"Loaded {len(templates)} templates")

# Test with a sample image (use one of the templates as test image)
test_label = list(templates.keys())[0]
test_img = templates[test_label]

# Benchmark single comparison
num_iterations = 100
start_time = time.time()

for _ in range(num_iterations):
    for label, template_img in templates.items():
        # Resize if sizes don't match
        if test_img.shape != template_img.shape:
            template_img = cv2.resize(template_img, (test_img.shape[1], test_img.shape[0]))
        
        # Template matching
        result = cv2.matchTemplate(test_img, template_img, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

end_time = time.time()

total_time = end_time - start_time
total_comparisons = num_iterations * len(templates)
avg_time_per_comparison = total_time / total_comparisons
avg_time_per_image = total_time / num_iterations

print(f"\nBenchmark results:")
print(f"Total time: {total_time:.3f}s")
print(f"Total comparisons: {total_comparisons}")
print(f"Average time per comparison: {avg_time_per_comparison * 1000:.3f}ms")
print(f"Average time per image (6 regions): {avg_time_per_image * 1000:.3f}ms")
print(f"Comparisons per second: {total_comparisons / total_time:.1f}")
