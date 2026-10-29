# 更新记录

版本号跟随所对应的 OpenYAMM 版本；补丁自身的修订用第三位表示。

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
