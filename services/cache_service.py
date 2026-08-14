"""
缓存服务模块
提供基于 TTL 的内存缓存，用于减少重复 LLM 调用和舌诊分析
"""

import hashlib
import logging
import threading
import time
from typing import Any, Optional

import settings

logger = logging.getLogger(__name__)

DEFAULT_TTL_SECONDS = 3600  # 1 hour
MAX_CACHE_SIZE = 200


class TTLCache:
    def __init__(self, ttl: int = DEFAULT_TTL_SECONDS, max_size: int = MAX_CACHE_SIZE):
        self._cache: dict[str, tuple[Any, float]] = {}
        self._lock = threading.Lock()
        self._ttl = ttl
        self._max_size = max_size

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key not in self._cache:
                return None
            value, expire_at = self._cache[key]
            if time.time() > expire_at:
                del self._cache[key]
                return None
            return value

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            if len(self._cache) >= self._max_size:
                self._evict_expired()
                if len(self._cache) >= self._max_size:
                    oldest_key = min(self._cache, key=lambda k: self._cache[k][1])
                    del self._cache[oldest_key]
            self._cache[key] = (value, time.time() + self._ttl)

    def _evict_expired(self) -> None:
        now = time.time()
        expired = [k for k, (_, exp) in self._cache.items() if now > exp]
        for k in expired:
            del self._cache[k]

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()

    @property
    def size(self) -> int:
        return len(self._cache)


def make_cache_key(*parts: str) -> str:
    combined = "|".join(str(p) for p in parts)
    return hashlib.md5(combined.encode()).hexdigest()


# P-N2: 缓存参数从 settings 读取（支持环境变量 LLM_CACHE_TTL/LLM_CACHE_MAX_SIZE 等覆盖），
# 避免配置定义与实现硬编码值漂移
llm_response_cache = TTLCache(
    ttl=settings.LLM_CACHE_TTL,
    max_size=settings.LLM_CACHE_MAX_SIZE,
)
tongue_result_cache = TTLCache(
    ttl=settings.TONGUE_CACHE_TTL,
    max_size=settings.TONGUE_CACHE_MAX_SIZE,
)
