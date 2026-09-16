"""内置资源目录：字体、图片等。"""
import sys
from pathlib import Path

if getattr(sys, "frozen", False):
    # PyInstaller 冻结模式：资源在 _MEIPASS/app/resources/
    _BASE = Path(sys._MEIPASS) if hasattr(sys, "_MEIPASS") else Path(sys.executable).parent
    RES_DIR = _BASE / "app" / "resources"
else:
    RES_DIR = Path(__file__).resolve().parent

FONTS_DIR = RES_DIR / "fonts"
IMAGES_DIR = RES_DIR / "images"
