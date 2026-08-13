from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from database import get_db
import models
import schemas
from auth import verify_password, get_password_hash, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, get_current_user
from services.auth_service import validate_invite_code
from services.security_service import check_rate_limit

router = APIRouter(prefix="/api/auth", tags=["认证"])


@router.post("/register", response_model=schemas.UserResponse)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # S10: 不预查用户名存在性（避免用户名枚举），统一提示；重复名由唯一约束兜底
    if not validate_invite_code(user.invite_code):
        raise HTTPException(status_code=400, detail="注册失败，请检查邀请码与注册信息")

    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        name=user.name,
        password_hash=hashed_password,
        invite_code=user.invite_code
    )
    db.add(db_user)
    try:
        db.commit()
    except IntegrityError:
        # S13: 用户名唯一约束冲突（并发注册/重名）
        db.rollback()
        raise HTTPException(status_code=400, detail="注册失败，请检查邀请码与注册信息")
    db.refresh(db_user)
    return db_user


@router.post("/login", response_model=schemas.Token)
def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    client_ip = request.client.host if request.client else "unknown"
    check_rate_limit(
        f"login:{client_ip}:{form_data.username.strip().lower()}",
        max_requests=5,
        window_seconds=60,
    )
    user = db.query(models.User).filter(models.User.name == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=schemas.UserResponse)
def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user
