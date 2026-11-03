# OpenYAMM 简体中文补丁

把 [OpenYAMM](https://github.com/pjasicek/openyamm)（魔法门 6／7／8 的开源重制引擎）的文本系统从
「单字节 CP1252 + 256 个字形槽」改造成「UTF-8 + 按 Unicode 码点取字形」，再配上简体中文译文，
让这三部二十多年前的老游戏能在现代分辨率下正常显示中文。

译文覆盖了大部分界面与对话，但**还没做到 100%**，仍有一些地方会冒出英文，具体范围见下一节。

> Simplified Chinese localization for OpenYAMM (an open-source reimplementation of Might and Magic VI/VII/VIII).
> The engine's 8-bit text path is replaced by UTF-8 with per-codepoint glyph lookup, plus a zh_CN translation
> layer. Coverage is broad but not complete — see the status table below. Documentation is in Chinese;
> the code comments are too.

## 两个仓库

| | 仓库 | 内容 | 许可 |
|---|---|---|---|
| 引擎 | [vnimy/openyamm](https://github.com/vnimy/openyamm) | 让引擎能显示中文的 C++ 改动，每个版本一个 tag | GPL-3.0 |
| 补丁 | 就是本仓库 | 译文语料、字体子集、打包与审计工具 | MIT |

本仓库**不含 C++ 源码**，也不直接改引擎：引擎侧的一切改动都在 `vnimy/openyamm` 里以 commit 固定，
跟上游合并后不会丢。所以「换一个上游新版本」不是重新移植，而是在 fork 里 `git merge upstream/vX.Y`，
见 [docs/upgrading.md](docs/upgrading.md)。

| 补丁版本（本仓库） | 引擎 tag |
|---|---|
| 1.19.3 | `v1.19.3-zh_cn` |

**当前适配 OpenYAMM 1.19**，引擎与补丁必须成对使用：只换 `mods/` 不换 `openyamm.exe`，
官方引擎会把 UTF-8 字节按 CP1252 渲染成乱码。旧版本 1.17 的补丁包仍留在 [Releases](../../releases)。

**Android 端**（arm64 APK）必须重新编译 Android 引擎；做法、本机构建环境与当前验证结果见
[docs/android.md](docs/android.md)。

---

## 现在能玩到什么程度

先把话说清楚：**主线流程、NPC 对话与世界对象提示已经全中文，但并没有把所有界面边角都译完。**
下表给的是实测口径，每一项都写明「译了多少」和「还会在哪儿看到英文」。

| 部分 | 现状 | 还会看到英文的地方 |
|---|---|---|
| 界面文字（菜单、设置、角色创建、物品栏、法术书、炼金台、日志、队伍面板……） | 覆盖表 5747 条；1.19 新增的战利品汇总、背包搜索、截图提示、存档列表日期也已汉化 | 引擎源码里散落的硬编码文案仍有约 495 条候选未收录（含大量误报与日志串），实际能看到的多集中在灵气／光环说明、掉落过滤说明、新角色向导等长文案 |
| NPC 对话正文与选项 | 全量覆盖：lua 的 `SetMessage` 1512 条 + `SimpleMessage`／`StatusText` 506 条手译；话题名、招呼语、职业描述、乞求／贿赂／威胁的条件台词、新闻话题标题全部中文 | 极少数解谜用字母串（方尖碑密文）按原样保留，避免破坏谜题 |
| 世界对象 | 装饰物 Hint（树／岩石／花草……130 条）、事件名（门、箱子、拉杆、传送点……）、世界物品交互提示全部中文 | 无（内部占位名 `_misc191` 之类不显示给玩家） |
| 物品名／描述／词缀 | 名称与描述约八成半取自 MMMerge 官方简中包；词缀 260 条已全覆盖；内部占位物品名补了中文占位 | MMMerge 新增而官方语言包没收录的物品名 |
| 怪物／NPC 名、屋名、地图名、技能、法术、书籍 | 名称列已无英文残留：怪物、NPC、房屋、地图（含 MM9 地名音译）、`House NNN` 占位屋名全部补齐 | 少量内部占位名（`Random MapNPC N`、`quest item N` 等）按占位处理 |
| 1.19 新功能 | 战利品汇总面板、背包搜索框、地图进度“一键拾取”、PrintScreen 截图提示、重做后的读档列表均已汉化 | 新增译文里若出现字体子集外的字会显示成空白，重跑 `tools/font_subset.py` 即可 |

完整的缺口清单、按文件的条数分布、以及「哪些是误报」见 **[docs/progress.md](docs/progress.md)**。
想自己扫一遍，不用进游戏截图：

```bash
python tools/dev/check_translation_rules.py  # 机制性检查：占位符/裸拼/缺条目/半拼接/术语（必须 0）
python tools/dev/audit_visible_text.py    # 屏幕文本残留英文验收（对话/世界对象/NPC/表项）
python tools/dev/check_table_residue.py    # 已部署数据表里残留的纯英文正文
python tools/check_literals.py --show 60  # 源码硬编码 UI 文案缺口（含误报）
```

## 安装

从 [Releases](../../releases) 下载 `OpenYAMM-<版本>-zh_cn.zip`，解压覆盖到游戏目录即可。
详细步骤和排错见 **[docs/install.md](docs/install.md)**。

补丁由两部分组成：

- `mods/engine/` —— 译文数据表与中文字体，引擎启动时叠加在自带资产之上；
- `openyamm.exe` —— 由 [vnimy/openyamm](https://github.com/vnimy/openyamm) 按对应 tag 重编的引擎，
  能光栅化 UTF-8、按码点排版、按中文规则断行。exe 与 mods 必须同版本。

**只换 mods 不换 exe 是没用的**：原版引擎拿到 UTF-8 字节会当成 CP1252 乱码渲染。

## 目录

```
corpus/
  mmmerge/       MMMerge 官方简中包解出来的 30 张原始表（可重建，见 tools/extract_corpus.py）
  overrides/     覆盖表与语料——汉化的主要工作面
                  manual_zh.tsv（手写的界面文案与占位文本，1649 条）
                  lua_dialog_zh.tsv（SetMessage 对话正文，生成）
                  lua_extra_mm6_zh.tsv / lua_extra_rest_zh.tsv（lua 的非 SetMessage 消息，手译）
                  world_objects_zh.tsv（装饰物提示、残留表项、新闻标题）
                  templates_zh.tsv（代码动态拼接文案的模板）
                  event_names_zh.tsv、house_names.tsv、enchant_names_zh.tsv、npc_professions_zh.tsv
                  ui_text.txt（上面这些合成出来的最终覆盖表，勿手改）
  reports/       缺口清单等中间稿
tools/           语料生成、覆盖表合成、字体烘焙、打包、审计
  dev/           排查/验收脚本（check_translation_rules.py 机制检查、audit_visible_text.py 屏幕文本、按文件细查）
scripts/         一键构建（build.ps1 / build.sh）
tests/scenarios/ 无头回归场景（不开窗口验证译文）
assets/fonts/    思源黑体（Noto Sans SC）与其 OFL 许可证
docs/            安装、构建、引擎改动、开发笔记、术语表、进度、[汉化原则](docs/translation-principles.md)
```

## 实现要点

下面讲的是**为什么这么改**；代码本身在 fork 里，用 `git -C ../openyamm log -p -- <文件>` 能看到
每一处改动和它的理由。

### 1. 字形：从「256 个字节槽」到「码点 → 字形」

原引擎给每个字体开 256 个槽，用字节值直接索引，本质上只能画 CP1252。
改造后 `FontAtlas::glyph` 按 Unicode 码点查表，图集按实际位图尺寸打包，字体描述文件新增
`metrics: freetype`、`glyphs:`、`padding:` 三个键。带 `glyphs:` 的面按布局尺寸烘焙一次，不随显示尺寸重光栅化。

中文字库动辄几万字，整张贴图装不下，所以 `tools/font_subset.py` 扫全部译文，把实际用到的码点写成
`cjk_glyphs.txt`，只烘焙这一份子集。

### 2. 排版：中文要按字断行

`engine/TextLayout.cpp` 重写了断行：宽字符按码点切分，遇到避头标点（`，。、？！：；）》」`）不放在行首。
菜单、HUD、角色创建界面三处的测量／截断／折行全部改走这套逻辑——否则中文会溢出按钮或把标点顶到行首。

### 3. 覆盖层：不改数据表，改「界面出口」

有大量文案改不了数据表：

- 屋名被 `HouseInteraction` 拿去做逻辑判断（旅店、公会、Baa 神殿），改了会静默失效；
- NPC 对话正文根本不在表里，是 `events/*.lua` 里 `evt.SetMessage("...")` 的字面量；
- 界面文案散落在 `game/ui/` 各处传给绘制函数的字符串里。

所以引擎侧新增 `game/ui/UiText` 覆盖层，读 `data_tables/english/ui_text.txt` 的「原文 → 译文」表，
支持整串精确、`*` 前缀、`{占位符}` 模板三种匹配。所有文本在**测量、截断、断行之前**先过一遍覆盖表，
布局才会按中文宽度算。

模板匹配是用来解决语序的。英文拼出来的句子是 `Bronze Ring of Earth Resistance`，
中文得是 `御土青铜戒指`——源码里改成

```cpp
UiText::translateTemplate("{item} {suffix}", {{"{item}", baseName}, {"{suffix}", suffix}});
```

语序就落到译文表里（`"{item} {suffix}"` → `"{suffix}{item}"`），不用为每一种词缀写死代码。

### 4. 语料：不重译，按记录 ID 对齐

译文主体来自 MMMerge 整合版的官方简体中文语言包（`10 LocZHCN.EnglishT.lod` 与 `Data/Text localization/ZHCN_*.txt`），
`tools/extract_corpus.py` 把它们解成 UTF-8，`tools/build_patch.py` 按记录 ID 填进 OpenYAMM 的同名表。
术语参考 [mm678-i18n](https://github.com/might-and-magic/mm678-i18n)。

## 自己构建

需要 Python 3.10+、CMake、MinGW 或 MSVC，以及 [vnimy/openyamm](https://github.com/vnimy/openyamm) 的源码树：

```bash
git clone https://github.com/vnimy/openyamm.git ../openyamm
git -C ../openyamm checkout v1.19.3-zh_cn     # 与本仓库 CHANGELOG 的版本对应
```

```bash
python tools/make_ui_text.py                      # 合成 corpus/overrides/ui_text.txt
python tools/build_patch.py --openyamm ../openyamm --out build/mods
python tools/font_subset.py --patch build/mods --openyamm ../openyamm \
       --out build/mods/engine/fonts/truetype
python tools/build_fonts.py --font assets/fonts/NotoSansSC.ttf \
       --license assets/fonts/OFL.txt --out build/mods
```

或者一行：`scripts/build.sh --openyamm ../openyamm`（Windows 用 `scripts\build.ps1`）。

`mods/` 只在**打包资产**布局下挂载：把 exe 放进 release 安装的 `app/<版本>/`，与 `assets/`、`mods/` 同级运行即可；
`-DOPENYAMM_DEV_ASSETS_DIR` 与这件事无关（它只决定开发期的资产根）。
完整步骤、依赖与踩坑见 **[docs/build.md](docs/build.md)**；引擎侧改了哪些文件见
**[docs/engine-changes.md](docs/engine-changes.md)**。

## 参与翻译

只改 `corpus/overrides/` 下的表就够了，不需要碰 C++，也不用改 Python：

1. 在 `manual_zh.tsv` 里补一行 `原文<TAB>译文`（或改掉现有译文）；
2. 跑 `python tools/make_ui_text.py` 重新合成 `ui_text.txt`；
3. 提 PR。

格式约定、前缀规则、模板占位符、常见错误的处理见 **[CONTRIBUTING.md](CONTRIBUTING.md)**。

## 已知限制

- **不是 100% 汉化**。界面与对话都有已知缺口（见上面的状态表和 [docs/progress.md](docs/progress.md)），
  碰到英文属于正常范围；想推动的话，把出现英文的面板名报 issue 就行，不用截图。
- `stats.txt` / `skill_des.txt` / `class.txt` 的第一列是引擎查表用的英文键，必须保持英文，只翻描述列。
- 带换行的文案在表里写作字面 `\n`，**不能写真实换行**——表是一行一条，真换行会把记录切断。
  （这个坑踩过一次：一条旅店台词把表拆成了 5 行。）
- 覆盖表在启动时一次性载入，改完**必须重启游戏**。
- MM6／MM7 的 `worlds/mm6/_legacy/tables/` 是原始表，OpenYAMM 目前还没接入运行时；接上后可复用同一套管线。

## 致谢

- [OpenYAMM](https://github.com/pjasicek/openyamm) —— 引擎本体（GPL-3.0-or-later）
- [vnimy/openyamm](https://github.com/vnimy/openyamm) —— 本项目的引擎分支，上面所有 C++ 改动都在这里
- MMMerge 与其官方简体中文语言包 —— 译文主体来源
- [mm678-i18n](https://github.com/might-and-magic/mm678-i18n) —— 术语参考
- [思源黑体 / Noto Sans SC](https://fonts.google.com/noto/specimen/Noto+Sans+SC) —— 中文字形（SIL OFL 1.1）

## 许可

本仓库的脚本、文档与译文表以 **MIT** 发布，见 [LICENSE](LICENSE)。
字体、游戏文本与 MMMerge 译文的版权归属与限制见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。

本项目是玩家自制的非官方本地化工程，**不包含游戏本体或任何原始美术／音效资源**。
Might and Magic 系列商标与内容版权归 Ubisoft 所有。
