# -*- coding: utf-8 -*-
"""图标资源管理：加载 Prism.ico 与 drop_card.svg，提供主题感知渲染。

所有外部图标资源统一从这里取值，避免各处硬编码路径。
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QByteArray, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

from qfluentwidgets import isDarkTheme, themeColor

import sys


def _find_logo_dir() -> Path:
    """查找 Logo 目录：优先开发模式路径，其次 PyInstaller 打包路径。"""
    # 开发模式: app/ui/icons.py → parents[2] = 项目根
    dev_path = Path(__file__).resolve().parents[2] / "Logo"
    if dev_path.exists():
        return dev_path
    # PyInstaller 冻结模式: _MEIPASS/Logo
    if hasattr(sys, "_MEIPASS"):
        frozen_path = Path(sys._MEIPASS) / "Logo"
        if frozen_path.exists():
            return frozen_path
    # 回退: exe 同级 Logo
    if getattr(sys, "frozen", False):
        exe_path = Path(sys.executable).resolve().parent / "Logo"
        if exe_path.exists():
            return exe_path
    return dev_path  # 返回开发路径（即便不存在）


_LOGO_DIR = _find_logo_dir()
_PRISM_ICO = _LOGO_DIR / "Prism.ico"
_DROP_CARD_SVG = _LOGO_DIR / "drop_card.svg"

# Prism.ico 裁剪后的内容缓存（图形为宽扁三角形，原画布约 60% 为透明边距）
_CROPPED_PM: QPixmap | None = None


def _prism_content() -> QPixmap:
    """返回裁剪掉透明边距后的 Prism 图标内容（懒加载缓存）。

    Prism.ico 的三角形图形只占画布约 90%x40%，直接绘制会显得很小；
    此函数扫描 alpha 通道找到内容边界并裁剪，使内容填满整个画布。
    """
    global _CROPPED_PM
    if _CROPPED_PM is not None:
        return _CROPPED_PM
    if not _PRISM_ICO.exists():
        return QPixmap()
    from PySide6.QtGui import QImage

    icon = QIcon(str(_PRISM_ICO))
    pm = icon.pixmap(128, 128)
    if pm.isNull():
        return QPixmap()
    img = pm.toImage()
    if img.format() != QImage.Format_RGBA8888:
        img = img.convertToFormat(QImage.Format_RGBA8888)
    w, h = img.width(), img.height()
    minX, minY, maxX, maxY = w, h, -1, -1
    for y in range(h):
        for x in range(w):
            if img.pixelColor(x, y).alpha() > 8:
                if x < minX:
                    minX = x
                if x > maxX:
                    maxX = x
                if y < minY:
                    minY = y
                if y > maxY:
                    maxY = y
    if maxX < 0:  # 全透明，保留原图
        _CROPPED_PM = pm
    else:
        _CROPPED_PM = QPixmap.fromImage(
            img.copy(minX, minY, maxX - minX + 1, maxY - minY + 1)
        )
    return _CROPPED_PM


def prism_icon() -> QIcon:
    """返回 Prism 应用图标 QIcon（已裁剪透明边距，内容最大化）。"""
    pm = _prism_content()
    if not pm.isNull():
        return QIcon(pm)
    if _PRISM_ICO.exists():
        return QIcon(str(_PRISM_ICO))
    return QIcon()


def prism_pixmap(size: int = 48) -> QPixmap:
    """返回指定尺寸的 Prism 图标 QPixmap（内容按比例填满 size 盒）。"""
    pm = _prism_content()
    if pm.isNull():
        return QPixmap(size, size)
    return pm.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)


def drop_card_pixmap(size: int = 34, color: QColor | None = None) -> QPixmap:
    """渲染 drop_card.svg 为指定颜色与尺寸的 QPixmap。

    Args:
        size: 输出像素尺寸
        color: 填充颜色；None 时自动按当前主题选取
    """
    if not _DROP_CARD_SVG.exists():
        return QPixmap(size, size)

    if color is None:
        if isDarkTheme():
            color = QColor(255, 255, 255, 230)
        else:
            color = QColor(40, 40, 40, 200)

    # 读取 SVG 并替换填充颜色
    svg_text = _DROP_CARD_SVG.read_text(encoding="utf-8")
    # 原始 SVG 中 fill="#bfbfbf" → 替换为目标颜色
    hex_color = color.name()  # #RRGGBB
    svg_text = svg_text.replace('fill="#bfbfbf"', f'fill="{hex_color}"')

    renderer = QSvgRenderer(QByteArray(svg_text.encode("utf-8")))
    if not renderer.isValid():
        return QPixmap(size, size)

    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    painter = QPainter(pm)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setRenderHint(QPainter.SmoothPixmapTransform)
    renderer.render(painter, QRectF(0, 0, size, size))
    painter.end()

    # 设置 alpha 通道
    if color.alpha() < 255:
        result = QPixmap(size, size)
        result.fill(Qt.transparent)
        p = QPainter(result)
        p.setRenderHint(QPainter.Antialiasing)
        p.setOpacity(color.alpha() / 255.0)
        p.drawPixmap(0, 0, pm)
        p.end()
        return result
    return pm
