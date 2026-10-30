
## 附：1.18 → 1.19 的实际记录（2026-10-30）

- 上游 1.18 → 1.19 共 **87 个文件**（`github.com/pjasicek/openyamm/compare/v1.18...v1.19.diff`，
  纯文本 diff 291 KB，无二进制改动）。
- 本机没有完整上游仓库（仓库 11.7 GB，含大量美术源文件），所以**没下整包源码**，而是：
  1. `curl`（走本机 SOCKS5，`git` 自带的 curl 可用）拉 `.diff`，解析出 87 个路径与 added/modified 状态；
  2. 对每个文件用 `raw.githubusercontent.com/.../v1.19/<path>` 取新内容、`.../v1.18/<path>` 取 base；
  3. 本地 `openyamm-1.18` 树逐文件比 hash：只被上游改过的直接覆盖，两边都改过的用
     `git merge-file -p --diff3 本地 base 上游` 三方合并。
- 结果：67 个直接覆盖、6 个新增（`game/items/ItemSearch.*`、`game/ui/GameplayLootSummaryRenderer.*`、
  `tests/ItemSearchTests.cpp`、`assets_dev/engine/ui/gameplay/loot_summary.yml`）、11 个三方合并，
  仅 `game/ui/screens/LoadGameScreen.cpp` 有 1 处冲突（旧汉化把 “(not installed)” 包成模板，
  上游把 `saveData->ruleset` 改成 `summary.ruleset`），手工合成。
- 本地 1.18 树里缺的 3 个上游文本文件（`assets_dev/.../character.yml`、两个 mm7 lua）从 v1.19 补回。
- 构建：新建 `openyamm-1.19/build-mingw`；`zstd`/`etcpak`/`etc2comp` 预解压到 `toolchains/deps/` 并用
  `-DFETCHCONTENT_SOURCE_DIR_OPENYAMM_*` 指过去，配置期不联网；FFmpeg 装头文件时仍要手工补一次（见 build.md）。
- 新界面译文：见 [engine-changes.md](engine-changes.md) 的 1.19 附录与 `CHANGELOG.md`。
8
cd openyamm-1.17 && tar cf - --exclude=.git --exclude=build-mingw . | (cd ../openyamm-1.18 && tar xf -)
```

然后按 `v118-changes.txt` 把上游的新版本逐个覆盖回来。`git archive` / `git show` 在这台机器上
拉 blob 会卡死在 SSH/git 协议上，**用 GitHub API 单文件取更快也更稳**：

```bash
gh api -H "Accept: application/vnd.github.raw" \
    "repos/pjasicek/openyamm/contents/<path>?ref=v1.18" > openyamm-1.18/<path>
```

（删掉的文件（`A`/`D`）要真的 `rm`。）

## 第三步：处理「两边都改过」的文件

取两份清单的交集。先备份我们改过的版本，再把它们的 **旧版原始内容** 也取下来当 base：

```bash
gh api -H "Accept: application/vnd.github.raw" \
    "repos/pjasicek/openyamm/contents/<path>?ref=v1.17" > base17/<path>
```

然后 `difflib` 生成 base→本地的 patch，`patch -p1 --fuzz=3` 打到新版本上：

```bash
cd openyamm-1.18
patch -p1 --fuzz=3 --no-backup-if-mismatch -i <path>.patch
```

1.17 → 1.18 有 6 个重叠文件：

| 文件 | 结果 |
|---|---|
| `game/CMakeLists.txt` | 干净打上（`UiText.cpp` / `TextLayout.cpp` 的注册） |
| `tests/CMakeLists.txt` | 同上 |
| `game/events/EventRuntime.cpp` | 同上 |
| `game/ui/GameplayPartyOverlayRenderer.cpp` | 同上 |
| `game/ui/screens/LoadGameScreen.cpp` | 同上 |
| `game/ui/screens/MainMenuScreen.cpp` | **第 8 段冲突**，手工补的（见下） |

冲突那段是 `MainMenuScreen::captureBinding`：1.18 把它从 `confirm("Assign Key", body, ...)` 改成
`confirm(title, body, ...)` 并加了「再按 Esc 取消」的分支。由于附近的行被上游改动，patch 的上下文对不上，
`patch` 拒绝，手工把两处 `confirm` 的标题和正文都包成 `UiText::translate(...)` 才对齐。

打完务必检查有没有 `.rej`：

```bash
find . -name "*.rej" -o -name "*.orig"
```

## 第四步：补新版本的界面译文

这是真正的工作量。1.18 的更新说明里提到存档更快、**快速存档/快速读取可以重绑键**、日志多了
**魔幻牌（Arcomage）标签页**、读档／存档界面**可以按名称或时间排序**。每一条都会带来新文案。

做法：

```bash
cd ../../openyamm-zh-cn
python tools/check_literals.py --openyamm ../openyamm-1.18 --write build/lit118.txt
```

再把缺口清单与 `v118-changes.txt` 求交集，**只看出现在「本次改动过的文件」里的条目**——
其它的是历史遗留，本次不必处理。1.18 这次交集是 39 条，其中真界面文案十来条，其余是
日志字符串（`save_migration name=...`、`turn_based_frame reason=` 这类）、switch 分支里的
内部比较值、以及注释。

值得说的是：**比较用的内部字符串不能译**。比如

```cpp
if (lowerName == "day of protection") { return "Day of Protection"; }
```

前半句是内部比较键，译成中文会直接失效；只有返回值那是展示层，才需要覆盖表兜住。

这次补进 `corpus/overrides/manual_zh.tsv` 的条目大致是：`Quick Save`/`Quick Load`（新的键位标签）、
`Automatic`/`Quick`/`Manual`（存档类型）、`Newest`（排序按钮）、`Arcomage`、`Elsewhere`、
`{continent}: {won} of {total} taverns won.`（魔幻牌进度模板）、`Cinematic grading: On`、
`Turn-based mode`/`Realtime mode`、`You can't rest here!`、`There are hostile enemies near!`、
`Spell failed`、` (off)`、`Reverting in {seconds} seconds.`、`{done} of {total} MB` 等。

改完记得：

```bash
python tools/make_ui_text.py
python tools/check_tables.py
```

## 第五步：编译

MinGW 工具链的注意事项记在 **[build.md](build.md)** 里，这次新踩到一个：

> **PortableGit 的 `bin\` 目录是坏的。** 里面 358 个条目的元数据全是 `?????????`（读不到内容），
> bash 偏偏会先从这里解析 `cat`/`sed`/`head`。于是 FFmpeg 的 `version.sh`、`pkgconfig_generate.sh`
> 全炸：`cat: cannot execute: required file not found`，连带 `version.c` 里
> `FFMPEG_VERSION` 宏没生成出来 → 编译失败。
>
> 构建脚本里已经把这条 PATH 去掉了，只留 `<git>\usr\bin`（那份是好的）。如果你自己写脚本，
> 照上面这条来。

## 第六步：验证与出包

```bash
python tools/build_patch.py --openyamm ../openyamm-1.18 --out build/mods
python tools/font_subset.py --patch build/mods --openyamm ../openyamm-1.18 --out build/mods/engine/fonts/truetype
python tools/build_fonts.py --font assets/fonts/NotoSansSC.ttf --license assets/fonts/OFL.txt --out build/mods
python tools/package.py --mod build/mods \
       --exe ../openyamm-1.18/build-mingw/game/openyamm.exe \
       --out dist/OpenYAMM-1.18-zh_cn.zip
```

无头场景别忘了跑（不用开游戏窗口）：

```bash
<安装目录>/app/1.18/openyamm.exe \
    --headless-run-scenario tests/scenarios/item_inspect_test.yml
```

## 检查清单

- [ ] `find . -name "*.rej"` 为空
- [ ] 编译通过，`openyamm.exe` 生成
- [ ] `python tools/check_tables.py` 无警告
- [ ] 两个无头场景都 `passed`
- [ ] 改动列表、新术语同步进 `docs/engine-changes.md` 与 `CHANGELOG.md`
