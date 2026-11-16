"""填充三位演示用户及其健康、饮食、运动和心理数据。

用法：
    uv run python scripts/seed_demo_users.py

脚本只清理 invite_code=DEMO2026 的演示账号；不会删除真实用户。
"""

import os
import sys
from datetime import date, datetime, time, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv

load_dotenv()

import chat_session  # 注册 chat_sessions / chat_messages 表
import models
import schemas
from auth import get_password_hash
from database import Base, SessionLocal, engine
from services.health_record_service import create_record
from services.mental_service import save_assessment, upsert_mood

DEMO_CODE = "DEMO2026"
DEMO_PASSWORD = "demo1234"
TODAY = datetime.now().date()  # 演示数据按本地日历日生成


def _days_ago(days: int) -> date:
    return TODAY - timedelta(days=days)


def _at(day: date, hour: int = 12, minute: int = 0) -> datetime:
    return datetime.combine(day, time(hour, minute))


def _cleanup_demo_users(db) -> None:
    demo_users = db.query(models.User).filter(models.User.invite_code == DEMO_CODE).all()
    for user in demo_users:
        sessions = db.query(chat_session.ChatSession).filter_by(user_id=user.id).all()
        for session in sessions:
            db.delete(session)
        for model in (
            models.HealthAnalysis,
            models.HealthRecord,
            models.UserFoodRecord,
            models.UserSportRecord,
            models.HealthWarning,
            models.AIAnalysis,
            models.UserHealthGoal,
            models.TongueDiagnosis,
            models.AIConfig,
            models.MentalRecord,
            models.ScaleAssessment,
        ):
            db.query(model).filter_by(user_id=user.id).delete(synchronize_session=False)
        db.delete(user)
    db.commit()


def _ensure_food(db, name: str, **values):
    food = db.query(models.Food).filter_by(name=name).first()
    if food is None:
        food = models.Food(name=name, **values)
        db.add(food)
        db.commit()
        db.refresh(food)
    return food


def _ensure_sport(db, name: str, **values):
    sport = db.query(models.Sport).filter_by(name=name).first()
    if sport is None:
        sport = models.Sport(name=name, **values)
        db.add(sport)
        db.commit()
        db.refresh(sport)
    return sport


def _add_health(db, user, values: dict, day: date) -> None:
    record = create_record(schemas.HealthRecordCreate(**values), user.id, db)
    recorded_at = _at(day, 9)
    record.record_date = recorded_at
    analysis = (
        db.query(models.HealthAnalysis)
        .filter_by(health_record_id=record.id)
        .order_by(models.HealthAnalysis.id.desc())
        .first()
    )
    if analysis:
        analysis.analysis_date = recorded_at
    db.commit()


def _add_food(db, user, food, grams: float, meal: str, day: date, hour: int) -> None:
    db.add(
        models.UserFoodRecord(
            user_id=user.id,
            food_id=food.id,
            quantity_grams=grams,
            calories=(food.calories_per_100g or 0) * grams / 100,
            meal_type=meal,
            record_date=_at(day, hour),
        )
    )


def _add_sport(db, user, sport, minutes: int, day: date, hour: int, notes: str) -> None:
    db.add(
        models.UserSportRecord(
            user_id=user.id,
            sport_id=sport.id,
            duration_minutes=minutes,
            calories_burned=(sport.calories_per_hour or 0) * minutes / 60,
            notes=notes,
            record_date=_at(day, hour),
        )
    )


def _add_mood(db, user, day: date, mood: int, sleep: float, tags: list[str], note: str) -> None:
    upsert_mood(
        db,
        user.id,
        mood_score=mood,
        stress_tags=tags,
        sleep_hours=sleep,
        note=note,
        today=day,
    )


def _add_scale(db, user, scale_type: str, answers: list[int], day: date) -> None:
    assessment, _ = save_assessment(db, user.id, scale_type, answers)
    assessment.created_at = _at(day, 20)
    db.commit()


def _create_user(db, name: str):
    existing = db.query(models.User).filter_by(name=name).first()
    if existing is not None:
        raise RuntimeError(f"用户名 {name!r} 已被非演示账号占用，请先处理后再运行")
    user = models.User(
        name=name,
        password_hash=get_password_hash(DEMO_PASSWORD),
        invite_code=DEMO_CODE,
        is_active=True,
        is_admin=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def seed() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        _cleanup_demo_users(db)

        # 基础食物 / 运动数据（若 init_data.py 已执行会自动复用）
        rice = _ensure_food(
            db,
            "米饭",
            category="主食",
            calories_per_100g=116,
            protein_per_100g=2.6,
            carbs_per_100g=25.9,
        )
        noodles = _ensure_food(
            db,
            "面条",
            category="主食",
            calories_per_100g=110,
            protein_per_100g=2.7,
            carbs_per_100g=24.3,
        )
        egg = _ensure_food(
            db,
            "鸡蛋",
            category="蛋类",
            calories_per_100g=144,
            protein_per_100g=13.0,
            fat_per_100g=9.9,
        )
        chicken = _ensure_food(
            db,
            "鸡胸肉",
            category="肉类",
            calories_per_100g=118,
            protein_per_100g=24.6,
            fat_per_100g=1.2,
        )
        beef = _ensure_food(
            db,
            "牛肉",
            category="肉类",
            calories_per_100g=250,
            protein_per_100g=20.0,
            fat_per_100g=18.0,
        )
        milk = _ensure_food(
            db,
            "牛奶",
            category="奶制品",
            calories_per_100g=54,
            protein_per_100g=3.0,
            carbs_per_100g=5.0,
        )
        yogurt = _ensure_food(
            db,
            "酸奶",
            category="奶制品",
            calories_per_100g=72,
            protein_per_100g=3.0,
            carbs_per_100g=10.0,
        )
        apple = _ensure_food(
            db,
            "苹果",
            category="水果",
            calories_per_100g=52,
            protein_per_100g=0.3,
            carbs_per_100g=14.0,
        )
        banana = _ensure_food(
            db,
            "香蕉",
            category="水果",
            calories_per_100g=89,
            protein_per_100g=1.1,
            carbs_per_100g=23.0,
        )
        broccoli = _ensure_food(
            db,
            "西兰花",
            category="蔬菜",
            calories_per_100g=34,
            protein_per_100g=2.8,
            carbs_per_100g=7.0,
        )
        tomato = _ensure_food(
            db,
            "西红柿",
            category="蔬菜",
            calories_per_100g=18,
            protein_per_100g=0.9,
            carbs_per_100g=3.9,
        )

        run = _ensure_sport(
            db, "跑步", category="有氧运动", calories_per_hour=600, intensity_level="高强度"
        )
        walk = _ensure_sport(
            db, "快走", category="有氧运动", calories_per_hour=300, intensity_level="低强度"
        )
        strength = _ensure_sport(
            db, "力量训练", category="力量训练", calories_per_hour=300, intensity_level="中等强度"
        )
        yoga = _ensure_sport(
            db, "瑜伽", category="室内运动", calories_per_hour=200, intensity_level="低强度"
        )
        basketball = _ensure_sport(
            db, "篮球", category="球类运动", calories_per_hour=450, intensity_level="高强度"
        )

        # ── 小林：熬夜、睡眠不足、轻度情绪低落 ─────────────────────────
        xiaolin = _create_user(db, "小林")
        _add_health(
            db,
            xiaolin,
            {
                "height": 165,
                "weight": 53,
                "blood_pressure_systolic": 110,
                "blood_pressure_diastolic": 70,
                "heart_rate": 78,
                "temperature": 36.6,
                "vision_left": 4.8,
                "vision_right": 4.9,
                "exercise_frequency": "rare",
                "sleep_hours": 5.5,
                "diet_habit": "外卖多，早餐不规律",
            },
            _days_ago(14),
        )
        _add_health(
            db,
            xiaolin,
            {
                "height": 165,
                "weight": 52,
                "blood_pressure_systolic": 108,
                "blood_pressure_diastolic": 68,
                "heart_rate": 76,
                "temperature": 36.5,
                "vision_left": 4.8,
                "vision_right": 4.9,
                "exercise_frequency": "rare",
                "sleep_hours": 5.0,
                "diet_habit": "外卖多，早餐不规律",
            },
            _days_ago(1),
        )
        for day, mood, sleep, tags, note in [
            (_days_ago(6), 2, 5.0, ["学业", "睡眠"], "赶作业到凌晨两点。"),
            (_days_ago(5), 2, 5.5, ["睡眠"], "早上起不来，白天没精神。"),
            (_days_ago(4), 3, 6.0, ["学业"], "今天稍微好一点。"),
            (_days_ago(3), 2, 5.0, ["睡眠", "学业"], "又熬夜了。"),
            (_days_ago(2), 3, 6.5, ["睡眠"], "比前几天早睡了一点。"),
            (_days_ago(1), 3, 7.0, ["学业"], "和朋友聊了聊，轻松一些。"),
            (TODAY, 4, 6.0, [], "今天状态还可以。"),
        ]:
            _add_mood(db, xiaolin, day, mood, sleep, tags, note)
        _add_scale(db, xiaolin, "phq9", [1, 1, 1, 1, 1, 1, 1, 0, 0], _days_ago(3))
        _add_scale(db, xiaolin, "gad7", [1, 1, 0, 1, 0, 0, 0], _days_ago(3))
        _add_food(db, xiaolin, noodles, 250, "lunch", _days_ago(2), 12)
        _add_food(db, xiaolin, egg, 50, "lunch", _days_ago(2), 12)
        _add_food(db, xiaolin, rice, 200, "dinner", _days_ago(2), 19)
        _add_food(db, xiaolin, chicken, 120, "dinner", _days_ago(2), 19)
        _add_food(db, xiaolin, milk, 250, "breakfast", _days_ago(1), 9)
        _add_food(db, xiaolin, rice, 180, "lunch", _days_ago(1), 12)
        _add_food(db, xiaolin, tomato, 150, "lunch", _days_ago(1), 12)
        _add_food(db, xiaolin, banana, 100, "snack", _days_ago(1), 16)
        _add_food(db, xiaolin, rice, 200, "dinner", TODAY, 19)
        _add_food(db, xiaolin, beef, 100, "dinner", TODAY, 19)
        _add_sport(db, xiaolin, yoga, 20, _days_ago(2), 21, "睡前拉伸")

        # ── 阿哲：考研压力、危机标记、血压偏高 ─────────────────────────
        azhe = _create_user(db, "阿哲")
        _add_health(
            db,
            azhe,
            {
                "height": 178,
                "weight": 71,
                "blood_pressure_systolic": 138,
                "blood_pressure_diastolic": 88,
                "heart_rate": 82,
                "temperature": 36.5,
                "vision_left": 4.6,
                "vision_right": 4.7,
                "exercise_frequency": "occasional",
                "sleep_hours": 6.0,
                "diet_habit": "备考期间外卖和咖啡较多",
            },
            _days_ago(14),
        )
        _add_health(
            db,
            azhe,
            {
                "height": 178,
                "weight": 72,
                "blood_pressure_systolic": 145,
                "blood_pressure_diastolic": 92,
                "heart_rate": 88,
                "temperature": 36.6,
                "vision_left": 4.6,
                "vision_right": 4.7,
                "exercise_frequency": "occasional",
                "sleep_hours": 5.0,
                "diet_habit": "备考期间外卖和咖啡较多",
            },
            _days_ago(1),
        )
        for day, mood, sleep, tags, note in [
            (_days_ago(6), 2, 5.0, ["考研", "焦虑"], "一整天都在担心复习进度。"),
            (_days_ago(5), 1, 4.5, ["考研", "失眠"], "凌晨三点还醒着。"),
            (_days_ago(4), 2, 5.5, ["焦虑"], "看不进去书，胸口发紧。"),
            (_days_ago(3), 2, 4.0, ["考研", "失眠"], "睡得很浅，反复醒来。"),
            (_days_ago(2), 1, 5.0, ["焦虑", "考研"], "觉得怎么努力都不够。"),
            (_days_ago(1), 2, 4.5, ["失眠"], "不想说话，只想一个人待着。"),
            (TODAY, 2, 5.0, ["考研", "焦虑"], "今天也很难集中注意力。"),
        ]:
            _add_mood(db, azhe, day, mood, sleep, tags, note)
        _add_scale(db, azhe, "phq9", [2, 2, 2, 1, 2, 2, 1, 1, 1], _days_ago(14))
        _add_scale(db, azhe, "phq9", [2, 2, 2, 2, 2, 2, 2, 1, 1], _days_ago(1))
        _add_scale(db, azhe, "gad7", [2, 2, 2, 2, 1, 2, 2], _days_ago(1))
        _add_food(db, azhe, noodles, 300, "lunch", _days_ago(1), 13)
        _add_food(db, azhe, egg, 50, "lunch", _days_ago(1), 13)
        _add_food(db, azhe, rice, 180, "dinner", _days_ago(1), 20)
        _add_food(db, azhe, beef, 120, "dinner", _days_ago(1), 20)
        _add_food(db, azhe, yogurt, 150, "snack", TODAY, 16)
        _add_sport(db, azhe, walk, 25, _days_ago(1), 18, "饭后走一走")

        # ── 小周：规律健身、饮食控制、状态稳定 ─────────────────────────
        xiaozhou = _create_user(db, "小周")
        _add_health(
            db,
            xiaozhou,
            {
                "height": 175,
                "weight": 69,
                "blood_pressure_systolic": 115,
                "blood_pressure_diastolic": 72,
                "heart_rate": 64,
                "temperature": 36.5,
                "vision_left": 5.0,
                "vision_right": 5.0,
                "exercise_frequency": "regular",
                "sleep_hours": 7.0,
                "diet_habit": "高蛋白、规律三餐",
            },
            _days_ago(14),
        )
        _add_health(
            db,
            xiaozhou,
            {
                "height": 175,
                "weight": 68,
                "blood_pressure_systolic": 112,
                "blood_pressure_diastolic": 70,
                "heart_rate": 62,
                "temperature": 36.4,
                "vision_left": 5.0,
                "vision_right": 5.0,
                "exercise_frequency": "daily",
                "sleep_hours": 7.5,
                "diet_habit": "高蛋白、规律三餐",
            },
            _days_ago(1),
        )
        for day, mood, sleep, tags, note in [
            (_days_ago(6), 4, 7.5, ["训练"], "今天练了腿，状态不错。"),
            (_days_ago(5), 4, 7.0, ["饮食"], "三餐按计划吃完了。"),
            (_days_ago(4), 5, 8.0, ["训练"], "睡得很足，精神很好。"),
            (_days_ago(3), 4, 7.5, ["训练"], "篮球打得有点累。"),
            (_days_ago(2), 5, 8.0, [], "休息日，心情不错。"),
            (_days_ago(1), 4, 7.0, ["饮食"], "蛋白质吃够了。"),
            (TODAY, 5, 7.5, ["训练"], "准备晚上去跑步。"),
        ]:
            _add_mood(db, xiaozhou, day, mood, sleep, tags, note)
        _add_scale(db, xiaozhou, "phq9", [0, 0, 0, 0, 1, 0, 0, 0, 0], _days_ago(2))
        _add_scale(db, xiaozhou, "gad7", [0, 0, 0, 0, 0, 0, 0], _days_ago(2))
        for offset in range(7):
            day = _days_ago(offset)
            _add_food(db, xiaozhou, milk, 250, "breakfast", day, 8)
            _add_food(db, xiaozhou, egg, 100, "breakfast", day, 8)
            _add_food(db, xiaozhou, apple, 150, "breakfast", day, 8)
            _add_food(db, xiaozhou, rice, 200, "lunch", day, 12)
            _add_food(db, xiaozhou, chicken, 180, "lunch", day, 12)
            _add_food(db, xiaozhou, broccoli, 200, "lunch", day, 12)
            _add_food(db, xiaozhou, rice, 180, "dinner", day, 19)
            _add_food(db, xiaozhou, beef, 120, "dinner", day, 19)
            _add_food(db, xiaozhou, tomato, 150, "dinner", day, 19)
        _add_sport(db, xiaozhou, run, 30, _days_ago(6), 18, "慢跑 5 公里")
        _add_sport(db, xiaozhou, strength, 45, _days_ago(4), 19, "上肢力量")
        _add_sport(db, xiaozhou, basketball, 60, _days_ago(3), 17, "和同学打球")
        _add_sport(db, xiaozhou, run, 25, _days_ago(1), 18, "轻松跑")
        _add_sport(db, xiaozhou, strength, 50, TODAY, 19, "腿部和核心")

        db.commit()
        print("演示数据已写入：")
        print(f"  小林 / {DEMO_PASSWORD}")
        print(f"  阿哲 / {DEMO_PASSWORD}")
        print(f"  小周 / {DEMO_PASSWORD}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
