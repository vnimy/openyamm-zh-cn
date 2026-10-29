# OpenYAMM 简体中文补丁

把 [OpenYAMM](https://github.com/OpenYAMM/OpenYAMM)（魔法门 6／7／8 的开源重制引擎）的文本系统从
「单字节 CP1252 + 256 个字形槽」改造成「UTF-8 + 按 Unicode 码点取字形」，再配上整套简体中文译文，
让这三部二十多年前的老游戏能在现代分辨率下正常显示中文。

> Simplified Chinese localization for OpenYAMM (an open-source reimplementation of Might and Magic VI/VII/VIII).
> The engine's 8-bit text path is replaced by UTF-8 with per-codepoint glyph lookup, plus a full zh_CN translation
> layer. Documentation is in Chinese; the code comments are too.

---

## 现在能玩到什么程度

| 部分 | 状态 | 说明 |
|---|---|---|
| 界面文字（菜单、设置、角色创建、物品栏、法术书、炼金台、日志、队伍面板……） | 基本完成 | 覆盖表 4291 条，按原文整串／前缀／模板三种方式匹配 |
| NPC 对话正文 | 完成 | 1512 条，正文其实不在数据表里，来自内容包 lua 的字面量 |
| 物品名／描述／词缀 | 完成 | 6583 格译自 MMMerge 官方简中包，词缀 260 条走展示层，并反转了「青铜戒指 of 御土」的语序 |
| 怪物／NPC 名、屋名、地图名、技能、法术、书籍 | 完成 | 30 张 MMMerge 表按记录 ID 对齐 |
| 字形渲染 | 完成 | 思源黑体子集，只烘焙译文实际用到的汉字 |
| 引擎源码里剩余的硬编码文案 | 进行中 | `tools/check_literals.py` 报告 620 条待译（含误报，见 [docs/progress.md](docs/progress.md)） |

想自己看还差哪些，不用进游戏截图：

```bash
python tools/check_literals.py --show 60
```

## 安装

从 [Releases](../../releases) 下载 `OpenYAMM-<版本>-zh_cn.zip`，解压覆盖到游戏目录即可。
详细步骤和排错见 **[docs/install.md](docs/install.md)**。

补丁由两部分组成：

- `mods/engine/` —— 译文数据表与中文字体，引擎启动时叠加在自带资产之上；
- `openyamm.exe` —— 按 1.17 源码重编的引擎，能光栅化 UTF-8、按码点排版、按中文规则断行。

**只换 mods 不换 exe 是没用的**：原版引擎拿到 UTF-8 字节会当成 CP1252 乱码渲染。

## 目录

```
corpus/
  mmmerge/       MMMerge 官方简中包解出来的 30 张原始表（可重建，见 tools/extract_corpus.py）
  overrides/     覆盖表与语料——汉化的主要工作面
                  manual_zh.tsv（手写的界面文案，1279 条）
                  lua_dialog_zh.tsv（对话正文）、event_names_zh.tsv、house_names.tsv、
                  enchant_names_zh.tsv、npc_professions_zh.tsv
                  ui_text.txt（上面这些合成出来的最终覆盖表，勿手改）
  reports/       缺口清单等中间稿
tools/           语料生成、覆盖表合成、字体烘焙、打包、审计
  dev/           排查用的一次性脚本（按文件细查、提取布局文案）
scripts/         一键构建（build.ps1 / build.sh）
tests/scenarios/ 无头回归场景（不开窗口验证译文）
assets/fonts/    思源黑体（Noto Sans SC）与其 OFL 许可证
docs/            安装、构建、引擎改动、开发笔记、术语表、进度
```

## 实现要点

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

需要 Python 3.10+、CMake、MinGW 或 MSVC，以及一份 OpenYAMM 1.17 源码树。

```bash
python tools/make_ui_text.py                      # 合成 corpus/overrides/ui_text.txt
python tools/build_patch.py --openyamm ../openyamm-1.17 --out build/mods
python tools/font_subset.py --patch build/mods --openyamm ../openyamm-1.17 \
       --out build/mods/engine/fonts/truetype
python tools/build_fonts.py --font assets/fonts/NotoSansSC.ttf \
       --license assets/fonts/OFL.txt --out build/mods
```

exe 要用「打包资产」方式构建（`-DOPENYAMM_DEV_ASSETS_DIR:STRING=assets`），否则运行时不会挂载 `mods/`。
完整步骤、依赖与踩坑见 **[docs/build.md](docs/build.md)**；引擎侧改了哪些文件见
**[docs/engine-changes.md](docs/engine-changes.md)**。

## 参与翻译

只改 `corpus/overrides/` 下的表就够了，不需要碰 C++，也不用改 Python：

1. 在 `manual_zh.tsv` 里补一行 `原文<TAB>译文`（或改掉现有译文）；
2. 跑 `python tools/make_ui_text.py` 重新合成 `ui_text.txt`；
3. 提 PR。

格式约定、前缀规则、模板占位符、常见错误的处理见 **[CONTRIBUTING.md](CONTRIBUTING.md)**。

## 已知限制

- `stats.txt` / `skill_des.txt` / `class.txt` 的第一列是引擎查表用的英文键，必须保持英文，只翻描述列。
- 带换行的文案在表里写作字面 `\n`，**不能写真实换行**——表是一行一条，真换行会把记录切断。
  （这个坑踩过一次：一条旅店台词把表拆成了 5 行。）
- 覆盖表在启动时一次性载入，改完**必须重启游戏**。
- MM6／MM7 的 `worlds/mm6/_legacy/tables/` 是原始表，OpenYAMM 目前还没接入运行时；接上后可复用同一套管线。

## 致谢

- [OpenYAMM](https://github.com/OpenYAMM/OpenYAMM) —— 引擎本体（GPL-3.0-or-later）
- MMMerge 与其官方简体中文语言包 —— 译文主体来源
- [mm678-i18n](https://github.com/might-and-magic/mm678-i18n) —— 术语参考
- [思源黑体 / Noto Sans SC](https://fonts.google.com/noto/specimen/Noto+Sans+SC) —— 中文字形（SIL OFL 1.1）

## 许可

本仓库的脚本、文档与译文表以 **MIT** 发布，见 [LICENSE](LICENSE)。
字体、游戏文本与 MMMerge 译文的版权归属与限制见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。

本项目是玩家自制的非官方本地化工程，**不包含游戏本体或任何原始美术／音效资源**。
Might and Magic 系列商标与内容版权归 Ubisoft 所有。
