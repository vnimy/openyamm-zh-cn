#!/usr/bin/env python3
"""生成「英文屋名 / 店名 -> 中文」对照，写进 corpus/house_names.tsv。

房屋名不能直接改数据表：HouseInteraction / GameplayDialogController 里拿英文屋名做逻辑判断
（旅店、公会技能表、Baa 神殿、地下城开场动画），改了就会静默失效。所以只在展示层查表覆盖。

输入：原版 OpenYAMM 资产包里的 `data_tables/house_data.txt`（英文名）+ corpus/ZHCN_2DEvents.txt
（MMMerge 官方简中的屋名，按记录 ID 对齐）。
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import paths

CORPUS = paths.MMMERGE / "ZHCN_2DEvents.txt"
OUT = paths.OVERRIDES / "house_names.tsv"

CJK = re.compile(r"[\u4e00-\u9fff]")


def load_house_data(packs: Path) -> str:
	"""从资产包里读出 house_data.txt 的原始文本。"""
	for pattern in ("engine.core-*.zip", "*.zip"):
		for path in sorted(packs.glob(pattern)):
			with zipfile.ZipFile(path) as archive:
				if "data_tables/house_data.txt" in archive.namelist():
					return archive.read("data_tables/house_data.txt").decode("latin-1", "replace")
	raise SystemExit(f"在 {packs} 里找不到 data_tables/house_data.txt")


def read_english(text: str) -> dict[str, str]:
	rows = list(csv.reader(text.splitlines(), delimiter="\t"))
	names: dict[str, str] = {}

	for row in rows[2:]:
		if len(row) > 7 and row[0].strip():
			names[row[0].strip()] = row[5].strip()

	return names


def read_chinese(path: Path) -> dict[str, str]:
	rows = list(csv.reader(path.read_text(encoding="utf-8").splitlines(), delimiter="\t"))
	names: dict[str, str] = {}

	for row in rows[1:]:
		if len(row) > 3 and row[0].strip():
			names[row[0].strip()] = row[1].strip()

	return names


def main() -> int:
	parser = argparse.ArgumentParser(description=__doc__,
									 formatter_class=argparse.RawDescriptionHelpFormatter)
	parser.add_argument("--packs", type=Path, default=None,
						help="原版安装的 assets/packs 目录（默认自动探测，或设 OPENYAMM_PACKS）")
	parser.add_argument("--corpus", type=Path, default=CORPUS, help="MMMerge 的 ZHCN_2DEvents.txt")
	parser.add_argument("--out", type=Path, default=OUT, help="输出 tsv（默认 corpus/overrides/house_names.tsv）")
	arguments = parser.parse_args()

	if not arguments.corpus.exists():
		raise SystemExit(f"找不到 {arguments.corpus}，先跑 tools/extract_corpus.py")

	english = read_english(load_house_data(paths.asset_packs(arguments.packs)))
	chinese = read_chinese(arguments.corpus)
	pairs: dict[str, str] = {}
	skipped = 0

	for key, source in english.items():
		target = chinese.get(key, "")

		if not source or not target or not CJK.search(target):
			skipped += 1
			continue

		if source.lower().startswith("placeholder") or "placeholder" in source.lower():
			skipped += 1
			continue

		# 同一个英文名可能出现多次；取第一次的译文，避免同一句在两栋房子间来回覆盖。
		pairs.setdefault(source, target)

	lines = [
		"# 房屋/店铺名：源码里拿英文名做判断，展示层靠这张表换成中文。",
		"",
	]
	lines.extend(f"{source}\t{target}" for source, target in pairs.items())
	arguments.out.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
	print(f"{len(pairs)} 条写入 {arguments.out}（跳过 {skipped} 条无译文/占位）")
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
