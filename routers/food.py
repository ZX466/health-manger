from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from database import get_db
import models
import schemas
from auth import get_current_user, get_admin_user
from services.food_service import (
    create_food,
    get_foods,
    get_food,
    update_food,
    delete_food,
    create_food_record,
    get_food_records,
    get_food_stats,
)

router = APIRouter(prefix="/api/food", tags=["食物管理"])


@router.post("/foods", response_model=schemas.FoodResponse)
def create_food_endpoint(
    food: schemas.FoodCreate,
    admin_user: models.User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    return create_food(food, db)


@router.get("/foods", response_model=List[schemas.FoodResponse])
def get_foods_endpoint(
    category: Optional[str] = Query(None, max_length=50),
    search: Optional[str] = Query(None, min_length=1, max_length=100),
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


@router.get("/records", response_model=List[schemas.UserFoodRecordResponse])
def get_food_records_endpoint(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_food_records(current_user.id, db, start_date, end_date)


@router.get("/records/stats", response_model=dict)
def get_food_stats_endpoint(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_food_stats(current_user.id, db, start_date, end_date)
