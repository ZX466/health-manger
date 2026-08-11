"""Tests for tongue diagnosis data consistency between feature_mapping and tongue_diagnosis."""

import pytest

import tongue.feature_mapping as feature_mapping
import tongue.diagnosis as tongue_diagnosis


@pytest.mark.unit
def test_tongue_colors_match_details():
    """tongue_diagnosis.TONGUE_COLORS is the same object as feature_mapping.TONGUE_COLOR_DETAILS."""
    assert tongue_diagnosis.TONGUE_COLORS is feature_mapping.TONGUE_COLOR_DETAILS


@pytest.mark.unit
def test_coating_colors_match_details():
    """tongue_diagnosis.COATING_COLORS is the same object as feature_mapping.COATING_COLOR_DETAILS."""
    assert tongue_diagnosis.COATING_COLORS is feature_mapping.COATING_COLOR_DETAILS


@pytest.mark.unit
def test_coating_thickness_match_descriptions():
    """tongue_diagnosis.COATING_THICKNESS is the same object as feature_mapping.COATING_THICKNESS_DESCRIPTIONS."""
    assert tongue_diagnosis.COATING_THICKNESS is feature_mapping.COATING_THICKNESS_DESCRIPTIONS


@pytest.mark.unit
def test_tongue_shapes_match_descriptions():
    """tongue_diagnosis.TONGUE_SHAPES is the same object as feature_mapping.TONGUE_SHAPE_DESCRIPTIONS."""
    assert tongue_diagnosis.TONGUE_SHAPES is feature_mapping.TONGUE_SHAPE_DESCRIPTIONS


@pytest.mark.unit
def test_moisture_levels_match_descriptions():
    """tongue_diagnosis.MOISTURE_LEVELS is the same object as feature_mapping.MOISTURE_LEVEL_DESCRIPTIONS."""
    assert tongue_diagnosis.MOISTURE_LEVELS is feature_mapping.MOISTURE_LEVEL_DESCRIPTIONS


@pytest.mark.unit
def test_tcm_syndromes_match():
    """tongue_diagnosis.TCM_SYNDROMES is the same object as feature_mapping.TCM_SYNDROMES."""
    assert tongue_diagnosis.TCM_SYNDROMES is feature_mapping.TCM_SYNDROMES


@pytest.mark.unit
def test_feature_mapping_has_all_tongue_colors():
    """All tongue color keys from the index map have detail entries."""
    for key in feature_mapping.TONGUE_COLOR_MAP["cn"].values():
        assert key in feature_mapping.TONGUE_COLOR_DETAILS, f"Missing detail for tongue color: {key}"


@pytest.mark.unit
def test_feature_mapping_has_all_coating_colors():
    """All coating color keys from the index map have detail entries."""
    for key in feature_mapping.COATING_COLOR_MAP["cn"].values():
        assert key in feature_mapping.COATING_COLOR_DETAILS, f"Missing detail for coating color: {key}"


@pytest.mark.unit
def test_feature_mapping_has_all_thickness():
    """All coating thickness keys from the index map have description entries."""
    for key in feature_mapping.COATING_THICKNESS_MAP["cn"].values():
        assert key in feature_mapping.COATING_THICKNESS_DESCRIPTIONS, f"Missing description for thickness: {key}"
