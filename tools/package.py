"""Assemble the distributable Chinese patch.

The patch is two things: a mod folder the engine overlays on its own assets (all translated tables and the CJK font
faces), and the rebuilt executable that can rasterize and lay out UTF-8 text. Both go into one zip together with the
font license and install notes.
"""

from __future__ import annotations

import argparse
import shutil
import zipfile
from pathlib import Path

INSTALL_NOTES = """魔法门 6/7/8 中文补丁（OpenYAMM 1.17）
==========================================

适用：官方 1.17 的 Windows 版（OpenYAMM-1.17-windows-x64.zip 解压后的目录）。

安装
----
1. 先启动一次游戏，让它把内容包（约 5.8 GB）下载完，然后退出。
2. 把本压缩包里的 mods 文件夹复制到"有 settings.ini 和 saves 的那一层"，
   也就是解压出来的 OpenYAMM 目录。最终应当是 OpenYAMM/mods/engine/data_tables/...
3. 把本压缩包里的 openyamm.exe 覆盖到 OpenYAMM/app/1.17/openyamm.exe
   （建议先把原文件改名为 openyamm.exe.orig 备份）。
4. 照常双击 OpenYAMM.exe 启动。启动日志里应出现
   "Mods: ... file(s) from .../mods" 与 "Development assets: assets"。

卸载
----
删掉 OpenYAMM/mods 文件夹，再用备份的 openyamm.exe 覆盖回去。

说明
----
* 译文来自 MMMerge 整合版的官方简体中文语言包，按记录 ID 逐条对应到 OpenYAMM 的数据表。
* 字体为思源黑体（Noto Sans SC，SIL Open Font License 1.1），只烘焙游戏实际用到的字形。
* 文本表全部为 UTF-8；引擎按 Unicode 码点取字形，中文按字断行并避开行首标点。
* 如果启动器把游戏升级到新版本（app/<新版本>/），需要按新版本重新出补丁。
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mod", type=Path, required=True, help="the built mod directory (out/mods/zh_cn)")
    parser.add_argument("--exe", type=Path, required=True, help="the rebuilt openyamm.exe")
    parser.add_argument("--out", type=Path, required=True, help="output zip path")
    arguments = parser.parse_args()

    staging = arguments.out.parent / "staging"
    if staging.exists():
        shutil.rmtree(staging)

    # The engine mounts mods/engine and mods/worlds directly: one folder per package root, not per patch.
    shutil.copytree(arguments.mod, staging / "mods")
    shutil.copyfile(arguments.exe, staging / "openyamm.exe")
    (staging / "安装说明.txt").write_text(INSTALL_NOTES, encoding="utf-8")

    arguments.out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(arguments.out, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(staging.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(staging))

    print(f"{arguments.out} ({arguments.out.stat().st_size / 1e6:.1f} MB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
