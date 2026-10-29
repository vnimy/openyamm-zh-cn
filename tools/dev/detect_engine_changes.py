"""列出上游 OpenYAMM 源码树相对某个 tag，哪些文件被本地改过 / 新增。

为什么不用 `git status`：这台机器上的 OpenYAMM 源码是手工拼的浅克隆，`.git/index` 可能缺失，
缺了 index 时 `git status` 会把整棵树报成「已删除」，而 `git diff` 又要联网拉 promisor 对象。
所以改成纯本地算 blob sha1 跟 `git ls-tree` 的结果比，不下载任何对象。

用法：
    python tools/dev/detect_engine_changes.py --tree /path/to/openyamm --tag v1.18
    python tools/dev/detect_engine_changes.py --tag v1.18 --out build/changed.txt

输出两类：
    M <path>   本地内容与 <tag> 的 blob 不同（我们改过）
    A <path>   <tag> 的树里没有（我们新增的，如 game/ui/UiText.*）

再拿这份清单配合 `git diff-tree -r --name-only <old> <new>` 就能算出「上游也改过」的重叠文件。
重叠的要先做三方对比（把旧版同文件取出来当 base 生成 patch，再打到新版上）；
不重叠的直接沿用本地版本，因为上游没动过它们。
"""

from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
from pathlib import Path

# 构建产物与版本控制目录一律跳过，它们本来就不在上游树里。
SKIP_DIRS = {".git", "build-mingw", "build-msvc", "build-linux", "build", "out", "cmake-build-debug"}


def blob_sha1(path: Path) -> str:
	"""git blob 的 sha1 = sha1("blob <len>\\0" + 内容)。"""
	data = path.read_bytes()
	digest = hashlib.sha1()
	digest.update(b"blob %d\0" % len(data))
	digest.update(data)
	return digest.hexdigest()


def upstream_tree(tree: Path, tag: str) -> dict[str, str]:
	result = subprocess.run(["git", "ls-tree", "-r", tag], cwd=tree, capture_output=True)
	if result.returncode != 0:
		raise SystemExit(f"git ls-tree {tag} 失败：{result.stderr.decode('utf-8', 'replace').strip()}")

	entries: dict[str, str] = {}
	for line in result.stdout.decode("utf-8", "replace").splitlines():
		meta, _, path = line.partition("\t")
		parts = meta.split()
		if len(parts) < 3 or parts[1] != "blob":
			continue
		entries[path] = parts[2]
	return entries


def main() -> int:
	parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
	parser.add_argument("--tree", type=Path, default=None, help="本地 OpenYAMM 源码树（默认 ../openyamm）")
	parser.add_argument("--tag", default="v1.18", help="对比基准 tag（默认 v1.18）")
	parser.add_argument("--out", type=Path, default=None, help="把清单写进文件，每行 'M|A<TAB>路径'")
	arguments = parser.parse_args()

	tree = arguments.tree
	if tree is None:
		tree = Path(__file__).resolve().parents[2] / "openyamm"
	if not tree.is_dir():
		raise SystemExit(f"源码树不存在：{tree}")

	remote = upstream_tree(tree, arguments.tag)
	print(f"上游 {arguments.tag} 共 {len(remote)} 个文件")

	modified: list[str] = []
	added: list[str] = []
	for path in tree.rglob("*"):
		if not path.is_file():
			continue
		relative = path.relative_to(tree).as_posix()
		if any(part in SKIP_DIRS for part in relative.split("/")) or relative.startswith("."):
			continue
		expected = remote.get(relative)
		if expected is None:
			added.append(relative)
		elif blob_sha1(path) != expected:
			modified.append(relative)

	lines = [f"M\t{p}" for p in sorted(modified)] + [f"A\t{p}" for p in sorted(added)]
	if arguments.out is not None:
		arguments.out.parent.mkdir(parents=True, exist_ok=True)
		arguments.out.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
		print(f"已写入 {arguments.out}")

	print(f"\n改过 {len(modified)} 个：")
	for p in sorted(modified):
		print("  M", p)
	print(f"\n新增 {len(added)} 个：")
	for p in sorted(added):
		print("  A", p)
	return 0


if __name__ == "__main__":
	sys.exit(main())
