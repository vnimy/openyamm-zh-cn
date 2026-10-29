# 汉化进度

数据截至 2026-10-29（OpenYAMM 1.17）。

## 覆盖表规模

| 表 | 条目 | 作用 |
|---|---:|---|
| `ui_text.txt` | 4291 | 引擎硬编码界面文案（菜单、设置、HUD、面板、物品词缀、事件名、屋名的合并结果） |
| `lua_dialog_zh.tsv` | 1512 | NPC 对话正文（内容包 lua 的 `evt.SetMessage` 字面量） |
| `house_names.tsv` | 887 | 屋名／店名（源码拿英文名做逻辑判断，只能展示层替换） |
| `event_names_zh.tsv` | 546 | 世界对象名：门、箱子、水池、神龛、传送点…… |
| `enchant_names_zh.tsv` | 260 | 物品词缀（25 标准属性 + 25 标准词缀 + 78 特殊描述 + 68 特殊词缀 + 65 特殊详述） |
| `npc_professions_zh.tsv` | 77 | NPC 职业名（「某人 the 某某」的后半句） |

数据表侧的译文来自 MMMerge 官方简中包，按记录 ID 对齐，30 张表：

| 表 | 覆盖 | 说明 |
|---|---:|---|
| `npc_news` | ~99% | 酒馆传闻 |
| `global` | ~99% | 界面通用串 |
| `monster_data` | ~99% | 怪物名 |
| `npc_names` | ~97% | NPC 名 |
| `npc_topic_text` | ~90% | NPC 对话正文（表里这份运行时其实不读，正文在 lua 里） |
| `items` | ~86% | 物品名／未鉴定名／备注 |
| `map_stats` | ~80% | 地图名 |
| `npc_greet` | ~76% | NPC 招呼语 |
| `trans` | ~59% | 传送点描述（其余多为 `Placeholder Text`） |
| `stats` / `skill_des` / `class` | 描述列 | 第一列是查表键，必须保持英文 |

剩余英文主要是 MMMerge 新增、官方语言包没覆盖的记录，以及 `_misc191`、`quest item 600` 这类内部占位名。

## 引擎源码里还没译的界面文案

```bash
python tools/check_literals.py --show 0
```

当前报告 **620 条**。按文件分布（前 15）：

| 条数 | 文件 |
|---:|---|
| 69 | `GameplayJournalAuras.cpp` |
| 47 | `GameplayDialogController.cpp` |
| 41 | `GameplayPartyOverlayInputController.cpp` |
| 39 | `HouseInteraction.cpp` |
| 36 | `GameplayCombatController.cpp` |
| 28 | `HouseServiceRuntime.cpp` |
| 28 | `MonsterSpellSupport.cpp` |
| 26 | `ActorBehaviorRuntime.cpp` |
| 25 | `GameplayJournalProgress.cpp` |
| 24 | `GameplayAlchemyBenchRenderer.cpp` |
| 23 | `NewGameScreen.cpp` |
| 19 | `MainMenuLootFilter.cpp` |
| 19 | `GameplayProjectileService.cpp` |
| 18 | `MainMenuScreen.cpp` |
| 17 | `GameplayInteractionController.cpp` |

要注意这个数字**含误报**：脚本按「像不像界面文案」的形态规则筛，日志串、内部 key、
拼装用的片段常常也会被算进来。实际待译量比 620 少，判断标准是「玩家能不能在屏幕上看到这句话」。

## 还没动的部分

- `npc_topic.txt` 的话题名（「Star Lake」之类）仍是英文。这张表的正文运行时不读（正文在 lua 里），
  但话题菜单上会显示，需要单独补一张覆盖表。
- `npc_topic_text.txt` 有 58 个重复键、30 个空键，来自 MMMerge 表本身的结构问题；因为运行时不走这张表，
  暂不处理。
- MM6／MM7 的 `worlds/mm6/_legacy/tables/` 原始表，OpenYAMM 还没接进运行时，接上后可直接复用现有管线。

## 认领一块

想帮忙的话，挑上面表格里的一个文件，跑

```bash
python tools/check_literals.py --files game/ui/GameplayJournalAuras.cpp --show 0
```

把缺口抄进 `corpus/overrides/manual_zh.tsv`，重新生成、提 PR 即可。格式与注意事项见
[CONTRIBUTING.md](../CONTRIBUTING.md)。
