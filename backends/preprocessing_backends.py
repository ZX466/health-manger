"""Concrete preprocessing backends."""

import re
from typing import Any, Dict

from interfaces.ai_interfaces import DataPreprocessor
from services.health_service import calculate_bmi


class HealthDataPreprocessor(DataPreprocessor):
    """Preprocess and validate health record data."""

    BP_SYSTOLIC_MAX = 250
    BP_DIASTOLIC_MAX = 180
    HEART_RATE_MAX = 250

    def preprocess(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        self._validate(raw_data)
        result = dict(raw_data)
        height = result.get("height")
        weight = result.get("weight")
        result["bmi"] = self._calc_bmi(height, weight)
        return result

    def _validate(self, data: Dict[str, Any]) -> None:
        sys_bp = data.get("blood_pressure_systolic")
        dia_bp = data.get("blood_pressure_diastolic")
        if sys_bp is not None and sys_bp > self.BP_SYSTOLIC_MAX:
            raise ValueError("血压数值超出合理范围")
        if dia_bp is not None and dia_bp > self.BP_DIASTOLIC_MAX:
            raise ValueError("血压数值超出合理范围")
        hr = data.get("heart_rate")
        if hr is not None and hr > self.HEART_RATE_MAX:
            raise ValueError("心率数值超出合理范围")

    @staticmethod
    def _calc_bmi(height, weight):
        if not height or not weight or height <= 0:
            return None
        return calculate_bmi(height, weight)


class TextPreprocessor(DataPreprocessor):
    """Sanitize and truncate text input for LLM calls."""

    MAX_LENGTH = 2000
    INJECTION_PATTERNS = [
        re.compile(r"ignore\s+all\s+previous\s+instructions", re.IGNORECASE),
        re.compile(r"system\s*prompt", re.IGNORECASE),
        re.compile(r"you\s+are\s+now", re.IGNORECASE),
    ]

    def preprocess(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        result = dict(raw_data)
        text = result.get("text", "")
        text = self._sanitize(text)
        text = self._truncate(text)
        result["text"] = text
        return result

    def _sanitize(self, text: str) -> str:
        for pattern in self.INJECTION_PATTERNS:
            text = pattern.sub("[已过滤]", text)
        return text

    def _truncate(self, text: str) -> str:
        if len(text) > self.MAX_LENGTH:
            return text[:self.MAX_LENGTH]
        return text
