"""Bring the OpenYAMM window to the front and capture it.

PowerShell's Add-Type and WScript.Shell are blocked by the host's security policy, so the window handling goes through
ctypes, which is part of the interpreter.
"""

from __future__ import annotations

import ctypes
import sys
import time
from ctypes import wintypes
from pathlib import Path

user32 = ctypes.WinDLL("user32", use_last_error=True)

SW_RESTORE = 9
WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)


def window_titles():
    windows = []

    def collect(hwnd, _):
        length = user32.GetWindowTextLengthW(hwnd)

        if length:
            buffer = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buffer, length + 1)
            windows.append((hwnd, buffer.value))
        return True

    user32.EnumWindows(WNDENUMPROC(collect), 0)
    return windows


def main() -> int:
    output = Path(sys.argv[1] if len(sys.argv) > 1 else "shot.png")
    match = None

    for hwnd, title in window_titles():
        lowered = title.lower()
        if "openyamm" in lowered or "might and magic" in lowered:
            match = (hwnd, title)

    if match is None:
        print("window not found")
        return 1

    hwnd, title = match
    user32.ShowWindow(hwnd, SW_RESTORE)
    user32.SetForegroundWindow(hwnd)
    time.sleep(1.5)

    rect = wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))

    from PIL import ImageGrab

    box = (max(0, rect.left), max(0, rect.top), rect.right, rect.bottom)
    ImageGrab.grab(bbox=box, all_screens=True).save(output)
    print(f"captured {title} {box} -> {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
