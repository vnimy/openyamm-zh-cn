# 更新记录

版本号跟随所对应的 OpenYAMM 版本；补丁自身的修订用第三位表示。

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
