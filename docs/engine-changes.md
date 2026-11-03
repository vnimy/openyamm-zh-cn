
## 附：1.18 → 1.19 的增量（2026-10-30）

上游 1.19 改了 87 个文件，与汉化重叠 11 个，三方合并后新增/保留的覆盖表接入点：

| 文件 | 1.19 的改动 / 汉化处理 |
|---|---|
| `game/ui/GameplayLootSummaryRenderer.cpp`（新） | 战利品汇总面板：`{satchels} satchels emptied, {items} items taken`、`{gold} gold`、`{gold} gold (followers took {share})` 改 `UiText::translateTemplate`；标题/表头走覆盖表 |
| `game/gameplay/GameplayScreenController.cpp` | 多袋规则下旧背包放不下的提示改 `{count} items from the old bags did not fit and lie at your feet` 模板 |
| `game/ui/GameplayMapProgressBar.cpp` | 地图进度“一键拾取”提示改 `{binding}: loot all` 模板；弹窗标题走覆盖表 |
| `game/ui/screens/LoadGameScreen.cpp` | 存档列表重做：`formatDate`/`formatClock` 的月份、星期、AM/PM 先翻译；`Saved {date}`、`Save {number}` 改模板；删除/读取/替换/标准/自动存档/快速存档等走覆盖表 |
| `game/ui/GameplayPartyOverlayRenderer.cpp` | 背包搜索框占位文本 “Search items (...)” 走覆盖表 |
| `game/items/ItemSearch.*`（新） | 搜索逻辑，无界面文案 |
| 设置 | `Minimap zoom`、`Quick save`/`Quick load` 标签补进覆盖表 |
{h,cpp}`（新增）

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

## 五、Android 端（1.18 起）

Android 版必须重编引擎，另外需要让 Android 也加载 `mods/`：上游在 `game/app/main.cpp` 用
`#if !defined(__ANDROID__)` 排除了 `modsRoot`，且 `engine/AssetFileSystem.cpp` 的 Android APK 资产分支
没有挂载点。改动共 4 处（`main.cpp`、`AssetFileSystem.cpp`、`android/app/src/main/cpp/openyamm_android_entry.cpp`、
`MusicStream.cpp` 的无 FFmpeg 兜底），细节、构建流水线与产物见 **[android.md](android.md)**。

## 同步到新版本

上游发新版时，改动集中在 `game/ui/` 与 `game/items/`，通常只需三方合并，重点看：

- `FontAsset` 与 `MenuScreenBase` 的字形接口有没有再变；
- 新增的 `game/ui/*.cpp` 里有没有新的硬编码文案 → 跑 `tools/check_literals.py` 就能知道；
- `english/global.txt` 这类表名在新版本里可能改名（1.17 就从 `global.txt` 变成了 `Global.txt`）。

## 附：1.17 → 1.18 的增量

上游 1.18 改了 75 个文件，与汉化重叠 6 个，三方合并后新增接入覆盖表的面：

| 文件 | 1.18 的新文案 |
|---|---|
| `game/ui/screens/MainMenuScreen.cpp` | 「Assign Key」弹窗、更新器倒计时与下载进度模板 |
| `game/ui/screens/LoadGameScreen.cpp` | 排序按钮 `Name`/`Newest`、规则过滤 `All`、存档类型 `Automatic`/`Quick`/`Manual`/`New save` |
| `game/gameplay/JournalArcomageRuntime.cpp` | 魔幻牌日志页：大陆统计、酒馆清单（模板） |
| `game/gameplay/GameplayScreenRuntime.cpp` | 休息提示、敌情警告、回合制／即时制切换、施法失败 |
| `game/ui/GameplayPartyOverlayRenderer.cpp` | 电影化调色开关、`(off)` 后缀、笔记搜索无结果提示 |

升级全过程见 [upgrading.md](upgrading.md)。

## 附：2026-10-30 补缺轮的引擎改动

这一轮补的是「对话里夹英文、选项还是英文、树显示 tree」的根因，C++ 侧新增的接入点：

| 文件 | 改动 |
|---|---|
| `game/events/EventDialogContent.cpp` | 贿赂按钮改 `translateTemplate("{topic} {cost} Gold")`；公会加入兜底改 `"Join guild for {cost} gold"` 模板；`formatNpcProfessionText` 的 `%05/%06/%07/%08/%11/%12` 先 `UiText::translate` 再注入（时段、职业、声誉等级原先会插英文），并补了 `%03/%09/%10` 三个原先未处理的占位符 |
| `game/gameplay/GameplayDialogController.cpp` | 佣兵自荐长句改 `{name}/{impression}/{class}` 模板，印象词与职业名先翻译 |
| `game/gameplay/GameplayInteractionController.cpp` | 世界对象/角色交互提示统一过覆盖表；`{verb} ({name})`、`Get {item}`、`You found an item ({item})!` 改模板 |
| `game/gameplay/GameplayHeldItemController.cpp` | 事件给物品的提示改 `You found something ({item})!` 模板 |

配套的覆盖表条目在 `corpus/overrides/templates_zh.tsv` 与 `manual_zh.tsv`（交互动词、`Drop *` 前缀等）。
这些文案在渲染层本来也会查覆盖表，改在生成处是为了让**动态拼出来的整句**也能命中模板（渲染层只能整串匹配）。

## 附：调试控制台的 ImGui 动态图集契约（2026-11-03 恢复）

这一节记录的是**丢失后恢复**的设计，不是新设计。2026-11-03 的误覆盖事故里，
`game/debug/GameImGuiBgfxRenderer.{h,cpp}` 与 `game/app/GameApplication.cpp` 的相关改动整段消失
（这三个文件当时与上游 v1.19 逐字节相同，三方合并没有 base 可用）。丢失后的症状是控制台里的中文
全部变成 `?`，因为 ImGui 退回内置 ASCII 字体。

### 为什么必须声明 `ImGuiBackendFlags_RendererHasTextures`

ImGui 1.92 的字形是**懒加载**的：某个字号第一次用到某个码位时才去栅格化，并把结果通过
`ImTextureData` 交给后端增量上传。如果后端不声明 `RendererHasTextures`，
`ImGui::UpdateFontsNewFrame()` 会在首帧后把 `atlas->Locked` 置真（imgui.cpp 里 `atlas->Locked = true`），
之后所有字形请求被静默丢弃。ASCII 在第一帧就全加载过所以看不出来，中文则一个都进不来。

### 三个必需件

| 文件 | 必须做的事 |
|---|---|
| `game/debug/GameImGuiBgfxRenderer.cpp` `initialize()` | 置 `io.BackendFlags |= ImGuiBackendFlags_RendererHasTextures`；**不要**再调 `GetTexDataAsRGBA32()` 自建一张静态图集 |
| 同上，新增 `updateTextures()` | 遍历 `ImGui::GetPlatformIO().Textures`，按 `ImTextureStatus` 处理：`WantCreate` → `bgfx::createTexture2D` + `SetTexID(handle.idx + 1)`；`WantUpdates` → 对每个 `ImTextureRect` 调 `bgfx::updateTexture2D`（pitch 用 `pTexture->GetPitch()`）；`WantDestroy` → `bgfx::destroy` + `SetTexID(ImTextureID_Invalid)` + `SetStatus(ImTextureStatus_Destroyed)` |
| `game/app/GameApplication.cpp` | 建字体（`installImGuiCjkFont`，等价于旧文档里的 `loadDebugConsoleFont`），并在 `ImGui::Render()` 之后、`renderDrawData()` 之前调 `updateTextures()` |

### 字体本身

`game/debug/ImGuiCjkFont.{h,cpp}`：从 mod 读 `fonts/truetype/openyamm_cjk.ttf`，
码位区间由 `fonts/truetype/cjk_glyphs.txt` 生成（与引擎字体共用同一份，两套图集覆盖的字符因此一致），
区间做相邻合并后再交给 `AddFontFromMemoryTTF`。`FontDataOwnedByAtlas = false`，
所以 TTF 字节存函数内 `static`，活得和进程一样久（1.92 要求字体数据在整个图集生命周期内有效）。

### 不要做的事

- **不要**为了让字大而"按最终像素预烘焙图集"。控制台在移动端用
  `ImGui::SetWindowFontScale(activeMobileConsoleScale())`（1.55~2.45 倍）放大布局；
  动态图集会按放大后的字号**重新栅格化**，所以放大反而清晰；预烘焙 + 放大只会糊。
- **不要**删掉 `SetWindowFontScale` 那行。
- 移动端还要置 `ImGuiConfigFlags_IsTouchScreen` 以及 `ScrollbarSize/GrabMinSize = 26`、
  `TouchExtraPadding`，否则手指按不住滚动条、轻点会被判成拖动。

### 验收

本机 shell 无法启动游戏窗口（原始 exe 同样 `exit=1`，缺交互桌面会话），
所以这部分只能靠「桌面 + 安卓双目标编译链接通过」+ 真机目视。真机上若中文重新变成 `?`，
就是 `RendererHasTextures` 那条路没生效。
