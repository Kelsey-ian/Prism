# -*- coding: utf-8 -*-
"""主题感知样式工具。

所有"次级文字 / 语义状态色 / 图标着色"统一从这里取值，禁止在各页面硬编码
rgba(0,0,0,..) 这类不随主题反转的颜色；页面切换主题时调用
``restyle_muted(self)`` 即可一键刷新全部被标记的文本控件。
"""
from __future__ import annotations

from typing import Optional, Union

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QLabel, QWidget

from qfluentwidgets import FluentIcon, Icon, isDarkTheme, qconfig, themeColor


def muted_css(alpha: float = 0.55) -> str:
    """次级说明文字颜色：深色主题用半透明白，浅色主题用半透明黑。"""
    if isDarkTheme():
        value = min(alpha + 0.10, 0.92)
        return f"color: rgba(255,255,255,{value:.2f});"
    return f"color: rgba(0,0,0,{alpha:.2f});"


def muted_color(alpha_light: int = 150, alpha_dark: int = 160) -> QColor:
    """图标等场景使用的主题感知半透明颜色。"""
    if isDarkTheme():
        return QColor(255, 255, 255, alpha_dark)
    return QColor(0, 0, 0, alpha_light)


def semantic_color(kind: str) -> str:
    """成功 / 错误语义色（深底色下提亮以保证对比度）。"""
    if kind == "success":
        return "#6CCB5F" if isDarkTheme() else "#107C10"
    if kind == "error":
        return "#FF99A4" if isDarkTheme() else "#C42B1C"
    return "#4CC2FF" if isDarkTheme() else "#0078D4"


def themed_icon(
    icon: Union[FluentIcon, Icon],
    size: int = 16,
    accent: bool = False,
) -> QIcon:
    """创建主题感知的图标：深色模式下自动使用白色，浅色模式使用深灰。

    Args:
        icon: FluentIcon 或 Icon 实例
        size: 图标像素尺寸
        accent: True 时使用强调色（themeColor），否则使用主题感知前景色

    Returns:
        QIcon 实例，可直接传给 setIcon()
    """
    if accent:
        color = QColor(themeColor().name())
    else:
        color = muted_color(alpha_light=230, alpha_dark=240)
    return icon.icon(color)


def themed_pixmap(
    icon: Union[FluentIcon, Icon],
    size: int = 16,
    accent: bool = False,
) -> QPixmap:
    """创建主题感知的 QPixmap（供 QLabel.setPixmap 使用）。"""
    return themed_icon(icon, size=size, accent=accent).pixmap(size, size)


def set_muted(label: QLabel, alpha: float = 0.55) -> None:
    """把标签标记为"次级文字"，并立即套用当前主题颜色。"""
    label.setProperty("mutedAlpha", alpha)
    label.setStyleSheet(muted_css(alpha))


def restyle_muted(root: QWidget) -> None:
    """主题切换后刷新 root 下所有 set_muted 标记过的标签。"""
    for widget in root.findChildren(QLabel):
        alpha = widget.property("mutedAlpha")
        if alpha is not None:
            try:
                widget.setStyleSheet(muted_css(float(alpha)))
            except (TypeError, ValueError):
                pass


def connect_theme_change(handler) -> None:
    """注册全局主题切换回调（视图存活期与进程一致，无需手动断开）。"""
    qconfig.themeChanged.connect(lambda _theme: handler())
