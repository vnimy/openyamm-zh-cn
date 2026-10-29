#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把所有语料合成一张覆盖表 corpus/overrides/ui_text.txt。

引擎侧的 `UiText` 读这张表做「原文 → 译文」替换（整串精确、`*` 前缀、`{占位符}` 模板三种匹配），
所以它必须包含所有来源：人工翻译的界面文案、物品词缀、事件名、屋名、lua 对话正文。

合并顺序（后者覆盖前者，同名时以靠后的为准）：

1. `enchant_names_zh.tsv`   词缀——`Might`、`Fire Resistance` 同时也是属性界面的词条，以界面译法为准
2. `event_names_zh.tsv`     世界对象名（门、箱子、水池……）
3. `house_names.tsv`        屋名/店名——与事件名大量重叠（店铺名同时是门牌），以屋名为准
4. `lua_dialog_zh.tsv`      NPC 对话正文
5. `manual_zh.tsv`          人工逐条翻译的界面文案，优先级最高

用法：`python tools/make_ui_text.py`
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import paths

# 输出表头：解释格式，免得后来者以为可以直接敲真换行。
HEADER = (
	"# OpenYAMM 简体中文补丁：界面文案覆盖表（由 tools/make_ui_text.py 合成，勿手改）。",
	"# 格式：原文<TAB>译文；# 开头为注释；以 * 结尾的原文按前缀匹配；换行写作字面 \\n。",
	"# 要改译文请改 corpus/overrides/ 下对应的源表，然后重跑 make_ui_text.py。",
	"",
)


def load_tsv_pairs(file_name: str) -> list:
	"""读 corpus/overrides 下「原文<TAB>译文」的两列对照表，跳过注释与空行。"""
	path = paths.OVERRIDES / file_name

	if not path.exists():
		print(f"  跳过 {file_name}（不存在）")
		return []

	pairs = []

	for line in path.read_text(encoding="utf-8").splitlines():
		if not line or line.startswith("#") or "\t" not in line:
			continue

		source, target = line.split("\t", 1)
		pairs.append((source, target))

	return pairs


def load_enchant_names() -> list:
	"""物品词缀译名（tools/make_enchant_names.py 生成）。"""
	return load_tsv_pairs("enchant_names_zh.tsv")


def load_event_names() -> list:
	"""世界对象/事件名对照（tools/make_event_names.py 手写）：门、箱子、水池等 HUD 提示文本。"""
	return load_tsv_pairs("event_names_zh.tsv")


def load_house_names() -> list:
	"""房屋/店铺名对照（tools/make_house_names.py 生成）。"""
	return load_tsv_pairs("house_names.tsv")


def load_lua_dialog() -> list:
	"""内容包 lua 里的对话正文（tools/make_lua_dialog.py 生成）。

	NPC 对话内容不在数据表里，而是内容包导出脚本中的 evt.SetMessage 字面量；
	引擎在 lua 绑定层过一遍覆盖表，所以这些条目是对话正文汉化的唯一来源。
	"""
	return load_tsv_pairs("lua_dialog_zh.tsv")


def load_manual() -> list:
	"""人工逐条翻译的界面文案（这一份是手写的，其余都是生成的）。"""
	return load_tsv_pairs("manual_zh.tsv")


def escape_newlines(text: str) -> str:
	"""表是「一行一条」，原文/译文里的真换行一律写成 \\n，引擎读表时会还原（见 UiText.cpp）。"""
	return text.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "\\n")


def main() -> None:
	out = paths.OVERRIDES / "ui_text.txt"
	out.parent.mkdir(parents=True, exist_ok=True)

	entries = (
		load_enchant_names()
		+ load_event_names()
		+ load_house_names()
		+ load_lua_dialog()
		+ load_manual()
	)

	# 同一原文只在表里留一次。dict 保序，后面的赋值覆盖前面的值但不改变位置。
	unique = {source: target for source, target in entries}

	lines = list(HEADER)
	lines.extend(f"{escape_newlines(source)}\t{escape_newlines(target)}" for source, target in unique.items())
	# 必须显式 newline="\n"：Windows 下默认会写 CRLF，行尾的 \r 会让引擎查表匹配不上。
	out.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")

	print(f"wrote {out} ({len(unique)} entries, {len(entries) - len(unique)} duplicates merged)")


if __name__ == "__main__":
	main()
