"""预警 / 分析相关查询的性能基线（任务 P-1）。

只读业务代码：脚本使用临时 SQLite 数据库 + FastAPI 依赖覆盖，不写生产库、不改任何生产模块。

用法：
    PYTHONUTF8=1 uv run python scripts/bench_health_queries.py
    PYTHONUTF8=1 uv run python scripts/bench_health_queries.py --sizes 1000,10000 --iterations 20
    PYTHONUTF8=1 uv run python scripts/bench_health_queries.py --simulate-index --json baseline.json
    PYTHONUTF8=1 uv run python scripts/bench_health_queries.py --sizes 50000 --users 5

输出：
    1) 每个规模下各端点的 p50 / p95（毫秒，经 ASGI 直连，含 FastAPI 校验与序列化开销）
    2) 每请求 SQL 语句数（用于发现 N+1）
    3) 关键查询的 EXPLAIN QUERY PLAN（SCAN = 全表扫描，SEARCH = 命中索引）
    4) --simulate-index 时额外给出「加 3 个候选索引」的对照结果（两个数据库分别播种，避免同库污染）
"""

import argparse
import asyncio
import json
import os
import statistics
import sys
import tempfile
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

load_dotenv()

# 基准脚本独立于生产配置运行
os.environ.setdefault("SECRET_KEY", "p1-bench-secret-key-not-for-production")
os.environ.setdefault("INVITE_CODES", "bench-invite")

from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import chat_session  # noqa: F401  # 注册 chat_sessions / chat_messages 表
import models
from auth import get_current_user, get_password_hash
from database import Base
from database import get_db as _production_get_db
from main import app

PASSWORD = "benchpass123"
WARNINGS_BASE = 5  # 每人基准预警数；随记录规模一同增长，模拟真实累积
WARNINGS_CAP = 200
CHECK_USER_EVERY = 10  # 每 10 个用户放一条危机量表记录，模拟真实分布
DAYS = 30

# 候选索引（仅写入临时库做对照，不改 models、不生成迁移）
CANDIDATE_INDEXES = [
    ("ix_health_records_user_date", "health_records(user_id, record_date)"),
    ("ix_health_warnings_user_created", "health_warnings(user_id, created_at)"),
    ("ix_health_analyses_user_date", "health_analyses(user_id, analysis_date)"),
]

ENDPOINTS = [
    ("GET", "/api/warning/list", "预警列表（全部）"),
    ("GET", "/api/warning/list?is_read=false", "预警列表（未读）"),
    ("POST", "/api/warning/check", "预警检查（计算 + 落库）"),
    ("GET", "/api/warning/stats", "预警统计"),
    ("GET", "/api/health/records", "健康记录列表"),
    ("GET", "/api/health/rating/latest", "最新健康评级"),
    ("GET", "/api/mental/trend?days=30", "心理趋势（30 天）"),
    ("GET", "/api/mental/summary", "心理汇总"),
]

QUERY_PLANS = [
    (
        "预警列表（全部）",
        "SELECT * FROM health_warnings WHERE user_id = :uid ORDER BY created_at DESC",
    ),
    (
        "预警列表（未读）",
        (
            "SELECT * FROM health_warnings WHERE user_id = :uid AND is_read = 0 "
            "ORDER BY created_at DESC"
        ),
    ),
    (
        "预警去重查询",
        (
            "SELECT * FROM health_warnings WHERE user_id = :uid AND warning_type = :t "
            "AND is_read = 0"
        ),
    ),
    (
        "最新健康记录",
        "SELECT * FROM health_records WHERE user_id = :uid ORDER BY record_date DESC LIMIT 1",
    ),
    (
        "健康记录列表",
        "SELECT * FROM health_records WHERE user_id = :uid ORDER BY record_date DESC",
    ),
    (
        "心理打卡窗口",
        (
            "SELECT * FROM mental_records WHERE user_id = :uid AND record_date >= :day "
            "ORDER BY record_date"
        ),
    ),
    (
        "量表历史",
        (
            "SELECT * FROM scale_assessments WHERE user_id = :uid AND scale_type = :t "
            "ORDER BY created_at DESC"
        ),
    ),
]


class QueryCounter:
    """统计两次 reset 之间执行的 SQL 语句（用于发现 N+1）。"""

    def __init__(self) -> None:
        self.statements: list[str] = []

    def reset(self) -> None:
        self.statements.clear()

    def __call__(self, conn, cursor, statement, parameters, context, executemany) -> None:
        self.statements.append(statement)

    @property
    def count(self) -> int:
        return len(self.statements)


def _build_engine(db_path: Path) -> Engine:
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return engine


def _apply_candidate_indexes(engine: Engine) -> None:
    with engine.begin() as conn:
        for name, target in CANDIDATE_INDEXES:
            conn.execute(text(f"CREATE INDEX IF NOT EXISTS {name} ON {target}"))


def _seed(engine: Engine, *, users: int, records: int) -> dict[str, int]:
    """按规模播种：users 个用户，均分 records 条健康记录 + DAYS 天心理打卡 + 累积预警。"""
    factory = sessionmaker(bind=engine)
    session: Session = factory()
    try:
        password_hash = get_password_hash(PASSWORD)
        user_ids: list[int] = []
        for index in range(users):
            user = models.User(
                name=f"bench{index:04d}",
                password_hash=password_hash,
                invite_code=os.environ["INVITE_CODES"],
            )
            session.add(user)
            session.flush()
            user_ids.append(user.id)

        now = datetime.now(UTC)
        per_user = max(records // max(users, 1), 1)
        warnings_per_user = min(max(WARNINGS_BASE, per_user // 2), WARNINGS_CAP)

        health_rows = []
        warning_rows = []
        mental_rows = []
        scale_rows = []
        analysis_rows = []
        for position, user_id in enumerate(user_ids):
            for day in range(per_user):
                health_rows.append(
                    models.HealthRecord(
                        user_id=user_id,
                        height=170.0,
                        weight=85.0,
                        bmi=29.4,
                        blood_pressure_systolic=150,
                        blood_pressure_diastolic=95,
                        heart_rate=95,
                        temperature=36.6,
                        record_date=now - timedelta(days=day),
                    )
                )
            for day in range(DAYS):
                mental_rows.append(
                    models.MentalRecord(
                        user_id=user_id,
                        mood_score=(day % 5) + 1,
                        stress_tags=json.dumps(["学业"], ensure_ascii=False),
                        sleep_hours=5.5 if day % 2 else 7.0,
                        record_date=(now - timedelta(days=day)).date(),
                    )
                )
            for index in range(warnings_per_user):
                warning_rows.append(
                    models.HealthWarning(
                        user_id=user_id,
                        warning_type=f"基准类型{index}",
                        warning_level="warning",
                        warning_content="基准数据，用于 /warning/list 的分页与排序测量。",
                        is_read=index % 2 == 0,
                        created_at=now - timedelta(hours=index),
                    )
                )
            if position % CHECK_USER_EVERY == 0:
                scale_rows.append(
                    models.ScaleAssessment(
                        user_id=user_id,
                        scale_type="phq9",
                        answers=json.dumps([0, 0, 0, 0, 0, 0, 0, 0, 1]),
                        score=22,
                        risk_level="severe",
                        crisis_flag=True,
                        created_at=now,
                    )
                )
            analysis_rows.append(
                models.HealthAnalysis(
                    user_id=user_id,
                    bmi_status="肥胖",
                    overall_status="需改善",
                    health_rating="需改善",
                    health_score=62,
                    analysis_date=now,
                )
            )

        session.bulk_save_objects(health_rows)
        session.bulk_save_objects(mental_rows)
        session.bulk_save_objects(warning_rows)
        session.bulk_save_objects(scale_rows)
        session.bulk_save_objects(analysis_rows)
        session.commit()

        return {
            "users": users,
            "health_records": len(health_rows),
            "health_records_per_user": per_user,
            "warnings": len(warning_rows),
            "warnings_per_user": warnings_per_user,
            "mental_records": len(mental_rows),
            "scale_assessments": len(scale_rows),
        }
    finally:
        session.close()


def _percentile(values: list[float], ratio: float) -> float:
    ordered = sorted(values)
    index = min(round(ratio * (len(ordered) - 1)), len(ordered) - 1)
    return ordered[index]


def _override_dependencies(engine: Engine, user: models.User) -> None:
    factory = sessionmaker(bind=engine)

    def override_db():
        session = factory()
        try:
            yield session
        finally:
            session.close()

    async def noop_lifespan(_app):
        yield

    app.router.lifespan_context = noop_lifespan
    app.dependency_overrides[_production_get_db] = override_db
    app.dependency_overrides[get_current_user] = lambda: user


async def _measure(
    engine: Engine, user: models.User, *, iterations: int, counter: QueryCounter
) -> list[dict[str, Any]]:
    _override_dependencies(engine, user)

    results: list[dict[str, Any]] = []
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://bench") as client:
        for method, path, label in ENDPOINTS:
            for _ in range(2):  # 预热：避免首请求的 import / 缓存抖动
                await client.request(method, path)

            samples: list[float] = []
            statements: list[int] = []
            statuses: set[int] = set()
            for _ in range(iterations):
                counter.reset()
                started = time.perf_counter()
                response = await client.request(method, path)
                samples.append((time.perf_counter() - started) * 1000)
                statements.append(counter.count)
                statuses.add(response.status_code)

            results.append(
                {
                    "endpoint": label,
                    "method": method,
                    "path": path,
                    "status": sorted(statuses),
                    "p50_ms": round(statistics.median(samples), 2),
                    "p95_ms": round(_percentile(samples, 0.95), 2),
                    "max_ms": round(max(samples), 2),
                    "queries_per_request": round(statistics.median(statements), 1),
                }
            )

    app.dependency_overrides.clear()
    return results


def _best_of(rounds: list[list[dict[str, Any]]]) -> list[dict[str, Any]]:
    """多轮测量取每端点最小 p50/p95（微基准的常规做法，抵消系统抖动）。"""
    merged: list[dict[str, Any]] = []
    for index, base in enumerate(rounds[0]):
        same = [round_[index] for round_ in rounds]
        merged.append(
            {
                **base,
                "p50_ms": min(item["p50_ms"] for item in same),
                "p95_ms": min(item["p95_ms"] for item in same),
                "max_ms": min(item["max_ms"] for item in same),
            }
        )
    return merged


async def _measure_rounds(
    engine: Engine, user: models.User, *, iterations: int, counter: QueryCounter, rounds: int
) -> list[dict[str, Any]]:
    results = []
    for _ in range(rounds):
        results.append(await _measure(engine, user, iterations=iterations, counter=counter))
    return _best_of(results)


def _explain(engine: Engine, user_id: int) -> list[dict[str, Any]]:
    plans = []
    with engine.connect() as conn:
        for label, sql in QUERY_PLANS:
            rows = conn.execute(
                text("EXPLAIN QUERY PLAN " + sql),
                {
                    "uid": user_id,
                    "t": "phq9",
                    "day": (datetime.now(UTC) - timedelta(days=DAYS)).date(),
                },
            ).all()
            detail = " | ".join(str(row[-1]) for row in rows)
            plans.append(
                {
                    "query": label,
                    "plan": detail,
                    "full_scan": "SCAN" in detail and "USING INDEX" not in detail,
                }
            )
    return plans


def _first_user(engine: Engine) -> models.User:
    factory = sessionmaker(bind=engine)
    session: Session = factory()
    try:
        return session.query(models.User).order_by(models.User.id.asc()).first()
    finally:
        session.close()


def _bench_queries(engine: Engine, user_id: int, *, iterations: int) -> list[dict[str, Any]]:
    """直接计时 QUERY_PLANS 里的 SQL，剥离 FastAPI / 序列化开销，看扫描本身多贵。"""
    params = {
        "uid": user_id,
        "t": "phq9",
        "day": (datetime.now(UTC) - timedelta(days=DAYS)).date(),
    }
    rows: list[dict[str, Any]] = []
    with engine.connect() as conn:
        for label, sql in QUERY_PLANS:
            statement = text(sql)
            for _ in range(3):
                conn.execute(statement, params).all()
            samples = []
            for _ in range(iterations):
                started = time.perf_counter()
                conn.execute(statement, params).all()
                samples.append((time.perf_counter() - started) * 1000)
            rows.append(
                {
                    "query": label,
                    "p50_ms": round(statistics.median(samples), 3),
                    "p95_ms": round(_percentile(samples, 0.95), 3),
                }
            )
    return rows


def _describe_gap(before: float, after: float) -> str:
    if not after:
        return "-"
    factor = before / after
    if factor >= 1.15:
        return f"快 {factor:.1f}×"
    if factor <= 0.87:
        return f"慢 {1 / factor:.1f}×"
    return "持平"


async def _run(args) -> dict[str, Any]:
    scenarios: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="p1-bench-") as workdir:
        root = Path(workdir)
        counter = QueryCounter()

        for index, records in enumerate(args.sizes):
            plain_engine = _build_engine(root / f"plain-{index}.db")
            event.listen(plain_engine, "before_cursor_execute", counter)
            dataset = _seed(plain_engine, users=args.users, records=records)
            user = _first_user(plain_engine)

            results = await _measure_rounds(
                plain_engine,
                user,
                iterations=args.iterations,
                counter=counter,
                rounds=args.rounds,
            )
            scenario: dict[str, Any] = {
                "records": records,
                "dataset": dataset,
                "results": results,
                "plans": _explain(plain_engine, user.id),
                "queries": _bench_queries(plain_engine, user.id, iterations=args.query_iterations),
            }

            if args.simulate_index:
                indexed_engine = _build_engine(root / f"indexed-{index}.db")
                event.listen(indexed_engine, "before_cursor_execute", counter)
                _seed(indexed_engine, users=args.users, records=records)
                _apply_candidate_indexes(indexed_engine)
                indexed_user = _first_user(indexed_engine)
                scenario["results_with_index"] = await _measure_rounds(
                    indexed_engine,
                    indexed_user,
                    iterations=args.iterations,
                    counter=counter,
                    rounds=args.rounds,
                )
                scenario["plans_after_index"] = _explain(indexed_engine, indexed_user.id)
                scenario["queries_with_index"] = _bench_queries(
                    indexed_engine, indexed_user.id, iterations=args.query_iterations
                )
                indexed_engine.dispose()

            plain_engine.dispose()
            scenarios.append(scenario)

    return {
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "users": args.users,
        "iterations": args.iterations,
        "rounds": args.rounds,
        "query_iterations": args.query_iterations,
        "scenarios": scenarios,
    }


def _print_scenario(scenario: dict[str, Any]) -> None:
    dataset = scenario["dataset"]
    print(
        f"### 规模 {dataset['health_records']} 条健康记录"
        f"（{dataset['users']} 用户 · 每人 {dataset['health_records_per_user']} 条记录 "
        f"/ {dataset['warnings_per_user']} 条预警）\n"
    )
    print("| 端点 | status | p50 (ms) | p95 (ms) | max (ms) | SQL/请求 |")
    print("|---|---|---|---|---|---|")
    for row in scenario["results"]:
        print(
            f"| {row['endpoint']} | {row['status']} | {row['p50_ms']} | {row['p95_ms']} "
            f"| {row['max_ms']} | {row['queries_per_request']} |"
        )
    print()

    if "results_with_index" in scenario:
        print("加 3 个候选索引后：\n")
        print("| 端点 | p50 (ms) | p95 (ms) | p50 对比 |")
        print("|---|---|---|---|")
        for before, after in zip(scenario["results"], scenario["results_with_index"]):
            print(
                f"| {after['endpoint']} | {after['p50_ms']} | {after['p95_ms']} "
                f"| {_describe_gap(before['p50_ms'], after['p50_ms'])} |"
            )
        print()

    print("单条 SQL 成本（剥离 HTTP / 序列化）：\n")
    indexed = {row["query"]: row for row in scenario.get("queries_with_index", [])}
    print("| 查询 | p50 无索引 (ms) | p50 有索引 (ms) | 对比 |")
    print("|---|---|---|---|")
    for row in scenario["queries"]:
        after = indexed.get(row["query"])
        gap = _describe_gap(row["p50_ms"], after["p50_ms"]) if after else "-"
        after_value = after["p50_ms"] if after else "-"
        print(f"| {row['query']} | {row['p50_ms']} | {after_value} | {gap} |")
    print()


def _print_plans(plans: list[dict[str, Any]], title: str) -> None:
    print(f"### {title}\n")
    print("| 查询 | 计划 | 全表扫描 |")
    print("|---|---|---|")
    for plan in plans:
        print(f"| {plan['query']} | {plan['plan']} | {'是' if plan['full_scan'] else '否'} |")
    print()


def _print_report(payload: dict[str, Any]) -> None:
    print("\n## 基准环境\n")
    print("- 数据库：临时 SQLite（脚本退出即删除），经 ASGI 直连调用路由")
    print(
        f"- 采样：预热 2 次 + 每轮 {payload['iterations']} 次，共 {payload['rounds']} 轮，"
        "各端点取轮内 p50/p95 的最小值"
    )
    print(f"- 用户数：{payload['users']}，心理打卡 {DAYS} 天，每 10 人一条危机量表记录\n")

    for scenario in payload["scenarios"]:
        _print_scenario(scenario)

    _print_plans(payload["scenarios"][0]["plans"], "EXPLAIN QUERY PLAN（未加候选索引）")
    if "plans_after_index" in payload["scenarios"][0]:
        _print_plans(
            payload["scenarios"][0]["plans_after_index"], "EXPLAIN QUERY PLAN（加候选索引后）"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="P-1 预警/分析查询性能基线")
    parser.add_argument("--sizes", default="1000,10000", help="健康记录规模，逗号分隔")
    parser.add_argument("--users", type=int, default=50, help="用户数")
    parser.add_argument("--iterations", type=int, default=20, help="每轮每端点采样次数")
    parser.add_argument("--rounds", type=int, default=2, help="测量轮数（取最优）")
    parser.add_argument("--json", default=None, help="把结果写入 JSON 文件")
    parser.add_argument("--query-iterations", type=int, default=50, help="单条 SQL 计时采样次数")
    parser.add_argument(
        "--simulate-index",
        action="store_true",
        help="额外在独立临时库建 3 个候选索引并对照测量（不改 models / 不生成迁移）",
    )
    args = parser.parse_args()
    args.sizes = [int(value) for value in args.sizes.split(",") if value.strip()]

    payload = asyncio.run(_run(args))
    _print_report(payload)
    if args.json:
        Path(args.json).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"JSON 已写入 {args.json}")


if __name__ == "__main__":
    main()
