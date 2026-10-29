#!/usr/bin/env python3
"""NPC 职业名的中文语料（「某人 the 某某」里的那半句）。

OpenYAMM 的 npc_professions.txt 用英文职业名而不是 Global.txt 的编号来拼显示名，
所以这里按记录 id 补一份中文对照。改完重跑 build_patch.py 即可。
"""
from __future__ import annotations

import argparse
import csv
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import paths

OUT = paths.OVERRIDES / "npc_professions_zh.tsv"


def load_professions(packs: Path) -> str:
	"""从资产包里读出 npc_professions.txt 的原始文本。"""
	for pattern in ("engine.core-*.zip", "*.zip"):
		for path in sorted(packs.glob(pattern)):
			with zipfile.ZipFile(path) as archive:
				if "data_tables/npc_professions.txt" in archive.namelist():
					return archive.read("data_tables/npc_professions.txt").decode("latin-1", "replace")
	raise SystemExit(f"在 {packs} 里找不到 data_tables/npc_professions.txt")

NAMES = {
	"Smith": "铁匠",
	"Armorer": "制甲匠",
	"Alchemist": "炼金术士",
	"Scholar": "学者",
	"Guide": "向导",
	"Tracker": "追踪者",
	"Pathfinder": "探路者",
	"Sailor": "水手",
	"Navigator": "领航员",
	"Healer": "治疗师",
	"Expert Healer": "高级治疗师",
	"Master Healer": "大师治疗师",
	"Teacher": "教师",
	"Instructor": "导师",
	"Arms Master": "军械大师",
	"Weapons Master": "兵器大师",
	"Apprentice": "学徒",
	"Mystic": "秘术师",
	"Spell Master": "法术大师",
	"Trader": "商贩",
	"Merchant": "商人",
	"Scout": "斥候",
	"Counselor": "顾问",
	"Barrister": "律师",
	"Tinker": "修补匠",
	"Locksmith": "锁匠",
	"Fool": "小丑",
	"Chimney Sweep": "清烟囱工",
	"Porter": "搬运工",
	"Quarter Master": "军需官",
	"Factor": "代理商",
	"Banker": "银行家",
	"Cook": "厨子",
	"Chef": "大厨",
	"Horseman": "骑手",
	"Bard": "吟游诗人",
	"Enchanter": "附魔师",
	"Cartographer": "制图师",
	"Wind Master": "风系大师",
	"Water Master": "水系大师",
	"Gate Master": "传送大师",
	"Acolyte": "侍僧",
	"Piper": "吹笛人",
	"Explorer": "探险家",
	"Pirate": "海盗",
	"Squire": "侍从",
	"Psychic": "灵能师",
	"Gypsy": "吉普赛人",
	"Negotiator": "谈判专家",
	"Duper": "骗子",
	"Burglar": "窃贼",
	"Peasant": "农民",
	"Serf": "农奴",
	"Tailor": "裁缝",
	"Laborer": "劳工",
	"Farmer": "农夫",
	"Cooper": "桶匠",
	"Potter": "陶匠",
	"Weaver": "织工",
	"Cobbler": "鞋匠",
	"Ditch Digger": "挖沟工",
	"Miller": "磨坊主",
	"Carpenter": "木匠",
	"Stone Cutter": "石匠",
	"Jester": "弄臣",
	"Trapper": "陷阱猎人",
	"Beggar": "乞丐",
	"Rustler": "偷牛贼",
	"Hunter": "猎人",
	"Scribe": "书记员",
	"Missionary": "传教士",
	"Clerk": "文书",
	"Guard": "卫兵",
	"Follower of Baa": "巴阿信徒",
	"Noble": "贵族",
	"Gambler": "赌徒",
	"Child": "孩子",
}


def main() -> None:
	parser = argparse.ArgumentParser(description=__doc__,
									 formatter_class=argparse.RawDescriptionHelpFormatter)
	parser.add_argument("--packs", type=Path, default=None,
						help="原版安装的 assets/packs 目录（默认自动探测，或设 OPENYAMM_PACKS）")
	parser.add_argument("--out", type=Path, default=OUT, help="输出 tsv（默认 corpus/overrides/npc_professions_zh.tsv）")
	arguments = parser.parse_args()

	text = load_professions(paths.asset_packs(arguments.packs))
	rows = list(csv.reader(text.splitlines(), delimiter="\t"))
	missing = []
	with open(arguments.out, "w", encoding="utf-8", newline="") as handle:
		for row in rows[1:]:
			if len(row) < 2 or not row[1].strip():
				continue
			english = row[1].strip()
			chinese = NAMES.get(english)

			if chinese is None:
				missing.append(english)
				continue

			handle.write(f"{row[0].strip()}\t{chinese}\n")
	print(f"写出职业名 {len(NAMES) - len(missing)} 条，缺 {len(missing)} 条：{missing}")


if __name__ == "__main__":
	main()
