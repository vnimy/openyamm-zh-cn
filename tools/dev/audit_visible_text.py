#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""扫「玩家能在屏幕上看到的文本」里还残留的英文，作为汉化验收口径。

只判断最终产物：build/mods 下的数据表 + corpus/overrides/ui_text.txt（覆盖表）。
判断方式与引擎一致：
- 数据表文本本身就是中文（已合并语料）；
- 覆盖表按 UiText::translate 的规则（整串精确 → 引号归一 → `*` 前缀递归）命中。

覆盖范围（都是屏幕文本）：
  lua 消息      内容包 lua 的 SetMessage / SimpleMessage / StatusText 字面量
  世界对象      decoration_data.txt 的 Hint（指向树/石头时的提示）、lua RegisterEvent 事件名
  NPC 对话      npc_topic 话题名、npc_greet 招呼语、npc_topic_text 正文、npc_news 标题与正文
  NPC/房屋/地名/怪物名/任务     对应数据表的名称列
  UI 文案       源码里传给绘制函数的硬编码字符串（复用 tools/check_literals.py 的扫描结果）

用法：
  python tools/dev/audit_visible_text.py                # 汇总 + 每类前若干个缺口
  python tools/dev/audit_visible_text.py --show 0       # 打印全部缺口
  python tools/dev/audit_visible_text.py --json build/audit.json
返回码：0 = 没有非白名单缺口；1 = 仍有缺口。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import zipfile
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Set, Tuple

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

import paths  # noqa: E402
import texttable  # noqa: E402

CJK = re.compile(r"[\u4e00-\u9fff]")
LATIN_WORD = re.compile(r"[A-Za-z]{2,}")

# 已知的、不算「没汉化」的占位/内部文本：内部 key、未使用的表记录、测试占位名。
WHITELIST_EXACT: Set[str] = {
    "Placeholder",
    "PLACEHOLDER",
    "MMExt Placeholder",
    "Missing Text 133",
    "missing text 38",
    "missing text 42",
    "yes",
    "null",
    "pending",
    "test",
    "Hint",
    "A",
    "B",
    "C",
    "D",
    "E",
    "F",
    "G",
    "H",
    "I",
    "J",
    "K",
    "L",
    "M",
    "N",
    "O",
    "P",
    "NWC",
    "New World Computing",
    "Dimensional Travel",
    "Blackshire guard hostility fixup",
    "Silver Cove guard hostility fixup",
    "Castle Ironfist guard hostility fixup",
    "Misty Islands guard hostility fixup",
    "New Sorpigal guard hostility fixup",
    "dodging expert unused",
    "dodging master unused",
    "dodging gm unused",
    "unarmed expert unused",
    "unarmed master unused",
    "unarmed gm unused",
    "stealing expert unused",
    "stealing master unused",
    "stealing gm unused",
    "",
}

# 内部占位名（_misc191、quest item 600 之类）不是玩家文本。
WHITELIST_PATTERNS: Sequence[re.Pattern] = (
    re.compile(r"^_?[a-z_]+(/[a-z_]+)?\d*$"),          # _misc191、_potion/reagent 这类内部名
    re.compile(r"^(scroll|book|artifact) \d+$"),
    re.compile(r"^Random MapNPC \d+$"),
    re.compile(r"^Tell James you see this \d+$"),
    re.compile(r"^Item #$"),
    re.compile(r"^Q Bit$"),
    re.compile(r"^Placeholder Text$"),
)


def is_english(text: str) -> bool:
    text = text.strip()

    if not text or CJK.search(text):
        return False

    if not LATIN_WORD.search(text):
        return False

    if text in WHITELIST_EXACT:
        return False

    return not any(pattern.match(text) for pattern in WHITELIST_PATTERNS)


def unescape(text: str) -> str:
    return text.replace("\\n", "\n")


class Overlay:
    """UiText::translate 的 Python 镜像（整串 → 归一化 → 前缀递归）。"""

    def __init__(self, path: Path) -> None:
        self.exact: Dict[str, str] = {}
        self.prefix: List[Tuple[str, str]] = []

        for line in path.read_text(encoding="utf-8").splitlines():
            if not line or line[0] == "#" or "\t" not in line:
                continue
            key, value = line.split("\t", 1)
            key, value = unescape(key), unescape(value)
            if key.endswith("*"):
                self.prefix.append((key[:-1], value))
            else:
                self.exact[key] = value

        self.normalized = {normalize_quotes(key): value for key, value in self.exact.items()}

    def translate(self, text: str, depth: int = 0) -> str:
        found = self.exact.get(text)

        if found is not None:
            return found

        normalized = self.normalized.get(normalize_quotes(text))

        if normalized is not None:
            return normalized

        if depth < 3:
            for prefix, value in self.prefix:
                if text.startswith(prefix):
                    return value + self.translate(text[len(prefix):], depth + 1)

        return text

    def covered(self, text: str) -> bool:
        return bool(CJK.search(self.translate(text)))


def normalize_quotes(text: str) -> str:
    out = []
    index = 0
    while index < len(text):
        lead = ord(text[index])
        if lead < 0x80:
            out.append(text[index])
            index += 1
            continue
        length = 0
        if lead & 0xE0 == 0xC0:
            length = 2
        elif lead & 0xF0 == 0xE0:
            length = 3
        elif lead & 0xF8 == 0xF0:
            length = 4
        valid = length > 0 and index + length <= len(text)
        for offset in range(1, length):
            if not valid:
                break
            valid = (ord(text[index + offset]) & 0xC0) == 0x80
        if valid:
            out.append(text[index:index + length])
            index += length
            continue
        replacement = {
            0x91: "'", 0x92: "'", 0x93: '"', 0x94: '"',
            0x85: "\u2026", 0x96: "\u2013", 0x97: "\u2014", 0xA0: " ",
        }.get(lead)
        if replacement is not None:
            out.append(replacement)
        elif lead >= 0xA0:
            out.append(chr(lead))
        index += 1
    return "".join(out)


def read_table(path: Path) -> List[List[str]]:
    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = raw.decode("cp1252")
    return texttable.parse(text)


def load_overlay() -> Overlay:
    override = paths.OVERRIDES / "ui_text.txt"
    if not override.exists():
        raise SystemExit(f"缺少覆盖表 {override}，先跑 tools/make_ui_text.py")
    return Overlay(override)


def data_tables_root() -> Path:
    return Path(os.environ.get("ZHPATCH_MODS", paths.BUILD / "mods")) / "engine/data_tables"


def packs_root() -> Path:
    return paths.asset_packs()


def current_pack_files() -> Dict[str, Path]:
    """当前安装（app/current 的 index.json）实际挂载的包：pack id -> zip 路径。

    1.18 → 1.19 时 assets/packs 里会同时留着两代包，按文件名 glob 会读到旧的那份；
    以 index.json 为准才和游戏实际加载的内容一致。取不到时退回 glob。
    """
    root = packs_root()
    game_root = root.parent.parent
    current = ""
    try:
        current = (game_root / "app" / "current").read_text(encoding="utf-8").strip()
    except OSError:
        current = ""

    index_path = game_root / "app" / current / "index.json"
    files: Dict[str, Path] = {}
    if current and index_path.exists():
        try:
            index = json.loads(index_path.read_text(encoding="utf-8"))
            for pack in index.get("packs", []):
                pack_id = pack.get("id", "")
                file_name = pack.get("file", "")
                if pack_id and file_name and (root / file_name).exists():
                    files[pack_id] = root / file_name
        except (ValueError, OSError):
            files = {}

    if files:
        return files

    for archive_path in sorted(root.glob("*.zip")):
        pack_id = archive_path.name.split("-")[0]
        files.setdefault(pack_id, archive_path)
    return files


def gather_lua_messages(overlay: Overlay) -> List[Tuple[str, str]]:
    found: Dict[str, str] = {}
    pattern = re.compile(rb'(SetMessage|SimpleMessage|StatusText)\(\s*"((?:[^"\\]|\\.)*)"')
    unescape_map = {b"n": b"\n", b"t": b"\t", b"r": b"\r", b'"': b'"', b"\\": b"\\"}

    pack_files = current_pack_files()
    for pack_id in ("engine.core", "mm6.core", "mm7.core", "mm8.core"):
        archive_path = pack_files.get(pack_id)
        if archive_path is None or not archive_path.exists():
            continue
        with zipfile.ZipFile(archive_path) as archive:
            for name in archive.namelist():
                if not name.endswith(".lua"):
                    continue
                data = archive.read(name)
                for match in pattern.finditer(data):
                    raw = bytearray()
                    index = 0
                    literal = match.group(2)
                    while index < len(literal):
                        if literal[index:index + 1] == b"\\" and index + 1 < len(literal):
                            raw += unescape_map.get(literal[index + 1:index + 2], literal[index + 1:index + 2])
                            index += 2
                            continue
                        raw += literal[index:index + 1]
                        index += 1
                    try:
                        text = bytes(raw).decode("utf-8").strip()
                    except UnicodeDecodeError:
                        continue
                    if text and not overlay.covered(text):
                        found.setdefault(text, f"{pack_id}:{name}")

    return [(text, where) for text, where in found.items() if is_english(text)]


def gather_decoration_hints(overlay: Overlay) -> List[Tuple[str, str]]:
    hints: Dict[str, str] = {}
    core = current_pack_files().get("engine.core")
    if core is None or not core.exists():
        return []
    with zipfile.ZipFile(core) as archive:
        text = archive.read("data_tables/decoration_data.txt").decode("utf-8", "replace")
    for line in text.splitlines()[1:]:
        cells = line.split("\t")
        if len(cells) > 2:
            hint = cells[2].strip()
            if hint and hint != "0":
                hints.setdefault(hint, f"decoration {cells[1].strip()}")
    return [(hint, where) for hint, where in hints.items() if is_english(hint) and not overlay.covered(hint)]


def gather_event_names(overlay: Overlay) -> List[Tuple[str, str]]:
    names: Dict[str, str] = {}
    pattern = re.compile(r'RegisterEvent\(\s*\d+\s*,\s*"((?:[^"\\]|\\.)*)"')
    pack_files = current_pack_files()
    for pack_id in ("engine.core", "mm6.core", "mm7.core", "mm8.core"):
        archive_path = pack_files.get(pack_id)
        if archive_path is None or not archive_path.exists():
            continue
        with zipfile.ZipFile(archive_path) as archive:
            for name in archive.namelist():
                if not name.endswith(".lua"):
                    continue
                text = archive.read(name).decode("utf-8", "replace")
                for match in pattern.finditer(text):
                    value = match.group(1).replace('\\"', '"').replace("\\\\", "\\")
                    if value:
                        names.setdefault(value, f"{pack_id}:{name}")
    return [(name, where) for name, where in names.items() if is_english(name) and not overlay.covered(name)]


def gather_tables(overlay: Overlay) -> Dict[str, List[Tuple[str, str]]]:
    root = data_tables_root()
    result: Dict[str, List[Tuple[str, str]]] = {}

    def check(name: str, label: str, columns: Sequence[int], id_column: int = 0) -> None:
        path = root / name
        if not path.exists():
            result[label] = [(f"<缺少 {name}>", str(path))]
            return
        rows = read_table(path)
        missing: List[Tuple[str, str]] = []
        for row in rows[1:]:
            record_id = row[id_column].strip() if id_column < len(row) else ""
            if not record_id.isdigit():
                continue
            for column in columns:
                if column < len(row):
                    value = row[column]
                    if is_english(value) and not overlay.covered(value):
                        missing.append((value.strip(), f"{name}#{record_id}"))
        result[label] = missing

    check("npc_topic.txt", "NPC 话题名", [1])
    check("npc_greet.txt", "NPC 招呼语", [1, 2])
    check("npc_topic_text.txt", "NPC 对话正文", [1])
    check("npc_news.txt", "酒馆传闻", [1, 2])
    check("npc.txt", "NPC 名字", [1])
    check("npc_professions.txt", "NPC 职业", [1])
    check("house_data.txt", "房屋名/店主", [5, 6, 7])
    check("map_stats.txt", "地图名", [1])
    check("monster_data.txt", "怪物名", [1])
    check("english/quests.txt", "任务日志", [1])
    check("english/autonote.txt", "自动笔记", [1])
    check("english/trans.txt", "传送点", [1])
    check("items.txt", "物品名", [2])

    return result


def gather_ui_literals(overlay: Overlay) -> List[Tuple[str, str]]:
    """复用 check_literals.py 的硬编码文案筛选规则，看覆盖表是否收录。"""
    sys.path.insert(0, str(REPO / "tools"))
    try:
        import check_literals
    except Exception:
        return []

    engine = paths.engine_source()
    candidates: List[Path] = []
    for pattern in check_literals.DEFAULT_GLOBS:
        candidates.extend(sorted(engine.glob(pattern)))

    gaps: Dict[str, str] = {}
    for path in candidates:
        if not path.is_file() or path.name in check_literals.EXCLUDED_FILES:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        joined = re.sub(r'"\s*\n\s*"', "", text)

        for match in check_literals.LITERAL.finditer(joined):
            literal = match.group(1)
            if not check_literals.is_ui_candidate(literal):
                continue
            line_start = joined.rfind("\n", 0, match.start()) + 1
            line_end = joined.find("\n", match.start())
            line = joined[line_start:line_end if line_end != -1 else len(joined)]
            if any(marker in line for marker in check_literals.LOG_MARKERS):
                continue
            if overlay.covered(literal):
                continue
            gaps.setdefault(literal, path.name)

    return sorted(gaps.items(), key=lambda item: (-len(item[0]), item[0]))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--show", type=int, default=12, help="每类最多打印多少条缺口（0 = 全部）")
    parser.add_argument("--json", type=Path, default=None, help="把结果写成 JSON")
    arguments = parser.parse_args()

    overlay = load_overlay()

    report: Dict[str, List[Tuple[str, str]]] = {}
    report["lua 消息"] = gather_lua_messages(overlay)
    report["世界对象装饰提示"] = gather_decoration_hints(overlay)
    report["世界对象事件名"] = gather_event_names(overlay)
    report.update(gather_tables(overlay))
    ui_gaps = gather_ui_literals(overlay)
    if ui_gaps:
        report["源码硬编码 UI"] = ui_gaps

    total = sum(len(items) for items in report.values())
    # 「源码硬编码 UI」含大量日志/拼接误报，只作参考，不计入验收失败条件；
    # 对话、NPC、房屋、世界对象与数据表缺口才是本脚本的判据。
    blocking = sum(len(items) for label, items in report.items() if label != "源码硬编码 UI")
    print(f"覆盖表 {paths.OVERRIDES / 'ui_text.txt'}：{len(overlay.exact)} 条精确 + {len(overlay.prefix)} 条前缀")
    for label, items in report.items():
        print(f"  {label}: {len(items)}")
    print(f"合计 {total}（其中阻断性缺口 {blocking}；源码硬编码 UI 仅参考）")

    for label, items in report.items():
        if not items:
            continue
        count = len(items) if arguments.show == 0 else min(arguments.show, len(items))
        print(f"\n== {label}（{len(items)} 条，显示 {count}）")
        for text, where in items[:count]:
            print(f"   {text[:140]!r}  [{where}]")

    if arguments.json:
        arguments.json.parent.mkdir(parents=True, exist_ok=True)
        arguments.json.write_text(
            json.dumps({label: items for label, items in report.items()}, ensure_ascii=False, indent=1),
            encoding="utf-8")

    return 0 if blocking == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
