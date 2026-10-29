#!/usr/bin/env python3
"""解码 MMerge 的 ZHCN_*.txt 本地化表。

这些文件把中文写成 ESC 标记 + GBK 字节：`\\x0e` 开始、`\\x07` 结束，中间每两字节一个 GBK 汉字。
本脚本把标记段还原成 UTF-8 中文，其余 ASCII 原样保留。
"""
from __future__ import annotations

import re
import sys

MARK_BEGIN = "\x0e"
MARK_END = "\x07"
# 解码后可能残留的标记字符（\x0f 是外层包装的结束符）。
MARK_CONTROL = re.compile(r"[\x0e\x0f\x07]")
# MMerge 把每个汉字写成「标记 + 两个 GBK 字节 + 标记」，标记之间还夹了一个空格，解码后要收回。
CJK_GAP = re.compile(r"(?<=[\u3000-\u9fff\uff00-\uffef]) +(?=[\u3000-\u9fff\uff00-\uffef])")


def decode_cell(cell: str) -> str:
	out: list[str] = []
	i = 0
	while i < len(cell):
		ch = cell[i]
		if ch == MARK_BEGIN:
			end = cell.find(MARK_END, i + 1)
			if end < 0:
				end = len(cell)
			raw = cell[i + 1:end]
			try:
				out.append(raw.encode("latin-1", "replace").decode("gbk", "replace"))
			except Exception:
				out.append(raw)
			i = end + 1
			continue
		if ch == MARK_END:
			i += 1
			continue
		out.append(ch)
		i += 1
	# ZHCN_2DEvents 用 \x0e…\x0f 把整格再包一层，内层标记解码后仍会剩下几个控制符，直接丢掉。
	cleaned = MARK_CONTROL.sub("", "".join(out))
	return CJK_GAP.sub("", cleaned)


def convert(path: str, out_path: str) -> None:
	text = open(path, "rb").read().decode("latin-1")
	lines = text.split("\r\n")
	converted = []
	for line in lines:
		cells = line.split("\t")
		converted.append("\t".join(decode_cell(c) for c in cells))
	open(out_path, "w", encoding="utf-8", newline="\n").write("\n".join(converted))


if __name__ == "__main__":
	if len(sys.argv) < 3:
		print("用法: decode_zhcn.py <输入> <输出>")
		raise SystemExit(2)
	convert(sys.argv[1], sys.argv[2])
