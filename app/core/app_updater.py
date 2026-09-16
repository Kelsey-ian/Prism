# -*- coding: utf-8 -*-
"""Prism 应用程序自身的更新检查器（独立于 FFmpeg 更新）。

从 GitHub Kelsey-ian/Prism 仓库查询最新 Release，比对版本号，
下载安装包并提供进度反馈。内置中国大陆 GitHub 加速源。

更新流程：
1. 查询 GitHub API 获取最新 release 信息（直连失败时尝试镜像）
2. 与本地 APP_VERSION 比对，判断是否需要更新
3. 下载安装包（支持多个加速源，测速选最快）
4. 下载完成后提示用户运行安装程序
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from PySide6.QtCore import QObject, Signal

from .. import APP_NAME, APP_VERSION
from ..config import DOWNLOAD_DIR, app_config
from .hardware import detect_arch

# GitHub 仓库
REPO_OWNER = "Kelsey-ian"
REPO_NAME = "Prism"
GITHUB_API_URL = (
    f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest"
)
GITHUB_REPO_URL = f"https://github.com/{REPO_OWNER}/{REPO_NAME}"

# GitHub API 镜像源（key -> 展示名, URL前缀）
# api.github.com 在大陆有时访问不稳定，以下镜像可代理 API 请求
GITHUB_API_MIRRORS: List[Tuple[str, str, str]] = [
    ("direct", "GitHub API 直连", ""),
    ("ghfast", "ghfast.top API 镜像", "https://ghfast.top/"),
    ("ghproxy", "gh-proxy.com API 镜像", "https://gh-proxy.com/"),
]

# GitHub 下载加速源（key -> 展示名, URL前缀）
GITHUB_DOWNLOAD_SOURCES: List[Tuple[str, str, str]] = [
    ("direct", "GitHub 官方源（直连）", ""),
    ("ghfast", "ghfast.top 大陆加速", "https://ghfast.top/"),
    ("ghproxy", "gh-proxy.com 大陆加速", "https://gh-proxy.com/"),
    ("moeyy", "github.moeyy.xyz 大陆加速", "https://github.moeyy.xyz/"),
]

_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Prism-AppUpdater/1.0"


@dataclass
class AppReleaseInfo:
    """GitHub Release 信息。"""
    version: str           # 版本号（纯数字，如 "1.1.0"）
    tag: str               # Git tag（如 "v1.1.0"）
    release_url: str       # release 页面 URL
    release_notes: str     # 更新说明
    asset_name: str        # 安装包文件名
    asset_url: str         # 安装包原始下载地址（未加速）
    published_at: str      # 发布时间


class AppUpdater(QObject):
    """Prism 应用更新控制器。

    信号与 FFmpegUpdater 风格一致，便于 UI 层复用 FunctionThread。
    """

    checking = Signal()
    checked = Signal(bool, bool, str, str)   # success, has_update, message, latest_version
    progress = Signal(int, str)              # 0~100, 状态文本
    finished = Signal(bool, str)             # 下载完成：success, message(含路径)
    busy_changed = Signal(bool)

    def __init__(self) -> None:
        super().__init__()
        self._busy = False
        self.latest: Optional[AppReleaseInfo] = None
        self._downloaded_path: Optional[str] = None

    @property
    def busy(self) -> bool:
        return self._busy

    @property
    def downloaded_path(self) -> Optional[str]:
        return self._downloaded_path

    def _set_busy(self, value: bool) -> None:
        self._busy = value
        self.busy_changed.emit(value)

    # ------------------------------------------------------------ 版本检查

    def check_latest(self) -> Optional[AppReleaseInfo]:
        """查询 GitHub 最新 release 信息。直连失败时尝试镜像源。"""
        for _key, _label, prefix in GITHUB_API_MIRRORS:
            url = (prefix + GITHUB_API_URL) if prefix else GITHUB_API_URL
            try:
                payload = json.loads(self._http_get_text(url, timeout=15))
                info = self._parse_release(payload)
                if info is not None:
                    return info
            except Exception:
                continue
        return None

    def _parse_release(self, payload: dict) -> Optional[AppReleaseInfo]:
        """从 GitHub API 返回的 JSON 中提取版本与安装包信息。"""
        tag = payload.get("tag_name", "") or ""
        version = re.sub(r"^[vV]", "", tag).strip()
        if not version:
            return None

        release_url = payload.get("html_url", GITHUB_REPO_URL)
        release_notes = payload.get("body", "") or ""
        published_at = (payload.get("published_at", "") or "")[:10]

        # 在 assets 中查找安装包：优先 Setup 安装程序，其次便携包
        arch = detect_arch()
        assets = payload.get("assets", [])
        asset = self._pick_asset(assets, arch)
        if asset is None:
            return None

        return AppReleaseInfo(
            version=version,
            tag=tag,
            release_url=release_url,
            release_notes=release_notes,
            asset_name=asset.get("name", ""),
            asset_url=asset.get("browser_download_url", ""),
            published_at=published_at,
        )

    @staticmethod
    def _pick_asset(assets: list, arch: str) -> Optional[dict]:
        """从 release assets 中选择最合适的安装包。"""
        # 按优先级匹配
        if arch == "arm64":
            patterns = [
                r"Setup.*arm64.*\.exe$",
                r"Setup.*arm.*\.exe$",
                r"Prism.*arm64.*\.exe$",
                r"Prism.*portable.*arm64.*\.zip$",
            ]
        else:
            patterns = [
                r"Setup.*x64.*\.exe$",
                r"Setup.*64.*\.exe$",
                r"Setup.*\.exe$",
                r"Prism.*x64.*\.exe$",
                r"Prism.*portable.*x64.*\.zip$",
                r"Prism.*\.zip$",
            ]

        for pattern in patterns:
            for asset in assets:
                name = asset.get("name", "")
                if re.search(pattern, name, re.IGNORECASE):
                    return asset
        return None

    def check_and_compare(self) -> None:
        """阻塞执行版本检查并发射 checked 信号（后台线程调用）。"""
        if self._busy:
            return
        self._set_busy(True)
        try:
            self.checking.emit()
            latest = self.check_latest()
            if latest is None:
                self.checked.emit(
                    False, False,
                    "无法连接 GitHub，请检查网络后重试（大陆用户可尝试设置加速源）",
                    "",
                )
                return

            has_update = self.is_newer(latest.version)
            if has_update:
                message = (
                    f"发现新版本：v{latest.version}（当前 v{APP_VERSION}）\n"
                    f"发布日期：{latest.published_at}"
                )
            else:
                message = f"当前已是最新版本（本地 v{APP_VERSION}，远端 v{latest.version}）"
            self.checked.emit(True, has_update, message, latest.version)
        finally:
            self._set_busy(False)

    def is_newer(self, remote_version: str) -> bool:
        """比较本地版本与远端版本（语义化版本比较）。"""
        remote = self._version_tuple(remote_version)
        local = self._version_tuple(APP_VERSION)
        return remote > local

    @staticmethod
    def _version_tuple(text: str) -> Tuple[int, ...]:
        numbers = re.findall(r"\d+", text)
        return tuple(int(n) for n in numbers[:4]) if numbers else (0,)

    # ------------------------------------------------------------ 下载源与测速

    def build_download_candidates(self, latest: AppReleaseInfo) -> List[AppReleaseInfo]:
        """根据通道配置，返回全部候选下载源（未测速排序）。"""
        candidates: List[AppReleaseInfo] = []
        for _key, label, prefix in self._enabled_channels():
            candidates.append(AppReleaseInfo(
                version=latest.version,
                tag=latest.tag,
                release_url=latest.release_url,
                release_notes=latest.release_notes,
                asset_name=latest.asset_name,
                asset_url=(prefix + latest.asset_url) if prefix else latest.asset_url,
                published_at=latest.published_at,
            ))
        return candidates

    def _enabled_channels(self) -> List[Tuple[str, str, str]]:
        key = app_config.get("update_channel", "auto")
        if key == "auto":
            return list(GITHUB_DOWNLOAD_SOURCES)
        if key == "direct":
            return [GITHUB_DOWNLOAD_SOURCES[0]]
        chosen = next((s for s in GITHUB_DOWNLOAD_SOURCES if s[0] == key), None)
        if chosen is None:
            return list(GITHUB_DOWNLOAD_SOURCES)
        return [chosen, GITHUB_DOWNLOAD_SOURCES[0]]

    def order_by_latency(
        self, candidates: List[AppReleaseInfo],
        log: Optional[Callable[[str], None]] = None,
    ) -> List[AppReleaseInfo]:
        """并发对所有源做延迟探测，按延迟从低到高排序。"""
        results: Dict[str, float] = {}
        threads: List[threading.Thread] = []

        def probe(item: AppReleaseInfo) -> None:
            results[item.asset_url] = self._probe_latency(item.asset_url) or 999.0

        for item in candidates:
            t = threading.Thread(target=probe, args=(item,), daemon=True)
            threads.append(t)
            t.start()
        for t in threads:
            t.join(timeout=8)

        reachable = [c for c in candidates if results.get(c.asset_url, 999) < 99]
        unreachable = [c for c in candidates if results.get(c.asset_url, 999) >= 99]
        reachable.sort(key=lambda c: results[c.asset_url])
        if log and reachable:
            summary = "；".join(
                f"{c.asset_name} {results[c.asset_url] * 1000:.0f}ms" for c in reachable
            )
            log(f"源测速结果：{summary}")
        return reachable + unreachable

    def rank_candidates(self, latest: AppReleaseInfo) -> List[AppReleaseInfo]:
        """构建候选 -> 全源测速 -> 排序。"""
        candidates = self.build_download_candidates(latest)
        ordered = self.order_by_latency(
            candidates,
            log=lambda msg: self.progress.emit(3, msg),
        )
        if not ordered:
            ordered = candidates
        return ordered

    def _probe_latency(self, url: str) -> Optional[float]:
        """对单个源做轻量探测（HEAD，失败时 GET Range），返回秒级耗时。"""
        headers = {"User-Agent": _UA}
        start = time.monotonic()
        try:
            req = urllib.request.Request(url, method="HEAD", headers=headers)
            with urllib.request.urlopen(req, timeout=5) as resp:
                resp.read(16)
            return time.monotonic() - start
        except urllib.error.HTTPError as exc:
            if exc.code not in (403, 405, 501):
                return None
        except (urllib.error.URLError, TimeoutError, OSError):
            return None
        try:
            req = urllib.request.Request(
                url, headers={**headers, "Range": "bytes=0-0"}
            )
            start = time.monotonic()
            with urllib.request.urlopen(req, timeout=5) as resp:
                resp.read(1)
            return time.monotonic() - start
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError):
            return None

    # ------------------------------------------------------------ 下载

    def download_update(self) -> None:
        """下载最新版本安装包到下载目录（后台线程调用）。"""
        self._set_busy(True)
        self._downloaded_path = None
        try:
            latest = self.latest or self.check_latest()
            if latest is None:
                self.finished.emit(
                    False, "无法获取更新信息，请检查网络连接"
                )
                return

            if not latest.asset_url:
                self.finished.emit(
                    False,
                    f"Release v{latest.version} 未包含可下载的安装包\n"
                    f"请前往 {latest.release_url} 手动下载"
                )
                return

            self.progress.emit(2, "正在测试各下载源延迟，选择最快通道…")
            ordered = self.rank_candidates(latest)

            dest = DOWNLOAD_DIR / latest.asset_name
            last_error = ""
            for index, item in enumerate(ordered):
                try:
                    hint = f"（源：{item.asset_name}）"
                    self.progress.emit(
                        5,
                        f"正在下载 Prism v{latest.version} {hint} …",
                    )
                    self._download(item.asset_url, dest, 5, 90)
                    break
                except Exception as exc:
                    last_error = str(exc)
                    continue
            else:
                self.finished.emit(
                    False, f"所有下载源均失败：{last_error[:160]}"
                )
                return

            # 校验文件非空
            if not dest.is_file() or dest.stat().st_size < 1024:
                self.finished.emit(False, "下载的文件无效或已损坏")
                return

            self.progress.emit(100, "下载完成")
            self._downloaded_path = str(dest)
            self.finished.emit(
                True,
                f"Prism v{latest.version} 安装包已下载完成\n"
                f"保存路径：{dest}\n"
                f"点击「安装」按钮运行安装程序（请先关闭 Prism）",
            )
        finally:
            self._set_busy(False)

    def run_installer(self) -> bool:
        """运行已下载的安装程序。返回是否成功启动。"""
        path = self._downloaded_path
        if not path or not Path(path).is_file():
            return False
        try:
            subprocess.Popen(
                [path], creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
            )
            return True
        except OSError:
            return False

    # ------------------------------------------------------------ 内部实现

    def _http_get_text(self, url: str, timeout: int = 15) -> str:
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": _UA,
                "Accept": "application/vnd.github+json",
            },
        )
        with urllib.request.urlopen(request, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")

    def _download(self, url: str, dest: Path, pct_from: int, pct_to: int) -> None:
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_suffix(dest.suffix + ".part")
        request = urllib.request.Request(url, headers={"User-Agent": _UA})
        with urllib.request.urlopen(request, timeout=60) as resp:
            total = int(resp.headers.get("Content-Length", 0) or 0)
            done = 0
            span = pct_to - pct_from
            with open(tmp, "wb") as fp:
                while True:
                    chunk = resp.read(1024 * 256)
                    if not chunk:
                        break
                    fp.write(chunk)
                    done += len(chunk)
                    if total:
                        percent = pct_from + int(done / total * span)
                        mb_done = done / 1024 / 1024
                        mb_total = total / 1024 / 1024
                        self.progress.emit(
                            min(percent, pct_to),
                            f"正在下载… {mb_done:.1f} / {mb_total:.1f} MB",
                        )
        shutil.move(str(tmp), str(dest))


# 全局单例
app_updater = AppUpdater()
