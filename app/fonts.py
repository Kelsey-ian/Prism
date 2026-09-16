# -*- coding: utf-8 -*-
"""MiSans 字体加载器：启动时注册内置 TTF，设置全局应用字体。"""
from __future__ import annotations

from PySide6.QtGui import QFont, QFontDatabase

from .resources import FONTS_DIR

_FONT_FAMILY = "MiSans"
_FALLBACK_FAMILY = "Microsoft YaHei UI"


def install_fonts() -> str:
    """注册 MiSans TTF 到 Qt 字体数据库，返回实际可用的字体族名。"""
    loaded = False
    for name in ("MiSans-Regular.ttf", "MiSans-Medium.ttf"):
        path = FONTS_DIR / name
        if path.is_file():
            font_id = QFontDatabase.addApplicationFont(str(path))
            if font_id != -1:
                loaded = True
    if loaded:
        # 确认 Qt 实际解析出的族名
        families = QFontDatabase.families()
        for fam in families:
            if "misans" in fam.lower():
                return fam
        return _FONT_FAMILY
    return _FALLBACK_FAMILY


def app_font(point_size: int = 9) -> QFont:
    """构造应用全局 QFont；若 MiSans 未加载则回退到雅黑。"""
    font = QFont(_FONT_FAMILY, point_size)
    font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
    # 检查 MiSans 是否真实可用，不可用时回退
    if not QFontDatabase.families().__contains__(_FONT_FAMILY) and \
       not any("misans" in f.lower() for f in QFontDatabase.families()):
        font = QFont(_FALLBACK_FAMILY, point_size)
        font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
    return font
