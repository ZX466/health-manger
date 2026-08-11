"""AI pipeline orchestration."""

import time
from dataclasses import dataclass, field
from typing import Any, Dict

from interfaces.ai_interfaces import DataPreprocessor, InferenceEngine, ResultPostprocessor
from ai_module.metrics import MetricsCollector
from ai_module.exceptions import PreprocessingError, InferenceError, PostprocessingError


@dataclass
class AIPipelineInput:
    input_type: str
    data: Dict[str, Any]
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AIPipelineOutput:
    result_type: str
    structured: Dict[str, Any]
    metrics: Dict[str, Any]


class AIPipeline:
    """Orchestrate preprocess -> infer -> postprocess."""

    def __init__(
        self,
        preprocessor: DataPreprocessor,
        engine: InferenceEngine,
        postprocessor: ResultPostprocessor,
        metrics: MetricsCollector,
    ) -> None:
        self._preprocessor = preprocessor
        self._engine = engine
        self._postprocessor = postprocessor
        self._metrics = metrics

    async def run(self, input_data: AIPipelineInput) -> AIPipelineOutput:
        start = time.perf_counter()

        try:
            processed = self._preprocessor.preprocess(input_data.data)
        except Exception as exc:
            self._metrics.record_failure(type(exc).__name__)
            raise PreprocessingError(str(exc)) from exc

        try:
            inference_result = await self._engine.infer(processed, input_data.config)
        except Exception as exc:
            self._metrics.record_failure(type(exc).__name__)
            raise InferenceError(str(exc)) from exc

        try:
            post_result = self._postprocessor.postprocess(inference_result)
        except Exception as exc:
            self._metrics.record_failure(type(exc).__name__)
            raise PostprocessingError(str(exc)) from exc

        elapsed_ms = (time.perf_counter() - start) * 1000
        self._metrics.record_success()
        self._metrics.record_latency(elapsed_ms)
        tokens = inference_result.get("tokens_used", 0)
        if tokens:
            self._metrics.record_tokens(tokens)

        return AIPipelineOutput(
            result_type=post_result.get("result_type", "unknown"),
            structured=post_result.get("structured", {}),
            metrics=self._metrics.get_snapshot(),
        )
