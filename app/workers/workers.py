# -*- coding: utf-8 -*-
"""后台工作线程：转换任务执行器 / 媒体信息探测 / 通用函数线程。"""
from __future__ import annotations

import os
import threading
import traceback
from typing import Callable, Optional

from PySide6.QtCore import QObject, QRunnable, QThread, Signal

from app.core.converter import build_commands
from app.core.ffmpeg import ffmpeg_manager
from app.core.models import ConversionTask, MediaCategory, TaskStatus
from app.core.presets import detect_category, format_duration, iter_media_files


class ConvertWorker(QRunnable):
    """执行单个 ConversionTask（可能包含多步 ffmpeg 命令）。"""

    class Signals(QObject):
        started = Signal(str)
        progress = Signal(str, float)
        finished = Signal(str, str, str)   # tid, TaskStatus 值, 消息

    def __init__(self, task: ConversionTask, cancel_event: threading.Event,
                 pause_event: Optional[threading.Event] = None) -> None:
        super().__init__()
        self.task = task
        self.cancel_event = cancel_event
        self.pause_event = pause_event or threading.Event()
        self.signals = self.Signals()
        self.setAutoDelete(True)

    def run(self) -> None:
        task = self.task
        self.signals.started.emit(task.tid)
        task.status = TaskStatus.RUNNING
        task.error = ""

        try:
            info = ffmpeg_manager.probe(task.input_path)
            if not task.size:
                task.size = info.size
            task.duration = info.duration
            commands, total = build_commands(task, info)
        except Exception as exc:  # 构建阶段异常（如输出目录不可写）
            task.status = TaskStatus.FAILED
            task.error = str(exc)
            self.signals.finished.emit(task.tid, task.status.value, task.error)
            return

        # resolve_output_path 判定为跳过
        if not commands:
            if task.status == TaskStatus.SKIPPED:
                self.signals.finished.emit(task.tid, TaskStatus.SKIPPED.value, "目标已存在")
                return
            self.signals.finished.emit(
                task.tid, TaskStatus.FAILED.value, "未能构建转换命令"
            )
            return

        step_count = len(commands)
        last_status = TaskStatus.COMPLETED
        last_message = ""

        for index, cmd in enumerate(commands):
            if self.cancel_event.is_set():
                last_status = TaskStatus.CANCELED
                last_message = "用户已取消转换"
                break

            def _cb(frac: float, _i=index, _n=step_count) -> None:
                self.signals.progress.emit(task.tid, (_i + frac) / _n)

            # 第 2 步开始时给一个基础进度（调色板生成阶段）
            if index > 0:
                self.signals.progress.emit(task.tid, index / step_count)

            ok, message, _pid = ffmpeg_manager.run(
                cmd,
                cancel_event=self.cancel_event,
                progress_cb=_cb,
                total_duration=total,
                pause_event=self.pause_event,
            )
            if not ok:
                if self.cancel_event.is_set() or "取消" in message:
                    last_status = TaskStatus.CANCELED
                    last_message = "用户已取消转换"
                else:
                    last_status = TaskStatus.FAILED
                    last_message = self._friendly_error(message)
                break

        # 清理临时调色板
        for cmd in commands:
            for part in cmd:
                if isinstance(part, str) and part.endswith("_palette.png"):
                    try:
                        os.remove(part)
                    except OSError:
                        pass

        task.status = last_status
        task.error = last_message
        if last_status == TaskStatus.COMPLETED:
            task.progress = 1.0
            self.signals.progress.emit(task.tid, 1.0)
        self.signals.finished.emit(task.tid, last_status.value, last_message)

    @staticmethod
    def _friendly_error(raw: str) -> str:
        """从 ffmpeg 输出中提炼用户可理解的错误结论。"""
        text = raw.strip()
        hints = (
            ("unknown encoder", "当前 FFmpeg 版本不包含该编码器，请更新内置 FFmpeg"),
            ("invalid data found", "文件已损坏或不是有效的媒体文件"),
            ("permission denied", "没有写入权限，请更换输出目录"),
            ("no such file", "文件不存在或路径无效"),
            ("already exists", "目标文件已存在"),
            ("could not find codec", "源文件编码不受支持，尝试更新 FFmpeg"),
        )
        lowered = text.lower()
        for needle, friendly in hints:
            if isinstance(needle, str) and needle.lower() in lowered:
                return f"{friendly}\n（{text.splitlines()[-1][:120]}）"
        return text[-240:] if text else "未知错误"


class MetaProbeWorker(QRunnable):
    """批量探测文件的媒体信息（时长/分辨率），用于文件列表展示。"""

    class Signals(QObject):
        ready = Signal(str, float, str)   # 文件路径, 时长, 展示文本

    def __init__(self, path: str) -> None:
        super().__init__()
        self.path = path
        self.signals = self.Signals()
        self.setAutoDelete(True)

    def run(self) -> None:
        try:
            if not ffmpeg_manager.available:
                return
            info = ffmpeg_manager.probe(self.path)
            cat = detect_category(self.path)
            if cat is not None and cat.value == "image" and info.resolution:
                text = info.resolution
            elif info.duration:
                text = format_duration(info.duration)
                if info.resolution:
                    text = f"{info.resolution} · {text}"
            else:
                text = info.resolution
            if text:
                self.signals.ready.emit(self.path, info.duration, text)
        except Exception:
            pass


class FileScanWorker(QRunnable):
    """后台扫描拖入 / 选择的文件或文件夹，返回分类后列表与不支持的项。"""

    class Signals(QObject):
        scanned = Signal(list, list)   # collected: List[Tuple[str, MediaCategory, int]], unsupported: List[str]

    def __init__(self, paths: list) -> None:
        super().__init__()
        self.paths = paths
        self.signals = self.Signals()
        self.setAutoDelete(True)

    def run(self) -> None:
        collected: list = []
        unsupported: list = []
        for raw in self.paths:
            path = os.path.normpath(raw)
            if os.path.isdir(path):
                found = iter_media_files(path)
                if not found:
                    unsupported.append(os.path.basename(path))
                collected.extend(found)
            elif os.path.isfile(path):
                cat = detect_category(path)
                if cat is None:
                    unsupported.append(os.path.basename(path))
                else:
                    collected.append((path, cat))

        # 预取文件大小，避免 UI 线程逐个 stat()
        sized: list = []
        for path, cat in collected:
            try:
                size = os.path.getsize(path)
            except OSError:
                size = 0
            sized.append((path, cat, size))
        self.signals.scanned.emit(sized, unsupported)


class FunctionThread(QThread):
    """在后台线程执行任意阻塞函数（用于版本检查 / 下载更新）。"""

    failed = Signal(str)

    def __init__(self, func: Callable, *args, **kwargs) -> None:
        super().__init__()
        self._func = func
        self._args = args
        self._kwargs = kwargs

    def run(self) -> None:
        try:
            self._func(*self._args, **self._kwargs)
        except Exception:
            self.failed.emit(traceback.format_exc(limit=2))
