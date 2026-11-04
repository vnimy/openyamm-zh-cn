# 开发与验证笔记

这一页是给自己看的踩坑记录，也是审稿人复查译文时的手册。

## 不开窗口验证译文

汉化最怕的事情是「改完得进游戏看一眼」，一个界面一个界面截图核对。这套流程全程不用开窗口：

```bash
# 先在 yml 里描述「新开一局 → 给队伍发一件带词缀的戒指 → 报告物品名」
<安装目录>/app/<版本>/openyamm.exe --headless-run-scenario tests/scenarios/item_inspect_test.yml
```

输出（节选）：

```
ruleset item: 御土青铜戒指 ... enchant1=14/4 special_line="土系抗性 +4"
ruleset item: 寒冰青铜戒指 ... special=4  special_line="（3-4）寒冷伤害"
```

`tests/scenarios/` 下是现有的两个用例：

| 文件 | 验证什么 |
|---|---|
| `item_inspect_test.yml` | 物品全名的语序（`{suffix}{item}`）、`Special:` 行、词缀数值 |
| `npc_dialog_test.yml` | 对话正文（内容包 lua 的字面量）是否命中覆盖表 |

常用开关：

| 开关 | 作用 |
|---|---|
| `--headless-run-scenario <yml>` | 跑场景，断言失败返回非 0 |
| `--headless-validate-scenario <yml>` | 只校验脚本语法，不执行 |
| `--scenario-dry-run` | 跑但不改存档 |
| `--scenario-quiet` / `--scenario-no-color` | 安静输出／去掉 ANSI 颜色 |

**无头场景要挂 mods，`AssetFileSystem::initialize` 必须用 6 参数重载**（多传一个 `installedContent`）。
用 5 参数那个重载，跑出来的永远是游戏自带的英文——这个坑排查了半天，因为日志里一切正常，
只是 mods 静默没挂上。挂上了会在日志里看到 `Mods: <n> file(s) from ...`。

## 覆盖表格式

手写译文放 `corpus/overrides/manual_zh.tsv`，一行一条，`原文<TAB>译文`：

| 写法 | 含义 |
|---|---|
| `Cancel<TAB>取消` | 整串精确匹配 |
| `Update to OpenYAMM *<TAB>更新到 OpenYAMM ` | `*` 结尾表示前缀匹配，用于拼了版本号这类动态串 |
| `{item} {suffix}<TAB>{suffix}{item}` | 模板：先查表得到模板，再由 `translateTemplate` 填 `{占位符}` |
| `...作老师了。\n\n抱歉...` | 换行写成**字面 `\n`**，引擎读表时还原成真换行 |

`ui_text.txt` 是 `make_ui_text.py` 把源表合并出来的产物（词缀 → 事件名 → 屋名 → 补充表 →
lua 对话 → 手写译文），**不要直接改它**——下次生成就没了。补充表指 `world_objects_zh.tsv`、
`lua_extra_mm6_zh.tsv`、`lua_extra_rest_zh.tsv`、`templates_zh.tsv`（见 `EXTRA_TABLES`）。

几条硬规矩：

1. **一行一条**。文案里带真换行会把记录切断，后面几行全部失效——踩过一次：一条旅店台词把表拆成 5 行，
   连带影响了同行之后的解析。
2. **同一原文只保留最后一条**。`make_ui_text.py` 按「词缀 → 事件名 → 屋名 → 对话 → 手写译文表」的顺序合并，
   同名后者覆盖前者，避免引擎的 `unordered_map` 悄悄按加载顺序决定谁赢。合并时会打印 `N duplicates merged`。
3. **译文里不要出现真正的 tab**。
4. **改完必须重启游戏**：`UiText::load` 启动时一次性载入。

## 多行表单元格：必须先折成逻辑记录（踩坑）

`npc_topic_text`、`npc_greet` 这类表把一段正文拆成多条物理行（引擎按「首列是数字开新记录，否则把本行
首列接到上一条记录末尾」加载）。MMMerge 译文把整段折成一行写进第一条物理行，如果只替换第一行，
后面那些英文续行会被引擎接在中文后面，屏幕上就出现「中文……\nEnglish tail」。

`tools/build_patch.py` 的 `FOLDED_TABLES` / `merge_folded_records` 就是处理这个的：先按引擎规则折叠，
再按记录写回「一条记录一行」。**新接一张多行表时要先确认它属于哪一类**，否则会出现只有第一条
有译文、后面夹英文的假象。`npc_news` 的第 2 列（Notes/Topic）也会被当成新闻话题按钮显示，映射别漏。

## 查缺口

```bash
python tools/dev/audit_visible_text.py          # 屏幕文本验收：对话、世界对象、NPC、表项
python tools/dev/audit_visible_text.py --show 0 --json build/audit.json
python tools/check_literals.py                 # 源码硬编码候选（默认范围，列 40 条）
python tools/check_literals.py --show 0        # 全部
python tools/check_literals.py --files game/ui/screens/NewGameScreen.cpp
python tools/check_literals.py --write build/literals_missing.txt
```

`audit_visible_text.py` 是「玩家能不能看到英文」的验收口径：它用与 `UiText::translate` 相同的匹配规则，
扫 lua 的 `SetMessage`/`SimpleMessage`/`StatusText`、装饰物 Hint、事件名、NPC 表、房屋/地图/怪物/物品名等；
返回 0 表示这些屏幕文本没有英文残留。「源码硬编码 UI」一项只作参考（含日志与拼接误报）。

`check_literals.py` 扫 `game/ui/`、`game/gameplay/`、`game/events/` 里传给绘制函数的字符串字面量，
过滤规则是「宁缺勿滥」。所以报告里仍会有误报（日志串、内部 key、纯拼接片段）。
判断标准很简单：**这句话玩家能在屏幕上看到吗**。

界面布局（`ui/**/*.yml` 的 `value:` 与设置项的下拉标签）不在这个脚本范围里，用：

```bash
python tools/dev/extract_ui_strings.py --json build/ui_all_strings.json
```

## 字形问题

**方块／豆腐块。**
说明引擎拿到了码点，但字体图集里没有这个字形。`tools/font_subset.py` 扫的是**所有会被画出来的文本**，
新加的译文如果用了生僻字，要重跑一次 subset 再重烘字体。

**看起来像乱码的拉丁字母（`æ­¦å™¨`）。**
这是 UTF-8 字节被当 CP1252 逐字节画了：exe 没换，或者表被编辑器存成了 GBK。

**句子里有个引号永远匹配不上。**
lua 里的引号常是 CP1252 的孤立字节（`0x91`／`0x92`），跟表里的 UTF-8 弯引号不是一个东西。
`UiText::normalizeQuotes` 会把孤立字节按 CP1252 还原，所以生成器与引擎两边必须**字节级一致**地处理，
改一边要同步另一边。

## 语料来源的边界

- `corpus/mmmerge/` 的 30 张表是从 MMMerge 官方简中包解出来的，属于「别人的译文」。
  不要为了省事在 `build_patch.py` 里就地改写它们——那会让下次重建 corpus 时改动丢失。
  要调译法就写进 `corpus/overrides/`。
- `stats.txt` / `skill_des.txt` / `class.txt` 第一列是引擎查表的英文键，**禁止翻译**。
- 屋名、职业名、事件名这类被源码拿去做逻辑判断的字符串，一律走展示层覆盖，不改数据表。
- **规则集补丁的键也属于「键」**：`ruleset.yml` 的 `keyColumn` 指到哪列，补丁就按哪列找行。法术名那一列
  既是键又是显示名，翻译完 MAW 的 188 条法术补丁一条也匹配不到，引擎会放弃整份规则集——
  表现就是新游戏选完 MAW、点起始大陆**没有任何反应**（日志里是
  `Failed to apply ruleset table engine/rulesets/maw/patches/spells.txt`）。
  构建末尾用 `tools/ruleset_patch_keys.py --patch build/mods` 把键按「英文名 → 记录 id → 译名」重写一份到
  `mods/engine/rulesets/<id>/`；`--check` 按引擎口径（每个键恰好命中一行）复核，出包前跑一次。
