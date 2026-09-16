# -*- coding: utf-8 -*-
"""文件拖放卡片：虚线边框 + 高亮反馈，支持文件 / 文件夹批量拖入。"""
from __future__ import annotations

import os
from typing import List

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QFileDialog, QFrame, QLabel, QVBoxLayout

from qfluentwidgets import BodyLabel, CaptionLabel, FluentIcon as FIF, isDarkTheme, qconfig, themeColor

from app.i18n import t
from app.ui.icons import drop_card_pixmap


class DropCard(QFrame):
    """大块拖放区域；点击也可弹出文件选择对话框。"""

    filesDropped = Signal(list)       # List[str]：文件 / 文件夹路径
    clicked = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setFixedHeight(158)
        self.setCursor(Qt.PointingHandCursor)
        self.setObjectName("dropCard")

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(8)

        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setFixedSize(52, 52)
        self._render_icon(False)

        # 必须使用 qfluentwidgets 的标签：原生 QLabel 在 Mica/Acrylic
        # 透明窗口上会继承到白色调色板，浅色主题下文字不可见。
        # 字号/字重用 QFont 设置，避免 setStyleSheet 覆盖库注入的主题色。
        self.title_label = BodyLabel()
        self.title_label.setAlignment(Qt.AlignCenter)
        title_font = QFont(self.font())
        title_font.setPixelSize(15)
        title_font.setWeight(QFont.Weight.DemiBold)
        self.title_label.setFont(title_font)

        self.hint_label = CaptionLabel()
        self.hint_label.setAlignment(Qt.AlignCenter)
        hint_font = QFont(self.font())
        hint_font.setPixelSize(12)
        self.hint_label.setFont(hint_font)

        layout.addWidget(self.icon_label)
        layout.addWidget(self.title_label)
        layout.addWidget(self.hint_label)

        self._hover = False
        # 主题切换时重绘虚线底色与图标颜色（文字标签由样式表自动反转）
        qconfig.themeChanged.connect(self._on_theme_changed)
        qconfig.themeColorChanged.connect(self._on_theme_changed)

        self.retranslate_ui()

    def retranslate_ui(self) -> None:
        """更新所有可见文案（语言切换时调用）。"""
        self.title_label.setText(t("drop.title"))
        self.hint_label.setText(t("drop.hint"))

    def showEvent(self, event) -> None:  # noqa: N802
        """首次显示时主题已确定，确保图标颜色正确。"""
        super().showEvent(event)
        self._render_icon(self._hover)
        self.update()

    def _on_theme_changed(self, _theme=None) -> None:
        if not self._hover:
            self._render_icon(False)
        self.update()

    # ------------------------------------------------------------ 外观

    def _render_icon(self, active: bool) -> None:
        if active:
            color = QColor(themeColor().name())
        else:
            # 深色模式下白色，浅色模式下深灰
            if isDarkTheme():
                color = QColor(255, 255, 255, 230)
            else:
                color = QColor(40, 40, 40, 200)
        self.icon_label.setPixmap(drop_card_pixmap(46, color))

    def _colors(self):
        if self._hover:
            return QColor(themeColor().name()), QColor(themeColor().name())
        if isDarkTheme():
            return QColor(255, 255, 255, 55), QColor(255, 255, 255, 22)
        return QColor(0, 0, 0, 55), QColor(0, 0, 0, 12)

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        radius = 12.0
        rect = self.rect().adjusted(1, 1, -1, -1)
        path = QPainterPath()
        path.addRoundedRect(rect, radius, radius)

        border_color, fill_color = self._colors()
        painter.fillPath(path, fill_color)
        pen = QPen(border_color, 1.4)
        pen.setStyle(Qt.DashLine if not self._hover else Qt.SolidLine)
        painter.setPen(pen)
        painter.drawPath(path)

    # ------------------------------------------------------------ 拖放

    def dragEnterEvent(self, event) -> None:  # noqa: N802
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self._hover = True
            self._render_icon(True)
            self.update()

    def dragMoveEvent(self, event) -> None:  # noqa: N802
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragLeaveEvent(self, event) -> None:  # noqa: N802
        self._hover = False
        self._render_icon(False)
        self.update()

    def dropEvent(self, event) -> None:  # noqa: N802
        paths: List[str] = []
        for url in event.mimeData().urls():
            local = url.toLocalFile()
            if local and os.path.exists(local):
                paths.append(os.path.normpath(local))
        self._hover = False
        self._render_icon(False)
        self.update()
        if paths:
            self.filesDropped.emit(paths)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def choose_files(self, name_filter: str) -> List[str]:
        """供外部调用：弹出多选文件对话框。"""
        paths, _ = QFileDialog.getOpenFileNames(
            self, t("convert.dialog.choose_files"), "", name_filter
        )
        return paths
