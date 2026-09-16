# -*- coding: utf-8 -*-
"""硬件检测与硬件加速选择。

检测内容（全部通过 Windows 系统 API / CIM 获取，不依赖第三方库）：
1. 系统架构：x64（AMD64）与 ARM64 原生识别；
2. 显卡厂商：Intel / AMD 核显，Intel / AMD / NVIDIA 独显；
3. CPU 厂商：Intel / AMD / ARM（高通骁龙等）；
4. 以本机内置 FFmpeg 的 -encoders 列表 + 实际编码冒烟测试，确认编码器可用。

加速策略（自动选择，可在设置中关闭）：
- NVIDIA 独显/核显 → NVENC（h264_nvenc / hevc_nvenc）
- Intel 核显/Arc   → Quick Sync（h264_qsv / hevc_qsv）
- AMD 核显/独显    → AMF（h264_amf / hevc_amf）
- ARM64 设备      → Media Foundation（h264_mf）
- 均不可用时回退 CPU 软件编码（libx264 / libx265）
解码统一使用 ffmpeg 的“-hwaccel auto”最佳努力硬件解码，失败自动回退。
"""
from __future__ import annotations

import platform
import subprocess
import threading
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from PySide6.QtCore import QObject, Signal

from ..config import app_config
from .ffmpeg import _CREATE_NO_WINDOW, ffmpeg_manager


# ------------------------------------------------------------ 架构识别


def detect_arch() -> str:
    """返回标准化架构标识：x64 / arm64 / x86 / arm。"""
    machine = platform.machine().lower()
    if machine in ("arm64", "aarch64"):
        return "arm64"
    if machine in ("amd64", "x86_64", "x64"):
        return "x64"
    if machine in ("x86", "i386", "i686"):
        return "x86"
    if machine.startswith("arm"):
        return "arm"
    return machine or "unknown"


# ------------------------------------------------------------ 数据结构


@dataclass
class GpuDevice:
    vendor: str          # nvidia / intel / amd / qualcomm / other
    name: str
    kind: str = "unknown"   # integrated（核显）/ discrete（独显）/ unknown


@dataclass
class CpuInfo:
    vendor: str          # intel / amd / arm / other
    name: str


@dataclass
class HwReport:
    """一次完整硬件探测的快照（跨线程只读共享）。"""
    arch: str = "x64"
    cpu: Optional[CpuInfo] = None
    gpus: List[GpuDevice] = field(default_factory=list)
    encoders: Set[str] = field(default_factory=set)
    verified: Dict[str, bool] = field(default_factory=dict)
    ffmpeg_ok: bool = False

    # ---------------- 厂商集合

    @property
    def gpu_vendors(self) -> Set[str]:
        return {g.vendor for g in self.gpus}

    # ---------------- 编码器选择

    def _candidate(self, codec: str) -> Optional[str]:
        """根据硬件厂商给出首选硬件编码器（不保证已验证）。"""
        if self.arch == "arm64":
            # ARM Windows：Media Foundation 硬件编码（d3d11/驱动转发到平台 MFT）
            return {"h264": "h264_mf", "hevc": "hevc_mf"}.get(codec)

        preference = [
            ("nvidia", {"h264": "h264_nvenc", "hevc": "hevc_nvenc"}),
            ("intel", {"h264": "h264_qsv", "hevc": "hevc_qsv"}),
            ("amd", {"h264": "h264_amf", "hevc": "hevc_amf"}),
        ]
        for vendor, mapping in preference:
            if vendor in self.gpu_vendors:
                return mapping.get(codec)
        return None

    def encoder_for(self, codec: str) -> Optional[str]:
        """返回已确认可用的硬件编码器；未验证或不可用返回 None（走软件编码）。"""
        if not app_config.get("hw_accel", True):
            return None
        encoder = self._candidate(codec)
        if not encoder:
            return None
        if encoder not in self.encoders:
            return None
        # 验证结果缺失时保守回退软件编码（探测完成后即自动启用）
        if not self.verified.get(encoder, False):
            return None
        return encoder

    @property
    def acceleration_mode(self) -> str:
        """当前实际会使用的加速模式标识。"""
        if not app_config.get("hw_accel", True):
            return "off"
        sample = self.encoder_for("h264") or ""
        if sample.endswith("_nvenc"):
            return "nvenc"
        if sample.endswith("_qsv"):
            return "qsv"
        if sample.endswith("_amf"):
            return "amf"
        if sample.endswith("_mf"):
            return "mf"
        if self.gpus and app_config.get("hw_accel", True):
            return "decode"   # 仅硬件解码可用
        return "cpu"

    # ---------------- 人类可读描述

    def mode_text(self) -> str:
        mode = self.acceleration_mode
        return {
            "nvenc": "NVIDIA NVENC 硬件编码 + 硬件解码",
            "qsv": "Intel Quick Sync 硬件编码 + 硬件解码",
            "amf": "AMD AMF 硬件编码 + 硬件解码",
            "mf": "Media Foundation 硬件编码 + 硬件解码（ARM 平台）",
            "decode": "硬件解码 + CPU 软件编码",
            "cpu": "CPU 软件编码（未检测到可用硬件编码器）",
            "off": "硬件加速已关闭，使用 CPU 软件编码",
        }.get(mode, "CPU 软件编码")

    def describe_lines(self) -> List[str]:
        lines: List[str] = []
        if self.cpu:
            label = {
                "intel": "Intel 处理器（软件编码优化）",
                "amd": "AMD 处理器（软件编码优化）",
                "arm": "ARM 处理器（ARM64 原生运行）",
            }.get(self.cpu.vendor, "处理器")
            lines.append(f"处理器：{self.cpu.name} · {label}")
        for gpu in self.gpus:
            kind = {"integrated": "核芯显卡", "discrete": "独立显卡"}.get(gpu.kind, "显卡")
            lines.append(f"显卡：{gpu.name} · {kind}")
        if self.arch == "arm64":
            lines.append("运行架构：ARM64（Windows on ARM 原生支持）")
        if not self.gpus and not self.cpu:
            lines.append("未能通过系统接口读取硬件信息，将使用 CPU 软件编码")
        lines.append("加速模式：" + self.mode_text())
        return lines


# ------------------------------------------------------------ 系统信息采集


_PS_SCRIPT = (
    "$ErrorActionPreference='SilentlyContinue';"
    "Write-Output '[GPU]';"
    "(Get-CimInstance Win32_VideoController).Name | ForEach-Object { Write-Output $_ };"
    "Write-Output '[CPU]';"
    "(Get-CimInstance Win32_Processor | Select-Object -First 1).Name"
)


def _query_system() -> tuple[List[str], str]:
    """通过 PowerShell CIM（系统 API）读取显卡 / CPU 名称。失败返回空。"""
    gpu_names: List[str] = []
    cpu_name = ""
    try:
        proc = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", _PS_SCRIPT],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            timeout=10, creationflags=_CREATE_NO_WINDOW,
        )
        section = ""
        for raw in proc.stdout.decode("utf-8", errors="ignore").splitlines():
            line = raw.strip()
            if line == "[GPU]":
                section = "gpu"
                continue
            if line == "[CPU]":
                section = "cpu"
                continue
            if not line:
                continue
            if section == "gpu":
                gpu_names.append(line)
            elif section == "cpu" and not cpu_name:
                cpu_name = line
    except (OSError, subprocess.SubprocessError):
        pass

    # 回退：老旧系统上的 wmic（25H2 已移除，仅兜底）
    if not gpu_names and not cpu_name:
        gpu_names, cpu_name = _query_system_wmic()
    return gpu_names, cpu_name


def _query_system_wmic() -> tuple[List[str], str]:
    gpu_names: List[str] = []
    cpu_name = ""
    try:
        proc = subprocess.run(
            ["wmic", "path", "Win32_VideoController", "get", "name"],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            timeout=10, creationflags=_CREATE_NO_WINDOW,
        )
        lines = proc.stdout.decode("utf-8", errors="ignore").splitlines()
        gpu_names = [x.strip() for x in lines[1:] if x.strip()]
    except (OSError, subprocess.SubprocessError):
        pass
    try:
        proc = subprocess.run(
            ["wmic", "cpu", "get", "name"],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            timeout=10, creationflags=_CREATE_NO_WINDOW,
        )
        lines = proc.stdout.decode("utf-8", errors="ignore").splitlines()
        for x in lines[1:]:
            if x.strip():
                cpu_name = x.strip()
                break
    except (OSError, subprocess.SubprocessError):
        pass
    return gpu_names, cpu_name


def _classify_gpu(name: str) -> GpuDevice:
    low = name.lower()
    if "nvidia" in low or "geforce" in low or "quadro" in low or "tesla" in low:
        return GpuDevice("nvidia", name, "discrete")
    if "intel" in low:
        discrete_marks = (
            "arc a3", "arc a5", "arc a7", "arc b", "arc pro", "flex",
            "max series", "iris xe max",
        )
        integrated_marks = ("hd graphics", "uhd", "iris", "arc graphics")
        if any(m in low for m in discrete_marks):
            kind = "discrete"
        elif any(m in low for m in integrated_marks):
            kind = "integrated"
        else:
            kind = "unknown"
        return GpuDevice("intel", name, kind)
    if any(k in low for k in ("amd", "radeon", "advanced micro", "ati ")):
        # APU 核显通常命名为 "AMD Radeon(TM) Graphics" / "Radeon 680M" 等
        integrated = (
            "radeon graphics" in low
            or low.endswith("m graphics")
            or "vega" in low and "rx vega" not in low
        )
        return GpuDevice("amd", name, "integrated" if integrated else "discrete")
    if any(k in low for k in ("qualcomm", "adreno", "snapdragon", "microsoft sq")):
        return GpuDevice("qualcomm", name, "integrated")
    if "microsoft basic" in low or "microsoft 基本" in low:
        return GpuDevice("other", name, "unknown")
    return GpuDevice("other", name, "unknown")


def _classify_cpu(name: str, arch: str) -> CpuInfo:
    low = name.lower()
    if arch == "arm64" or any(k in low for k in ("snapdragon", "sq1", "sq2", "sq3", "arm")):
        return CpuInfo("arm", name)
    if "intel" in low or "xeon" in low or "pentium" in low or "celeron" in low:
        return CpuInfo("intel", name)
    if any(k in low for k in ("amd", "ryzen", "epyc", "athlon", "threadripper")):
        return CpuInfo("amd", name)
    return CpuInfo("other", name or "未知处理器")


# ------------------------------------------------------------ 冒烟测试


def _verify_encoder(encoder: str) -> bool:
    """实际编码 10 帧到 null 复用器，确认硬件编码器真正可用。"""
    ok, _ = ffmpeg_manager.run_capture(
        [
            "-hide_banner", "-loglevel", "error",
            "-f", "lavfi", "-i", "testsrc2=size=256x144:rate=10:duration=1",
            "-an", "-c:v", encoder, "-frames:v", "10", "-f", "null", "-",
        ],
        timeout=20,
    )
    return ok


# ------------------------------------------------------------ 管理器


class HardwareManager(QObject):
    """硬件探测单例；探测在后台线程完成，完成后发射 detected 信号。"""

    detected = Signal(object)   # HwReport

    def __init__(self) -> None:
        super().__init__()
        self._lock = threading.Lock()
        self._report = HwReport(arch=detect_arch())
        self._probing = False

    @property
    def report(self) -> HwReport:
        with self._lock:
            return self._report

    def encoder_for(self, codec: str) -> Optional[str]:
        return self.report.encoder_for(codec)

    def hardware_decode_args(self) -> List[str]:
        """输入侧硬件解码参数；任何异常/不支持时 ffmpeg 自动回退软件解码。"""
        report = self.report
        if not app_config.get("hw_accel", True):
            return []
        if not report.ffmpeg_ok or not report.gpus:
            return []
        return ["-hwaccel", "auto"]

    def start_probe(self, force_verify: bool = False) -> bool:
        """启动后台探测；已有探测在跑则跳过。返回是否成功启动。"""
        with self._lock:
            if self._probing:
                return False
            self._probing = True
        thread = threading.Thread(
            target=self._probe_worker, args=(force_verify,), daemon=True
        )
        thread.start()
        return True

    # ------------------------------------------------------------ 探测线程

    @staticmethod
    def _read_cache(key: str) -> Optional[bool]:
        """读取编码器验证缓存（兼容 INI 存成字符串 / 布尔的情况）。"""
        raw = app_config.get(key, None)
        if raw is None:
            return None
        if isinstance(raw, bool):
            return raw
        text = str(raw).strip().lower()
        if text in ("1", "true", "yes", "on"):
            return True
        if text in ("0", "false", "no", "off"):
            return False
        return None

    def _probe_worker(self, force_verify: bool) -> None:
        try:
            arch = detect_arch()
            gpu_names, cpu_name = _query_system()
            gpus = [_classify_gpu(n) for n in gpu_names if n]
            # 过滤远程会话里的“虚拟/基础显示适配器”重复噪声
            gpus = [g for g in gpus if not (
                g.vendor == "other" and "microsoft basic" in g.name.lower()
                and any(x.vendor in ("nvidia", "intel", "amd") for x in gpus)
            )]
            cpu = _classify_cpu(cpu_name, arch) if cpu_name else None

            ffmpeg_ok = ffmpeg_manager.available
            encoders = ffmpeg_manager.supported_encoders() if ffmpeg_ok else set()

            # 需要实测的候选编码器（去重）
            pseudo = HwReport(arch=arch, gpus=gpus)
            candidates = []
            for codec in ("h264", "hevc"):
                enc = pseudo._candidate(codec)
                if enc and enc in encoders and enc not in candidates:
                    candidates.append(enc)

            verified: Dict[str, bool] = {}
            cache_key = ffmpeg_manager.version or "unknown"
            for enc in candidates:
                cached = self._read_cache(f"hw_ok_{enc}_{cache_key}")
                if cached is not None and not force_verify:
                    verified[enc] = cached
                    continue
                ok = _verify_encoder(enc)
                verified[enc] = ok
                app_config.set(f"hw_ok_{enc}_{cache_key}", "1" if ok else "0")
            app_config.sync()

            report = HwReport(
                arch=arch, cpu=cpu, gpus=gpus,
                encoders=set(encoders), verified=verified,
                ffmpeg_ok=ffmpeg_ok,
            )
            with self._lock:
                self._report = report
            # 应用退出阶段不再向 UI 发射信号，避免接收者已析构时的风险
            from PySide6.QtWidgets import QApplication
            if QApplication.instance() is not None:
                self.detected.emit(report)
        except Exception:
            # 探测永远不应影响主流程
            pass
        finally:
            with self._lock:
                self._probing = False


hw_manager = HardwareManager()
