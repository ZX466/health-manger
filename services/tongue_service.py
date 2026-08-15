"""Business logic for tongue diagnosis: file handling, analysis, CRUD, stats."""

import asyncio
import hashlib
import logging
import os
import uuid
from pathlib import Path
from typing import List

from fastapi import HTTPException, UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session

import models
from services.cache_service import tongue_result_cache

logger = logging.getLogger(__name__)

UPLOAD_DIR = os.path.join("uploads", "tongue")
os.makedirs(UPLOAD_DIR, exist_ok=True)

MAX_FILE_SIZE = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


async def upload_and_analyze(
    file: UploadFile, user_id: int, db: Session
) -> models.TongueDiagnosis:
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="请上传图片文件")

    file_ext = os.path.splitext(file.filename)[1].lower() or ".jpg"
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式，允许: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="文件大小不能超过10MB")

    # S5: 魔数/真实图像校验——content-type 可伪造，用 PIL 验证确为有效图像
    try:
        import io

        from PIL import Image

        with Image.open(io.BytesIO(content)) as img:
            img.verify()
    except Exception:
        raise HTTPException(status_code=400, detail="文件不是有效的图片")

    filename = f"{uuid.uuid4().hex}{file_ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    image_hash = hashlib.sha256(content).hexdigest()

    with open(filepath, "wb") as f:
        f.write(content)

    db_diagnosis = models.TongueDiagnosis(
        user_id=user_id,
        image_path=filepath,
        image_hash=image_hash,
        analysis_status="analyzing",
    )
    db.add(db_diagnosis)
    db.commit()
    db.refresh(db_diagnosis)

    try:
        from tongue import analyze_tongue_image

        # 使用用户自定义视觉模型配置（未配置回退默认 ARK）
        from services.ai_config_service import build_vision_config_for_user
        vision_config = build_vision_config_for_user(db, user_id)

        cached_result = tongue_result_cache.get(image_hash)
        if cached_result:
            result = cached_result
        else:
            result = await asyncio.to_thread(analyze_tongue_image, filepath, vision_config)
            tongue_result_cache.set(image_hash, result)

        db_diagnosis.tongue_color = result["tongue_color"]
        db_diagnosis.coating_color = result["coating_color"]
        db_diagnosis.coating_thickness = result["coating_thickness"]
        db_diagnosis.has_cracks = result["has_cracks"]
        db_diagnosis.has_teeth_marks = result["has_teeth_marks"]
        db_diagnosis.tongue_shape = result["tongue_shape"]
        db_diagnosis.moisture_level = result["moisture_level"]
        db_diagnosis.tongue_spirit = result["tongue_spirit"]
        db_diagnosis.overall_type = result["overall_type"]
        db_diagnosis.confidence_score = result["confidence_score"]
        db_diagnosis.tcm_syndrome = result["tcm_syndrome"]
        db_diagnosis.health_advice = result["health_advice"]
        db_diagnosis.diet_suggestion = result["diet_suggestion"]
        db_diagnosis.lifestyle_advice = result["lifestyle_advice"]
        db_diagnosis.analysis_status = "completed"

        db.commit()
        db.refresh(db_diagnosis)
    except RuntimeError as e:
        logger.error("舌诊云端分析失败: %s", e, exc_info=True)
        _cleanup_failed_diagnosis(db_diagnosis, filepath, db)
        raise HTTPException(status_code=503, detail="分析服务暂不可用，请稍后重试")
    except Exception as e:
        logger.error("舌诊分析失败: %s", e, exc_info=True)
        _cleanup_failed_diagnosis(db_diagnosis, filepath, db)
        raise HTTPException(status_code=500, detail="分析失败，请稍后重试")

    return db_diagnosis


def _cleanup_failed_diagnosis(
    diagnosis: models.TongueDiagnosis, filepath: str, db: Session
) -> None:
    """分析失败时清理孤儿图片文件与失败记录，避免磁盘与 DB 累积。"""
    if os.path.exists(filepath):
        try:
            os.remove(filepath)
        except (OSError, IOError):
            pass

    db.delete(diagnosis)
    db.commit()


def get_diagnoses(
    user_id: int, db: Session, limit: int = 20, offset: int = 0
) -> List[models.TongueDiagnosis]:
    return (
        db.execute(
            select(models.TongueDiagnosis)
            .where(models.TongueDiagnosis.user_id == user_id)
            .order_by(models.TongueDiagnosis.created_at.desc())
            .offset(offset)
            .limit(limit)
        ).scalars().all()
    )


def get_diagnosis(diagnosis_id: int, user_id: int, db: Session) -> models.TongueDiagnosis:
    diagnosis = db.execute(
        select(models.TongueDiagnosis).where(
            models.TongueDiagnosis.id == diagnosis_id,
            models.TongueDiagnosis.user_id == user_id,
        )
    ).scalars().first()
    if not diagnosis:
        raise HTTPException(status_code=404, detail="舌诊记录不存在")
    return diagnosis


def get_diagnosis_image_path(diagnosis: models.TongueDiagnosis) -> str:
    """Return an existing diagnosis image only when it remains under UPLOAD_DIR."""
    upload_root = Path(UPLOAD_DIR).resolve()
    image_path = Path(diagnosis.image_path).resolve()
    try:
        image_path.relative_to(upload_root)
    except ValueError:
        logger.warning("Rejected tongue image path outside upload directory: %s", image_path)
        raise HTTPException(status_code=404, detail="舌诊图片不存在")

    if not image_path.is_file():
        raise HTTPException(status_code=404, detail="舌诊图片不存在")
    return str(image_path)


def get_latest_completed(user_id: int, db: Session) -> models.TongueDiagnosis:
    diagnosis = db.execute(
        select(models.TongueDiagnosis)
        .where(
            models.TongueDiagnosis.user_id == user_id,
            models.TongueDiagnosis.analysis_status == "completed",
        )
        .order_by(models.TongueDiagnosis.created_at.desc())
    ).scalars().first()
    if not diagnosis:
        raise HTTPException(status_code=404, detail="暂无舌诊记录，请先上传舌象图片")
    return diagnosis


def delete_diagnosis(diagnosis_id: int, user_id: int, db: Session) -> dict:
    diagnosis = get_diagnosis(diagnosis_id, user_id, db)

    if diagnosis.image_path and os.path.exists(diagnosis.image_path):
        try:
            os.remove(diagnosis.image_path)
        except (OSError, IOError):
            pass

    db.delete(diagnosis)
    db.commit()
    return {"message": "删除成功"}


def get_stats(user_id: int, db: Session) -> dict:
    total = db.scalar(
        select(func.count()).select_from(models.TongueDiagnosis).where(
            models.TongueDiagnosis.user_id == user_id
        )
    )

    completed = db.scalar(
        select(func.count()).select_from(models.TongueDiagnosis).where(
            models.TongueDiagnosis.user_id == user_id,
            models.TongueDiagnosis.analysis_status == "completed",
        )
    )

    latest = db.execute(
        select(models.TongueDiagnosis)
        .where(
            models.TongueDiagnosis.user_id == user_id,
            models.TongueDiagnosis.analysis_status == "completed",
        )
        .order_by(models.TongueDiagnosis.created_at.desc())
    ).scalars().first()

    syndrome_distribution: dict[str, int] = {}
    if completed > 0:
        syndromes = db.execute(
            select(models.TongueDiagnosis.tcm_syndrome).where(
                models.TongueDiagnosis.user_id == user_id,
                models.TongueDiagnosis.analysis_status == "completed",
            )
        ).all()
        for s in syndromes:
            if s[0]:
                syndrome_distribution[s[0]] = syndrome_distribution.get(s[0], 0) + 1

    return {
        "total_records": total,
        "completed_records": completed,
        "latest_syndrome": latest.tcm_syndrome if latest else None,
        "latest_overall_type": latest.overall_type if latest else None,
        "syndrome_distribution": syndrome_distribution,
    }
