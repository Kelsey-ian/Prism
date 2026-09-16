# -*- coding: utf-8 -*-
"""「关于 Prism」对话框：软件简介、功能特点、开发信息、版本历史。"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget,
)

from qfluentwidgets import (
    BodyLabel, CaptionLabel, FluentIcon as FIF, HyperlinkButton,
    MessageBoxBase, SmoothScrollArea, StrongBodyLabel, TitleLabel,
    isDarkTheme, qconfig, themeColor,
)

from app import (
    APP_AUTHOR, APP_BUILD_TIME, APP_COPYRIGHT, APP_DEV_YEARS,
    APP_DISPLAY, APP_LICENSE, APP_NAME, APP_SUBTITLE, APP_VERSION,
)
from app.i18n import t
from app.ui.icons import prism_pixmap
from app.ui.theme_aware import muted_color


def _scaled_font(label: QLabel, *, point_size: float, weight=None) -> None:
    """以 point size 设置字体，Qt 会按 DPI 自动缩放。"""
    font = QFont(label.font())
    font.setPointSize(point_size)
    if weight is not None:
        font.setWeight(weight)
    label.setFont(font)


class _AppBadge(QFrame):
    """应用图标徽章：圆角方块 + Prism 图标。"""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFixedSize(66, 66)
        self.setObjectName("appBadge")

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        rect = self.rect().adjusted(4, 4, -4, -4)
        path = QPainterPath()
        path.addRoundedRect(rect, 24, 24)
        # 背景：强调色
        accent = QColor(themeColor().name())
        bg = QColor(accent)
        bg.setAlpha(230)
        # painter.fillPath(path, bg)
        # Prism 图标（已裁剪透明边距的宽扁三角形，保持比例最大化绘制）
        pm = prism_pixmap(240)
        if not pm.isNull():
            # 水平几乎占满徽章（留 8px 边距），垂直居中
            avail = rect.width() - 16
            w = min(pm.width(), avail)
            h = int(w * pm.height() / pm.width())
            max_h = rect.height() - 16
            if h > max_h:
                h = max_h
                w = int(h * pm.width() / pm.height())
            x = rect.x() + (rect.width() - w) // 2
            y = rect.y() + (rect.height() - h) // 2
            painter.drawPixmap(x, y, w, h, pm)
        else:
            # 回退：白色 MEDIA 图标
            FIF.MEDIA.icon(QColor(255, 255, 255, 240)).paint(
                painter, rect.adjusted(18, 18, -18, -18)
            )


class AboutPrismDialog(MessageBoxBase):
    """「关于 Prism」对话框。"""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("aboutPrismDialog")
        self.hideCancelButton()
        self.yesButton.setText(t("common.close"))
        self.buttonLayout.removeWidget(self.yesButton)
        self.buttonLayout.addWidget(self.yesButton, 0, Qt.AlignRight)

        view = QWidget()
        layout = QVBoxLayout(view)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(12)

        # ---- 头部：图标 + 名称 + 副标题 ----
        header = QHBoxLayout()
        header.setSpacing(16)
        self.badge = _AppBadge()
        header.addWidget(self.badge)
        name_col = QVBoxLayout()
        name_col.setSpacing(2)
        self.app_name = TitleLabel(f"{APP_DISPLAY}  {APP_NAME}")
        _scaled_font(self.app_name, point_size=15, weight=QFont.Weight.Bold)
        self.app_sub = CaptionLabel(APP_SUBTITLE)
        _scaled_font(self.app_sub, point_size=9)
        self.app_ver = CaptionLabel(f"v{APP_VERSION}")
        _scaled_font(self.app_ver, point_size=8)
        name_col.addWidget(self.app_name)
        name_col.addWidget(self.app_sub)
        name_col.addWidget(self.app_ver)
        name_col.addStretch(1)
        header.addLayout(name_col, 1)
        layout.addLayout(header)

        # ---- 分隔线 ----
        self.sep = QFrame()
        self.sep.setFrameShape(QFrame.HLine)
        self._refresh_separator()
        layout.addWidget(self.sep)

        # 主题切换时刷新分隔线颜色
        qconfig.themeChanged.connect(self._refresh_separator)

        # ---- 主体：可滚动文本区域 ----
        # 文本量较大时，固定高度 + 滚动条可适配各种分辨率，
        # 用户可手动拖动滚动条查看完整内容。
        self.scroll_area = SmoothScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFixedHeight(360)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet(
            "QScrollArea{border: none; background: transparent;}"
        )

        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 4, 8, 4)
        scroll_layout.setSpacing(10)

        # ---- 软件简介 ----
        self.intro_title = StrongBodyLabel(t("about_prism.intro_title"))
        scroll_layout.addWidget(self.intro_title)
        self.intro_text = BodyLabel(t("about_prism.intro_text"))
        self.intro_text.setWordWrap(True)
        scroll_layout.addWidget(self.intro_text)

        # ---- 功能特点 ----
        self.features_title = StrongBodyLabel(t("about_prism.features_title"))
        scroll_layout.addWidget(self.features_title)
        self.features_text = BodyLabel(t("about_prism.features_text"))
        self.features_text.setWordWrap(True)
        scroll_layout.addWidget(self.features_text)

        # ---- 版本信息 ----
        self.ver_title = StrongBodyLabel(t("about_prism.version_title"))
        scroll_layout.addWidget(self.ver_title)
        self.ver_info = CaptionLabel(
            f"{t('about_prism.version_current')}：v{APP_VERSION}\n"
            f"{t('about_prism.build_time')}：{APP_BUILD_TIME}\n"
            f"{t('about_prism.license')}：{APP_LICENSE}"
        )
        self.ver_info.setWordWrap(True)
        scroll_layout.addWidget(self.ver_info)

        # ---- 开发信息 ----
        self.dev_title = StrongBodyLabel(t("about_prism.dev_title"))
        scroll_layout.addWidget(self.dev_title)
        self.dev_info = CaptionLabel(
            f"{t('about_prism.author')}：{APP_AUTHOR}\n"
            f"{t('about_prism.dev_years')}：{APP_DEV_YEARS}"
        )
        self.dev_info.setWordWrap(True)
        scroll_layout.addWidget(self.dev_info)

        # ---- 版本历史 ----
        self.history_title = StrongBodyLabel(t("about_prism.history_title"))
        scroll_layout.addWidget(self.history_title)
        self.history_text = CaptionLabel(t("about_prism.history_text"))
        self.history_text.setWordWrap(True)
        scroll_layout.addWidget(self.history_text)

        scroll_layout.addStretch(1)
        self.scroll_area.setWidget(scroll_content)
        layout.addWidget(self.scroll_area)

        # ---- 底部版权 ----
        self.copyright_label = CaptionLabel(APP_COPYRIGHT)
        self.copyright_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.copyright_label)

        self.viewLayout.addWidget(view)
        self.widget.setMinimumWidth(520)

    def retranslate_ui(self) -> None:
        self.yesButton.setText(t("common.close"))
        self.app_name.setText(f"{APP_DISPLAY}  {APP_NAME}")
        self.app_sub.setText(APP_SUBTITLE)
        self.intro_title.setText(t("about_prism.intro_title"))
        self.intro_text.setText(t("about_prism.intro_text"))
        self.features_title.setText(t("about_prism.features_title"))
        self.features_text.setText(t("about_prism.features_text"))
        self.ver_title.setText(t("about_prism.version_title"))
        self.ver_info.setText(
            f"{t('about_prism.version_current')}：v{APP_VERSION}\n"
            f"{t('about_prism.build_time')}：{APP_BUILD_TIME}\n"
            f"{t('about_prism.license')}：{APP_LICENSE}"
        )
        self.dev_title.setText(t("about_prism.dev_title"))
        self.dev_info.setText(
            f"{t('about_prism.author')}：{APP_AUTHOR}\n"
            f"{t('about_prism.dev_years')}：{APP_DEV_YEARS}"
        )
        self.history_title.setText(t("about_prism.history_title"))
        self.history_text.setText(t("about_prism.history_text"))

    def _refresh_separator(self, _theme=None) -> None:
        """主题切换时刷新分隔线颜色。"""
        color = muted_color(alpha_light=55, alpha_dark=220)
        self.sep.setStyleSheet(
            f"color: {color.name()};"
            f"border: none; background: currentColor; max-height: 1px;"
        )
