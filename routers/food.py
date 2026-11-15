from datetime import date

from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.orm import Session

import models
import schemas
from auth import get_admin_user, get_current_user
from database import get_db
from routers._uploads import read_image_upload
from services.food_service import (
    create_food,
    create_food_record,
    delete_food,
    delete_food_record,
    get_food,
    get_food_records,
    get_food_stats,
    get_foods,
    update_food,
)
from services.security_service import check_rate_limit

router = APIRouter(prefix="/api/food", tags=["食物管理"])

RECOGNIZE_RATE_LIMIT = 10
RECOGNIZE_RATE_WINDOW_SECONDS = 60


@router.post("/foods", response_model=schemas.FoodResponse)
def create_food_endpoint(
    food: schemas.FoodCreate,
    admin_user: models.User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    return create_food(food, db)


@router.get("/foods", response_model=list[schemas.FoodResponse])
def get_foods_endpoint(
    category: str | None = Query(None, max_length=50),
    search: str | None = Query(None, min_length=0, max_length=100),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_foods(category, search, db)


@router.get("/foods/{food_id}", response_model=schemas.FoodResponse)
def get_food_endpoint(
    food_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_food(food_id, db)


@router.put("/foods/{food_id}", response_model=schemas.FoodResponse)
def update_food_endpoint(
    food_id: int,
    food: schemas.FoodCreate,
    admin_user: models.User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    return update_food(food_id, food, db)


@router.delete("/foods/{food_id}", response_model=schemas.MessageResponse)
def delete_food_endpoint(
    food_id: int,
    admin_user: models.User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    return delete_food(food_id, db)


@router.post("/records", response_model=schemas.UserFoodRecordResponse)
def create_food_record_endpoint(
    record: schemas.UserFoodRecordCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return create_food_record(record, current_user.id, db)


@router.get("/records", response_model=list[schemas.UserFoodRecordResponse])
def get_food_records_endpoint(
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_food_records(current_user.id, db, start_date, end_date)


@router.get("/records/stats", response_model=dict)
def get_food_stats_endpoint(
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_food_stats(current_user.id, db, start_date, end_date)


@router.delete("/records/{record_id}", response_model=schemas.MessageResponse)
def delete_food_record_endpoint(
    record_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return delete_food_record(record_id, current_user.id, db)


@router.post("/recognize", response_model=schemas.FoodRecognizeResponse)
async def recognize_meal_endpoint(
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """拍照识餐：只返回草稿，不写库；确认后走 /custom + /records。"""
    check_rate_limit(
        f"food_recognize:{current_user.id}",
        RECOGNIZE_RATE_LIMIT,
        RECOGNIZE_RATE_WINDOW_SECONDS,
    )
    raw = await read_image_upload(file)
    from services.food_recognition_service import arecognize_meal

    return await arecognize_meal(db, current_user.id, raw)


@router.post("/custom", response_model=schemas.FoodResponse)
def create_custom_food_endpoint(
    payload: schemas.FoodCustomCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """用户确认识别结果后创建自定义食物，description 固定 AI 估算前缀。"""
    food = schemas.FoodCreate(
        **payload.model_dump(),
        description="[AI估算] 由拍照识餐确认创建",
    )
    return create_food(food, db)
