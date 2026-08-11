from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from database import get_db
import models
import schemas
from auth import get_current_user, get_admin_user
from services.sport_service import (
    create_sport,
    get_sports,
    get_sport,
    update_sport,
    delete_sport,
    create_sport_record,
    get_sport_records,
    get_sport_stats,
)

router = APIRouter(prefix="/api/sport", tags=["运动管理"])


@router.post("/sports", response_model=schemas.SportResponse)
def create_sport_endpoint(
    sport: schemas.SportCreate,
    admin_user: models.User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    return create_sport(sport, db)


@router.get("/sports", response_model=List[schemas.SportResponse])
def get_sports_endpoint(
    category: Optional[str] = Query(None, max_length=50),
    search: Optional[str] = Query(None, min_length=1, max_length=100),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_sports(category, search, db)


@router.get("/sports/{sport_id}", response_model=schemas.SportResponse)
def get_sport_endpoint(
    sport_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_sport(sport_id, db)


@router.put("/sports/{sport_id}", response_model=schemas.SportResponse)
def update_sport_endpoint(
    sport_id: int,
    sport: schemas.SportCreate,
    admin_user: models.User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    return update_sport(sport_id, sport, db)


@router.delete("/sports/{sport_id}", response_model=schemas.MessageResponse)
def delete_sport_endpoint(
    sport_id: int,
    admin_user: models.User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    return delete_sport(sport_id, db)


@router.post("/records", response_model=schemas.UserSportRecordResponse)
def create_sport_record_endpoint(
    record: schemas.UserSportRecordCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return create_sport_record(record, current_user.id, db)


@router.get("/records", response_model=List[schemas.UserSportRecordResponse])
def get_sport_records_endpoint(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_sport_records(current_user.id, db, start_date, end_date)


@router.get("/records/stats", response_model=dict)
def get_sport_stats_endpoint(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_sport_stats(current_user.id, db, start_date, end_date)
