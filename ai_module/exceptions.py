"""Custom exceptions for the AI pipeline."""

from typing import Any, Dict, Optional


class AIPipelineError(Exception):
    """Base exception for AI pipeline errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.details = details or {}


class PreprocessingError(AIPipelineError, ValueError):
    """Raised when data preprocessing fails."""


class InferenceError(AIPipelineError):
    """Raised when inference fails."""


class PostprocessingError(AIPipelineError):
    """Raised when postprocessing fails."""
