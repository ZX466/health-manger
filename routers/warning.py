from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models
import schemas
from auth import get_current_user
from datetime import datetime, timezone
from services.warning_service import check_health_warnings

router = APIRouter(prefix="/api/warning", tags=["健康预警"])


@router.post("/check", response_model=schemas.MessageResponse)
def check_warnings(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """检查当前用户的健康数据并生成预警"""
    warnings = check_health_warnings(current_user.id, db)
    return {"message": "检查完成", "new_warnings": len(warnings)}


@router.get("/list", response_model=List[schemas.HealthWarningResponse])
def get_warnings(
    is_read: Optional[bool] = None,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户的健康预警列表"""
    query = db.query(models.HealthWarning).filter(
        models.HealthWarning.user_id == current_user.id
    )
    
    if is_read is not None:
        query = query.filter(models.HealthWarning.is_read == is_read)
    
    warnings = query.order_by(models.HealthWarning.created_at.desc()).all()
    return warnings


@router.put("/read/{warning_id}", response_model=schemas.HealthWarningResponse)
def mark_as_read(
    warning_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """标记预警为已读"""
    warning = db.query(models.HealthWarning).filter(
        models.HealthWarning.id == warning_id,
        models.HealthWarning.user_id == current_user.id
    ).first()
    
    if not warning:
        raise HTTPException(status_code=404, detail="预警不存在")
    
    warning.is_read = True
    warning.resolved_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(warning)
    return warning


@router.put("/read-all", response_model=schemas.MessageResponse)
def mark_all_as_read(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """标记所有预警为已读"""
    db.query(models.HealthWarning).filter(
        models.HealthWarning.user_id == current_user.id,
        models.HealthWarning.is_read.is_(False)
    ).update({"is_read": True, "resolved_at": datetime.now(timezone.utc)})
    db.commit()
    return {"message": "已全部标记为已读"}


@router.delete("/{warning_id}", response_model=schemas.MessageResponse)
def delete_warning(
    warning_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除预警"""
    warning = db.query(models.HealthWarning).filter(
        models.HealthWarning.id == warning_id,
        models.HealthWarning.user_id == current_user.id
    ).first()
    
    if not warning:
        raise HTTPException(status_code=404, detail="预警不存在")
    
    db.delete(warning)
    db.commit()
    return {"message": "删除成功"}


@router.get("/stats", response_model=schemas.WarningStatsResponse)
def get_warning_stats(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取预警统计信息"""
    total = db.query(models.HealthWarning).filter(
        models.HealthWarning.user_id == current_user.id
    ).count()
    
    unread = db.query(models.HealthWarning).filter(
        models.HealthWarning.user_id == current_user.id,
        models.HealthWarning.is_read.is_(False)
    ).count()
    
    danger_count = db.query(models.HealthWarning).filter(
        models.HealthWarning.user_id == current_user.id,
        models.HealthWarning.warning_level == "danger",
        models.HealthWarning.is_read.is_(False)
    ).count()
    
    return {
        "total": total,
        "unread": unread,
        "danger": danger_count
    }
