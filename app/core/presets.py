# -*- coding: utf-8 -*-
"""支持的格式与转换预设定义。

- 通过扩展名识别源文件分类（音频 / 视频 / 图片）
- 每一种目标格式包含若干“质量预设”，预设对应 ffmpeg 的输出参数
- 实际可转格式以本机 FFmpeg 能力为准（ffmpeg.py 会做能力探测），
  这里维护的是面向用户的常用格式清单，覆盖 FFmpeg 最主流的封装/编码。
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .models import MediaCategory

# ---------------------------------------------------------------- 输入扩展名

AUDIO_EXTS = {
    "mp3", "wav", "flac", "aac", "m4a", "ogg", "oga", "opus", "wma",
    "aiff", "aif", "amr", "ape", "alac", "m4b", "m4r", "ac3", "au",
    "ra", "mid", "midi", "voc", "dts",
}

VIDEO_EXTS = {
    "mp4", "m4v", "mkv", "avi", "mov", "webm", "flv", "f4v", "wmv",
    "mpg", "mpeg", "mpe", "3gp", "3g2", "ts", "mts", "m2ts", "vob",
    "ogv", "rmvb", "rm", "asf", "dv", "swf", "mxf",
}

IMAGE_EXTS = {
    "jpg", "jpeg", "jfif", "png", "gif", "bmp", "webp", "tif", "tiff",
    "ico", "heic", "heif", "avif", "jp2", "tga", "dds", "ppm", "pgm",
    "pbm", "pcx",
}

_ALL_EXTS = AUDIO_EXTS | VIDEO_EXTS | IMAGE_EXTS

# ---------------------------------------------------------------- 数据结构


@dataclass
class Preset:
    id: str
    name: str
    args: List[str] = field(default_factory=list)   # ffmpeg 输出参数（位于 -i 之后、输出路径之前）
    palette: bool = False                            # GIF 调色板双步转换标记


@dataclass
class TargetFormat:
    id: str            # 格式 / 扩展名标识，如 mp3
    label: str         # 下拉框显示名
    group: str         # 分组（视频格式 / 提取音频 / 图片格式）
    ext: str           # 输出扩展名
    presets: List[Preset]
    kind: str          # audio / video / image

    def preset(self, preset_id: str) -> Preset:
        for p in self.presets:
            if p.id == preset_id:
                return p
        return self.presets[0]


# ---------------------------------------------------------------- 目标格式定义

def _audio_targets() -> List[TargetFormat]:
    return [
        TargetFormat("mp3", "MP3（MPEG 音频）", "提取音频", "mp3", kind="audio", presets=[
            Preset("mp3_320", "高质量 320 kbps", ["-vn", "-c:a", "libmp3lame", "-b:a", "320k"]),
            Preset("mp3_192", "标准 192 kbps", ["-vn", "-c:a", "libmp3lame", "-b:a", "192k"]),
            Preset("mp3_128", "小体积 128 kbps", ["-vn", "-c:a", "libmp3lame", "-b:a", "128k"]),
            Preset("mp3_vbr", "VBR 动态码率（约 200 kbps）", ["-vn", "-c:a", "libmp3lame", "-q:a", "2"]),
        ]),
        TargetFormat("wav", "WAV（无损 PCM）", "提取音频", "wav", kind="audio", presets=[
            Preset("wav_16_44", "PCM 16bit / 44.1kHz（CD 音质）",
                   ["-vn", "-c:a", "pcm_s16le", "-ar", "44100"]),
            Preset("wav_16_48", "PCM 16bit / 48kHz",
                   ["-vn", "-c:a", "pcm_s16le", "-ar", "48000"]),
            Preset("wav_24", "PCM 24bit 高清", ["-vn", "-c:a", "pcm_s24le"]),
        ]),
        TargetFormat("flac", "FLAC（无损压缩）", "提取音频", "flac", kind="audio", presets=[
            Preset("flac_5", "无损（压缩级别 5，推荐）", ["-vn", "-c:a", "flac", "-compression_level", "5"]),
            Preset("flac_0", "无损（最快）", ["-vn", "-c:a", "flac", "-compression_level", "0"]),
            Preset("flac_8", "无损（最小体积）", ["-vn", "-c:a", "flac", "-compression_level", "8"]),
        ]),
        TargetFormat("m4a", "M4A（AAC 音频）", "提取音频", "m4a", kind="audio", presets=[
            Preset("m4a_256", "高质量 256 kbps", ["-vn", "-c:a", "aac", "-b:a", "256k"]),
            Preset("m4a_192", "标准 192 kbps", ["-vn", "-c:a", "aac", "-b:a", "192k"]),
            Preset("m4a_128", "小体积 128 kbps", ["-vn", "-c:a", "aac", "-b:a", "128k"]),
        ]),
        TargetFormat("ogg", "OGG（Vorbis）", "提取音频", "ogg", kind="audio", presets=[
            Preset("ogg_q5", "高质量（Q5）", ["-vn", "-c:a", "libvorbis", "-q:a", "5"]),
            Preset("ogg_q3", "标准（Q3）", ["-vn", "-c:a", "libvorbis", "-q:a", "3"]),
        ]),
        TargetFormat("opus", "OPUS（现代高效编码）", "提取音频", "opus", kind="audio", presets=[
            Preset("opus_128", "128 kbps（推荐）", ["-vn", "-c:a", "libopus", "-b:a", "128k"]),
            Preset("opus_96", "96 kbps", ["-vn", "-c:a", "libopus", "-b:a", "96k"]),
            Preset("opus_64", "64 kbps（语音/有声书）", ["-vn", "-c:a", "libopus", "-b:a", "64k"]),
        ]),
        TargetFormat("wma", "WMA（Windows Media）", "提取音频", "wma", kind="audio", presets=[
            Preset("wma_192", "192 kbps", ["-vn", "-c:a", "wmav2", "-b:a", "192k"]),
            Preset("wma_128", "128 kbps", ["-vn", "-c:a", "wmav2", "-b:a", "128k"]),
        ]),
        TargetFormat("aac", "AAC（裸音频流）", "提取音频", "aac", kind="audio", presets=[
            Preset("aac_192", "192 kbps", ["-vn", "-c:a", "aac", "-b:a", "192k", "-f", "adts"]),
        ]),
    ]


def _video_targets() -> List[TargetFormat]:
    return [
        TargetFormat("mp4", "MP4（H.264 通用格式）", "视频格式", "mp4", kind="video", presets=[
            Preset("mp4_h264_20", "H.264 高质量（CRF 20）",
                   ["-c:v", "libx264", "-crf", "20", "-preset", "medium", "-c:a", "aac", "-b:a", "192k"]),
            Preset("mp4_h264_23", "H.264 标准（CRF 23）",
                   ["-c:v", "libx264", "-crf", "23", "-preset", "medium", "-c:a", "aac", "-b:a", "128k"]),
            Preset("mp4_h264_28", "H.264 小体积（CRF 28）",
                   ["-c:v", "libx264", "-crf", "28", "-preset", "medium", "-c:a", "aac", "-b:a", "96k"]),
            Preset("mp4_h265", "H.265/HEVC 高压缩（CRF 24）",
                   ["-c:v", "libx265", "-crf", "24", "-preset", "medium", "-c:a", "aac", "-b:a", "192k"]),
        ]),
        TargetFormat("mkv", "MKV（Matroska）", "视频格式", "mkv", kind="video", presets=[
            Preset("mkv_h264", "H.264 + AAC",
                   ["-c:v", "libx264", "-crf", "21", "-preset", "medium", "-c:a", "aac", "-b:a", "192k"]),
            Preset("mkv_h265", "H.265/HEVC + AAC（体积更小）",
                   ["-c:v", "libx265", "-crf", "24", "-preset", "medium", "-c:a", "aac", "-b:a", "160k"]),
        ]),
        TargetFormat("mov", "MOV（QuickTime）", "视频格式", "mov", kind="video", presets=[
            Preset("mov_h264", "H.264 + AAC",
                   ["-c:v", "libx264", "-crf", "21", "-preset", "medium", "-c:a", "aac", "-b:a", "192k"]),
        ]),
        TargetFormat("avi", "AVI（经典格式）", "视频格式", "avi", kind="video", presets=[
            Preset("avi_mpeg4", "MPEG-4 + MP3（兼容老设备）",
                   ["-c:v", "mpeg4", "-q:v", "4", "-c:a", "libmp3lame", "-q:a", "4"]),
        ]),
        TargetFormat("av1", "AV1（高效视频编码）", "视频格式", "mp4", kind="video", presets=[
            Preset("av1_crf_28", "AV1 高质量（CRF 28）",
                   ["-c:v", "libsvtav1", "-crf", "28", "-preset", "6", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "192k"]),
            Preset("av1_crf_32", "AV1 标准（CRF 32）",
                   ["-c:v", "libsvtav1", "-crf", "32", "-preset", "8", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "128k"]),
            Preset("av1_crf_36", "AV1 小体积（CRF 36）",
                   ["-c:v", "libsvtav1", "-crf", "36", "-preset", "10", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "96k"]),
        ]),
        TargetFormat("webm", "WEBM（网页视频）", "视频格式", "webm", kind="video", presets=[
            Preset("webm_av1", "AV1 + Opus（高版本，推荐）",
                   ["-c:v", "libsvtav1", "-crf", "32", "-preset", "6", "-pix_fmt", "yuv420p",
                    "-c:a", "libopus", "-b:a", "160k"]),
            Preset("webm_vp9", "VP9 + Opus",
                   ["-c:v", "libvpx-vp9", "-crf", "31", "-b:v", "0", "-c:a", "libopus", "-b:a", "160k"]),
            Preset("webm_vp8", "VP8 + Vorbis",
                   ["-c:v", "libvpx", "-crf", "10", "-b:v", "0", "-c:a", "libvorbis", "-q:a", "4"]),
        ]),
        TargetFormat("gif", "GIF（动态图片）", "视频格式", "gif", kind="video", presets=[
            Preset("gif_480", "480px 流畅（12fps，调色板优化）",
                   ["-r", "12"], palette=True),
            Preset("gif_360", "360px 标准（10fps，调色板优化）",
                   ["-r", "10"], palette=True),
            Preset("gif_320_small", "320px 小体积（8fps，调色板优化）",
                   ["-r", "8"], palette=True),
        ]),
        TargetFormat("flv", "FLV（Flash 视频）", "视频格式", "flv", kind="video", presets=[
            Preset("flv_std", "H.264 + MP3",
                   ["-c:v", "libx264", "-crf", "23", "-preset", "medium", "-c:a", "libmp3lame", "-b:a", "128k"]),
        ]),
    ]


def _image_targets() -> List[TargetFormat]:
    return [
        TargetFormat("jpg", "JPG / JPEG（通用照片）", "图片格式", "jpg", kind="image", presets=[
            Preset("jpg_q2", "高质量（q=2）", ["-frames:v", "1", "-q:v", "2"]),
            Preset("jpg_q5", "标准（q=5）", ["-frames:v", "1", "-q:v", "5"]),
            Preset("jpg_q8", "小体积（q=8）", ["-frames:v", "1", "-q:v", "8"]),
        ]),
        TargetFormat("png", "PNG（无损透明图）", "图片格式", "png", kind="image", presets=[
            Preset("png_6", "标准压缩（级别 6）", ["-frames:v", "1", "-compression_level", "6"]),
            Preset("png_0", "最快（无压缩）", ["-frames:v", "1", "-compression_level", "0"]),
            Preset("png_9", "最小体积（级别 9）", ["-frames:v", "1", "-compression_level", "9"]),
        ]),
        TargetFormat("webp", "WEBP（现代图片）", "图片格式", "webp", kind="image", presets=[
            Preset("webp_l90", "高质量 90", ["-frames:v", "1", "-quality", "90"]),
            Preset("webp_l75", "标准 75", ["-frames:v", "1", "-quality", "75"]),
        ]),
        TargetFormat("bmp", "BMP（位图）", "图片格式", "bmp", kind="image", presets=[
            Preset("bmp_std", "标准位图", ["-frames:v", "1"]),
        ]),
        TargetFormat("tiff", "TIFF（印刷/专业）", "图片格式", "tiff", kind="image", presets=[
            Preset("tiff_lzw", "LZW 无损压缩", ["-frames:v", "1", "-compression_algo", "lzw"]),
        ]),
        TargetFormat("gif", "GIF（静态首帧）", "图片格式", "gif", kind="image", presets=[
            Preset("gif_static", "单帧 GIF", ["-frames:v", "1"]),
        ]),
        TargetFormat("ico", "ICO（Windows 图标）", "图片格式", "ico", kind="image", presets=[
            Preset("ico_256", "多尺寸图标（含 256px）",
                   ["-frames:v", "1", "-vf", "scale=256:256:force_original_aspect_ratio=decrease"]),
        ]),
    ]


AUDIO_TARGETS: List[TargetFormat] = _audio_targets()
VIDEO_TARGETS: List[TargetFormat] = _video_targets()
IMAGE_TARGETS: List[TargetFormat] = _image_targets()

_BY_ID: Dict[str, TargetFormat] = {
    t.id: t for t in (AUDIO_TARGETS + VIDEO_TARGETS + IMAGE_TARGETS)
}

# GIF 预设对应的输出短边宽度
GIF_WIDTH = {"gif_480": 480, "gif_360": 360, "gif_320_small": 320}

# 视频分辨率选项（高度）——不再设上限，最高支持 4K UHD（仅向下压缩，不放大）
RESOLUTIONS = [
    ("source", "原始分辨率（不缩放）"),
    ("custom", "自定义分辨率..."),
    ("480", "480p（标清 640×480）"),
    ("720", "720p（高清 1280×720）"),
    ("1080", "1080p（全高清 1920×1080）"),
    ("1440", "2K QHD（2560×1440）"),
    ("2160", "4K UHD（3840×2160）"),
]

# 视频帧率选项
FRAME_RATES = [
    ("source", "原始帧率（不变）"),
    ("24", "24 fps（电影）"),
    ("25", "25 fps（PAL）"),
    ("30", "30 fps（通用）"),
    ("50", "50 fps（高帧率）"),
    ("60", "60 fps（高帧率）"),
]


# ---------------------------------------------------------------- 查询辅助

def detect_category(path: str | os.PathLike) -> Optional[MediaCategory]:
    """根据扩展名判断媒体分类，不支持则返回 None。"""
    ext = Path(path).suffix.lstrip(".").lower()
    if ext in AUDIO_EXTS:
        return MediaCategory.AUDIO
    if ext in VIDEO_EXTS:
        return MediaCategory.VIDEO
    if ext in IMAGE_EXTS:
        return MediaCategory.IMAGE
    return None


def is_supported(path: str | os.PathLike) -> bool:
    return detect_category(path) is not None


def targets_for_category(category: MediaCategory) -> List[TargetFormat]:
    """源分类 -> 允许的目标格式列表（视频可转视频或提取音频）。"""
    if category == MediaCategory.VIDEO:
        return VIDEO_TARGETS + AUDIO_TARGETS
    if category == MediaCategory.AUDIO:
        return AUDIO_TARGETS
    return IMAGE_TARGETS


def get_target(format_id: str, category: Optional[MediaCategory] = None) -> TargetFormat:
    """按 id 查找目标格式；视频 GIF 与图片 GIF 等同名格式按源分类区分。"""
    if category is not None:
        for target in targets_for_category(category):
            if target.id == format_id:
                return target
    return _BY_ID[format_id]


def iter_media_files(folder: str | os.PathLike) -> List[Tuple[str, MediaCategory]]:
    """递归收集文件夹内受支持的媒体文件。"""
    result: List[Tuple[str, MediaCategory]] = []
    for root, _dirs, files in os.walk(folder):
        for name in sorted(files):
            full = os.path.join(root, name)
            cat = detect_category(full)
            if cat is not None:
                result.append((full, cat))
    return result


def format_file_size(size: int) -> str:
    """字节数 -> 易读字符串。"""
    value = float(size)
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024 or unit == "GB":
            return f"{value:.1f} {unit}" if unit != "B" else f"{int(value)} B"
        value /= 1024
    return f"{value:.1f} GB"


def format_duration(seconds: float) -> str:
    """秒 -> HH:MM:SS / MM:SS。"""
    if not seconds or seconds <= 0:
        return ""
    total = int(seconds)
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"
