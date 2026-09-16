# -*- coding: utf-8 -*-
"""主窗口：FluentWindow 导航框架，串联转换 / 队列 / 设置 / 帮助页面。"""
from __future__ import annotations

from PySide6.QtCore import Qt, QThread, QTimer, QRectF, Signal
from PySide6.QtGui import QCloseEvent, QColor, QIcon, QPainter
from PySide6.QtWidgets import QApplication, QDialog, QVBoxLayout

from qfluentwidgets import (
    BodyLabel, CaptionLabel, FluentIcon as FIF, FluentWindow,
    IndeterminateProgressBar, MessageBox, MessageBoxBase,
    NavigationItemPosition, PrimaryPushButton, PushButton,
    StrongBodyLabel, isDarkTheme, qconfig, themeColor,
)

from app import APP_DISPLAY
from app.config import app_config
from app.core.ffmpeg import ffmpeg_manager
from app.core.hardware import hw_manager
from app.core.updater import ffmpeg_updater
from app.i18n import i18n, t
from app.ui.icons import prism_icon, prism_pixmap

from .views.convert_view import ConvertView
from .views.help_view import HelpView
from .views.queue_view import QueueView
from .views.settings_view import SettingsView


# ------------------------------------------------------------ 导航栏图标放大
# qfluentwidgets 在 NavigationPushButton.paintEvent 中硬编码了 16x16 的图标绘制矩形，
# 通过 monkey-patch 替换 paintEvent 以绘制更大图标，并相应调整文本起始位置。
_NAV_ICON_SIZE = 20          # 导航项图标像素尺寸（原 16）
_NAV_ITEM_HEIGHT = 44        # 导航项高度（原 36）


def _patch_navigation_icon() -> None:
    """一次性扩大 FluentWindow 导航栏图标尺寸。"""
    try:
        from qfluentwidgets.components.navigation.navigation_widget import (
            NavigationPushButton,
        )
        from qfluentwidgets.common.icon import drawIcon
        from qfluentwidgets.common.config import isDarkTheme
        from qfluentwidgets.common.color import autoFallbackThemeColor
    except ImportError:
        return

    if getattr(NavigationPushButton, "_prism_patched", False):
        return

    def _patched_paintEvent(self, e) -> None:  # noqa: N802
        from PySide6.QtCore import QRect, QRectF, QPoint
        from PySide6.QtGui import QColor, QCursor

        painter = QPainter(self)
        painter.setRenderHints(
            QPainter.Antialiasing
            | QPainter.TextAntialiasing
            | QPainter.SmoothPixmapTransform
        )
        painter.setPen(Qt.NoPen)

        if self.isPressed:
            painter.setOpacity(0.7)
        if not self.isEnabled():
            painter.setOpacity(0.4)

        c = 255 if isDarkTheme() else 0
        m = self._margins()
        pl, pr = m.left(), m.right()
        globalRect = QRect(self.mapToGlobal(QPoint()), self.size())

        if self._canDrawIndicator():
            painter.setBrush(QColor(c, c, c, 6 if self.isEnter else 10))
            painter.drawRoundedRect(self.rect(), 5, 5)
            # 指示条颜色（主题感知）+ 垂直居中
            painter.setBrush(autoFallbackThemeColor(
                self.lightIndicatorColor, self.darkIndicatorColor))
            ind_h = 16
            ind_y = (self.height() - ind_h) / 2
            painter.drawRoundedRect(
                QRectF(m.left(), ind_y, 3, ind_h), 1.5, 1.5)
        elif (
            (self.isEnter and globalRect.contains(QCursor.pos()))
            or self.isAboutSelected
        ) and self.isEnabled():
            painter.setBrush(QColor(c, c, c, 6 if self.isAboutSelected else 10))
            painter.drawRoundedRect(self.rect(), 5, 5)

        # 图标绘制：保持原 12px 起始边距，按新尺寸垂直居中
        icon_size = _NAV_ICON_SIZE
        icon_x = 12.0 + pl
        icon_y = (self.height() - icon_size) / 2
        drawIcon(self._icon, painter,
                 QRectF(icon_x, icon_y, icon_size, icon_size))

        if self.isCompacted:
            return

        painter.setFont(self.font())
        painter.setPen(self.textColor())
        # 文本起始位置随之右移，避免与图标重叠
        has_icon = not self.icon().isNull()
        left = (icon_x + icon_size + 12) if has_icon else (pl + 16)
        painter.drawText(
            QRectF(left, 0, self.width() - 13 - left - pr, self.height()),
            Qt.AlignVCenter, self.text(),
        )

    NavigationPushButton.paintEvent = _patched_paintEvent
    NavigationPushButton._prism_patched = True

    # 同时放大导航项高度，让图标周围有更宽松的呼吸空间
    def _patched_set_compacted(self, is_compacted: bool) -> None:  # noqa: N802
        if is_compacted:
            self.setFixedSize(40, _NAV_ITEM_HEIGHT)
        else:
            self.setFixedSize(self.EXPAND_WIDTH, _NAV_ITEM_HEIGHT)

    NavigationPushButton.setCompacted = _patched_set_compacted


_patch_navigation_icon()


class _CloseChoiceBox(MessageBoxBase):
    """有任务进行中且已有暂存更新时的三选一对话框。"""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.action = "return"   # wait / exit / return

        title = StrongBodyLabel(t("close.update_ready.title"))
        content = BodyLabel(t("close.update_ready.desc"))
        content.setWordWrap(True)
        self.viewLayout.addWidget(title)
        self.viewLayout.addWidget(content)

        self.yesButton.hide()
        self.cancelButton.setText(t("close.update_ready.btn_return"))
        self.btn_exit = PushButton(FIF.CANCEL, t("close.update_ready.btn_exit"))
        self.btn_wait = PrimaryPushButton(FIF.ACCEPT, t("close.update_ready.btn_wait"))
        # 从左到右：立即退出 / 等待并安装 / 返回
        self.buttonLayout.insertWidget(0, self.btn_exit)
        self.buttonLayout.insertWidget(1, self.btn_wait)

        self.btn_wait.clicked.connect(self._choose_wait)
        self.btn_exit.clicked.connect(self._choose_exit)
        self.widget.setMinimumWidth(460)

    def _choose_wait(self) -> None:
        self.action = "wait"
        self.accept()

    def _choose_exit(self) -> None:
        self.action = "exit"
        self.accept()


class _ApplyStagedThread(QThread):
    """退出阶段执行暂存更新安装（避免阻塞 UI 线程）。"""

    progress = Signal(int, str)
    done = Signal(bool, str)

    def run(self) -> None:
        ok, msg = ffmpeg_updater.apply_staged(
            progress_cb=lambda pct, text: self.progress.emit(pct, text)
        )
        self.done.emit(ok, msg)


class _ClosingDialog(QDialog):
    """退出过渡窗口：等待下载 / 转换任务 / 安装更新。"""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowFlags(
            Qt.Dialog | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
        )
        self.setModal(False)
        self.setFixedSize(380, 150)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(14)
        self.title = StrongBodyLabel(t("close.preparing.title"))
        self.caption = CaptionLabel(t("close.preparing.caption"))
        self.caption.setWordWrap(True)
        self.bar = IndeterminateProgressBar()
        self.bar.setFixedHeight(4)
        self.bar.start()
        layout.addWidget(self.title)
        layout.addWidget(self.caption)
        layout.addStretch(1)
        layout.addWidget(self.bar)

    def set_text(self, title: str, caption: str) -> None:
        self.title.setText(title)
        self.caption.setText(caption)


class MainWindow(FluentWindow):
    def __init__(self, queue) -> None:
        super().__init__()
        self.queue = queue
        self._closing = False
        self._apply_thread: _ApplyStagedThread | None = None

        self.convert_view = ConvertView(queue)
        self.queue_view = QueueView(queue)
        self.settings_view = SettingsView(queue)
        self.help_view = HelpView()

        self._init_navigation()
        self._init_window()
        self._connect_cross_navigation()

        # 启动后的硬件探测与 FFmpeg 自检 / 更新检查（延迟一点，等界面渲染）
        QTimer.singleShot(500, self._startup_check)

    def _init_navigation(self) -> None:
        self.addSubInterface(
            self.convert_view, FIF.VIDEO, t("nav.convert"),
            position=NavigationItemPosition.TOP,
        )
        self.addSubInterface(
            self.queue_view, FIF.TILES, t("nav.queue"),
            position=NavigationItemPosition.TOP,
        )
        self.addSubInterface(
            self.settings_view, FIF.SETTING, t("nav.settings"),
            position=NavigationItemPosition.BOTTOM,
        )
        self.addSubInterface(
            self.help_view, FIF.HELP, t("nav.help"),
            position=NavigationItemPosition.BOTTOM,
        )

    def _init_window(self) -> None:
        self._update_window_title()
        self.resize(1180, 760)
        self.setMinimumSize(980, 640)
        self._enlarge_titlebar_icon()
        self._refresh_window_icon()
        # 主题色 / 深浅色切换时重绘窗口图标
        qconfig.themeColorChanged.connect(self._refresh_window_icon)
        qconfig.themeChanged.connect(self._refresh_window_icon)
        # 语言切换时重新翻译全部界面
        i18n.languageChanged.connect(self._retranslate_ui)

    def _enlarge_titlebar_icon(self) -> None:
        """放大标题栏应用图标。

        qfluentwidgets 的 FluentTitleBar 将 iconLabel 硬编码为 18x18，
        这里扩到 28x28，并在窗口图标变化时以 28px 重新渲染。
        连接顺序保证本槽在库自身的 18px 渲染之后执行、覆盖其结果。
        """
        label = getattr(self.titleBar, "iconLabel", None)
        if label is None:
            return
        size = 28
        label.setFixedSize(size, size)

        def _apply(icon: QIcon) -> None:
            label.setPixmap(icon.pixmap(size, size))

        self.windowIconChanged.connect(_apply)

    def _update_window_title(self) -> None:
        """根据当前语言生成窗口标题：非英文/英文US → 本地化名称 - Prism。"""
        code = i18n.current()
        if code in ("en", "en_US"):
            self.setWindowTitle("Prism")
        else:
            self.setWindowTitle(f"{t('app.name')} - Prism")

    def _retranslate_ui(self, _code: str = "") -> None:
        """语言切换后更新窗口标题、导航标签与各子页面文案。"""
        self._update_window_title()
        for obj_name, key in (
            ("convertView", "nav.convert"),
            ("queueView", "nav.queue"),
            ("settingsView", "nav.settings"),
            ("helpView", "nav.help"),
        ):
            item = self.navigationInterface.widget(obj_name)
            if item is not None and hasattr(item, "setText"):
                item.setText(t(key))
        # 通知各子页面重新翻译
        for view in (self.convert_view, self.queue_view,
                     self.settings_view, self.help_view):
            method = getattr(view, "retranslate_ui", None)
            if callable(method):
                method()

    def _refresh_window_icon(self, *_args) -> None:
        """窗口图标：使用 Prism.ico 中固定较大尺寸渲染，避免系统自动选小图。"""
        from PySide6.QtGui import QIcon
        # 直接取较大尺寸 pixmap 再包装为 QIcon，避免系统自动选择 16x16
        pm = prism_pixmap(64)
        if not pm.isNull():
            self.setWindowIcon(QIcon(pm))
        else:
            icon = prism_icon()
            if not icon.isNull():
                self.setWindowIcon(icon)

    def _connect_cross_navigation(self) -> None:
        self.convert_view.go_settings.connect(
            lambda: self.switchTo(self.settings_view)
        )
        self.queue_view.go_convert.connect(
            lambda: self.switchTo(self.convert_view)
        )

    def _startup_check(self) -> None:
        # 系统 API 硬件探测（后台线程，幂等）
        hw_manager.start_probe()

        if not ffmpeg_manager.available:
            box = MessageBox(
                t("convert.info.no_ffmpeg.title"),
                t("convert.info.no_ffmpeg.content"),
                self,
            )
            box.yesButton.setText(t("common.download"))
            box.cancelButton.setText(t("common.later"))
            if box.exec():
                self.switchTo(self.settings_view)
                self.settings_view.download()
        elif app_config.get("auto_check_update", True):
            # 静默比对：发现新版本由设置页自动后台下载暂存，不弹窗
            self.settings_view.check_update(silent=True)

    # ================================================================ 关闭流程

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        if self._closing:
            event.ignore()
            return

        active = self.queue.has_active()
        staged = ffmpeg_updater.has_staged()

        cancel_tasks = False
        install_after_close = staged

        if active and staged:
            box = _CloseChoiceBox(self)
            if not box.exec():
                event.ignore()
                return
            if box.action == "wait":
                cancel_tasks = False
                install_after_close = True
            else:
                cancel_tasks = True
                install_after_close = False   # 暂存保留，下次退出再装
        elif active:
            box = MessageBox(
                t("close.confirm_exit.title"),
                t("close.confirm_exit.desc"),
                self,
            )
            box.yesButton.setText(t("close.confirm_exit.btn_exit"))
            box.cancelButton.setText(t("close.confirm_exit.btn_continue"))
            if not box.exec():
                event.ignore()
                return
            cancel_tasks = True
            install_after_close = staged

        # 转入异步收尾：隐藏主窗口，显示退出过渡对话框
        event.ignore()
        self.hide()
        self._begin_close_sequence(cancel_tasks, install_after_close)

    def _begin_close_sequence(self, cancel_tasks: bool, install: bool) -> None:
        self._closing = True
        self._close_cancel = cancel_tasks
        self._close_install = install
        self._close_wait = not cancel_tasks

        self._close_dlg = _ClosingDialog(self)
        self._center_dialog(self._close_dlg)
        self._close_dlg.show()
        QTimer.singleShot(150, self._close_tick)

    @staticmethod
    def _center_dialog(dialog: QDialog) -> None:
        screen = QApplication.primaryScreen()
        if screen is None:
            return
        area = screen.availableGeometry()
        dialog.move(
            area.center().x() - dialog.width() // 2,
            area.center().y() - dialog.height() // 2,
        )

    def _close_tick(self) -> None:
        # 1) 后台更新下载 / 检查必须先结束（QThread 不能在运行时销毁）
        if ffmpeg_updater.busy:
            self._close_dlg.set_text(
                t("close.preparing.title"),
                t("close.downloading.caption"),
            )
            QTimer.singleShot(250, self._close_tick)
            return

        # 2) 等待模式：让队列把等待中 / 转换中的任务全部跑完，不取消
        if self._close_wait and self.queue.has_active():
            self.queue.set_paused(False)
            running = self.queue.running_count()
            waiting = self.queue.waiting_count()
            self._close_dlg.set_text(
                t("close.waiting_tasks.title"),
                t("close.waiting_tasks.caption",
                  running=running, waiting=waiting),
            )
            QTimer.singleShot(400, self._close_tick)
            return

        # 3) 收敛后台线程与任务线程
        self.settings_view.shutdown()
        if self._close_cancel:
            self.queue.shutdown()          # 取消全部并 waitForDone
        else:
            self.queue.pool.waitForDone(3000)

        # 4) 安装已暂存的更新
        if self._close_install and ffmpeg_updater.has_staged():
            self._close_dlg.set_text(
                t("close.installing.title"),
                t("close.installing.caption"),
            )
            self._apply_thread = _ApplyStagedThread()
            self._apply_thread.progress.connect(
                lambda _pct, text: self._close_dlg.caption.setText(text)
            )
            self._apply_thread.done.connect(self._on_apply_done)
            self._apply_thread.start()
            return

        self._finish_close()

    def _on_apply_done(self, ok: bool, message: str) -> None:
        if self._apply_thread is not None:
            self._apply_thread.wait(2000)
            self._apply_thread = None
        if ok:
            self._close_dlg.set_text(
                t("close.install_done.title"),
                t("close.install_done.caption"),
            )
        else:
            self._close_dlg.set_text(
                t("close.not_installed.title"),
                t("close.not_installed.caption", message=message),
            )
        QTimer.singleShot(900, self._finish_close)

    def _finish_close(self) -> None:
        try:
            self._close_dlg.close()
        except Exception:
            pass
        QApplication.quit()
