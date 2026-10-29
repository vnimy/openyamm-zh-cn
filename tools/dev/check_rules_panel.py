"""检查 ruleset.yml 里展示用字符串是否都在 ui_text 覆盖表中。

    python tools/dev/check_rules_panel.py [ruleset.yml 路径]
"""
import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import paths

engine = paths.engine_source()
yml = Path(sys.argv[1]) if len(sys.argv) > 1 else engine / "assets_dev/engine/rulesets/maw/ruleset.yml"
table = paths.OVERRIDES / "ui_text.txt"

data = yaml.safe_load(yml.read_text(encoding="utf-8"))
keys = set()
for line in table.read_text(encoding="utf-8").splitlines():
    if not line or line.startswith("#"):
        continue
    if "\t" in line:
        k, v = line.split("\t", 1)
        keys.add(k)

wanted = []


def add(text, where):
    if isinstance(text, str) and text.strip():
        wanted.append((text, where))


add(data.get("name"), "name")
add(data.get("description"), "description")
for i, c in enumerate(data.get("credits") or []):
    add(c, f"credits[{i}]")
panel = data.get("rulesPanel") or {}
add(panel.get("title"), "title")
add(panel.get("subtitle"), "subtitle")
add(panel.get("summary"), "summary")
for i, c in enumerate(panel.get("difficultyColumns") or []):
    add(c, f"column[{i}]")
for diff, entry in (panel.get("difficulties") or {}).items():
    for i, v in enumerate(entry.get("values") or []):
        add(v, f"{diff}.values[{i}]")
    add(entry.get("description"), f"{diff}.description")
    add(entry.get("warning"), f"{diff}.warning")
for k, v in (panel.get("progressions") or {}).items():
    add(v, f"progression.{k}")
for k, v in (panel.get("challengeModes") or {}).items():
    add(v, f"challenge.{k}")

missing = [(t, w) for t, w in wanted if t not in keys]
print(f"总字符串 {len(wanted)}，缺失 {len(missing)}")
for t, w in missing:
    print(f"[{w}] {t}")
