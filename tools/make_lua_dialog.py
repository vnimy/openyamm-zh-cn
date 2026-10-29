#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从内容包 lua 提取对话正文（evt.SetMessage 字面量），生成 UiText 覆盖表。

为什么要这一步：NPC 对话正文、事件提示并不在数据表里。OpenYAMM 把原版 EVT 导出成
events/Global.lua 与 events/maps/*.lua，正文以 ``evt.SetMessage("...")`` 的字符串字面量
硬编码在脚本里，所以改 npc_topic_text.txt 对画面上的对话内容毫无影响。
引擎侧已在 lua 绑定层（SetMessage / SimpleMessage / StatusText）过一遍 UiText，
因此这里只需要产出「原文<TAB>译文」。

译文来源：materials 里的 npc_topic_text 中英对照（MMerge 官方简中），按 id 对齐后成对取用。
同一个英文串在 lua 里和表里的写法常有出入（弯引号、0x91/0x92 原字节、引号重复），
所以匹配放宽，但**输出的键取 lua 原文归一后的形态**，保证运行时能张冠李戴地命中。
"""

from __future__ import annotations

import argparse
import glob
import os
import re
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import paths

def default_packs() -> str:
	"""资产包目录：环境变量优先，否则交给 paths 自动探测。"""
	explicit = os.environ.get("OPENYAMM_PACKS")
	try:
		return str(paths.asset_packs(explicit))
	except SystemExit:
		return explicit or ""


# 中英对照取自「已生成好的 npc_topic_text 表」，路径随构建目录走，不入库。
DEFAULT_TRANSLATED = str(paths.BUILD / "mods/engine/data_tables/npc_topic_text.txt")

# lua 里的字面量：SetMessage("...")，允许 \ 转义
SET_MESSAGE = re.compile(rb'SetMessage\(\s*"((?:[^"\\]|\\.)*)"')

_UNESCAPE = {
	b"n": b"\n",
	b"t": b"\t",
	b"r": b"\r",
	b'"': b'"',
	b"\\": b"\\",
}


def unescape_lua(raw: bytes) -> bytes:
	"""把 lua 字符串字面量还原成运行时字节序列。"""
	out = bytearray()
	index = 0
	while index < len(raw):
		if raw[index:index + 1] == b"\\" and index + 1 < len(raw):
			token = raw[index + 1:index + 2]
			out += _UNESCAPE.get(token, token)
			index += 2
			continue
		out += raw[index:index + 1]
		index += 1
	return bytes(out)


def normalize_quotes(raw: bytes) -> bytes:
	"""与引擎 UiText::normalizeQuotes 字节级一致的引号/CP1252 归一。

	合法 UTF-8 序列原样保留；形不成序列的孤立字节（内容包里常见的 0x91/0x92 弯引号、
	0x96/0x97 破折号、0x85 省略号、0xE9 重音字母）按 CP1252 还原成 UTF-8。
	"""
	out = bytearray()
	index = 0
	while index < len(raw):
		lead = raw[index]
		if lead < 0x80:
			out.append(lead)
			index += 1
			continue

		if lead & 0xE0 == 0xC0:
			length = 2
		elif lead & 0xF0 == 0xE0:
			length = 3
		elif lead & 0xF8 == 0xF0:
			length = 4
		else:
			length = 0
		valid = length > 0 and index + length <= len(raw)
		for offset in range(1, length):
			if not valid:
				break
			valid = raw[index + offset] & 0xC0 == 0x80
		if valid:
			out += raw[index:index + length]
			index += length
			continue

		if lead in (0x91, 0x92):
			out += b"'"
		elif lead in (0x93, 0x94):
			out += b'"'
		elif lead == 0x85:
			out += "\u2026".encode("utf-8")
		elif lead == 0x96:
			out += "\u2013".encode("utf-8")
		elif lead == 0x97:
			out += "\u2014".encode("utf-8")
		elif lead == 0xA0:
			out += b" "
		elif lead >= 0xA0:
			out += bytes((0xC0 | (lead >> 6), 0x80 | (lead & 0x3F)))
		# 0x80..0x9F 的 C1 控制字符直接丢掉。
		index += 1
	return bytes(out)


def loose_key(raw: bytes) -> bytes:
	"""只用于「找译文」的宽松形态：引号归一 + 重复引号折叠 + 空白压缩 + 去首尾引号。"""
	text = normalize_quotes(raw)
	text = text.replace(b'""', b'"')
	text = re.sub(rb"\s+", b" ", text)
	return text.strip().strip(b'"').strip()


def parse_topic_text(contents: bytes) -> dict:
	"""按引擎 NpcDialogTable::loadTextsFromRows 的规则解析话题正文表：首列数字开新条，否则续行。"""
	texts: dict[int, bytes] = {}
	pending_id = None
	pending = None
	for line in contents.split(b"\n"):
		if line.endswith(b"\r"):
			line = line[:-1]
		if not line:
			continue
		fields = line.split(b"\t")
		if fields[0].strip().isdigit():
			if pending_id is not None and pending is not None:
				texts[pending_id] = pending
			pending_id = int(fields[0])
			pending = fields[1] if len(fields) > 1 else b""
		elif pending is not None:
			pending += b"\n" + fields[0]
	if pending_id is not None and pending is not None:
		texts[pending_id] = pending
	return texts


def load_pairs(packs_dir: str, translated_path: str) -> tuple[dict, dict]:
	"""返回 (精确匹配表, 宽松匹配表)，都是 英文bytes -> 译文str。"""
	engine_core = sorted(glob.glob(os.path.join(packs_dir, "engine.core-*.zip")))
	if not engine_core:
		raise SystemExit(f"找不到 engine.core 包：{packs_dir}")
	with zipfile.ZipFile(engine_core[0]) as archive:
		original = archive.read("data_tables/npc_topic_text.txt")
	with open(translated_path, "rb") as handle:
		translated = handle.read()

	originals = parse_topic_text(original)
	chinese = parse_topic_text(translated)

	exact: dict[bytes, str] = {}
	loose: dict[bytes, str] = {}
	for text_id, english in originals.items():
		target = chinese.get(text_id)
		if not target:
			continue
		source = english.strip().strip(b'"').strip()
		target_text = target.strip().strip(b'"').strip()
		if not source or not target_text or source == target_text:
			continue
		try:
			chinese_text = target_text.decode("utf-8")
		except UnicodeDecodeError:
			continue
		exact.setdefault(source, chinese_text)
		loose.setdefault(loose_key(source), chinese_text)
	return exact, loose


def collect_literals(packs_dir: str) -> dict:
	"""扫描所有内容包 lua，收集 SetMessage 字面量及出现它的包名。"""
	found: dict[bytes, set] = {}
	for archive_path in sorted(glob.glob(os.path.join(packs_dir, "*.zip"))):
		pack = os.path.basename(archive_path).split("-")[0]
		with zipfile.ZipFile(archive_path) as archive:
			for name in archive.namelist():
				if not name.endswith(".lua"):
					continue
				contents = archive.read(name)
				for match in SET_MESSAGE.finditer(contents):
					literal = unescape_lua(match.group(1)).strip()
					if literal:
						found.setdefault(literal, set()).add(pack)
	return found


def escape_cell(raw: bytes) -> str | None:
	"""把字节串写成单行表格单元格：换行转义成 \\n；含制表符/反斜杠或非 UTF-8 时返回 None。

	引擎侧的 unescape 只认 \\n，其余反斜杠原样保留，所以带反斜杠的串一律跳过，
	免得写进去和读出来不是同一个字节序列。
	"""
	if b"\t" in raw or b"\\" in raw:
		return None
	try:
		text = raw.decode("utf-8")
	except UnicodeDecodeError:
		return None
	if text.startswith("#"):
		return None
	return text.replace("\n", "\\n")


def main() -> int:
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument("--packs", default=default_packs())
	parser.add_argument("--translated", default=DEFAULT_TRANSLATED)
	parser.add_argument("--out", default=str(paths.OVERRIDES / "lua_dialog_zh.tsv"))
	parser.add_argument("--missing", default=str(paths.REPORTS / "lua_dialog_missing.txt"))
	arguments = parser.parse_args()

	exact, loose = load_pairs(arguments.packs, arguments.translated)
	literals = collect_literals(arguments.packs)
	print(f"对照表：{len(exact)} 条精确 / {len(loose)} 条宽松")
	print(f"lua 对话字面量：{len(literals)} 条去重")

	rows: dict[str, str] = {}
	missing = []
	skipped = 0
	for literal, packs in literals.items():
		target = exact.get(literal)
		if target is None:
			target = loose.get(loose_key(literal))
		if target is None:
			missing.append((literal, packs))
			continue
		key = escape_cell(normalize_quotes(literal))
		value = escape_cell(target.encode("utf-8"))
		if key is None or value is None:
			skipped += 1
			continue
		rows[key] = value

	missing.sort(key=lambda item: -len(item[0]))
	lines = [
		"# 内容包 lua 里的对话正文（evt.SetMessage 字面量）覆盖表。",
		"# 由 tools/make_lua_dialog.py 生成，译文取自 npc_topic_text 中英对照，勿手工编辑。",
		"",
	]
	lines.extend(f"{key}\t{value}" for key, value in rows.items())
	with open(arguments.out, "w", encoding="utf-8", newline="\n") as handle:
		handle.write("\n".join(lines) + "\n")
	print(f"wrote {arguments.out} ({len(rows)} entries, {skipped} skipped)")

	with open(arguments.missing, "w", encoding="utf-8", newline="\n") as handle:
		for literal, packs in missing:
			handle.write(f"{','.join(sorted(packs))}\t{literal[:160]!r}\n")
	print(f"wrote {arguments.missing} ({len(missing)} untranslated)")
	return 0


if __name__ == "__main__":
	sys.exit(main())
