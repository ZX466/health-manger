"""异步任务持久化队列测试 - 覆盖提交 / 原子领取 / 执行 / 启动恢复 / 清理。"""

import json
import threading

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import models
from async_tasks import TaskStatus, _run_llm_sync
from database import Base


@pytest.fixture
def queue_engine(tmp_path):
    """独立文件型 SQLite：worker 线程各持连接，便于真实并发测试。"""
    import models  # noqa: F401 - 注册所有表到 Base.metadata

    db_path = str(tmp_path / "async_queue.db")
    eng = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False, "timeout": 30},
    )
    Base.metadata.create_all(bind=eng)
    yield eng
    eng.dispose()


@pytest.fixture
def queue(queue_engine):
    """把全局 task_queue 的 session_factory 指向隔离库，测试后还原。"""
    from async_tasks import task_queue

    original_factory = task_queue._session_factory
    original_running = task_queue.running
    original_workers = list(task_queue.workers)
    original_cleanup = task_queue.cleanup_thread

    task_queue._session_factory = sessionmaker(
        bind=queue_engine, autocommit=False, autoflush=False
    )
    task_queue.running = False
    task_queue.workers.clear()
    task_queue.cleanup_thread = None
    yield task_queue
    task_queue._session_factory = original_factory
    task_queue.running = original_running
    task_queue.workers.clear()
    task_queue.workers.extend(original_workers)
    task_queue.cleanup_thread = original_cleanup


def _claim_and_execute(q, monkeypatch, task_id="submit-1", llm_result=None):
    q.submit_task(task_id, user_id=1, messages=[{"role": "user", "content": "hi"}])
    monkeypatch.setattr(
        "async_tasks._run_llm_sync",
        llm_result or (lambda messages, config: {"content": "建议", "tokens_used": 3}),
    )
    claimed = q._claim_task()
    assert claimed is not None
    q._execute_task(claimed)
    return claimed


def test_submit_creates_pending_task(queue):
    task_id = "submit-1"
    queue.submit_task(task_id, user_id=1, messages=[{"role": "user", "content": "hi"}])

    status = queue.get_task_status(task_id, user_id=1)
    assert status["status"] == "pending"
    assert status["task_id"] == task_id
    assert status["result"] is None


def test_submit_persists_payload_without_api_key(queue):
    messages = [{"role": "user", "content": "分析健康数据"}]
    queue.submit_task("submit-payload", user_id=1, messages=messages)

    from sqlalchemy import select

    session = queue._session_factory()
    row = session.execute(
        select(models.AsyncTask).where(models.AsyncTask.task_id == "submit-payload")
    ).scalar_one()
    session.close()

    payload = json.loads(row.payload)
    assert payload["messages"] == messages
    # payload 绝不应包含用户 API Key 等 LLM 配置
    assert "api_key" not in row.payload
    assert "api_key" not in json.dumps(payload)


def test_status_isolated_by_user(queue, monkeypatch):
    _claim_and_execute(queue, monkeypatch)

    # 本人可查
    assert queue.get_task_status("submit-1", user_id=1)["status"] == "completed"
    # 他人不可查（用户隔离）
    assert queue.get_task_status("submit-1", user_id=2) is None


def test_claim_is_atomic_no_duplicate_claims(queue, monkeypatch):
    for i in range(5):
        queue.submit_task(f"task-{i}", user_id=1, messages=[])

    claimed_ids = []
    lock = threading.Lock()

    def claim_once():
        claimed = queue._claim_task()
        if claimed is not None:
            with lock:
                claimed_ids.append(claimed.task_id)

    threads = [threading.Thread(target=claim_once) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(claimed_ids) == 5
    assert len(set(claimed_ids)) == 5
    for task_id in claimed_ids:
        assert queue.get_task_status(task_id, user_id=1)["status"] == "running"


def test_submit_complete_and_restart_queryable(queue, monkeypatch):
    """提交 → 完成 → 模拟重启（停队列）后状态仍可从持久化库查询。"""
    _claim_and_execute(queue, monkeypatch)

    queue.stop()

    status = queue.get_task_status("submit-1", user_id=1)
    assert status["status"] == "completed"
    assert status["result"]["content"] == "建议"
    assert status["result"]["analysis_id"] is not None


def test_execute_invalid_payload_marks_failed(queue):
    """payload 解析失败也收敛为 failed，不卡在 running（评审 P1 覆盖项）。"""
    queue.submit_task("task_bad_payload", user_id=1, messages="not-a-dict")

    # 将 payload 改为非法 JSON，模拟落库数据损坏
    session = queue._session_factory()
    try:
        task = session.query(models.AsyncTask).filter(models.AsyncTask.task_id == "task_bad_payload").first()
        task.payload = "{broken json"
        session.commit()
    finally:
        session.close()

    claimed = queue._claim_task()
    assert claimed is not None
    queue._execute_task(claimed)

    status = queue.get_task_status("task_bad_payload")
    assert status["status"] == "failed"
    assert status["error"]


def test_execute_commit_failure_does_not_leave_running(queue, monkeypatch):
    """成功路径落库失败时任务收敛为 failed，不留下 running（评审 P1/P2 覆盖项）。"""
    queue.submit_task("task_commit_fail", user_id=1, messages=[{"role": "user", "content": "x"}])

    real_ai_analysis = models.AIAnalysis
    monkeypatch.setattr(
        "async_tasks._run_llm_sync",
        lambda messages, config: {"content": "ok", "tokens_used": 5},
    )

    def exploding_add(*args, **kwargs):
        raise RuntimeError("db write failed")

    monkeypatch.setattr(models, "AIAnalysis", exploding_add)
    claimed = queue._claim_task()
    assert claimed is not None
    queue._execute_task(claimed)

    status = queue.get_task_status("task_commit_fail")
    assert status["status"] == "failed"
    assert status["error"]
    # 不留 running，也不留下未落库的已完成分析
    session = queue._session_factory()
    try:
        analyses = session.query(real_ai_analysis).filter(
            real_ai_analysis.user_id == 1
        ).all()
        assert len(analyses) == 0
    finally:
        session.close()


def test_completed_analysis_persisted_in_db(queue, monkeypatch):
    """结果直接落 ai_analyses，任务表 result 含 analysis_id。"""
    _claim_and_execute(queue, monkeypatch)

    session = queue._session_factory()
    analysis = (
        session.query(models.AIAnalysis)
        .filter(models.AIAnalysis.user_id == 1)
        .first()
    )
    session.close()
    assert analysis is not None
    assert analysis.analysis_type == "AI 异步分析"
    assert analysis.response_content == "建议"


def test_execute_failure_marks_failed_and_masks_error(queue, monkeypatch):
    def boom(messages, config):
        raise RuntimeError("upstream detailed error")

    monkeypatch.setattr("async_tasks._run_llm_sync", boom)
    queue.submit_task("fail-task", user_id=1, messages=[])

    claimed = queue._claim_task()
    assert claimed is not None
    queue._execute_task(claimed)

    status = queue.get_task_status("fail-task", user_id=1)
    assert status["status"] == "failed"
    # 不泄露上游异常细节，只暴露固定文案
    assert status["error"] == "任务执行失败，请稍后重试"


def test_recover_interrupted_marks_running_as_failed(queue):
    session = queue._session_factory()
    session.add(
        models.AsyncTask(
            task_id="interrupted",
            user_id=1,
            status=TaskStatus.RUNNING.value,
            payload="{}",
            claim_token="abc",
        )
    )
    session.commit()
    session.close()

    queue._recover_interrupted()

    status = queue.get_task_status("interrupted", user_id=1)
    assert status["status"] == "failed"
    assert status["error"] == "任务执行中断，请重新提交"


def test_cleanup_removes_completed_keeps_active(queue, monkeypatch):
    _claim_and_execute(queue, monkeypatch)
    queue.submit_task("active-pending", user_id=1, messages=[])

    queue.cleanup_old_tasks(max_age_seconds=-1)

    # 已完成且超期 -> 清理
    assert queue.get_task_status("submit-1", user_id=1) is None
    # pending 是有效工作 -> 保留
    assert queue.get_task_status("active-pending", user_id=1) is not None


def test_run_llm_sync_returns_json_serializable_result(monkeypatch):
    async def fake_call_llm(messages, config):
        return "同步包装结果", 7

    monkeypatch.setattr("async_tasks.call_llm", fake_call_llm)
    result = _run_llm_sync([], object())
    assert result == {"content": "同步包装结果", "tokens_used": 7}
    assert json.dumps(result)  # 可 JSON 序列化


def test_start_and_stop_creates_workers(queue):
    queue.start()
    assert queue.running is True
    assert len(queue.workers) == queue.max_workers
    queue.stop()
    assert queue.running is False


def test_stale_worker_cannot_complete_recovered_task(queue, monkeypatch):
    """恢复结算后，旧 worker 的晚到结果不得覆盖终态，也不得落分析记录（P1 回归）。"""
    queue.submit_task("stale-complete", user_id=1, messages=[{"role": "user", "content": "x"}])
    monkeypatch.setattr(
        "async_tasks._run_llm_sync",
        lambda messages, config: {"content": "晚到结果", "tokens_used": 1},
    )
    claimed = queue._claim_task()
    assert claimed is not None

    # 模拟启动恢复：任务被判 failed 并清空领取令牌
    queue._recover_interrupted()
    assert queue.get_task_status("stale-complete")["status"] == "failed"

    queue._execute_task(claimed)

    status = queue.get_task_status("stale-complete")
    assert status["status"] == "failed"  # 未被旧 worker 覆盖为 completed
    assert status["result"] is None
    session = queue._session_factory()
    try:
        assert session.query(models.AIAnalysis).filter_by(user_id=1).count() == 0
    finally:
        session.close()


def test_stale_worker_cannot_mark_failed_after_settlement(queue):
    """令牌失效后，旧 worker 的失败标记不得覆盖已结算状态。"""
    queue.submit_task("stale-failed", user_id=1, messages=[])
    claimed = queue._claim_task()
    assert claimed is not None

    queue._recover_interrupted()  # 恢复先结算为 failed 且清空令牌
    # 模拟任务随后被新 worker 完成
    session = queue._session_factory()
    try:
        task = session.query(models.AsyncTask).filter_by(task_id="stale-failed").first()
        task.status = TaskStatus.COMPLETED.value
        task.result = json.dumps({"content": "新 worker 结果"})
        task.claim_token = None
        session.commit()
    finally:
        session.close()

    queue._mark_failed("stale-failed", "旧 worker 失败", claimed.claim_token)

    status = queue.get_task_status("stale-failed")
    assert status["status"] == "completed"
    assert status["result"] == {"content": "新 worker 结果"}
