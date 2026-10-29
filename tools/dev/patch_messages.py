#!/usr/bin/env python3
"""把事件/NPC 对话里「名字/金币拼进去」的消息改成覆盖表模板。

这些消息先拼好英文再交给界面，整串永远查不到覆盖表。改成
``UiText::translateTemplate("英文模板", {{"{占位符}", 变量}})`` 后，中文语序写在
corpus/ui_text.txt 里，源码只负责填值。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import paths

CALL = re.compile(r"([A-Za-z_.]*messages\.push_back)\(\s*([\s\S]{0,500}?)\)\s*;")


def tpl(text: str, params: str, indent: str = "                ") -> str:
	return f'UiText::translateTemplate("{text}",\n{indent}    {{{params}}})'


# (文件, 唯一标记, 替换用的实参代码)
EDITS: list[tuple[str, str, str]] = [
	("game/gameplay/HouseInteraction.cpp", "'s condition.\"",
	 tpl("The temple staff cannot treat {name}'s condition.", '{"{name}", pMember->name}')),
	("game/gameplay/HouseInteraction.cpp", "is already well.\"",
	 tpl("The temple staff says {name} is already well.", '{"{name}", pMember->name}')),
	("game/gameplay/HouseInteraction.cpp", "gold for healing.\"",
	 tpl("You need {gold} gold for healing.", '{"{gold}", std::to_string(price)}')),
	("game/gameplay/HouseInteraction.cpp", "The temple restores ",
	 tpl("The temple restores {name} for {gold} gold.",
	     '{"{name}", pMember->name}, {"{gold}", std::to_string(price)}')),
	("game/gameplay/HouseInteraction.cpp", "to donate here.\"",
	 tpl("You need {gold} gold to donate here.", '{"{gold}", std::to_string(price)}')),
	("game/gameplay/HouseInteraction.cpp", "to rent a room.\"",
	 tpl("You need {gold} gold to rent a room.", '{"{gold}", std::to_string(price)}')),
	("game/gameplay/HouseInteraction.cpp", "for provisions.\"",
	 tpl("You need {gold} gold for provisions.", '{"{gold}", std::to_string(price)}')),
	("game/gameplay/HouseInteraction.cpp", "fills your packs to ",
	 tpl("The innkeeper fills your packs to {days} days.", '{"{days}", std::to_string(foodTarget)}')),
	("game/gameplay/HouseInteraction.cpp", "gold for a drink.\"",
	 tpl("You need {gold} gold for a drink.", '{"{gold}", std::to_string(DrinkPrice)}')),
	("game/gameplay/HouseInteraction.cpp", "gold for a tip.\"",
	 tpl("You need {gold} gold for a tip.", '{"{gold}", std::to_string(TipPrice)}')),
	("game/gameplay/HouseInteraction.cpp", "Your current fine is ",
	 tpl("Your current fine is {gold} gold.", '{"{gold}", std::to_string(party.fineGold())}')),
	("game/gameplay/HouseInteraction.cpp", "to pay your fine.\"",
	 tpl("You need {gold} gold to pay your fine.", '{"{gold}", std::to_string(fine)}')),
	("game/gameplay/HouseInteraction.cpp", "more experience to train to level ",
	 tpl("You need {exp} more experience to train to level {level}.",
	     '{"{exp}", std::to_string(*experienceShortfall)}, {"{level}", std::to_string(pMember->level + 1)}')),
	("game/gameplay/HouseInteraction.cpp", "gold for training.\"",
	 tpl("You need {gold} gold for training.", '{"{gold}", std::to_string(price)}')),
	("game/gameplay/HouseInteraction.cpp", "is now level ",
	 tpl("{name} is now level {level} and has earned {points} skill points!",
	     '{"{name}", pMember->name}, {"{level}", std::to_string(newLevel)}, '
	     '{"{points}", std::to_string(skillPointsEarned)}')),
	("game/gameplay/HouseInteraction.cpp", "cannot learn ",
	 tpl("{name} cannot learn {skill} here.",
	     '{"{name}", pMember->name}, {"{skill}", UiText::translate(displaySkillName(action.argument))}')),
	("game/gameplay/HouseInteraction.cpp", ' learns "',
	 tpl("{name} learns {skill} for {gold} gold.",
	     '{"{name}", pMember->name}, {"{skill}", UiText::translate(displaySkillName(action.argument))}, '
	     '{"{gold}", std::to_string(price)}')),
	("game/gameplay/HouseInteraction.cpp", "to travel to ",
	 tpl("It will take {days} to travel to {destination}.",
	     '{"{days}", transportTravelDaysText(travelDays)}, {"{destination}", route.destinationName}')),
	("game/gameplay/HouseInteraction.cpp", '"Deposited "',
	 tpl("Deposited {gold} gold.", '{"{gold}", std::to_string(depositedGold)}')),
	("game/gameplay/HouseInteraction.cpp", '"Withdrew "',
	 tpl("Withdrew {gold} gold.", '{"{gold}", std::to_string(withdrawnGold)}')),
	("game/gameplay/GameplayDialogController.cpp", "waits at the Adventurer's Inn.",
	 tpl("{name} waits at the Adventurer's Inn.", '{"{name}", recruit.character.name}')),
	("game/gameplay/GameplayDialogController.cpp", "recruit.character.name + \" joined the party.\"",
	 tpl("{name} joined the party.", '{"{name}", recruit.character.name}')),
	("game/gameplay/GameplayDialogController.cpp", "pRosterEntry->name + \" joined the party.\"",
	 tpl("{name} joined the party.", '{"{name}", pRosterEntry->name}')),
	("game/gameplay/GameplayDialogController.cpp", "is already following you.",
	 tpl("{name} is already following you.", '{"{name}", pNpc->name}')),
	("game/gameplay/GameplayDialogController.cpp", "joined the followers.",
	 tpl("{name} joined the followers.", '{"{name}", pNpc->name}')),
	("game/gameplay/GameplayDialogController.cpp", "left the followers.",
	 tpl("{name} left the followers.",
	     '{"{name}", pNpc != nullptr && !pNpc->name.empty() ? pNpc->name : UiText::translate("The follower")}')),
]


def main() -> int:
	roots = [Path(p) for p in sys.argv[1:]]
	if not roots:
		roots = [paths.engine_source()]

	pending = list(EDITS)
	failed = []

	for root in roots:
		by_file: dict[str, list[tuple[str, str]]] = {}
		for path, marker, code in pending:
			by_file.setdefault(path, []).append((marker, code))

		for path, items in by_file.items():
			full = root / path
			text = full.read_text(encoding="utf-8")
			spans = [(m.start(), m.end(), m.group(1), m.group(2)) for m in CALL.finditer(text)]
			replacements = []

			for marker, code in items:
				hit = [s for s in spans if marker in s[3]]
				if len(hit) != 1:
					failed.append(f"{path}: {marker} 命中 {len(hit)} 处")
					continue
				start, end, call, _ = hit[0]
				replacements.append((start, end, f"{call}({code});"))

			for start, end, new in sorted(replacements, reverse=True):
				text = text[:start] + new + text[end:]

			full.write_text(text, encoding="utf-8", newline="")
			print(f"{path}: {len(replacements)} 处改写")

	if failed:
		for line in failed:
			print("未处理:", line)
		return 1
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
