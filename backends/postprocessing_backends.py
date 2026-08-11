"""Concrete postprocessing backends."""

from typing import Any, Dict

from interfaces.ai_interfaces import ResultPostprocessor


class HealthAnalysisPostprocessor(ResultPostprocessor):
    """Structure health analysis inference output."""

    def postprocess(self, inference_result: Dict[str, Any]) -> Dict[str, Any]:
        content = inference_result.get("content", {})
        backend_type = inference_result.get("backend_type", "unknown")

        structured = {}

        if isinstance(content, dict):
            structured["rating"] = content.get("health_rating")
            structured["score"] = content.get("health_score")
            structured["bmi_status"] = content.get("bmi_status")

            if backend_type == "hybrid":
                structured["advice"] = content.get("llm_analysis", "")
            else:
                structured["advice"] = content.get("overall_advice", "")

        return {
            "result_type": "health_analysis",
            "structured": structured,
        }


class MetricsExtractor(ResultPostprocessor):
    """Extract performance metrics from inference output."""

    def postprocess(self, inference_result: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "result_type": "metrics",
            "structured": {},
            "metrics": {
                "tokens_used": inference_result.get("tokens_used", 0),
                "latency_ms": inference_result.get("latency_ms", 0.0),
                "backend_type": inference_result.get("backend_type", "unknown"),
            },
        }
