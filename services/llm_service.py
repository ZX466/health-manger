import asyncio
import ipaddress
import json
import logging
import threading
from collections.abc import AsyncIterator
from urllib.parse import urlsplit

import httpx

import settings
from services.security_service import sanitize_for_prompt

logger = logging.getLogger(__name__)

ZHIPU_API_KEY = settings.ZHIPU_API_KEY
ZHIPU_API_URL = settings.ZHIPU_API_URL
DEFAULT_MODEL = settings.ZHIPU_MODEL
DEFAULT_TIMEOUT = settings.LLM_TIMEOUT

# S-1：供应商与默认地址由服务端固定，不能由用户提交的 base_url 反推。
# 只有智谱默认地址允许使用服务级 ZHIPU_API_KEY；其他供应商/自定义地址
# 必须使用用户自己保存的密钥，避免把服务端密钥发送到任意主机。
_PROVIDER_DEFAULT_URLS = {
    "openai": "https://api.openai.com/v1/chat/completions",
    "ark": "https://ark.cn-beijing.volces.com/api/v3/chat/completions",
}
_LOOPBACK_HOSTS = {"localhost", "127.0.0.1", "::1"}


def _normalized_url(url: str | None) -> str:
    return (url or "").strip().rstrip("/")


def provider_default_url(provider: str) -> str:
    """返回服务端认可的供应商默认地址；未知供应商返回空串。"""
    if provider == "zhipu":
        return _normalized_url(ZHIPU_API_URL)
    return _normalized_url(_PROVIDER_DEFAULT_URLS.get(provider))


def is_provider_default_url(provider: str, base_url: str | None) -> bool:
    """判断地址是否为该供应商的默认地址（忽略末尾斜杠）。"""
    default_url = provider_default_url(provider)
    return bool(default_url) and _normalized_url(base_url) == default_url


def _is_loopback_host(host: str) -> bool:
    if host in _LOOPBACK_HOSTS:
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def _is_private_host(host: str) -> bool:
    if _is_loopback_host(host):
        return True
    if host.endswith(".local"):
        return True
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return False
    return address.is_private or address.is_link_local or address.is_reserved


def validate_llm_endpoint(
    provider: str, base_url: str | None, *, has_user_key: bool
) -> str:
    """校验出站地址并返回规范化后的 URL。

    - 仅允许 http(s)，且 http 只允许回环地址（本地开发）；
    - 非默认地址必须由用户自己的密钥驱动，禁止服务级密钥外发；
    - 非默认地址不得指向内网、链路本地或保留地址。
    """
    provider = (provider or "zhipu").strip().lower()
    default_url = provider_default_url(provider)
    if not default_url:
        raise ValueError("不支持的 AI 供应商")

    url = _normalized_url(base_url) or default_url
    parsed = urlsplit(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError("AI 服务地址必须以 http:// 或 https:// 开头")
    if parsed.username or parsed.password:
        raise ValueError("AI 服务地址不能包含账号或密码")
    host = parsed.hostname
    if not host:
        raise ValueError("AI 服务地址缺少主机名")

    if parsed.scheme == "http" and not _is_loopback_host(host):
        raise ValueError("AI 服务地址必须使用 HTTPS")

    if not is_provider_default_url(provider, url):
        if not has_user_key:
            raise ValueError("自定义 AI 服务地址必须配置独立 API 密钥")
        if _is_private_host(host) and not _is_loopback_host(host):
            raise ValueError("AI 服务地址不能指向内网或保留地址")

    return url

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
    """LLM 调用配置。

    provider/api_key/base_url 支持运行时覆盖（用户自定义 AI 配置）。
    服务级 ZHIPU_API_KEY 只绑定智谱默认地址；自定义地址必须自带密钥。
    所有 provider 均走 OpenAI 兼容 chat/completions 格式（zhipu/openai/ark 均支持）。
    """

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        temperature: float = 0.7,
        max_tokens: int = 1500,
        timeout: float = DEFAULT_TIMEOUT,
        provider: str = "zhipu",
        api_key: str | None = None,
        base_url: str | None = None,
    ):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.provider = (provider or "zhipu").strip().lower()
        user_key = api_key.strip() if isinstance(api_key, str) else api_key
        self.base_url = validate_llm_endpoint(
            self.provider, base_url, has_user_key=bool(user_key)
        )
        if user_key:
            self.api_key = user_key
        elif self.provider == "zhipu" and is_provider_default_url(
            self.provider, self.base_url
        ):
            self.api_key = ZHIPU_API_KEY
        else:
            # 不把服务级智谱密钥发给其他供应商或自定义地址
            self.api_key = ""


# Retry configuration
MAX_RETRIES = settings.LLM_MAX_RETRIES
RETRY_BACKOFF_BASE = settings.LLM_RETRY_BACKOFF_BASE


async def call_llm(messages: list, config: LLMConfig | None = None) -> tuple:
    """调用智谱 AI LLM 接口，带指数退避重试（最多 MAX_RETRIES 次）。

    返回:
        (content, tokens_used) 元组
    抛出:
        ValueError  -- API 密钥未配置
        RuntimeError -- 所有重试耗尽或不可恢复的错误
    """
    # --- 配置校验与请求准备 ---
    config = config or LLMConfig()

    if not config.api_key:
        raise ValueError("未配置 AI API 密钥")

    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {config.api_key}"}

    payload = {
        "model": config.model,
        "messages": messages,
        "temperature": config.temperature,
        "max_tokens": config.max_tokens,
        "stream": False,
    }

    last_exception: Exception | None = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(
                "LLM 请求开始 (attempt=%d/%d, model=%s, timeout=%.1fs)",
                attempt,
                MAX_RETRIES,
                config.model,
                config.timeout,
            )

            client = await _get_client()
            response = await client.post(
                config.base_url, headers=headers, json=payload, timeout=config.timeout
            )

            if response.status_code != 200:
                # S-1：上游响应体可能含内部细节/回显内容，只保留状态码。
                raise RuntimeError(f"AI 服务调用失败 (HTTP {response.status_code})")

            result = response.json()
            content = result["choices"][0]["message"]["content"]
            tokens_used = result.get("usage", {}).get("total_tokens", 0)

            logger.info(
                "LLM 请求成功 (attempt=%d, tokens_used=%d)",
                attempt,
                tokens_used,
            )
            return content, tokens_used

        except (httpx.TimeoutException, httpx.ConnectError) as exc:
            # Transient network errors -- retry
            last_exception = exc
            logger.warning(
                "LLM 请求超时或连接失败 (attempt=%d/%d, error=%s)",
                attempt,
                MAX_RETRIES,
                type(exc).__name__,
            )

        except RuntimeError as exc:
            # Non-200 status from the API -- retry only on 5xx (server errors)
            error_msg = str(exc)
            is_server_error = any(f"HTTP {code}" in error_msg for code in (500, 502, 503, 504))
            if is_server_error and attempt < MAX_RETRIES:
                last_exception = exc
                logger.warning(
                    "LLM 服务端错误，将重试 (attempt=%d/%d, error=%s)",
                    attempt,
                    MAX_RETRIES,
                    type(exc).__name__,
                )
            else:
                # 4xx or final attempt -- do not retry
                logger.error(
                    "LLM 请求失败 (attempt=%d/%d, error=%s)",
                    attempt,
                    MAX_RETRIES,
                    type(exc).__name__,
                )
                raise

        except (KeyError, IndexError) as exc:
            # Response parsing error -- likely a malformed API response, no retry
            logger.error(
                "LLM 响应解析失败 (attempt=%d/%d, error=%s)",
                attempt,
                MAX_RETRIES,
                type(exc).__name__,
            )
            raise RuntimeError("AI 服务返回数据格式异常") from exc

        # Exponential backoff before next attempt (skip delay after last attempt)
        if attempt < MAX_RETRIES:
            delay = RETRY_BACKOFF_BASE * (2 ** (attempt - 1))
            logger.info("等待 %.1f 秒后进行第 %d 次重试", delay, attempt + 1)
            await asyncio.sleep(delay)

    # All retries exhausted
    logger.error(
        "LLM 请求在 %d 次重试后仍然失败",
        MAX_RETRIES,
    )
    raise RuntimeError(f"AI 服务在 {MAX_RETRIES} 次重试后仍然失败") from last_exception


async def stream_llm(messages: list, config: LLMConfig | None = None) -> AsyncIterator[str]:
    """流式调用 OpenAI 兼容的 chat/completions 接口，逐块产出增量文本。

    与 call_llm 的区别：
    - 请求体 stream=True，用 httpx 的流式响应逐行解析 SSE；
    - 只产出 choices[0].delta.content（忽略 reasoning_content 等思考字段）；
    - **不重试**：一旦已向下游产出内容，重试会导致重复文本，故失败即抛错。

    抛出:
        ValueError  -- API 密钥未配置
        RuntimeError -- 超时 / 连接失败 / 非 200 响应（错误信息不含 API Key）
    """
    config = config or LLMConfig()

    if not config.api_key:
        raise ValueError("未配置 AI API 密钥")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config.api_key}",
    }
    payload = {
        "model": config.model,
        "messages": messages,
        "temperature": config.temperature,
        "max_tokens": config.max_tokens,
        "stream": True,
    }

    logger.info("LLM 流式请求开始 (model=%s, timeout=%.1fs)", config.model, config.timeout)
    client = await _get_client()

    try:
        async with client.stream(
            "POST",
            config.base_url,
            headers=headers,
            json=payload,
            timeout=config.timeout,
        ) as response:
            if response.status_code != 200:
                # S-1：不读取/回显上游响应体，避免内部错误细节进入 SSE 错误。
                raise RuntimeError(f"AI 服务调用失败 (HTTP {response.status_code})")

            async for raw_line in response.aiter_lines():
                line = raw_line.strip()
                if not line or not line.startswith("data:"):
                    # 空行是 SSE 事件分隔符，其余（如 ": keep-alive"）忽略
                    continue

                data = line[len("data:") :].strip()
                if data == "[DONE]":
                    break

                try:
                    chunk = json.loads(data)
                except json.JSONDecodeError:
                    logger.warning("LLM 流式响应出现非 JSON 数据块，已跳过")
                    continue

                choices = chunk.get("choices") or []
                if not choices:
                    continue

                delta = choices[0].get("delta") or {}
                content = delta.get("content")
                if content:
                    yield content

    except httpx.TimeoutException as exc:
        logger.warning("LLM 流式请求超时: %s", type(exc).__name__)
        raise RuntimeError("AI 服务响应超时，请稍后重试") from exc
    except httpx.HTTPError as exc:
        logger.warning("LLM 流式请求连接失败: %s", type(exc).__name__)
        raise RuntimeError(f"AI 服务连接失败（{type(exc).__name__}），请稍后重试") from exc

    logger.info("LLM 流式请求结束 (model=%s)", config.model)


def build_health_analysis_prompt(health_data: dict, user_question: str) -> list:
    system_prompt = """你是一位专业的健康顾问，擅长根据用户的健康数据提供个性化的健康建议。
请用中文回答，语气亲切专业，建议具体可行。"""

    safe_question = sanitize_for_prompt(user_question, max_length=500)
    safe_data = {k: sanitize_for_prompt(str(v), max_length=100) for k, v in health_data.items()}

    user_prompt = f"""我的健康数据如下：
{json.dumps(safe_data, ensure_ascii=False)}

用户问题：{safe_question}

请根据我的健康数据，提供专业的健康分析和建议。"""

    return [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]


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

    return [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]


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

    return [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]
