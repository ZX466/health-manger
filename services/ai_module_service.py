"""Service layer for the AI module pipeline."""

from typing import Any, Dict

from sqlalchemy import select
from sqlalchemy.orm import Session

import models
from ai_module.factory import AIPipelineFactory
from ai_module.pipeline import AIPipelineInput
from services.llm_service import call_llm  # noqa: F401 - re-exported for test patching

_factory = AIPipelineFactory()


class AIModuleService:
    """Orchestrate AI pipeline runs with persistence."""

    def __init__(self, db: Session) -> None:
        self._db = db

    async def analyze_health_data(
        self,
        user_id: int,
        request_content: str,
        analysis_type: str = "健康咨询",
    ) -> Dict[str, Any]:
        # 传入模块全局 call_llm（调用时解析，可被 patch("services.ai_module_service.call_llm") 拦截）
        pipeline = _factory.create_pipeline("health_analysis", llm_call=call_llm)
        input_data = AIPipelineInput(
            input_type="health_data",
            data={"request": request_content},
            config={},
        )
        output = await pipeline.run(input_data)
        return {
            "analysis_type": analysis_type,
            "result": output.structured,
            "metrics": output.metrics,
        }

    def get_metrics_report(self) -> Dict[str, Any]:
        metrics = self._db.execute(select(models.AIMetric)).scalars().all()
        total = len(metrics)
        successes = sum(1 for m in metrics if m.success)
        failures = total - successes
        latencies = [m.latency_ms for m in metrics if m.latency_ms is not None]
        tokens = [m.tokens_used for m in metrics if m.tokens_used is not None]
        return {
            "total_requests": total,
            "successful_requests": successes,
            "failed_requests": failures,
            "success_rate": successes / total if total > 0 else 0.0,
            "avg_latency_ms": round(sum(latencies) / len(latencies), 2) if latencies else 0.0,
            "total_tokens": sum(tokens),
        }
