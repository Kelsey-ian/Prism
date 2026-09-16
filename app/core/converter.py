# -*- coding: utf-8 -*-
"""转换命令构建：ConversionTask -> ffmpeg 命令（可能是多步，如 GIF 调色板）。"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import List, Optional, Tuple

from .models import ConversionTask, MediaCategory, TaskStatus
from .presets import GIF_WIDTH, get_target
from .ffmpeg import MediaInfo
from .hardware import hw_manager

_BASE_ARGS = ["-y", "-hide_banner", "-loglevel", "error", "-progress", "pipe:1"]

# 软件编码器 -> 编码器族
_SW_CODECS = {"libx264": "h264", "libx265": "hevc"}


def resolve_output_path(task: ConversionTask) -> Optional[str]:
    """根据冲突策略确定最终输出路径。

    返回 None 表示该任务应跳过（目标已存在且策略为 skip）。
    """
    target = get_target(task.target_format, task.category)
    out_dir = Path(task.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    candidate = out_dir / f"{Path(task.input_path).stem}.{target.ext}"

    if not candidate.exists():
        return str(candidate)

    if task.conflict == "overwrite":
        return str(candidate)
    if task.conflict == "skip":
        return None

    # rename：自动追加 (1)、(2)…
    index = 1
    while True:
        renamed = out_dir / f"{candidate.stem} ({index}){candidate.suffix}"
        if not renamed.exists():
            return str(renamed)
        index += 1


def _video_filter(task: ConversionTask, info: MediaInfo) -> List[str]:
    """分辨率缩放参数（向下兼容，不放大；宽高保持偶数）。

    支持两种形式：
    - 预设高度（"480" / "720" / "1080" …）：宽度按比例自适应，不放大
    - 自定义 "WxH"（如 "1920x1080"）：等比缩放到目标范围内，不放大
    """
    if task.resolution in ("source", "", None, "custom"):
        return []

    res = str(task.resolution).strip().lower()

    # 自定义分辨率：WxH
    if "x" in res:
        try:
            parts = res.split("x")
            if len(parts) != 2:
                return []
            w, h = int(parts[0]), int(parts[1])
        except (ValueError, IndexError):
            return []
        if w <= 0 or h <= 0:
            return []
        # 保证偶数（多数编码器要求）
        w -= w % 2
        h -= h % 2
        if w < 2 or h < 2:
            return []
        # 等比缩放到目标范围内，不放大，强制偶数输出
        return ["-vf", rf"scale={w}:{h}:force_original_aspect_ratio=decrease:force_divisible_by=2"]

    # 预设分辨率（按高度缩放）
    try:
        height = int(res)
    except (TypeError, ValueError):
        return []
    # 注意：不经过 shell 调用，逗号需用 ffmpeg 的转义形式 \,
    # 宽度 -2 自动取偶数；高度用 trunc(.../2)*2 保证偶数；min 保证不放大
    return ["-vf", rf"scale=-2:trunc(min({height}\,ih)/2)*2"]


def _fps_args(task: ConversionTask) -> List[str]:
    """输出帧率参数（在滤镜之后、输出路径之前生效）。"""
    fps = (task.fps or "source").strip()
    if not fps or fps == "source":
        return []
    try:
        value = float(fps)
    except ValueError:
        return []
    if value <= 0:
        return []
    return ["-r", str(int(value) if value == int(value) else value)]


def _hw_rate_args(encoder: str, crf: Optional[int]) -> List[str]:
    """各硬件编码器的码率/质量控制参数（由软件 CRF 预设映射）。"""
    crf = crf or 23
    if encoder.endswith("_nvenc"):
        # VBR 恒定质量（-b:v 0 表示 CQ 模式）
        return ["-rc", "vbr", "-cq", str(crf), "-b:v", "0"]
    if encoder.endswith("_qsv"):
        # QSV 全局质量（1~51，越小越好）
        return ["-global_quality", str(crf)]
    if encoder.endswith("_amf"):
        # AMF CQP 固定量化参数
        return [
            "-quality", "quality", "-rc", "cqp",
            "-qp_i", str(crf), "-qp_p", str(crf), "-qp_b", str(crf),
        ]
    if encoder.endswith("_mf"):
        # Media Foundation 编码器以目标码率控制为主
        bitrate = {20: "8M", 21: "8M", 23: "5M", 24: "5M", 28: "2500k"}.get(crf, "5M")
        return ["-b:v", bitrate]
    return []


def _apply_hardware(args: List[str]) -> List[str]:
    """把 libx264/libx265 软件编码参数替换为自动选中的硬件编码器参数。

    其他编码器（libvpx / mpeg4 / flac / aac 等）保持原样；
    硬件编码器不可用时整体原样返回（自动回退软件编码）。
    """
    try:
        idx = args.index("-c:v")
    except ValueError:
        return args
    if idx + 1 >= len(args):
        return args
    sw_encoder = args[idx + 1]
    codec = _SW_CODECS.get(sw_encoder)
    if not codec:
        return args
    hw_encoder = hw_manager.encoder_for(codec)
    if not hw_encoder:
        return args

    crf: Optional[int] = None
    if "-crf" in args:
        crf_index = args.index("-crf")
        if crf_index + 1 < len(args):
            try:
                crf = int(args[crf_index + 1])
            except ValueError:
                crf = None

    rebuilt: List[str] = []
    skip = False
    for pos, token in enumerate(args):
        if skip:
            skip = False
            continue
        if token in ("-crf", "-preset") and pos + 1 < len(args):
            # CRF / x264 preset 对硬件编码器无意义，连同取值一起丢弃
            skip = True
            continue
        if token == "-c:v":
            rebuilt += ["-c:v", hw_encoder] + _hw_rate_args(hw_encoder, crf)
            skip = True
            continue
        rebuilt.append(token)
    return rebuilt


def _input_prefix() -> List[str]:
    """输入文件之前的参数（硬件解码）。"""
    return hw_manager.hardware_decode_args()


def build_commands(
    task: ConversionTask,
    info: Optional[MediaInfo] = None,
) -> Tuple[List[List[str]], float]:
    """构建要顺序执行的 ffmpeg 命令列表，以及用于进度计算的总时长。

    返回 (commands, total_duration_seconds)。
    """
    target = get_target(task.target_format, task.category)
    preset = target.preset(task.preset_id)
    info = info or MediaInfo()

    output_path = resolve_output_path(task)
    task.output_path = output_path or ""
    if output_path is None:
        task.status = TaskStatus.SKIPPED
        return [], 0.0

    commands: List[List[str]] = []
    hw_decode = _input_prefix()

    # ---------------- GIF：调色板双步转换（画质显著优于直接输出）
    if preset.palette:
        width = GIF_WIDTH.get(task.preset_id, 480)
        # 从预设参数中取帧率
        fps = 12
        if "-r" in preset.args:
            idx = preset.args.index("-r")
            if idx + 1 < len(preset.args):
                fps = int(preset.args[idx + 1])

        palette_path = os.path.join(
            tempfile.gettempdir(), f"fmtstudio_{task.tid}_palette.png"
        )
        vf1 = f"fps={fps},scale={width}:-1:flags=lanczos,palettegen=stats_mode=full"
        vf2 = (
            f"fps={fps},scale={width}:-1:flags=lanczos,split[s0][s1];"
            f"[s0]palettegen=stats_mode=full[p];"
            f"[s1][p]paletteuse=dither=sierra2_4a"
        )
        commands.append(
            _BASE_ARGS + hw_decode + ["-i", task.input_path, "-vf", vf1, palette_path]
        )
        commands.append(
            _BASE_ARGS + hw_decode + [
                "-i", task.input_path, "-i", palette_path,
                "-lavfi", vf2, output_path,
            ]
        )
        return commands, info.duration

    # ---------------- 常规单步转换
    args = list(_BASE_ARGS) + hw_decode + ["-i", task.input_path]
    args += _apply_hardware(list(preset.args))

    # 视频 -> 视频：追加分辨率缩放（纯音频/GIF/图片参数不加）
    if task.category == MediaCategory.VIDEO and target.kind == "video":
        args += _video_filter(task, info)
        args += _fps_args(task)

    # ICO 图标确保输出方形（预设已含缩放时不重复）
    args.append(output_path)
    commands.append(args)
    return commands, info.duration
