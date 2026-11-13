"""Resolve the production Chinese font on Windows and macOS."""
from pathlib import Path


def chinese_font(bold=False):
    candidates = [
        'C:/Windows/Fonts/msyhbd.ttc' if bold else 'C:/Windows/Fonts/msyh.ttc',
        '/System/Library/Fonts/STHeiti Medium.ttc',
        '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return candidate
    raise FileNotFoundError('Install Microsoft YaHei or a Chinese Noto Sans font')
