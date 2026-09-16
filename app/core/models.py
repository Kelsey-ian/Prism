# -*- coding: utf-8 -*-
"""核心数据模型：媒体分类、任务状态、转换任务。"""
from __future__ import annotations

import enum
import os
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path


class MediaCategory(str, enum.Enum):
    AUDIO = "audio"
    VIDEO = "video"
    IMAGE = "image"


# 状态展示文案统一从这里取，避免各处硬编码
class TaskStatus(str, enum.Enum):
    WAITING = "waiting"
    RUNNING = "running"
    PAUSED = "paused"        # 已暂停（等待继续，未开始的任务可暂停）
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"
    SKIPPED = "skipped"

    @property
    def label(self) -> str:
        from app.i18n import t
        return {
            TaskStatus.WAITING: t("task.waiting"),
            TaskStatus.RUNNING: t("task.running"),
            TaskStatus.PAUSED: t("task.paused"),
            TaskStatus.COMPLETED: t("task.completed"),
            TaskStatus.FAILED: t("task.failed"),
            TaskStatus.CANCELED: t("task.canceled"),
            TaskStatus.SKIPPED: t("task.skipped"),
        }[self]


# 终结态集合
FINISHED_STATUSES = {
    TaskStatus.COMPLETED,
    TaskStatus.FAILED,
    TaskStatus.CANCELED,
    TaskStatus.SKIPPED,
}


@dataclass
class ConversionTask:
    """一次文件转换任务（纯数据对象，跨线程传递时只在 worker 线程写进度字段，
    UI 通过 QueueManager 的信号感知变化）。"""

    input_path: str
    output_dir: str                 # 输出目录（绝对路径）
    target_format: str              # 目标格式 id，如 mp3 / mp4 / png
    preset_id: str                  # 预设 id
    category: MediaCategory         # 源文件分类
    resolution: str = "source"      # 视频分辨率：source/480/720/1080/1440/2160
    fps: str = "source"             # 输出帧率：source/24/25/30/50/60
    conflict: str = "rename"        # rename / overwrite / skip

    tid: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    status: TaskStatus = TaskStatus.WAITING
    progress: float = 0.0           # 0~1；-1 表示不确定进度
    error: str = ""
    output_path: str = ""
    size: int = 0                   # 源文件大小（字节）
    duration: float = 0.0           # 媒体时长（秒），图片为 0
    meta_text: str = ""             # 时长 / 分辨率等展示信息
    created_at: float = field(default_factory=time.time)

    def __post_init__(self) -> None:
        if isinstance(self.category, str):
            self.category = MediaCategory(self.category)
        if isinstance(self.status, str):
            self.status = TaskStatus(self.status)
        if not self.size and os.path.exists(self.input_path):
            try:
                self.size = os.path.getsize(self.input_path)
            except OSError:
                pass

    @property
    def name(self) -> str:
        return Path(self.input_path).name

    @property
    def source_ext(self) -> str:
        return Path(self.input_path).suffix.lstrip(".").lower()

    def reset(self) -> None:
        """重置为可重新执行的状态。"""
        self.status = TaskStatus.WAITING
        self.progress = 0.0
        self.error = ""
        self.output_path = ""
