"""异步任务队列清理测试（性能域 P1：results 无界增长）"""

import time
from datetime import datetime, timedelta

import pytest

from async_tasks import AsyncTaskQueue, TaskResult, TaskStatus


@pytest.fixture(autouse=True)
def reset_task_queue_singleton():
    """确保每个测试用全新队列实例（AsyncTaskQueue 是单例）"""
    AsyncTaskQueue._instance = None
    AsyncTaskQueue._initialized = False
    yield
    AsyncTaskQueue._instance = None
    AsyncTaskQueue._initialized = False


def _seed_completed(q, task_id, completed_ago_seconds):
    """直接向 results 注入一个已完成的历史任务（不经队列，避免 worker 竞态覆盖）"""
    with q.lock:
        result = TaskResult(task_id)
        result.status = TaskStatus.COMPLETED
        result.created_at = datetime.now() - timedelta(
            seconds=completed_ago_seconds + 60
        )
        result.completed_at = datetime.now() - timedelta(seconds=completed_ago_seconds)
        result.result = {"content": "x" * 1000}  # 模拟大段 LLM 文本
        q.results[task_id] = result
    return task_id


def _submit_completed(q, task_id, completed_ago_seconds):
    """提交任务并直接标记为已完成（绕过真实工作线程）"""
    q.submit_task(task_id, lambda: {"ok": "done"})
    with q.lock:
        result = q.results[task_id]
        result.status = TaskStatus.COMPLETED
        result.completed_at = datetime.now() - timedelta(seconds=completed_ago_seconds)
        result.result = {"content": "x" * 1000}  # 模拟大段 LLM 文本
    return task_id


class TestCleanupOldTasks:
    def test_removes_expired_completed_task(self):
        q = AsyncTaskQueue(max_workers=1)
        _submit_completed(q, "t1", completed_ago_seconds=3600)
        q.cleanup_old_tasks(max_age_seconds=60)
        assert q.get_task_status("t1") is None

    def test_keeps_fresh_completed_task(self):
        q = AsyncTaskQueue(max_workers=1)
        _submit_completed(q, "t2", completed_ago_seconds=10)
        q.cleanup_old_tasks(max_age_seconds=3600)
        assert q.get_task_status("t2") is not None

    def test_removes_stale_pending_task(self):
        """悬空的 pending 任务（如工作线程崩溃后遗留）也必须被清理"""
        q = AsyncTaskQueue(max_workers=1)
        q.submit_task("t3", lambda: None)
        with q.lock:
            q.results["t3"].created_at = datetime.now() - timedelta(seconds=7200)
        q.cleanup_old_tasks(max_age_seconds=3600)
        assert q.get_task_status("t3") is None

    def test_keeps_fresh_pending_task(self):
        q = AsyncTaskQueue(max_workers=1)
        q.submit_task("t4", lambda: None)
        q.cleanup_old_tasks(max_age_seconds=3600)
        assert q.get_task_status("t4") is not None

    def test_cleanup_removes_failed_task(self):
        q = AsyncTaskQueue(max_workers=1)
        q.submit_task("t6", lambda: None)
        with q.lock:
            result = q.results["t6"]
            result.set_failed("boom")
            result.completed_at = datetime.now() - timedelta(seconds=7200)
        q.cleanup_old_tasks(max_age_seconds=3600)
        assert q.get_task_status("t6") is None


class TestPeriodicCleanup:
    def test_cleanup_loop_removes_expired_results(self):
        """启动后定时清理线程应按 settings.TASK_RESULT_TTL 自动清理"""
        q = AsyncTaskQueue(max_workers=1, cleanup_interval_seconds=1)
        # 先直接注入一个过期结果（不经队列/worker，避免竞态覆盖 completed_at）
        _seed_completed(q, "t5", completed_ago_seconds=7200)
        q.start()
        try:
            deadline = time.time() + 5
            while time.time() < deadline:
                if q.get_task_status("t5") is None:
                    break
                time.sleep(0.1)
            assert q.get_task_status("t5") is None
            assert len(q.results) == 0
        finally:
            q.stop()
