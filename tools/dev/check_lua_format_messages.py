#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查 lua 里用 `string.format` 拼出来的动态消息有没有译文。

`tools/make_lua_dialog.py` 只抓 `evt.SetMessage("字面量")` 这种写法。但内容包里还有一批：

    evt.SetMessage(string.format("This is %s, the month of %s.\\nJourney to the Shrine of %s ...",
                                 month, stat, map))

这些串在运行时才拼好，整句永远不在覆盖表里，只能：
  1. 把 `string.format` 的模板当成一条独立文案去翻（如果引擎在拼接前不经过 translate，则模板翻译无效）；
  2. 或者按变量取值枚举出所有最终句子（本仓库对「先知朝圣」用的就是这个办法：12 个月 × 固定句式）；
  3. 或者给引擎加一个「按模板匹配」的翻译层。

本脚本做两件事：
  * 列出所有 `SetMessage/SimpleMessage/StatusText(string.format(...))` 的模板串；
  * 标出哪些模板已经在覆盖表里、哪些没有。
"""

from __future__ import annotations

import argparse
import glob
import re
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

import paths  # noqa: E402

# 匹配 evt.SetMessage( string.format( "..." ,  ... ) )
FORMAT_CALL = re.compile(
    r"(?:evt\.)?(?:SetMessage|SimpleMessage|StatusText|Message)\s*\(\s*string\.format\s*\(\s*"
    r'"((?:[^"\\]|\\.)*)"',
    re.S)


def load_overlay() -> dict[str, str]:
    overlay: dict[str, str] = {}
    path = paths.OVERRIDES / "ui_text.txt"
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#") or "\t" not in line:
            continue
        key, _, value = line.partition("\t")
        overlay.setdefault(key, value)
    return overlay


def lua_sources() -> list[tuple[str, str]]:
    """(包内路径, 文本) —— 扫安装包里的 lua。"""
    packs = sorted(paths.asset_packs(None).glob("*.zip"))
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
    parser.add_argument("--show", type=int, default=30, help="最多显示多少条（0 = 全部）")
    arguments = parser.parse_args()

    overlay = load_overlay()
    sources = lua_sources()
    print(f"扫了 {len(sources)} 个 lua 文件，覆盖表 {len(overlay)} 条")

    found: list[tuple[str, str, bool]] = []
    seen: set[str] = set()
    for where, text in sources:
        for match in FORMAT_CALL.finditer(text):
            template = match.group(1)
            if template in seen:
                continue
            seen.add(template)
            # 覆盖表里存的是还原过 \n 的形态
            key = template.replace("\\n", "\n")
            found.append((where, template, key in overlay))

    missing = [item for item in found if not item[2]]
    print(f"string.format 模板 {len(found)} 条，其中覆盖表没有的 {len(missing)} 条")

    count = len(missing) if arguments.show == 0 else min(arguments.show, len(missing))
    if missing:
        print(f"\n== 未覆盖（显示 {count} / {len(missing)}）")
        for where, template, _ in missing[:count]:
            pack = where.split(":")[0]
            print(f"   [{pack}] {template[:110]!r}")

    return 0 if not missing else 1


if __name__ == "__main__":
    raise SystemExit(main())
