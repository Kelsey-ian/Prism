# -*- coding: utf-8 -*-
"""帮助页面：快速上手、支持格式、常见问题、FFmpeg 资源。"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from qfluentwidgets import (
    BodyLabel, CaptionLabel, CardWidget, FluentIcon as FIF,
    PrimaryPushButton, qconfig, SingleDirectionScrollArea,
    StrongBodyLabel, TitleLabel,
)

from app.core.presets import AUDIO_TARGETS, IMAGE_TARGETS, VIDEO_TARGETS
from app.i18n import t

from ..theme_aware import restyle_muted, set_muted
from .about_ffmpeg import AboutFFmpegDialog


# 步骤序号：1..4，对应 help.step.{n}.title / help.step.{n}.desc
_STEP_INDICES = (1, 2, 3, 4)

# FAQ 序号：1..8，对应 help.faq.{n}.q / help.faq.{n}.a
_FAQ_INDICES = (1, 2, 3, 4, 5, 6, 7, 8)

# 支持格式的分类：(i18n 键, 预设列表)
_FORMAT_SECTIONS = (
    ("help.formats.video_section", VIDEO_TARGETS),
    ("help.formats.audio_section", AUDIO_TARGETS),
    ("help.formats.image_section", IMAGE_TARGETS),
)


class HelpView(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("helpView")
        self._build_ui()
        qconfig.themeChanged.connect(lambda _theme: restyle_muted(self))

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

        self.title = TitleLabel(t("help.title"))
        self.subtitle = BodyLabel(t("help.subtitle"))
        root.addWidget(self.title)
        root.addWidget(self.subtitle)

        # 快速开始
        start_card = CardWidget()
        start_layout = QVBoxLayout(start_card)
        start_layout.setContentsMargins(20, 18, 20, 18)
        start_layout.setSpacing(10)
        self.start_title = StrongBodyLabel(t("help.quick_start.title"))
        start_layout.addWidget(self.start_title)
        self._step_items = []  # [(title_label, desc_label, index)]
        for index in _STEP_INDICES:
            row = QVBoxLayout()
            row.setSpacing(2)
            title_label = BodyLabel(f"{index}.  {t(f'help.step.{index}.title')}")
            title_label.setStyleSheet("font-weight: 600;")
            desc_label = CaptionLabel(t(f"help.step.{index}.desc"))
            desc_label.setWordWrap(True)
            set_muted(desc_label, 0.55)
            row.addWidget(title_label)
            row.addWidget(desc_label)
            start_layout.addLayout(row)
            self._step_items.append((title_label, desc_label, index))
        root.addWidget(start_card)

        # 支持的格式
        format_card = CardWidget()
        format_layout = QVBoxLayout(format_card)
        format_layout.setContentsMargins(20, 18, 20, 18)
        format_layout.setSpacing(8)
        self.format_title = StrongBodyLabel(t("help.formats.title"))
        format_layout.addWidget(self.format_title)
        self._format_labels = []  # [(label, section_key, targets)]
        for section_key, targets in _FORMAT_SECTIONS:
            section_title = t(section_key)
            names = "、".join(
                target.label.split("（")[0].strip() for target in targets
            )
            label = CaptionLabel(f"{section_title}：{names}")
            label.setWordWrap(True)
            set_muted(label, 0.65)
            format_layout.addWidget(label)
            self._format_labels.append((label, section_key, targets))
        self.format_note = CaptionLabel(t("help.formats.note"))
        self.format_note.setWordWrap(True)
        set_muted(self.format_note, 0.45)
        format_layout.addWidget(self.format_note)
        root.addWidget(format_card)

        # FFmpeg 引擎与资源
        engine_card = CardWidget()
        engine_layout = QVBoxLayout(engine_card)
        engine_layout.setContentsMargins(20, 18, 20, 18)
        engine_layout.setSpacing(8)
        self.engine_title = StrongBodyLabel(t("help.engine.title"))
        engine_layout.addWidget(self.engine_title)
        self.engine_desc = CaptionLabel(t("help.engine.desc"))
        self.engine_desc.setWordWrap(True)
        set_muted(self.engine_desc, 0.55)
        engine_layout.addWidget(self.engine_desc)
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        self.btn_about_ffmpeg = PrimaryPushButton(FIF.INFO, t("help.engine.about_btn"))
        self.btn_about_ffmpeg.clicked.connect(self._show_about_ffmpeg)
        btn_row.addWidget(self.btn_about_ffmpeg)
        btn_row.addStretch(1)
        engine_layout.addLayout(btn_row)
        root.addWidget(engine_card)

        # FAQ
        faq_card = CardWidget()
        faq_layout = QVBoxLayout(faq_card)
        faq_layout.setContentsMargins(20, 18, 20, 18)
        faq_layout.setSpacing(10)
        self.faq_title = StrongBodyLabel(t("help.faq.title"))
        faq_layout.addWidget(self.faq_title)
        self._faq_items = []  # [(q_label, a_label, index)]
        for index in _FAQ_INDICES:
            box = QVBoxLayout()
            box.setSpacing(2)
            q = BodyLabel(t("help.faq.q_prefix") + t(f"help.faq.{index}.q"))
            q.setStyleSheet("font-weight: 600;")
            a = CaptionLabel(t("help.faq.a_prefix") + t(f"help.faq.{index}.a"))
            a.setWordWrap(True)
            set_muted(a, 0.55)
            box.addWidget(q)
            box.addWidget(a)
            faq_layout.addLayout(box)
            self._faq_items.append((q, a, index))
        root.addWidget(faq_card)
        root.addStretch(1)

    def retranslate_ui(self) -> None:
        """语言切换后重新翻译本页面所有可见文案。"""
        self.title.setText(t("help.title"))
        self.subtitle.setText(t("help.subtitle"))
        self.start_title.setText(t("help.quick_start.title"))
        for title_label, desc_label, index in self._step_items:
            title_label.setText(f"{index}.  {t(f'help.step.{index}.title')}")
            desc_label.setText(t(f"help.step.{index}.desc"))
        self.format_title.setText(t("help.formats.title"))
        for label, section_key, targets in self._format_labels:
            section_title = t(section_key)
            names = "、".join(
                target.label.split("（")[0].strip() for target in targets
            )
            label.setText(f"{section_title}：{names}")
        self.format_note.setText(t("help.formats.note"))
        self.engine_title.setText(t("help.engine.title"))
        self.engine_desc.setText(t("help.engine.desc"))
        self.btn_about_ffmpeg.setText(t("help.engine.about_btn"))
        self.faq_title.setText(t("help.faq.title"))
        for q_label, a_label, index in self._faq_items:
            q_label.setText(t("help.faq.q_prefix") + t(f"help.faq.{index}.q"))
            a_label.setText(t("help.faq.a_prefix") + t(f"help.faq.{index}.a"))

    def _show_about_ffmpeg(self) -> None:
        AboutFFmpegDialog(self).exec()
