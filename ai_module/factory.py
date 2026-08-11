"""Factory for creating configured AI pipelines."""

from backends.preprocessing_backends import HealthDataPreprocessor, TextPreprocessor
from backends.inference_backends import LLMInferenceBackend, HybridInferenceBackend
from backends.postprocessing_backends import HealthAnalysisPostprocessor
from ai_module.pipeline import AIPipeline
from ai_module.metrics import MetricsCollector


class AIPipelineFactory:
    """Create pre-configured AI pipelines by type."""

    def create_pipeline(self, pipeline_type: str) -> AIPipeline:
        if pipeline_type == "health_analysis":
            return AIPipeline(
                preprocessor=HealthDataPreprocessor(),
                engine=HybridInferenceBackend(),
                postprocessor=HealthAnalysisPostprocessor(),
                metrics=MetricsCollector(),
            )
        if pipeline_type == "text_analysis":
            return AIPipeline(
                preprocessor=TextPreprocessor(),
                engine=LLMInferenceBackend(),
                postprocessor=HealthAnalysisPostprocessor(),
                metrics=MetricsCollector(),
            )
        raise ValueError(f"未知的流水线类型: {pipeline_type}")
