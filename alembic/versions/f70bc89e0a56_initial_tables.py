"""initial tables

Revision ID: f70bc89e0a56
Revises:
Create Date: 2026-05-04 11:15:15.506261

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f70bc89e0a56'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all application tables."""
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('invite_code', sa.String(50), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
    )
    op.create_table(
        'health_records',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('height', sa.Float(), nullable=True),
        sa.Column('weight', sa.Float(), nullable=True),
        sa.Column('bmi', sa.Float(), nullable=True),
        sa.Column('blood_pressure_systolic', sa.Integer(), nullable=True),
        sa.Column('blood_pressure_diastolic', sa.Integer(), nullable=True),
        sa.Column('heart_rate', sa.Integer(), nullable=True),
        sa.Column('temperature', sa.Float(), nullable=True),
        sa.Column('vision_left', sa.Float(), nullable=True),
        sa.Column('vision_right', sa.Float(), nullable=True),
        sa.Column('exercise_frequency', sa.String(50), nullable=True),
        sa.Column('sleep_hours', sa.Float(), nullable=True),
        sa.Column('diet_habit', sa.Text(), nullable=True),
        sa.Column('record_date', sa.DateTime(), nullable=True),
    )
    op.create_table(
        'health_analyses',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('health_record_id', sa.Integer(), sa.ForeignKey('health_records.id'), nullable=True),
        sa.Column('bmi_status', sa.String(50), nullable=True),
        sa.Column('bmi_advice', sa.Text(), nullable=True),
        sa.Column('blood_pressure_status', sa.String(50), nullable=True),
        sa.Column('blood_pressure_advice', sa.Text(), nullable=True),
        sa.Column('overall_status', sa.String(50), nullable=True),
        sa.Column('overall_advice', sa.Text(), nullable=True),
        sa.Column('health_rating', sa.String(20), nullable=True),
        sa.Column('health_score', sa.Integer(), nullable=True),
        sa.Column('analysis_date', sa.DateTime(), nullable=True),
    )
    op.create_table(
        'foods',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('category', sa.String(50), nullable=True),
        sa.Column('calories_per_100g', sa.Float(), nullable=True),
        sa.Column('protein_per_100g', sa.Float(), nullable=True),
        sa.Column('fat_per_100g', sa.Float(), nullable=True),
        sa.Column('carbs_per_100g', sa.Float(), nullable=True),
        sa.Column('fiber_per_100g', sa.Float(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )
    op.create_table(
        'sports',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('category', sa.String(50), nullable=True),
        sa.Column('calories_per_hour', sa.Float(), nullable=True),
        sa.Column('intensity_level', sa.String(20), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )
    op.create_table(
        'user_food_records',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('food_id', sa.Integer(), sa.ForeignKey('foods.id'), nullable=False),
        sa.Column('quantity_grams', sa.Float(), nullable=False),
        sa.Column('calories', sa.Float(), nullable=True),
        sa.Column('record_date', sa.DateTime(), nullable=True),
        sa.Column('meal_type', sa.String(20), nullable=True),
    )
    op.create_table(
        'user_sport_records',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('sport_id', sa.Integer(), sa.ForeignKey('sports.id'), nullable=False),
        sa.Column('duration_minutes', sa.Integer(), nullable=False),
        sa.Column('calories_burned', sa.Float(), nullable=True),
        sa.Column('record_date', sa.DateTime(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
    )
    op.create_table(
        'health_articles',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('category', sa.String(50), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('author', sa.String(100), nullable=True),
        sa.Column('views', sa.Integer(), nullable=True),
        sa.Column('is_recommended', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )
    op.create_table(
        'health_warnings',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('warning_type', sa.String(50), nullable=False),
        sa.Column('warning_level', sa.String(20), nullable=False),
        sa.Column('warning_content', sa.Text(), nullable=False),
        sa.Column('is_read', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
    )
    op.create_table(
        'ai_analyses',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('request_content', sa.Text(), nullable=False),
        sa.Column('response_content', sa.Text(), nullable=False),
        sa.Column('analysis_type', sa.String(50), nullable=True),
        sa.Column('tokens_used', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )
    op.create_table(
        'user_health_goals',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('goal_type', sa.String(50), nullable=False),
        sa.Column('target_value', sa.Float(), nullable=True),
        sa.Column('current_value', sa.Float(), nullable=True),
        sa.Column('start_date', sa.DateTime(), nullable=True),
        sa.Column('end_date', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(20), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )
    op.create_table(
        'tongue_diagnoses',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('image_path', sa.String(500), nullable=False),
        sa.Column('image_hash', sa.String(64), nullable=True),
        sa.Column('tongue_color', sa.String(50), nullable=True),
        sa.Column('coating_color', sa.String(50), nullable=True),
        sa.Column('coating_thickness', sa.String(30), nullable=True),
        sa.Column('has_cracks', sa.Boolean(), nullable=True),
        sa.Column('has_teeth_marks', sa.Boolean(), nullable=True),
        sa.Column('tongue_shape', sa.String(50), nullable=True),
        sa.Column('moisture_level', sa.String(30), nullable=True),
        sa.Column('tongue_spirit', sa.String(20), nullable=True),
        sa.Column('overall_type', sa.String(50), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('tcm_syndrome', sa.String(100), nullable=True),
        sa.Column('health_advice', sa.Text(), nullable=True),
        sa.Column('diet_suggestion', sa.Text(), nullable=True),
        sa.Column('lifestyle_advice', sa.Text(), nullable=True),
        sa.Column('analysis_status', sa.String(20), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )
    op.create_table(
        'ai_metrics',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('pipeline_type', sa.String(50), nullable=False),
        sa.Column('latency_ms', sa.Float(), nullable=True),
        sa.Column('tokens_used', sa.Integer(), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=True),
        sa.Column('error_type', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    """Drop all application tables in reverse order."""
    for table_name in [
        'ai_metrics', 'tongue_diagnoses', 'user_health_goals',
        'ai_analyses', 'health_warnings', 'health_articles',
        'user_sport_records', 'user_food_records', 'sports',
        'foods', 'health_analyses', 'health_records', 'users',
    ]:
        op.drop_table(table_name)
