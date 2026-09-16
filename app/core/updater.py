# -*- coding: utf-8 -*-
"""内置 FFmpeg 的自动升级。

升级策略（v2）：
1. 启动后后台静默比对版本，发现新版本自动下载到暂存目录（不替换正在使用
   的二进制，因此绝不打断进行中的转换任务）；
2. 用户正常关闭程序时，若暂存更新已就绪，替换 bin/ 下的文件完成安装；
3. 关闭时仍有任务进行：可选择等待任务全部完成后再退出并安装；
4. 更新源：gyan.dev 稳定版（x64）+ BtbN GitHub 每日构建（x64 / ARM64），
   GitHub 提供多个中国大陆加速前缀；下载前对全部源做延迟测速，选最快源；
5. 旧版本仅保留最近 1 份，便于回滚，更早的历史文件自动清理。
"""
from __future__ import annotations

import json
import os
import re
import shutil
import tempfile
import threading
import time
import urllib.error
import urllib.request
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from PySide6.QtCore import QObject, Signal

from ..config import BIN_DIR, DOWNLOAD_DIR, INSTALL_RECORD, STAGING_DIR, app_config
from .ffmpeg import _CREATE_NO_WINDOW, ffmpeg_manager
from .hardware import detect_arch

GYAN_VERSION_URL = "https://www.gyan.dev/ffmpeg/builds/release-version"
GYAN_ZIP_URL = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
BTBN_API_URL = "https://api.github.com/repos/BtbN/FFmpeg-Builds/releases/latest"

# BtbN 按架构提供不同构建
BTBN_ASSETS = {
    "x64": "ffmpeg-master-latest-win64-gpl.zip",
    "arm64": "ffmpeg-master-latest-winarm64-gpl.zip",
}

# GitHub 下载通道：key -> (展示名, URL 前缀)
GITHUB_SOURCES = [
    ("direct", "GitHub 官方源（直连）", ""),
    ("ghfast", "ghfast.top 大陆加速", "https://ghfast.top/"),
    ("ghproxy", "gh-proxy.com 大陆加速", "https://gh-proxy.com/"),
    ("moeyy", "github.moeyy.xyz 大陆加速", "https://github.moeyy.xyz/"),
]

_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) FormatStudio-Updater/2.0"


@dataclass
class LatestInfo:
    version: str            # 展示用版本名
    url: str                # 实际下载地址（GitHub 为未加速的原始地址）
    source: str             # gyan / btbn
    label: str = "官方源"   # 源展示名
    build_date: str = ""    # BtbN 每日构建日期（YYYY-MM-DD）
    arch: str = "x64"


class FFmpegUpdater(QObject):
    """升级控制器；阻塞方法由 UI 层放入 FunctionThread 执行，信号跨线程回传。"""

    checking = Signal()
    checked = Signal(bool, bool, str, str)      # success, has_update, message, latest_version
    progress = Signal(int, str)                 # 0~100, 状态文本
    finished = Signal(bool, str)                # 即时安装流程结束（首装）
    staged = Signal(bool, str)                  # 更新包暂存结束：success, message
    busy_changed = Signal(bool)

    def __init__(self) -> None:
        super().__init__()
        self._busy = False
        self.latest: Optional[LatestInfo] = None
        self._btbn: Optional[LatestInfo] = None

    @property
    def busy(self) -> bool:
        return self._busy

    def _set_busy(self, value: bool) -> None:
        self._busy = value
        self.busy_changed.emit(value)

    # ------------------------------------------------------------ 版本检查

    def check_latest(self) -> Optional[LatestInfo]:
        """获取各源最新版本信息（gyan 稳定版优先；同时记录 BtbN 备选）。"""
        arch = detect_arch()
        self._btbn = self._query_btbn(arch)

        # gyan.dev 仅提供 x64 稳定版
        if arch == "x64":
            try:
                text = self._http_get_text(GYAN_VERSION_URL, timeout=12)
                version = text.strip().splitlines()[0].strip()
                if re.fullmatch(r"\d+(\.\d+)+", version):
                    self.latest = LatestInfo(
                        version=version, url=GYAN_ZIP_URL,
                        source="gyan", label="gyan.dev 稳定版", arch=arch,
                    )
                    return self.latest
            except Exception:
                pass

        if self._btbn is not None:
            self.latest = self._btbn
            return self.latest
        self.latest = None
        return None

    def _query_btbn(self, arch: str) -> Optional[LatestInfo]:
        asset_name = BTBN_ASSETS.get(arch)
        if not asset_name:
            return None
        try:
            payload = json.loads(self._http_get_text(BTBN_API_URL, timeout=18))
            asset_url = ""
            for asset in payload.get("assets", []):
                if asset.get("name") == asset_name:
                    asset_url = asset.get("browser_download_url", "")
                    break
            tag = payload.get("tag_name", "") or payload.get("published_at", "")[:10]
            date_match = re.search(r"(\d{4}-\d{2}-\d{2})", tag)
            if asset_url:
                return LatestInfo(
                    version=tag or "latest",
                    url=asset_url,
                    source="btbn",
                    label=f"BtbN 每日构建（{arch}）",
                    build_date=date_match.group(1) if date_match else "",
                    arch=arch,
                )
        except Exception:
            return None
        return None

    def check_and_compare(self) -> None:
        """阻塞执行版本检查并发射 checked 信号（后台线程）。仅比对，不下载。"""
        if self._busy:
            return
        self._set_busy(True)
        try:
            self.checking.emit()
            latest = self.check_latest()
            if latest is None:
                self.checked.emit(
                    False, False,
                    "无法连接升级服务器，请检查网络后重试",
                    "",
                )
                return

            local = ffmpeg_manager.version
            if not ffmpeg_manager.available:
                has_update = True
                message = f"未安装 FFmpeg，最新版本：{latest.version}（可直接下载内置）"
            else:
                has_update = self.is_newer(latest)
                if has_update:
                    message = f"发现新版本：{latest.version}（当前 {local or '未知'}），建议更新"
                else:
                    message = f"当前已是最新版本（本地 {local}，服务器 {latest.version}）"
            self.checked.emit(True, has_update, message, latest.version)
        finally:
            self._set_busy(False)

    def is_newer(self, latest: LatestInfo) -> bool:
        """比较本地版本与远端版本。"""
        record = self.read_record()
        local = ffmpeg_manager.version

        if latest.source == "gyan" and local:
            return self._version_tuple(latest.version) > self._version_tuple(local)
        if latest.source == "btbn":
            if latest.build_date and record.get("build_date"):
                return latest.build_date > record["build_date"]
            if latest.build_date and local:
                # 无安装记录时，每日构建默认提示一次
                return True
        return False

    @staticmethod
    def _version_tuple(text: str) -> Tuple[int, ...]:
        numbers = re.findall(r"\d+", text)
        return tuple(int(n) for n in numbers[:4]) if numbers else (0,)

    # ------------------------------------------------------------ 下载源与测速

    def build_candidates(self, latest: LatestInfo) -> List[LatestInfo]:
        """根据当前架构与通道配置，返回全部候选下载源（未测速排序）。"""
        candidates: List[LatestInfo] = []
        if latest.source == "gyan":
            candidates.append(latest)
        btbn = self._btbn if latest.source == "gyan" else latest
        if btbn is not None and btbn.source == "btbn":
            for key, label, prefix in self._enabled_channels():
                candidates.append(LatestInfo(
                    version=btbn.version,
                    url=(prefix + btbn.url if prefix else btbn.url),
                    source="btbn", label=label,
                    build_date=btbn.build_date, arch=btbn.arch,
                ))
        if latest.source == "btbn" and not candidates:
            candidates.append(latest)
        return candidates

    def _enabled_channels(self) -> List[Tuple[str, str, str]]:
        key = app_config.get("update_channel", "auto")
        if key == "auto":
            return list(GITHUB_SOURCES)
        if key == "direct":
            return [GITHUB_SOURCES[0]]
        chosen = next((s for s in GITHUB_SOURCES if s[0] == key), None)
        if chosen is None:
            return list(GITHUB_SOURCES)
        # 指定镜像失败时仍允许回退直连
        return [chosen, GITHUB_SOURCES[0]]

    def order_by_latency(
        self, candidates: List[LatestInfo], log: Optional[Callable[[str], None]] = None,
    ) -> List[LatestInfo]:
        """并发对所有源做延迟探测，按延迟从低到高排序（失败源沉底）。"""
        results: Dict[str, float] = {}
        threads: List[threading.Thread] = []

        def probe(item: LatestInfo) -> None:
            results[item.url] = self._probe_latency(item.url) or 999.0

        for item in candidates:
            t = threading.Thread(target=probe, args=(item,), daemon=True)
            threads.append(t)
            t.start()
        for t in threads:
            t.join(timeout=8)

        reachable = [c for c in candidates if results.get(c.url, 999) < 99]
        unreachable = [c for c in candidates if results.get(c.url, 999) >= 99]
        reachable.sort(key=lambda c: results[c.url])
        if log and reachable:
            summary = "；".join(
                f"{c.label} {results[c.url] * 1000:.0f}ms" for c in reachable
            )
            log(f"源测速结果：{summary}")
        return reachable + unreachable

    def rank_candidates(self, latest: LatestInfo) -> List[LatestInfo]:
        """构建候选 -> 全源测速 -> 同构建线优先的下载顺序。

        所有源都会参与延迟测速（满足“每次更新前测速、选最快源”）；
        但稳定版（gyan）优先于 BtbN 每日构建，仅当稳定源下载失败时
        才跨线容灾到每日构建，避免把稳定版用户意外换成 nightly。
        """
        candidates = self.build_candidates(latest)
        ordered = self.order_by_latency(
            candidates,
            log=lambda msg: self.progress.emit(3, msg),
        )
        if not ordered:
            ordered = candidates
        same_line = [c for c in ordered if c.source == latest.source]
        cross_line = [c for c in ordered if c.source != latest.source]
        return same_line + cross_line

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
            # 部分加速源不接受 HEAD，用 1 字节 Range GET 复测
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

    # ------------------------------------------------------------ 下载（暂存）

    def download_only(self) -> None:
        """后台下载更新包到暂存目录，不安装（在后台线程调用）。"""
        self._set_busy(True)
        try:
            latest = self.latest or self.check_latest()
            if latest is None:
                self.staged.emit(False, "无法获取更新信息，请检查网络连接")
                return

            # 已暂存同一版本则直接提示
            existing = self.read_stage_marker()
            if existing and existing.get("version") == latest.version and self.has_staged():
                self.staged.emit(
                    True, f"更新包 {latest.version} 已下载，将在退出后自动安装"
                )
                return

            self.progress.emit(2, "正在测试各更新源延迟，选择最快通道…")
            ordered = self.rank_candidates(latest)

            zip_path = STAGING_DIR / "package.zip"
            chosen_meta: Optional[LatestInfo] = None
            last_error = ""
            for index, item in enumerate(ordered):
                try:
                    hint = f"（源：{item.label}）"
                    self.progress.emit(
                        5 if index == 0 else 5,
                        f"正在下载 FFmpeg {latest.version} {hint} …",
                    )
                    self._download(item.url, zip_path, 5, 60)
                    chosen_meta = item
                    break
                except Exception as exc:
                    last_error = str(exc)
                    continue
            if chosen_meta is None:
                self.staged.emit(False, f"所有更新源均下载失败：{last_error[:160]}")
                return

            self.progress.emit(63, "下载完成，正在解压校验…")
            try:
                extracted = self._extract_bins(zip_path, STAGING_DIR)
            except Exception as exc:
                self.staged.emit(False, f"解压失败：{exc}")
                return
            if not extracted:
                self.staged.emit(False, "压缩包中未找到 ffmpeg.exe / ffprobe.exe")
                return

            new_ffmpeg, new_ffprobe = extracted
            if not self._verify_exe(new_ffmpeg):
                self.staged.emit(False, "下载的 FFmpeg 校验失败，已中止")
                return

            self.progress.emit(78, "更新包校验通过，已放入暂存区…")
            self._stage_bins(new_ffmpeg, new_ffprobe)
            self.write_stage_marker(chosen_meta)
            self._cleanup_temp(zip_path)
            self.progress.emit(100, "更新包就绪，将在退出后自动安装")
            self.staged.emit(
                True,
                f"FFmpeg {chosen_meta.version} 更新包已下载完成，"
                f"将在退出程序后自动安装（更新源：{chosen_meta.label}）",
            )
        finally:
            self._set_busy(False)

    def apply_staged(self, progress_cb: Optional[Callable[[int, str], None]] = None
                     ) -> Tuple[bool, str]:
        """退出时调用：把暂存的新二进制安装到 bin/。同步执行。"""
        marker = self.read_stage_marker()
        staged_ffmpeg = STAGING_DIR / "ffmpeg.exe"
        staged_ffprobe = STAGING_DIR / "ffprobe.exe"
        if not marker or not staged_ffmpeg.is_file():
            return False, "没有待安装的更新"

        def report(pct: int, text: str) -> None:
            if progress_cb:
                progress_cb(pct, text)

        report(20, "正在校验更新包…")
        if not self._verify_exe(str(staged_ffmpeg)):
            return False, "暂存更新校验失败"
        report(45, "正在安装 FFmpeg 更新（保留 1 份旧版本备份）…")
        try:
            self._install_bins(str(staged_ffmpeg), str(staged_ffprobe))
        except PermissionError:
            return False, "文件被占用，本次跳过安装"
        except OSError as exc:
            return False, f"安装失败：{exc}"

        report(85, "正在刷新引擎版本…")
        ffmpeg_manager.locate()
        ffmpeg_manager.refresh_version()
        self.write_record(LatestInfo(
            version=marker.get("version", ffmpeg_manager.version or ""),
            url="", source=marker.get("source", "staged"),
            build_date=marker.get("build_date", ""),
            arch=marker.get("arch", detect_arch()),
        ))
        self._clear_staging()
        report(100, "更新安装完成")
        return True, f"FFmpeg 已更新到 {ffmpeg_manager.version or marker.get('version')}"

    def has_staged(self) -> bool:
        return (STAGING_DIR / "ffmpeg.exe").is_file() and (
            STAGING_DIR / "update.json"
        ).is_file()

    def read_stage_marker(self) -> Dict[str, str]:
        try:
            return json.loads(
                (STAGING_DIR / "update.json").read_text(encoding="utf-8")
            )
        except (OSError, json.JSONDecodeError):
            return {}

    def write_stage_marker(self, latest: LatestInfo) -> None:
        STAGING_DIR.mkdir(parents=True, exist_ok=True)
        (STAGING_DIR / "update.json").write_text(
            json.dumps(
                {
                    "version": latest.version,
                    "source": latest.source,
                    "label": latest.label,
                    "build_date": latest.build_date,
                    "arch": latest.arch,
                    "downloaded_at": datetime.now().isoformat(timespec="seconds"),
                },
                ensure_ascii=False, indent=2,
            ),
            encoding="utf-8",
        )

    def _stage_bins(self, ffmpeg_exe: str, ffprobe_exe: str) -> None:
        """把校验过的二进制落到暂存根目录（原子替换）。"""
        STAGING_DIR.mkdir(parents=True, exist_ok=True)
        for src in (ffmpeg_exe, ffprobe_exe):
            if not src:
                continue
            dst = STAGING_DIR / Path(src).name
            tmp = dst.with_suffix(".new")
            shutil.copy2(src, tmp)
            os.replace(tmp, dst)

    def _clear_staging(self) -> None:
        for name in ("ffmpeg.exe", "ffprobe.exe", "update.json", "package.zip"):
            try:
                (STAGING_DIR / name).unlink(missing_ok=True)
            except OSError:
                pass
        for entry in STAGING_DIR.glob("ffmpeg_pkg_*"):
            if entry.is_dir():
                shutil.rmtree(entry, ignore_errors=True)

    # ------------------------------------------------------------ 首装（即时安装）

    def download_and_install(self) -> None:
        """未安装 FFmpeg 时的首装流程：测速下载 -> 解压 -> 立即安装。"""
        self._set_busy(True)
        zip_path = DOWNLOAD_DIR / "ffmpeg_package.zip"
        try:
            latest = self.latest or self.check_latest()
            if latest is None:
                self.finished.emit(False, "无法获取下载信息，请检查网络连接")
                return

            self.progress.emit(2, "正在测试各更新源延迟，选择最快通道…")
            ordered = self.rank_candidates(latest)

            chosen_meta: Optional[LatestInfo] = None
            last_error = ""
            for item in ordered:
                try:
                    self.progress.emit(5, f"正在下载 FFmpeg {latest.version}（源：{item.label}）…")
                    self._download(item.url, zip_path, 5, 68)
                    chosen_meta = item
                    break
                except Exception as exc:
                    last_error = str(exc)
                    continue
            if chosen_meta is None:
                self.finished.emit(False, f"所有下载源均失败：{last_error[:160]}")
                return

            self.progress.emit(72, "下载完成，正在解压校验…")
            try:
                extracted = self._extract_bins(zip_path, DOWNLOAD_DIR)
            except Exception as exc:
                self.finished.emit(False, f"解压失败：{exc}")
                return
            if not extracted:
                self.finished.emit(False, "压缩包中未找到 ffmpeg.exe / ffprobe.exe")
                return

            new_ffmpeg, new_ffprobe = extracted
            if not self._verify_exe(new_ffmpeg):
                self.finished.emit(False, "下载的 FFmpeg 校验失败，已中止安装")
                return

            self.progress.emit(88, "正在安装到内置目录…")
            try:
                self._install_bins(new_ffmpeg, new_ffprobe)
            except PermissionError:
                self.finished.emit(
                    False, "文件被占用：请先停止所有转换任务后重试"
                )
                return
            except OSError as exc:
                self.finished.emit(False, f"安装失败：{exc}")
                return

            ffmpeg_manager.locate()
            ffmpeg_manager.refresh_version()
            self.write_record(chosen_meta)
            self.progress.emit(100, "安装完成")
            self.finished.emit(
                True,
                f"FFmpeg 已安装：{ffmpeg_manager.version or latest.version}"
                f"（更新源：{chosen_meta.label}）",
            )
        finally:
            self._set_busy(False)
            self._cleanup_temp(zip_path)

    # ------------------------------------------------------------ 安装记录

    def read_record(self) -> Dict[str, str]:
        try:
            return json.loads(INSTALL_RECORD.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}

    def write_record(self, latest: LatestInfo) -> None:
        try:
            INSTALL_RECORD.write_text(
                json.dumps(
                    {
                        "version": ffmpeg_manager.version or latest.version,
                        "source": latest.source,
                        "build_date": latest.build_date,
                        "installed_at": datetime.now().isoformat(timespec="seconds"),
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
        except OSError:
            pass

    # ------------------------------------------------------------ 内部实现

    def _http_get_text(self, url: str, timeout: int = 15) -> str:
        request = urllib.request.Request(url, headers={"User-Agent": _UA, "Accept": "*/*"})
        with urllib.request.urlopen(request, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")

    def _download(self, url: str, dest: Path, pct_from: int, pct_to: int) -> None:
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_suffix(".zip.part")
        request = urllib.request.Request(url, headers={"User-Agent": _UA})
        with urllib.request.urlopen(request, timeout=30) as resp:
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

    def _extract_bins(self, zip_path: Path, work_dir: Path
                      ) -> Optional[Tuple[str, str]]:
        """解压并找出 ffmpeg.exe / ffprobe.exe，返回临时目录中的绝对路径。"""
        target_dir = Path(tempfile.mkdtemp(prefix="ffmpeg_pkg_", dir=str(work_dir)))
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(target_dir)

        ffmpeg_exe = ffprobe_exe = None
        for root, _dirs, files in os.walk(target_dir):
            for name in files:
                lower = name.lower()
                if lower == "ffmpeg.exe":
                    ffmpeg_exe = os.path.join(root, name)
                elif lower == "ffprobe.exe":
                    ffprobe_exe = os.path.join(root, name)
        if not ffmpeg_exe:
            shutil.rmtree(target_dir, ignore_errors=True)
            return None
        return ffmpeg_exe, ffprobe_exe or ""

    @staticmethod
    def _verify_exe(path: str) -> bool:
        import subprocess
        try:
            proc = subprocess.run(
                [path, "-version"],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                timeout=10, creationflags=_CREATE_NO_WINDOW,
            )
            return proc.returncode == 0 and b"ffmpeg version" in proc.stdout[:200]
        except (OSError, subprocess.SubprocessError):
            return False

    @staticmethod
    def _install_bins(ffmpeg_exe: str, ffprobe_exe: str) -> None:
        """替换 bin 目录下的可执行文件；旧文件按版本整组备份，仅保留 1 份。"""
        BIN_DIR.mkdir(parents=True, exist_ok=True)
        backup_root = BIN_DIR / "_backup"

        old_files = [BIN_DIR / "ffmpeg.exe", BIN_DIR / "ffprobe.exe"]
        has_old = any(p.is_file() for p in old_files)
        if has_old:
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            version_dir = backup_root / stamp
            suffix = 1
            while version_dir.exists():
                suffix += 1
                version_dir = backup_root / f"{stamp}_{suffix}"
            version_dir.mkdir(parents=True, exist_ok=True)
            for old in old_files:
                if old.is_file():
                    shutil.move(str(old), str(version_dir / old.name))

        for src in (ffmpeg_exe, ffprobe_exe):
            if not src:
                continue
            dst = BIN_DIR / Path(src).name
            tmp_dst = dst.with_suffix(".new")
            shutil.copy2(src, tmp_dst)
            os.replace(tmp_dst, dst)

        # 仅保留最近 1 个旧版本（按时间排序的备份文件夹，整组删除更早版本）
        if backup_root.is_dir():
            versions = sorted(
                (p for p in backup_root.iterdir() if p.is_dir()),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )
            for old_dir in versions[1:]:
                shutil.rmtree(old_dir, ignore_errors=True)

    def _cleanup_temp(self, zip_path: Path) -> None:
        """清理压缩包与解压临时目录（不动暂存根目录上的新二进制）。"""
        try:
            zip_path.unlink(missing_ok=True)
        except OSError:
            pass
        for base in (DOWNLOAD_DIR, STAGING_DIR):
            for entry in base.glob("ffmpeg_pkg_*"):
                if entry.is_dir():
                    shutil.rmtree(entry, ignore_errors=True)


# 全局单例
ffmpeg_updater = FFmpegUpdater()
