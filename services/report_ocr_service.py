"""体检报告 OCR 服务（M-PERF2）。

只返回**草稿**，不写 `HealthRecord`：前端复用 v1 健康记录表单，用户确认后
`POST /api/health/records`。越界值一律置 `None`（草稿容错优先），最终范围校验
仍由 v1 表单接口把关。
"""

import asyncio
import logging
import math

from fastapi import HTTPException

from services.image_service import ImageValidationError, prepare_image
from services.text_cleaning import clean_output_list
from services.vision_service import (
    VisionServiceError,
    analyze_image_json_sync,
    resolve_vision_config,
)

logger = logging.getLogger(__name__)

MAX_ABNORMAL_ITEMS = 10
MAX_ABNORMAL_TEXT = 30

# 字段 -> (类型, 下限, 上限)；与 models.HealthRecord 的取值语义一致
FIELD_RANGES: dict[str, tuple[str, float, float]] = {
    "height": ("float", 50, 250),
    "weight": ("float", 10, 300),
    "blood_pressure_systolic": ("int", 50, 260),
    "blood_pressure_diastolic": ("int", 30, 200),
    "heart_rate": ("int", 20, 250),
    "temperature": ("float", 30, 45),
    "vision_left": ("float", 0, 10),
    "vision_right": ("float", 0, 10),
}

REPORT_PROMPT = """你是体检报告识别助手。请从这张体检报告照片中提取数值指标。

严格只返回 JSON，不要任何解释文字，格式如下：
{"fields":{"height":172.0,"weight":65.5,"blood_pressure_systolic":118,"blood_pressure_diastolic":76,"heart_rate":72,"temperature":36.5,"vision_left":4.8,"vision_right":4.9},"abnormal":["血压偏高"],"confidence":0.74}

要求：
1. fields 必须包含上述全部 8 个键；识别不到的键填 null，不要臆造数值。
2. height 单位厘米，weight 单位千克，体温单位摄氏度，视力按报告原始记法（如 4.8 或 1.0）。
3. abnormal 是 0-5 条异常提示短语（如"血压偏高""空腹血糖偏高"），仅作展示，不下诊断。
4. confidence 是 0-1 的整体置信度。
5. 只输出 JSON，不要 markdown 代码块。"""


def _coerce(value, kind: str, low: float, high: float):
    """把模型给的原始值收敛到合法范围；越界、非数值、NaN/±Inf 返回 None。"""
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    # inf 会被下面的范围判断拦掉，但显式限定有限值更直接，避免 round(inf) 溢出
    if not math.isfinite(number) or number < low or number > high:
        return None
    return round(number) if kind == "int" else round(number, 2)


def _clean_abnormal(value) -> list[str]:
    return clean_output_list(value, max_items=MAX_ABNORMAL_ITEMS, max_length=MAX_ABNORMAL_TEXT)


def extract_report(db, user_id: int, raw: bytes) -> dict:
    """识别体检报告，返回草稿（不写库）。"""
    try:
        image = prepare_image(raw)
    except ImageValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    config = resolve_vision_config(db, user_id)

    try:
        payload = analyze_image_json_sync(image, REPORT_PROMPT, config=config, max_tokens=1024)
    except VisionServiceError as exc:
        logger.warning("体检报告 OCR 失败：%s", exc)
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    raw_fields = payload.get("fields")
    if not isinstance(raw_fields, dict):
        raw_fields = {}

    fields = {
        key: _coerce(raw_fields.get(key), kind, low, high)
        for key, (kind, low, high) in FIELD_RANGES.items()
    }

    confidence = _coerce(payload.get("confidence", 0.5), "float", 0, 1)

    logger.info(
        "体检报告 OCR 完成（user=%d, 命中 %d 项）",
        user_id,
        sum(1 for v in fields.values() if v is not None),
    )
    return {
        "fields": fields,
        "abnormal": _clean_abnormal(payload.get("abnormal")),
        "confidence": confidence if confidence is not None else 0.0,
        "needs_confirm": True,
    }


async def aextract_report(db, user_id: int, raw: bytes) -> dict:
    """异步包装：把阻塞的 HTTP + PIL 处理放线程池。"""
    return await asyncio.to_thread(extract_report, db, user_id, raw)
