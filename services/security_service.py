import re
import time
import unicodedata
import threading
from collections import defaultdict

PROMPT_INJECTION_PATTERNS = [
    r"(?i)ignore\s+(all\s+)?(previous|prior|above|following)\s+(instructions?|prompts?)",
    r"(?i)(forget|disregard|override)\s+(everything|all|previous)",
    r"(?i)you\s+are\s+now",
    r"(?i)act\s+as\s+(if\s+you\s+are)",
    r"(?i)system\s*:\s*",
    r"(?i)role\s*:\s*(system|admin|administrator)",
    r"(?i)(jailbreak|DAN|developer\s+mode)",
    r"<\|.*?\|>",
    r"\[.*?INST.*?\]",
    r"```(?:python|bash|javascript).*?```",
    # Chinese injection patterns
    r"请(忘掉|忽略|无视|抛弃|丢弃|不要管|不用管)(你)?(之前|以前|上面|以上)(的)?(所有|全部)?(指令|提示|规则|限制|设定|指导)",
    r"(从现在开始|从现在起|从此刻起)(你)?(是|变成|成为|扮演|当做)",
    r"(系统|system)\s*(提示|prompt|指令|设定)",
    r"(输出|显示|告诉|打印|复述)(你)?(的)?(系统|原始|完整|所有)(提示|prompt|指令|设定|规则)",
    r"(你的|你的真正|原本的)(身份|角色|目的|指令|prompt)",
    r"(不要|不可以|不准|禁止)(遵守|遵循|执行|听从)(你)?(之前|以前|原始)(的)?(指令|规则|限制)",
    # S8: 补充常见绕过变体（拆词/同义改写/斜杠变体）
    r"(?i)ignore\s*(the)?\s*(system|developer|admin)?\s*prompt",
    r"(?i)print\s*(your|the)\s*(system|initial|full|original)\s*prompt",
    r"(?i)reveal\s*(your|the)\s*(system|hidden|original)\s*prompt",
    r"(?i)repeat\s*(everything|all)\s*(above|below)",
    r"(?i)disregard\s+(the\s+)?(previous|earlier|prior)",
    r"(?i)bypass\s*(the)?\s*(safet|guardrail|filter)",
    r"请(展示|显示|复述|背诵)(你)?(的)?(全部|所有|原始)(系统)?(提示词|设定|指令)",
    r"忽略(上面|之前的)?(所有)?(内容|消息|对话|规则)",
    r"(?i)\b((role|system)\s*[:=])\s*(admin|system|developer|assistant)\b",
]

_MAX_INPUT_LENGTH = 2000

DEFAULT_RATE_LIMIT_REQUESTS = 60
DEFAULT_RATE_LIMIT_WINDOW_SECONDS = 60

_ZERO_WIDTH_RE = re.compile(r'[​-‏ - ⁠-⁯﻿­]')


def sanitize_for_prompt(text: str, max_length: int = _MAX_INPUT_LENGTH) -> str:
    if not text:
        return ""

    truncated = text[:max_length]

    cleaned = _ZERO_WIDTH_RE.sub('', truncated)
    cleaned = unicodedata.normalize('NFKD', cleaned)

    for pattern in PROMPT_INJECTION_PATTERNS:
        cleaned = re.sub(pattern, "[已过滤]", cleaned, flags=re.IGNORECASE)

    control_chars_removed = "".join(
        ch for ch in cleaned if ch >= " " or ch in "\n\r\t"
    )

    return control_chars_removed.strip()


class RateLimiter:
    def __init__(self):
        self._requests: defaultdict[str, list] = defaultdict(list)
        self._lock = threading.Lock()

    def is_allowed(self, key: str, max_requests: int = DEFAULT_RATE_LIMIT_REQUESTS,
                   window_seconds: int = DEFAULT_RATE_LIMIT_WINDOW_SECONDS) -> tuple:
        now = time.time()
        cutoff = now - window_seconds

        with self._lock:
            self._requests[key] = [
                t for t in self._requests[key] if t > cutoff
            ]

            if len(self._requests[key]) >= max_requests:
                oldest = self._requests[key][0]
                retry_after = int(oldest + window_seconds - now) + 1
                return False, retry_after

            self._requests[key].append(now)
            return True, 0

    def cleanup(self):
        now = time.time()
        with self._lock:
            for key in list(self._requests.keys()):
                self._requests[key] = [t for t in self._requests[key] if t > now - 3600]
                if not self._requests[key]:
                    del self._requests[key]


_rate_limiter = RateLimiter()


def check_rate_limit(key: str,
                     max_requests: int = DEFAULT_RATE_LIMIT_REQUESTS,
                     window_seconds: int = DEFAULT_RATE_LIMIT_WINDOW_SECONDS):
    allowed, retry_after = _rate_limiter.is_allowed(key, max_requests, window_seconds)
    if not allowed:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=429,
            detail="请求过于频繁，请稍后再试",
            headers={"Retry-After": str(retry_after)}
        )
