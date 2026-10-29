#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""体检 corpus/overrides 下的覆盖表：格式错误、重复键、空译文、编码损坏。

这些错误在游戏里表现为「某句话永远不翻译」或「整段界面错位」，而且很难靠肉眼发现——
表是几千行的纯文本，漏一个 tab 就和正常行长得差不多。

    python tools/check_tables.py
    python tools/check_tables.py --strict     # 有警告也返回非 0
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import paths

# 这些字符一旦出现，说明文件被别的编码写过一遍（编辑器存成 GBK 或 CP1252 的典型症状）。
SUSPECT = {
	"\ufffd": "UTF-8 解码失败的替换字符",
	"\x00": "NUL 字节",
}


def check_file(path: Path) -> tuple[list, list]:
	"""返回（错误, 警告）。"""
	errors: list = []
	warnings: list = []
	seen: dict = {}

	raw = path.read_bytes()

	if raw.startswith(b"\xef\xbb\xbf"):
		errors.append("文件带 UTF-8 BOM，引擎读第一行会多出空白")

	text = raw.decode("utf-8", "replace")

	for character, reason in SUSPECT.items():
		if character in text:
			errors.append(f"含有{reason}")

	lines = text.split("\n")

	if lines and lines[-1] == "":
		lines = lines[:-1]

	for number, line in enumerate(lines, start=1):
		if not line.strip():
			continue

		if line.startswith("#"):
			continue

		if "\t" not in line:
			errors.append(f"第 {number} 行没有 tab：{line[:60]!r}")
			continue

		key, value = line.split("\t", 1)

		if not key.strip():
			errors.append(f"第 {number} 行原文为空")
		if not value.strip():
			errors.append(f"第 {number} 行译文为空：{key[:60]!r}")
		if value.count("\t"):
			warnings.append(f"第 {number} 行译文里有 tab：{key[:40]!r}")

		# 键在文件内重复：后一条会覆盖前一条，多半是复制粘贴时忘了改原文。
		if key in seen:
			warnings.append(f"第 {number} 行原文与第 {seen[key]} 行重复：{key[:60]!r}")
		else:
			seen[key] = number

		# 前缀规则必须放在精确键之后才不会被吃掉，这里只做形态提示。
		if key.endswith("*") and len(key) < 4:
			warnings.append(f"第 {number} 行前缀太短，容易误伤：{key!r}")

	return errors, warnings


def main() -> int:
	parser = argparse.ArgumentParser(description=__doc__,
									 formatter_class=argparse.RawDescriptionHelpFormatter)
	parser.add_argument("--dir", type=Path, default=paths.OVERRIDES, help="要检查的目录")
	parser.add_argument("--strict", action="store_true", help="有警告也返回非 0")
	arguments = parser.parse_args()

	total_errors = 0
	total_warnings = 0
	checked = 0

	for path in sorted(arguments.dir.glob("*")):
		if not path.is_file() or path.suffix not in (".txt", ".tsv"):
			continue

		checked += 1
		errors, warnings = check_file(path)
		total_errors += len(errors)
		total_warnings += len(warnings)

		status = "ok" if not errors and not warnings else ("错误" if errors else "警告")
		print(f"{path.name}: {status}（错误 {len(errors)}，警告 {len(warnings)}）")

		for message in errors[:20]:
			print(f"    ! {message}")
		for message in warnings[:10]:
			print(f"    ? {message}")

		if len(errors) > 20:
			print(f"    ... 还有 {len(errors) - 20} 条错误")

		if len(warnings) > 10:
			print(f"    ... 还有 {len(warnings) - 10} 条警告")

	print(f"\n检查 {checked} 个文件：错误 {total_errors}，警告 {total_warnings}")

	if total_errors:
		return 1
	if arguments.strict and total_warnings:
		return 1
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
