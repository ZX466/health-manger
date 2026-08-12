"""Factory for creating configured AI pipelines."""

from typing import Any, Optional

from ai_module.metrics import MetricsCollector
from ai_module.pipeline import AIPipeline
from backends.inference_backends import HybridInferenceBackend, LLMInferenceBackend
from backends.postprocessing_backends import HealthAnalysisPostprocessor
from backends.preprocessing_backends import HealthDataPreprocessor, TextPreprocessor


class AIPipelineFactory:
    """Create pre-configured AI pipelines by type."""

    def create_pipeline(self, pipeline_type: str, llm_call: Optional[Any] = None) -> AIPipeline:
        if pipeline_type == "health_analysis":
            return AIPipeline(
                preprocessor=HealthDataPreprocessor(),
                engine=HybridInferenceBackend(llm_call=llm_call),
                postprocessor=HealthAnalysisPostprocessor(),
                metrics=MetricsCollector(),
            )
        if pipeline_type == "text_analysis":
            return AIPipeline(
                preprocessor=TextPreprocessor(),
                engine=LLMInferenceBackend(llm_call=llm_call),
                postprocessor=HealthAnalysisPostprocessor(),
                metrics=MetricsCollector(),
            )
        raise ValueError(f"未知的流水线类型: {pipeline_type}")
