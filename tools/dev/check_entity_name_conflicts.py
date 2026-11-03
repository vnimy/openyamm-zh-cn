#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""找出「覆盖表把数据表已有的官方译名又翻了一遍、而且翻得不一样」的条目。

背景：法术名、技能名、怪物名这类实体名字来自**数据表**（官方简体语料已译）。
但代码里还有一批**硬编码的英文名**（队伍增益表、光环名、事件提示等），它们走
`UiText::translate()` 查覆盖表。如果覆盖表给同一个英文名配了另一种译法，
同一个东西就会在不同界面叫不同名字——「魔力神眼」↔「巫师之眼」、「圣灵佑佐」↔「祝福」。

这个脚本把「覆盖表的英文键」与「数据表里同名实体的官方译名」对起来比，不一致就报。
"""

from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

import paths  # noqa: E402

INSTALLED = Path(r"D:\Projects\MM678\game")


def load_overlay() -> dict[str, str]:
    overlay: dict[str, str] = {}
    path = paths.OVERRIDES / "ui_text.txt"
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#") or "\t" not in line:
            continue
        key, _, value = line.partition("\t")
        overlay.setdefault(key, value)
    return overlay


def pristine_tables() -> dict[str, str]:
    """英文原件：安装包的 engine.core（官方英文，未打补丁）。"""
    packs = sorted((INSTALLED / "assets/packs").glob("engine.core-*.zip"))
    if not packs:
        return {}
    with zipfile.ZipFile(packs[0]) as archive:
        return {
            name: archive.read(name).decode("utf-8", "replace")
            for name in archive.namelist()
            if name.startswith("data_tables/") and name.endswith(".txt")
        }


def patched(name: str) -> str:
    path = INSTALLED / "mods/engine" / name
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def rows(text: str) -> dict[int, list[str]]:
    out: dict[int, list[str]] = {}
    for line in text.splitlines():
        cells = line.split("\t")
        if cells and cells[0].strip().isdigit():
            out[int(cells[0])] = cells
    return out


def english_to_chinese(english_text: str, chinese_text: str, name_column: int) -> dict[str, str]:
    """按记录 id 把英文名对到官方中文名。"""
    english = rows(english_text)
    chinese = rows(chinese_text)
    mapping: dict[str, str] = {}
    for record_id, english_row in english.items():
        chinese_row = chinese.get(record_id)
        if chinese_row is None or name_column >= len(english_row) or name_column >= len(chinese_row):
            continue
        english_name = english_row[name_column].strip().strip('"')
        chinese_name = chinese_row[name_column].strip().strip('"')
        if english_name and chinese_name and english_name != chinese_name:
            mapping.setdefault(english_name, chinese_name)
    return mapping


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--show", type=int, default=40, help="最多显示多少条（0 = 全部）")
    arguments = parser.parse_args()

    overlay = load_overlay()
    packs = pristine_tables()
    if not packs:
        print("找不到官方英文数据表（安装包的 engine.core），无法比对")
        return 2

    # 参与比对的实体：表名 -> 名称所在列
    entities = {
        "data_tables/english/spells.txt": 2,
        "data_tables/spells.txt": 2,
        "data_tables/monster_data.txt": 1,
        "data_tables/english/class.txt": 1,
    }

    conflicts: list[tuple[str, str, str, str]] = []
    for name, column in entities.items():
        if name not in packs:
            continue
        mapping = english_to_chinese(packs[name], patched(name), column)
        for english_name, official in mapping.items():
            override = overlay.get(english_name)
            if override is None:
                continue
            if override != official:
                conflicts.append((name.split("/")[-1], english_name, official, override))

    print(f"覆盖表 {len(overlay)} 条；比对了 {len(entities)} 张实体表")
    print(f"「覆盖表译法」与「数据表官方译名」不一致：{len(conflicts)} 条")

    count = len(conflicts) if arguments.show == 0 else min(arguments.show, len(conflicts))
    if conflicts:
        print(f"\n== 冲突（显示 {count} / {len(conflicts)}）")
        for table, english, official, override in conflicts[:count]:
            print(f"   {english!r:28} 官方={official!r:12} 覆盖表={override!r:12} [{table}]")

    return 0 if not conflicts else 1


if __name__ == "__main__":
    raise SystemExit(main())
