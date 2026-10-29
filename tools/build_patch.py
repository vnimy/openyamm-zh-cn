"""Build the Simplified Chinese tables for the OpenYAMM patch.

Sources, both extracted into the `corpus` directory by tools/extract_corpus.py:

* the localization LOD of the MMMerge build, which carries the full professional Chinese translation of the MM8
  tables (NPC dialogue, greetings, news, quests, scrolls, skills, spells, ...);
* the plain ZHCN_*.txt override tables of the same build, which carry names keyed by ID (items, monsters, maps,
  houses, place monsters, NPC names).

Both were exported for the engine's GBK renderer, so cells break across physical lines without quoting. The importer
rebuilds the logical records first, joins them to the OpenYAMM tables by ID, and writes every patched table back as
UTF-8 with properly quoted cells.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

sys.path.insert(0, str(Path(__file__).parent))

import texttable
import paths

# A record opens with its ID and a tab; a row without an ID starts with a tab (the header of the empty first column).
RECORD_START = re.compile(r"^(?:#|\d+|\t)")


@dataclass(frozen=True)
class ColumnMapping:
    """One target table fed from one source table.

    `columns` pairs target column indexes with the source column that replaces them. Rows join on `key`, the column
    holding the record ID; `key` is None when both tables share the record order.
    """

    source: str
    target: str
    columns: Sequence[Tuple[int, int]]
    key: Optional[int] = 0
    skip_header: int = 1


# The MM8 tables of the localization LOD, matched to the tables OpenYAMM keeps in data_tables.
TABLES: Sequence[ColumnMapping] = (
    ColumnMapping("Autonote.txt", "english/autonote.txt", ((1, 1),)),
    ColumnMapping("GAwards.txt", "english/awards.txt", ((1, 1),)),
    ColumnMapping("Global.txt", "english/Global.txt", ((1, 1),)),
    ColumnMapping("Quests.txt", "english/quests.txt", ((1, 1),)),
    ColumnMapping("Scroll.txt", "english/scroll.txt", ((1, 1),)),
    # The first column is the canonical English key the engine looks skills up by, so only the descriptions change.
    ColumnMapping("Skilldes.txt", "english/skill_des.txt", ((1, 1), (2, 2), (3, 3), (4, 4), (5, 5)), key=None),
    ColumnMapping("Spells.txt", "english/spells.txt",
                  ((2, 2), (4, 4), (5, 5), (6, 6), (7, 7), (8, 8), (9, 9), (10, 10))),
    # 1.17 的法术书读的是新表 data_tables/spells.txt（带法力/恢复列），旧表只是兼容副本，两张都要填。
    ColumnMapping("Spells.txt", "spells.txt",
                  ((2, 2), (4, 4), (5, 5), (6, 6), (7, 7), (8, 8), (9, 9), (10, 10))),
    ColumnMapping("stats.txt", "english/stats.txt", ((1, 1),), key=None),
    ColumnMapping("Trans.txt", "english/trans.txt", ((1, 1),)),
    ColumnMapping("MERCHANT.TXT", "english/merchant.txt", ((1, 1), (2, 2), (3, 3), (4, 4)), key=None),
    ColumnMapping("NPCData.txt", "npc.txt", ((1, 1),)),
    ColumnMapping("NPCGreet.txt", "npc_greet.txt", ((1, 1), (2, 2))),
    ColumnMapping("mYNPCTopic.txt", "npc_topic.txt", ((1, 1),)),
    ColumnMapping("NPCText.txt", "npc_topic_text.txt", ((1, 1),)),
    ColumnMapping("NPCNews.txt", "npc_news.txt", ((1, 1),)),
    ColumnMapping("history.txt", "english/history.txt", ((1, 1),)),
    ColumnMapping("MM7history.txt", "english/mm7_history.txt", ((1, 1),)),
    ColumnMapping("Class.txt", "english/class.txt", ((1, 1),), key=None),
)

# Names live in the override tables, keyed by the record ID of the table they translate.
NAME_TABLES: Sequence[Tuple[str, str, Sequence[Tuple[int, int]]]] = (
    # 第 16 列才是 Notes（描述），第 17 列是 package_id，写错会把包 id 覆盖成中文。
    ("ZHCN_ItemsTxt.txt", "items.txt", ((2, 1), (10, 2), (16, 3))),
    # 2D 事件表只换店主名与职称（「Caine, Blacksmith」→「凯恩·铁匠」）。店名（第 5 列）故意不动：
    # HouseInteraction 里有十来处拿英文屋名做判断（旅店、公会技能、Baa 神殿、地下城开场动画），
    # 改成中文会让这些逻辑失效；中文店名改从 ui_text.txt 走展示层覆盖，见 tools/make_house_names.py。
    ("ZHCN_2DEvents.txt", "house_data.txt", ((6, 2), (7, 3))),
)

# Ordered tables: the translation carries one row per record, in the same order, so it joins by position.
ORDERED_TABLES: Sequence[Tuple[str, str, Sequence[Tuple[int, int]]]] = (
    # NPC 随机人名：男/女两列，按行序对齐。
    ("ZHCN_NPCNames.txt", "npc_names.txt", ((0, 0), (1, 1))),
    # NPC 职业名（「某某 the Gambler」里的那半句），语料按记录 id 手写。
    ("npc_professions_zh.tsv", "npc_professions.txt", ((1, 1),)),
)

# Field patches replace only the name column of their target row.
FIELD_TABLES: Sequence[Tuple[str, str, int]] = (
    ("ZHCN_Monsters.txt", "monster_data.txt", 1),
    ("ZHCN_MapStats.txt", "map_stats.txt", 1),
    ("ZHCN_Placemon.txt", "english/place_mon.txt", 1),
)

# Tables whose cells hold several physical lines: the translated cell folds them into one, so the English tail has to go.
CONTINUATION_TABLES = {
    "npc_topic_text.txt",
    "npc_greet.txt",
    "npc_news.txt",
    "english/scroll.txt",
    "english/quests.txt",
}


def decode_source(raw: bytes) -> str:
    """The corpus is UTF-8; extract_corpus.py already translated the GBK escape scheme."""
    return raw.decode("utf-8", errors="replace")


def split_records(text: str) -> List[str]:
    """Group the physical lines of a translated table into its logical records."""
    blocks: List[str] = []
    current: List[str] = []

    for line in text.split("\n"):
        line = line.rstrip("\r")

        # The first line of a table is a header without an ID, so it opens its own record.
        if RECORD_START.match(line) or not current:
            if current:
                blocks.append("\n".join(current))
            current = [line]
            continue

        if current:
            current.append(line)

    if current:
        blocks.append("\n".join(current))

    return blocks


def split_cells(block: str) -> List[str]:
    """Split a record on tabs, keeping the newlines a cell may hold, and drop the export's quoting."""
    cells = block.split("\t")

    for index, cell in enumerate(cells):
        if len(cell) >= 2 and cell.startswith('"') and cell.endswith('"'):
            cells[index] = cell[1:-1].replace('""', '"')

    return cells


def read_target_rows(path: Path) -> List[List[str]]:
    """Read a table the way the engine reads it: quoted cells keep their newlines."""
    raw = path.read_bytes()

    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = raw.decode("cp1252")

    return texttable.parse(text)


def read_records(path: Path) -> Dict[str, List[str]]:
    """Index a translated table by record ID."""
    records: Dict[str, List[str]] = {}

    for block in split_records(decode_source(path.read_bytes())):
        cells = split_cells(block)
        key = cells[0].strip()

        if key and key not in records:
            records[key] = cells

    return records


def read_ordered_rows(path: Path) -> List[List[str]]:
    """Ordered tables keep one record per line and quote their long cells, so the strict parser is exact."""
    return texttable.parse(decode_source(path.read_bytes()))


def read_field_patch(path: Path) -> Dict[str, str]:
    """Read a MMMerge override table, which patches one field of a game table per row.

    The rows are `Table  Id  Field  New text`, and the table name is left empty once it repeats.
    """
    values: Dict[str, str] = {}
    table = ""

    for line in decode_source(path.read_bytes()).split("\n"):
        line = line.rstrip("\r")

        if not line:
            continue

        cells = line.split("\t")

        if len(cells) < 4 or cells[0] == "Table (of Game struct)":
            continue

        if cells[0].strip():
            table = cells[0].strip()

        given_id = cells[1].strip()

        if not given_id.isdigit():
            continue

        values.setdefault(given_id, clean_translation(cells[3]))

    return values


def read_simple_names(path: Path) -> Dict[str, List[str]]:
    """The override tables are plain TSV rows with the ID in the first column."""
    records: Dict[str, List[str]] = {}

    for line in decode_source(path.read_bytes()).split("\n"):
        line = line.rstrip("\r")

        if not line or line.startswith("#"):
            continue

        cells = line.split("\t")

        if not cells[0].strip():
            continue

        records[cells[0].strip()] = cells

    return records


def clean_translation(value: str) -> str:
    """Every translated cell is padded with a leading space by the GBK export."""
    return value.replace("\r", "").lstrip(" ")


CJK_TEXT = re.compile(r"[\u4e00-\u9fff]")
LATIN_TEXT = re.compile(r"[A-Za-z]")


def drop_translated_continuations(rows: List[List[str]]) -> int:
    """Remove the English tail of a record whose text the translation already folded in.

    The game's tables break a multi-line cell into one physical line per cell, and the MMMerge export joins those lines
    into a single translated cell. Without this pass the original second line survives as a stray record and the game
    prints it after the translated line ("嗯，我叫多丽丝。" followed by "Name's Doris.").
    """
    kept: List[List[str]] = []
    dropped = 0
    for row in rows:
        first = row[0].strip() if row else ""

        if first and not first.isdigit() and first != "#" and len(row) <= 2 and kept:
            previous = kept[-1]
            previous_is_record = bool(previous) and previous[0].strip().isdigit()
            previous_text = "\t".join(previous[1:])

            if previous_is_record and CJK_TEXT.search(previous_text) and LATIN_TEXT.search(first) \
                    and not CJK_TEXT.search("\t".join(row)):
                dropped += 1
                continue

        kept.append(row)

    rows[:] = kept
    return dropped


def build_quest_table(target_path: Path, source_path: Path, output_path: Path) -> Tuple[int, int]:
    """Fill english/quests.txt.

    The table is inconsistent about where a note's text lives: some records put it in "Quest Note Text" and leave
    "Notes" for the hint ("Given by Dadeross"), others leave "Quest Note Text" empty and keep the note in "Notes".
    The translation always carries the note text in its first column, so it goes into whichever column is in use.
    """
    records = read_records(source_path)
    rows = read_target_rows(target_path)
    translated = 0
    untouched = 0

    for row in rows[1:]:
        record = records.get(row[0].strip()) if row else None
        text = clean_translation(record[1]) if record is not None and len(record) > 1 else ""

        if not text:
            untouched += 1
            continue

        if len(row) > 1 and row[1].strip():
            row[1] = text
        elif len(row) > 2:
            row[2] = text
        else:
            untouched += 1
            continue

        translated += 1

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(texttable.serialize(rows), encoding="utf-8", newline="")
    return translated, untouched


def merge_rows(target_rows: List[List[str]], mapping: ColumnMapping, source_path: Path) -> Tuple[int, int]:
    """Replace the mapped cells of every target row whose ID the translation carries."""
    ordered = mapping.key is None
    records = {} if ordered else read_records(source_path)
    ordered_rows = read_ordered_rows(source_path) if ordered else []
    translated = 0
    untouched = 0

    for position, row in enumerate(target_rows):
        if position < mapping.skip_header:
            continue

        if ordered:
            # Both tables open with the same header row, so the record order carries over unchanged.
            source_row = ordered_rows[position] if position < len(ordered_rows) else None
        else:
            source_row = records.get(row[mapping.key].strip()) if mapping.key < len(row) else None

        if source_row is None:
            untouched += 1
            continue

        changed = False

        for target_column, source_column in mapping.columns:
            if target_column >= len(row) or source_column >= len(source_row):
                continue

            value = clean_translation(source_row[source_column])

            if value and value != row[target_column]:
                row[target_column] = value
                changed = True

        if changed:
            translated += 1
        else:
            untouched += 1

    return translated, untouched


def corpus_file(name: str, primary: Path) -> Path:
    """语料可能在 corpus/mmmerge（MMMerge 提取）或 corpus/overrides（本项目维护）下，两处都找。"""
    candidate = primary / name

    if candidate.exists():
        return candidate

    fallback = paths.OVERRIDES / name

    if fallback.exists():
        return fallback

    return candidate


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, default=paths.MMMERGE,
                        help="MMMerge 中文表目录（默认 corpus/mmmerge）")
    parser.add_argument("--openyamm", type=Path, required=True, help="OpenYAMM checkout")
    parser.add_argument("--out", type=Path, required=True, help="patch asset root (becomes the mod directory)")
    arguments = parser.parse_args()

    target_root = arguments.openyamm / "assets_dev/engine/data_tables"
    output_root = arguments.out / "engine/data_tables"
    report: List[str] = []

    for mapping in TABLES:
        source_path = corpus_file(mapping.source, arguments.corpus)

        if not source_path.exists():
            report.append(f"{mapping.target}: missing {mapping.source}")
            continue

        if mapping.target == "english/quests.txt":
            translated, untouched = build_quest_table(
                target_root / mapping.target, source_path, output_root / mapping.target)
            report.append(f"{mapping.target}: {translated} rows translated, {untouched} kept")
            continue

        rows = read_target_rows(target_root / mapping.target)
        translated, untouched = merge_rows(rows, mapping, source_path)
        dropped = drop_translated_continuations(rows) if mapping.target in CONTINUATION_TABLES else 0
        output_path = output_root / mapping.target
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(texttable.serialize(rows), encoding="utf-8", newline="")
        report.append(f"{mapping.target}: {translated} rows translated, {untouched} kept, {dropped} stray lines dropped")

    for source_name, target_name, columns in NAME_TABLES:
        source_path = corpus_file(source_name, arguments.corpus)

        if not source_path.exists():
            report.append(f"{target_name}: missing {source_name}")
            continue

        names = read_simple_names(source_path)
        rows = read_target_rows(target_root / target_name)
        replaced = 0

        for row in rows:
            source_row = names.get(row[0].strip()) if row else None

            if source_row is None:
                continue

            for target_column, source_column in columns:
                if target_column >= len(row) or source_column >= len(source_row):
                    continue

                value = clean_translation(source_row[source_column])

                if value:
                    row[target_column] = value
                    replaced += 1

        output_path = output_root / target_name
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(texttable.serialize(rows), encoding="utf-8", newline="")
        report.append(f"{target_name}: {replaced} cells from {source_name}")

    for source_name, target_name, columns in ORDERED_TABLES:
        source_path = corpus_file(source_name, arguments.corpus)

        if not source_path.exists():
            report.append(f"{target_name}: missing {source_name}")
            continue

        if source_name.endswith(".tsv"):
            # 手写语料：id 在第一列，其余列是译文。
            records = read_simple_names(source_path)
            rows = read_target_rows(target_root / target_name)
            replaced = 0

            for row in rows:
                source_row = records.get(row[0].strip()) if row else None

                if source_row is None:
                    continue

                for target_column, source_column in columns:
                    if target_column < len(row) and source_column < len(source_row) and source_row[source_column].strip():
                        row[target_column] = clean_translation(source_row[source_column])
                        replaced += 1

            output_path = output_root / target_name
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(texttable.serialize(rows), encoding="utf-8", newline="")
            report.append(f"{target_name}: {replaced} cells from {source_name}")
            continue

        source_rows = read_ordered_rows(source_path)
        rows = read_target_rows(target_root / target_name)
        replaced = 0

        for position, row in enumerate(rows):
            if position == 0 or position >= len(source_rows):
                continue

            source_row = source_rows[position]

            for target_column, source_column in columns:
                if target_column >= len(row) or source_column >= len(source_row):
                    continue

                value = clean_translation(source_row[source_column])

                if value:
                    row[target_column] = value
                    replaced += 1

        output_path = output_root / target_name
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(texttable.serialize(rows), encoding="utf-8", newline="")
        report.append(f"{target_name}: {replaced} cells from {source_name}")

    for source_name, target_name, column in FIELD_TABLES:
        source_path = corpus_file(source_name, arguments.corpus)

        if not source_path.exists():
            report.append(f"{target_name}: missing {source_name}")
            continue

        names = read_field_patch(source_path)
        rows = read_target_rows(target_root / target_name)
        replaced = 0

        for row in rows:
            value = names.get(row[0].strip()) if row else None

            if value and column < len(row):
                row[column] = value
                replaced += 1

        output_path = output_root / target_name
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(texttable.serialize(rows), encoding="utf-8", newline="")
        report.append(f"{target_name}: {replaced} names from {source_name}")

    # 菜单 UI 覆盖表：make_ui_text.py 的产物，引擎 game/ui 层按原文整串/前缀替换。
    ui_text_path = paths.OVERRIDES / "ui_text.txt"
    if ui_text_path.exists():
        output_path = output_root / "english/ui_text.txt"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(ui_text_path.read_text(encoding="utf-8"), encoding="utf-8", newline="")
        entries = sum(1 for line in ui_text_path.read_text(encoding="utf-8").splitlines()
                      if line.strip() and not line.startswith("#"))
        report.append(f"english/ui_text.txt: {entries} entries")
    else:
        report.append("english/ui_text.txt: missing corpus/overrides/ui_text.txt (run tools/make_ui_text.py)")

    # 角色创建界面的随机名池：引擎读 english/pc_names.txt，按职业/性别分 8 列。
    import make_pc_names

    pc_names_path = output_root / "english/pc_names.txt"
    pc_names_path.parent.mkdir(parents=True, exist_ok=True)
    pc_names_path.write_text(make_pc_names.build_text(), encoding="utf-8", newline="")
    report.append(f"english/pc_names.txt: {make_pc_names.total_names()} names in {len(make_pc_names.HEADER)} columns")

    print("\n".join(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
