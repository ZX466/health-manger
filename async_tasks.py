"""
异步任务处理模块
参考 TongueDiagnosis 项目的队列处理设计
支持后台任务执行和状态查询
"""

import logging
import queue
import threading
from typing import Callable, Dict, Any, Optional
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskResult:
    def __init__(self, task_id: str, user_id: Optional[int] = None):
        self.task_id = task_id
        self.user_id = user_id
        self.status = TaskStatus.PENDING
        self.result: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None
        self.created_at = datetime.now()
        self.completed_at: Optional[datetime] = None

    def set_running(self):
        self.status = TaskStatus.RUNNING

    def set_completed(self, result: Dict[str, Any]):
        self.status = TaskStatus.COMPLETED
        self.result = result
        self.completed_at = datetime.now()

    def set_failed(self, error: str):
        self.status = TaskStatus.FAILED
        self.error = error
        self.completed_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }


class AsyncTaskQueue:
    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, max_workers: int = 2):
        if self._initialized:
            return

        self.task_queue = queue.Queue()
        self.results: Dict[str, TaskResult] = {}
        self.workers = []
        self.max_workers = max_workers
        self.running = False
        self.lock = threading.Lock()

        AsyncTaskQueue._initialized = True

    def start(self):
        if self.running:
            return

        self.running = True
        for i in range(self.max_workers):
            worker = threading.Thread(target=self._worker, daemon=True)
            worker.start()
            self.workers.append(worker)
        logger.info("异步任务队列已启动，工作线程数: %d", self.max_workers)

    def stop(self):
        self.running = False
        for worker in self.workers:
            worker.join(timeout=1)
        self.workers.clear()
        logger.info("异步任务队列已停止")

    def _worker(self):
        while self.running:
            try:
                task = self.task_queue.get(timeout=1)
                if task is None:
                    continue

                task_id, func, args, kwargs, callback = task

                with self.lock:
                    if task_id in self.results:
                        self.results[task_id].set_running()

                try:
                    result = func(*args, **kwargs)

                    with self.lock:
                        if task_id in self.results:
                            self.results[task_id].set_completed(result)

                    if callback:
                        callback(task_id, result)

                except Exception as e:
                    with self.lock:
                        if task_id in self.results:
                            self.results[task_id].set_failed(str(e))
                    logger.error("任务 %s 执行失败: %s", task_id, e)

                finally:
                    self.task_queue.task_done()

            except queue.Empty:
                continue
            except Exception as e:
                logger.error("工作线程异常: %s", e)

    def submit_task(self, task_id: str, func: Callable,
                    args: tuple = (), kwargs: dict = None,
                    callback: Callable = None, user_id: Optional[int] = None) -> str:
        if kwargs is None:
            kwargs = {}

        with self.lock:
            self.results[task_id] = TaskResult(task_id, user_id=user_id)

        self.task_queue.put((task_id, func, args, kwargs, callback))

        return task_id

    def get_task_status(self, task_id: str, user_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        with self.lock:
            if task_id in self.results:
                if user_id is not None and self.results[task_id].user_id != user_id:
                    return None
                return self.results[task_id].to_dict()
        return None

    def is_task_completed(self, task_id: str) -> bool:
        with self.lock:
            if task_id in self.results:
                return self.results[task_id].status in [TaskStatus.COMPLETED, TaskStatus.FAILED]
        return False

    def get_task_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        with self.lock:
            if task_id in self.results and self.results[task_id].status == TaskStatus.COMPLETED:
                return self.results[task_id].result
        return None

    def cleanup_old_tasks(self, max_age_seconds: int = 3600):
        now = datetime.now()
        with self.lock:
            to_remove = []
            for task_id, result in self.results.items():
                if result.completed_at:
                    age = (now - result.completed_at).total_seconds()
                    if age > max_age_seconds:
                        to_remove.append(task_id)

            for task_id in to_remove:
                del self.results[task_id]


task_queue = AsyncTaskQueue()


def start_task_queue():
    task_queue.start()


def stop_task_queue():
    task_queue.stop()
