# -*- coding: utf-8 -*-
"""Windows 进程挂起/恢复。

使用 NtSuspendProcess / NtResumeProcess 实现 FFmpeg 进程的无缝暂停与恢复。
仅在 Windows 下可用；其他平台通过"停止调度 + 运行中任务继续"的方式实现队列级暂停。
"""
from __future__ import annotations

import ctypes
import sys
from typing import Optional


_NtSuspendProcess = None
_NtResumeProcess = None
_kernel32 = None


def _load_api() -> bool:
    """动态加载 ntdll 的挂起/恢复函数。"""
    global _NtSuspendProcess, _NtResumeProcess, _kernel32
    if _NtSuspendProcess is not None:
        return True
    if sys.platform != "win32":
        return False
    try:
        ntdll = ctypes.WinDLL("ntdll", use_last_error=True)
        _NtSuspendProcess = ntdll.NtSuspendProcess
        _NtResumeProcess = ntdll.NtResumeProcess
        _NtSuspendProcess.argtypes = [ctypes.c_void_p]
        _NtResumeProcess.argtypes = [ctypes.c_void_p]
        _NtSuspendProcess.restype = ctypes.c_long
        _NtResumeProcess.restype = ctypes.c_long
        _kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        return True
    except OSError:
        return False


def suspend_process(pid: int) -> bool:
    """挂起指定 PID 的进程。成功返回 True。"""
    if not _load_api():
        return False
    try:
        handle = _kernel32.OpenProcess(0x1FFFFF, False, pid)  # PROCESS_ALL_ACCESS
        if not handle:
            return False
        ret = _NtSuspendProcess(handle)
        _kernel32.CloseHandle(handle)
        return ret == 0
    except (OSError, AttributeError):
        return False


def resume_process(pid: int) -> bool:
    """恢复指定 PID 的进程。成功返回 True。"""
    if not _load_api():
        return False
    try:
        handle = _kernel32.OpenProcess(0x1FFFFF, False, pid)
        if not handle:
            return False
        ret = _NtResumeProcess(handle)
        _kernel32.CloseHandle(handle)
        return ret == 0
    except (OSError, AttributeError):
        return False


def is_available() -> bool:
    """检测当前平台是否支持进程挂起/恢复。"""
    return _load_api()
