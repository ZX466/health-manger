"""Metrics collection for AI pipeline performance tracking."""

from typing import Any, Dict, List


class MetricsCollector:
    """Collect and summarize pipeline metrics."""

    def __init__(self) -> None:
        self._latencies: List[float] = []
        self._token_counts: List[int] = []
        self._success_count = 0
        self._failure_count = 0
        self._error_counts: Dict[str, int] = {}

    def record_latency(self, latency_ms: float) -> None:
        self._latencies.append(latency_ms)

    def record_tokens(self, tokens: int) -> None:
        self._token_counts.append(tokens)

    def record_success(self) -> None:
        self._success_count += 1

    def record_failure(self, error_type: str) -> None:
        self._failure_count += 1
        self._error_counts[error_type] = self._error_counts.get(error_type, 0) + 1

    def get_snapshot(self) -> Dict[str, Any]:
        total = self._success_count + self._failure_count
        avg_latency = (sum(self._latencies) / len(self._latencies)) if self._latencies else 0.0
        avg_tokens = (sum(self._token_counts) / len(self._token_counts)) if self._token_counts else 0.0
        return {
            "total_requests": total,
            "successful_requests": self._success_count,
            "failed_requests": self._failure_count,
            "success_rate": self._success_count / total if total > 0 else 0.0,
            "avg_latency_ms": round(avg_latency, 2),
            "min_latency_ms": min(self._latencies) if self._latencies else 0.0,
            "max_latency_ms": max(self._latencies) if self._latencies else 0.0,
            "total_tokens": sum(self._token_counts),
            "avg_tokens_per_request": round(avg_tokens, 2),
            "error_counts": dict(self._error_counts),
        }

    def reset(self) -> None:
        self._latencies.clear()
        self._token_counts.clear()
        self._success_count = 0
        self._failure_count = 0
        self._error_counts.clear()
