# -*- coding: utf-8 -*-
"""Prism —— 基于 FFmpeg 的现代 Fluent 风格媒体格式转换工具。

入口脚本：创建 QApplication 并显示主窗口。
"""
import os
import sys
from pathlib import Path

# 确保项目根目录在 sys.path 中（双击运行 / python main.py 两种方式都兼容）
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) in sys.path:
    sys.path.remove(str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR))

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from qfluentwidgets import setTheme, Theme

from app import APP_DISPLAY, APP_VERSION
from app.config import app_config, ensure_dirs
from app.core.queue_manager import QueueManager
from app.fonts import app_font, install_fonts
from app.ui.icons import prism_icon
from app.ui.main_window import MainWindow


def main() -> int:
    ensure_dirs()

    # 高 DPI 与缩放：Qt6 默认开启，这里仅设置缩放策略保持清晰
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("Prism")
    app.setApplicationDisplayName(APP_DISPLAY)
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName("Prism")

    # 设置应用程序图标（任务栏、窗口标题栏）
    _icon = prism_icon()
    if not _icon.isNull():
        app.setWindowIcon(_icon)

    # 安装 MiSans 字体并设为全局字体（失败时回退雅黑）
    install_fonts()
    app.setFont(app_font(9))

    theme_map = {
        "auto": Theme.AUTO,
        "light": Theme.LIGHT,
        "dark": Theme.DARK,
    }
    setTheme(theme_map.get(app_config.get("theme", "auto"), Theme.AUTO))

    # 应用点缀色（跟随系统或手动选择）
    from app.core.accent import apply_accent_color
    apply_accent_color(
        color=app_config.get("accent_color", "system"),
        follow_system=bool(app_config.get("accent_follow_system", True)),
    )

    # 多语言初始化
    from app.i18n import set_language
    set_language(app_config.get("language", "auto"))

    queue = QueueManager()
    window = MainWindow(queue)
    window.show()

    code = app.exec()

    # 退出前取消仍在运行的转换任务，避免遗留 ffmpeg 进程
    queue.shutdown()
    return code


if __name__ == "__main__":
    raise SystemExit(main())
