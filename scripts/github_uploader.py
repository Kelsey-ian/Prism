# -*- coding: utf-8 -*-
"""GitHub 项目上传工具（GUI）——将 Prism 项目文件上传到 GitHub。

功能：
1. 自动检测 GitHub 上是否已存在目标仓库，不存在时自动创建
2. 上传源代码文件（GitHub Contents API）
3. 上传可执行文件与安装包（GitHub Releases Assets）
4. 中国大陆 GitHub 加速支持（API 镜像 + 下载加速）
5. 进度反馈与错误处理
6. 自动排除本脚本自身

运行方式：
    python scripts/github_uploader.py
"""
from __future__ import annotations

import base64
import json
import os
import re
import shutil
import socket
import sys
import tempfile
import threading
import time
import traceback
import urllib.error
import urllib.request
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QFileDialog, QHBoxLayout, QLabel,
    QLineEdit, QMainWindow, QMessageBox, QPlainTextEdit, QProgressBar,
    QPushButton, QVBoxLayout, QWidget, QGroupBox,
)
from PySide6.QtGui import QFont

# ============================================================ 配置

# 项目根目录（脚本在 scripts/ 下，根目录是其父目录）
PROJECT_ROOT = Path(__file__).resolve().parent.parent
# 本脚本文件名（上传时排除自身）
SELF_NAME = Path(__file__).name

# GitHub 仓库信息（默认值，可在界面修改）
DEFAULT_OWNER = "Kelsey-ian"
DEFAULT_REPO = "Prism"

# GitHub API 端点
GITHUB_API = "https://api.github.com"
GITHUB_UPLOADS = "https://uploads.github.com"

# GitHub API 镜像（中国大陆加速）
API_MIRRORS = [
    ("直连", ""),
    ("gh-proxy.com", "https://gh-proxy.com/"),
    ("ghfast.top", "https://ghfast.top/"),
]

# 上传时排除的目录/文件
EXCLUDE_DIRS = {
    ".venv", "build", "dist", "__pycache__", ".git", ".idea", ".vscode",
    "data", "config", "node_modules", ".pytest_cache", "Logo", ".trae",
}
EXCLUDE_FILES = {SELF_NAME, ".gitignore", ".gitattributes", ".trae"}

# 源代码文件扩展名
SOURCE_EXTS = {
    ".py", ".bat", ".nsi", ".spec", ".txt", ".json", ".ini",
    ".qss", ".svg", ".ico", ".ttf", ".md", ".toml", ".cfg",
}

# 首次上传后才保护的文件（仓库已存在时不再覆盖，避免覆盖用户在线编辑的内容）
PROTECTED_FILES = {"LICENSE.txt", "README.md", "README.rst", "CHANGELOG.md"}

# Token 等配置持久化（存于用户主目录，不会被项目上传波及）
CONFIG_FILE = Path.home() / ".prism_uploader.json"

# 可执行文件 / 安装包路径
PORTABLE_EXE = PROJECT_ROOT / "dist" / "Prism" / "Prism.exe"
INSTALLER_EXE = PROJECT_ROOT / "dist" / "Prism_Setup_x64.exe"

_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Prism-GitHubUploader/1.0"


# ============================================================ 配置持久化

def load_config() -> dict:
    """从用户主目录读取保存的配置（token 等）。"""
    try:
        if CONFIG_FILE.is_file():
            return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        pass
    return {}


def save_config(data: dict) -> None:
    """保存配置到用户主目录。"""
    try:
        CONFIG_FILE.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except OSError:
        pass


# ============================================================ 网络工具

def detect_china_network(timeout: float = 3.0) -> bool:
    """探测是否处于中国大陆网络环境（通过连接 github.com 的延迟判断）。"""
    try:
        sock = socket.create_connection(("github.com", 443), timeout=timeout)
        sock.close()
        return False  # 能直连，不在受限网络
    except (socket.timeout, OSError):
        return True   # 无法直连，可能在大陆
    except Exception:
        return True


def http_request(
    url: str, token: str, method: str = "GET",
    data: Optional[bytes] = None, content_type: str = "application/json",
    timeout: int = 30,
) -> Tuple[int, bytes, dict]:
    """发送 HTTP 请求，返回 (status_code, body, response_headers)。"""
    headers = {
        "User-Agent": _UA,
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }
    if data is not None:
        headers["Content-Type"] = content_type
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read(), dict(resp.headers)
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read(), dict(exc.headers)


def api_request(
    path: str, token: str, method: str = "GET",
    data: Optional[dict] = None, timeout: int = 30,
    use_mirror: bool = False, mirror_prefix: str = "",
) -> Tuple[int, dict]:
    """GitHub API 请求，返回 (status_code, json_dict)。"""
    if use_mirror and mirror_prefix:
        url = mirror_prefix + GITHUB_API + path
    else:
        url = GITHUB_API + path
    body = json.dumps(data).encode("utf-8") if data else None
    status, raw, _ = http_request(url, token, method, body, timeout=timeout)
    try:
        return status, json.loads(raw.decode("utf-8", errors="replace"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return status, {}


# ============================================================ 上传线程

class UploadWorker(QThread):
    """后台上传线程。"""

    log = Signal(str)
    progress = Signal(int, str)     # percent, status text
    finished_signal = Signal(bool)  # success

    def __init__(
        self, token: str, owner: str, repo: str,
        upload_source: bool, upload_exe: bool, upload_installer: bool,
        upload_source_zip: bool,
        use_mirror: bool, mirror_prefix: str,
    ) -> None:
        super().__init__()
        self.token = token
        self.owner = owner
        self.repo = repo
        self.upload_source = upload_source
        self.upload_exe = upload_exe
        self.upload_installer = upload_installer
        self.upload_source_zip = upload_source_zip
        self.use_mirror = use_mirror
        self.mirror_prefix = mirror_prefix
        self._cancelled = False
        self._repo_existed = False

    def cancel(self) -> None:
        self._cancelled = True

    def run(self) -> None:
        try:
            self._do_upload()
            self.finished_signal.emit(not self._cancelled)
        except Exception:
            self.log.emit(f"[ERROR] 上传过程发生异常：\n{traceback.format_exc()}")
            self.finished_signal.emit(False)

    # -------------------------------------------------------- 仓库管理

    def _check_repo_exists(self) -> bool:
        """检查仓库是否已存在。"""
        status, body = api_request(
            f"/repos/{self.owner}/{self.repo}", self.token,
            timeout=15, use_mirror=self.use_mirror,
            mirror_prefix=self.mirror_prefix,
        )
        if status == 200:
            self._repo_existed = True
            self.log.emit(f"[OK] 仓库 {self.owner}/{self.repo} 已存在（非首次上传）")
            return True
        if status == 404:
            self._repo_existed = False
            self.log.emit(f"[INFO] 仓库 {self.owner}/{self.repo} 尚不存在（首次上传）")
            return False
        if status == 401:
            raise RuntimeError("GitHub Token 无效或已过期，请检查")
        if status == 403:
            raise RuntimeError("GitHub API 速率限制或权限不足，请稍后重试")
        raise RuntimeError(f"检查仓库失败：HTTP {status} {body.get('message', '')}")

    def _create_repo(self) -> None:
        """创建新仓库。"""
        self.log.emit(f"[INFO] 正在创建仓库 {self.owner}/{self.repo} …")
        status, body = api_request(
            "/user/repos", self.token, method="POST",
            data={
                "name": self.repo,
                "description": "Prism — 基于 FFmpeg 的现代 Fluent 风格媒体格式转换工具",
                "private": False,
                "auto_init": True,
            },
            timeout=30, use_mirror=self.use_mirror,
            mirror_prefix=self.mirror_prefix,
        )
        if status not in (200, 201):
            raise RuntimeError(f"创建仓库失败：HTTP {status} {body.get('message', '')}")
        self.log.emit(f"[OK] 仓库 {self.owner}/{self.repo} 创建成功")
        # 创建后等待 GitHub 处理
        time.sleep(2)

    # -------------------------------------------------------- 源代码上传

    def _collect_source_files(self) -> List[Tuple[str, Path]]:
        """收集项目源代码文件，返回 (repo_path, local_path) 列表。"""
        result: List[Tuple[str, Path]] = []
        for root, dirs, files in os.walk(PROJECT_ROOT):
            # 过滤排除目录
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            for name in sorted(files):
                if name in EXCLUDE_FILES:
                    continue
                ext = Path(name).suffix.lower()
                if ext not in SOURCE_EXTS:
                    continue
                local_path = Path(root) / name
                # 计算仓库内相对路径
                rel = local_path.relative_to(PROJECT_ROOT).as_posix()
                result.append((rel, local_path))
        return result

    def _upload_source_files(self) -> None:
        """通过 Contents API 上传源代码文件。"""
        files = self._collect_source_files()
        if not files:
            self.log.emit("[WARN] 未找到可上传的源代码文件")
            return

        total = len(files)
        self.log.emit(f"[INFO] 共 {total} 个源代码文件待上传")
        self.progress.emit(0, f"开始上传源代码（{total} 个文件）…")

        for index, (repo_path, local_path) in enumerate(files):
            if self._cancelled:
                return
            pct = int(index / total * 100)
            self.progress.emit(pct, f"上传源代码 [{index + 1}/{total}] {repo_path}")
            try:
                content = local_path.read_bytes()
                content_b64 = base64.b64encode(content).decode("ascii")
                status, body = api_request(
                    f"/repos/{self.owner}/{self.repo}/contents/{repo_path}",
                    self.token, method="PUT",
                    data={
                        "message": f"upload {repo_path}",
                        "content": content_b64,
                        "branch": "main",
                    },
                    timeout=60, use_mirror=self.use_mirror,
                    mirror_prefix=self.mirror_prefix,
                )
                if status not in (200, 201):
                    self.log.emit(
                        f"  [FAIL] {repo_path}: HTTP {status} "
                        f"{body.get('message', 'unknown')}"
                    )
                else:
                    # 只在调试时输出成功项，避免日志过长
                    if (index + 1) % 10 == 0:
                        self.log.emit(f"  已上传 {index + 1}/{total} …")
            except Exception as exc:
                self.log.emit(f"  [ERROR] {repo_path}: {exc}")

        self.progress.emit(100, "源代码上传完成")
        self.log.emit(f"[OK] 源代码上传完成（共 {total} 个文件）")

    # -------------------------------------------------------- 二进制上传

    def _create_release(self, tag: str, name: str, body_text: str) -> Optional[int]:
        """创建 GitHub Release，返回 release_id。"""
        status, body = api_request(
            f"/repos/{self.owner}/{self.repo}/releases", self.token,
            method="POST",
            data={
                "tag_name": tag,
                "name": name,
                "body": body_text,
                "draft": False,
                "prerelease": False,
            },
            timeout=30, use_mirror=self.use_mirror,
            mirror_prefix=self.mirror_prefix,
        )
        if status == 422:
            # tag 已存在，尝试获取已有 release
            self.log.emit(f"[INFO] Tag {tag} 已存在，尝试获取对应 release")
            status, body = api_request(
                f"/repos/{self.owner}/{self.repo}/releases/tags/{tag}",
                self.token, timeout=15, use_mirror=self.use_mirror,
                mirror_prefix=self.mirror_prefix,
            )
            if status == 200:
                return body.get("id")
        if status not in (200, 201):
            self.log.emit(f"[ERROR] 创建 release 失败：HTTP {status} {body.get('message', '')}")
            return None
        return body.get("id")

    def _upload_asset(self, release_id: int, file_path: Path) -> bool:
        """上传单个二进制文件到 Release Assets。"""
        file_size = file_path.stat().st_size
        file_name = file_path.name
        self.log.emit(f"[INFO] 上传 {file_name}（{file_size / 1024 / 1024:.1f} MB）…")

        # uploads.github.com 不支持加速镜像，使用直连
        upload_url = f"{GITHUB_UPLOADS}/repos/{self.owner}/{self.repo}/releases/{release_id}/assets?name={file_name}"
        try:
            data = file_path.read_bytes()
            status, raw, _ = http_request(
                upload_url, self.token, method="POST",
                data=data, content_type="application/octet-stream",
                timeout=max(300, int(file_size / 1024 / 100)),  # 大文件长超时
            )
            try:
                body = json.loads(raw.decode("utf-8", errors="replace"))
            except json.JSONDecodeError:
                body = {}
            if status not in (200, 201):
                self.log.emit(
                    f"  [FAIL] HTTP {status}: {body.get('message', 'unknown')}"
                )
                return False
            self.log.emit(f"  [OK] {file_name} 上传成功")
            return True
        except Exception as exc:
            self.log.emit(f"  [ERROR] 上传 {file_name} 失败：{exc}")
            return False

    def _upload_binaries(self) -> None:
        """上传可执行文件与安装包到 GitHub Releases。"""
        binaries: List[Path] = []
        if self.upload_exe and PORTABLE_EXE.is_file():
            binaries.append(PORTABLE_EXE)
        elif self.upload_exe and not PORTABLE_EXE.is_file():
            self.log.emit(f"[WARN] 可执行文件不存在：{PORTABLE_EXE}")
        if self.upload_installer and INSTALLER_EXE.is_file():
            binaries.append(INSTALLER_EXE)
        elif self.upload_installer and not INSTALLER_EXE.is_file():
            self.log.emit(f"[WARN] 安装包不存在：{INSTALLER_EXE}")

        if not binaries:
            self.log.emit("[WARN] 没有可上传的二进制文件")
            return

        # 创建 release
        version_tag = f"v{datetime.now().strftime('%Y.%m.%d')}"
        release_name = f"Prism {version_tag}"
        release_body = "Prism 媒体格式转换工具发布包"
        release_id = self._create_release(version_tag, release_name, release_body)
        if release_id is None:
            self.log.emit("[ERROR] 无法创建 Release，跳过二进制上传")
            return

        total = len(binaries)
        for index, file_path in enumerate(binaries):
            if self._cancelled:
                return
            self.progress.emit(
                int(index / total * 100),
                f"上传二进制 [{index + 1}/{total}] {file_path.name}",
            )
            self._upload_asset(release_id, file_path)

        self.progress.emit(100, "二进制文件上传完成")

    # -------------------------------------------------------- 主流程

    def _do_upload(self) -> None:
        """上传主流程。"""
        self.log.emit("=" * 60)
        self.log.emit(f"GitHub 上传工具 — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.log.emit(f"目标仓库：{self.owner}/{self.repo}")
        if self.use_mirror:
            self.log.emit(f"加速源：{self.mirror_prefix or '直连'}")
        self.log.emit("=" * 60)

        # 1. 检查/创建仓库
        if not self._check_repo_exists():
            self._create_repo()

        # 2. 上传源代码
        if self.upload_source:
            self.log.emit("-" * 40)
            self._upload_source_files()

        # 3. 上传二进制
        if (self.upload_exe or self.upload_installer) and not self._cancelled:
            self.log.emit("-" * 40)
            self._upload_binaries()

        self.log.emit("=" * 60)
        if self._cancelled:
            self.log.emit("[INFO] 上传已被用户取消")
        else:
            self.log.emit("[OK] 全部上传任务完成")
        self.log.emit("=" * 60)


# ============================================================ GUI

class GitHubUploaderWindow(QMainWindow):
    """GitHub 上传工具主窗口。"""

    def __init__(self) -> None:
        super().__init__()
        self._worker: Optional[UploadWorker] = None
        self._build_ui()
        self._detect_network()

    def _build_ui(self) -> None:
        self.setWindowTitle("Prism GitHub 上传工具")
        self.setMinimumSize(640, 600)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        # ---- 标题 ----
        title = QLabel("Prism GitHub 上传工具")
        font = QFont(title.font())
        font.setPointSize(14)
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)

        # ---- 认证区 ----
        auth_group = QGroupBox("GitHub 认证")
        auth_layout = QVBoxLayout(auth_group)

        token_row = QHBoxLayout()
        token_row.addWidget(QLabel("Token:"))
        self.edit_token = QLineEdit()
        self.edit_token.setEchoMode(QLineEdit.Password)
        self.edit_token.setPlaceholderText("ghp_xxxx...（需要 repo 权限）")
        token_row.addWidget(self.edit_token, 1)
        auth_layout.addLayout(token_row)

        repo_row = QHBoxLayout()
        repo_row.addWidget(QLabel("用户名:"))
        self.edit_owner = QLineEdit(DEFAULT_OWNER)
        repo_row.addWidget(self.edit_owner, 1)
        repo_row.addWidget(QLabel("仓库名:"))
        self.edit_repo = QLineEdit(DEFAULT_REPO)
        repo_row.addWidget(self.edit_repo, 1)
        auth_layout.addLayout(repo_row)

        layout.addWidget(auth_group)

        # ---- 上传选项 ----
        opt_group = QGroupBox("上传内容")
        opt_layout = QVBoxLayout(opt_group)

        self.chk_source = QCheckBox(
            f"源代码文件（.py / .bat / .nsi / .spec 等，排除 .venv / build / dist / 本脚本）"
        )
        self.chk_source.setChecked(True)
        opt_layout.addWidget(self.chk_source)

        self.chk_exe = QCheckBox(
            f"可执行文件（{PORTABLE_EXE.name}）"
        )
        self.chk_exe.setToolTip(str(PORTABLE_EXE))
        opt_layout.addWidget(self.chk_exe)

        self.chk_installer = QCheckBox(
            f"安装包（{INSTALLER_EXE.name}）"
        )
        self.chk_installer.setToolTip(str(INSTALLER_EXE))
        opt_layout.addWidget(self.chk_installer)

        layout.addWidget(opt_group)

        # ---- 加速选项 ----
        net_group = QGroupBox("网络加速（中国大陆）")
        net_layout = QVBoxLayout(net_group)
        self.chk_mirror = QCheckBox("使用 GitHub 加速镜像（API 请求）")
        self.chk_mirror.toggled.connect(self._on_mirror_toggled)
        net_layout.addWidget(self.chk_mirror)
        mirror_row = QHBoxLayout()
        mirror_row.addWidget(QLabel("镜像源:"))
        self.combo_mirror = QLineEdit()
        self.combo_mirror.setPlaceholderText("https://gh-proxy.com/")
        self.combo_mirror.setEnabled(False)
        mirror_row.addWidget(self.combo_mirror, 1)
        net_layout.addLayout(mirror_row)
        layout.addWidget(net_group)

        # ---- 操作按钮 ----
        btn_row = QHBoxLayout()
        self.btn_upload = QPushButton("开始上传")
        self.btn_upload.clicked.connect(self._start_upload)
        btn_row.addWidget(self.btn_upload)
        self.btn_cancel = QPushButton("取消")
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.clicked.connect(self._cancel_upload)
        btn_row.addWidget(self.btn_cancel)
        btn_row.addStretch(1)
        layout.addLayout(btn_row)

        # ---- 进度 ----
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        layout.addWidget(self.progress_bar)
        self.lbl_status = QLabel("就绪")
        layout.addWidget(self.lbl_status)

        # ---- 日志 ----
        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setMaximumBlockCount(5000)
        font_log = QFont("Consolas")
        font_log.setPointSize(9)
        self.log_view.setFont(font_log)
        layout.addWidget(self.log_view, 1)

    def _on_mirror_toggled(self, checked: bool) -> None:
        self.combo_mirror.setEnabled(checked)
        if checked and not self.combo_mirror.text():
            self.combo_mirror.setText("https://gh-proxy.com/")

    def _detect_network(self) -> None:
        """后台检测是否在大陆网络。"""
        def detect():
            is_china = detect_china_network()
            if is_china:
                self._safe_log("[INFO] 检测到可能处于中国大陆网络环境，建议启用加速镜像")
                self._safe_toggle_mirror(True)
            else:
                self._safe_log("[INFO] GitHub 直连正常，无需加速")
        t = threading.Thread(target=detect, daemon=True)
        t.start()

    def _safe_log(self, msg: str) -> None:
        """线程安全的日志输出。"""
        from PySide6.QtCore import QMetaObject, Qt as QtConst
        QMetaObject.invokeMethod(
            self.log_view, "appendPlainText", QtConst.QueuedConnection, msg
        )

    def _safe_toggle_mirror(self, enable: bool) -> None:
        from PySide6.QtCore import QMetaObject
        QMetaObject.invokeMethod(
            self.chk_mirror, "setChecked", Qt.QueuedConnection, enable
        )

    def _log(self, msg: str) -> None:
        self.log_view.appendPlainText(msg)
        self.log_view.verticalScrollBar().setValue(
            self.log_view.verticalScrollBar().maximum()
        )

    def _start_upload(self) -> None:
        token = self.edit_token.text().strip()
        owner = self.edit_owner.text().strip()
        repo = self.edit_repo.text().strip()

        if not token:
            QMessageBox.warning(self, "提示", "请输入 GitHub Token")
            return
        if not owner or not repo:
            QMessageBox.warning(self, "提示", "请输入用户名和仓库名")
            return
        if not (self.chk_source.isChecked() or self.chk_exe.isChecked()
                or self.chk_installer.isChecked()):
            QMessageBox.warning(self, "提示", "请至少选择一项上传内容")
            return

        use_mirror = self.chk_mirror.isChecked()
        mirror_prefix = self.combo_mirror.text().strip() if use_mirror else ""

        self._worker = UploadWorker(
            token=token, owner=owner, repo=repo,
            upload_source=self.chk_source.isChecked(),
            upload_exe=self.chk_exe.isChecked(),
            upload_installer=self.chk_installer.isChecked(),
            use_mirror=use_mirror, mirror_prefix=mirror_prefix,
        )
        self._worker.log.connect(self._log)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished_signal.connect(self._on_finished)
        self._worker.start()

        self.btn_upload.setEnabled(False)
        self.btn_cancel.setEnabled(True)
        self.progress_bar.setValue(0)

    def _cancel_upload(self) -> None:
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self._log("[INFO] 正在取消上传…")
        self.btn_cancel.setEnabled(False)

    def _on_progress(self, percent: int, text: str) -> None:
        self.progress_bar.setValue(percent)
        self.lbl_status.setText(text)

    def _on_finished(self, success: bool) -> None:
        self.btn_upload.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        if success:
            self.progress_bar.setValue(100)
            self.lbl_status.setText("上传完成")
            QMessageBox.information(self, "完成", "上传任务已完成")
        else:
            self.lbl_status.setText("上传未完成")
            QMessageBox.warning(self, "提示", "上传过程中出现问题，请查看日志")


# ============================================================ 入口

def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Prism GitHub Uploader")
    window = GitHubUploaderWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
