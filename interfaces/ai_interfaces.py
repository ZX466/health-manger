"""Abstract interfaces for the AI pipeline stages."""

from abc import ABC, abstractmethod
from typing import Any, Dict


class DataPreprocessor(ABC):
    """Abstract base for data preprocessors."""

    @abstractmethod
    def preprocess(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform raw input into a normalized dict ready for inference."""
        ...


class InferenceEngine(ABC):
    """Abstract base for inference engines."""

    @abstractmethod
    async def infer(self, preprocessed: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Run inference and return a result dict."""
        ...


class ResultPostprocessor(ABC):
    """Abstract base for result postprocessors."""

    @abstractmethod
    def postprocess(self, inference_result: Dict[str, Any]) -> Dict[str, Any]:
        """Structure raw inference output into a standardized format."""
        ...
