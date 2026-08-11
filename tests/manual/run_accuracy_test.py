from tongue import analyze_tongue_image

test_cases = [
    {'file': 'test_normal.jpg', 'expected': '淡红', 'expected_syndrome': 'normal'},
    {'file': 'test_hot.jpg', 'expected': '红', 'expected_syndrome': 'yin_deficiency'},
    {'file': 'test_yin_hot.jpg', 'expected': '绛红', 'expected_syndrome': 'yin_deficiency'},
    {'file': 'test_blood_stasis.jpg', 'expected': '青紫', 'expected_syndrome': 'blood_stasis'},
    {'file': 'test_qi_deficiency.jpg', 'expected': '淡白', 'expected_syndrome': 'yang_deficiency'},
]

correct_color = 0
correct_syndrome = 0
total = len(test_cases)

print("=" * 70)
print("YOLOv8 混合方案舌诊精度测试报告")
print("=" * 70)

for tc in test_cases:
    result = analyze_tongue_image(tc['file'])
    color_ok = result['tongue_color'] == tc['expected']
    syndrome_ok = tc['expected_syndrome'] in result['tcm_syndrome']
    
    if color_ok:
        correct_color += 1
    if syndrome_ok:
        correct_syndrome += 1
    
    status = "✓" if (color_ok and syndrome_ok) else "✗"
    print(f"\n{status} {tc['file']}")
    print(f"  预期舌色：{tc['expected']}, 实际：{result['tongue_color']} {'✓' if color_ok else '✗'}")
    print(f"  预期体质：{tc['expected_syndrome']}, 实际：{result['tcm_syndrome']} {'✓' if syndrome_ok else '✗'}")
    print(f"  AI 分析：{'是' if result.get('is_ai_analysis') else '否'}")
    print(f"  置信度：{result['confidence_score']}")

print("\n" + "=" * 70)
print(f"舌色识别准确率：{correct_color}/{total} = {correct_color/total*100:.1f}%")
print(f"体质辨识准确率：{correct_syndrome}/{total} = {correct_syndrome/total*100:.1f}%")
print("=" * 70)
