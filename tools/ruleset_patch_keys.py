"""把规则集补丁里按英文名定位的键改写成译文里的名字。

引擎应用规则集补丁时用 ruleset.yml 的 keyColumn 在目标表里找**唯一**一行
（ContentTableComposer 的 applyTableCellOverrides：一条匹配不上整份表就失败）。汉化把
data_tables/spells.txt 的名字列译成中文后，MAW 的 spells 补丁（188 条，全部按英文法术名
定位）一条也匹配不到，引擎于是放弃整份规则集——新游戏的起始大陆界面点了没反应
（NewGameScreen::selectContinent 加载失败后直接 return）。

这里按「英文名 → 记录 id → 译名」重写补丁的键列，列名与数值原样保留，产物写进补丁目录的
engine/rulesets/<id>/，构建时覆盖内容包里的同名文件。内容包本身不改：升级换包后重跑一次即可。

用法：
    python tools/ruleset_patch_keys.py --patch build/mods
    python tools/ruleset_patch_keys.py --patch build/mods --check

校验口径与引擎一致：补丁里每个键都必须在（翻译后的）目标表里恰好命中一行。英语原表里没有的
键（规则集自己 append 出来的行）不属于汉化的责任，跳过。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import paths

PATCH_HEADER = ["key", "column", "value"]
ROW_KEY = "row"


def decode(raw: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "cp1252"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def read_rows(text: str) -> List[List[str]]:
    rows: List[List[str]] = []

    for line in text.split("\n"):
        line = line.rstrip("\r")

        if line.strip():
            rows.append(line.split("\t"))

    return rows


def cell(row: Sequence[str], index: int) -> str:
    return row[index].strip() if 0 <= index < len(row) else ""


def game_root(explicit: Optional[str]) -> Path:
    return Path(explicit) if explicit else paths.REPO.parent / "game"


def release_dir(game: Path) -> Path:
    current = game / "app" / "current"

    if not current.is_file():
        raise SystemExit("找不到 " + str(current) + "，无法确定当前内容版本。")

    return game / "app" / current.read_text(encoding="utf-8").strip()


def pack_paths(game: Path) -> Dict[str, Path]:
    index = release_dir(game) / "index.json"

    if not index.is_file():
        raise SystemExit("找不到 " + str(index) + "。")

    manifest = json.loads(index.read_text(encoding="utf-8"))
    store = (index.parent / manifest.get("store", "../../assets/packs")).resolve()
    return {entry["id"]: store / entry["file"] for entry in manifest.get("packs", [])}


def ruleset_roots(archive: zipfile.ZipFile) -> Dict[str, str]:
    roots: Dict[str, str] = {}

    for name in archive.namelist():
        head, _, tail = name.partition("/")

        if tail == "ruleset.yml":
            roots[head] = head + "/"

    return roots


def parse_tables(ruleset_text: str) -> List[Dict[str, str]]:
    """只解析 ruleset.yml 的 tables 列表：每项是一张表的补丁说明。"""
    entries: List[Dict[str, str]] = []
    in_tables = False
    current: Optional[Dict[str, str]] = None

    for line in ruleset_text.split("\n"):
        stripped = line.strip()

        if not stripped or stripped.startswith("#"):
            continue

        if not line[:1].isspace():
            if current is not None:
                entries.append(current)
                current = None

            in_tables = stripped.split(":", 1)[0] == "tables"
            continue

        if not in_tables:
            continue

        item = re.match(r"^\s+-\s+([A-Za-z]+):\s*(.+?)\s*$", line)

        if item:
            if current is not None:
                entries.append(current)

            current = {item.group(1): item.group(2)}
            continue

        field = re.match(r"^\s+([A-Za-z]+):\s*(.+?)\s*$", line)

        if field and current is not None:
            current[field.group(1)] = field.group(2)

    if current is not None:
        entries.append(current)

    return entries


def key_column(entry: Dict[str, str]) -> Optional[int]:
    value = entry.get("keyColumn")

    if value is None or value.strip('"') == ROW_KEY:
        return None

    return int(value)


def header_row(entry: Dict[str, str]) -> int:
    return int(entry.get("headerRow", "0"))


def pack_table_text(packs: Dict[str, Path], core_id: str, table: str) -> Optional[str]:
    with zipfile.ZipFile(packs[core_id]) as archive:
        member = "data_tables/" + table

        if member not in archive.namelist():
            return None

        return decode(archive.read(member))


def renamed_keys(base_rows: List[List[str]], translated_rows: List[List[str]], column: int) -> Dict[str, str]:
    """英文键 → 译名；同一个英文名对上多个译名就放弃（引擎那边本来也定位不到）。"""
    english_by_id: Dict[str, str] = {}
    seen: Dict[str, str] = {}
    renamed: Dict[str, str] = {}

    for row in base_rows:
        if row:
            english_by_id.setdefault(cell(row, 0), cell(row, column))

    for row in translated_rows:
        if not row:
            continue

        chinese = cell(row, column)
        english = english_by_id.get(cell(row, 0))

        if not english or not chinese or english == chinese:
            continue

        previous = seen.get(english)

        if previous is not None and previous != chinese:
            renamed.pop(english, None)
            continue

        seen[english] = chinese
        renamed[english] = chinese

    return renamed


def rewrite_patch(patch_rows: List[List[str]], renamed: Dict[str, str]) -> Tuple[List[List[str]], int]:
    rows = [list(row) for row in patch_rows]
    changed = 0

    for row in rows[1:]:
        if not row:
            continue

        translated = renamed.get(cell(row, 0))

        if translated is None:
            continue

        row[0] = translated
        changed += 1

    return rows, changed


def unmatched_keys(rows: List[List[str]], column: int, header: int, keys: Sequence[str]) -> List[str]:
    found: Dict[str, int] = {}

    for index, row in enumerate(rows):
        if index == header or not row:
            continue

        key = cell(row, column)
        found[key] = found.get(key, 0) + 1

    return [key for key in keys if found.get(key, 0) != 1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--patch", type=Path, default=paths.BUILD / "mods", help="汉化补丁目录（含 engine/data_tables）")
    parser.add_argument("--game", default=None, help="OpenYAMM 安装目录（默认 ../game）")
    parser.add_argument("--check", action="store_true", help="只校验补丁键能否命中，不写文件")
    arguments = parser.parse_args()

    game = game_root(arguments.game)
    packs = pack_paths(game)

    if "engine.core" not in packs or "engine.rulesets" not in packs:
        raise SystemExit("当前内容的 index.json 里没有 engine.core / engine.rulesets 包。")

    table_root = arguments.patch / "engine" / "data_tables"
    output_root = arguments.patch / "engine" / "rulesets"
    failures = 0
    rewritten = 0

    with zipfile.ZipFile(packs["engine.rulesets"]) as archive:
        for ruleset, root in sorted(ruleset_roots(archive).items()):
            for entry in parse_tables(decode(archive.read(root + "ruleset.yml"))):
                column = key_column(entry)
                path = entry.get("path", "")

                if column is None or not path.endswith(".txt") or entry.get("mode") != "override":
                    continue

                translated_path = table_root / entry["table"]

                if not translated_path.is_file():
                    continue

                base_text = pack_table_text(packs, "engine.core", entry["table"])

                if base_text is None:
                    continue

                base_rows = read_rows(base_text)
                translated_rows = read_rows(translated_path.read_text(encoding="utf-8"))
                patch_rows = read_rows(decode(archive.read(root + path)))

                if patch_rows[:1] != [PATCH_HEADER]:
                    raise SystemExit(path + " 不是 key/column/value 补丁表。")

                renamed = renamed_keys(base_rows, translated_rows, column)
                rows, changed = rewrite_patch(patch_rows, renamed)
                output_path = output_root / ruleset / path

                if arguments.check:
                    # 校验这次构建真正会被加载的那份文件：有本地化副本就用副本，否则是内容包里的原文件。
                    effective = read_rows(output_path.read_text(encoding="utf-8")) if output_path.is_file() else patch_rows
                    english_keys = {cell(row, column) for row in base_rows if row}
                    keys = [cell(row, 0) for row in effective[1:] if row and cell(row, 0) in english_keys]
                    missing = unmatched_keys(translated_rows, column, header_row(entry), keys)

                    if missing:
                        failures += len(missing)
                        print(f"{ruleset}/{path}: {len(missing)} 个键匹配不到，例如 {missing[:5]}")

                    continue

                if not changed:
                    if output_path.is_file():
                        output_path.unlink()
                        print(f"{ruleset}/{path}: 译文与原表一致，删掉多余的本地化副本")

                    continue

                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text("\n".join("\t".join(row) for row in rows) + "\n", encoding="utf-8", newline="")
                rewritten += changed
                print(f"{ruleset}/{path}: {changed} 个键改用译名 → {output_path}")

    if arguments.check:
        if failures:
            print(f"{failures} 个规则集补丁键匹配不到目标行。")
            return 1

        print("规则集补丁键全部命中。")
        return 0

    print(f"完成：改写 {rewritten} 个键，产物在 {output_root}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
