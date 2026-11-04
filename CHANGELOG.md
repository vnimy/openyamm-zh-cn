# 更新记录

版本号跟随所对应的 OpenYAMM 版本；补丁自身的修订用第三位表示。

## 1.20.3 — 2026-11-04

### 修复：新游戏选 MAW 后点起始大陆没反应

`NewGameScreen::selectContinent` 会先激活规则集；激活失败就 `return`，界面既不提示也不跳转，看起来像点击没响应。
日志 `game/openyamm.log` 里每次点击都留了一行：

```
Failed to apply ruleset table engine/rulesets/maw/patches/spells.txt: override line 2: key 'Fire Spike' must match exactly one row
New game: the MAW ruleset tables could not be loaded
```

MAW 的法术补丁按**英文法术名**（`keyColumn: 2`）定位行，而汉化把 `data_tables/spells.txt` 的名字列整体译成了中文，
188 条键一条也匹配不上（引擎要求「恰好命中一行」）。这一次不是漏翻，是「被翻译的列同时是别人查表的键」。

### 工具

- 新增 `tools/ruleset_patch_keys.py`：从安装内容的 `engine.rulesets` 包里读规则集补丁，按
  「英文名 → 记录 id → 译名」重写键列（值原样保留），产物写进 `mods/engine/rulesets/<id>/`；
  `--check` 按引擎口径复核补丁键能否恰好命中一行，出包前跑一次。
- `scripts/build.sh` / `scripts/build.ps1` 增加该步骤（找不到 `../game/assets/packs` 时跳过并提示）。
- `docs/dev-notes.md` 记入这条边界：`keyColumn` 指到的列同样禁止「只顾着翻」。

### 产物

- 已部署到本机 `game/mods`（`engine/rulesets/maw/patches/spells.txt`，188 条键）。
- 桌面包 `dist/OpenYAMM-1.20-zh_cn.zip`（33,454,188 B，SHA256 `573327AC…B116D94`）：
  这次按 `build/mods` 重新打包。上一个包是拿 `dist/staging/mods`（6:36 的快照）压的，
  缺了 1.20.2 的方尖碑修复与重建的 `map_stats.txt`——逐文件 SHA256 比对时 45 个文件有 2 个对不上，
  所以「沿用 1.20.2 的产物」会把已知修复挡在门外。包内 `openyamm.exe` 为含引擎改动的 1.20 构建。
- 安卓包 `build-android/artifacts/OpenYAMM-1.20-android-arm64-zh.apk`（51,193,094 B，
  SHA256 `16F0D98E…1428F6DDC`）**未重新构建**：它内置的 `assets/mods` 仍是 6:36 的快照，
  因此安卓端暂时看不到 1.20.2 的方尖碑修复，等下一版重出 APK 才会带上。

## 1.20.2 — 2026-11-04

### 修复：方尖碑消息显示成密文（`_t_staoi_on_oiz_`）

铁拳城堡的方尖碑事件在 `mm6.core/events/maps/outd3.lua` 里硬编码了整条消息：

```lua
evt.SetMessage("The surface of the obelisk is blood warm ... <156 个空格> _t_staoi_on_oiz_")
```

覆盖表原本只译了「方尖碑的表面……」这句前缀，**结尾的密文原样保留**，玩家看到的
就是一串像变量名的拉丁字母。官方简中语料的做法是把密文替换成**解码后的中文片段**
（`Autonote.txt` 里已有），本次按这个口径改了 13 条整句译文，并补 38 条「裸密文 → 中文片段」
条目兜底单独显示的情况。

### 工具

- 新增 `tools/dev/check_lua_message_literals.py`：扫内容包 lua 的 `SetMessage` 等字面量，
  核对覆盖表。**标注为诊断用、未校准**——引擎的引号归一与前缀规则尚不能完全复刻，
  会出现误报，不接进出包阻断门禁。
- 修 `build-android/pack_zh_apk.ps1`：Java 源码路径写死 `openyamm-<版本>`，1.20 起源码树统一叫
  `openyamm`，改为先试版本目录再退回 `openyamm`；同时把脚本内的中文注释换成 ASCII
  （PowerShell 5.1 按 ANSI 读 UTF-8 注释会导致变量赋值异常）。

### 产物

- 桌面包 `dist/OpenYAMM-1.20-zh_cn.zip`（33,452,830 B）
- 安卓包 `build-android/artifacts/OpenYAMM-1.20-android-arm64-zh.apk`（51,192,998 B，
  SHA256 `96ABD6B1…D311062`）

## 1.20.1 — 2026-11-04

处理本轮用户反馈（继续按根因归类，不做点名补译）。

### 修复

- **先知「探险历程」正文仍是英文**：真凶是 lua 的 `string.format` 动态句
  （`This is {month}, the month of {mighty}.\nJourney to the Shrine of {map} ...`），
  `make_lua_dialog.py` 只抓 `SetMessage("字面量")`，抓不到这种写法。
  已按 12 个月逐条枚举最终句（变量固定），并补「等待下个月」提示。
  新增 `tools/dev/check_lua_format_messages.py` 扫描这类消息。
- **增益效果与法术名不一致**（「魔力神眼」在增益里变「巫师之眼」、「圣灵佑佐」变「祝福」）：
  双重原因——① 部署的 `ui_text.txt` 是过期产物（6154 行 vs 源表生成的 5747 行），
  残留旧键静默覆盖官方译名；② 同名不同义只能给一种译法。
  新增 `SpellName:` 语境键 111 条 + `UiText::translateInContext`，增益面板按语境查，
  与法术书保持同一官方译名。
- **装备特殊效果属性缩写**（「Luck (+10), Int (+10)」）：引擎读表会剥掉包裹单元格的引号，
  覆盖表键带引号则永远匹配不上（F 类）。生成脚本统一剥引号，并补属性缩写词条。
- **安卓控制台没有「界面英文报告」按钮**：上一轮只把按钮加进桌面版的 `renderQuickActions()`，
  而安卓走的是 `renderMobileQuickActions()`，两个面板是两套代码，所以手机上根本点不到。
  已补到移动端快捷操作列；同时把 `UI Text Report` / `Dump UI Text` 和 `uireport` 的五条回显
  补进 `console_zh.tsv`（此前桌面版按钮本身也是英文），并让桌面版开关后缀也走翻译（`[On]`/`[Off]`）。

### v1.20 接入点补齐

v1.20 同步上游时部分汉化接入点被覆盖回去，已补回：拾取提示（含随从金币分成）、
旅行确认框 4 个句式、房屋选项标签、物品详情/炼金台/MAW 说明等 30 余处半拼接、
120 处裸英文字面量。

### 验收

- 覆盖表 5476 → 6080 条
- 六类阻断检查 + 实体名冲突检查全部 0 命中
- 8 个无头场景在 1.20 上全通过（新增先知朝圣场景）

## 1.20.0 — 2026-11-04

跟进上游 OpenYAMM 1.20（tag `v1.20`，commit `1add1d3`，18 个提交）。引擎与译文同步升级，PC 与 Android 两套产物都基于 1.20 重出。

- 引擎：`v1.20.0-zh_cn` 由 [vnimy/openyamm](https://github.com/vnimy/openyamm) 合并上游后的提交重编（Windows `openyamm.exe` + Android `libmain.so`）。
- 合并冲突只有 2 个文件 3 处（`game/rules/maw/MawItemRules.cpp`、`game/gameplay/GameplayPartyOverlayInputController.cpp`），解法一致：取上游新逻辑，再把用户可见文案重新包回 `UiText::translate`。汉化文本层（`game/ui/UiText.*`、`engine/FontAsset.*`、`engine/TextLayout.*`、`game/ui/MenuScreenBase.cpp`、`game/ui/MenuDesignScreen.cpp`、`game/ui/GameplayHudCommon.cpp`、`game/debug/ImGuiCjkFont.*`）上游一个字节都没碰，合并后与 1.19 版逐字节相同。
- `map_stats.txt` 按 1.20 基表重建：上游 1.20 把 MM9 怪物 id 改成带命名空间的名字（`Ogre Warrior` → `MM9 Icky` 等 32 行），整表替换的补丁会把这一改动回退。现在以 1.20 基表为准、只搬回 201 条地图译名，其余列与上游逐字节一致（`tools/dev/merge_map_stats_120.py`）。
- Android APK 改在官方 `OpenYAMM-1.20-android-arm64.apk` 上重打包（之前用 1.19 壳的包作废），签名与 1.19 包相同，可直接覆盖升级。
- 文档：两个仓库的 README 都补了「资源包（游戏内容）怎么下载、怎么用」——频道清单 URL、`packs/<sha256>.zip` 规则、PC 的自动／命令行／手动离线四种用法、安卓首次下载与 1.19→1.20 的 13 个包增量；`docs/install.md`、`docs/android.md` 的版本与产物信息同步到 1.20。

### 已知问题

- 1.20 新增的界面文案还没进覆盖表：`GameMechanics::equipRefusalReason`（`Requires the X skill`／`Requires N Might`／`Requires N Accuracy`）与 `ItemRuntime::wearRequirementText`（`Knights only`／`Men only` 等）由上游直出英文、未接 `UiText::translate`，运行时显示英文。
- 本轮只做「引擎跟到 1.20 + 数据表按 1.20 重建」，没有全量重扫 1.20 的新文案；缺口清单待下一轮用 `tools/dev/audit_visible_text.py` 与 `tools/check_literals.py` 重测。

## 未发布

- 文档：把「引擎源码」这条依赖写实。引擎改动全部在 [vnimy/openyamm](https://github.com/vnimy/openyamm)，
  按版本打 tag；本仓库只出译文、字体与工具，不再声称自己保存 C++ 源码。
- `docs/upgrading.md` 重写：从「没有上游仓库，手工三方合并」改成 `git merge upstream/vX.Y` 的流程，原来的手工迁移记录降级为附录。
- `docs/engine-changes.md` 补回被吃掉的开头（一级标题与「一、文本层」），并把 1.18→1.19 的增量表挪到附录区。
- `docs/android.md` 去掉 2026-10-30 的过时状态行（1.19 的 APK 已经出了），并修掉一处非法字节。
- README 增加「两个仓库」一节与版本对应表；`docs/build.md`、CONTRIBUTING、构建脚本的示例路径同步更新。

## 1.19.3 — 2026-11-03

恢复调试控制台的 ImGui 动态字体图集，并把这一轮补完的译文接上钩子。

### 根因（G 类：丢失的改动没有出处）

2026-11-03 的误覆盖事故里，`game/debug/GameImGuiBgfxRenderer.{h,cpp}` 与
`game/app/GameApplication.cpp` 的定制整段消失 —— 当时它们与上游 v1.19 逐字节相同，
三方合并没有 base 可依。症状是控制台中文全变 `?`（ImGui 退回内置 ASCII 字体）。

恢复要点见 `docs/engine-changes.md` 的「调试控制台的 ImGui 动态图集契约」：必须声明
`ImGuiBackendFlags_RendererHasTextures` 并在每帧处理 `ImTextureStatus` 的
WantCreate/WantUpdates/WantDestroy，否则 1.92 的字形懒加载在首帧后就被锁死。

### 同时补上

| 项 | 内容 |
|---|---|
| 物品属性 | `resolveItemInspectDetailText` 两份副本（`GameplayPartyOverlayRenderer.cpp` / `OutdoorGameView.cpp`）的 Armor / Charges / Attack-Damage / Shoot-Damage / Power / Uses / Duration 全部改模板键 |
| 法术与增益时长 | `formatCharacterDetailDuration`、`formatRemainingDuration`、`personalBuffName`、队伍增益名与标题接覆盖表 |
| 房屋服务 | 动作标签（Sell/Repair/Deposit/Buy Standard/Buy Special/Bounty Hunt/Learn Skills）、房屋标题、洛蕾塔对白、无队员提示 |
| 译文缺口 | 补齐 100 处「钩子已在、译文缺失」的键；这一批运行时一律返回英文，是最隐蔽的一类 |
| 存档迁移 | `migrateLocalizeJournalTrainerNotes`：读档时按注记自记的「技能 - 等级」重算教师注记，老存档也变中文 |

## 1.19.2 — 2026-11-03

修「装备特殊效果里的属性缩写仍是英文」（如明月头盔的「特殊：Luck (+10), Int (+10)」），
并把它归进新的一类根因。

### 根因（F 类：引号形态不匹配）

引擎的 `engine/TextTable.cpp` `parseTabSeparated()` 会把**整体被双引号包裹**的单元格剥成不带引号的串。
`special_item_enchants.txt` 里有 24 条描述列是这个形态（`"Luck (+10), Int (+10)"` 等），
而覆盖表按「带引号」的原文写了键 —— 运行时引擎拿到的是剥掉引号的串，**永远匹配不上，且不报错**，
看起来就像整条没译。

### 修复

- `tools/make_enchant_names.py`：`put()` 统一剥掉包裹整个串的引号再入表；
  `missing` 自检也用归一后的形态，不再把这类误报成「已覆盖」。
- 补一份**属性缩写**词条兜底：`Luck` 运气、`Int`/`Intelect` 智力、`Per` 个性、`Spd` 速度、
  `SP` 魔法值、`End` 耐力、`Acc` 精确、`AC` 防御等级、`HP` 生命值、`Res` 抗性。
- 24 条被引号包裹的描述全部恢复中文（明月→「运气（+10），智力（+10）」、
  苍穹→「智力（+10），速度（+10），法术（+10）」等）。

### 验收

- `check_translation_rules.py` 新增 **F 项**：扫资产包里被引号包裹的单元格，
  若覆盖表只有带引号的键、没有剥引号后的键就报错。六项检查当前全部 0 命中。
- 新增 `tools/dev/check_table_residue.py`：扫已部署数据表里还剩多少纯英文正文
  （区分玩家可见与编辑器备注），用来发现「官方语料本身缺译」的记录。
- 无头场景 `item_inspect_test.yml` 改为直接覆盖本次反馈的三件装备
  （明月/苍穹/御土青铜戒指），验证 `special_line` 输出为中文。

## 1.19.1 — 2026-11-03

修「逐个反馈点补译」的老路：这次按**结构性根因**归类，每类都做全量清扫并固化成可阻断的验收项。
报告见 [docs/translation-principles.md](docs/translation-principles.md)。

### 引擎（机制修复）

- **等级名不再当职业名翻**：`SkillMastery` 的 Master 与僧侣最终职业「Master（智者）」同形，共用一个键会把
  职业名也翻错。新增 `localizedMasteryName()` / `localizedMasteryEntry()`，等级名查 `SkillMastery: <名>` 前缀键，
  取不到才退回裸写法。技能页、角色页、炼金台、新游戏、MAW 技能、训练对话共 8 处接入。
- **显示名函数内部走 UiText**：`displaySkillName()` 自己就翻译，调用方不必再包一层；
  `masteryDisplayName()` 保留英文原文供代码判断（`Grandmaster`→`Grand` 的缩写依赖它）。
- **拾取提示**：`formatWorldItemPickupStatusText()`、新增 `formatFoundGoldStatusText()` 走模板；
  室内/室外/统一交互三条拾取路径与「随从分成」金币提示全部接入。
- **旅行确认框**：`EventDialogContent` 的 `It will take N days to travel to …` /
  `Do you wish to leave|enter {place}?` / `Do you wish to leave this area?` 由裸拼改成模板，天数单独成句
  （中文写「5 天」而不是「5 days」）。对话框所有按钮 label 统一过 `UiText`。
- **物品详情**：`Attack/Shoot/Armor/Charges/Power/Uses/Duration/Broken` 等拼接改成模板；
  时长单位 `:yr/:mo/:dy/:hr/:mn` 也进覆盖表。
- **房屋选项标签**：`makeOption()` 统一在入口翻一次，覆盖 `Buy Standard`、`Learn Skills` 等全部调用点。
- **330 处裸英文字面量**批量包进 `UiText::translate()`（幂等：查不到原样返回），
  并把「只翻了前缀」的半拼接（`translate("Identified ") + 名字`）逐条改成完整模板。

### 译文

- 覆盖表 5740 条（+264）。新增技能名/等级名/职业名、训练与升级对话、旅行与进出场所、拾取与金币、
  附魔与物品详情、地图进度（竞技场/次元模式）、商店买卖修理、MAW 光环与物品等模板。
- **按官方标准校正术语**（来源 `github.com/might-and-magic/mm678-i18n` `references/notes/zh/customlist.list`）：
  `Bow` 弓→**弓箭**、`Spear` 矛→**长矛**、`Blaster`→**榴弹枪**、`Armor Class`→**防御等级**、
  `Luck` 幸运→**运气**、`Air Resistance`→**风系抗性**、`Mind Resistance`→**心系抗性**、
  `Body Resistance`→**体系抗性**；`Body Magic` 统一为**肢体魔法**（原先「身体魔法/肢体魔法」混用）。
  九大学派、技能、属性全部对齐官方表。

### 验收

- 新增 [tools/dev/check_translation_rules.py](tools/dev/check_translation_rules.py)，把五类根因做成阻断检查：
  A 占位符未译、B 裸拼英文、C 覆盖表缺条目、D 半拼接、E 术语不一致。当前**全部 0 命中**。
- 新增两个无头场景：`skill_name_test.yml`（技能名与等级名）、`zh_text_coverage.yml`（关键文案）。
- 全部 7 个场景在 1.19 + 1.19 内容包 + 汉化 mods 下通过。

## 1.19.0 — 2026-10-30

跟进 OpenYAMM 1.19。

### 引擎

- 上游 1.18 → 1.19 变更 87 个文件（无二进制），按 [docs/upgrading.md](docs/upgrading.md) 的做法逐文件三方合并：
  67 个文件直接换成上游版本、6 个新增文件、11 个两边都改过的文件 `git merge-file` 合并（仅 `LoadGameScreen.cpp`
  一处冲突，手工合成）。汉化新增的 `UiText` / `TextLayout` 与全部覆盖表接入点保留。
- 1.19 新界面接入覆盖表：清空地图后的战利品汇总（标题、袋子/物品计数、金币与随从分成、留在袋子里的提示）、
  背包搜索框占位文本、地图进度“一键拾取”提示、PrintScreen 截图提示、重做后的读档/存档列表（日期、星期、
  “保存于”、删除/读取/替换/标准/自动存档/快速存档等）。
- 存档列表的日期与时间不再拼英文：`formatDate`/`formatClock` 的月份、星期、AM/PM 走覆盖表，
  `Saved <date>`、`Save <n>` 改模板。

### 构建

- 新增 `openyamm-1.19` 构建树与构建脚本；`zstd`/`etcpak`/`etc2comp` 预解压到 `toolchains/deps/` 后用
  `FETCHCONTENT_SOURCE_DIR_*` 指向本地，配置期不再联网。
- 修掉 FFmpeg `make install` 在 cmd 进程树里把头文件列表截断的问题（手动 `make install` + 补头文件）。

### 译文

- 覆盖表 5476 条（+37）。1.19 新增/漏译的界面文案补进 `manual_zh.tsv`。

## 1.18.1 — 2026-10-30

补对话与世界对象的漏译。线上反馈集中在「NPC 对话里夹英文」「选项还是英文」「树显示 tree」，
根因都在生成流程与覆盖表，不在个别译文。

### 修复

- **多行表单元格没折叠**（最大根因）：`npc_topic_text` / `npc_greet` 的译文只写进第一条物理行，
  引擎把后面的英文续行接在中文后面，出现「中文……\nEnglish tail」。`build_patch.py` 现在按引擎加载
  规则把物理行折成逻辑记录再合并，一次清掉 717 条英文尾巴与 79 条夹英文招呼语。
- **`npc_news` 第 2 列没翻译**：它会被当成新闻话题按钮显示（「Begging」等），现已随正文一起翻。
- **lua 的 `SimpleMessage` / `StatusText` 整类漏掉**：陷阱、神龛祝福、任务提示、学识之骨等 506 条已手译。
- **世界对象提示没进覆盖表**：装饰物 `Hint` 130 条（树、岩石、花草……）、世界对象交互提示
  （开门／拾取／搜刮／使用拉杆……）已补。
- **动态拼接文案**：贿赂价格、公会会费、佣兵自荐、`%01`～`%17` 台词占位符（含 `%03/%09/%10`）
  改为 `UiText` 模板；NPC 台词里的时段、职业名、声誉等级先翻译再注入。
- **残留占位/表项**：`Placeholder`、`Missing Text N`、`Put Text Here N`、`House NNN`、MM9 地图名、
  部分怪物名、`Price fixing` 任务文本已补中文。

### 译文与工具

- 覆盖表 5439 条（+1122）：新增 `lua_extra_mm6_zh.tsv`（322）、`lua_extra_rest_zh.tsv`（184）、
  `world_objects_zh.tsv`（292）、`templates_zh.tsv`（8），`manual_zh.tsv` 1649 条。
- 新增 `tools/dev/audit_visible_text.py`：按 `UiText::translate` 规则扫屏幕文本（lua 消息、装饰物提示、
  事件名、NPC/房屋/地图/怪物/物品名），返回 0 才算通过。
- 新增无头回归场景：`tests/scenarios/baa_letter_test.yml`、`maria_moon_test.yml`、`isaac_shop_test.yml`。

### 已知问题

- 引擎源码硬编码 UI 仍有约 495 条候选（含误报/日志串），集中在灵气说明、掉落过滤说明、新角色向导等长文案，
  见 [docs/progress.md](docs/progress.md)。
- 方尖碑密文按原样保留（拼字谜题）；MM9 地名按音译处理。

## 1.18.0 — 2026-10-29

跟进 OpenYAMM 1.18。升级流程沉淀成 [docs/upgrading.md](docs/upgrading.md)，新工具
`tools/dev/detect_engine_changes.py` 按内容哈希找本地改动，不再依赖 `git status`。

### 引擎

- 上游 1.18 变更 75 个文件，与汉化重叠 6 个，全部三方合并（`MainMenuScreen::captureBinding`
  一处上下文漂移，手工对齐）。
- 新界面文案接入覆盖表：魔幻牌（Arcomage）日志页、读档界面按名称／时间排序、
  存档类型（自动／快速／手动／新存档）、电影化调色开关、休息提示、更新器提示等。

### 译文

- `manual_zh.tsv` 新增约 25 条；覆盖表 4317 条（1.17 时 4291 条）。

## 1.17.0 — 2026-10-29

首个公开版本，对应 OpenYAMM 1.17。

### 引擎

- 字形系统从「256 个字节槽」改为「码点 → 字形」，图集按实际位图尺寸打包；
  字体描述文件新增 `metrics: freetype`、`glyphs:`、`padding:`。
- 新增 `engine/TextLayout`：宽字符断行、避头标点处理。菜单、HUD、角色创建三处的测量／截断／折行统一走它。
- 新增 `game/ui/UiText` 覆盖层：整串精确、`*` 前缀、`{占位符}` 模板三种匹配，
  外加 `titleWithName` 处理「某人 the 某某」的中文语序。
- 覆盖表加载时机提前到文本测量之前，否则菜单仍按英文宽度排版。
- 进游戏时也装载覆盖表（原先只有菜单装载，游戏内文案全部漏掉）。
- lua 绑定层统一过覆盖表：`SetMessage` / `SimpleMessage` / `StatusText`，NPC 对话正文得以汉化。
- 拼接文案改模板：物品全名、词缀属性、买卖／鉴定／修理台词、队友进出提示等。

### 译文

- 覆盖表 4291 条；对话正文 1512 条；屋名 887 条；事件名 546 条；词缀 260 条；NPC 职业 77 条。
- 数据表 30 张，按记录 ID 对齐 MMMerge 官方简中包。
- 角色创建界面随机名池改成中文（480 个名字，8 列）。
- 物品词缀反转语序：`Bronze Ring of Earth Resistance` → 「御土青铜戒指」。

### 工具

- `tools/check_literals.py`：扫引擎源码里的界面字面量，报告覆盖表缺口。不用进游戏截图核对。
- `tools/make_ui_text.py`：把手写译文表与各路语料合成一张覆盖表，同名后者覆盖前者并报告合并数。
- `tools/build_patch.py`：一次生成全部译文数据表，跑完打印每张表的翻译行数。
- `tools/font_subset.py` + `tools/build_fonts.py`：只烘焙译文用到的码点，避免几万字整库进图集。
- `tools/extract_corpus.py` + `tools/decode_zhcn.py`：解 MMMerge 的本地化 LOD 与 `ESC + GBK` 编码表。
- `tools/paths.py`：统一路径约定，所有脚本不再写死本机绝对路径。

### 修复

- **多行文案破坏覆盖表结构**：一条旅店台词里带真实换行，把表拆成 5 行，导致其后解析错位。
  现在生成器统一把真换行转义成字面 `\n`（引擎读表时还原）。
- **角色随机名表漏打包**：`pc_names.txt` 之前是手工生成、没进构建流程，正式包里缺失。
  已并入 `build_patch.py`。
- **无头场景挂不上 mods**：`AssetFileSystem::initialize` 用了 5 参数重载，读的永远是游戏自带英文。
  改用 6 参数（含 `installedContent`）后日志出现 `Mods:`。
- **确认弹窗末行被截断**：按英文行数算框高。改为用 `UiText::translate(body)` 量行。
- **CP1252 孤立字节**：lua 里的 `0x91`／`0x92` 弯引号与表内 UTF-8 弯引号对不上，画成方块。
  `UiText::normalizeQuotes` 按 CP1252 还原，生成器与引擎两边字节级一致。

### 已知问题

- 引擎源码里仍有约 620 处字面量待译（含误报），见 [docs/progress.md](docs/progress.md)。
- `npc_topic.txt` 的话题名仍是英文。
- 只支持 1.17；启动器升级到新版本后需重新出补丁。
