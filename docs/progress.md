# 汉化进度

数据截至 2026-10-30（OpenYAMM 1.19）。

这份文档记的是**已经译了什么、还差什么**，不是一张「已完成」清单。判断标准优先用脚本，
其次才是进游戏转一圈：

```bash
python tools/dev/audit_visible_text.py      # 屏幕文本（对话/世界对象/NPC/表项）残留英文；返回 0 = 无缺口
python tools/check_literals.py --show 60    # 源码硬编码 UI 文案缺口（含误报）
```

## 覆盖表规模（2026-10-30）

| 表 | 条目 | 作用 |
|---|---:|---|
| `ui_text.txt` | 5476 | 最终覆盖表（下面这些源表 + MMMerge 语料合成，勿手改） |
| `manual_zh.tsv` | 1649 | 手写界面文案、世界对象交互提示、占位文本 |
| `lua_dialog_zh.tsv` | 1512 | lua `evt.SetMessage` 对话正文（由 `tools/make_lua_dialog.py` 从语料生成） |
| `lua_extra_mm6_zh.tsv` | 322 | mm6 内容包里非 `SetMessage` 的 lua 消息（`SimpleMessage`/`StatusText`）手译 |
| `lua_extra_rest_zh.tsv` | 184 | mm7／mm8／engine 内容包同类消息手译 |
| `world_objects_zh.tsv` | 292 | 装饰物 Hint、残留表项（占位话题/地图名/怪物名/新闻标题/价格垄断任务） |
| `templates_zh.tsv` | 8 | 代码动态拼接文案的 `{占位符}` 模板（贿赂价格、公会会费、佣兵自荐） |
| `event_names_zh.tsv` | 546 | 世界对象名：门、箱子、水池、神龛、传送点…… |
| `house_names.tsv` | 887 | 屋名／店名（源码拿英文名做逻辑判断，只能展示层替换） |
| `enchant_names_zh.tsv` | 260 | 物品词缀 |
| `npc_professions_zh.tsv` | 77 | NPC 职业名 |

数据表侧的译文来自 MMMerge 官方简中包，按记录 ID 对齐。当前 `build_patch.py` 的合并结果：

| 表 | 结果 | 说明 |
|---|---|---|
| `npc_topic_text` | 2680 / 2714 条有译文 | 其余为 `Placeholder`/`Missing Text`/`yes` 这类占位（已在覆盖表里换成中文占位） |
| `npc_greet` | 330 / 332 条有译文 | 余下 2 条是 `MMExt Placeholder` |
| `npc_topic` | 1756 / 1798 条有译文 | 其余是 `Placeholder`/`Put Text Here` 占位 |
| `npc_news` | 908 / 922 条有译文 | 第 2 列（Notes/Topic，部分会当话题按钮显示）也已一起翻 |
| `npc` / `npc_professions` / `house_data` | 名字、职业、店主全译 | 内部占位名（`Random MapNPC N` 等）不进画面 |
| `map_stats` / `monster_data` / `items` | 名称列无英文残留 | 内部占位名按占位处理 |
| `quests` / `scroll` / `autonote` / `trans` / `Global` / `spells` / `class` / `stats` 等 | 见构建输出 | 任务日志真正显示的正文已无英文 |

## 2026-10-30 补缺轮（本次）

线上反馈集中在「对话里夹英文」「选项还是英文」「树显示 tree」，根因与处理如下：

1. **多行表单元格没折叠干净（最大根因）**
   内容表把一段正文拆成多条物理行，译文只写进了第一行；引擎加载时会把后面的英文续行接在中文后面，
   于是出现「中文……\nEnglish tail」。`build_patch.py` 现在按引擎加载规则把物理行折成逻辑记录再合并，
   `npc_topic_text`／`npc_greet` 的 717 条英文尾巴与 79 条夹英文招呼语一次清掉。
2. **`npc_news` 第 2 列没映射**
   NPC 对话里的新闻话题按钮（「Begging」之类）读的是这列，原先只翻了正文列；现在标题列一起翻。
3. **lua 的非 `SetMessage` 消息整类漏掉**
   `SimpleMessage`／`StatusText`（陷阱、神龛祝福、任务提示、学识之骨……）共 506 条，已手译并进覆盖表。
4. **世界对象提示没进覆盖表**
   装饰物 `Hint` 130 条（树、岩石、花草、火把……）与交互提示（开门、拾取、搜刮、使用拉杆……）已补，
   并给「动词 (名字)」这类拼接加了模板。
5. **代码里动态拼接的按钮/文本**
   贿赂价格、公会会费、佣兵自荐、`%01`～`%17` 台词占位符（含 `%03/%09/%10` 这组原先未处理的）
   统一走 `UiText` 模板；NPC 台词里的时段（morning…）、职业名、声誉等级（Notorious…）也先翻译再注入。
6. **占位/残留表项**
   `Placeholder`、`MMExt Placeholder`、`Missing Text N`、`Put Text Here N`、`House NNN`、MM9 地图名、
   彩色十字军/法师类怪物名、`Price fixing` 任务文本均已补中文。

回归场景（无头，不用开窗口）：

```bash
cd <安装目录>
app/1.19/openyamm.exe --headless-run-scenario <仓库>/tests/scenarios/baa_letter_test.yml
app/1.19/openyamm.exe --headless-run-scenario <仓库>/tests/scenarios/maria_moon_test.yml
app/1.19/openyamm.exe --headless-run-scenario <仓库>/tests/scenarios/isaac_shop_test.yml
```

## 还没动的部分

- **源码硬编码 UI 文案**：`check_literals.py` 仍报约 495 条候选（含误报与日志串）。玩家可见的集中在
  灵气／光环说明、掉落过滤说明、新角色向导、调试面板帮助等长文案，不属于「房屋/NPC 对话/世界对象」范围；
  按文件挑着补即可。
- **方尖碑密文**（`Itotecthothesaip` 这类）：拼字谜题的一部分，按原样保留，只翻了提示句。
- **MM9 地名**：仓库内没有权威中文参照，按通用音译处理（索加德/斯特姆福德/德朗海姆……），有既定译名可批量替换。
- `npc_topic_text` 有 58 个重复键、30 个空键，来自 MMMerge 表本身的结构问题；运行时不走这张表的部分暂不处理。
- MM6／MM7 的 `worlds/mm6/_legacy/tables/` 原始表，OpenYAMM 还没接进运行时，接上后可直接复用现有管线。

## 认领一块

想帮忙的话，挑上面表格里的一个文件，跑

```bash
python tools/check_literals.py --files game/ui/GameplayJournalAuras.cpp --show 0
```

把缺口抄进 `corpus/overrides/manual_zh.tsv`，重新生成、提 PR 即可。格式与注意事项见
[CONTRIBUTING.md](../CONTRIBUTING.md)；改完用 `tools/dev/audit_visible_text.py` 验一遍
「对话/世界对象/表项」不再出现英文。
