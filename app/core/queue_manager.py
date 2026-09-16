# -*- coding: utf-8 -*-
"""转换任务队列：并发调度、取消、重试。

UI 线程只通过信号感知任务变化；任务执行在 QThreadPool 的 worker 线程中。
队列支持“暂停调度”（等待中的任务不再启动，正在运行的继续完成）。
"""
from __future__ import annotations

import threading
from typing import Dict, List, Optional

from PySide6.QtCore import QObject, QThreadPool, Signal

from app.config import app_config
from app.workers.workers import ConvertWorker

from .models import FINISHED_STATUSES, ConversionTask, TaskStatus


class QueueManager(QObject):
    task_added = Signal(str)              # tid
    task_removed = Signal(str)            # tid
    task_updated = Signal(str)            # tid（进度 / 状态变化）
    task_started = Signal(str)            # tid
    task_finished = Signal(str, str)      # tid, TaskStatus 值
    queue_changed = Signal()
    paused_changed = Signal(bool)

    def __init__(self) -> None:
        super().__init__()
        self._tasks: Dict[str, ConversionTask] = {}
        self._cancel_events: Dict[str, threading.Event] = {}
        self._pause_events: Dict[str, threading.Event] = {}
        self._running: set[str] = set()
        self._paused = False

        self.pool = QThreadPool(self)
        self.pool.setMaxThreadCount(max(1, int(app_config.get("concurrency", 2))))

    # ------------------------------------------------------------ 属性

    @property
    def paused(self) -> bool:
        return self._paused

    def tasks(self) -> List[ConversionTask]:
        return list(self._tasks.values())

    def get(self, tid: str) -> Optional[ConversionTask]:
        return self._tasks.get(tid)

    def is_running(self, tid: str) -> bool:
        return tid in self._running

    def running_count(self) -> int:
        return len(self._running)

    def waiting_count(self) -> int:
        return sum(1 for t in self._tasks.values() if t.status == TaskStatus.WAITING)

    def has_active(self) -> bool:
        return bool(self._running) or self.waiting_count() > 0

    # ------------------------------------------------------------ 入队 / 调度

    def enqueue(self, task: ConversionTask) -> str:
        self._tasks[task.tid] = task
        self.task_added.emit(task.tid)
        self.queue_changed.emit()
        self._dispatch()
        return task.tid

    def enqueue_many(self, tasks: List[ConversionTask]) -> List[str]:
        ids = []
        for task in tasks:
            self._tasks[task.tid] = task
            ids.append(task.tid)
            self.task_added.emit(task.tid)
        self.queue_changed.emit()
        self._dispatch()
        return ids

    def _dispatch(self) -> None:
        if self._paused:
            return
        for task in self._tasks.values():
            if len(self._running) >= self.pool.maxThreadCount():
                break
            if task.status == TaskStatus.WAITING and task.tid not in self._running:
                self._start(task)

    def _start(self, task: ConversionTask) -> None:
        event = threading.Event()
        pause_event = threading.Event()
        self._cancel_events[task.tid] = event
        self._pause_events[task.tid] = pause_event
        self._running.add(task.tid)
        worker = ConvertWorker(task, event, pause_event)
        worker.signals.started.connect(self._on_started)
        worker.signals.progress.connect(self._on_progress)
        worker.signals.finished.connect(self._on_finished)
        self.pool.start(worker)

    # ------------------------------------------------------------ worker 信号

    def _on_started(self, tid: str) -> None:
        self.task_started.emit(tid)
        self.task_updated.emit(tid)
        self.queue_changed.emit()

    def _on_progress(self, tid: str, value: float) -> None:
        task = self._tasks.get(tid)
        if task:
            task.progress = value
            self.task_updated.emit(tid)

    def _on_finished(self, tid: str, status_value: str, message: str) -> None:
        task = self._tasks.get(tid)
        if task:
            task.status = TaskStatus(status_value)
            task.error = message
        self._running.discard(tid)
        self._cancel_events.pop(tid, None)
        self._pause_events.pop(tid, None)
        self.task_updated.emit(tid)
        self.task_finished.emit(tid, status_value)
        self.queue_changed.emit()
        self._dispatch()

    # ------------------------------------------------------------ 控制操作

    def cancel(self, tid: str) -> None:
        """取消单个任务（等待中直接标记，运行中终止进程）。"""
        task = self._tasks.get(tid)
        if not task:
            return
        if tid in self._running:
            event = self._cancel_events.get(tid)
            if event:
                event.set()
        elif task.status == TaskStatus.WAITING:
            task.status = TaskStatus.CANCELED
            task.error = "用户已取消转换"
            self.task_updated.emit(tid)
            self.task_finished.emit(tid, TaskStatus.CANCELED.value)
            self.queue_changed.emit()

    def cancel_all(self) -> None:
        for tid in list(self._running):
            event = self._cancel_events.get(tid)
            if event:
                event.set()
        for task in self._tasks.values():
            if task.status == TaskStatus.WAITING:
                task.status = TaskStatus.CANCELED
                task.error = "用户已取消转换"
                self.task_updated.emit(task.tid)
                self.task_finished.emit(task.tid, TaskStatus.CANCELED.value)
        self.queue_changed.emit()

    def pause_task(self, tid: str) -> bool:
        """暂停单个正在运行的任务。"""
        pause_event = self._pause_events.get(tid)
        if pause_event is None:
            return False
        pause_event.set()
        task = self._tasks.get(tid)
        if task:
            task.status = TaskStatus.PAUSED
            self.task_updated.emit(tid)
        return True

    def resume_task(self, tid: str) -> bool:
        """恢复单个已暂停的任务。"""
        pause_event = self._pause_events.get(tid)
        if pause_event is None:
            return False
        pause_event.clear()
        task = self._tasks.get(tid)
        if task:
            task.status = TaskStatus.RUNNING
            self.task_updated.emit(tid)
        return True

    def pause_all_running(self) -> int:
        """暂停所有运行中的任务，返回暂停的任务数。"""
        count = 0
        for tid in list(self._running):
            if self.pause_task(tid):
                count += 1
        return count

    def resume_all_paused(self) -> int:
        """恢复所有已暂停的任务，返回恢复的任务数。"""
        count = 0
        for tid in list(self._pause_events):
            if self.resume_task(tid):
                count += 1
        return count

    def retry(self, tid: str) -> bool:
        task = self._tasks.get(tid)
        if not task or tid in self._running:
            return False
        if task.status not in FINISHED_STATUSES:
            return False
        task.reset()
        self.task_updated.emit(tid)
        self.queue_changed.emit()
        self._dispatch()
        return True

    def retry_failed(self) -> int:
        count = 0
        for task in list(self._tasks.values()):
            if task.status in (TaskStatus.FAILED, TaskStatus.CANCELED):
                task.reset()
                self.task_updated.emit(task.tid)
                count += 1
        if count:
            self.queue_changed.emit()
            self._dispatch()
        return count

    def remove(self, tid: str) -> bool:
        if tid in self._running:
            return False
        if self._tasks.pop(tid, None) is not None:
            self._cancel_events.pop(tid, None)
            self.task_removed.emit(tid)
            self.queue_changed.emit()
            return True
        return False

    def clear_finished(self) -> int:
        removable = [
            tid for tid, task in self._tasks.items()
            if task.status in FINISHED_STATUSES and tid not in self._running
        ]
        for tid in removable:
            self._tasks.pop(tid, None)
            self.task_removed.emit(tid)
        if removable:
            self.queue_changed.emit()
        return len(removable)

    def set_paused(self, paused: bool) -> None:
        if self._paused == paused:
            return
        self._paused = paused
        self.paused_changed.emit(paused)
        if not paused:
            self._dispatch()

    def set_concurrency(self, count: int) -> None:
        count = max(1, min(8, int(count)))
        app_config.set("concurrency", count)
        self.pool.setMaxThreadCount(count)
        if count > 1:
            self._dispatch()

    def shutdown(self) -> None:
        """应用退出时调用：取消所有任务并等待线程结束。"""
        self._paused = True
        for event in self._cancel_events.values():
            event.set()
        self.pool.waitForDone(3000)
