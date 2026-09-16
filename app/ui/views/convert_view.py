# -*- coding: utf-8 -*-
"""格式转换主页面：分类导航 / 拖放添加 / 文件列表 / 输出设置 / 发起转换。"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, List, Optional

from PySide6.QtCore import Qt, QThreadPool, QUrl, Signal
from PySide6.QtGui import QColor, QDesktopServices
from PySide6.QtWidgets import (
    QFileDialog, QFrame, QGridLayout, QHBoxLayout, QHeaderView, QLabel,
    QSizePolicy, QTableWidgetItem, QVBoxLayout, QWidget,
)

from qfluentwidgets import (
    BodyLabel, CaptionLabel, CardWidget, ComboBox, FluentIcon as FIF,
    InfoBar, InfoBarPosition, LineEdit, Pivot, PrimaryPushButton, ProgressBar,
    PushButton, qconfig, RadioButton, SingleDirectionScrollArea,
    StrongBodyLabel, TableWidget, TitleLabel, TransparentToolButton,
)

from app.config import app_config
from app.core.ffmpeg import ffmpeg_manager
from app.core.models import ConversionTask, MediaCategory, TaskStatus
from app.core.presets import (
    FRAME_RATES, RESOLUTIONS, detect_category, format_file_size, is_supported,
    iter_media_files, targets_for_category,
)
from app.i18n import t
from app.workers.workers import FileScanWorker, MetaProbeWorker

from ..components.drop_card import DropCard
from ..theme_aware import muted_color, restyle_muted, semantic_color, set_muted

_CATEGORIES = [
    ("video", MediaCategory.VIDEO, "convert.category.video"),
    ("audio", MediaCategory.AUDIO, "convert.category.audio"),
    ("image", MediaCategory.IMAGE, "convert.category.image"),
]

_DIALOG_FILTER = {
    MediaCategory.VIDEO: "convert.filter.video",
    MediaCategory.AUDIO: "convert.filter.audio",
    MediaCategory.IMAGE: "convert.filter.image",
}

_CONFLICT_OPTIONS = [
    ("rename", "convert.conflict.rename"),
    ("overwrite", "convert.conflict.overwrite"),
    ("skip", "convert.conflict.skip"),
]


@dataclass
class FileEntry:
    path: str
    category: MediaCategory
    size: int = 0
    meta: str = ""
    tid: Optional[str] = None


class _StatusCell(QWidget):
    """表格“状态”单元格：状态图标 + 进度条 + 状态文字。"""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(2)

        row = QHBoxLayout()
        row.setSpacing(6)
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(18, 18)
        self.caption = CaptionLabel(t("convert.status_cell.default"))
        row.addWidget(self.icon_label)
        row.addWidget(self.caption)
        row.addStretch(1)

        self.bar = ProgressBar()
        self.bar.setFixedHeight(4)
        self.bar.setTextVisible(False)
        self.bar.setRange(0, 100)
        self.bar.setValue(0)
        self.bar.hide()

        layout.addLayout(row)
        layout.addWidget(self.bar)

        self._last_status = TaskStatus.WAITING
        self._last_progress = 0.0
        self._icon = FIF.HISTORY
        self.set_state(TaskStatus.WAITING)

    @staticmethod
    def _status_style(status: TaskStatus):
        """返回当前主题下的 (图标, 颜色)。"""
        icon_map = {
            TaskStatus.WAITING: FIF.HISTORY,
            TaskStatus.RUNNING: FIF.SYNC,
            TaskStatus.COMPLETED: FIF.ACCEPT,
            TaskStatus.FAILED: FIF.CANCEL,
            TaskStatus.CANCELED: FIF.CANCEL,
            TaskStatus.SKIPPED: FIF.INFO,
            TaskStatus.PAUSED: FIF.PAUSE,
        }
        icon = icon_map.get(status, FIF.INFO)
        if status == TaskStatus.COMPLETED:
            color = QColor(semantic_color("success"))
        elif status == TaskStatus.FAILED:
            color = QColor(semantic_color("error"))
        elif status == TaskStatus.RUNNING:
            color = QColor(semantic_color("info"))
        else:
            color = muted_color(alpha_light=140, alpha_dark=170)
        return icon, color

    def set_state(self, status: TaskStatus, progress: float = 0.0) -> None:
        self._last_status = status
        self._last_progress = progress
        icon, color = self._status_style(status)
        self._icon = icon
        self.icon_label.setPixmap(icon.icon(color).pixmap(17, 17))
        self.caption.setText(status.label)
        self.caption.setStyleSheet(
            f"color: rgb({color.red()},{color.green()},{color.blue()});"
        )
        self.caption.setToolTip("")

        if status in (TaskStatus.RUNNING, TaskStatus.PAUSED):
            self.bar.show()
            self.bar.setRange(0, 100)
            self.bar.setValue(max(0, min(100, int(progress * 100))))
        else:
            self.bar.hide()

    def restyle(self) -> None:
        """主题切换后按当前状态重新着色。"""
        self.set_state(self._last_status, self._last_progress)

    def show_error_tip(self, text: str) -> None:
        self.caption.setToolTip(text)


class ConvertView(QWidget):
    go_settings = Signal()

    def __init__(self, queue, parent=None) -> None:
        super().__init__(parent)
        self.queue = queue
        self.setObjectName("convertView")

        self._files: Dict[MediaCategory, List[FileEntry]] = {
            MediaCategory.VIDEO: [],
            MediaCategory.AUDIO: [],
            MediaCategory.IMAGE: [],
        }
        self.category = MediaCategory(app_config.get("last_category", "video"))
        if isinstance(self.category, str):
            self.category = MediaCategory(self.category)

        self.probe_pool = QThreadPool(self)
        self.probe_pool.setMaxThreadCount(2)

        self._building = False
        self._build_ui()
        self._connect_signals()
        self._set_category(self.category)

        # 主题切换：刷新所有次级文字与状态单元格颜色
        qconfig.themeChanged.connect(self._on_theme_changed)

    def _on_theme_changed(self, _theme=None) -> None:
        restyle_muted(self)
        self._update_mode_label()
        for row in range(self.table.rowCount()):
            cell = self.table.cellWidget(row, 4)
            if isinstance(cell, _StatusCell):
                cell.restyle()

    def retranslate_ui(self) -> None:
        """语言切换后重新翻译本页面所有可见文案。"""
        self.title.setText(t("convert.title"))
        self.subtitle.setText(t("convert.subtitle"))
        for key, _cat, text_key in _CATEGORIES:
            self.pivot.setItemText(routeKey=key, text=t(text_key))
        self.mode_badge_label.setText(t("convert.current_mode"))
        self._update_mode_label()
        self.drop_card.retranslate_ui()
        self.file_list_title.setText(t("convert.file_list.title"))
        self.btn_add.setText(t("convert.file_list.add_files"))
        self.btn_add_dir.setText(t("convert.file_list.add_folder"))
        self.btn_clear.setText(t("convert.file_list.clear"))
        self.table.setHorizontalHeaderLabels(
            [t(k) for k in self._table_header_keys]
        )
        self.output_title.setText(t("convert.output.title"))
        for label, title_key in self._field_labels:
            label.setText(t(title_key))
        self.output_dest_label.setText(t("convert.output.destination"))
        self.radio_source_dir.setText(t("convert.output.source_dir"))
        self.radio_custom_dir.setText(t("convert.output.custom_dir"))
        self.edit_output_dir.setPlaceholderText(t("convert.output.dir_placeholder"))
        self.conflict_label.setText(t("convert.output.conflict"))
        for idx, label_key in enumerate(self._conflict_keys):
            self.combo_conflict.setItemText(idx, t(label_key))
        self.btn_start.setText(t("convert.start"))
        # 自定义分辨率输入框占位符
        self.edit_res_width.setPlaceholderText(t("convert.output.res_width"))
        self.edit_res_height.setPlaceholderText(t("convert.output.res_height"))
        # 重新计算依赖计数的动态文案
        self._update_summary()
        for row in range(self.table.rowCount()):
            cell = self.table.cellWidget(row, 4)
            if isinstance(cell, _StatusCell):
                cell.restyle()

    # ================================================================ UI 构建

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
        root.setSpacing(14)
        root.setContentsMargins(2, 0, 14, 8)

        # 标题
        self.title = TitleLabel(t("convert.title"))
        self.subtitle = BodyLabel(t("convert.subtitle"))
        set_muted(self.subtitle, 0.55)
        root.addWidget(self.title)
        root.addWidget(self.subtitle)

        # 分类 Pivot
        self.pivot = Pivot()
        for key, _cat, text_key in _CATEGORIES:
            self.pivot.addItem(routeKey=key, text=t(text_key))
        root.addWidget(self.pivot)

        # 当前模式指示器
        mode_row = QHBoxLayout()
        mode_row.setSpacing(6)
        self.mode_icon_label = QLabel()
        self.mode_icon_label.setFixedSize(26, 26)
        self.mode_badge_label = CaptionLabel(t("convert.current_mode"))
        set_muted(self.mode_badge_label, 0.55)
        self.mode_name_label = StrongBodyLabel()
        mode_row.addWidget(self.mode_icon_label)
        mode_row.addWidget(self.mode_badge_label)
        mode_row.addWidget(self.mode_name_label)
        mode_row.addStretch(1)
        root.addLayout(mode_row)

        # 拖放卡片
        self.drop_card = DropCard()
        root.addWidget(self.drop_card)

        # 文件列表卡片
        self.files_card = CardWidget()
        files_layout = QVBoxLayout(self.files_card)
        files_layout.setContentsMargins(20, 16, 20, 16)
        files_layout.setSpacing(10)

        head_row = QHBoxLayout()
        self.file_list_title = StrongBodyLabel(t("convert.file_list.title"))
        head_row.addWidget(self.file_list_title)
        self.count_label = CaptionLabel(t("convert.file_list.count_zero"))
        head_row.addSpacing(8)
        head_row.addWidget(self.count_label)
        head_row.addStretch(1)
        self.btn_add = PushButton(FIF.ADD, t("convert.file_list.add_files"))
        self.btn_add_dir = PushButton(FIF.FOLDER, t("convert.file_list.add_folder"))
        self.btn_clear = PushButton(FIF.DELETE, t("convert.file_list.clear"))
        for btn in (self.btn_add, self.btn_add_dir, self.btn_clear):
            head_row.addWidget(btn)
        files_layout.addLayout(head_row)

        self.table = TableWidget()
        self.table.setColumnCount(6)
        self._table_header_keys = [
            "convert.column.filename", "convert.column.source_format",
            "convert.column.size", "convert.column.media_info",
            "convert.column.status", "convert.column.action",
        ]
        self.table.setHorizontalHeaderLabels(
            [t(k) for k in self._table_header_keys]
        )
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(TableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(TableWidget.SelectRows)
        self.table.setSelectionMode(TableWidget.ExtendedSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setBorderVisible(False)
        self.table.setMinimumHeight(220)
        self.table.setShowGrid(False)
        header = self.table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for col in range(1, 6):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().setDefaultSectionSize(46)
        files_layout.addWidget(self.table)
        root.addWidget(self.files_card)

        # 输出设置卡片
        setting_card = CardWidget()
        setting_layout = QVBoxLayout(setting_card)
        setting_layout.setContentsMargins(20, 16, 20, 18)
        setting_layout.setSpacing(12)
        self.output_title = StrongBodyLabel(t("convert.output.title"))
        setting_layout.addWidget(self.output_title)

        opt_row = QGridLayout()
        opt_row.setHorizontalSpacing(18)
        opt_row.setVerticalSpacing(4)

        self.combo_format = ComboBox()
        self.combo_preset = ComboBox()
        self.combo_resolution = ComboBox()
        self.combo_fps = ComboBox()
        self.combo_format.setMinimumWidth(218)
        self.combo_preset.setMinimumWidth(238)
        self.combo_resolution.setMinimumWidth(168)
        self.combo_fps.setMinimumWidth(150)
        for value, label in RESOLUTIONS:
            self.combo_resolution.addItem(label, userData=value)
        for value, label in FRAME_RATES:
            self.combo_fps.addItem(label, userData=value)

        self._field_labels: List[tuple] = []
        opt_row.addWidget(self._wrap_field("convert.output.format", self.combo_format), 0, 0)
        opt_row.addWidget(self._wrap_field("convert.output.preset", self.combo_preset), 0, 1)

        # 分辨率字段（含自定义分辨率输入行）
        self.resolution_field = QWidget()
        res_layout = QVBoxLayout(self.resolution_field)
        res_layout.setContentsMargins(0, 0, 0, 0)
        res_layout.setSpacing(2)
        self.res_label = CaptionLabel(t("convert.output.resolution"))
        set_muted(self.res_label, 0.55)
        self._field_labels.append((self.res_label, "convert.output.resolution"))
        res_layout.addWidget(self.res_label)
        res_layout.addWidget(self.combo_resolution)

        # 自定义分辨率输入行（默认隐藏）
        self.custom_res_row = QWidget()
        custom_res_layout = QHBoxLayout(self.custom_res_row)
        custom_res_layout.setContentsMargins(0, 0, 0, 0)
        custom_res_layout.setSpacing(4)
        self.edit_res_width = LineEdit()
        self.edit_res_width.setPlaceholderText(t("convert.output.res_width"))
        self.edit_res_width.setFixedWidth(76)
        self.edit_res_width.setValidator(None)
        self.res_sep_label = BodyLabel("×")
        self.edit_res_height = LineEdit()
        self.edit_res_height.setPlaceholderText(t("convert.output.res_height"))
        self.edit_res_height.setFixedWidth(76)
        custom_res_layout.addWidget(self.edit_res_width)
        custom_res_layout.addWidget(self.res_sep_label)
        custom_res_layout.addWidget(self.edit_res_height)
        custom_res_layout.addStretch(1)
        res_layout.addWidget(self.custom_res_row)
        self.custom_res_row.setVisible(False)

        opt_row.addWidget(self.resolution_field, 0, 2)
        self.fps_field = self._wrap_field("convert.output.fps", self.combo_fps)
        opt_row.addWidget(self.fps_field, 0, 3)
        opt_row.setColumnStretch(4, 1)
        setting_layout.addLayout(opt_row)

        # 输出位置
        dir_row = QHBoxLayout()
        dir_row.setSpacing(10)
        self.output_dest_label = BodyLabel(t("convert.output.destination"))
        dir_row.addWidget(self.output_dest_label)
        self.radio_source_dir = RadioButton(t("convert.output.source_dir"))
        self.radio_custom_dir = RadioButton(t("convert.output.custom_dir"))
        self.edit_output_dir = LineEdit()
        self.edit_output_dir.setPlaceholderText(t("convert.output.dir_placeholder"))
        self.edit_output_dir.setMinimumWidth(280)
        self.btn_browse = TransparentToolButton(FIF.FOLDER)
        dir_row.addWidget(self.radio_source_dir)
        dir_row.addWidget(self.radio_custom_dir)
        dir_row.addWidget(self.edit_output_dir, 1)
        dir_row.addWidget(self.btn_browse)
        setting_layout.addLayout(dir_row)

        # 冲突策略
        conflict_row = QHBoxLayout()
        conflict_row.setSpacing(10)
        self.conflict_label = BodyLabel(t("convert.output.conflict"))
        conflict_row.addWidget(self.conflict_label)
        self.combo_conflict = ComboBox()
        self._conflict_keys: List[str] = []
        for value, label_key in _CONFLICT_OPTIONS:
            self.combo_conflict.addItem(t(label_key), userData=value)
            self._conflict_keys.append(label_key)
        conflict_row.addWidget(self.combo_conflict)
        conflict_row.addStretch(1)
        setting_layout.addLayout(conflict_row)

        # 底部操作行
        footer_row = QHBoxLayout()
        self.summary_label = CaptionLabel(t("convert.summary.ready"))
        self.btn_start = PrimaryPushButton(FIF.PLAY, t("convert.start"))
        self.btn_start.setFixedHeight(38)
        self.btn_start.setMinimumWidth(170)
        footer_row.addWidget(self.summary_label)
        footer_row.addStretch(1)
        footer_row.addWidget(self.btn_start)
        setting_layout.addLayout(footer_row)

        root.addWidget(setting_card)
        root.addStretch(1)

        # 恢复设置
        saved_dir = app_config.get("output_dir", "")
        if saved_dir:
            self.radio_custom_dir.setChecked(True)
            self.edit_output_dir.setText(saved_dir)
        else:
            self.radio_source_dir.setChecked(True)
        conflict = app_config.get("conflict", "rename")
        for idx in range(self.combo_conflict.count()):
            if self.combo_conflict.itemData(idx) == conflict:
                self.combo_conflict.setCurrentIndex(idx)
                break

    def _wrap_field(self, title_key: str, widget) -> QWidget:
        box = QWidget()
        layout = QVBoxLayout(box)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        label = CaptionLabel(t(title_key))
        set_muted(label, 0.55)
        self._field_labels.append((label, title_key))
        layout.addWidget(label)
        layout.addWidget(widget)
        return box

    def _connect_signals(self) -> None:
        self.pivot.currentItemChanged.connect(self._on_pivot_changed)
        self.drop_card.filesDropped.connect(self.add_paths)
        self.drop_card.clicked.connect(self._choose_files)
        self.btn_add.clicked.connect(self._choose_files)
        self.btn_add_dir.clicked.connect(self._choose_folder)
        self.btn_clear.clicked.connect(self._clear_files)
        self.btn_browse.clicked.connect(self._choose_output_dir)
        self.btn_start.clicked.connect(self._start_conversion)
        self.combo_format.currentIndexChanged.connect(self._rebuild_presets)
        self.combo_resolution.currentIndexChanged.connect(self._on_resolution_changed)
        self.radio_source_dir.toggled.connect(self._update_dir_editable)

        self.queue.task_updated.connect(self._on_task_updated)
        self.queue.task_removed.connect(self._on_task_removed)

    # ================================================================ 分类切换

    def _on_pivot_changed(self, key: str) -> None:
        cat = {k: c for k, c, _ in _CATEGORIES}.get(key)
        if cat:
            self._set_category(cat)

    def _set_category(self, cat: MediaCategory) -> None:
        self.category = cat
        app_config.set("last_category", cat.value)
        key = cat.value
        if self.pivot.currentItem() != key:
            self._building = True
            self.pivot.setCurrentItem(key)
            self._building = False
        self._rebuild_format_combo()
        self._refresh_table()
        self._update_summary()
        self._update_mode_label()

    def _update_mode_label(self) -> None:
        """更新当前模式指示器的图标、文字与颜色。"""
        # 图标映射
        icon_map = {
            MediaCategory.VIDEO: FIF.VIDEO,
            MediaCategory.AUDIO: FIF.MUSIC,
            MediaCategory.IMAGE: FIF.PHOTO,
        }
        cat_key = f"convert.category.{self.category.value}"
        self.mode_name_label.setText(t(cat_key))
        color = muted_color(alpha_light=230, alpha_dark=240)
        self.mode_name_label.setStyleSheet(
            f"color: rgba({color.red()},{color.green()},{color.blue()},{color.alpha()});"
        )
        icon = icon_map.get(self.category, FIF.VIDEO)
        self.mode_icon_label.setPixmap(icon.icon(color).pixmap(24, 24))

    # ================================================================ 格式 / 预设

    def _rebuild_format_combo(self) -> None:
        self._building = True
        self.combo_format.blockSignals(True)
        try:
            self.combo_format.clear()
            targets = targets_for_category(self.category)
            for target in targets:
                self.combo_format.addItem(target.label, userData=target.id)
        finally:
            self.combo_format.blockSignals(False)
        self._building = False
        self._rebuild_presets()

    def _rebuild_presets(self) -> None:
        if self._building:
            return
        target = self._current_target()
        if target is None:
            return
        self.combo_preset.blockSignals(True)
        try:
            self.combo_preset.clear()
            for preset in target.presets:
                self.combo_preset.addItem(preset.name, userData=preset.id)
        finally:
            self.combo_preset.blockSignals(False)
        self._update_dir_editable()
        is_video_out = self.category == MediaCategory.VIDEO and target.kind == "video"
        # GIF 帧率由质量预设固定（调色板双步流程），不再显示独立帧率选项
        is_gif = target.id == "gif"
        show_res = is_video_out and not is_gif
        self.resolution_field.setVisible(show_res)
        self.fps_field.setVisible(show_res)
        # 自定义分辨率输入行仅在分辨率字段可见且选中"自定义"时显示
        is_custom = self.combo_resolution.currentData() == "custom"
        self.custom_res_row.setVisible(show_res and is_custom)

    def _on_resolution_changed(self) -> None:
        """分辨率下拉变化时切换自定义输入框的显示。"""
        target = self._current_target()
        is_video_out = (
            target is not None
            and self.category == MediaCategory.VIDEO
            and target.kind == "video"
            and target.id != "gif"
        )
        is_custom = self.combo_resolution.currentData() == "custom"
        self.custom_res_row.setVisible(is_video_out and is_custom)

    def _current_target(self):
        format_id = self.combo_format.currentData()
        if not format_id:
            return None
        from app.core.presets import get_target
        return get_target(format_id, self.category)

    def _update_dir_editable(self) -> None:
        custom = self.radio_custom_dir.isChecked()
        self.edit_output_dir.setEnabled(custom)
        self.btn_browse.setEnabled(custom)

    # ================================================================ 文件添加

    def _choose_files(self) -> None:
        paths = self.drop_card.choose_files(t(_DIALOG_FILTER[self.category]))
        if paths:
            self.add_paths(paths)

    def _choose_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, t("convert.dialog.choose_folder"))
        if folder:
            self.add_paths([folder])

    def _choose_output_dir(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, t("convert.dialog.choose_output_folder"))
        if folder:
            self.radio_custom_dir.setChecked(True)
            self.edit_output_dir.setText(os.path.normpath(folder))

    def add_paths(self, paths: List[str]) -> None:
        """处理拖入 / 选择的文件或文件夹，后台扫描后按分类归组。"""
        if not paths:
            return
        worker = FileScanWorker(paths)
        worker.signals.scanned.connect(self._on_paths_scanned)
        self.probe_pool.start(worker)

    def _on_paths_scanned(self, collected: list, unsupported: list) -> None:
        """FileScanWorker 完成后的回调：在 UI 线程执行数据入列与刷新。"""
        if not collected:
            if unsupported:
                self._info(
                    t("convert.info.no_media.title"),
                    t("convert.info.no_media.content",
                      items=", ".join(unsupported[:5])),
                    kind="warning",
                )
            return

        # 智能切换：根据拖入文件的类型自动切换到对应分类
        cats = [c for _p, c, _s in collected]
        cat_counts: Dict[MediaCategory, int] = {}
        for c in cats:
            cat_counts[c] = cat_counts.get(c, 0) + 1

        if cat_counts:
            # 找占比最高的分类
            total = len(cats)
            dominant_cat, dominant_count = max(cat_counts.items(), key=lambda x: x[1])
            is_pure = dominant_count == total  # 所有文件同一分类
            is_majority = dominant_count >= total * 0.7  # 70% 以上属于同一类

            if dominant_cat != self.category:
                # 纯净集合：始终自动切换；多数集合：仅在当前分类为空时切换
                if is_pure or (is_majority and not self._files[self.category]):
                    old_cat = self.category
                    self._set_category(dominant_cat)
                    # 给用户明确的自动切换反馈
                    if old_cat is not None:
                        self._info(
                            t("convert.info.auto_switched.title"),
                            t(
                                "convert.info.auto_switched.content",
                                category=t(f"convert.category.{dominant_cat.value}"),
                            ),
                            kind="info",
                            duration=2200,
                        )

        # 所有受支持文件按各自分类入列（切换分类页即可看到）
        added = 0
        added_current = 0
        for path, cat, size in collected:
            if any(e.path == path for e in self._files[cat]):
                continue
            self._files[cat].append(FileEntry(path=path, category=cat, size=size))
            added += 1
            if cat == self.category:
                added_current += 1
            self._probe_meta(path)

        self._refresh_table()
        self._update_summary()

        other_count = added - added_current
        if added_current:
            if other_count:
                content = t("convert.info.added.other", count=added, other=other_count)
            else:
                content = t("convert.info.added.content", count=added)
            self._info(
                t("convert.info.added.title"),
                content,
                kind="success", duration=2200,
            )
        elif other_count:
            self._info(
                t("convert.info.other_category.title"),
                t("convert.info.other_category.content",
                  count=other_count, category=self.category.value),
                kind="info", duration=3000,
            )
        if unsupported:
            self._info(
                t("convert.info.unsupported.title"),
                t("convert.info.unsupported.content",
                  count=len(unsupported), items=", ".join(unsupported[:3])),
                kind="warning",
            )

    def _probe_meta(self, path: str) -> None:
        if not ffmpeg_manager.available:
            return
        worker = MetaProbeWorker(path)
        worker.signals.ready.connect(self._on_meta_ready)
        self.probe_pool.start(worker)

    def _on_meta_ready(self, path: str, _duration: float, text: str) -> None:
        for entry in self._files.get(self.category, []):
            if entry.path == path:
                entry.meta = text
        self._set_meta_cell(path, text)

    def _clear_files(self) -> None:
        kept = [e for e in self._files[self.category] if e.tid is not None]
        if len(kept) == len(self._files[self.category]) and kept:
            self._info(t("convert.info.cannot_clear.title"),
                       t("convert.info.cannot_clear.content"), kind="info")
            return
        self._files[self.category] = kept
        self._refresh_table()
        self._update_summary()

    # ================================================================ 表格渲染

    def _refresh_table(self) -> None:
        entries = self._files[self.category]
        self.table.setUpdatesEnabled(False)
        self.table.blockSignals(True)
        try:
            self.table.setRowCount(len(entries))
            for row, entry in enumerate(entries):
                name_item = QTableWidgetItem(os.path.basename(entry.path))
                name_item.setToolTip(entry.path)
                name_item.setData(Qt.UserRole, entry.path)
                ext_item = QTableWidgetItem(entry.category.value.upper() +
                                            (" · " + os.path.splitext(entry.path)[1][1:].upper()
                                             if os.path.splitext(entry.path)[1] else ""))
                size_item = QTableWidgetItem(format_file_size(entry.size))
                meta_item = QTableWidgetItem(entry.meta or "—")
                for col, item in enumerate((name_item, ext_item, size_item, meta_item)):
                    self.table.setItem(row, col, item)

                cell = _StatusCell()
                if entry.tid:
                    task = self.queue.get(entry.tid)
                    if task:
                        cell.set_state(task.status, task.progress)
                        if task.error:
                            cell.show_error_tip(task.error)
                self.table.setCellWidget(row, 4, cell)
                self.table.setCellWidget(row, 5, self._build_action_cell(entry))

            self.table.resizeRowsToContents()
        finally:
            self.table.blockSignals(False)
            self.table.setUpdatesEnabled(True)
            self.table.viewport().update()

    def _build_action_cell(self, entry: FileEntry) -> QWidget:
        box = QWidget()
        layout = QHBoxLayout(box)
        layout.setContentsMargins(4, 0, 4, 0)
        layout.setSpacing(2)

        btn_open = TransparentToolButton(FIF.FOLDER)
        btn_open.setToolTip(t("convert.tip.open_output_dir"))
        btn_open.setVisible(False)
        btn_open.clicked.connect(lambda: self._open_output_dir(entry))

        btn_remove = TransparentToolButton(FIF.DELETE)
        btn_remove.setToolTip(t("convert.tip.remove"))
        btn_remove.clicked.connect(lambda: self._remove_entry(entry))

        if entry.tid:
            task = self.queue.get(entry.tid)
            if task and task.status == TaskStatus.COMPLETED and task.output_path:
                btn_open.setVisible(True)

        layout.addWidget(btn_open)
        layout.addWidget(btn_remove)
        layout.addStretch(1)
        return box

    def _remove_entry(self, entry: FileEntry) -> None:
        if entry.tid and self.queue.is_running(entry.tid):
            self._info(t("convert.info.task_running.title"),
                       t("convert.info.task_running.content"), kind="warning")
            return
        if entry.tid:
            self.queue.remove(entry.tid)
        if entry in self._files[entry.category]:
            self._files[entry.category].remove(entry)
        self._refresh_table()
        self._update_summary()

    def _open_output_dir(self, entry: FileEntry) -> None:
        if not entry.tid:
            return
        task = self.queue.get(entry.tid)
        if task and task.output_path:
            QDesktopServices.openUrl(QUrl.fromLocalFile(
                os.path.dirname(task.output_path) or task.output_dir))

    def _row_for_path(self, path: str) -> int:
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and item.data(Qt.UserRole) == path:
                return row
        return -1

    def _set_meta_cell(self, path: str, text: str) -> None:
        row = self._row_for_path(path)
        if row >= 0:
            self.table.item(row, 3).setText(text or "—")

    # ================================================================ 发起转换

    def _start_conversion(self) -> None:
        if not ffmpeg_manager.available:
            self._info(
                t("convert.info.no_ffmpeg.title"),
                t("convert.info.no_ffmpeg.content"),
                kind="error",
                duration=4000,
            )
            self.go_settings.emit()
            return

        target = self._current_target()
        if target is None:
            self._info(t("convert.info.no_format.title"), "", kind="warning")
            return

        entries = [e for e in self._files[self.category] if e.tid is None]
        if not entries:
            self._info(t("convert.info.no_new_files.title"),
                       t("convert.info.no_new_files.content"), kind="info")
            return

        # 输出目录
        if self.radio_custom_dir.isChecked():
            out_dir = self.edit_output_dir.text().strip()
            if not out_dir or not os.path.isdir(out_dir):
                self._info(t("convert.info.invalid_dir.title"),
                           t("convert.info.invalid_dir.content"), kind="warning")
                return
        else:
            out_dir = ""

        conflict = self.combo_conflict.currentData() or "rename"
        resolution = self.combo_resolution.currentData() or "source"
        # 自定义分辨率：组合为 "WxH" 供 converter 解析
        if resolution == "custom":
            w_text = self.edit_res_width.text().strip()
            h_text = self.edit_res_height.text().strip()
            if not w_text or not h_text or not w_text.isdigit() or not h_text.isdigit():
                self._info(
                    t("convert.info.invalid_resolution.title"),
                    t("convert.info.invalid_resolution.content"),
                    kind="warning",
                )
                return
            w_val, h_val = int(w_text), int(h_text)
            if w_val < 16 or h_val < 16 or w_val > 8192 or h_val > 8192:
                self._info(
                    t("convert.info.invalid_resolution.title"),
                    t("convert.info.invalid_resolution.range"),
                    kind="warning",
                )
                return
            resolution = f"{w_val}x{h_val}"
        fps = self.combo_fps.currentData() or "source"
        preset_id = self.combo_preset.currentData() or target.presets[0].id

        # 持久化偏好
        app_config.set("output_dir", out_dir)
        app_config.set("conflict", conflict)

        tasks: List[ConversionTask] = []
        for entry in entries:
            task_out_dir = out_dir or os.path.dirname(entry.path)
            tasks.append(
                ConversionTask(
                    input_path=entry.path,
                    output_dir=task_out_dir,
                    target_format=target.id,
                    preset_id=preset_id,
                    category=entry.category,
                    resolution=resolution,
                    fps=fps,
                    conflict=conflict,
                    size=entry.size,
                )
            )

        ids = self.queue.enqueue_many(tasks)
        for entry, tid in zip(entries, ids):
            entry.tid = tid

        self._refresh_table()
        self._update_summary()
        self._info(
            t("convert.info.enqueued.title"),
            t("convert.info.enqueued.content", count=len(tasks)),
            kind="success",
            duration=2600,
        )

    # ================================================================ 队列信号

    def _on_task_updated(self, tid: str) -> None:
        task = self.queue.get(tid)
        if not task:
            return
        for entry in self._files[self.category]:
            if entry.tid == tid:
                row = self._row_for_path(entry.path)
                if row >= 0:
                    cell = self.table.cellWidget(row, 4)
                    if isinstance(cell, _StatusCell):
                        cell.set_state(task.status, task.progress)
                        if task.error:
                            cell.show_error_tip(task.error)
                    self.table.setCellWidget(row, 5, self._build_action_cell(entry))
                break

    def _on_task_removed(self, tid: str) -> None:
        for entry in self._files[self.category]:
            if entry.tid == tid:
                entry.tid = None
                self._refresh_table()
                break
        self._update_summary()

    # ================================================================ 杂项

    def _update_summary(self) -> None:
        entries = self._files[self.category]
        enqueued = sum(1 for e in entries if e.tid is not None)
        self.count_label.setText(t("convert.file_list.count", count=len(entries)))
        if entries:
            if enqueued:
                self.summary_label.setText(
                    t("convert.summary.enqueued",
                      total=len(entries), enqueued=enqueued)
                )
            else:
                self.summary_label.setText(
                    t("convert.summary.total", count=len(entries))
                )
        else:
            self.summary_label.setText(t("convert.summary.ready"))

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
