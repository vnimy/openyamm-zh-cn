#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查「已部署的数据表里还剩多少纯英文的记录」。

`audit_visible_text.py` 查的是覆盖表能不能命中；这个脚本查的是**数据表本身**
（`build/mods` 或已安装的 `game/mods`）——用官方语料补丁过的表本该是中文，
仍出现纯英文就说明那条记录语料里没有译文（或合并时没对上）。

输出按表分组，并区分：
  * 玩家可见（正文列）：需要补译
  * 内部/占位（Notes、缺文本占位、编辑器备注）：不算漏译
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

import paths  # noqa: E402

CJK = re.compile(r"[\u4e00-\u9fff]")
LATIN = re.compile(r"[A-Za-z]{3,}")

# 每条记录里「正文/名称」所在列（0 = id，跳过）。只查这些列。
TEXT_COLUMNS: dict[str, tuple[int, ...]] = {
    "english/autonote.txt": (1,),
    "english/awards.txt": (1,),
    "english/history.txt": (1,),
    "english/mm7_history.txt": (1,),
    "english/quests.txt": (1,),
    "english/scroll.txt": (1,),
    "english/trans.txt": (1,),
    "english/spells.txt": (2, 4, 5, 6, 7, 8, 9, 10),
    "spells.txt": (2, 4, 5, 6, 7, 8, 9, 10),
    "english/skill_des.txt": (1, 2, 3, 4, 5),
    "english/class.txt": (1,),
    "english/stats.txt": (1,),
    "english/merchant.txt": (1, 2, 3, 4),
    "npc_topic_text.txt": (1,),
    "npc_greet.txt": (1, 2),
    "npc_news.txt": (1,),
    "npc_topic.txt": (1,),
    "items.txt": (2, 10, 16),
    "monster_data.txt": (1,),
    "map_stats.txt": (1,),
}

# 占位/内部文本，不算漏译
PLACEHOLDER = re.compile(
    r"missing|placeholder|unused|todo|% craft|\bTBD\b|^\W*$", re.IGNORECASE)

# 表头行：这几张表的第一条记录是列名，不是内容
HEADER_CELLS = {
    "Autonote Text", "Class description", "Transition Description", "Description", "message text",
    "Quest Note Text", "Spell Description", "Map Stats", "Statistics Descriptions", "Stats Descriptions",
    "Not identified name", "Identify", "Notes / Topic", "Greeting 1", "Forward",
    "Fire Spells", "Air Spells", "Water Spells", "Earth Spells", "Spirit Spells", "Mind Spells",
    "Body Spells", "Light Spells", "Dark Spells", "Item#",
}

# 编辑器备注：地点/用途说明，游戏内不显示（scroll 的第 2 列、quests 的内部标注等）
EDITOR_NOTE = re.compile(
    r"^(Event,|Player Castle,|In Chest with|Message from .* to |Message Scroll Text\.|D8 Spiral|"
    r"III = 16|Tularean Caves$|Fort Riverstride$|Temple of Baa$|Bandit Caves$|Erathian Sewers$|"
    r"Mercenary Guild$|City of Steadwick\.$|Grand Temple of Light,|White Cliff Caves,|"
    r"Act \d (Good|Evil|Both)$|Put Text Here|Group \d+$|If you see this text tell James|"
    r"Greeting \d+$|Wizard Ambassador$|Necro Ambassador$|(Evil|Good) Arbiter$|"
    r"No Proving Grounds$|Short Name$|(Dark Elf|Vampire|Dragon) Abilities$)",
    re.IGNORECASE)


def load_table(path: Path) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        rows.append(line.split("\t"))
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--mods", type=Path, default=None,
                        help="mods 目录（默认 REPO/build/mods，回退到已安装的 game/mods/engine/data_tables）")
    parser.add_argument("--show", type=int, default=6, help="每表最多显示多少条")
    arguments = parser.parse_args()

    root = arguments.mods
    if root is None:
        candidate = REPO / "build/mods/engine/data_tables"
        installed = Path(r"D:\Projects\MM678\game/mods/engine/data_tables")
        root = candidate if candidate.exists() else installed
    print(f"检查目录 {root}")

    total_gaps = 0
    for name, columns in sorted(TEXT_COLUMNS.items()):
        path = root / name
        if not path.exists():
            continue
        rows = load_table(path)
        gaps: list[str] = []
        for row in rows:
            for column in columns:
                if column >= len(row):
                    continue
                cell = row[column].strip().strip('"')
                if len(cell) < 8 or CJK.search(cell) or not LATIN.search(cell):
                    continue
                if PLACEHOLDER.search(cell) or cell in HEADER_CELLS:
                    continue
                if EDITOR_NOTE.search(cell):
                    continue
                gaps.append(cell[:90])
                break
        if gaps:
            total_gaps += len(gaps)
            count = len(gaps) if arguments.show == 0 else min(arguments.show, len(gaps))
            print(f"\n{name}: {len(gaps)} 条纯英文正文")
            for text in gaps[:count]:
                print(f"   {text!r}")

    print(f"\n合计 {total_gaps} 条")
    return 0 if total_gaps == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
