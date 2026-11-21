"""今日一件小事 API。"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

import models
import schemas
from auth import get_current_user
from database import get_db
from services.daily_action_service import (
    NOT_COMPLETABLE_DETAIL,
    DailyActionNotCompletableError,
    DailyActionNotFoundError,
    complete_daily_action,
    generate_daily_action,
)

router = APIRouter(prefix="/api/daily-action", tags=["今日一件小事"])

NOT_FOUND_DETAIL = "行动不存在"


@router.get("/today", response_model=schemas.DailyActionResponse)
def get_today_action(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return generate_daily_action(db, current_user.id)


@router.post("/{action_id}/complete", response_model=schemas.DailyActionResponse)
def complete_action(
    action_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    try:
        return complete_daily_action(db, current_user.id, action_id)
    except DailyActionNotFoundError:
        # 全局 404 处理器会改写 detail，这里直接返回响应以保留契约文案。
        return JSONResponse(status_code=404, content={"detail": NOT_FOUND_DETAIL})
    except DailyActionNotCompletableError:
        raise HTTPException(status_code=400, detail=NOT_COMPLETABLE_DETAIL)
