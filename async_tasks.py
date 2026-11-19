"""
异步任务持久化队列
参考 TongueDiagnosis 项目的队列处理设计
任务持久化在 SQLite async_tasks 表，支持提交 / 原子领取 / 状态查询 / 启动恢复
"""

import json
import logging
import threading
import time
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, NamedTuple

from sqlalchemy import text

import models
import settings
from database import SessionLocal
from services.ai_config_service import build_llm_config_for_user
from services.llm_service import LLMConfig, call_llm

logger = logging.getLogger(__name__)

# 异步分析使用的 LLM 参数（服务级默认，用户自定义配置在领取时合并）
_ANALYSIS_CONFIG = LLMConfig(
    temperature=settings.AI_ANALYSIS_TEMPERATURE, max_tokens=settings.AI_ANALYSIS_MAX_TOKENS
)


def _public_task_error(exc: Exception) -> str:
    """S-1：异步任务对外只暴露固定错误文案，不返回上游响应/异常细节。"""
    if isinstance(exc, ValueError) and "API 密钥" in str(exc):
        return "未配置 AI API 密钥，请稍后重试"
    return "任务执行失败，请稍后重试"


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class _ClaimedTask(NamedTuple):
    task_id: str
    user_id: int
    payload: str
    created_at: datetime


def _run_llm_sync(messages: list, config: LLMConfig) -> dict:
    """在工作线程中同步执行 LLM 调用，返回 {content, tokens_used}。"""
    import asyncio

    loop = asyncio.new_event_loop()
    try:
        content, tokens_used = loop.run_until_complete(call_llm(messages, config))
        return {"content": content, "tokens_used": tokens_used}
    finally:
        loop.close()


class AsyncTaskQueue:
    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(
        self,
        max_workers: int | None = None,
        cleanup_interval_seconds: int | None = None,
        session_factory=None,
    ):
        # P-N2: 从 settings 读取队列参数（支持环境变量覆盖），而非硬编码默认值
        if max_workers is None:
            max_workers = settings.TASK_QUEUE_MAX_WORKERS
        if cleanup_interval_seconds is None:
            cleanup_interval_seconds = settings.TASK_RESULT_TTL // 2 or 60
        if self._initialized:
            return

        self.workers = []
        self.cleanup_thread: threading.Thread | None = None
        self.max_workers = max_workers
        self.cleanup_interval_seconds = max(1, cleanup_interval_seconds)
        self.running = False
        self.lock = threading.Lock()
        self._session_factory = session_factory or SessionLocal

        AsyncTaskQueue._initialized = True

    def start(self):
        if self.running:
            return

        self._recover_interrupted()
        self.running = True
        for _ in range(self.max_workers):
            worker = threading.Thread(target=self._worker, daemon=True)
            worker.start()
            self.workers.append(worker)

        # P1: 定期清理过期任务结果，防止 async_tasks 表无界增长
        self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self.cleanup_thread.start()
        logger.info("异步任务队列已启动，工作线程数: %d", self.max_workers)

    def _recover_interrupted(self):
        """启动恢复：上次进程被中断时停留在 running 的任务标记为 failed。"""
        session = self._session_factory()
        try:
            stale = (
                session.query(models.AsyncTask)
                .filter(models.AsyncTask.status == TaskStatus.RUNNING.value)
                .all()
            )
            now = datetime.now()
            for task in stale:
                task.status = TaskStatus.FAILED.value
                task.error = "任务执行中断，请重新提交"
                task.completed_at = now
                task.claim_token = None
            if stale:
                session.commit()
                logger.info("启动恢复：将 %d 个中断任务标记为 failed", len(stale))
        finally:
            session.close()

    def _cleanup_loop(self):
        """定时清理线程：按 settings.TASK_RESULT_TTL 过期已完成/失败任务"""
        max_age_seconds = max(0, int(settings.TASK_RESULT_TTL))
        while self.running:
            time.sleep(self.cleanup_interval_seconds)
            try:
                self.cleanup_old_tasks(max_age_seconds=max_age_seconds)
            except Exception as e:
                logger.error("定期清理异步任务失败: %s", e)

    def stop(self):
        self.running = False
        for worker in self.workers:
            worker.join(timeout=1)
        self.workers.clear()
        if self.cleanup_thread and self.cleanup_thread.is_alive():
            self.cleanup_thread.join(timeout=2)
            self.cleanup_thread = None
        logger.info("异步任务队列已停止")

    def _worker(self):
        while self.running:
            try:
                claimed = self._claim_task()
                if claimed is None:
                    time.sleep(0.5)
                    continue
                self._execute_task(claimed)
            except Exception as e:
                logger.error("工作线程异常: %s", e)
                time.sleep(0.5)

    def _claim_task(self) -> _ClaimedTask | None:
        """原子领取一个 pending 任务（跨进程安全：UPDATE 子查询 + 唯一领取令牌）。"""
        session = self._session_factory()
        try:
            token = uuid.uuid4().hex
            now = datetime.now()
            result = session.execute(
                text(
                    "UPDATE async_tasks "
                    "SET status = :running, claimed_at = :now, claim_token = :token "
                    "WHERE task_id = (SELECT task_id FROM async_tasks "
                    "  WHERE status = :pending ORDER BY id LIMIT 1)"
                ),
                {"running": TaskStatus.RUNNING.value, "pending": TaskStatus.PENDING.value,
                 "now": now, "token": token},
            )
            session.commit()
            if result.rowcount == 0:
                return None
            task = (
                session.query(models.AsyncTask)
                .filter(models.AsyncTask.claim_token == token)
                .first()
            )
            if task is None:
                return None
            return _ClaimedTask(
                task_id=task.task_id,
                user_id=task.user_id,
                payload=task.payload,
                created_at=task.created_at,
            )
        finally:
            session.close()

    def _execute_task(self, claimed: _ClaimedTask):
        """执行任务：领取时按 user_id 解析用户 AI 配置（密钥仅在内存，不落库），结果落 ai_analyses。"""
        session = self._session_factory()
        try:
            messages = json.loads(claimed.payload)["messages"]
            config = build_llm_config_for_user(session, claimed.user_id, _ANALYSIS_CONFIG)
            try:
                result = _run_llm_sync(messages, config)

                analysis = models.AIAnalysis(
                    user_id=claimed.user_id,
                    request_content="异步 AI 分析",
                    response_content=result["content"],
                    analysis_type="AI 异步分析",
                    tokens_used=result["tokens_used"],
                )
                session.add(analysis)
                session.commit()
                session.refresh(analysis)
                result["analysis_id"] = analysis.id

                task = (
                    session.query(models.AsyncTask)
                    .filter(models.AsyncTask.task_id == claimed.task_id)
                    .first()
                )
                task.status = TaskStatus.COMPLETED.value
                task.result = json.dumps(result)
                task.completed_at = datetime.now()
                task.claim_token = None
                session.commit()
            except Exception as exc:
                session.rollback()
                logger.error("任务 %s 执行失败 (error=%s)", claimed.task_id, type(exc).__name__)
                task = (
                    session.query(models.AsyncTask)
                    .filter(models.AsyncTask.task_id == claimed.task_id)
                    .first()
                )
                task.status = TaskStatus.FAILED.value
                task.error = _public_task_error(exc)
                task.completed_at = datetime.now()
                task.claim_token = None
                session.commit()
        finally:
            session.close()

    def submit_task(self, task_id: str, user_id: int, messages: list) -> str:
        """持久化提交异步分析任务：写入 async_tasks 表，状态 pending，等待 worker 领取。"""
        payload = json.dumps({"messages": messages})
        session = self._session_factory()
        try:
            session.add(
                models.AsyncTask(
                    task_id=task_id,
                    user_id=user_id,
                    status=TaskStatus.PENDING.value,
                    payload=payload,
                    created_at=datetime.now(),
                )
            )
            session.commit()
        finally:
            session.close()
        return task_id

    def get_task_status(self, task_id: str, user_id: int | None = None) -> dict[str, Any] | None:
        session = self._session_factory()
        try:
            task = (
                session.query(models.AsyncTask)
                .filter(models.AsyncTask.task_id == task_id)
                .first()
            )
            if task is None:
                return None
            if user_id is not None and task.user_id != user_id:
                return None
            return {
                "task_id": task.task_id,
                "status": task.status,
                "result": json.loads(task.result) if task.result else None,
                "error": task.error,
                "created_at": task.created_at.isoformat() if task.created_at else None,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            }
        finally:
            session.close()

    def is_task_completed(self, task_id: str) -> bool:
        status = self.get_task_status(task_id)
        return bool(status) and status["status"] in [
            TaskStatus.COMPLETED.value,
            TaskStatus.FAILED.value,
        ]

    def cleanup_old_tasks(self, max_age_seconds: int = 3600):
        """清理过期结果：已完成/失败按完成时间；pending/running 为有效工作不清理。"""
        now = datetime.now()
        session = self._session_factory()
        try:
            tasks = (
                session.query(models.AsyncTask)
                .filter(
                    models.AsyncTask.status.in_(
                        [TaskStatus.COMPLETED.value, TaskStatus.FAILED.value]
                    )
                )
                .all()
            )
            stale = [
                task
                for task in tasks
                if (now - (task.completed_at or task.created_at)).total_seconds() > max_age_seconds
            ]
            for task in stale:
                session.delete(task)
            if stale:
                session.commit()
                logger.info("清理过期异步任务 %d 个（TTL=%ds）", len(stale), max_age_seconds)
        finally:
            session.close()


task_queue = AsyncTaskQueue()


def start_task_queue():
    task_queue.start()


def stop_task_queue():
    task_queue.stop()
