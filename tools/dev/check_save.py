#!/usr/bin/env python3
"""旧存档自查：给一个 .oysav，一条命令说清「这个档在当前版本能不能载入、不能的话卡在哪」。

    python tools/dev/check_save.py <file.oysav> [<file2.oysav> ...] [--game-dir <安装根>]

只读头部 12 字节与安装清单，不反序列化存档内容，也不改任何文件。
判定依据（openyamm/game/maps/SaveGame.cpp）：

  * 前 8 字节必须是 b"OYSAVE1\0"，随后 4 字节小端 uint32 是存档版本；
  * 版本 > 142（SaveVersion）→ 引擎报 written by a newer version of OpenYAMM，
    这类档在读档列表里不显示，只统计条数；
  * 版本 < 140（SaveVersionSummaryFirst）→ 引擎仍读得动（旧摘要布局在游戏状态之后），
    但 save-tools 的解码器只吃 140-142；
  * 140 <= 版本 <= 142 → 引擎与 save-tools 都能处理。

退出码：全部文件都判为引擎可读 → 0；任一文件不是本引擎存档、或由更新版本写入 → 1。
"""

from __future__ import annotations

import argparse
import json
import re
import struct
import sys
import zipfile
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

SAVE_MAGIC = b"OYSAVE1\x00"
SAVE_HEADER_SIZE = 12
SAVE_VERSION = 142  # SaveGame.cpp:25 constexpr uint32_t SaveVersion
SAVE_VERSION_SUMMARY_FIRST = 140  # SaveGame.cpp:208

VERDICT_CURRENT = "当前引擎可读"
VERDICT_NEWER = "由更新版本写入"
VERDICT_OLD = "旧格式但引擎可读（save-tools 不可解码）"
VERDICT_NOT_SAVE = "不是 OpenYAMM 存档（invalid save header）"
ENGINE_READABLE = (VERDICT_CURRENT, VERDICT_OLD)

SCHEMA_KEY = re.compile(r"^\s*contentSchemaVersion\s*:\s*(\d+)\s*$", re.MULTILINE)


def configure_stdout() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError):
            pass


def read_header(path: Path) -> tuple[bool, int | None, bytes, int]:
    """返回（头是否合法, 版本号, 实际读到的头 8 字节, 文件长度）。"""
    size = path.stat().st_size

    with path.open("rb") as handle:
        header = handle.read(SAVE_HEADER_SIZE)

    head = header[:8]

    if len(header) < len(SAVE_MAGIC) or head != SAVE_MAGIC:
        return False, None, head, size

    if len(header) < SAVE_HEADER_SIZE:
        return False, None, head, size

    return True, struct.unpack("<I", header[8:12])[0], head, size


def read_summary_fields(path: Path) -> tuple[str, float, str] | None:
    """从摘要块读（地图文件名, 游戏分钟, 规则集 id）。只对 140+ 的摘要前置布局成立。

    布局：magic(8) + version(4) + 摘要字节数(4)，随后是 8 字节长度前缀的地图名、f32 游戏分钟、
    再一个 8 字节长度前缀的规则集 id（SaveGame.cpp 的摘要写入顺序）。读不出来就算没有，不影响结论。
    """
    try:
        with path.open("rb") as handle:
            data = handle.read(4096)
        offset = 16

        def read_string(position: int) -> tuple[str, int]:
            length = struct.unpack_from("<Q", data, position)[0]
            position += 8
            if length > len(data) - position:
                raise ValueError("summary field runs past the header window")
            return data[position:position + length].decode("utf-8", "replace"), position + length

        map_name, offset = read_string(offset)
        minutes = struct.unpack_from("<f", data, offset)[0]
        offset += 4
        ruleset, _ = read_string(offset)
        return map_name, minutes, ruleset
    except (OSError, struct.error, ValueError):
        return None


STANDARD_RULESET = "mmerge"


def verdict_for(ok: bool, version: int | None) -> str:
    if not ok or version is None:
        return VERDICT_NOT_SAVE

    if version > SAVE_VERSION:
        return VERDICT_NEWER

    if version < SAVE_VERSION_SUMMARY_FIRST:
        return VERDICT_OLD

    return VERDICT_CURRENT


def hint_for(verdict: str) -> str:
    if verdict == VERDICT_NEWER:
        return "这个档由比当前引擎更新的版本写入；只能升级引擎，手改版本字节会把档改坏。"
    if verdict == VERDICT_NOT_SAVE:
        return "OpenYAMM 只认 OYSAVE1 容器；原版 MM6/7/8 与 MMMerge 的存档导入不了。"
    if verdict == VERDICT_OLD:
        return "引擎能载入（旧摘要布局），但 save-tools 解码器只支持 140-142。"
    return ""


def find_pack(pack_name: str, pack_dirs: list[Path]) -> Path | None:
    for directory in pack_dirs:
        candidate = directory / pack_name
        if candidate.is_file():
            return candidate
    return None


def world_manifest_schema(zip_path: Path) -> tuple[int, bool, bool]:
    """（contentSchemaVersion, 包里有没有 world.yml, world.yml 里有没有这个键）。

    引擎读内容包的 world.yml，键缺省为 1（ContentManifest.cpp:117）；
    只有 .core 这类内容包带 world.yml，其余包按缺省 1 处理。
    """
    try:
        with zipfile.ZipFile(zip_path) as archive:
            if "world.yml" not in archive.namelist():
                return 1, False, False
            text = archive.read("world.yml").decode("utf-8", "replace")
    except (OSError, zipfile.BadZipFile, KeyError):
        return 1, False, False

    match = SCHEMA_KEY.search(text)
    return (int(match.group(1)) if match else 1), True, bool(match)


def describe_saves_dir(saves_dir: Path) -> list[str]:
    if not saves_dir.is_dir():
        return [f"  读档列表扫：{saves_dir}\\*.oysav —— 目录不存在（游戏启动时会建）"]

    saves = sorted(p for p in saves_dir.iterdir() if p.is_file() and p.suffix.lower() == ".oysav")

    if not saves:
        return [f"  读档列表扫：{saves_dir}\\*.oysav —— 0 个文件"]

    lines = [f"  读档列表扫：{saves_dir}\\*.oysav —— {len(saves)} 个文件"]
    lines += [f"    {p.name}" for p in saves]
    return lines


def describe_game_dir(game_dir: Path) -> dict:
    """打印安装侧信息，返回给逐文件结论用的上下文。"""
    print(f"安装根：{game_dir}")
    context = {"install_root": game_dir, "version": None, "index": None, "manifest_error": None}

    current = game_dir / "app" / "current"
    release = False

    if current.exists():
        release = True
        context["version"] = current.read_text(encoding="utf-8", errors="replace").strip()
        print(f"  版式：发布版安装（app/current 存在），当前版本 {context['version']}")
        index = game_dir / "app" / context["version"] / "index.json"
    else:
        index = game_dir / "assets" / "index.json"
        if index.is_file():
            release = True
            print("  版式：发布版安装（assets/index.json 存在），无 app/current 版本目录")
        else:
            print("  版式：未发现发布版安装标志（app/current 与 assets/index.json 都没有）")

    context["release"] = release
    manifest = None

    if index.is_file():
        try:
            manifest = json.loads(index.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            context["manifest_error"] = f"{index} 读不出：{error}"
            print(f"  内容清单：{context['manifest_error']}")
    else:
        context["manifest_error"] = f"找不到内容清单 {index}"
        print(f"  内容清单：{context['manifest_error']}")

    packs = manifest.get("packs", []) if isinstance(manifest, dict) else []

    if packs:
        package_counts = Counter(pack.get("package", "?") for pack in packs)
        print(f"  内容清单：{index} —— {len(packs)} 个包，{len(package_counts)} 个 package")

        candidate_dirs = [game_dir / "assets" / "packs", game_dir / "packs"]
        if context["version"]:
            candidate_dirs += [game_dir / "app" / context["version"] / "packs",
                               game_dir / "app" / context["version"] / "assets" / "packs"]
        pack_dirs = [d for d in candidate_dirs if d.is_dir()]

        schemas: dict[str, list[tuple[int, bool, bool]]] = defaultdict(list)
        missing = 0

        for pack in packs:
            name = pack.get("file", "")
            found = find_pack(name, pack_dirs) if name else None
            if found is None:
                missing += 1
                schemas[pack.get("package", "?")].append((1, False, False))
                continue
            schemas[pack.get("package", "?")].append(world_manifest_schema(found))

        for package in sorted(schemas):
            values = schemas[package]
            distinct = sorted({schema for schema, _, _ in values})
            labelled = [str(v) for v in distinct]
            note = ""
            if not any(has_world for _, has_world, _ in values):
                note = "，包内没有 world.yml，引擎取缺省 1"
            elif not any(has_key for _, _, has_key in values):
                note = "，world.yml 无该键，引擎取缺省 1"
            elif len(distinct) > 1:
                note = "，同一 package 内取值不一致"
            print(f"    {package:<8} {package_counts[package]:>4} 个包   contentSchemaVersion "
                  f"{'/'.join(labelled)}{note}")

        if not pack_dirs:
            print("    （没找到 assets/packs 包目录，world.yml 一律按缺省 1 处理）")
        if missing:
            print(f"    （{missing} 个包的文件不在包目录里，按缺省 1 处理）")

    user_data = game_dir if release else Path.cwd()
    context["user_data"] = user_data
    context["saves_dir"] = user_data / "saves"

    print(f"  User data 目录：{user_data}")
    if release:
        print("    （发布版安装：saves、settings.ini、openyamm.log 都在安装根；日志里那行 User data folder: 就是它）")
    else:
        print("    （不是发布版安装：用当前工作目录；也可以用 --user-data 显式指定）")

    for line in describe_saves_dir(context["saves_dir"]):
        print(line)

    return context


def describe_save(path: Path) -> tuple[str, int]:
    print()
    print(f"存档：{path}")

    if not path.is_file():
        print("  读不出：文件不存在")
        return VERDICT_NOT_SAVE, 1

    try:
        ok, version, head, size = read_header(path)
        mtime = datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
    except OSError as error:
        print(f"  读不出：{error}")
        return VERDICT_NOT_SAVE, 1

    print(f"  大小：{size:,} 字节")
    print(f"  修改时间：{mtime}")

    if ok:
        print(f"  文件头：{head!r} ✓")
        print(f"  版本：{version}")
    else:
        print(f"  文件头：{head!r} ✗（期望 {SAVE_MAGIC!r}）")
        print("  版本：读不到")

    if ok and version >= SAVE_VERSION_SUMMARY_FIRST:
        summary = read_summary_fields(path)
        if summary is not None:
            map_name, minutes, ruleset = summary
            print(f"  地图：{map_name}   游戏时间：{minutes:.0f} 分钟（约 {minutes / 1440:.1f} 天）")
            print(f"  规则集：{ruleset}")
            if ruleset and ruleset != STANDARD_RULESET:
                print(f"  ⚠ 非标准规则集 '{ruleset}'：读档前引擎要先加载 engine/rulesets/{ruleset}/ 的补丁表。"
                      f"补丁表按英文名定位目标行，汉化把目标表译名后会一条也匹配不上，"
                      f"activateRuleset 失败，表现为点了载入没反应或退回主菜单；"
                      f"日志里是 Failed to apply ruleset table ... key '...' must match exactly one row。")

    verdict = verdict_for(ok, version)
    print(f"  结论：{verdict}")

    hint = hint_for(verdict)
    if hint:
        print(f"  → {hint}")

    return verdict, 0 if verdict in ENGINE_READABLE else 1


def mention_saves_dir(path: Path, context: dict) -> None:
    saves_dir = context.get("saves_dir")
    if saves_dir is None:
        return

    resolved = path.resolve() if path.exists() else path
    inside = str(resolved).lower().startswith(str(saves_dir.resolve()).lower() + "\\") \
        or str(resolved).lower().startswith(str(saves_dir.resolve()).lower() + "/")

    if inside:
        print(f"  在游戏扫的目录里：是（{saves_dir}）")
        return

    print("  在游戏扫的目录里：否")
    print(f"  ⚠ 游戏扫的是 {saves_dir}，你的档在 {resolved} —— "
          f"用读档界面的 Import Saves，或把文件拷进 {saves_dir}")


def main(argv: list[str]) -> int:
    configure_stdout()

    parser = argparse.ArgumentParser(
        add_help=True,
        description="旧存档自查：这个 .oysav 在当前版本能不能载入。只读，不改存档。")
    parser.add_argument("files", nargs="+", metavar="file.oysav", help="要检查的存档文件")
    parser.add_argument("--game-dir", metavar="安装根",
                        help="OpenYAMM 安装根（含 app/current 的那一层），给出后额外检查安装清单与 user data 目录")
    args = parser.parse_args(argv)

    context = {}
    if args.game_dir:
        game_dir = Path(args.game_dir).expanduser().resolve()
        context = describe_game_dir(game_dir)

    exit_code = 0
    for name in args.files:
        path = Path(name).expanduser()
        _, code = describe_save(path)
        exit_code = max(exit_code, code)
        if context:
            mention_saves_dir(path, context)

    print()
    print(f"合计 {len(args.files)} 个文件，退出码 {exit_code}"
          f"（0 = 全部引擎可读，1 = 有读不了或由更新版本写入的）")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))