from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator


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
    height: float | None = Field(None, gt=30, lt=300)
    weight: float | None = Field(None, gt=1, lt=500)
    blood_pressure_systolic: int | None = Field(None, gt=30, lt=300)
    blood_pressure_diastolic: int | None = Field(None, gt=20, lt=200)
    heart_rate: int | None = Field(None, gt=20, lt=300)
    temperature: float | None = Field(None, gt=30, lt=45)
    vision_left: float | None = Field(None, gt=0, le=5.0)
    vision_right: float | None = Field(None, gt=0, le=5.0)
    exercise_frequency: Literal["none", "rare", "occasional", "regular", "daily"] | None = None
    sleep_hours: float | None = Field(None, ge=0, le=24)
    diet_habit: str | None = Field(None, max_length=200)


class HealthRecordCreate(HealthRecordBase):
    pass


class HealthRecordResponse(HealthRecordBase):
    id: int
    user_id: int
    bmi: float | None = None
    record_date: datetime

    class Config:
        from_attributes = True


class HealthAnalysisResponse(BaseModel):
    id: int
    user_id: int
    bmi_status: str | None = None
    bmi_advice: str | None = None
    blood_pressure_status: str | None = None
    blood_pressure_advice: str | None = None
    overall_status: str | None = None
    overall_advice: str | None = None
    health_rating: str | None = None
    health_score: int | None = None
    analysis_date: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    user_id: int | None = None


class FoodBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    category: str | None = Field(None, max_length=50)
    calories_per_100g: float | None = Field(None, ge=0, le=10000)
    protein_per_100g: float | None = Field(None, ge=0, le=1000)
    fat_per_100g: float | None = Field(None, ge=0, le=1000)
    carbs_per_100g: float | None = Field(None, ge=0, le=1000)
    fiber_per_100g: float | None = Field(None, ge=0, le=1000)
    description: str | None = Field(None, max_length=500)


class FoodCreate(FoodBase):
    pass


class FoodResponse(FoodBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class SportBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    category: str | None = Field(None, max_length=50)
    calories_per_hour: float | None = Field(None, ge=0, le=10000)
    intensity_level: Literal["low", "moderate", "high", "extreme"] | None = None
    description: str | None = Field(None, max_length=500)


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
    meal_type: Literal["breakfast", "lunch", "dinner", "snack"] | None = None


class UserFoodRecordCreate(UserFoodRecordBase):
    pass


class UserFoodRecordResponse(UserFoodRecordBase):
    id: int
    user_id: int
    calories: float | None = None
    record_date: datetime
    food_name: str | None = None

    class Config:
        from_attributes = True


class UserSportRecordBase(BaseModel):
    sport_id: int = Field(..., ge=1)
    duration_minutes: int = Field(..., gt=0, le=1440)
    notes: str | None = Field(None, max_length=500)


class UserSportRecordCreate(UserSportRecordBase):
    pass


class UserSportRecordResponse(UserSportRecordBase):
    id: int
    user_id: int
    calories_burned: float | None = None
    record_date: datetime
    sport_name: str | None = None

    class Config:
        from_attributes = True


class HealthArticleBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    category: str | None = Field(None, max_length=50)
    content: str = Field(..., min_length=1, max_length=50000)
    author: str | None = Field(None, max_length=100)
    is_recommended: bool | None = False


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
    resolved_at: datetime | None = None

    class Config:
        from_attributes = True


class AIAnalysisBase(BaseModel):
    request_content: str = Field(..., min_length=1, max_length=5000)
    analysis_type: str | None = Field(None, max_length=50)


class AIAnalysisCreate(AIAnalysisBase):
    pass


class AIAnalysisResponse(AIAnalysisBase):
    id: int
    user_id: int
    response_content: str
    tokens_used: int | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class UserHealthGoalBase(BaseModel):
    goal_type: str = Field(..., min_length=1, max_length=50)
    target_value: float | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None

    @model_validator(mode="after")
    def validate_dates(self):
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValueError("start_date must be before end_date")
        return self


class UserHealthGoalCreate(UserHealthGoalBase):
    pass


class UserHealthGoalResponse(UserHealthGoalBase):
    id: int
    user_id: int
    current_value: float | None = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class TongueDiagnosisResponse(BaseModel):
    id: int
    user_id: int
    image_path: str
    tongue_color: str | None = None
    coating_color: str | None = None
    coating_thickness: str | None = None
    has_cracks: bool | None = None
    has_teeth_marks: bool | None = None
    tongue_shape: str | None = None
    moisture_level: str | None = None
    tongue_spirit: str | None = None
    overall_type: str | None = None
    confidence_score: float | None = Field(None, ge=0, le=1)
    tcm_syndrome: str | None = None
    health_advice: str | None = None
    diet_suggestion: str | None = None
    lifestyle_advice: str | None = None
    analysis_status: str
    created_at: datetime

    class Config:
        from_attributes = True


class ChatSessionCreate(BaseModel):
    title: str | None = Field(None, max_length=200)
    context_type: Literal["general", "tongue", "health"] | None = "general"


class ChatSessionResponse(BaseModel):
    id: int
    user_id: int
    title: str | None = None
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
    tokens_used: int | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class AsyncTaskStatus(BaseModel):
    task_id: str
    status: str
    result: dict | None = None
    error: str | None = None
    created_at: str | None = None
    completed_at: str | None = None


# ── Generic response schemas ──


class MessageResponse(BaseModel):
    message: str


class DeleteRecordResponse(BaseModel):
    message: str
    deleted_id: int


class HealthRatingResponse(BaseModel):
    rating: str | None = None
    score: int | None = None
    emoji: str = "❓"
    color: str = "#999999"
    bg_color: str = "#f5f5f5"
    bmi_status: str | None = None
    blood_pressure_status: str | None = None
    overall_status: str | None = None
    overall_advice: str | None = None
    analysis_date: datetime | None = None


class SendMessageResponse(BaseModel):
    message: str
    response: str
    tokens_used: int | None = None


class QuickAnalysisResponse(BaseModel):
    message: str
    analysis_id: int
    cached: bool = False


class HealthEvaluationResponse(BaseModel):
    message: str
    rule_score: int | None = None
    rule_rating: str | None = None
    llm_evaluation: str
    tokens_used: int | None = None
    analysis_id: int
    cached: bool = False


class WarningStatsResponse(BaseModel):
    total: int
    unread: int
    danger: int


class AIConfigUpdate(BaseModel):
    # 聊天/分析模型
    provider: Literal["zhipu", "openai", "ark"] = "zhipu"
    model: str = Field(..., min_length=1, max_length=100)
    base_url: str | None = Field(None, max_length=500)
    api_key: str | None = Field(None, min_length=1, max_length=500)
    # 舌诊视觉模型
    vision_provider: Literal["zhipu", "openai", "ark"] | None = None
    vision_model: str | None = Field(None, max_length=100)
    vision_base_url: str | None = Field(None, max_length=500)
    vision_api_key: str | None = Field(None, min_length=1, max_length=500)


class AIConfigResponse(BaseModel):
    provider: str
    model: str
    base_url: str | None = None
    api_key_masked: str = ""
    has_api_key: bool = False
    # 舌诊视觉模型
    vision_provider: str | None = None
    vision_model: str | None = None
    vision_base_url: str | None = None
    vision_api_key_masked: str = ""
    has_vision_api_key: bool = False


class AIConfigTestResponse(BaseModel):
    success: bool
    message: str
    model: str | None = None


class TongueStatsResponse(BaseModel):
    total_records: int
    completed_records: int
    latest_syndrome: str | None = None
    latest_overall_type: str | None = None
    syndrome_distribution: dict
