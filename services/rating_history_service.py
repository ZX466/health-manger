"""历史健康评级查询（K-2）。

按日返回近 N 天的综合评级。口径：
- 日期序列连续（含今天），**缺失日保留 `date`，`score`/`level` 为 `null`**，前端无需猜；
- 同一天多次分析取最新一条（`analysis_date` 最大，其次 `id` 最大）；
- 只返回当前用户的数据。
"""

from datetime import date, datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

import models


def rating_history(
    db: Session,
    user_id: int,
    days: int,
    *,
    today: date | None = None,
) -> list[dict]:
    end = today or datetime.now().date()
    start = end - timedelta(days=days - 1)

    rows = (
        db.execute(
            select(models.HealthAnalysis)
            .where(
                models.HealthAnalysis.user_id == user_id,
                models.HealthAnalysis.analysis_date >= datetime.combine(start, time.min),
            )
            .order_by(
                models.HealthAnalysis.analysis_date.asc(),
                models.HealthAnalysis.id.asc(),
            )
        )
        .scalars()
        .all()
    )

    by_day: dict[date, tuple[int | None, str | None]] = {}
    for row in rows:
        if row.analysis_date is None:
            continue
        day = row.analysis_date.date()
        if day < start or day > end:
            continue
        # 升序遍历，同日后者覆盖前者 = 当天最新分析
        by_day[day] = (row.health_score, row.health_rating)

    points = []
    for offset in range(days):
        day = start + timedelta(days=offset)
        score, level = by_day.get(day, (None, None))
        points.append({"date": day, "score": score, "level": level})
    return points
