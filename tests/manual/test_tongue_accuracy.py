import cv2
import numpy as np

# 创建测试图像集
test_cases = [
    {'name': 'normal', 'color': (255, 182, 193), 'expected': '淡红'},
    {'name': 'hot', 'color': (255, 68, 68), 'expected': '红'},
    {'name': 'yin_hot', 'color': (204, 0, 0), 'expected': '绛红'},
    {'name': 'blood_stasis', 'color': (128, 0, 128), 'expected': '青紫'},
    {'name': 'qi_deficiency', 'color': (245, 245, 220), 'expected': '淡白'},
]

for tc in test_cases:
    img = np.ones((480, 640, 3), dtype=np.uint8)
    img[:] = tc['color']
    cv2.ellipse(img, (320, 240), (150, 80), 0, 0, 360, tc['color'], -1)
    cv2.imwrite(f"test_{tc['name']}.jpg", img)
    print(f"Created: test_{tc['name']}.jpg")
