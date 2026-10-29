#!/usr/bin/env python3
"""提取 1.17 官方内容包里全部 UI 布局（ui/**/*.yml）的可见文本。

用途：与 corpus/ui_text.txt 的键比对，找出尚未汉化的界面布局文案。

    python tools/dev/extract_ui_strings.py                # 列表 + 缺口统计
    python tools/dev/extract_ui_strings.py --json build/ui_all_strings.json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import paths

FIELD = re.compile(r"^\s*(value|title|text|label|name|desc|description|tooltip|placeholder):\s*(.+?)\s*$")

# settings_catalog.yml 里的下拉选项写成 `- [value, Label]`，展示名在逗号后面，
# 不匹配 FIELD 正则——之前逐条肉眼比对时才漏掉了 Windowed / Very low / Soft 这些选项。
OPTION = re.compile(r"^-\s*\[(.*)\]$")
OPTION_PAIR = re.compile(r"""^\s*(['"]?)([^,'"]*)\1\s*,\s*(['"]?)(.*?)\3\s*$""")
HAS_LETTERS = re.compile(r"[A-Za-z]")


def strip_quotes(text: str) -> str:
	text = text.strip()
	if len(text) >= 2 and text[0] == text[-1] and text[0] in ("\"", "'"):
		return text[1:-1]
	return text


def collect(packs: Path) -> dict:
	found: dict = {}
	for path in sorted(packs.glob("*.zip")):
		try:
			archive = zipfile.ZipFile(path)
		except Exception:
			continue
		with archive:
			for name in archive.namelist():
				if not (name.startswith("ui/") and name.endswith(".yml")):
					continue
				data = archive.read(name).decode("utf-8", "replace")
				for line in data.splitlines():
					option = OPTION.match(line.strip())
					if option:
						pair = OPTION_PAIR.match(option.group(1))
						if pair and pair.group(4).strip() and HAS_LETTERS.search(pair.group(4)):
							found.setdefault(pair.group(4).strip(), set()).add(name)
						continue
					match = FIELD.match(line)
					if not match:
						continue
					value = strip_quotes(match.group(2))
					if len(value) < 2:
						continue
					# 跳过纯 id / 路径 / 变量名
					if " " not in value and re.match(r"^[a-z0-9_./-]+$", value):
						continue
					found.setdefault(value, set()).add(name)
	return found


def main() -> int:
	parser = argparse.ArgumentParser(description=__doc__,
									 formatter_class=argparse.RawDescriptionHelpFormatter)
	parser.add_argument("--packs", type=Path, default=None,
						help="原版安装的 assets/packs 目录（默认自动探测，或设 OPENYAMM_PACKS）")
	parser.add_argument("--table", type=Path, default=paths.OVERRIDES / "ui_text.txt", help="覆盖表")
	parser.add_argument("--json", type=Path, default=None, help="把提取结果写成 json")
	parser.add_argument("--show", type=int, default=200, help="最多列出多少条缺口")
	arguments = parser.parse_args()

	found = collect(paths.asset_packs(arguments.packs))
	payload = {key: sorted(value) for key, value in sorted(found.items())}
	print(f"UI 布局可见文本 {len(payload)} 条")

	if arguments.json:
		arguments.json.parent.mkdir(parents=True, exist_ok=True)
		with open(arguments.json, "w", encoding="utf-8", newline="\n") as handle:
			json.dump(payload, handle, ensure_ascii=False, indent=1)
		print(f"已写到 {arguments.json}")

	keys = set()
	if arguments.table.exists():
		for line in arguments.table.read_text(encoding="utf-8").splitlines():
			if not line or line.startswith("#") or "\t" not in line:
				continue
			keys.add(line.split("\t", 1)[0].rstrip("*"))

	missing = [text for text in payload if text not in keys]
	print(f"未汉化 {len(missing)} 条：")
	for text in missing[:arguments.show]:
		print(f"  {text!r}  <- {payload[text]}")
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
