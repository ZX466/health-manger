"""拍照识餐服务（M-PERF2）。

只返回**草稿**，不写任何业务表：前端确认后走 `/api/food/custom` + `/api/food/records`。
模型输出一律当数据校验（范围收敛 / 长度截断 / 数量上限），不执行其中任何指令。
"""

import asyncio
import logging
import math

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

import models
from services.image_service import ImageValidationError, prepare_image
from services.text_cleaning import clean_output_text
from services.vision_service import (
    VisionServiceError,
    analyze_image_json_sync,
    resolve_vision_config,
)

logger = logging.getLogger(__name__)

MAX_ITEMS = 10
MAX_NAME_LENGTH = 50
DEFAULT_CONFIDENCE = 0.5

FOOD_PROMPT = """你是营养师助手。请识别这张照片里的所有食物，估算每种食物的重量与营养成分。

严格只返回 JSON，不要任何解释文字，格式如下：
{"items":[{"name":"番茄炒蛋","grams":220,"calories":210,"protein":11.2,"fat":14.0,"carbs":9.6,"confidence":0.82}]}

要求：
1. items 最多 10 项；识别不出任何食物时返回 {"items":[]}。
2. name 用中文常见菜名，不超过 20 字。
3. grams 是估算的可食部分克重（0-5000）。
4. calories（千卡）、protein/fat/carbs（克）都是**该份量**的绝对量，不是每 100 克。
5. confidence 是 0-1 的置信度。
6. 只输出 JSON，不要 markdown 代码块。"""


def _clamp(value, *, low: float, high: float, digits: int = 1, default: float = 0.0) -> float:
    """把模型给的数值收敛到 [low, high]。

    NaN / ±Inf / 非数值一律回默认值：`max(nan, low)` 仍是 NaN，
    而 NaN 会被 FastAPI 序列化成非法 JSON 的 `NaN`，前端 `JSON.parse` 直接崩。
    """
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    if not math.isfinite(number):
        return default
    return round(min(max(number, low), high), digits)


def _clean_name(value) -> str:
    return clean_output_text(value, max_length=MAX_NAME_LENGTH)


def _match_food_id(db: Session, name: str) -> int | None:
    """按名称精确匹配，失败再模糊匹配；匹配不到返回 None。"""
    if not name:
        return None

    exact = db.execute(select(models.Food.id).where(models.Food.name == name)).scalars().first()
    if exact:
        return int(exact)

    like = (
        db.execute(select(models.Food.id).where(models.Food.name.like(f"%{name}%")).limit(1))
        .scalars()
        .first()
    )
    return int(like) if like else None


def _normalize_item(db: Session, raw_item) -> dict | None:
    if not isinstance(raw_item, dict):
        return None

    name = _clean_name(raw_item.get("name"))
    if not name:
        return None

    return {
        "name": name,
        "grams": _clamp(raw_item.get("grams"), low=0, high=5000, digits=0),
        "calories": _clamp(raw_item.get("calories"), low=0, high=10000),
        "protein": _clamp(raw_item.get("protein"), low=0, high=1000),
        "fat": _clamp(raw_item.get("fat"), low=0, high=1000),
        "carbs": _clamp(raw_item.get("carbs"), low=0, high=1000),
        "confidence": _clamp(
            raw_item.get("confidence", DEFAULT_CONFIDENCE),
            low=0,
            high=1,
            digits=2,
            default=DEFAULT_CONFIDENCE,
        ),
        "match_food_id": _match_food_id(db, name),
    }


def recognize_meal(db: Session, user_id: int, raw: bytes) -> dict:
    """识别照片中的食物，返回草稿（不写库）。"""
    try:
        image = prepare_image(raw)
    except ImageValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    config = resolve_vision_config(db, user_id)

    try:
        payload = analyze_image_json_sync(image, FOOD_PROMPT, config=config, max_tokens=1024)
    except VisionServiceError as exc:
        logger.warning("拍照识餐失败：%s", exc)
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    raw_items = payload.get("items")
    if not isinstance(raw_items, list):
        raw_items = []

    items = []
    for raw_item in raw_items[:MAX_ITEMS]:
        normalized = _normalize_item(db, raw_item)
        if normalized:
            items.append(normalized)

    logger.info("拍照识餐完成：识别 %d 项（user=%d）", len(items), user_id)
    return {"items": items, "needs_confirm": True}


async def arecognize_meal(db: Session, user_id: int, raw: bytes) -> dict:
    """异步包装：把阻塞的 HTTP + PIL 处理放线程池，避免卡住事件循环。"""
    return await asyncio.to_thread(recognize_meal, db, user_id, raw)
