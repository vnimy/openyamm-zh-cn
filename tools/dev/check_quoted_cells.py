#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查「引擎读表会剥引号、覆盖表键带引号」导致整类译文失效的问题。

引擎的 engine/TextTable.cpp `parseTabSeparated()` 会把**整体被双引号包裹**的单元格
剥成不带引号的串。所以：
  * 覆盖表的键必须写成剥掉引号后的形态，否则永远匹配不上（整条译文静默失效）；
  * 反过来，如果某些表/某些路径不剥引号，键就得带引号。

这个脚本扫所有数据表，找出「被引号包裹的单元格」，逐一检查覆盖表里对应的键对不对得上。
"""

from __future__ import annotations

import argparse
import glob
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

import paths  # noqa: E402

CJK = __import__("re").compile(r"[\u4e00-\u9fff]")


def load_overlay() -> dict[str, str]:
    overlay: dict[str, str] = {}
    path = paths.OVERRIDES / "ui_text.txt"
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#") or "\t" not in line:
            continue
        key, _, value = line.partition("\t")
        overlay.setdefault(key, value)
    return overlay


def engine_packs() -> list[Path]:
    packs = paths.asset_packs(None)
    return sorted(packs.glob("*.zip"))


def quoted_cells() -> dict[str, list[str]]:
    """返回 {带引号原文: [来源文件...]}，只看含拉丁字母、长度足够的单元格。"""
    found: dict[str, list[str]] = {}
    for pack in engine_packs():
        with zipfile.ZipFile(pack) as archive:
            for name in archive.namelist():
                if not name.startswith("data_tables/") or not name.endswith(".txt"):
                    continue
                text = archive.read(name).decode("utf-8", "replace")
                for line in text.splitlines():
                    for cell in line.split("\t"):
                        cell = cell.strip()
                        if len(cell) < 4 or not cell.startswith('"') or not cell.endswith('"'):
                            continue
                        if CJK.search(cell):
                            continue
                        found.setdefault(cell, []).append(name)
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--show", type=int, default=20, help="最多显示多少条（0 = 全部）")
    arguments = parser.parse_args()

    overlay = load_overlay()
    cells = quoted_cells()
    print(f"资产包里被引号包裹的单元格 {len(cells)} 个（去重）")

    # 只看「值得翻译」的：含空格或逗号、像个句子/清单的
    wrong: list[tuple[str, str]] = []
    missing: list[tuple[str, str]] = []
    for cell, sources in sorted(cells.items()):
        inner = cell[1:-1].strip()
        if len(inner) < 8:
            continue
        has_inner = inner in overlay
        has_quoted = cell in overlay
        if has_quoted and not has_inner:
            wrong.append((cell, sources[0]))
        elif not has_inner and not has_quoted:
            missing.append((cell, sources[0]))

    print(f"  键写成带引号（永远匹配不上）：{len(wrong)}")
    print(f"  完全没有译文：{len(missing)}")

    if wrong:
        count = len(wrong) if arguments.show == 0 else min(arguments.show, len(wrong))
        print(f"\n== 引号导致失效（{len(wrong)}，显示 {count}）")
        for cell, source in wrong[:count]:
            print(f"   {cell[:100]!r}  [{source}]")

    if missing:
        count = len(missing) if arguments.show == 0 else min(arguments.show, len(missing))
        print(f"\n== 缺译文（{len(missing)}，显示 {count}）")
        for cell, source in missing[:count]:
            print(f"   {cell[:100]!r}  [{source}]")

    return 0 if not wrong else 1


if __name__ == "__main__":
    raise SystemExit(main())
