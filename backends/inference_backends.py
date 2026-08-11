"""Concrete inference backends."""

from typing import Any, Dict
from types import SimpleNamespace

from interfaces.ai_interfaces import InferenceEngine
from services.llm_service import call_llm
from health_rating import calculate_health_rating


class LLMInferenceBackend(InferenceEngine):
    """Inference via external LLM API."""

    async def infer(self, preprocessed: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        messages = preprocessed.get("messages", [])
        temperature = config.get("temperature", 0.7)
        content, tokens = await call_llm(messages, temperature=temperature)
        return {
            "content": content,
            "tokens_used": tokens,
            "backend_type": "llm",
        }


class RuleBasedInferenceBackend(InferenceEngine):
    """Deterministic rule-based health inference using canonical health_rating module."""

    def infer(self, preprocessed: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        record = SimpleNamespace(
            height=preprocessed.get("height"),
            weight=preprocessed.get("weight"),
            bmi=preprocessed.get("bmi"),
            blood_pressure_systolic=preprocessed.get("blood_pressure_systolic"),
            blood_pressure_diastolic=preprocessed.get("blood_pressure_diastolic"),
            heart_rate=preprocessed.get("heart_rate"),
            temperature=preprocessed.get("temperature"),
        )
        rating, score, detail = calculate_health_rating(record)
        return {
            "content": {
                "health_rating": rating,
                "health_score": score,
                "detail": detail,
            },
            "tokens_used": 0,
            "backend_type": "rule_based",
        }


class HybridInferenceBackend(InferenceEngine):
    """Combine rule-based scoring with LLM advice."""

    async def infer(self, preprocessed: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        rule_engine = RuleBasedInferenceBackend()
        rule_result = rule_engine.infer(preprocessed, config)

        llm_messages = preprocessed.get("messages", [])
        llm_content = ""
        tokens = 0
        if llm_messages:
            llm_content, tokens = await call_llm(llm_messages)

        return {
            "content": {
                "rule_based": rule_result["content"],
                "llm_analysis": llm_content,
            },
            "tokens_used": tokens,
            "backend_type": "hybrid",
        }
