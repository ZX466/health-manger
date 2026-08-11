"""Tests for medical threshold constant relationships."""

import pytest

import constants


@pytest.mark.unit
def test_bmi_threshold_ordering():
    """BMI thresholds must be in ascending order."""
    assert constants.BMI_THIN < constants.BMI_UNDERWEIGHT < constants.BMI_NORMAL_UPPER < constants.BMI_OVERWEIGHT_UPPER


@pytest.mark.unit
def test_bmi_chinese_standard_values():
    """BMI thresholds match Chinese clinical standard."""
    assert constants.BMI_UNDERWEIGHT == 18.5
    assert constants.BMI_NORMAL_UPPER == 24.0
    assert constants.BMI_OVERWEIGHT_UPPER == 28.0


@pytest.mark.unit
def test_bp_threshold_ordering():
    """Blood pressure thresholds must be in ascending order for each arm."""
    assert constants.BP_SYSTOLIC_LOW < constants.BP_SYSTOLIC_NORMAL < constants.BP_SYSTOLIC_ELEVATED < constants.BP_SYSTOLIC_HIGH
    assert constants.BP_DIASTOLIC_LOW < constants.BP_DIASTOLIC_NORMAL < constants.BP_DIASTOLIC_ELEVATED < constants.BP_DIASTOLIC_HIGH


@pytest.mark.unit
def test_bp_chinese_standard_values():
    """Blood pressure thresholds match Chinese clinical standard."""
    assert constants.BP_SYSTOLIC_LOW == 90
    assert constants.BP_SYSTOLIC_NORMAL == 120
    assert constants.BP_SYSTOLIC_ELEVATED == 140
    assert constants.BP_SYSTOLIC_HIGH == 160
    assert constants.BP_DIASTOLIC_LOW == 60
    assert constants.BP_DIASTOLIC_NORMAL == 80
    assert constants.BP_DIASTOLIC_ELEVATED == 90
    assert constants.BP_DIASTOLIC_HIGH == 100


@pytest.mark.unit
def test_hr_threshold_ordering():
    """Heart rate thresholds must be in ascending order."""
    assert constants.HR_EXTREME_LOW < constants.HR_VERY_LOW < constants.HR_LOW < constants.HR_HIGH < constants.HR_VERY_HIGH < constants.HR_EXTREME_HIGH


@pytest.mark.unit
def test_hr_standard_values():
    """Heart rate normal range matches clinical standard (60-100)."""
    assert constants.HR_LOW == 60
    assert constants.HR_HIGH == 100


@pytest.mark.unit
def test_temp_threshold_ordering():
    """Temperature thresholds must be in ascending order."""
    assert constants.TEMP_LOW < constants.TEMP_NORMAL_LOW < constants.TEMP_NORMAL_HIGH < constants.TEMP_FEVER < constants.TEMP_HIGH_FEVER


@pytest.mark.unit
def test_temp_chinese_standard_values():
    """Temperature thresholds match Chinese clinical standard."""
    assert constants.TEMP_NORMAL_HIGH == 37.3
    assert constants.TEMP_FEVER == 37.5
    assert constants.TEMP_HIGH_FEVER == 38.0
    assert constants.TEMP_NORMAL_LOW == 36.0
    assert constants.TEMP_LOW == 35.0
