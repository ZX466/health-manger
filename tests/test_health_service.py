"""Regression tests for health_service blood-pressure analysis.

Bug: analyze_blood_pressure 无高血压优先判定，混合读数（170/55、85/90）
被低血压分支遮蔽，与已修复的 health_rating/warning_service 不一致。
"""

from services.health_service import analyze_blood_pressure


def test_mixed_severe_hypertension_with_low_diastolic_is_hypertension():
    # 170/55 -> 收缩压达高血压标准(>=140)，不应被低舒张压遮蔽为低血压
    status, _ = analyze_blood_pressure(170, 55)
    assert status == "高血压", f"170/55 应判高血压，实际 {status}"


def test_mixed_hypertension1_diastolic_with_low_systolic_is_hypertension():
    # 85/90 -> 舒张压达高血压标准(>=90)，不应被低收缩压遮蔽为低血压
    status, _ = analyze_blood_pressure(85, 90)
    assert status == "高血压", f"85/90 应判高血压，实际 {status}"


def test_low_pressure_is_low():
    status, _ = analyze_blood_pressure(85, 55)
    assert status == "低血压"


def test_normal_pressure_is_normal():
    status, _ = analyze_blood_pressure(118, 76)
    assert status == "正常"


def test_elevated_pressure_is_elevated():
    status, _ = analyze_blood_pressure(128, 82)
    assert status == "偏高"


def test_boundary_mixed_low_diastolic_is_low():
    # 130/55、110/55 -> 收缩压未达高血压标准，舒张压低，应判低血压
    assert analyze_blood_pressure(130, 55)[0] == "低血压"
    assert analyze_blood_pressure(110, 55)[0] == "低血压"


def test_boundary_hypertension1_is_hypertension():
    # 150/95 -> 收缩压/舒张压均达高血压标准
    assert analyze_blood_pressure(150, 95)[0] == "高血压"
