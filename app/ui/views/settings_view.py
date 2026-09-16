# -*- coding: utf-8 -*-
"""设置页面：FFmpeg 引擎管理与升级、硬件加速、外观、网络更新源、关于。"""
from __future__ import annotations

import os

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QFileDialog, QHBoxLayout, QVBoxLayout, QWidget,
)

from qfluentwidgets import (
    BodyLabel, CaptionLabel, CardWidget, ComboBox, FluentIcon as FIF,
    InfoBar, InfoBarPosition, MessageBox, PrimaryPushButton,
    ProgressBar, PushButton, qconfig, SegmentedWidget,
    SingleDirectionScrollArea, StrongBodyLabel, SwitchButton, TitleLabel,
    isDarkTheme, themeColor,
)

from app import APP_DISPLAY, APP_NAME, APP_VERSION
from app.config import app_config
from app.i18n import t
from app.core.ffmpeg import ffmpeg_manager
from app.core.hardware import hw_manager
from app.core.updater import ffmpeg_updater
from app.core.app_updater import app_updater
from app.workers.workers import FunctionThread

from ..theme_aware import restyle_muted, semantic_color, set_muted
from .about_ffmpeg import AboutFFmpegDialog
from .about_prism import AboutPrismDialog


class _ColorSwatch(QWidget):
    """可点击的圆形色板，用于点缀色选择。"""

    clicked = Signal(bool)

    def __init__(self, color_hex: str, parent=None) -> None:
        super().__init__(parent)
        self.color_hex = color_hex
        self._checked = False
        self._enabled = True
        self.setFixedSize(28, 28)
        self.setCursor(Qt.PointingHandCursor)

    def setChecked(self, checked: bool) -> None:
        self._checked = checked
        self.update()

    def setEnabled(self, enabled: bool) -> None:  # noqa: N802
        self._enabled = enabled
        self.update()

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.LeftButton and self._enabled:
            self._checked = True
            self.clicked.emit(True)
            self.update()
        super().mousePressEvent(event)

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        cx = cy = self.width() // 2
        radius = 9
        # 外圈（选中态）
        if self._checked:
            ring = QColor(themeColor().name())
            painter.setPen(QPen(ring, 2))
            path = QPainterPath()
            path.addEllipse(cx, cy, radius * 2 + 6, radius * 2 + 6)
            painter.drawPath(path)
        # 色板
        c = QColor(self.color_hex)
        if not self._enabled:
            c.setAlpha(100)
        painter.setBrush(c)
        painter.setPen(QPen(QColor(0, 0, 0, 40), 1))
        painter.drawEllipse(cx - radius, cy - radius, radius * 2, radius * 2)


class _InfoRow(QWidget):
    """图标 + 标题 + 说明 + 右侧控件的设置行。"""

    def __init__(self, icon, title: str, desc: str, control: QWidget = None,
                 parent=None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 6, 0, 6)
        layout.setSpacing(12)

        icon_label = _IconBadge(icon)
        layout.addWidget(icon_label, 0, Qt.AlignTop)

        texts = QVBoxLayout()
        texts.setSpacing(2)
        self.title_label = StrongBodyLabel(title)
        self.desc_label = CaptionLabel(desc)
        self.desc_label.setWordWrap(True)
        set_muted(self.desc_label, 0.5)
        texts.addWidget(self.title_label)
        texts.addWidget(self.desc_label)
        layout.addLayout(texts, 1)

        if control is not None:
            layout.addWidget(control, 0, Qt.AlignVCenter)


class _IconBadge(QWidget):
    def __init__(self, icon) -> None:
        super().__init__()
        self.setFixedSize(36, 36)
        self._icon = icon

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(self.rect().adjusted(2, 2, -2, -2), 8, 8)
        color = QColor(themeColor().name())
        color.setAlpha(28 if not isDarkTheme() else 42)
        painter.fillPath(path, color)
        self._icon.icon(QColor(themeColor().name())).paint(
            painter, self.rect().adjusted(8, 8, -8, -8)
        )


class SettingsView(QWidget):
    def __init__(self, queue, parent=None) -> None:
        super().__init__(parent)
        self.queue = queue
        self.setObjectName("settingsView")
        self._threads: list[FunctionThread] = []
        self._silent_check = False
        self._ffmpeg_ok = False
        self._pending_latest = ""
        self._hw_probed = False
        self._build_ui()
        self._connect_updater()
        self._connect_app_updater()
        self.refresh_ffmpeg_status()
        self._refresh_hw()
        # 硬件探测（幂等：管理器内部保证同一时刻只有一个探测线程）
        hw_manager.detected.connect(self._on_hw_detected)
        hw_manager.start_probe()
        # 主题切换：刷新次级文字与状态胶囊颜色
        qconfig.themeChanged.connect(self._on_theme_changed)

    # ================================================================ 界面

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(36, 28, 36, 20)
        scroll = SingleDirectionScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea{border: none; background: transparent;}")
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        scroll.setWidget(container)
        outer.addWidget(scroll)

        root = QVBoxLayout(container)
        root.setContentsMargins(2, 0, 14, 8)
        root.setSpacing(14)

        self.title = TitleLabel(t("nav.settings"))
        self.subtitle = BodyLabel(t("settings.subtitle"))
        root.addWidget(self.title)
        root.addWidget(self.subtitle)

        self._build_ffmpeg_card(root)
        self._build_hardware_card(root)
        self._build_appearance_card(root)
        self._build_network_card(root)
        self._build_about_card(root)
        root.addStretch(1)

    def retranslate_ui(self) -> None:
        """语言切换后重新翻译本页面所有可见文案。"""
        # 页面标题
        self.title.setText(t("nav.settings"))
        self.subtitle.setText(t("settings.subtitle"))
        # FFmpeg 卡片
        self.ffmpeg_card_title.setText(t("settings.ffmpeg.title"))
        self.btn_detect.setText(t("settings.ffmpeg.btn_detect"))
        self.btn_manual.setText(t("settings.ffmpeg.btn_manual"))
        self.btn_about.setText(t("settings.ffmpeg.btn_about"))
        # 动态标签：根据当前状态重新生成文案（不重新探测）
        if self._ffmpeg_ok:
            self.lbl_version.setText(
                t("settings.ffmpeg.version_with_source",
                  version=ffmpeg_manager.version or t("common.unknown"),
                  source=ffmpeg_manager.source)
            )
            self.lbl_path.setText(
                t("settings.ffmpeg.path_label", path=ffmpeg_manager.ffmpeg_path)
            )
            self._set_primary_button(check_only=not self._pending_latest)
        else:
            self.lbl_version.setText(t("settings.ffmpeg.version_not_found"))
            self.lbl_path.setText(t("settings.ffmpeg.path_hint"))
            self.btn_primary.setText(t("settings.ffmpeg.btn_download"))
        self._apply_pill_style()
        # 硬件卡片
        self.hw_info_row.title_label.setText(t("settings.hw.title"))
        self.hw_info_row.desc_label.setText(t("settings.hw.desc"))
        self.btn_hw_redetect.setText(t("settings.hw.btn_redetect"))
        self._refresh_hw()
        # 外观卡片
        self.appearance_title.setText(t("settings.appearance.title"))
        for key, text_key in self._theme_keys.items():
            self.theme_segment.setItemText(routeKey=key, text=t(text_key))
        # 语言选择行
        self.lang_info_row.title_label.setText(t("settings.language.label"))
        self.lang_info_row.desc_label.setText(t("settings.language.desc"))
        # 语言下拉框（只有"跟随系统"会变，原生语言名称不变）
        for idx, (_code, name) in enumerate(self._lang_entries):
            if _code == "auto":
                self.combo_lang.setItemText(idx, t("settings.appearance.theme_auto"))
        # 点缀色行
        self.accent_info_row.title_label.setText(t("settings.accent.follow_system_label"))
        self.accent_info_row.desc_label.setText(t("settings.accent.follow_system_desc"))
        for sw, (_hex, key) in zip(self._accent_swatch_btns, self._accent_presets):
            sw.setToolTip(t(key))
        # 网络通道下拉框
        for idx, (_code, key) in enumerate(self._channel_keys):
            self.combo_channel.setItemText(idx, t(key))
        self.network_info_row.title_label.setText(t("settings.network.title"))
        self.network_info_row.desc_label.setText(t("settings.network.desc"))
        self.channel_info_row.title_label.setText(t("settings.network.channel_title"))
        self.channel_info_row.desc_label.setText(t("settings.network.channel_desc"))
        # 关于卡片
        self.about_title.setText(t("settings.about.title"))
        self.about_version_label.setText(
            t("settings.about.version_display", app=APP_DISPLAY, version=APP_VERSION)
        )
        self.attribution_label.setText(t("settings.about.attribution"))
        self.btn_about_ffmpeg_2.setText(t("settings.about.about_ffmpeg_btn"))
        self.btn_check_app_update.setText(t("settings.app_update.btn_check"))
        # 强调色当前状态标签（动态文案）
        self._refresh_accent_label()

    def _build_ffmpeg_card(self, root: QVBoxLayout) -> None:
        card = CardWidget()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(10)

        head = QHBoxLayout()
        self.ffmpeg_card_title = StrongBodyLabel(t("settings.ffmpeg.title"))
        head.addWidget(self.ffmpeg_card_title)
        head.addStretch(1)
        self.status_pill = CaptionLabel(t("settings.ffmpeg.status_detecting"))
        head.addWidget(self.status_pill)
        layout.addLayout(head)

        self.lbl_version = BodyLabel(t("settings.ffmpeg.version_none"))
        self.lbl_path = CaptionLabel(t("settings.ffmpeg.path_none"))
        self.lbl_path.setWordWrap(True)
        layout.addWidget(self.lbl_version)
        layout.addWidget(self.lbl_path)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        self.btn_detect = PushButton(FIF.SYNC, t("settings.ffmpeg.btn_detect"))
        self.btn_manual = PushButton(FIF.FOLDER, t("settings.ffmpeg.btn_manual"))
        self.btn_about = PushButton(FIF.INFO, t("settings.ffmpeg.btn_about"))
        self.btn_primary = PrimaryPushButton(FIF.DOWNLOAD, t("settings.ffmpeg.btn_check_update"))
        btn_row.addWidget(self.btn_detect)
        btn_row.addWidget(self.btn_manual)
        btn_row.addWidget(self.btn_about)
        btn_row.addStretch(1)
        btn_row.addWidget(self.btn_primary)
        layout.addLayout(btn_row)

        self.update_bar = ProgressBar()
        self.update_bar.setRange(0, 100)
        self.update_bar.setValue(0)
        self.update_bar.setVisible(False)
        self.update_caption = CaptionLabel("")
        self.update_caption.setWordWrap(True)
        self.update_caption.setVisible(False)
        layout.addWidget(self.update_bar)
        layout.addWidget(self.update_caption)

        root.addWidget(card)

        self.btn_detect.clicked.connect(lambda: self.refresh_ffmpeg_status(notify=True))
        self.btn_manual.clicked.connect(self._choose_manual_ffmpeg)
        self.btn_about.clicked.connect(lambda: AboutFFmpegDialog(self).exec())
        self.btn_primary.clicked.connect(self._on_primary_clicked)

    def _build_hardware_card(self, root: QVBoxLayout) -> None:
        card = CardWidget()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 14)
        layout.setSpacing(6)

        self.switch_hw = SwitchButton()
        self.switch_hw.setChecked(bool(app_config.get("hw_accel", True)))
        self.hw_info_row = _InfoRow(
            FIF.SPEED_HIGH, t("settings.hw.title"),
            t("settings.hw.desc"),
            self.switch_hw,
        )
        layout.addWidget(self.hw_info_row)

        self.lbl_hw = CaptionLabel(t("settings.hw.detecting"))
        self.lbl_hw.setWordWrap(True)
        layout.addWidget(self.lbl_hw)

        row = QHBoxLayout()
        self.btn_hw_redetect = PushButton(FIF.SYNC, t("settings.hw.btn_redetect"))
        row.addWidget(self.btn_hw_redetect)
        row.addStretch(1)
        layout.addLayout(row)
        root.addWidget(card)

        self.switch_hw.checkedChanged.connect(self._on_hw_toggle)
        self.btn_hw_redetect.clicked.connect(self._redetect_hardware)

    def _build_appearance_card(self, root: QVBoxLayout) -> None:
        card = CardWidget()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 14)
        layout.setSpacing(4)
        self.appearance_title = StrongBodyLabel(t("settings.appearance.title"))
        layout.addWidget(self.appearance_title)

        # ---- 主题模式 ----
        self.theme_segment = SegmentedWidget()
        self._theme_keys = {
            "auto": "settings.appearance.theme_auto",
            "light": "settings.appearance.theme_light",
            "dark": "settings.appearance.theme_dark",
        }
        self.theme_segment.addItem(routeKey="auto", text=t("settings.appearance.theme_auto"))
        self.theme_segment.addItem(routeKey="light", text=t("settings.appearance.theme_light"))
        self.theme_segment.addItem(routeKey="dark", text=t("settings.appearance.theme_dark"))
        self.theme_segment.setCurrentItem(app_config.get("theme", "auto"))
        seg_wrap = QHBoxLayout()
        seg_wrap.addWidget(self.theme_segment)
        seg_wrap.addStretch(1)
        layout.addLayout(seg_wrap)

        # ---- 语言选择 ----
        # 语言名称为原生写法（无需翻译）；仅"跟随系统"走 i18n
        self._lang_entries = [
            ("auto", t("settings.appearance.theme_auto")),
            ("zh_CN", "简体中文"),
            ("zh_HK", "繁體中文（香港）"),
            ("zh_TW", "繁體中文（台灣）"),
            ("en", "English"),
            ("en_US", "English (US)"),
            ("fr", "Français"),
            ("ja", "日本語"),
            ("ru", "Русский"),
            ("es", "Español"),
        ]
        self.combo_lang = ComboBox()
        for code, name in self._lang_entries:
            self.combo_lang.addItem(name, userData=code)
        cur_lang = app_config.get("language", "auto")
        for idx in range(self.combo_lang.count()):
            if self.combo_lang.itemData(idx) == cur_lang:
                self.combo_lang.setCurrentIndex(idx)
                break
        self.combo_lang.setFixedWidth(200)
        self.lang_info_row = _InfoRow(
            FIF.LANGUAGE, t("settings.language.label"),
            t("settings.language.desc"),
            self.combo_lang,
        )
        layout.addWidget(self.lang_info_row)

        # ---- 点缀色 ----
        self.switch_accent = SwitchButton()
        self.switch_accent.setChecked(
            bool(app_config.get("accent_follow_system", True))
        )
        self.accent_info_row = _InfoRow(
            FIF.PALETTE, t("settings.accent.follow_system_label"),
            t("settings.accent.follow_system_desc"),
            self.switch_accent,
        )
        layout.addWidget(self.accent_info_row)

        # 预设色板
        self._accent_presets = [
            ("#0078D4", "settings.accent.preset.blue"),
            ("#E81123", "settings.accent.preset.red"),
            ("#F7630C", "settings.accent.preset.orange"),
            ("#FFB900", "settings.accent.preset.gold"),
            ("#107C10", "settings.accent.preset.green"),
            ("#008566", "settings.accent.preset.teal"),
            ("#5C2D91", "settings.accent.preset.purple"),
            ("#767676", "settings.accent.preset.gray"),
        ]
        swatch_row = QHBoxLayout()
        swatch_row.setSpacing(8)
        self._accent_swatch_btns: list[_ColorSwatch] = []
        cur_accent = app_config.get("accent_color", "system")
        for hex_color, key in self._accent_presets:
            sw = _ColorSwatch(hex_color)
            sw.setToolTip(t(key))
            sw.clicked.connect(lambda _checked, c=hex_color: self._on_accent_picked(c))
            sw.setChecked(cur_accent == hex_color)
            self._accent_swatch_btns.append(sw)
            swatch_row.addWidget(sw)
        swatch_row.addStretch(1)
        layout.addLayout(swatch_row)

        # 自定义颜色当前状态标签
        self.lbl_accent_current = CaptionLabel("")
        self.lbl_accent_current.setWordWrap(True)
        layout.addWidget(self.lbl_accent_current)
        self._refresh_accent_label()

        # 非跟随系统时禁用色板
        self._on_accent_follow_changed(self.switch_accent.isChecked())

        root.addWidget(card)

        self.theme_segment.currentItemChanged.connect(self._on_theme_mode_changed)
        self.combo_lang.currentIndexChanged.connect(self._on_language_changed)
        self.switch_accent.checkedChanged.connect(self._on_accent_follow_changed)

    def _on_language_changed(self, _idx: int) -> None:
        code = self.combo_lang.currentData()
        app_config.set("language", code)
        app_config.sync()
        from app.i18n import set_language
        set_language(code)

    def _on_accent_follow_changed(self, follow: bool) -> None:
        app_config.set("accent_follow_system", follow)
        app_config.sync()
        for sw in self._accent_swatch_btns:
            sw.setEnabled(not follow)
        if follow:
            app_config.set("accent_color", "system")
            app_config.sync()
            from app.core.accent import apply_accent_color
            apply_accent_color(follow_system=True)
        self._refresh_accent_label()

    def _on_accent_picked(self, hex_color: str) -> None:
        if self.switch_accent.isChecked():
            return
        app_config.set("accent_color", hex_color)
        app_config.sync()
        for sw in self._accent_swatch_btns:
            sw.setChecked(sw.color_hex.lower() == hex_color.lower())
        from app.core.accent import apply_accent_color
        apply_accent_color(color=hex_color)
        self._refresh_accent_label()

    def _refresh_accent_label(self) -> None:
        from app.core.accent import read_system_accent, read_system_accent_registry
        follow = self.switch_accent.isChecked()
        if follow:
            sc = read_system_accent() or read_system_accent_registry()
            if sc is not None:
                self.lbl_accent_current.setText(
                    t("settings.accent.current_system",
                      color=f"{sc.rgb() & 0xFFFFFF:06X}")
                )
            else:
                self.lbl_accent_current.setText(t("settings.accent.reading_system"))
        else:
            cur = app_config.get("accent_color", "system")
            self.lbl_accent_current.setText(t("settings.accent.current_custom", color=cur))

    def _build_network_card(self, root: QVBoxLayout) -> None:
        card = CardWidget()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 14, 20, 10)
        layout.setSpacing(4)

        self.switch_auto = SwitchButton()
        self.switch_auto.setChecked(bool(app_config.get("auto_check_update", True)))
        self.network_info_row = _InfoRow(
            FIF.UPDATE, t("settings.network.title"),
            t("settings.network.desc"),
            self.switch_auto,
        )
        layout.addWidget(self.network_info_row)

        self.combo_channel = ComboBox()
        self._channel_keys = [
            ("auto", "settings.network.channel_auto"),
            ("direct", "settings.network.channel_direct"),
            ("ghfast", "settings.network.channel_ghfast"),
            ("ghproxy", "settings.network.channel_ghproxy"),
            ("moeyy", "settings.network.channel_moeyy"),
        ]
        for _code, key in self._channel_keys:
            self.combo_channel.addItem(t(key), userData=_code)
        channel = app_config.get("update_channel", "auto")
        for idx in range(self.combo_channel.count()):
            if self.combo_channel.itemData(idx) == channel:
                self.combo_channel.setCurrentIndex(idx)
                break
        self.combo_channel.setFixedWidth(280)
        self.channel_info_row = _InfoRow(
            FIF.GLOBE, t("settings.network.channel_title"),
            t("settings.network.channel_desc"),
            self.combo_channel,
        )
        layout.addWidget(self.channel_info_row)
        root.addWidget(card)

        self.switch_auto.checkedChanged.connect(
            lambda checked: app_config.set("auto_check_update", checked)
        )
        self.combo_channel.currentIndexChanged.connect(
            lambda _i: app_config.set("update_channel", self.combo_channel.currentData())
        )

    def _build_about_card(self, root: QVBoxLayout) -> None:
        card = CardWidget()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(4)
        self.about_title = StrongBodyLabel(t("settings.about.title"))
        layout.addWidget(self.about_title)
        self.about_version_label = BodyLabel(
            t("settings.about.version_display", app=APP_DISPLAY, version=APP_VERSION)
        )
        layout.addWidget(self.about_version_label)
        self.attribution_label = CaptionLabel(t("settings.about.attribution"))
        self.attribution_label.setWordWrap(True)
        layout.addWidget(self.attribution_label)
        row = QHBoxLayout()
        self.btn_about_prism = PushButton(FIF.APPLICATION, f"{APP_DISPLAY} {APP_NAME}")
        self.btn_about_prism.clicked.connect(lambda: AboutPrismDialog(self).exec())
        row.addWidget(self.btn_about_prism)
        self.btn_about_ffmpeg_2 = PushButton(FIF.INFO, t("settings.about.about_ffmpeg_btn"))
        self.btn_about_ffmpeg_2.clicked.connect(lambda: AboutFFmpegDialog(self).exec())
        row.addWidget(self.btn_about_ffmpeg_2)
        row.addStretch(1)
        layout.addLayout(row)

        # ---- Prism 应用更新 ----
        app_update_row = QHBoxLayout()
        app_update_row.setSpacing(8)
        self.btn_check_app_update = PushButton(FIF.SYNC, t("settings.app_update.btn_check"))
        self.btn_check_app_update.clicked.connect(self._on_check_app_update)
        self.btn_install_app_update = PrimaryPushButton(FIF.DOWNLOAD, t("settings.app_update.btn_install"))
        self.btn_install_app_update.setEnabled(False)
        self.btn_install_app_update.clicked.connect(self._on_install_app_update)
        app_update_row.addWidget(self.btn_check_app_update)
        app_update_row.addWidget(self.btn_install_app_update)
        app_update_row.addStretch(1)
        layout.addLayout(app_update_row)

        self.app_update_bar = ProgressBar()
        self.app_update_bar.setRange(0, 100)
        self.app_update_bar.setValue(0)
        self.app_update_bar.setVisible(False)
        self.app_update_caption = CaptionLabel("")
        self.app_update_caption.setWordWrap(True)
        self.app_update_caption.setVisible(False)
        layout.addWidget(self.app_update_bar)
        layout.addWidget(self.app_update_caption)

        root.addWidget(card)

    # ================================================================ FFmpeg 状态

    def refresh_ffmpeg_status(self, notify: bool = False) -> None:
        manual = app_config.get("manual_ffmpeg_path", "")
        ok = ffmpeg_manager.locate(manual)
        if ok:
            ffmpeg_manager.refresh_version()
            self._ffmpeg_ok = True
            self.lbl_version.setText(
                t("settings.ffmpeg.version_with_source",
                  version=ffmpeg_manager.version or t("common.unknown"),
                  source=ffmpeg_manager.source)
            )
            self.lbl_path.setText(
                t("settings.ffmpeg.path_label", path=ffmpeg_manager.ffmpeg_path)
            )
            self._set_primary_button(check_only=True)
            staged = ffmpeg_updater.read_stage_marker()
            if staged.get("version") and ffmpeg_updater.has_staged():
                self._set_caption(
                    t("settings.ffmpeg.staged_hint", version=staged['version']),
                    visible=True,
                )
            if notify:
                self._info(t("settings.ffmpeg.info_detect_success.title"),
                           ffmpeg_manager.status_text()[1], "success")
        else:
            self._ffmpeg_ok = False
            self.lbl_version.setText(t("settings.ffmpeg.version_not_found"))
            self.lbl_path.setText(t("settings.ffmpeg.path_hint"))
            self.btn_primary.setText(t("settings.ffmpeg.btn_download"))
            if notify:
                self._info(t("settings.ffmpeg.info_not_found.title"),
                           t("settings.ffmpeg.info_not_found.content"), "warning")
        self._apply_pill_style()

    def _apply_pill_style(self) -> None:
        if self._ffmpeg_ok:
            self.status_pill.setText(t("settings.ffmpeg.pill_ready"))
            self.status_pill.setStyleSheet(
                f"color: {semantic_color('success')}; font-weight: 600;"
            )
        else:
            self.status_pill.setText(t("settings.ffmpeg.pill_not_installed"))
            self.status_pill.setStyleSheet(
                f"color: {semantic_color('error')}; font-weight: 600;"
            )

    def _set_primary_button(self, check_only: bool) -> None:
        if check_only:
            self.btn_primary.setIcon(FIF.SYNC)
            self.btn_primary.setText(t("settings.ffmpeg.btn_check_update"))
            self.btn_primary.setEnabled(True)
        elif self._pending_latest:
            self.btn_primary.setIcon(FIF.DOWNLOAD)
            self.btn_primary.setText(
                t("settings.ffmpeg.btn_download_version", version=self._pending_latest)
            )
            self.btn_primary.setEnabled(True)
        else:
            self.btn_primary.setIcon(FIF.SYNC)
            self.btn_primary.setText(t("settings.ffmpeg.btn_check_update"))
            self.btn_primary.setEnabled(True)

    def _choose_manual_ffmpeg(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, t("settings.ffmpeg.dialog_choose_exe"), "",
            t("settings.ffmpeg.dialog_exe_filter")
        )
        if not path:
            return
        app_config.set("manual_ffmpeg_path", os.path.normpath(path))
        self.refresh_ffmpeg_status(notify=True)
        # 手动指定的引擎可能支持不同编码器，强制重新探测
        hw_manager.start_probe(force_verify=True)

    # ================================================================ 硬件加速

    def _on_hw_toggle(self, checked: bool) -> None:
        app_config.set("hw_accel", checked)
        app_config.sync()
        self._refresh_hw()

    def _redetect_hardware(self) -> None:
        started = hw_manager.start_probe(force_verify=True)
        if started:
            self.lbl_hw.setText(t("settings.hw.redetecting"))
        else:
            self._info(t("settings.hw.info_in_progress.title"),
                       t("settings.hw.info_in_progress.content"),
                       "info", duration=1600)

    def _on_hw_detected(self, report) -> None:
        self._hw_probed = True
        self._refresh_hw(report)

    def _refresh_hw(self, report=None) -> None:
        report = report or hw_manager.report
        if not self._hw_probed and not (report.gpus or report.cpu):
            self.lbl_hw.setText(t("settings.hw.detecting"))
            return
        lines = report.describe_lines()
        if not app_config.get("hw_accel", True):
            lines.append(t("settings.hw.disabled_note"))
        self.lbl_hw.setText("\n".join(lines))

    # ================================================================ 更新流程

    def _connect_updater(self) -> None:
        u = ffmpeg_updater
        u.checking.connect(self._on_checking)
        u.checked.connect(self._on_checked)
        u.progress.connect(self._on_progress)
        u.finished.connect(self._on_first_install_finished)
        u.staged.connect(self._on_staged)
        u.busy_changed.connect(self._set_busy)

    # ================================================================ Prism 应用更新

    def _connect_app_updater(self) -> None:
        au = app_updater
        au.checking.connect(self._on_app_checking)
        au.checked.connect(self._on_app_checked)
        au.progress.connect(self._on_app_progress)
        au.finished.connect(self._on_app_download_finished)
        au.busy_changed.connect(self._on_app_busy_changed)

    def _on_check_app_update(self) -> None:
        """启动 Prism 版本检查。"""
        if app_updater.busy:
            return
        thread = FunctionThread(app_updater.check_and_compare)
        self._threads.append(thread)
        thread.failed.connect(self._on_thread_error)
        thread.finished.connect(lambda: self._cleanup_thread(thread))
        thread.start()

    def _on_app_checking(self) -> None:
        self.btn_check_app_update.setEnabled(False)
        self.app_update_bar.setVisible(True)
        self.app_update_caption.setVisible(True)
        self.app_update_bar.setValue(2)
        self.app_update_caption.setText(t("settings.app_update.caption_connecting"))

    def _on_app_checked(self, success: bool, has_update: bool,
                        message: str, latest: str) -> None:
        self.btn_check_app_update.setEnabled(True)
        self.app_update_bar.setVisible(False)
        if not success:
            self.app_update_caption.setText(message)
            self.app_update_caption.setVisible(True)
            self._info(t("settings.app_update.info_check_failed.title"),
                       message, "warning", duration=4000)
            return

        if has_update:
            self.app_update_caption.setText(message)
            self.app_update_caption.setVisible(True)
            self.btn_install_app_update.setEnabled(True)
            self.btn_install_app_update.setText(
                t("settings.app_update.btn_download_version", version=latest)
            )
            box = MessageBox(
                t("settings.app_update.dialog_new_version.title"),
                message, self,
            )
            box.yesButton.setText(t("settings.app_update.dialog_new_version.btn_download"))
            box.cancelButton.setText(t("common.later"))
            if box.exec():
                self._start_app_download()
        else:
            self.btn_install_app_update.setEnabled(False)
            self.app_update_caption.setText(message)
            self.app_update_caption.setVisible(True)
            self._info(t("settings.app_update.info_already_latest.title"),
                       message, "success", duration=3600)

    def _start_app_download(self) -> None:
        """后台下载 Prism 安装包。"""
        if app_updater.busy:
            return
        self.app_update_bar.setVisible(True)
        self.app_update_caption.setVisible(True)
        self.app_update_bar.setValue(2)
        self.app_update_caption.setText(t("settings.app_update.caption_preparing_download"))
        thread = FunctionThread(app_updater.download_update)
        self._threads.append(thread)
        thread.failed.connect(self._on_thread_error)
        thread.finished.connect(lambda: self._cleanup_thread(thread))
        thread.start()

    def _on_app_progress(self, percent: int, text: str) -> None:
        self.app_update_bar.setVisible(True)
        self.app_update_bar.setValue(max(0, min(100, percent)))
        self.app_update_caption.setText(text)
        self.app_update_caption.setVisible(True)

    def _on_app_download_finished(self, success: bool, message: str) -> None:
        self.app_update_bar.setValue(100 if success else self.app_update_bar.value())
        self.app_update_caption.setText(message)
        self.app_update_caption.setVisible(True)
        if success:
            self.btn_install_app_update.setEnabled(True)
            self.btn_install_app_update.setText(t("settings.app_update.btn_install"))
            self._info(t("settings.app_update.info_download_done.title"),
                       message, "success", duration=5000)
        else:
            self._info(t("settings.app_update.info_download_failed.title"),
                       message, "error", duration=5000)

    def _on_install_app_update(self) -> None:
        """运行已下载的安装程序。"""
        if app_updater.downloaded_path:
            box = MessageBox(
                t("settings.app_update.dialog_install.title"),
                t("settings.app_update.dialog_install.content"),
                self,
            )
            box.yesButton.setText(t("settings.app_update.dialog_install.btn_install"))
            box.cancelButton.setText(t("common.cancel"))
            if box.exec():
                if app_updater.run_installer():
                    self._info(
                        t("settings.app_update.info_installing.title"),
                        t("settings.app_update.info_installing.content"),
                        "info", duration=3000,
                    )
                else:
                    self._info(
                        t("settings.app_update.info_install_failed.title"),
                        t("settings.app_update.info_install_failed.content"),
                        "error", duration=4000,
                    )
        else:
            self._start_app_download()

    def _on_app_busy_changed(self, busy: bool) -> None:
        self.btn_check_app_update.setEnabled(not busy)
        if not busy:
            self.app_update_bar.setRange(0, 100)
            self.app_update_bar.setValue(0)

    def check_update(self, silent: bool = False) -> None:
        """启动后台版本检查；仅比对版本，不下载。"""
        if ffmpeg_updater.busy:
            return
        self._silent_check = silent
        thread = FunctionThread(ffmpeg_updater.check_and_compare)
        self._threads.append(thread)
        thread.finished.connect(lambda: self._cleanup_thread(thread))
        thread.start()

    def _on_checking(self) -> None:
        self.btn_primary.setEnabled(False)
        if not self._silent_check:
            self._set_caption(t("settings.ffmpeg.caption_connecting"), visible=True)

    def _on_primary_clicked(self) -> None:
        """未安装 → 首装；已安装且有待下载新版 → 暂存下载；否则执行版本检查。"""
        if ffmpeg_updater.busy:
            return
        if not ffmpeg_manager.available:
            self.download()
            return
        if self._pending_latest:
            self._ask_then_stage()
            return
        self.check_update(silent=False)

    def download(self) -> None:
        """未安装 FFmpeg 时的首装：立即下载并安装。"""
        if ffmpeg_updater.busy:
            return
        self.update_bar.setVisible(True)
        self.update_caption.setVisible(True)
        self.update_bar.setValue(2)
        self.update_caption.setText(t("settings.ffmpeg.caption_preparing_download"))
        thread = FunctionThread(ffmpeg_updater.download_and_install)
        self._threads.append(thread)
        thread.failed.connect(self._on_thread_error)
        thread.finished.connect(lambda: self._cleanup_thread(thread))
        thread.start()

    def _ask_then_stage(self) -> None:
        version = self._pending_latest
        box = MessageBox(
            t("settings.ffmpeg.dialog_new_version.title"),
            t("settings.ffmpeg.dialog_new_version.content", version=version),
            self,
        )
        box.yesButton.setText(t("settings.ffmpeg.dialog_new_version.btn_download"))
        box.cancelButton.setText(t("common.later"))
        if box.exec():
            self.start_staging()
        else:
            self._pending_latest = ""
            self._set_primary_button(check_only=True)

    def start_staging(self) -> None:
        """后台下载更新包到暂存区（不安装）。"""
        if ffmpeg_updater.busy:
            return
        self.update_bar.setVisible(True)
        self.update_caption.setVisible(True)
        self.update_bar.setValue(2)
        self.update_caption.setText(t("settings.ffmpeg.caption_preparing_staging"))
        thread = FunctionThread(ffmpeg_updater.download_only)
        self._threads.append(thread)
        thread.failed.connect(self._on_thread_error)
        thread.finished.connect(lambda: self._cleanup_thread(thread))
        thread.start()

    def _on_checked(self, success: bool, has_update: bool, message: str,
                    latest: str) -> None:
        self.btn_primary.setEnabled(True)
        silent = self._silent_check
        self._silent_check = False

        if not success:
            self._set_caption("" , visible=False)
            if not silent:
                self._info(t("settings.ffmpeg.info_check_failed.title"),
                           message, "warning", duration=4000)
            return

        if not ffmpeg_manager.available:
            # 未安装由首装流程负责（启动弹窗 / 主按钮首装）
            return

        if has_update:
            self._pending_latest = latest
            if silent:
                # 启动后的静默检查：直接后台下载暂存，全程不弹窗
                self.start_staging()
            else:
                self.update_caption.setText(message)
                self.update_caption.setVisible(True)
                self._ask_then_stage()
            return

        # 无新版本：手动检查时明确告知
        self._pending_latest = ""
        self._set_primary_button(check_only=True)
        if not silent:
            self._set_caption(message, visible=True)
            self._info(t("settings.ffmpeg.info_already_latest.title"),
                       message, "success", duration=3600)

    def _on_progress(self, percent: int, text: str) -> None:
        self.update_bar.setVisible(True)
        self.update_bar.setValue(max(0, min(100, percent)))
        self.update_caption.setText(text)
        self.update_caption.setVisible(True)

    def _on_first_install_finished(self, success: bool, message: str) -> None:
        self.update_bar.setValue(100 if success else self.update_bar.value())
        self.refresh_ffmpeg_status()
        if success:
            self._info(t("settings.ffmpeg.info_install_done.title"),
                       message, "success", duration=4000)
            # 新引擎就位，强制做一次完整硬件探测
            hw_manager.start_probe(force_verify=True)
        else:
            self._info(t("settings.ffmpeg.info_install_failed.title"),
                       message, "error", duration=5000)

    def _on_staged(self, success: bool, message: str) -> None:
        self._pending_latest = ""
        if success:
            self._set_primary_button(check_only=True)
            self._set_caption(message, visible=True)
            self._info(t("settings.ffmpeg.info_staged.title"),
                       message, "success", duration=5000)
        else:
            self._set_primary_button(check_only=True)
            # 静默自动下载失败（常见于网络受限）不打扰用户
            self._set_caption(message, visible=True)
            self._info(t("settings.ffmpeg.info_stage_failed.title"),
                       message, "error", duration=5000)

    def _set_caption(self, text: str, visible: bool) -> None:
        self.update_caption.setText(text)
        self.update_caption.setVisible(visible)

    def _set_busy(self, busy: bool) -> None:
        self.btn_primary.setEnabled(not busy)
        self.btn_detect.setEnabled(not busy)
        self.btn_manual.setEnabled(not busy)
        if not busy:
            self.update_bar.setRange(0, 100)
            self.update_bar.setValue(0)
            self.update_bar.setVisible(False)

    def _on_theme_mode_changed(self, key: str) -> None:
        from qfluentwidgets import Theme, setTheme
        mapping = {"auto": Theme.AUTO, "light": Theme.LIGHT, "dark": Theme.DARK}
        setTheme(mapping.get(key, Theme.AUTO))
        app_config.set("theme", key)

    def _on_theme_changed(self, _theme=None) -> None:
        restyle_muted(self)
        self._apply_pill_style()

    def _on_thread_error(self, tb: str) -> None:
        self._info(t("settings.ffmpeg.info_exception.title"),
                   tb[-300:], "error", duration=6000)

    def _cleanup_thread(self, thread: FunctionThread) -> None:
        try:
            self._threads.remove(thread)
        except ValueError:
            pass
        thread.deleteLater()

    def shutdown(self) -> None:
        """窗口关闭前等待后台检查/下载线程结束，避免退出时崩溃。"""
        for thread in list(self._threads):
            if thread.isRunning():
                thread.wait(3000)

    def _info(self, title: str, content: str, kind: str = "info",
              duration: int = 2600) -> None:
        params = dict(orient=Qt.Horizontal, isClosable=True,
                      position=InfoBarPosition.TOP_RIGHT, duration=duration,
                      parent=self)
        bar = {
            "success": InfoBar.success,
            "warning": InfoBar.warning,
            "error": InfoBar.error,
            "info": InfoBar.info,
        }.get(kind, InfoBar.info)
        bar(title, content, **params)
