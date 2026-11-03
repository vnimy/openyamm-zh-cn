#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""汉化机制性检查：把「会反复出现」的四类漏译做成可阻断的验收项。

背景：用户反馈的漏译不是零散个例，而是四类结构性根因（见 docs/translation-principles.md）：

  A 占位符未译   translateTemplate 的占位符实参本身没过 UiText（「把 Bow 提升为 Expert」）
  B 裸拼英文     UI 文本在 C++ 里裸拼、整句没过 UiText（旅行确认框、拾取提示）
  C 缺译文       UiText::translate 用到的字面量在覆盖表里没有条目
  D 半拼接       只包了前缀（UiText::translate("前缀") + 变量），中英混排
  E 术语不一致   同一英文术语在不同地方译法不同（肢体魔法 / 身体魔法）

用法：
  python tools/dev/check_translation_rules.py            # 摘要
  python tools/dev/check_translation_rules.py --show 0   # 全部
返回码：0 = 全部通过；1 = 有阻断项。
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

import paths  # noqa: E402

CJK = re.compile(r"[\u4e00-\u9fff]")
LITERAL = re.compile(r'"((?:[^"\\]|\\.)*)"')
WORDY = re.compile(r"[A-Za-z]{2,}[ ,.'!?]*[A-Za-z]{2,}")
PLACEHOLDER = re.compile(r"\{([a-z_0-9]+)\}")
# 不算「玩家可见」的源文件
SKIP_FILES = {"ScenarioRunner.cpp", "DebugConsole.cpp", "HeadlessOutdoorDiagnostics.cpp"}
# 内部用途调用：日志、断言、脚本解析
SKIP_CALLS = ("GAMEPLAY_DEBUG_TRACE", "LOG_", "SPDLOG", "throw ", "assert(", "printf",
              "std::cerr", "std::cout", "debugTrace", "traceLog", "errorMessage",
              "expect", "yaml", "Yaml", "YAML")
# UI 输出型调用：这类行里的英文字面量必须过 UiText
UI_CALLS = ("setStatusBarEvent", "painter.text", "painter.label", ".label =", "displayText",
            "statusText", "setMessage", "lines.push_back", "messages.push_back")

# 术语表：英文 -> 官方标准译名（来自 mm678-i18n references/notes/zh/customlist.list）
GLOSSARY: Dict[str, str] = {
    # 技能
    "Staff": "手杖", "Sword": "长剑", "Dagger": "匕首", "Axe": "战斧", "Spear": "长矛",
    "Bow": "弓箭", "Mace": "钉锤", "Blaster": "榴弹枪", "Shield": "盾牌",
    "Leather Armor": "皮甲", "Chain Armor": "锁甲", "Plate Armor": "钢甲",
    "Fire Magic": "火系魔法", "Air Magic": "空气魔法", "Water Magic": "水系魔法",
    "Earth Magic": "土系魔法", "Spirit Magic": "灵魂魔法", "Mind Magic": "心智魔法",
    "Body Magic": "肢体魔法", "Light Magic": "光明魔法", "Dark Magic": "暗黑魔法",
    "Identify Item": "物品鉴定术", "Identify Monster": "怪物鉴定术", "Repair Item": "修补术",
    "Disarm Traps": "陷阱拆卸术", "Body Building": "健身术", "Bodybuilding": "健身术",
    "Meditation": "冥想术", "Perception": "洞察术", "Learning": "学习术", "Alchemy": "炼金术",
    "Armsmaster": "武器使用术", "Stealing": "偷窃术", "Dodging": "闪躲术",
    "Unarmed": "空手搏斗术", "Regeneration": "再生术", "Merchant": "经商术",
    "Dark Elf Ability": "黑暗精灵能力", "Vampire Ability": "吸血鬼能力", "Dragon Ability": "飞龙能力",
    # 属性
    "Might": "力量", "Intellect": "智力", "Personality": "个性", "Endurance": "耐力",
    "Accuracy": "精确", "Speed": "速度", "Luck": "运气",
    "Hit Points": "生命值", "Spell Points": "魔法值", "Armor Class": "防御等级",
    "Skill Points": "技能点数",
    "Fire Resistance": "火系抗性", "Air Resistance": "风系抗性", "Water Resistance": "水系抗性",
    "Earth Resistance": "土系抗性", "Mind Resistance": "心系抗性", "Body Resistance": "体系抗性",
    # 职业
    "Master": "智者", "Expert": "专家", "Grand Master": "宗师",
}

# 术语「不应出现的变体」：中文写法 -> 正确写法
TERM_VARIANTS: Dict[str, str] = {
    "身体魔法": "肢体魔法", "肉体魔法": "肢体魔法", "躯干魔法": "肢体魔法",
    "身体抗性": "体系抗性", "肢体抗性": "体系抗性",
    "气系抗性": "风系抗性", "心智抗性": "心系抗性",
    "护甲等级": "防御等级",
}


def load_overlay() -> Dict[str, str]:
    overlay: Dict[str, str] = {}
    path = paths.OVERRIDES / "ui_text.txt"
    if not path.exists():
        return overlay
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#") or "\t" not in line:
            continue
        key, _, value = line.partition("\t")
        overlay.setdefault(key, value)
    return overlay


def source_files() -> List[Path]:
    root = paths.engine_source() / "game"
    if not root.exists():
        return []
    return [p for p in root.rglob("*.cpp") if p.name not in SKIP_FILES]


def is_internal(line: str) -> bool:
    stripped = line.strip()
    if stripped.startswith("//") or stripped.startswith("*"):
        return True
    return any(call in line for call in SKIP_CALLS)


# ---------------------------------------------------------------- A：占位符未译
def check_untranslated_placeholders(files: List[Path], overlay: Dict[str, str]) -> List[Tuple[str, str]]:
    """translateTemplate 的占位符实参若直接是英文名函数（masteryDisplayName / displaySkillName…）
    且没过 UiText，就会显示「把 Bow 提升为 Expert」。"""
    gaps: List[Tuple[str, str]] = []
    suspicious = re.compile(r'"\{(?:[a-z_0-9]+)\}",\s*([A-Za-z_][A-Za-z0-9_:<>()\[\].,\s]*)')
    display_call = re.compile(r"\b(displaySkillName|masteryDisplayName|displayClassName|localizedMasteryName)\s*\(")
    for path in files:
        text = path.read_text(encoding="utf-8", errors="replace")
        for lineno, line in enumerate(text.splitlines(), 1):
            if "translateTemplate" not in line:
                continue
            for match in suspicious.finditer(line):
                argument = match.group(1)
                call = display_call.search(argument)
                if call is None:
                    continue
                # localizedMasteryName 内部已走 UiText，是安全的
                if call.group(1) == "localizedMasteryName":
                    continue
                gaps.append((line.strip()[:130], f"{path.name}:{lineno}"))
    return gaps


# ---------------------------------------------------------------- B：裸拼英文
def looks_player_facing(literal: str) -> bool:
    if len(literal) < 8 or CJK.search(literal):
        return False
    if re.fullmatch(r"(?:\{[a-z_0-9]+\}[\s:/+~-]*)+", literal):
        return False
    if re.fullmatch(r"(?:[A-Z][a-z0-9]*){2,}", literal) or re.fullmatch(r"[a-z]+[A-Z][A-Za-z0-9]*", literal):
        return False
    if "/" in literal or "\\" in literal or re.search(r"\.(txt|yml|png|lua|json)$", literal):
        return False
    if not WORDY.search(literal):
        return False
    if re.fullmatch(r"[a-z_]+", literal):
        return False
    return True


def check_bare_english(files: List[Path]) -> List[Tuple[str, str]]:
    gaps: List[Tuple[str, str]] = []
    for path in files:
        text = path.read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines()
        for index, line in enumerate(lines):
            if is_internal(line) or not any(call in line for call in UI_CALLS):
                continue
            # 模板可能跨行：往前看三条已开启的语句，只要其中出现 UiText 调用就认为已包装。
            window = "\n".join(lines[max(0, index - 2):index + 1])
            if "UiText::translate" in window:
                continue
            for match in LITERAL.finditer(line):
                literal = match.group(1)
                if not looks_player_facing(literal):
                    continue
                gaps.append((literal[:110], f"{path.name}:{index + 1}"))
                break
    return gaps


# ---------------------------------------------------------------- C：覆盖表缺条目
def check_missing_overrides(files: List[Path], overlay: Dict[str, str]) -> List[Tuple[str, str]]:
    gaps: List[Tuple[str, str]] = []
    pattern = re.compile(r'UiText::(?:translate|translateTemplate)\(\s*"((?:[^"\\]|\\.)*)"')
    for path in files:
        text = path.read_text(encoding="utf-8", errors="replace")
        for lineno, line in enumerate(text.splitlines(), 1):
            for match in pattern.finditer(line):
                key = match.group(1)
                if key in overlay or not re.search(r"[A-Za-z]{2,}", key):
                    continue
                gaps.append((key[:110], f"{path.name}:{lineno}"))
    return gaps


# ---------------------------------------------------------------- D：半拼接
def check_half_split(files: List[Path]) -> List[Tuple[str, str]]:
    gaps: List[Tuple[str, str]] = []
    pattern = re.compile(r'UiText::translate\(\s*"(?:[^"\\]|\\.)*"\s*\)\s*\+')
    for path in files:
        text = path.read_text(encoding="utf-8", errors="replace")
        for lineno, line in enumerate(text.splitlines(), 1):
            if pattern.search(line):
                gaps.append((line.strip()[:120], f"{path.name}:{lineno}"))
    return gaps



# ---------------------------------------------------------------- F：引号形态不匹配
def check_quoted_keys() -> List[Tuple[str, str]]:
    """引擎的 TextTable 会把整体被双引号包裹的单元格剥成不带引号的串。
    覆盖表的键若写成带引号的样子，运行时永远匹配不上——译文静默失效，
    典型症状是「装备特殊效果里的属性缩写仍是英文」。"""
    import glob
    import zipfile

    overlay = load_overlay()
    packs = sorted(paths.asset_packs(None).glob("engine.core-*.zip"))
    gaps: List[Tuple[str, str]] = []
    for pack in packs:
        with zipfile.ZipFile(pack) as archive:
            for name in archive.namelist():
                if not name.startswith("data_tables/") or not name.endswith(".txt"):
                    continue
                text = archive.read(name).decode("utf-8", "replace")
                for line in text.splitlines():
                    for cell in line.split("\t"):
                        cell = cell.strip()
                        if len(cell) < 8 or not cell.startswith('"') or not cell.endswith('"'):
                            continue
                        inner = cell[1:-1].strip()
                        # 键写成带引号、剥引号的形态却没有 -> 这条译文永远命中不了
                        if cell in overlay and inner not in overlay:
                            gaps.append((cell[:100], name))
            break  # engine.core 已含全部相关表
    return gaps

# ---------------------------------------------------------------- E：术语一致性
def check_terminology(overlay: Dict[str, str]) -> List[Tuple[str, str]]:
    gaps: List[Tuple[str, str]] = []
    for english, standard in GLOSSARY.items():
        current = overlay.get(english)
        if current is None:
            continue  # 缺条目由 C 类负责，这里只管「译得不一样」
        if current != standard:
            gaps.append((f"{english}：标准「{standard}」，实际「{current}」", "ui_text.txt"))
    for variant, standard in TERM_VARIANTS.items():
        for key, value in overlay.items():
            if variant in value:
                gaps.append((f"「{variant}」应为「{standard}」：{key[:50]}", "ui_text.txt"))
                break
    return gaps


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--show", type=int, default=8, help="每类最多显示多少条（0 = 全部）")
    arguments = parser.parse_args()

    overlay = load_overlay()
    files = source_files()
    if not files:
        print("找不到引擎源码树（tools/paths.py engine_source），跳过源码类检查")
    if not overlay:
        print("找不到覆盖表 corpus/overrides/ui_text.txt")

    report = {
        "A 占位符未译": check_untranslated_placeholders(files, overlay),
        "B 裸拼英文": check_bare_english(files),
        "C 覆盖表缺条目": check_missing_overrides(files, overlay),
        "D 半拼接（前缀已译、后半英文）": check_half_split(files),
        "E 术语不一致": check_terminology(overlay),
        "F 引号形态不匹配": check_quoted_keys(),
    }

    blocking = 0
    print(f"检查 {len(files)} 个源文件，覆盖表 {len(overlay)} 条")
    for label, items in report.items():
        print(f"  {label}: {len(items)}")
        blocking += len(items)
    print(f"合计阻断项 {blocking}")

    for label, items in report.items():
        if not items:
            continue
        count = len(items) if arguments.show == 0 else min(arguments.show, len(items))
        print(f"\n== {label}（{len(items)} 条，显示 {count}）")
        for text, where in items[:count]:
            print(f"   {text!r}  [{where}]")

    return 0 if blocking == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
