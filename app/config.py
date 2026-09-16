# -*- coding: utf-8 -*-
"""全局路径与应用配置（基于 INI 的 QSettings，便携、可随项目迁移）。"""
from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QSettings

# PyInstaller 冻结模式检测
_FROZEN = getattr(sys, "frozen", False)

if _FROZEN:
    # 打包后：exe 所在目录（用户可写入）
    BASE_DIR = Path(sys.executable).resolve().parent
    # 资源目录（PyInstaller 解包路径，只读）
    _RESOURCE_DIR = Path(sys._MEIPASS) if hasattr(sys, "_MEIPASS") else BASE_DIR
else:
    BASE_DIR = Path(__file__).resolve().parent.parent
    _RESOURCE_DIR = BASE_DIR

# 内置 FFmpeg 目录：优先 exe 同级 bin/（可写、供更新），其次打包内置
_BIN_CANDIDATES = [BASE_DIR / "bin", _RESOURCE_DIR / "bin"]
BIN_DIR = next((d for d in _BIN_CANDIDATES if d.exists()), _RESOURCE_DIR / "bin")
# 下载等临时数据目录
DATA_DIR = BASE_DIR / "data"
DOWNLOAD_DIR = DATA_DIR / "downloads"
# 更新包暂存目录（下载完成后、退出安装前存放新二进制）
STAGING_DIR = DATA_DIR / "staging"
# 配置目录（用户可写）
CONFIG_DIR = BASE_DIR / "config"
SETTINGS_FILE = CONFIG_DIR / "settings.ini"

# 内置 FFmpeg 安装信息（版本 / 来源 / 安装时间）
INSTALL_RECORD = BIN_DIR / "ffmpeg.install.json"

# 设置项默认值
_DEFAULTS = {
    "theme": "auto",                 # auto / light / dark
    "concurrency": 2,                # 同时转换任务数
    "output_dir": "",                # 空表示输出到源文件所在目录
    "conflict": "rename",            # rename / overwrite / skip
    "auto_check_update": True,       # 启动时检查 FFmpeg 更新
    "manual_ffmpeg_path": "",        # 用户手动指定的 ffmpeg.exe
    "update_channel": "auto",        # auto(测速) / direct / ghfast / ghproxy / moeyy
    "hw_accel": True,                # 硬件加速总开关（自动检测）
    "last_category": "video",        # 上次使用的分类页
    "language": "auto",             # auto(系统) / zh_CN / en / en_US / fr / ja / ru / es
    "accent_color": "system",       # system / #RRGGBB
    "accent_follow_system": True,    # 跟随系统强调色开关
}


def ensure_dirs() -> None:
    """创建运行所需目录。"""
    for d in (BIN_DIR, DOWNLOAD_DIR, STAGING_DIR, CONFIG_DIR):
        d.mkdir(parents=True, exist_ok=True)


class AppConfig:
    """对 QSettings 的轻量封装，统一默认值与类型转换。"""

    def __init__(self) -> None:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        self._settings = QSettings(str(SETTINGS_FILE), QSettings.IniFormat)
        self._settings.setFallbacksEnabled(False)

    def get(self, key: str, default=None):
        default = _DEFAULTS.get(key, default)
        value = self._settings.value(key, default)
        # QSettings 常把值读成字符串，按默认值类型还原
        if isinstance(default, bool) and isinstance(value, str):
            return value.lower() in ("1", "true", "yes", "on")
        if isinstance(default, int) and not isinstance(value, bool):
            try:
                return int(value)
            except (TypeError, ValueError):
                return default
        return value

    def set(self, key: str, value) -> None:
        self._settings.setValue(key, value)

    def sync(self) -> None:
        self._settings.sync()


app_config = AppConfig()
