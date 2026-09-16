# -*- coding: utf-8 -*-
"""任务队列页面：全局任务总览、暂停调度、取消 / 重试 / 清空、并发数设置。"""
from __future__ import annotations

import os

from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QHBoxLayout, QHeaderView, QLabel, QTableWidgetItem, QVBoxLayout, QWidget,
)

from qfluentwidgets import (
    BodyLabel, CaptionLabel, CardWidget, FluentIcon as FIF, PrimaryPushButton,
    PushButton, qconfig, SingleDirectionScrollArea, SpinBox, StrongBodyLabel,
    TableWidget, TitleLabel, TransparentToolButton,
)

from app.core.models import FINISHED_STATUSES, TaskStatus
from app.core.presets import format_file_size, get_target
from app.i18n import t

from ..theme_aware import muted_color
from .convert_view import _StatusCell


class QueueView(QWidget):
    go_convert = Signal()

    def __init__(self, queue, parent=None) -> None:
        super().__init__(parent)
        self.queue = queue
        self.setObjectName("queueView")
        self._build_ui()

        queue.task_added.connect(lambda _tid: self._rebuild())
        queue.task_removed.connect(lambda _tid: self._rebuild())
        queue.task_finished.connect(lambda _tid, _s: self._rebuild())
        queue.queue_changed.connect(self._refresh_summary)
        queue.paused_changed.connect(self._refresh_pause_button)
        queue.task_updated.connect(self._update_progress_row)
        qconfig.themeChanged.connect(self._on_theme_changed)

        self._rebuild()

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

        self.title = TitleLabel(t("queue.title"))
        root.addWidget(self.title)
        self.subtitle = BodyLabel(t("queue.subtitle"))
        root.addWidget(self.subtitle)

        card = CardWidget()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 20)
        layout.setSpacing(12)

        # 工具栏
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)
        self.btn_pause = PushButton(FIF.PAUSE, t("queue.btn.pause"))
        self.btn_cancel_all = PushButton(FIF.CANCEL, t("queue.btn.cancel_all"))
        self.btn_retry = PushButton(FIF.SYNC, t("queue.btn.retry_failed"))
        self.btn_clear = PushButton(FIF.DELETE, t("queue.btn_clear_finished"))
        for btn in (self.btn_pause, self.btn_cancel_all, self.btn_retry, self.btn_clear):
            toolbar.addWidget(btn)
        toolbar.addStretch(1)
        self.concurrency_label = CaptionLabel(t("queue.concurrency"))
        toolbar.addWidget(self.concurrency_label)
        self.spin_concurrency = SpinBox()
        self.spin_concurrency.setRange(1, 8)
        self.spin_concurrency.setValue(int(self.queue.pool.maxThreadCount()))
        self.spin_concurrency.setFixedWidth(120)
        toolbar.addWidget(self.spin_concurrency)
        layout.addLayout(toolbar)

        self.summary_label = CaptionLabel("")
        layout.addWidget(self.summary_label)

        self.table = TableWidget()
        self.table.setColumnCount(6)
        self._table_header_keys = [
            "convert.column.filename", "convert.column.target_format",
            "convert.column.size", "convert.column.output_dir",
            "convert.column.status_progress", "convert.column.action",
        ]
        self.table.setHorizontalHeaderLabels(
            [t(k) for k in self._table_header_keys]
        )
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(TableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(TableWidget.SelectRows)
        self.table.setSelectionMode(TableWidget.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setBorderVisible(False)
        self.table.setShowGrid(False)
        self.table.setMinimumHeight(380)
        header = self.table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        for col in (1, 2, 4, 5):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().setDefaultSectionSize(48)
        layout.addWidget(self.table)

        # 空状态
        self.empty_widget = QWidget()
        empty_layout = QVBoxLayout(self.empty_widget)
        empty_layout.setAlignment(Qt.AlignCenter)
        empty_layout.setSpacing(10)
        self.empty_icon = QLabel()
        self.empty_icon.setAlignment(Qt.AlignCenter)
        self.empty_icon.setPixmap(FIF.TILES.icon(muted_color(90, 90)).pixmap(56, 56))
        icon = self.empty_icon
        self.empty_hint = StrongBodyLabel(t("queue.empty.hint"))
        self.empty_hint.setAlignment(Qt.AlignCenter)
        self.empty_desc = BodyLabel(t("queue.empty.desc"))
        self.empty_desc.setAlignment(Qt.AlignCenter)
        self.btn_go = PrimaryPushButton(FIF.VIDEO, t("queue.empty.go_add"))
        self.btn_go.setFixedWidth(160)
        empty_layout.addStretch(1)
        empty_layout.addWidget(icon)
        empty_layout.addWidget(self.empty_hint)
        empty_layout.addWidget(self.empty_desc)
        row = QHBoxLayout()
        row.addStretch(1)
        row.addWidget(self.btn_go)
        row.addStretch(1)
        empty_layout.addLayout(row)
        empty_layout.addStretch(1)
        layout.addWidget(self.empty_widget)

        root.addWidget(card)
        root.addStretch(1)

        self.btn_pause.clicked.connect(self._toggle_pause)
        self.btn_cancel_all.clicked.connect(self.queue.cancel_all)
        self.btn_retry.clicked.connect(self._retry_failed)
        self.btn_clear.clicked.connect(self._clear_finished)
        self.btn_go.clicked.connect(self.go_convert.emit)
        self.spin_concurrency.valueChanged.connect(self.queue.set_concurrency)

    def _on_theme_changed(self, _theme=None) -> None:
        """主题切换：刷新空状态图标与所有状态单元格颜色。"""
        self.empty_icon.setPixmap(FIF.TILES.icon(muted_color(90, 90)).pixmap(56, 56))
        for row in range(self.table.rowCount()):
            cell = self.table.cellWidget(row, 4)
            if isinstance(cell, _StatusCell):
                cell.restyle()

    def retranslate_ui(self) -> None:
        """语言切换后重新翻译本页面所有可见文案。"""
        self.title.setText(t("queue.title"))
        self.subtitle.setText(t("queue.subtitle"))
        self.btn_cancel_all.setText(t("queue.btn.cancel_all"))
        self.btn_retry.setText(t("queue.btn.retry_failed"))
        self.btn_clear.setText(t("queue.btn_clear_finished"))
        self.concurrency_label.setText(t("queue.concurrency"))
        self.table.setHorizontalHeaderLabels(
            [t(k) for k in self._table_header_keys]
        )
        self.empty_hint.setText(t("queue.empty.hint"))
        self.empty_desc.setText(t("queue.empty.desc"))
        self.btn_go.setText(t("queue.empty.go_add"))
        # 重建表格行以刷新操作按钮工具提示，并刷新汇总与暂停按钮文案
        self._rebuild()

    # ------------------------------------------------------------ 操作

    def _toggle_pause(self) -> None:
        self.queue.set_paused(not self.queue.paused)

    def _refresh_pause_button(self, paused: bool) -> None:
        if paused:
            self.btn_pause.setIcon(FIF.PLAY)
            self.btn_pause.setText(t("queue.btn.resume"))
        else:
            self.btn_pause.setIcon(FIF.PAUSE)
            self.btn_pause.setText(t("queue.btn.pause"))

    def _retry_failed(self) -> None:
        count = self.queue.retry_failed()
        if count == 0:
            pass

    def _clear_finished(self) -> None:
        self.queue.clear_finished()

    # ------------------------------------------------------------ 渲染

    def _rebuild(self) -> None:
        tasks = self.queue.tasks()
        self.table.setRowCount(len(tasks))
        for row, task in enumerate(tasks):
            name_item = QTableWidgetItem(task.name)
            name_item.setToolTip(task.input_path)
            name_item.setData(Qt.UserRole, task.tid)

            try:
                target = get_target(task.target_format, task.category)
                target_text = f"{target.ext.upper()} · {target.preset(task.preset_id).name}"
            except Exception:
                target_text = task.target_format.upper()
            target_item = QTableWidgetItem(target_text)
            size_item = QTableWidgetItem(format_file_size(task.size))
            dir_item = QTableWidgetItem(task.output_dir)
            dir_item.setToolTip(task.output_dir)

            self.table.setItem(row, 0, name_item)
            self.table.setItem(row, 1, target_item)
            self.table.setItem(row, 2, size_item)
            self.table.setItem(row, 3, dir_item)

            cell = _StatusCell()
            cell.set_state(task.status, task.progress)
            if task.error:
                cell.show_error_tip(task.error)
            self.table.setCellWidget(row, 4, cell)
            self.table.setCellWidget(row, 5, self._build_actions(task))

        has_tasks = bool(tasks)
        self.table.setVisible(has_tasks)
        self.empty_widget.setVisible(not has_tasks)
        if has_tasks:
            self.table.resizeRowsToContents()
        self._refresh_summary()
        self._refresh_pause_button(self.queue.paused)

    def _update_progress_row(self, tid: str) -> None:
        task = self.queue.get(tid)
        if not task:
            return
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and item.data(Qt.UserRole) == tid:
                cell = self.table.cellWidget(row, 4)
                if isinstance(cell, _StatusCell):
                    cell.set_state(task.status, task.progress)
                    if task.error:
                        cell.show_error_tip(task.error)
                break

    def _build_actions(self, task) -> QWidget:
        box = QWidget()
        layout = QHBoxLayout(box)
        layout.setContentsMargins(4, 0, 4, 0)
        layout.setSpacing(2)

        if task.status in (TaskStatus.RUNNING, TaskStatus.WAITING):
            btn_cancel = TransparentToolButton(FIF.CANCEL)
            btn_cancel.setToolTip(t("queue.tip.cancel_task"))
            btn_cancel.clicked.connect(lambda: self.queue.cancel(task.tid))
            layout.addWidget(btn_cancel)
        else:
            if task.status in (TaskStatus.FAILED, TaskStatus.CANCELED):
                btn_retry = TransparentToolButton(FIF.SYNC)
                btn_retry.setToolTip(t("queue.tip.retry"))
                btn_retry.clicked.connect(lambda: self.queue.retry(task.tid))
                layout.addWidget(btn_retry)
            if task.status == TaskStatus.COMPLETED and task.output_path:
                btn_open = TransparentToolButton(FIF.FOLDER)
                btn_open.setToolTip(t("queue.tip.open_output_dir"))
                btn_open.clicked.connect(
                    lambda: QDesktopServices.openUrl(
                        QUrl.fromLocalFile(os.path.dirname(task.output_path))
                    )
                )
                layout.addWidget(btn_open)
            btn_remove = TransparentToolButton(FIF.DELETE)
            btn_remove.setToolTip(t("queue.tip.remove_task"))
            btn_remove.clicked.connect(lambda: self.queue.remove(task.tid))
            layout.addWidget(btn_remove)

        layout.addStretch(1)
        return box

    def _refresh_summary(self) -> None:
        tasks = self.queue.tasks()
        running = sum(1 for t in tasks if t.status == TaskStatus.RUNNING)
        waiting = sum(1 for t in tasks if t.status == TaskStatus.WAITING)
        done = sum(1 for t in tasks if t.status == TaskStatus.COMPLETED)
        failed = sum(1 for t in tasks if t.status == TaskStatus.FAILED)
        parts = [t("queue.summary.total", count=len(tasks))]
        if running:
            parts.append(t("queue.summary.running", count=running))
        if waiting:
            parts.append(t("queue.summary.waiting", count=waiting))
        if done:
            parts.append(t("queue.summary.done", count=done))
        if failed:
            parts.append(t("queue.summary.failed", count=failed))
        self.summary_label.setText(t("queue.summary.separator").join(parts))
