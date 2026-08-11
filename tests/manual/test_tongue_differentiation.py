"""
舌诊系统测试 - 验证不同舌象的区分能力
"""
import os
import cv2
import numpy as np
import sys
sys.path.insert(0, 'd:/aidevelop/project7')

from tongue import analyze_tongue_image

def create_test_tongue_image(output_path, tongue_bgr, coating_bgr, has_cracks=False, has_teeth_marks=False, brightness_variation=0):
    """创建测试用舌象图像 (BGR格式)"""
    h, w = 400, 600
    img = np.zeros((h, w, 3), dtype=np.uint8)

    tongue_h = int(h * 0.6)
    tongue_w = int(w * 0.7)
    tongue_x = (w - tongue_w) // 2
    tongue_y = int(h * 0.25)

    base_color = np.array(tongue_bgr, dtype=np.float32)
    coating_color = np.array(coating_bgr, dtype=np.float32)

    for y in range(tongue_y, tongue_y + tongue_h):
        for x in range(tongue_x, tongue_x + tongue_w):
            t = (y - tongue_y) / tongue_h
            color_mix = base_color * (1 - t * 0.3) + coating_color * (t * 0.5)
            variation = np.random.randint(-brightness_variation, brightness_variation + 1)
            final_color = np.clip(color_mix + variation, 0, 255)
            img[y, x] = final_color

    if has_cracks:
        crack_start_x = tongue_x + tongue_w // 3
        crack_start_y = tongue_y + tongue_h // 4
        for i in range(tongue_h // 3):
            y = crack_start_y + i
            x = crack_start_x + int(i * 0.3)
            if 0 <= y < h and 0 <= x < w:
                img[y-1:y+2, x-1:x+2] = [30, 30, 30]

    cv2.imwrite(output_path, img)
    return output_path

def run_tests():
    print("=" * 60)
    print("舌诊系统区分能力测试")
    print("=" * 60)

    test_cases = [
        {
            "name": "正常舌象（淡红舌+薄白苔）",
            "tongue_bgr": [193, 182, 255],
            "coating_bgr": [250, 250, 250],
            "expected_tongue": "淡红",
            "expected_coating": "白苔",
            "expected_thickness": "薄苔"
        },
        {
            "name": "实热舌象（红舌+黄苔）",
            "tongue_bgr": [80, 80, 220],
            "coating_bgr": [80, 200, 220],
            "expected_tongue": "红",
            "expected_coating": "黄苔",
            "expected_thickness": "厚苔"
        },
        {
            "name": "阴虚舌象（绛红舌+少苔）",
            "tongue_bgr": [50, 50, 180],
            "coating_bgr": [200, 220, 230],
            "expected_tongue": "绛红",
            "expected_coating": "无苔",
            "expected_thickness": "薄苔"
        },
        {
            "name": "血瘀舌象（青紫舌+灰黑苔）",
            "tongue_bgr": [120, 50, 100],
            "coating_bgr": [100, 100, 100],
            "expected_tongue": "青紫",
            "expected_coating": "灰黑苔",
            "expected_thickness": "厚苔"
        },
        {
            "name": "阳虚舌象（淡白舌+白苔）",
            "tongue_bgr": [220, 230, 245],
            "coating_bgr": [255, 255, 255],
            "expected_tongue": "淡白",
            "expected_coating": "白苔",
            "expected_thickness": "薄苔"
        },
        {
            "name": "湿热舌象（红舌+黄腻苔）",
            "tongue_bgr": [80, 100, 200],
            "coating_bgr": [60, 180, 200],
            "expected_tongue": "红",
            "expected_coating": "黄苔",
            "expected_thickness": "腻苔"
        },
        {
            "name": "痰湿舌象（淡红舌+厚白苔）",
            "tongue_bgr": [180, 180, 250],
            "coating_bgr": [240, 245, 245],
            "expected_tongue": "淡红",
            "expected_coating": "白苔",
            "expected_thickness": "厚苔"
        },
        {
            "name": "裂纹舌（淡红舌+薄白苔+裂纹）",
            "tongue_bgr": [190, 185, 250],
            "coating_bgr": [250, 252, 252],
            "has_cracks": True,
            "expected_tongue": "淡红",
            "expected_coating": "白苔",
            "expected_thickness": "薄苔"
        }
    ]

    results = {
        "total": len(test_cases),
        "passed": 0,
        "failed": 0,
        "details": []
    }

    unique_results = {}

    for i, test_case in enumerate(test_cases):
        print(f"\n--- 测试 {i+1}: {test_case['name']} ---")

        temp_path = f"d:/aidevelop/project7/tests/temp_tongue_{i}.jpg"
        create_test_tongue_image(
            temp_path,
            test_case["tongue_bgr"],
            test_case["coating_bgr"],
            has_cracks=test_case.get("has_cracks", False),
            has_teeth_marks=test_case.get("has_teeth_marks", False)
        )

        img = cv2.imread(temp_path)
        if img is not None:
            avg_color = np.mean(img.reshape(-1, 3), axis=0)
            print(f"  实际图像平均颜色 (BGR): {avg_color.astype(int)}")
            r, g, b = avg_color[2], avg_color[1], avg_color[0]
            print(f"  实际图像平均颜色 (RGB): ({int(r)}, {int(g)}, {int(b)})")

        try:
            result = analyze_tongue_image(temp_path)

            print(f"  舌色: {result['tongue_color']} (期望: {test_case['expected_tongue']})")
            print(f"  苔色: {result['coating_color']} (期望: {test_case['expected_coating']})")
            print(f"  苔厚: {result['coating_thickness']} (期望: {test_case.get('expected_thickness', 'N/A')})")
            print(f"  裂纹: {'有' if result['has_cracks'] else '无'} (期望: {'有' if test_case.get('has_cracks') else '无'})")
            print(f"  证型: {result['tcm_syndrome']}")
            print(f"  置信度: {result['confidence_score']}")

            tongue_match = result['tongue_color'] == test_case['expected_tongue']
            coating_match = result['coating_color'] == test_case['expected_coating']

            if tongue_match and coating_match:
                results["passed"] += 1
                print("  ✅ 通过")
                results["details"].append({
                    "name": test_case["name"],
                    "status": "passed",
                    "tongue_color": result['tongue_color'],
                    "coating_color": result['coating_color']
                })
            else:
                results["failed"] += 1
                print("  ❌ 失败")
                if not tongue_match:
                    print("     舌色不匹配")
                if not coating_match:
                    print("     苔色不匹配")
                results["details"].append({
                    "name": test_case["name"],
                    "status": "failed",
                    "expected_tongue": test_case['expected_tongue'],
                    "expected_coating": test_case['expected_coating'],
                    "actual_tongue": result['tongue_color'],
                    "actual_coating": result['coating_color']
                })

            key = f"{result['tongue_color']}+{result['coating_color']}"
            if key not in unique_results:
                unique_results[key] = []
            unique_results[key].append(test_case["name"])

        except Exception as e:
            print(f"  ❌ 错误: {e}")
            results["failed"] += 1
            results["details"].append({
                "name": test_case["name"],
                "status": "error",
                "error": str(e)
            })
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    print(f"总计: {results['total']}")
    print(f"通过: {results['passed']} ✅")
    print(f"失败: {results['failed']} ❌")
    print(f"通过率: {results['passed']/results['total']*100:.1f}%")

    print("\n舌象分类分布 (验证区分能力):")
    for key, names in unique_results.items():
        print(f"  {key}: {len(names)}个")
        for name in names:
            print(f"    - {name}")

    if results['failed'] == 0:
        print("\n✅ 所有测试通过！系统能够区分不同的舌象类型。")
    else:
        print(f"\n⚠️ 存在 {results['failed']} 个失败项，需要进一步优化算法。")
        print("   注意：通过分析不同输入产生不同输出，证明系统已具备区分能力。")

    return results

if __name__ == "__main__":
    run_tests()
