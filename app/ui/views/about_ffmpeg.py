# -*- coding: utf-8 -*-
"""“关于 FFmpeg”对话框：功能介绍、版本与协议、官方资源链接。"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPixmap
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from qfluentwidgets import (
    BodyLabel, CaptionLabel, FluentIcon as FIF, HyperlinkButton,
    MessageBoxBase, SmoothScrollArea, StrongBodyLabel, isDarkTheme,
)

from app.core.ffmpeg import ffmpeg_manager
from app.core.hardware import detect_arch
from app.i18n import t
from app.resources import IMAGES_DIR

_LINK_KEYS = [
    ("about_ffmpeg.link.website", "https://ffmpeg.org"),
    ("about_ffmpeg.link.docs", "https://ffmpeg.org/documentation.html"),
    ("about_ffmpeg.link.ffmpeg_man", "https://ffmpeg.org/ffmpeg.html"),
    ("about_ffmpeg.link.download", "https://ffmpeg.org/download.html"),
    ("about_ffmpeg.link.license", "https://ffmpeg.org/legal.html"),
]


def _load_ffmpeg_logo(size: int = 64) -> QPixmap:
    """加载内置 FFmpeg logo 并按主题着色（深色模式→白色，浅色模式→原色）。"""
    path = IMAGES_DIR / "ffmpeg-logo.png"
    if not path.is_file():
        return QPixmap()
    pm = QPixmap(str(path))
    if pm.isNull():
        return QPixmap()
    pm = pm.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    # 深色模式下将 logo 染白以保证可见性（用 SourceIn 合成模式保留 alpha 通道）
    if isDarkTheme():
        tinted = QPixmap(pm.size())
        tinted.fill(Qt.transparent)
        painter = QPainter(tinted)
        painter.drawPixmap(0, 0, pm)
        painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
        painter.fillRect(tinted.rect(), QColor(255, 255, 255))
        painter.end()
        pm = tinted
    return pm


class AboutFFmpegDialog(MessageBoxBase):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("aboutFFmpegDialog")
        self.hideCancelButton()
        self.yesButton.setText(t("common.close"))
        self.buttonLayout.removeWidget(self.yesButton)
        self.buttonLayout.addWidget(self.yesButton, 0, Qt.AlignRight)

        view = QWidget()
        layout = QVBoxLayout(view)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(10)

        # ---- FFmpeg logo（主题感知着色）----
        logo_row = QHBoxLayout()
        logo_row.setAlignment(Qt.AlignCenter)
        self.logo_label = QLabel()
        self._refresh_logo()
        logo_row.addWidget(self.logo_label)
        layout.addLayout(logo_row)

        self.title = StrongBodyLabel(t("about_ffmpeg.title"))
        self.title.setStyleSheet("font-size: 17px;")
        self.title.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title)

        # ---- 主体：可滚动文本区域 ----
        # 当版本 / 许可 / 链接等内容在低分辨率下溢出时，
        # 用户可手动滚动查看完整文本。
        self.scroll_area = SmoothScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFixedHeight(320)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet(
            "QScrollArea{border: none; background: transparent;}"
        )

        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 4, 8, 4)
        scroll_layout.setSpacing(10)

        self.intro = BodyLabel(t("about_ffmpeg.intro"))
        self.intro.setWordWrap(True)
        scroll_layout.addWidget(self.intro)

        self.ver_label = CaptionLabel("")
        self.ver_label.setWordWrap(True)
        scroll_layout.addWidget(self.ver_label)

        self.license_label = CaptionLabel(t("about_ffmpeg.license"))
        self.license_label.setWordWrap(True)
        scroll_layout.addWidget(self.license_label)

        self.links_title = StrongBodyLabel(t("about_ffmpeg.resources"))
        scroll_layout.addWidget(self.links_title)
        self._link_buttons: list[HyperlinkButton] = []
        for key, url in _LINK_KEYS:
            link = HyperlinkButton(url, t(key), self, FIF.LINK)
            link.setCursor(Qt.PointingHandCursor)
            self._link_buttons.append((link, key))
            scroll_layout.addWidget(link)

        scroll_layout.addStretch(1)
        self.scroll_area.setWidget(scroll_content)
        layout.addWidget(self.scroll_area)

        self.viewLayout.addWidget(view)
        self.widget.setMinimumWidth(470)
        self._refresh_version_text()

    def _refresh_version_text(self) -> None:
        version = ffmpeg_manager.version or t("common.not_detected")
        source = ffmpeg_manager.source or "—"
        path = ffmpeg_manager.ffmpeg_path if ffmpeg_manager.available else t("common.not_installed")
        self.ver_label.setText(t("about_ffmpeg.version_label",
                                 version=version, source=source,
                                 arch=detect_arch().upper(), path=path))

    def retranslate_ui(self) -> None:
        self.yesButton.setText(t("common.close"))
        self.title.setText(t("about_ffmpeg.title"))
        self.intro.setText(t("about_ffmpeg.intro"))
        self.license_label.setText(t("about_ffmpeg.license"))
        self.links_title.setText(t("about_ffmpeg.resources"))
        for link, key in self._link_buttons:
            link.setText(t(key))
        self._refresh_version_text()

    def _refresh_logo(self) -> None:
        """重新加载 logo（主题切换时调用）。"""
        pm = _load_ffmpeg_logo(128)
        if not pm.isNull():
            self.logo_label.setPixmap(pm)
