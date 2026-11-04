#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查内容包 lua 里所有「玩家可见的消息字面量」是否已被覆盖表收录。

**诊断用，未校准，不要接进出包阻断门禁。**
引擎的匹配规则还带引号归一与前缀规则，本脚本的归一化尚不能完全复刻，
会出现「覆盖表里明明有、这里报缺失」的误报。定位具体漏译时人工比对即可；
要真正固化，应让引擎在启动时导出「未命中字符串清单」再比对。


引擎在 `luaSetMessage` / `luaSimpleMessage` / `StatusText` 这一层把最终字符串交给
`UiText::translate()`。所以只要 lua 里出现了英文消息字面量而覆盖表没有对应条目，
屏幕上就是英文——「方尖碑密文」就是这么暴露出来的：

    evt.SetMessage("The surface of the obelisk is blood warm ... _t_staoi_on_oiz_")

这类串往往很长、藏在某张地图的 lua 里，人眼很难发现。本脚本把它们全部列出来并核对。
"""

from __future__ import annotations

import argparse
import re
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

import paths  # noqa: E402

CJK = re.compile(r"[\u4e00-\u9fff]")
# evt.SetMessage("...") / evt.SimpleMessage("...") / evt.StatusText("...") / evt.Message("...")
MESSAGE_CALL = re.compile(
    r'(?:evt\.)?(?:SetMessage|SimpleMessage|StatusText|Message)\s*\(\s*"((?:[^"\\]|\\.)*)"',
    re.S)
# 只关心「像人话」的串：有 >=2 个英文单词
WORDY = re.compile(r"[A-Za-z]{2,}[ ,.'!?:;]*[A-Za-z]{2,}")


def normalize(text: str) -> str:
    """与引擎 UiText::normalizeQuotes 对齐的粗归一：弯引号/省略号/破折号统一成 ASCII。"""
    # 内容包里的 lua 混着 CP1252 单字节（0x85=…、0x91/0x92=’、0x96/0x97=–/—）。
    # 这里按 utf-8 解码时它们会变成 U+FFFD，所以把它和真正的省略号一起归一成 "..."。
    text = text.strip()
    return (text.replace("\u2019", "'").replace("\u2018", "'")
                .replace("\u201c", '"').replace("\u201d", '"')
                .replace("\u2026", "...").replace("\ufffd", "...")
                .replace("\u2013", "-").replace("\u2014", "-"))


def load_overlay() -> dict[str, str]:
    overlay: dict[str, str] = {}
    path = paths.OVERRIDES / "ui_text.txt"
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#") or "\t" not in line:
            continue
        key, _, value = line.partition("\t")
        overlay.setdefault(key, value)
    return overlay


def current_pack_files() -> list[str]:
    """当前目标版本的包文件名列表（来自 app/<ver>/index.json），避免扫到同目录下的旧版本包。"""
    import json

    installed = Path(r"D:\Projects\MM678\game")
    for version in ("1.20", "1.19"):
        index = installed / "app" / version / "index.json"
        if not index.exists():
            continue
        try:
            data = json.loads(index.read_text(encoding="utf-8"))
        except Exception:
            continue
        packs = data.get("packs")
        if isinstance(packs, list):
            return [entry.get("file", "") for entry in packs if entry.get("file")]
    return []


def lua_texts() -> list[tuple[str, str]]:
    wanted = set(current_pack_files())
    candidates = sorted(paths.asset_packs(None).glob("*.zip"))
    packs = [p for p in candidates if not wanted or p.name in wanted]
    out: list[tuple[str, str]] = []
    for pack in packs:
        with zipfile.ZipFile(pack) as archive:
            for name in archive.namelist():
                if not name.endswith(".lua"):
                    continue
                out.append((f"{pack.name}:{name}", archive.read(name).decode("utf-8", "replace")))
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--show", type=int, default=20, help="最多显示多少条（0 = 全部）")
    arguments = parser.parse_args()

    overlay = load_overlay()
    normalized_overlay = {normalize(key) for key in overlay}
    sources = lua_texts()
    print(f"扫了 {len(sources)} 个 lua 文件，覆盖表 {len(overlay)} 条")

    missing: list[tuple[str, str]] = []
    seen: set[str] = set()
    for where, text in sources:
        for match in MESSAGE_CALL.finditer(text):
            # 覆盖表把换行存成字面 \n，所以先用原始形态查一次，再退回还原换行的形态。
            raw = match.group(1)
            unescaped = (raw.replace("\\n", "\n")
                            .replace('\\"', '"')
                            .replace("\\'", "'"))
            if len(raw) < 8 or CJK.search(raw) or not WORDY.search(raw):
                continue
            if (raw in overlay or unescaped in overlay
                    or normalize(raw) in normalized_overlay
                    or normalize(unescaped) in normalized_overlay):
                continue
            if raw in seen:
                continue
            seen.add(raw)
            missing.append((where, raw))

    print(f"未覆盖的 lua 消息字面量：{len(missing)}")
    count = len(missing) if arguments.show == 0 else min(arguments.show, len(missing))
    for where, literal in missing[:count]:
        print(f"   [{where.split(':')[0]}] {literal[:110]!r}")

    return 0 if not missing else 1


if __name__ == "__main__":
    raise SystemExit(main())
