from pydantic import BaseModel, Field, model_validator
from typing import Optional, Literal
from datetime import datetime


class UserBase(BaseModel):
    name: str


class UserCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=6, max_length=128)
    invite_code: str = Field(..., min_length=1, max_length=100)


class UserLogin(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1, max_length=128)


class UserResponse(BaseModel):
    id: int
    name: str
    created_at: datetime
    is_active: bool
    is_admin: bool = False

    class Config:
        from_attributes = True


class HealthRecordBase(BaseModel):
    height: Optional[float] = Field(None, gt=30, lt=300)
    weight: Optional[float] = Field(None, gt=1, lt=500)
    blood_pressure_systolic: Optional[int] = Field(None, gt=30, lt=300)
    blood_pressure_diastolic: Optional[int] = Field(None, gt=20, lt=200)
    heart_rate: Optional[int] = Field(None, gt=20, lt=300)
    temperature: Optional[float] = Field(None, gt=30, lt=45)
    vision_left: Optional[float] = Field(None, gt=0, le=5.0)
    vision_right: Optional[float] = Field(None, gt=0, le=5.0)
    exercise_frequency: Optional[Literal["none", "rare", "occasional", "regular", "daily"]] = None
    sleep_hours: Optional[float] = Field(None, ge=0, le=24)
    diet_habit: Optional[str] = Field(None, max_length=200)


class HealthRecordCreate(HealthRecordBase):
    pass


class HealthRecordResponse(HealthRecordBase):
    id: int
    user_id: int
    bmi: Optional[float] = None
    record_date: datetime

    class Config:
        from_attributes = True


class HealthAnalysisResponse(BaseModel):
    id: int
    user_id: int
    bmi_status: Optional[str] = None
    bmi_advice: Optional[str] = None
    blood_pressure_status: Optional[str] = None
    blood_pressure_advice: Optional[str] = None
    overall_status: Optional[str] = None
    overall_advice: Optional[str] = None
    health_rating: Optional[str] = None
    health_score: Optional[int] = None
    analysis_date: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    user_id: Optional[int] = None


class FoodBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    category: Optional[str] = Field(None, max_length=50)
    calories_per_100g: Optional[float] = Field(None, ge=0, le=10000)
    protein_per_100g: Optional[float] = Field(None, ge=0, le=1000)
    fat_per_100g: Optional[float] = Field(None, ge=0, le=1000)
    carbs_per_100g: Optional[float] = Field(None, ge=0, le=1000)
    fiber_per_100g: Optional[float] = Field(None, ge=0, le=1000)
    description: Optional[str] = Field(None, max_length=500)


class FoodCreate(FoodBase):
    pass


class FoodResponse(FoodBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class SportBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    category: Optional[str] = Field(None, max_length=50)
    calories_per_hour: Optional[float] = Field(None, ge=0, le=10000)
    intensity_level: Optional[Literal["low", "moderate", "high", "extreme"]] = None
    description: Optional[str] = Field(None, max_length=500)


class SportCreate(SportBase):
    pass


class SportResponse(SportBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class UserFoodRecordBase(BaseModel):
    food_id: int = Field(..., ge=1)
    quantity_grams: float = Field(..., gt=0, le=50000)
    meal_type: Optional[Literal["breakfast", "lunch", "dinner", "snack"]] = None


class UserFoodRecordCreate(UserFoodRecordBase):
    pass


class UserFoodRecordResponse(UserFoodRecordBase):
    id: int
    user_id: int
    calories: Optional[float] = None
    record_date: datetime
    food_name: Optional[str] = None

    class Config:
        from_attributes = True


class UserSportRecordBase(BaseModel):
    sport_id: int = Field(..., ge=1)
    duration_minutes: int = Field(..., gt=0, le=1440)
    notes: Optional[str] = Field(None, max_length=500)


class UserSportRecordCreate(UserSportRecordBase):
    pass


class UserSportRecordResponse(UserSportRecordBase):
    id: int
    user_id: int
    calories_burned: Optional[float] = None
    record_date: datetime
    sport_name: Optional[str] = None

    class Config:
        from_attributes = True


class HealthArticleBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    category: Optional[str] = Field(None, max_length=50)
    content: str = Field(..., min_length=1, max_length=50000)
    author: Optional[str] = Field(None, max_length=100)
    is_recommended: Optional[bool] = False


class HealthArticleCreate(HealthArticleBase):
    pass


class HealthArticleResponse(HealthArticleBase):
    id: int
    views: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class HealthWarningBase(BaseModel):
    warning_type: str = Field(..., max_length=50)
    warning_level: Literal["info", "warning", "danger", "critical"]
    warning_content: str = Field(..., min_length=1, max_length=1000)


class HealthWarningCreate(HealthWarningBase):
    pass


class HealthWarningResponse(HealthWarningBase):
    id: int
    user_id: int
    is_read: bool
    created_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AIAnalysisBase(BaseModel):
    request_content: str = Field(..., min_length=1, max_length=5000)
    analysis_type: Optional[str] = Field(None, max_length=50)


class AIAnalysisCreate(AIAnalysisBase):
    pass


class AIAnalysisResponse(AIAnalysisBase):
    id: int
    user_id: int
    response_content: str
    tokens_used: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class UserHealthGoalBase(BaseModel):
    goal_type: str = Field(..., min_length=1, max_length=50)
    target_value: Optional[float] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    @model_validator(mode='after')
    def validate_dates(self):
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValueError('start_date must be before end_date')
        return self


class UserHealthGoalCreate(UserHealthGoalBase):
    pass


class UserHealthGoalResponse(UserHealthGoalBase):
    id: int
    user_id: int
    current_value: Optional[float] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class TongueDiagnosisResponse(BaseModel):
    id: int
    user_id: int
    image_path: str
    tongue_color: Optional[str] = None
    coating_color: Optional[str] = None
    coating_thickness: Optional[str] = None
    has_cracks: Optional[bool] = None
    has_teeth_marks: Optional[bool] = None
    tongue_shape: Optional[str] = None
    moisture_level: Optional[str] = None
    tongue_spirit: Optional[str] = None
    overall_type: Optional[str] = None
    confidence_score: Optional[float] = Field(None, ge=0, le=1)
    tcm_syndrome: Optional[str] = None
    health_advice: Optional[str] = None
    diet_suggestion: Optional[str] = None
    lifestyle_advice: Optional[str] = None
    analysis_status: str
    created_at: datetime

    class Config:
        from_attributes = True


class ChatSessionCreate(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    context_type: Optional[Literal["general", "tongue", "health"]] = "general"


class ChatSessionResponse(BaseModel):
    id: int
    user_id: int
    title: Optional[str] = None
    context_type: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0

    class Config:
        from_attributes = True


class ChatMessageCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)


class ChatMessageResponse(BaseModel):
    id: int
    session_id: int
    role: str
    content: str
    tokens_used: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AsyncTaskStatus(BaseModel):
    task_id: str
    status: str
    result: Optional[dict] = None
    error: Optional[str] = None
    created_at: Optional[str] = None
    completed_at: Optional[str] = None


# ── Generic response schemas ──


class MessageResponse(BaseModel):
    message: str


class DeleteRecordResponse(BaseModel):
    message: str
    deleted_id: int


class HealthRatingResponse(BaseModel):
    rating: Optional[str] = None
    score: Optional[int] = None
    emoji: str = "❓"
    color: str = "#999999"
    bg_color: str = "#f5f5f5"
    bmi_status: Optional[str] = None
    blood_pressure_status: Optional[str] = None
    overall_status: Optional[str] = None
    overall_advice: Optional[str] = None
    analysis_date: Optional[datetime] = None


class SendMessageResponse(BaseModel):
    message: str
    response: str
    tokens_used: Optional[int] = None


class QuickAnalysisResponse(BaseModel):
    message: str
    analysis_id: int
    cached: bool = False


class HealthEvaluationResponse(BaseModel):
    message: str
    rule_score: Optional[int] = None
    rule_rating: Optional[str] = None
    llm_evaluation: str
    tokens_used: Optional[int] = None
    analysis_id: int
    cached: bool = False


class WarningStatsResponse(BaseModel):
    total: int
    unread: int
    danger: int


class TongueStatsResponse(BaseModel):
    total_records: int
    completed_records: int
    latest_syndrome: Optional[str] = None
    latest_overall_type: Optional[str] = None
    syndrome_distribution: dict


