"""Regression tests for blood-pressure scoring.

Bug: the hypotension branch sat after the "normal" branch and was unreachable,
so low pressure (e.g. 110/55, 85/55) was scored as normal (25) or elevated.
"""

from types import SimpleNamespace

from health_rating import _calculate_blood_pressure_score


def _bp(systolic, diastolic):
    return SimpleNamespace(
        blood_pressure_systolic=systolic,
        blood_pressure_diastolic=diastolic,
    )


def test_low_pressure_both_arms_low_is_scored_low():
    # 85/55 -> 低血压，不得判为正常(25) 或 偏高
    score, detail = _calculate_blood_pressure_score(_bp(85, 55))
    assert score == 15, f"85/55 应判偏低(15)，实际 {score} {detail}"


def test_mixed_low_diastolic_is_scored_low():
    # 110/55 -> 舒张压低于下限，应判偏低(15) 而非正常(25)
    score, detail = _calculate_blood_pressure_score(_bp(110, 55))
    assert score == 15, f"110/55 应判偏低(15)，实际 {score} {detail}"


def test_mixed_high_systolic_low_diastolic_is_scored_low():
    # 130/55 -> 舒张压低，应判偏低(15) 而非偏高(20)
    score, detail = _calculate_blood_pressure_score(_bp(130, 55))
    assert score == 15, f"130/55 应判偏低(15)，实际 {score} {detail}"


def test_normal_pressure_still_scores_normal():
    score, detail = _calculate_blood_pressure_score(_bp(118, 76))
    assert score == 25, f"118/76 应判正常(25)，实际 {score} {detail}"


def test_hypertension_still_scores_high():
    score, detail = _calculate_blood_pressure_score(_bp(150, 95))
    assert score == 12, f"150/95 应判高血压1级(12)，实际 {score} {detail}"
