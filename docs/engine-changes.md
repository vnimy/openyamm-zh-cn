# 引擎侧改动

补丁能生效的前提是引擎改过。改的是 OpenYAMM **1.17** 的源码树，本仓库只放译文与工具，不放 C++。
这一页说明改了哪些文件、为什么改，照着做可以自己复现一份能跑中文的 exe。

整体分四层：

```
语料/覆盖表  →  UiText 覆盖层  →  绘制与排版（UTF-8 / 码点）  →  FontAsset 光栅化子集字形
```

## 一、文本基础设施

### `engine/FontAsset.{h,cpp}`

原来每个字体开 256 个「字节槽」，字形的索引就是字节值，本质上是 CP1252 专用。
现在：

- 字形表改成 `码点 → 字形` 的映射，`FontAtlas::glyph` 按 Unicode 码点查；
- 图集按实际位图尺寸打包，不再假定 16×16 的等宽格子；
- 字体描述文件新增三个键：`metrics: freetype`（用自己的轮廓度量，而不是硬编码基线）、
  `glyphs:`（要烘焙的码点子集，见下）、`padding:`（图集间距，防止采样串色）；
- 新增 `decodeUtf8`（把 UTF-8 解成码点序列）与 `faceUsesOutlineMetrics`；
- 带 `glyphs:` 的面按**布局尺寸**烘焙一次，之后不再随显示尺寸重新光栅化——否则每个字号都要重烘一遍，
  中文字形太多，启动就卡死了。

### `engine/TextLayout.{h,cpp}`（新增）

宽字符断行：按码点切分；行首不放避头标点（`，。、？！：；）》」』` 等），行尾不放避尾标点（`（《「『` 等）。
没有这个，中文会把标点顶到行首、或者把整句塞进按钮里溢出。

### `engine/TextTable.cpp`

补丁写出的表必须能被引擎原样读回：单元格允许加引号，引号内 `""` 表示字面引号，tab 与换行是数据。
`tools/texttable.py` 是它的 Python 侧镜像，**两边语义必须一致**，改一边要同步改另一边。

### `game/ui/UiText.{h,cpp}`（新增）

覆盖层。读 `data_tables/english/ui_text.txt`，把「原文 → 译文」装进 `s_overrides`，提供：

| 接口 | 用途 |
|---|---|
| `translate(text)` | 整串精确匹配，其次 `*` 前缀匹配（`"Update to OpenYAMM *"` 这类动态串） |
| `translateTemplate(text, params)` | 先查表得到模板，再填 `{占位符}`；用来解决中英文语序差异 |
| `titleWithName(name, title)` | 「某人 the 某某」改成中文语序「某某某人」 |

`load()` 只跑一次（`s_overrides` 非空就直接返回）——**改完表必须重启游戏**。

还有 `normalizeQuotes`：lua 与老数据表里的引号常是 CP1252 的孤立字节（`0x91`／`0x92` 弯引号、
`0x96`／`0x97` 破折号、`0x85` 省略号）。合法 UTF-8 序列原样保留，孤立字节按 CP1252 还原，
否则查表永远差一个引号，界面上还画成方块。

## 二、绘制与排版

| 文件 | 改动 |
|---|---|
| `game/ui/MenuScreenBase.cpp` | 文本绘制／测宽改成按码点取字形，去掉固定 16×16 格子；是否按显示尺寸光栅化由描述文件决定 |
| `game/ui/GameplayHudCommon.cpp` | HUD 的绘制、测宽、截断、折行全部走 UTF-8 与码点；`renderLayoutLabel`／`renderHudFontLayer`／`wrapHudTextToWidth` 三处先查覆盖表再测量——**查表必须在测量之前**，否则布局仍按英文宽度算 |
| `game/ui/MenuDesignScreen.cpp` | 去掉 UTF-8→CP1252 的转换，文本原样透传 |
| `game/ui/screens/NewGameScreen.cpp` | 角色创建界面的折行改成码点安全，按中文规则断行；随机名池改从 mod 的 `pc_names.txt` 读 |
| `game/ui/GameplayUiController.cpp` | 进游戏时装载覆盖表（原先只有菜单装载，游戏内文案全漏） |
| `game/tables/MergedBaseTables.cpp`、`game/gameplay/HouseInteraction.cpp`、`game/ui/GameplayHudOverlaySupport.cpp` | 人名 + 头衔拼接改走 `UiText::titleWithName` |

## 三、为拼接文案加模板

英文靠空格拼出来的句子，直接翻译会得到「青铜戒指 土系抗性」这种语序。解决办法是把拼接挪进模板，
语序写进译文表。

### `game/items/ItemEnchantRuntime.cpp`

物品全名 = 基础名 + 词缀，`displayAsPrefix` 决定词缀在前还是在后。改成：

```cpp
const std::string baseName =
    UiText::translate(itemDefinition.name.empty() ? "Unknown item" : itemDefinition.name);
const auto withSuffix = [&baseName](const std::string &suffix)
{
    return UiText::translateTemplate(
        "{item} {suffix}",
        {{"{item}", baseName}, {"{suffix}", UiText::translate(suffix)}});
};
```

译文表里写 `"{item} {suffix}"` → `"{suffix}{item}"`，于是 `Bronze Ring` + `of Earth Resistance`
变成「御土青铜戒指」。词缀属性同理走 `"{stat} +{value}"`。

### `game/events/EventRuntime.cpp`

NPC 对话正文不在任何数据表里，是内容包 lua 的 `evt.SetMessage("...")` 字面量。
在 lua 绑定层统一过一遍覆盖表：`luaSetMessage`、`luaSimpleMessage`、`luaStatusText`。

### `game/gameplay/HouseServiceRuntime.cpp`

买卖、鉴定、修理的台词共 17 处改成模板，例如：

```cpp
UiText::translateTemplate("Bought {item} for {price} gold.",
                          {{"{item}", name}, {"{price}", std::to_string(price)}});
```

### 其余接入点

下面这些文件都加了 `UiText::translate` / `translateTemplate` 调用（共 25 个文件）：

```
game/events/EventDialogContent.cpp
game/events/EventRuntime.cpp
game/gameplay/CorpseLootRuntime.cpp
game/gameplay/GameplayDialogController.cpp
game/gameplay/GameplayPartyOverlayInputController.cpp
game/gameplay/HouseInteraction.cpp
game/gameplay/HouseServiceRuntime.cpp
game/gameplay/MasteryTeacherDialog.cpp
game/items/ItemEnchantRuntime.cpp
game/tables/MergedBaseTables.cpp
game/ui/GameplayAlchemyBenchRenderer.cpp
game/ui/GameplayAlchemyBenchView.cpp
game/ui/GameplayCombatLogPanel.cpp
game/ui/GameplayCraftingBenchRenderer.cpp
game/ui/GameplayHudCommon.cpp
game/ui/GameplayHudOverlaySupport.cpp
game/ui/GameplayJournalAuras.cpp
game/ui/GameplayPartyOverlayRenderer.cpp
game/ui/GameplayUiController.cpp
game/ui/MenuDesignScreen.cpp
game/ui/UiText.cpp
game/ui/UiText.h
game/ui/screens/LoadGameScreen.cpp
game/ui/screens/MainMenuScreen.cpp
game/ui/screens/NewGameScreen.cpp
```

`tools/check_literals.py` 就是按这份清单扫缺口的。

## 四、构建与测试

| 文件 | 改动 |
|---|---|
| `cmake/Ffmpeg.cmake`、`cmake/RewriteMsysPaths.cmake` | Windows 原生构建：FFmpeg 的 MSYS 路径改写为盘符路径；已存在的库跳过重建 |
| `game/CMakeLists.txt`、`game/audio/HouseVideoPlayer.cpp` | 新增 `OPENYAMM_HOUSE_VIDEOS` 开关（默认开），关掉时提供空实现 |
| `tests/*` | 字体测试改用码点接口；新增「CJK 字面烘焙」用例（设 `OPENYAMM_CJK_ASSETS` 才跑） |
| `game/scenario/ScenarioRunner.cpp` | 无头场景：`report_items` 抽成独立断言，带 `mods/` 的场景要传 6 参数 `AssetFileSystem::initialize`（含 `installedContent`）才挂载 mod |

## 同步到新版本

上游发新版时，改动集中在 `game/ui/` 与 `game/items/`，通常只需三方合并，重点看：

- `FontAsset` 与 `MenuScreenBase` 的字形接口有没有再变；
- 新增的 `game/ui/*.cpp` 里有没有新的硬编码文案 → 跑 `tools/check_literals.py` 就能知道；
- `english/global.txt` 这类表名在新版本里可能改名（1.17 就从 `global.txt` 变成了 `Global.txt`）。
