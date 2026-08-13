import asyncio
import json
import logging
import threading
from typing import Optional

import httpx

import settings
from services.security_service import sanitize_for_prompt

logger = logging.getLogger(__name__)

ZHIPU_API_KEY = settings.ZHIPU_API_KEY
ZHIPU_API_URL = settings.ZHIPU_API_URL
DEFAULT_MODEL = settings.ZHIPU_MODEL
DEFAULT_TIMEOUT = settings.LLM_TIMEOUT

# S14: httpx.AsyncClient 非线程安全。异步端点与 async_tasks 工作线程
# （_run_llm_sync 新建 event loop）会并发调用，改用线程本地 client，
# 每个线程一个独立连接池，避免共享同一 client 的竞态。
_client_local = threading.local()


async def _get_client() -> httpx.AsyncClient:
    client = getattr(_client_local, "client", None)
    if client is None or client.is_closed:
        client = httpx.AsyncClient(timeout=DEFAULT_TIMEOUT)
        _client_local.client = client
    return client


async def close_http_client() -> None:
    client = getattr(_client_local, "client", None)
    if client and not client.is_closed:
        await client.aclose()
        _client_local.client = None


class LLMConfig:
    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        temperature: float = 0.7,
        max_tokens: int = 1500,
        timeout: float = DEFAULT_TIMEOUT
    ):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout


# Retry configuration
MAX_RETRIES = settings.LLM_MAX_RETRIES
RETRY_BACKOFF_BASE = settings.LLM_RETRY_BACKOFF_BASE


async def call_llm(
    messages: list,
    config: Optional[LLMConfig] = None
) -> tuple:
    """调用智谱 AI LLM 接口，带指数退避重试（最多 MAX_RETRIES 次）。

    返回:
        (content, tokens_used) 元组
    抛出:
        ValueError  -- API 密钥未配置
        RuntimeError -- 所有重试耗尽或不可恢复的错误
    """
    # --- 配置校验与请求准备 ---
    config = config or LLMConfig()

    if not ZHIPU_API_KEY:
        raise ValueError("未配置智谱 AI API 密钥 (ZHIPU_API_KEY)")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {ZHIPU_API_KEY}"
    }

    payload = {
        "model": config.model,
        "messages": messages,
        "temperature": config.temperature,
        "max_tokens": config.max_tokens,
        "stream": False
    }

    last_exception: Optional[Exception] = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(
                "LLM 请求开始 (attempt=%d/%d, model=%s, timeout=%.1fs)",
                attempt, MAX_RETRIES, config.model, config.timeout,
            )

            client = await _get_client()
            response = await client.post(
                ZHIPU_API_URL,
                headers=headers,
                json=payload,
                timeout=config.timeout
            )

            if response.status_code != 200:
                raise RuntimeError(
                    f"AI 服务调用失败 (HTTP {response.status_code})：{response.text}"
                )

            result = response.json()
            content = result["choices"][0]["message"]["content"]
            tokens_used = result.get("usage", {}).get("total_tokens", 0)

            logger.info(
                "LLM 请求成功 (attempt=%d, tokens_used=%d)",
                attempt, tokens_used,
            )
            return content, tokens_used

        except (httpx.TimeoutException, httpx.ConnectError) as exc:
            # Transient network errors -- retry
            last_exception = exc
            logger.warning(
                "LLM 请求超时或连接失败 (attempt=%d/%d): %s",
                attempt, MAX_RETRIES, exc,
            )

        except RuntimeError as exc:
            # Non-200 status from the API -- retry only on 5xx (server errors)
            error_msg = str(exc)
            is_server_error = any(
                f"HTTP {code}" in error_msg
                for code in (500, 502, 503, 504)
            )
            if is_server_error and attempt < MAX_RETRIES:
                last_exception = exc
                logger.warning(
                    "LLM 服务端错误，将重试 (attempt=%d/%d): %s",
                    attempt, MAX_RETRIES, exc,
                )
            else:
                # 4xx or final attempt -- do not retry
                logger.error(
                    "LLM 请求失败 (attempt=%d/%d): %s",
                    attempt, MAX_RETRIES, exc,
                )
                raise

        except (KeyError, IndexError) as exc:
            # Response parsing error -- likely a malformed API response, no retry
            logger.error(
                "LLM 响应解析失败 (attempt=%d/%d): %s",
                attempt, MAX_RETRIES, exc,
            )
            raise RuntimeError(f"AI 服务返回数据格式异常：{exc}") from exc

        # Exponential backoff before next attempt (skip delay after last attempt)
        if attempt < MAX_RETRIES:
            delay = RETRY_BACKOFF_BASE * (2 ** (attempt - 1))
            logger.info("等待 %.1f 秒后进行第 %d 次重试", delay, attempt + 1)
            await asyncio.sleep(delay)

    # All retries exhausted
    logger.error(
        "LLM 请求在 %d 次重试后仍然失败", MAX_RETRIES,
    )
    raise RuntimeError(
        f"AI 服务在 {MAX_RETRIES} 次重试后仍然失败：{last_exception}"
    ) from last_exception


def build_health_analysis_prompt(health_data: dict, user_question: str) -> list:
    system_prompt = """你是一位专业的健康顾问，擅长根据用户的健康数据提供个性化的健康建议。
请用中文回答，语气亲切专业，建议具体可行。"""

    safe_question = sanitize_for_prompt(user_question, max_length=500)
    safe_data = {k: sanitize_for_prompt(str(v), max_length=100) for k, v in health_data.items()}

    user_prompt = f"""我的健康数据如下：
{json.dumps(safe_data, ensure_ascii=False)}

用户问题：{safe_question}

请根据我的健康数据，提供专业的健康分析和建议。"""

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]


def build_quick_analysis_prompt(health_data: dict) -> list:
    system_prompt = """你是一位专业的健康顾问，擅长根据用户的健康数据提供个性化的健康建议。
请用中文回答，语气亲切专业，建议具体可行。"""

    safe_data = {k: sanitize_for_prompt(str(v), max_length=100) for k, v in health_data.items()}

    user_prompt = f"""我的健康数据如下：
{json.dumps(safe_data, ensure_ascii=False)}

请根据我的健康数据，给出全面的健康评估和建议，包括：
1. BMI 评估
2. 血压评估
3. 整体健康状况
4. 具体的改善建议"""

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]


CHAT_SYSTEM_PROMPT = """你是一位专业的中医健康顾问，擅长根据用户的舌诊结果和健康数据提供个性化的健康建议。
请用中文回答，语气亲切专业，建议具体可行。"""


def build_health_rating_llm_prompt(health_data: dict, rule_score: int, rule_rating: str) -> list:
    system_prompt = """你是一位专业的健康评估专家。基于用户的健康数据和已有的规则评分结果，给出综合健康评价。
要求：
1. 先确认规则评分的合理性
2. 补充规则评分无法覆盖的维度（如生活方式、心理状态、运动习惯等）
3. 给出综合评价和个性化改善建议
请用中文回答，语气亲切专业。"""

    safe_data = {k: sanitize_for_prompt(str(v), max_length=100) for k, v in health_data.items()}

    user_prompt = f"""我的健康数据：
{json.dumps(safe_data, ensure_ascii=False)}

系统规则评分结果：
- 健康评分：{rule_score}/100
- 健康等级：{rule_rating}

请基于以上数据给出综合健康评价，补充规则评分无法涵盖的分析维度，并给出改善建议。"""

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
