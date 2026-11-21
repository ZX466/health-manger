"""健康周报聚合服务。

只读取既有业务表，不新增存储：
- 体检记录提供睡眠/体重，心理打卡在体检缺睡眠时兜底；
- 饮食/运动按自然日汇总；
- 健康评级取每天最新一条分析；
- 规则洞察只做生活方式提示，不做诊断，不开处方。
"""

import json
from collections import Counter
from datetime import date, datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

import models

WEEK_DAYS = 7
SLEEP_TARGET_HOURS = 8.0
SLEEP_MIN_DAYS = 4
SPORT_TARGET_MINUTES = 150

SAFETY_SUGGESTION = (
    "先联系学校心理咨询中心；如有危机想法，请立即拨打 120 或 12356。"
)


def _today() -> date:
    return datetime.now().date()


def _day_label(value: date) -> str:
    return f"{value.month}.{value.day}"


def _parse_tags(raw: str | None) -> list[str]:
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError):
        return []
    return [str(item) for item in parsed] if isinstance(parsed, list) else []


def _empty_day(day: date) -> dict:
    return {
        "date": day.isoformat(),
        "score": None,
        "sleep_hours": None,
        "mood_score": None,
        "calories_in": 0.0,
        "calories_burned": 0.0,
        "sport_minutes": 0,
        "has_data": False,
    }


def _window(end_date: date | None = None) -> tuple[date, date]:
    end = end_date or _today()
    return end - timedelta(days=WEEK_DAYS - 1), end


def build_weekly_report(
    db: Session, user_id: int, *, end_date: date | None = None
) -> dict:
    """构建近 7 天（含 end_date）的健康周报。"""
    start, end = _window(end_date)
    start_dt = datetime.combine(start, time.min)
    end_dt = datetime.combine(end, time.max)

    days = [start + timedelta(days=offset) for offset in range(WEEK_DAYS)]
    daily = {day: _empty_day(day) for day in days}
    food_days: set[date] = set()
    sport_days: set[date] = set()
    sleep_days: set[date] = set()
    mood_days: set[date] = set()
    tag_counter: Counter[str] = Counter()

    health_rows = (
        db.execute(
            select(models.HealthRecord)
            .where(
                models.HealthRecord.user_id == user_id,
                models.HealthRecord.record_date >= start_dt,
                models.HealthRecord.record_date <= end_dt,
            )
            .order_by(models.HealthRecord.record_date.asc(), models.HealthRecord.id.asc())
        )
        .scalars()
        .all()
    )
    for record in health_rows:
        if record.record_date is None:
            continue
        day = record.record_date.date()
        if day not in daily:
            continue
        daily[day]["has_data"] = True
        if record.sleep_hours is not None:
            daily[day]["sleep_hours"] = float(record.sleep_hours)
            sleep_days.add(day)

    mental_rows = (
        db.execute(
            select(models.MentalRecord)
            .where(
                models.MentalRecord.user_id == user_id,
                models.MentalRecord.record_date >= start,
                models.MentalRecord.record_date <= end,
            )
            .order_by(models.MentalRecord.record_date.asc())
        )
        .scalars()
        .all()
    )
    for record in mental_rows:
        day = record.record_date
        if day not in daily:
            continue
        daily[day]["has_data"] = True
        if record.mood_score is not None:
            daily[day]["mood_score"] = record.mood_score
            mood_days.add(day)
        # 体检没填睡眠时，用心理打卡的睡眠兜底，避免同一晚被算两次
        if record.sleep_hours is not None and daily[day]["sleep_hours"] is None:
            daily[day]["sleep_hours"] = float(record.sleep_hours)
            sleep_days.add(day)
        tag_counter.update(_parse_tags(record.stress_tags))

    food_rows = (
        db.execute(
            select(models.UserFoodRecord).where(
                models.UserFoodRecord.user_id == user_id,
                models.UserFoodRecord.record_date >= start_dt,
                models.UserFoodRecord.record_date <= end_dt,
            )
        )
        .scalars()
        .all()
    )
    for record in food_rows:
        if record.record_date is None:
            continue
        day = record.record_date.date()
        if day not in daily:
            continue
        daily[day]["calories_in"] = round(
            daily[day]["calories_in"] + float(record.calories or 0), 1
        )
        daily[day]["has_data"] = True
        food_days.add(day)

    sport_rows = (
        db.execute(
            select(models.UserSportRecord).where(
                models.UserSportRecord.user_id == user_id,
                models.UserSportRecord.record_date >= start_dt,
                models.UserSportRecord.record_date <= end_dt,
            )
        )
        .scalars()
        .all()
    )
    for record in sport_rows:
        if record.record_date is None:
            continue
        day = record.record_date.date()
        if day not in daily:
            continue
        daily[day]["calories_burned"] = round(
            daily[day]["calories_burned"] + float(record.calories_burned or 0), 1
        )
        daily[day]["sport_minutes"] += int(record.duration_minutes or 0)
        daily[day]["has_data"] = True
        sport_days.add(day)

    analysis_rows = (
        db.execute(
            select(models.HealthAnalysis)
            .where(
                models.HealthAnalysis.user_id == user_id,
                models.HealthAnalysis.analysis_date >= start_dt,
                models.HealthAnalysis.analysis_date <= end_dt,
            )
            .order_by(
                models.HealthAnalysis.analysis_date.asc(),
                models.HealthAnalysis.id.asc(),
            )
        )
        .scalars()
        .all()
    )
    for record in analysis_rows:
        if record.analysis_date is None:
            continue
        day = record.analysis_date.date()
        if day in daily and record.health_score is not None:
            daily[day]["score"] = int(record.health_score)

    warnings = (
        db.execute(
            select(models.HealthWarning).where(
                models.HealthWarning.user_id == user_id,
                models.HealthWarning.created_at >= start_dt,
                models.HealthWarning.created_at <= end_dt,
            )
        )
        .scalars()
        .all()
    )
    warnings_total = len(warnings)
    warnings_danger = sum(1 for item in warnings if item.warning_level == "danger")

    crisis_flag = (
        db.execute(
            select(models.ScaleAssessment.id)
            .where(
                models.ScaleAssessment.user_id == user_id,
                models.ScaleAssessment.created_at >= start_dt,
                models.ScaleAssessment.created_at <= end_dt,
                models.ScaleAssessment.crisis_flag.is_(True),
            )
            .limit(1)
        ).first()
        is not None
    )

    daily_list = [daily[day] for day in days]
    recorded_days = sum(1 for item in daily_list if item["has_data"])
    score_values = [item["score"] for item in daily_list if item["score"] is not None]
    mood_values = [item["mood_score"] for item in daily_list if item["mood_score"] is not None]
    sleep_values = [item["sleep_hours"] for item in daily_list if item["sleep_hours"] is not None]

    score_avg = round(sum(score_values) / len(score_values), 1) if score_values else None
    score_change = (
        score_values[-1] - score_values[0] if len(score_values) >= 2 else None
    )
    sleep_avg = (
        round(sum(sleep_values) / len(sleep_values), 1)
        if len(sleep_values) >= SLEEP_MIN_DAYS
        else None
    )
    sleep_debt = (
        round(sum(max(0.0, SLEEP_TARGET_HOURS - value) for value in sleep_values), 1)
        if len(sleep_values) >= SLEEP_MIN_DAYS
        else None
    )
    mood_avg = round(sum(mood_values) / len(mood_values), 1) if mood_values else None
    total_calories_in = sum(item["calories_in"] for item in daily_list)
    calories_in_avg = (
        round(total_calories_in / len(food_days), 1) if food_days else None
    )
    calories_burned_total = round(
        sum(item["calories_burned"] for item in daily_list), 1
    )
    sport_minutes_total = sum(item["sport_minutes"] for item in daily_list)

    report = {
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "days": WEEK_DAYS,
        "has_data": recorded_days > 0,
        "recorded_days": recorded_days,
        "score_avg": score_avg,
        "score_change": score_change,
        "sleep_avg": sleep_avg,
        "sleep_debt": sleep_debt,
        "sleep_days": len(sleep_days),
        "mood_avg": mood_avg,
        "mood_days": len(mood_days),
        "food_days": len(food_days),
        "calories_in_avg": calories_in_avg,
        "calories_burned_total": calories_burned_total,
        "sport_days": len(sport_days),
        "sport_minutes_total": sport_minutes_total,
        "warnings_total": warnings_total,
        "warnings_danger": warnings_danger,
        "crisis_flag": crisis_flag,
        "top_stress_tags": [tag for tag, _ in tag_counter.most_common(5)],
        "daily": daily_list,
    }
    report["insights"] = _build_insights(report)
    report["suggestions"] = _build_suggestions(report)
    report["summary_text"] = _build_summary(report)
    return report


def _build_insights(report: dict) -> list[dict]:
    insights: list[dict] = []
    if report["crisis_flag"]:
        insights.append(
            {
                "kind": "safety",
                "title": "先照顾自己",
                "text": "这一周出现了需要认真对待的心理信号。先联系学校心理咨询中心；如有危机想法，请立即拨打 120 或 12356。",
            }
        )

    days = report["recorded_days"]
    if days >= 5:
        insights.append(
            {
                "kind": "positive",
                "title": "记录很稳定",
                "text": f"这一周有 {days} 天留下记录，稳定的记录比完美的数据更有用。",
            }
        )
    elif days:
        insights.append(
            {
                "kind": "info",
                "title": "记录还在积累",
                "text": f"这一周记录了 {days} 天，再多几天就能看出更清楚的趋势。",
            }
        )
    else:
        insights.append(
            {
                "kind": "info",
                "title": "这周还没有记录",
                "text": "从一顿饭、一次散步或一次睡前打卡开始就好，不用一次记全。",
            }
        )

    if report["sleep_days"] == 0:
        insights.append(
            {
                "kind": "info",
                "title": "睡眠还没留下数据",
                "text": "在体检记录或心理打卡里填一次睡眠时长，接下来就能看到睡眠趋势。",
            }
        )
    elif report["sleep_days"] < SLEEP_MIN_DAYS:
        insights.append(
            {
                "kind": "info",
                "title": "睡眠记录不足 4 天",
                "text": "样本还少，这一周先不算平均睡眠和睡眠债，避免给你一个不准的数字。",
            }
        )
    elif report["sleep_avg"] < 6:
        insights.append(
            {
                "kind": "attention",
                "title": "睡眠明显不足",
                "text": f"有记录日均 {report['sleep_avg']}h，睡眠债 {report['sleep_debt']}h。接下来先把入睡时间往前挪一点。",
            }
        )
    elif report["sleep_avg"] < 7:
        insights.append(
            {
                "kind": "info",
                "title": "睡眠还能再多一点",
                "text": f"有记录日均 {report['sleep_avg']}h，离 8h 目标还差一点，睡眠债 {report['sleep_debt']}h。",
            }
        )
    else:
        insights.append(
            {
                "kind": "positive",
                "title": "睡眠节奏不错",
                "text": f"有记录日均 {report['sleep_avg']}h，这一周的睡眠基本达标。",
            }
        )

    if report["sport_days"] == 0:
        insights.append(
            {
                "kind": "attention",
                "title": "这一周还没运动",
                "text": "不用一上来就跑步，先安排一次 20 分钟快走也算开始。",
            }
        )
    elif report["sport_minutes_total"] < SPORT_TARGET_MINUTES:
        gap = SPORT_TARGET_MINUTES - report["sport_minutes_total"]
        insights.append(
            {
                "kind": "info",
                "title": "运动量差一点达标",
                "text": f"这一周运动 {report['sport_minutes_total']} 分钟，再补 {gap} 分钟就接近每周 150 分钟的建议量。",
            }
        )
    else:
        insights.append(
            {
                "kind": "positive",
                "title": "运动量达标",
                "text": f"这一周运动 {report['sport_minutes_total']} 分钟，已经达到每周 150 分钟的建议量。",
            }
        )

    if report["mood_days"] == 0:
        insights.append(
            {
                "kind": "info",
                "title": "心情还没打卡",
                "text": "每天 1 分钟记录心情，考试周尤其有用。",
            }
        )
    elif report["mood_avg"] < 3:
        insights.append(
            {
                "kind": "attention",
                "title": "这周心情偏低",
                "text": f"有记录日均 {report['mood_avg']}/5。先减少一点消耗，必要时去心理空间或找信任的人聊聊。",
            }
        )
    elif report["mood_avg"] >= 4:
        insights.append(
            {
                "kind": "positive",
                "title": "心情整体不错",
                "text": f"有记录日均 {report['mood_avg']}/5，保持现在的节奏。",
            }
        )
    else:
        insights.append(
            {
                "kind": "info",
                "title": "心情比较平稳",
                "text": f"有记录日均 {report['mood_avg']}/5，平稳也是一种好状态。",
            }
        )

    if report["warnings_danger"]:
        insights.append(
            {
                "kind": "attention",
                "title": "有危险级预警",
                "text": f"这一周有 {report['warnings_danger']} 条危险级健康提醒，建议先处理或咨询校医院。",
            }
        )

    return insights[:6]


def _build_suggestions(report: dict) -> list[str]:
    suggestions: list[str] = []
    if report["crisis_flag"]:
        suggestions.append(SAFETY_SUGGESTION)

    if report["sleep_days"] == 0:
        suggestions.append("这一周挑 3 天记录睡眠，先有数据再谈调整。")
    elif report["sleep_avg"] is not None and report["sleep_avg"] < 7:
        suggestions.append("接下来挑 3 天，比这一周平均早睡 30 分钟。")

    if report["sport_minutes_total"] < SPORT_TARGET_MINUTES:
        suggestions.append("接下来安排 3 次 30 分钟快走或慢跑，先把总量凑到 150 分钟。")

    if report["food_days"] < 4:
        suggestions.append("选 4 天记录三餐，比只记一顿更容易看出饮食节奏。")

    if report["mood_days"] < 4:
        suggestions.append("每天花 1 分钟在心理空间打卡，考试周也别断。")

    if not suggestions:
        suggestions.append("保持现在的节奏，接下来给自己留一个完全不赶任务的晚上。")

    return suggestions[:3]


def _build_summary(report: dict) -> str:
    period = f"{_day_label(date.fromisoformat(report['start_date']))}–{_day_label(date.fromisoformat(report['end_date']))}"
    if not report["has_data"]:
        return f"这一周（{period}）还没有健康记录。接下来从一顿饭、一次散步或一次睡前打卡开始。"

    if report["crisis_flag"]:
        return f"这一周（{period}）先照顾好自己。需要时联系学校心理咨询中心，或拨打 120 / 12356。"

    parts = [f"这一周（{period}）记录了 {report['recorded_days']} 天"]
    if report["sleep_avg"] is not None:
        parts.append(f"有记录日均睡眠 {report['sleep_avg']}h")
    if report["sport_minutes_total"]:
        parts.append(f"运动 {report['sport_minutes_total']} 分钟")
    if report["mood_avg"] is not None:
        parts.append(f"心情 {report['mood_avg']}/5")
    return "，".join(parts) + "。接下来继续保持，能记多少记多少。"


def build_weekly_ai_messages(report: dict) -> list[dict]:
    """把结构化周报压成 LLM 可读的事实清单，禁止模型自行补数据。"""
    lines = [
        f"周期：{report['start_date']} 至 {report['end_date']}",
        f"记录天数：{report['recorded_days']}/7",
        f"平均健康分：{report['score_avg'] if report['score_avg'] is not None else '无'}",
        f"平均睡眠：{report['sleep_avg'] if report['sleep_avg'] is not None else '记录不足'}",
        f"睡眠债：{report['sleep_debt'] if report['sleep_debt'] is not None else '记录不足'}",
        f"心情均值：{report['mood_avg'] if report['mood_avg'] is not None else '无'}",
        f"日均摄入：{report['calories_in_avg'] if report['calories_in_avg'] is not None else '无'} kcal",
        f"运动总时长：{report['sport_minutes_total']} 分钟",
        f"运动消耗：{report['calories_burned_total']} kcal",
        f"压力标签：{'、'.join(report['top_stress_tags']) or '无'}",
        f"危险级预警：{report['warnings_danger']} 条",
        f"危机信号：{'有' if report['crisis_flag'] else '无'}",
        "规则洞察：",
    ]
    lines.extend(f"- {item['title']}：{item['text']}" for item in report["insights"])
    lines.append("可执行建议：")
    lines.extend(f"- {item}" for item in report["suggestions"])

    system = (
        "你是大学生健康管理助手「搭子」。只根据用户给出的周报事实回答，"
        "不编造缺失数据，不做疾病诊断，不开药，不替代医生。"
        "若出现危机信号，优先建议联系学校心理咨询中心或拨打 120/12356。"
        "用中文写 150–250 字，分三段：第一段肯定这一周做得好的地方；"
        "第二段指出这一周最值得留意的一项，并说明数据依据；"
        "第三段给两条具体、可执行、适合学生作息的建议。"
        "记录天数少于 4 天时，先说明样本有限，不要把单条满分或单次数据外推为整周状态。"
        "语气温和，不说教，不要只写一句话。"
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": "\n".join(lines)},
    ]
