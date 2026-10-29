"""扫描 NewGameScreen.cpp 里传给 label/confirm/textInRect 的字面量，报告覆盖表缺失项。

开发期的一次性排查脚本，留作「按单个文件细查」的模板。

    python tools/dev/check_newgame_text.py
"""
import io
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import paths

engine = paths.engine_source()
cpp = (engine / "game/ui/screens/NewGameScreen.cpp").read_text(encoding="utf-8")
table = paths.OVERRIDES / "ui_text.txt"

keys = {}
for line in io.open(table, encoding="utf-8"):
    line = line.rstrip("\n")
    if not line or line.startswith("#") or "\t" not in line:
        continue
    k, v = line.split("\t", 1)
    keys[k] = v

# 相邻的字符串字面量拼接（"... " "..."）先合并成一条。
def literals(segment: str):
    joined = re.sub(r'"\s*\n?\s*"', "", segment)
    return re.findall(r'"((?:[^"\\]|\\.)*)"', joined)


found = []
# label("id", <expr>)
for m in re.finditer(r'label\(\s*"[^"]*"\s*,\s*(.{0,400}?)\)\s*;', cpp, re.S):
    expr = m.group(1)
    strs = literals(expr)
    if strs:
        found.append(("label", strs[0] if len(strs) == 1 else " ".join(strs)))
# confirm("title", "body", ...)
for m in re.finditer(r'confirm\(\s*(.{0,600}?),\s*\n?\s*\[', cpp, re.S):
    strs = literals(m.group(1))
    if strs:
        found.append(("confirm-title", strs[0]))
        if len(strs) > 1:
            found.append(("confirm-body", strs[1]))
# textInRect(..., "text", ...)
for m in re.finditer(r'textInRect\(\s*\{[^}]*\}\s*,\s*(.{0,300}?),\s*"', cpp, re.S):
    strs = literals(m.group(1))
    if strs:
        found.append(("textInRect", " ".join(strs)))

missing = []
for kind, text in found:
    if not text.strip() or not re.search(r"[A-Za-z]", text):
        continue
    if text in keys:
        continue
    if any(re.match(r"^[A-Za-z_]+$", t) and t in keys for t in text.split()):
        pass
    missing.append((kind, text))

seen = set()
print(f"扫描到 {len(found)} 处文本，缺失 {len(missing)} 条：")
for kind, text in missing:
    if text in seen:
        continue
    seen.add(text)
    print(f"[{kind}] {text}")
