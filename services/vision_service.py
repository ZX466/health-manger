"""视觉模型调用服务（M-PERF2）。

把「图片 + 提示词 -> JSON 字典」收敛成一条可复用路径，供拍照识餐、体检报告 OCR
复用（舌诊继续走 `tongue/cloud_analyzer.py`，避免破坏既有诊断链路）。

统一走 OpenAI 兼容 `chat/completions` 多模态格式（image_url data URI），
兼容智谱 GLM-4V / OpenAI / 火山 ARK 等。

安全边界：
- 模型输出一律当**数据**处理，只允许解析成 JSON，不执行其中任何指令；
- 错误信息不含 API Key；
- 无可用视觉配置时抛 `RuntimeError`，由路由转 503。
"""

import asyncio
import base64
import json
import logging
import re

import httpx

import settings

logger = logging.getLogger(__name__)

DEFAULT_VISION_TIMEOUT = 60.0
_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL)


class VisionServiceError(RuntimeError):
    """视觉模型调用失败（调用方应转 503）。"""


def resolve_vision_config(db, user_id: int) -> dict:
    """取用户自定义视觉配置，缺省回退 ARK 默认模型。"""
    from services.ai_config_service import build_vision_config_for_user

    config = build_vision_config_for_user(db, user_id)
    if config and config.get("api_key"):
        return config

    return {
        "provider": "ark",
        "base_url": settings.ARK_API_URL,
        "model": settings.ARK_MODEL_ID,
        "api_key": settings.ARK_API_KEY,
    }


def _describe_failure(status: int, body: str) -> str:
    """把上游 HTTP 失败翻译成可操作的提示（不回显上游原文，避免噪声/泄露）。"""
    code = ""
    message = ""
    try:
        data = json.loads(body)
        error = data.get("error") if isinstance(data, dict) else None
        if isinstance(error, dict):
            code = str(error.get("code") or "")
            message = str(error.get("message") or "")
    except (json.JSONDecodeError, TypeError):
        pass

    # 智谱 1210：messages.content.type 只允许 text，说明所选模型不支持图片输入。
    if code == "1210" or "content.type" in message:
        return "当前模型不支持图片输入，请在 AI 设置中换用视觉模型（如 glm-4v-plus）"
    if status in (401, 403):
        return f"视觉模型鉴权失败（HTTP {status}），请检查 AI 设置中的 API Key"
    if status == 404:
        return "视觉模型接口不存在（HTTP 404），请检查 Base URL 与模型名"
    if status == 400:
        return "视觉模型拒绝了请求（HTTP 400），请确认所选模型支持图像输入"
    return f"视觉模型拒绝了本次请求（HTTP {status}），请检查 AI 设置"


def _normalize_chat_url(base_url: str) -> str:
    """把 ARK 的 `/responses` 端点纠正为 OpenAI 兼容的 `/chat/completions`。"""
    url = (base_url or "").strip()
    if not url:
        return url
    if url.rstrip("/").endswith("/responses"):
        return url.rstrip("/")[: -len("/responses")] + "/chat/completions"
    return url


def _data_uri(image_bytes: bytes) -> str:
    """按真实格式生成 data URI（不信任 content-type / 扩展名）。"""
    import io

    from PIL import Image

    try:
        with Image.open(io.BytesIO(image_bytes)) as img:
            image_format = (img.format or "JPEG").upper()
    except Exception:
        image_format = "JPEG"

    mime = {"PNG": "png", "WEBP": "webp", "GIF": "gif"}.get(image_format, "jpeg")
    encoded = base64.b64encode(image_bytes).decode("utf-8")
    return f"data:image/{mime};base64,{encoded}"


def _extract_content(data: dict) -> str:
    """兼容 chat/completions 与 ARK responses 两种响应形态。"""
    choices = data.get("choices")
    if choices:
        message = choices[0].get("message") or {}
        content = message.get("content")
        if isinstance(content, str):
            return content.strip()
        if isinstance(content, list):
            parts = [
                part.get("text", "")
                for part in content
                if isinstance(part, dict) and part.get("type") in ("text", "output_text")
            ]
            if parts:
                return "".join(parts).strip()

    output = data.get("output")
    if isinstance(output, list):
        for item in output:
            if not isinstance(item, dict):
                continue
            for content_item in item.get("content") or []:
                if isinstance(content_item, dict) and "text" in content_item:
                    return str(content_item["text"]).strip()

    if isinstance(data.get("output_text"), str):
        return data["output_text"].strip()

    raise VisionServiceError("视觉模型返回内容为空")


def _parse_json_payload(text: str) -> dict:
    """剥离 ```json 围栏与首尾噪声后解析 JSON。"""
    candidate = (text or "").strip()
    fence = _JSON_FENCE_RE.search(candidate)
    if fence:
        candidate = fence.group(1).strip()

    start = candidate.find("{")
    end = candidate.rfind("}")
    if start != -1 and end > start:
        candidate = candidate[start : end + 1]

    parsed = json.loads(candidate)
    if not isinstance(parsed, dict):
        raise TypeError("模型返回的不是 JSON 对象")
    return parsed


def _post_chat(
    image_bytes: bytes,
    prompt: str,
    *,
    config: dict,
    max_tokens: int,
    use_json_mode: bool,
) -> dict:
    api_key = config.get("api_key")
    if not api_key:
        raise VisionServiceError("未配置视觉模型 API Key，请在 AI 设置中完善")

    url = _normalize_chat_url(config.get("base_url") or settings.ARK_API_URL)
    payload = {
        "model": config.get("model") or settings.ARK_MODEL_ID,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": _data_uri(image_bytes)}},
                    {"type": "text", "text": prompt},
                ],
            }
        ],
        "temperature": 0.2,
        "max_tokens": max_tokens,
    }
    if use_json_mode:
        payload["response_format"] = {"type": "json_object"}

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    with httpx.Client(timeout=DEFAULT_VISION_TIMEOUT) as client:
        response = client.post(url, json=payload, headers=headers)
    return response.status_code, response.text


def analyze_image_json_sync(
    image_bytes: bytes,
    prompt: str,
    *,
    config: dict,
    max_tokens: int = 1024,
) -> dict:
    """同步版：请求视觉模型并返回解析后的 JSON 字典。

    `response_format=json_object` 不被支持时自动去掉重试；JSON 解析失败重试一次。
    """
    if not image_bytes:
        raise VisionServiceError("图片内容为空")

    attempts: list[bool] = [True, False]  # 第一次带 json_object，第二次不带
    last_error: Exception | None = None

    for index, use_json_mode in enumerate(attempts):
        try:
            status, body = _post_chat(
                image_bytes,
                prompt,
                config=config,
                max_tokens=max_tokens,
                use_json_mode=use_json_mode,
            )
        except httpx.TimeoutException as exc:
            raise VisionServiceError("视觉模型响应超时，请稍后重试") from exc
        except httpx.HTTPError as exc:
            raise VisionServiceError(
                f"视觉模型连接失败（{type(exc).__name__}），请稍后重试"
            ) from exc

        if status == 400 and use_json_mode:
            logger.info("视觉接口不支持 response_format，去掉后重试")
            continue
        if status >= 500 or status == 429:
            raise VisionServiceError("视觉模型服务暂时不可用，请稍后重试")
        if status != 200:
            logger.warning("视觉模型返回 HTTP %s", status)
            raise VisionServiceError(_describe_failure(status, body))

        try:
            data = json.loads(body)
        except json.JSONDecodeError as exc:
            raise VisionServiceError("视觉模型返回了非法响应") from exc

        try:
            return _parse_json_payload(_extract_content(data))
        except (TypeError, ValueError, VisionServiceError) as exc:
            last_error = exc
            logger.warning("视觉模型 JSON 解析失败（第 %d 次）：%s", index + 1, type(exc).__name__)
            continue

    raise VisionServiceError("视觉模型返回内容无法解析，请重试") from last_error


async def analyze_image_json(
    image_bytes: bytes,
    prompt: str,
    *,
    config: dict,
    max_tokens: int = 1024,
) -> dict:
    """异步版：把阻塞的 HTTP 调用放到线程池，避免卡住事件循环。"""
    return await asyncio.to_thread(
        analyze_image_json_sync,
        image_bytes,
        prompt,
        config=config,
        max_tokens=max_tokens,
    )
