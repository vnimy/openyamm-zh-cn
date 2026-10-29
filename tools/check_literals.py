#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""扫描引擎源码里的界面文案字面量，报告覆盖表（corpus/ui_text.txt）里还缺哪些。

汉化最容易漏的是「界面文案」，而它们散落在 `game/ui/`、`game/gameplay/`、`game/events/`
各处传给文本绘制函数的字符串字面量里。与其一个个界面截图核对，不如把源码里的候选串全捞出来
和覆盖表对一遍——本项目能在不上游戏的情况下清掉绝大部分界面，靠的就是这个脚本。

判定「像界面文案」的规则（宁缺勿滥，噪声太大会淹没真正的问题）：

- 至少两个「词」，且含空格；
- 只由可见 ASCII 构成；
- 不以 `/`、`\\`、`:` 结尾，不像资源路径、键名、格式化模板 id；
- 不是纯大写常量名（含下划线且全大写）；
- 长度 >= 4。

用法：

    python tools/check_literals.py                          # 扫默认范围
    python tools/check_literals.py --files game/ui/screens/NewGameScreen.cpp
    python tools/check_literals.py --all --show 200         # 连日志/控制台一起列
    python tools/check_literals.py --write build/literals_missing.txt

返回值：发现缺口时退出码为 1，方便当检查项用（加 `--allow-missing` 可关掉）。
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import paths

# 默认关注范围：玩家能看见文字的界面与交互逻辑。
DEFAULT_GLOBS = (
	"game/ui/*.cpp",
	"game/ui/screens/*.cpp",
	"game/gameplay/*.cpp",
	"game/events/EventDialogContent.cpp",
	"game/app/*.cpp",
)

# 纯开发/日志用途的文件，里面的字符串不会画到界面上。
EXCLUDED_FILES = {
	"main.cpp",
	"ContentSetup.cpp",
	"GameUpdater.cpp",
	"GameSettings.cpp",
	"ActorBehaviorCatalog.cpp",
	"TurnBasedCombatRuntime.cpp",
	# 控制台帮助文本有几百条，扫进来只会淹没真正的缺口。
	"GameApplication.cpp",
}

# 出现这些调用的行，字符串是控制台/日志输出，不是界面文案。
LOG_MARKERS = (
	"std::cout",
	"std::cerr",
	"std::clog",
	"scenarioLog",
	"GameplayDebugTrace",
	"trace(",
	"logInfo",
	"logWarning",
	"logError",
	"#include",
)

LITERAL = re.compile(r'"((?:[^"\\]|\\.)*)"')

# 明显不是文案的形态
NOT_TEXT = re.compile(
	r"^(?:"
	r"[a-z0-9_]+(?:/[a-z0-9_.]+)+"          # 资源路径
	r"|[A-Z][A-Za-z0-9]*_[A-Za-z0-9_]+"      # 标识符
	r"|[A-Z_]{3,}"                           # 全大写常量
	r"|#[0-9a-fA-F]{3,8}"                    # 颜色
	r"|\{.*\}"                               # 占位符模板
	r")$"
)


def load_table(path: Path) -> dict:
	"""读覆盖表，返回「原文 -> 译文」。"""
	table: dict = {}
	for line in path.read_text(encoding="utf-8").splitlines():
		if not line or line.startswith("#") or "\t" not in line:
			continue
		key, value = line.split("\t", 1)
		table[key] = value
	return table


def is_ui_candidate(text: str) -> bool:
	if len(text) < 4 or " " not in text:
		return False
	if not text.isprintable():
		return False
	if any(character in text for character in "\t\r\n"):
		return False
	if NOT_TEXT.match(text):
		return False
	if text.startswith(("assets/", "engine/", "worlds/", "data_tables/")):
		return False
	# 至少有一个像英文单词的小写词
	if not re.search(r"\b[a-z]{2,}\b", text):
		return False
	if re.fullmatch(r"[\W_]+", text):
		return False
	return True


def prefix_hit(text: str, keys) -> bool:
	for key in keys:
		if key.endswith("*") and text.startswith(key[:-1]):
			return True
	return False


def main() -> int:
	parser = argparse.ArgumentParser(description=__doc__,
									 formatter_class=argparse.RawDescriptionHelpFormatter)
	parser.add_argument("--openyamm", type=Path, default=None, help="OpenYAMM 源码树（默认自动找）")
	parser.add_argument("--table", type=Path, default=paths.OVERRIDES / "ui_text.txt",
						help="覆盖表路径（默认 corpus/overrides/ui_text.txt）")
	parser.add_argument("--files", nargs="*", default=None, help="只查这些相对源码树的路径")
	parser.add_argument("--all", action="store_true", help="不过滤日志/控制台输出")
	parser.add_argument("--show", type=int, default=40, help="最多列出多少条缺口（0 表示全部）")
	parser.add_argument("--write", type=Path, default=None, help="把缺口清单写到这个文件")
	parser.add_argument("--allow-missing", action="store_true", help="有缺口也返回 0（当报告用）")
	arguments = parser.parse_args()

	engine = paths.engine_source(arguments.openyamm)
	table = load_table(arguments.table)
	prefix_keys = [key for key in table if key.endswith("*")]

	if arguments.files:
		candidates = [engine / name for name in arguments.files]
	else:
		candidates = []
		for pattern in DEFAULT_GLOBS:
			candidates.extend(sorted(engine.glob(pattern)))

	gaps: dict = {}
	total = 0
	scanned = 0

	for path in candidates:
		if not path.is_file() or path.name in EXCLUDED_FILES:
			continue
		scanned += 1
		text = path.read_text(encoding="utf-8", errors="replace")
		# 相邻字面量拼接 "... " "..." 先合并
		joined = re.sub(r'"\s*\n\s*"', "", text)

		for match in LITERAL.finditer(joined):
			literal = match.group(1)
			if not is_ui_candidate(literal):
				continue
			if not arguments.all:
				line_start = joined.rfind("\n", 0, match.start()) + 1
				line_end = joined.find("\n", match.start())
				line = joined[line_start:line_end if line_end != -1 else len(joined)]
				if any(marker in line for marker in LOG_MARKERS):
					continue
			total += 1
			if literal in table or prefix_hit(literal, prefix_keys):
				continue
			gaps.setdefault(literal, set()).add(path.name)

	ordered = sorted(gaps.items(), key=lambda item: (-len(item[0]), item[0]))
	print(f"扫描 {scanned} 个文件，候选文案 {total} 条，未收录 {len(gaps)} 条")

	limit = len(ordered) if arguments.show == 0 else arguments.show
	for literal, files in ordered[:limit]:
		print(f"  [{','.join(sorted(files))}] {literal[:120]!r}")

	if arguments.write:
		arguments.write.parent.mkdir(parents=True, exist_ok=True)
		lines = [f"{literal}\t{','.join(sorted(files))}" for literal, files in ordered]
		arguments.write.write_text("\n".join(lines) + "\n", encoding="utf-8")
		print(f"清单已写到 {arguments.write}")

	if gaps and not arguments.allow_missing:
		return 1
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
