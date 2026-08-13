from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from database import Base


def _utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    invite_code = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=_utcnow)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)

    health_records = relationship("HealthRecord", back_populates="user")
    health_analyses = relationship("HealthAnalysis", back_populates="user")
    food_records = relationship("UserFoodRecord", back_populates="user")
    sport_records = relationship("UserSportRecord", back_populates="user")


class HealthRecord(Base):
    __tablename__ = "health_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    height = Column(Float, nullable=True)
    weight = Column(Float, nullable=True)
    bmi = Column(Float, nullable=True)
    blood_pressure_systolic = Column(Integer, nullable=True)
    blood_pressure_diastolic = Column(Integer, nullable=True)
    heart_rate = Column(Integer, nullable=True)
    temperature = Column(Float, nullable=True)
    vision_left = Column(Float, nullable=True)
    vision_right = Column(Float, nullable=True)
    exercise_frequency = Column(String(50), nullable=True)
    sleep_hours = Column(Float, nullable=True)
    diet_habit = Column(Text, nullable=True)
    record_date = Column(DateTime, default=_utcnow)

    user = relationship("User", back_populates="health_records")


class HealthAnalysis(Base):
    __tablename__ = "health_analyses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    health_record_id = Column(Integer, ForeignKey("health_records.id"), nullable=True)
    bmi_status = Column(String(50), nullable=True)
    bmi_advice = Column(Text, nullable=True)
    blood_pressure_status = Column(String(50), nullable=True)
    blood_pressure_advice = Column(Text, nullable=True)
    overall_status = Column(String(50), nullable=True)
    overall_advice = Column(Text, nullable=True)
    health_rating = Column(String(20), nullable=True)
    health_score = Column(Integer, nullable=True)
    analysis_date = Column(DateTime, default=_utcnow)

    user = relationship("User", back_populates="health_analyses")


class Food(Base):
    __tablename__ = "foods"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    category = Column(String(50), nullable=True)
    calories_per_100g = Column(Float, nullable=True)
    protein_per_100g = Column(Float, nullable=True)
    fat_per_100g = Column(Float, nullable=True)
    carbs_per_100g = Column(Float, nullable=True)
    fiber_per_100g = Column(Float, nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow)

    user_records = relationship("UserFoodRecord", back_populates="food")


class Sport(Base):
    __tablename__ = "sports"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    category = Column(String(50), nullable=True)
    calories_per_hour = Column(Float, nullable=True)
    intensity_level = Column(String(20), nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow)

    user_records = relationship("UserSportRecord", back_populates="sport")


class UserFoodRecord(Base):
    __tablename__ = "user_food_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    food_id = Column(Integer, ForeignKey("foods.id"), nullable=False)
    quantity_grams = Column(Float, nullable=False)
    calories = Column(Float, nullable=True)
    record_date = Column(DateTime, default=_utcnow)
    meal_type = Column(String(20), nullable=True)

    user = relationship("User", back_populates="food_records")
    food = relationship("Food", back_populates="user_records")


class UserSportRecord(Base):
    __tablename__ = "user_sport_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    sport_id = Column(Integer, ForeignKey("sports.id"), nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    calories_burned = Column(Float, nullable=True)
    record_date = Column(DateTime, default=_utcnow)
    notes = Column(Text, nullable=True)

    user = relationship("User", back_populates="sport_records")
    sport = relationship("Sport", back_populates="user_records")


class HealthArticle(Base):
    __tablename__ = "health_articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, index=True)
    category = Column(String(50), nullable=True)
    content = Column(Text, nullable=False)
    author = Column(String(100), nullable=True)
    views = Column(Integer, default=0)
    is_recommended = Column(Boolean, default=False)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)


class HealthWarning(Base):
    __tablename__ = "health_warnings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    warning_type = Column(String(50), nullable=False)
    warning_level = Column(String(20), nullable=False)
    warning_content = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=_utcnow)
    resolved_at = Column(DateTime, nullable=True)

    user = relationship("User", backref="health_warnings")


class AIAnalysis(Base):
    __tablename__ = "ai_analyses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    request_content = Column(Text, nullable=False)
    response_content = Column(Text, nullable=False)
    analysis_type = Column(String(50), nullable=True)
    tokens_used = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=_utcnow)

    user = relationship("User", backref="ai_analyses")


class UserHealthGoal(Base):
    __tablename__ = "user_health_goals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    goal_type = Column(String(50), nullable=False)
    target_value = Column(Float, nullable=True)
    current_value = Column(Float, nullable=True)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=_utcnow)

    user = relationship("User", backref="health_goals")


class AIMetric(Base):
    __tablename__ = "ai_metrics"

    id = Column(Integer, primary_key=True, index=True)
    pipeline_type = Column(String(50), nullable=False)
    latency_ms = Column(Float, nullable=True)
    tokens_used = Column(Integer, nullable=True)
    success = Column(Boolean, default=True)
    error_type = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=_utcnow)


class TongueDiagnosis(Base):
    __tablename__ = "tongue_diagnoses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    image_path = Column(String(500), nullable=False)
    image_hash = Column(String(64), nullable=True)

    tongue_color = Column(String(50), nullable=True)
    coating_color = Column(String(50), nullable=True)
    coating_thickness = Column(String(30), nullable=True)
    has_cracks = Column(Boolean, nullable=True)
    has_teeth_marks = Column(Boolean, nullable=True)
    tongue_shape = Column(String(50), nullable=True)
    moisture_level = Column(String(30), nullable=True)

    tongue_spirit = Column(String(20), nullable=True)
    overall_type = Column(String(50), nullable=True)
    confidence_score = Column(Float, nullable=True)

    tcm_syndrome = Column(String(100), nullable=True)
    health_advice = Column(Text, nullable=True)
    diet_suggestion = Column(Text, nullable=True)
    lifestyle_advice = Column(Text, nullable=True)

    analysis_status = Column(String(20), default="pending")
    created_at = Column(DateTime, default=_utcnow)

    user = relationship("User", backref="tongue_diagnoses")


