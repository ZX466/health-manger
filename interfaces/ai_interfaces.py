"""Abstract interfaces for the AI pipeline stages."""

from abc import ABC, abstractmethod
from typing import Any


class DataPreprocessor(ABC):
    """Abstract base for data preprocessors."""

    @abstractmethod
    def preprocess(self, raw_data: dict[str, Any]) -> dict[str, Any]:
        """Transform raw input into a normalized dict ready for inference."""
        ...


class InferenceEngine(ABC):
    """Abstract base for inference engines."""

    @abstractmethod
    async def infer(self, preprocessed: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
        """Run inference and return a result dict."""
        ...


class ResultPostprocessor(ABC):
    """Abstract base for result postprocessors."""

    @abstractmethod
    def postprocess(self, inference_result: dict[str, Any]) -> dict[str, Any]:
        """Structure raw inference output into a standardized format."""
        ...
