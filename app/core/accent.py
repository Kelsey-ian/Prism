# -*- coding: utf-8 -*-
"""读取 Windows 系统强调色并应用到 qfluentwidgets。"""
from __future__ import annotations

import ctypes
from typing import Optional

from PySide6.QtGui import QColor


def read_system_accent() -> Optional[QColor]:
    """通过 DwmGetColorizationColor 读取 Win10/11 系统强调色。失败时返回 None。"""
    try:
        dwmapi = ctypes.WinDLL("dwmapi")
        color = ctypes.c_uint32()
        opaque = ctypes.c_int()
        # DwmGetColorizationColor(DWORD *pcolorization, BOOL *pfOpaque)
        if dwmapi.DwmGetColorizationColor(ctypes.byref(color), ctypes.byref(opaque)):
            return None
        argb = color.value
        a = (argb >> 24) & 0xFF
        r = (argb >> 16) & 0xFF
        g = (argb >> 8) & 0xFF
        b = argb & 0xFF
        return QColor(r, g, b, a if a > 0 else 255)
    except (OSError, AttributeError):
        return None


def read_system_accent_registry() -> Optional[QColor]:
    """回退方案：读注册表 HKCU\\Software\\Microsoft\\Windows\\DWM\\ColorizationColor。"""
    try:
        import winreg
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\DWM"
        ) as key:
            value, _type = winreg.QueryValueEx(key, "ColorizationColor")
        argb = int(value)
        a = (argb >> 24) & 0xFF if argb > 0xFFFFFF else 255
        r = (argb >> 16) & 0xFF
        g = (argb >> 8) & 0xFF
        b = argb & 0xFF
        return QColor(r, g, b, a)
    except (OSError, ImportError):
        return None


def apply_accent_color(
    color: str | QColor | None = None,
    follow_system: bool = False,
) -> None:
    """应用强调色到 qfluentwidgets。"""
    from qfluentwidgets import setThemeColor

    if follow_system or color in (None, "system", ""):
        sys_color = read_system_accent() or read_system_accent_registry()
        if sys_color is not None:
            setThemeColor(sys_color, save=False, lazy=False)
        return
    if isinstance(color, str):
        color = QColor(color)
    if isinstance(color, QColor) and color.isValid():
        setThemeColor(color, save=False, lazy=False)
