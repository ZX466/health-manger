"""
使用真实测试图片进行舌诊分析验证
"""
import sys
sys.path.insert(0, 'd:/aidevelop/project7')
from tongue import analyze_tongue_image

test_images = [
    ('tests/test_normal.jpg', '正常舌象'),
    ('tests/test_hot.jpg', '热证舌象'),
    ('tests/test_yin_hot.jpg', '阴虚热证'),
    ('tests/test_blood_stasis.jpg', '血瘀舌象'),
    ('tests/test_qi_deficiency.jpg', '气虚舌象'),
]

print('=' * 60)
print('使用真实测试图片进行舌诊分析')
print('=' * 60)

results = {}
for img_path, expected in test_images:
    print(f'\n--- {expected} ---')
    print(f'图片: {img_path}')
    try:
        result = analyze_tongue_image(img_path)
        print(f'  舌色: {result["tongue_color"]}')
        print(f'  苔色: {result["coating_color"]}')
        print(f'  苔厚: {result["coating_thickness"]}')
        print(f'  裂纹: {"有" if result["has_cracks"] else "无"}')
        print(f'  舌形: {result["tongue_shape"]}')
        print(f'  湿润: {result["moisture_level"]}')
        print(f'  证型: {result["tcm_syndrome"]}')
        print(f'  置信度: {result["confidence_score"]}')
        key = f'{result["tongue_color"]}+{result["coating_color"]}'
        if key not in results:
            results[key] = []
        results[key].append(expected)
    except Exception as e:
        print(f'  错误: {e}')

print('\n' + '=' * 60)
print('分析结果汇总')
print('=' * 60)
print(f'不同输出数量: {len(results)}')
for key, names in results.items():
    print(f'  {key}: {len(names)}个 - {", ".join(names)}')

if len(results) > 1:
    print('\n✅ 系统能够区分不同的舌象类型！')
else:
    print('\n⚠️ 所有图片产生相同结果，需要检查')
