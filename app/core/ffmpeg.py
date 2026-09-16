# -*- coding: utf-8 -*-
"""FFmpeg 可执行文件管理：定位、版本读取、媒体探测与统一执行入口。

定位优先级：用户手动指定 -> 项目内置 bin/ 目录 -> 系统 PATH。
所有外部进程调用统一从这里走，保证：
1. Windows 下不弹出黑色控制台窗口；
2. 路径以列表参数传递，天然兼容中文/空格路径；
3. 进度通过 `-progress pipe:1` 的机器可读输出解析，稳定可靠。
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from ..config import BIN_DIR

# Windows 进程创建标志：不弹控制台窗口
_CREATE_NO_WINDOW = 0x08000000

_VERSION_RE = re.compile(r"ffmpeg version (?:n)?(\d+(?:\.\d+)+)", re.IGNORECASE)


@dataclass
class MediaInfo:
    duration: float = 0.0          # 秒
    size: int = 0
    bitrate: int = 0
    width: int = 0
    height: int = 0
    has_audio: bool = False
    has_video: bool = False
    video_codec: str = ""
    audio_codec: str = ""
    format_name: str = ""

    @property
    def resolution(self) -> str:
        return f"{self.width}x{self.height}" if self.width and self.height else ""


class FFmpegNotFoundError(RuntimeError):
    pass


class FFmpegManager:
    """单例式 FFmpeg 管理器（无状态 UI 无关逻辑，可跨线程调用）。"""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._ffmpeg: Optional[str] = None
        self._ffprobe: Optional[str] = None
        self._version: Optional[str] = None
        self._source: str = ""
        self._muxers: Optional[set] = None
        self._encoders: Optional[set] = None

    # ------------------------------------------------------------ 定位 / 状态

    def locate(self, manual_path: str = "") -> bool:
        """按优先级定位 ffmpeg / ffprobe，成功返回 True。"""
        with self._lock:
            candidates: List[Tuple[str, str]] = []  # (ffmpeg, 来源)

            if manual_path and Path(manual_path).is_file():
                candidates.append((manual_path, "手动指定"))

            bundled = BIN_DIR / "ffmpeg.exe"
            if bundled.is_file():
                candidates.append((str(bundled), "内置版本"))

            system_ffmpeg = shutil.which("ffmpeg")
            if system_ffmpeg:
                candidates.append((system_ffmpeg, "系统 PATH"))

            for ffmpeg_path, source in candidates:
                ffprobe_path = str(Path(ffmpeg_path).with_name("ffprobe.exe"))
                if not Path(ffprobe_path).is_file():
                    alt = shutil.which("ffprobe")
                    if alt:
                        ffprobe_path = alt
                version = self._read_version(ffmpeg_path)
                if version:
                    self._ffmpeg = ffmpeg_path
                    self._ffprobe = ffprobe_path if Path(ffprobe_path).is_file() else ""
                    self._source = source
                    self._version = version
                    self._muxers = None
                    self._encoders = None
                    return True
            self._ffmpeg = None
            self._ffprobe = None
            self._version = None
            self._source = ""
            return False

    @property
    def available(self) -> bool:
        if self._ffmpeg is None:
            self.locate()
        return bool(self._ffmpeg)

    @property
    def ffmpeg_path(self) -> str:
        if not self.available:
            raise FFmpegNotFoundError("未找到 FFmpeg，可在“设置”中下载或手动指定。")
        return self._ffmpeg or ""

    @property
    def ffprobe_path(self) -> str:
        return self._ffprobe or ""

    @property
    def version(self) -> str:
        return self._version or ""

    @property
    def source(self) -> str:
        return self._source or ""

    def status_text(self) -> Tuple[bool, str]:
        """供设置页展示的状态摘要。"""
        if self.available:
            probe = "（含 ffprobe）" if self._ffprobe else "（缺少 ffprobe，媒体信息不可用）"
            return True, f"已就绪 · FFmpeg {self._version} · {self._source}{probe}"
        return False, "未找到 FFmpeg，请点击下方按钮自动下载内置版本"

    # ------------------------------------------------------------ 版本读取

    def _read_version(self, ffmpeg_path: str) -> str:
        try:
            proc = subprocess.run(
                [ffmpeg_path, "-version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=8,
                creationflags=_CREATE_NO_WINDOW,
            )
        except (OSError, subprocess.SubprocessError):
            return ""
        head = proc.stdout.decode("utf-8", errors="ignore")[:300]
        match = _VERSION_RE.search(head)
        return match.group(1) if match else ""

    def refresh_version(self) -> str:
        """重新读取当前 ffmpeg 版本（更新后调用）。"""
        if self._ffmpeg:
            self._version = self._read_version(self._ffmpeg) or self._version
        return self.version

    # ------------------------------------------------------------ 能力探测

    def supported_muxers(self, force: bool = False) -> set:
        """获取当前 ffmpeg 支持的复用器（输出封装）集合。"""
        if self._muxers is not None and not force:
            return self._muxers
        muxers: set = set()
        try:
            proc = subprocess.run(
                [self.ffmpeg_path, "-hide_banner", "-muxers"],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                timeout=15, creationflags=_CREATE_NO_WINDOW,
            )
            for line in proc.stdout.decode("utf-8", errors="ignore").splitlines():
                # 形如 "  E mp4             MP4 (MPEG-4 Part 14)"
                parts = line.split()
                if len(parts) >= 3 and parts[0] in ("E", "D", "DE") and parts[1] != "=":
                    muxers.add(parts[1].strip(","))
        except (OSError, subprocess.SubprocessError, FFmpegNotFoundError):
            pass
        self._muxers = muxers
        return muxers

    def supported_encoders(self, force: bool = False) -> set:
        """获取当前 ffmpeg 编译进的编码器集合（如 h264_nvenc / h264_qsv）。"""
        if self._encoders is not None and not force:
            return self._encoders
        encoders: set = set()
        try:
            proc = subprocess.run(
                [self.ffmpeg_path, "-hide_banner", "-encoders"],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                timeout=15, creationflags=_CREATE_NO_WINDOW,
            )
            for line in proc.stdout.decode("utf-8", errors="ignore").splitlines():
                # 形如 " V....D h264_nvenc           NVIDIA NVENC H.264 encoder"
                parts = line.split()
                if len(parts) >= 2 and parts[0].startswith("V") and parts[0] != "V":
                    encoders.add(parts[1])
        except (OSError, subprocess.SubprocessError, FFmpegNotFoundError):
            pass
        self._encoders = encoders
        return encoders

    def run_capture(self, args: List[str], timeout: int = 20) -> Tuple[bool, str]:
        """执行短命令并收集输出（供硬件编码冒烟测试使用）。"""
        cmd = [self.ffmpeg_path] + args
        try:
            proc = subprocess.run(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                timeout=timeout, creationflags=_CREATE_NO_WINDOW,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            return False, str(exc)
        text = proc.stdout.decode("utf-8", errors="ignore")
        return proc.returncode == 0, text

    def probe(self, input_path: str) -> MediaInfo:
        """使用 ffprobe 读取媒体信息；ffprobe 缺失或失败时退回基础文件信息。"""
        info = MediaInfo()
        try:
            info.size = os.path.getsize(input_path)
        except OSError:
            pass

        if not self._ffprobe:
            return info

        try:
            proc = subprocess.run(
                [
                    self._ffprobe, "-v", "error",
                    "-print_format", "json",
                    "-show_format", "-show_streams",
                    input_path,
                ],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                timeout=20, creationflags=_CREATE_NO_WINDOW,
            )
        except (OSError, subprocess.SubprocessError):
            return info

        if proc.returncode != 0:
            return info
        try:
            data = json.loads(proc.stdout.decode("utf-8", errors="ignore"))
        except json.JSONDecodeError:
            return info

        fmt = data.get("format", {})
        info.format_name = fmt.get("format_name", "")
        try:
            info.duration = float(fmt.get("duration", 0) or 0)
        except (TypeError, ValueError):
            info.duration = 0
        try:
            info.bitrate = int(float(fmt.get("bit_rate", 0) or 0))
        except (TypeError, ValueError):
            info.bitrate = 0

        for stream in data.get("streams", []):
            codec_type = stream.get("codec_type")
            if codec_type == "video" and not info.has_video:
                info.has_video = True
                info.video_codec = stream.get("codec_name", "")
                info.width = int(stream.get("width", 0) or 0)
                info.height = int(stream.get("height", 0) or 0)
            elif codec_type == "audio" and not info.has_audio:
                info.has_audio = True
                info.audio_codec = stream.get("codec_name", "")
        return info

    # ------------------------------------------------------------ 执行转换

    def run(
        self,
        args: List[str],
        cancel_event: Optional[threading.Event] = None,
        progress_cb: Optional[Callable[[float], None]] = None,
        total_duration: float = 0.0,
        pause_event: Optional[threading.Event] = None,
    ) -> Tuple[bool, str, Optional[int]]:
        """执行一条 ffmpeg 命令。

        参数 args 为 ffmpeg 之后的完整参数列表；通过 -progress pipe:1
        输出的 out_time_us 计算 0~1 进度。stderr 合并进 stdout 统一读取，
        避免管道阻塞死锁。

        Returns:
            (success, message, pid) — pid 供外部挂起/恢复使用；失败时为 None。
        """
        from app.core.process_ctrl import resume_process, suspend_process

        cmd = [self.ffmpeg_path] + args
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                creationflags=_CREATE_NO_WINDOW,
            )
        except OSError as exc:
            return False, f"无法启动 FFmpeg：{exc}", None

        error_lines: List[str] = []
        last_progress = -1.0
        step_duration = max(total_duration, 0.0)
        proc_pid = proc.pid

        # 取消看门狗
        watchdog: Optional[threading.Thread] = None
        if cancel_event is not None:
            def _watch_cancel() -> None:
                if cancel_event.wait(timeout=1.0):
                    self.terminate(proc)
                while proc.poll() is None:
                    if cancel_event.wait(timeout=0.5):
                        self.terminate(proc)
                        break

            watchdog = threading.Thread(target=_watch_cancel, daemon=True)
            watchdog.start()

        # 暂停看门狗：事件被清除时挂起进程，设置时恢复
        pause_watchdog: Optional[threading.Thread] = None
        if pause_event is not None:
            def _watch_pause() -> None:
                was_paused = False
                while proc.poll() is None:
                    if pause_event.is_set() and not was_paused:
                        suspend_process(proc_pid)
                        was_paused = True
                    elif not pause_event.is_set() and was_paused:
                        resume_process(proc_pid)
                        was_paused = False
                    pause_event.wait(0.4)
                # 进程结束时确保恢复（防止系统资源泄漏）
                if was_paused:
                    resume_process(proc_pid)

            pause_watchdog = threading.Thread(target=_watch_pause, daemon=True)
            pause_watchdog.start()

        assert proc.stdout is not None
        for line in proc.stdout:
            line = line.strip()
            if not line:
                continue
            if line[0].isalpha() and "=" in line:
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip()
                if key in ("out_time_us", "out_time_ms") and progress_cb and step_duration > 0:
                    try:
                        us = int(value)
                        if key == "out_time_ms" and us > 10 ** 12:
                            pass
                        frac = min(max(us / 1_000_000.0 / step_duration, 0.0), 0.99)
                        if frac != last_progress:
                            progress_cb(frac)
                            last_progress = frac
                    except ValueError:
                        pass
                elif key == "progress" and value == "end" and progress_cb:
                    progress_cb(1.0)
            else:
                if not line.startswith(("frame=", "fps=", "bitrate=")):
                    error_lines.append(line)

        proc.wait()

        if cancel_event is not None and cancel_event.is_set():
            return False, "用户已取消转换", proc_pid

        if proc.returncode != 0:
            tail = "\n".join(error_lines[-6:]) or f"FFmpeg 退出码 {proc.returncode}"
            return False, tail, proc_pid
        return True, "", proc_pid

    def terminate(self, proc: subprocess.Popen) -> None:
        """温和终止，失败则强杀。"""
        try:
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
        except OSError:
            pass


# 全局单例
ffmpeg_manager = FFmpegManager()
