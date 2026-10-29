# 升级到新的引擎版本

引擎每出一个新版本，就要做一次移植。这一篇记的是 **1.17 → 1.18** 的实际过程与踩到的坑，
换别的版本时步骤通用。

## 一句话流程

以旧的工作区为底复制出新目录 → 用上游新版本覆盖「上游自己改过的文件」 → 把我们对新版本也改过的
那部分做三方对比打回去 → 补新界面的译文 → 编译、无头验证、出包。

关键点：**不能直接把旧工作区改名当成新版本**。这样会丢掉上游的新功能，也容易带着旧 bug。
反过来，**也不能整份替换成新版本**，那样汉化全没了。

## 第一步：拿到上游改了哪些文件

```bash
cd /path/to/openyamm-1.17
git fetch --depth 1 origin tag v1.18
git diff-tree -r --name-status v1.17 v1.18 > v118-changes.txt
wc -l v118-changes.txt
```

1.17 → 1.18 是 75 个文件（其中 1 个 `assets_source` 是子模块指针，忽略）。

本地这台机器上 `.git/index` 有可能不存在（源码树是手工拼的浅克隆），这时 `git status` 会把整棵树
报成已删除、`git diff` 又要联网拉 promisor 对象。别指望它，改用仓库里的工具按内容哈希比对：

```bash
python tools/dev/detect_engine_changes.py --tree ../openyamm-1.17 --tag v1.17
```

它只做两件事：`git ls-tree -r <tag>` 拿上游清单，然后本地算每个文件的 blob sha1 跟它比，
全程不下载对象。跑出来是我们改过的 37 个 + 新增的 5 个（`game/ui/UiText.*`、
`engine/TextLayout.*`、`cmake/RewriteMsysPaths.cmake`）。

## 第二步：铺新目录

```bash
mkdir openyamm-1.18
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
E:/Games/OpenYAMM-1.18/OpenYAMM/app/1.18/openyamm.exe \
    --headless-run-scenario tests/scenarios/item_inspect_test.yml
```

## 检查清单

- [ ] `find . -name "*.rej"` 为空
- [ ] 编译通过，`openyamm.exe` 生成
- [ ] `python tools/check_tables.py` 无警告
- [ ] 两个无头场景都 `passed`
- [ ] 改动列表、新术语同步进 `docs/engine-changes.md` 与 `CHANGELOG.md`
