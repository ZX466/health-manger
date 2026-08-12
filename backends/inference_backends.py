"""Concrete inference backends."""

from types import SimpleNamespace
from typing import Any, Dict, Optional

from health_rating import calculate_health_rating
from interfaces.ai_interfaces import InferenceEngine
from services.llm_service import LLMConfig, call_llm


class LLMInferenceBackend(InferenceEngine):
    """Inference via external LLM API.

    llm_call 为可选的注入点（默认 None 表示在调用时从模块解析 call_llm），
    既支持上层注入（services.ai_module_service），也兼容对
    backends.inference_backends.call_llm 的测试 patch。
    """

    def __init__(self, llm_call: Optional[Any] = None) -> None:
        self._llm_call = llm_call

    async def infer(self, preprocessed: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        messages = preprocessed.get("messages", [])
        temperature = config.get("temperature", 0.7)
        llm = self._llm_call or call_llm
        content, tokens = await llm(messages, LLMConfig(temperature=temperature))
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

    def __init__(self, llm_call: Optional[Any] = None) -> None:
        self._llm_call = llm_call

    async def infer(self, preprocessed: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        rule_engine = RuleBasedInferenceBackend()
        rule_result = rule_engine.infer(preprocessed, config)

        llm_messages = preprocessed.get("messages", [])
        llm_content = ""
        tokens = 0
        if llm_messages:
            llm = self._llm_call or call_llm
            llm_content, tokens = await llm(llm_messages)

        return {
            "content": {
                "rule_based": rule_result["content"],
                "llm_analysis": llm_content,
            },
            "tokens_used": tokens,
            "backend_type": "hybrid",
        }
