# 汉化原则：按根因分类，不做「点名修一句」

这份文档写给以后接手的人（也包括 AI）。**用户反馈某句没翻时，不要只补那一句。**
先判断它属于哪一类根因，然后把这一类全量扫一遍，最后把检查固化进验收脚本——
否则下一轮反馈还是同一类问题换个地方出现。

2026-11-03 那一轮反馈就是典型：用户报了 7 处，实际背后是 6 类结构性问题，影响数百处。

## 六类根因

### A 类：模板已译，占位符的值没译

**症状**：句子骨架是中文，里面夹着英文单词。例：「花 2000 金币把 **Bow** 提升为 **Expert**」。

**成因**：`UiText::translateTemplate("Become {mastery} in {skill} for {cost} gold", …)` 只翻模板本身，
填进去的 `{mastery}` / `{skill}` 是数据层的英文原名。覆盖表按整串匹配，管不到占位符里的值。

**做法**：占位符实参自己也要过翻译。
- 技能名统一走 `displaySkillName()`（内部已翻）。
- 等级名统一走 `localizedMasteryName()`。
- 其它数据层名字（物品、职业、学派）同理，别把英文原名直接塞进模板。

**检查**：`check_translation_rules.py` 的 A 项会找出 `translateTemplate` 里直接塞
`masteryDisplayName(...)` 这类英文名函数的调用。

### B 类：整句裸拼英文，根本没走翻译层

**症状**：整句英文照原样显示，比如拾取提示 `You found an item (…)!`、旅行确认
`It will take 5 days to travel to …`。

**成因**：C++ 里 `"It will take " + std::to_string(days) + " day" + …` 直接拼好交给 UI。
覆盖表按整串匹配，拼出来的串从来不在表里。

**做法**：把拼接改成 `UiText::translateTemplate`，静态部分进覆盖表、动态部分走占位符。
数字后面带单位时（`5 days`），单位单独成一条模板（`{count} days` → `{count} 天`），
中文语序才好排。

**检查**：B 项扫所有 UI 输出调用（`setStatusBarEvent`、`painter.text`、`.label =`、
`lines.push_back` 等）里的英文字面量，没被 `UiText` 包住就报。

### C 类：覆盖表缺条目

**症状**：代码已经调了 `UiText::translate("…")`，但屏幕上还是英文。

**成因**：覆盖表里没这条键。常见于新增界面、上游升级带来的新文案。

**做法**：补条目。注意几个细节：
- **半译**：已有译文里仍夹英文的（专有名词白名单除外），也要扫出来补。
- **`%NN` token**：`npc_topic_text` 等表的正文带 `%02`/`%05`/`%06`/`%10` 这类人名/敬称 token。
  译文必须**原样保留 token**、位置正确，否则要么匹配不上，要么人名不替换。不能把 token 写死成人名。
- **引号**：引擎有弯引号归一兜底，但表里的键一律写 ASCII 引号最稳。
- **多行表**：`npc_topic_text` / `npc_greet` 必须按引擎加载规则先折成逻辑记录再合并
  （`tools/build_patch.py` 的 `FOLDED_TABLES`），否则英文续行会接在中文后面。

**检查**：C 项扫源码里所有 `UiText::translate` 用到的字面量，覆盖表没有就报。

### D 类：只翻了前缀，后半仍是英文

**症状**：「已鉴定 Bronze Ring.」「Can't drop 长剑」这类中英混排。

**成因**：`UiText::translate("Identified ") + 名字` —— 只包了前半句。

**做法**：改成 `UiText::translateTemplate("Identified {item}.", {{"{item}", 名字}})`。

**检查**：D 项扫 `UiText::translate("…") +` 这种形态。

### E 类：术语不一致

**症状**：同一个概念在不同界面不同叫法（「肢体魔法」另一处叫「身体魔法」、「大师」被译成「智者」）。

**成因**：多人/多轮翻译各写各的；或者一个英文词有多种含义。

**做法**：
1. 以官方标准译名为准——`github.com/might-and-magic/mm678-i18n`
   的 `references/notes/zh/customlist.list` 按 context（`skilldes` / `stats` / `class` / `items` …）
   给出每个词的权威译法。
2. 一个英文词多种含义时，**不要共用一个键**。典型例子：`Master`
   - 作为僧侣最终职业 → **智者**
   - 作为技能等级 → **大师**
   所以技能等级查的是 `SkillMastery: Master` 前缀键，不查裸 `Master`。

**检查**：E 项拿术语表（`check_translation_rules.py` 的 `GLOSSARY` / `TERM_VARIANTS`）
核对覆盖表里的值。

### F 类：引号形态不匹配（译文静默失效）

**症状**：覆盖表里明明有译文，游戏里却是英文。典型如装备特殊效果
「特殊：Luck (+10), Int (+10)」——属性缩写一个都没翻。

**成因**：引擎的 `engine/TextTable.cpp` `parseTabSeparated()` 会把**整体被双引号包裹**的单元格
剥成不带引号的串：

```
表里:  "Luck (+10), Int (+10)"     <- 单元格被引号包裹
运行时: Luck (+10), Int (+10)      <- 引擎已剥掉引号
```

覆盖表按整串精确匹配，键写成了带引号的样子 → 永远命中不了，而且**没有任何报错**，
看起来就像「这条没译」。

**做法**：
1. 生成覆盖表的脚本在写入前统一剥掉包裹整个串的引号（`make_enchant_names.py` 的 `put()` 已这么做）。
2. 判断键的形态时以「引擎读表后拿到什么」为准，不是以「文件里写着什么」为准。
3. 整句模板之外，再补一份单词级条目兜底（如 `Luck`→运气、`Int`→智力、`Spd`→速度、`SP`→魔法值、
   `Per`→个性、`End`→耐力、`Acc`→精确、`AC`→防御等级），这样即便某个整句漏了，
   至少缩写本身能看懂。

**检查**：F 项扫资产包里所有被引号包裹的单元格，若覆盖表里有带引号的键、却没有剥引号后的键，
就报出来。

## 官方术语表速查（节选）

| 类别 | 英文 | 官方中文 |
|---|---|---|
| 武器技能 | Staff / Sword / Dagger / Axe / Spear / Bow / Mace / Blaster / Shield | 手杖 / 长剑 / 匕首 / 战斧 / 长矛 / 弓箭 / 钉锤 / 榴弹枪 / 盾牌 |
| 魔法学派 | Fire / Air / Water / Earth / Spirit / Mind / Body / Light / Dark (Magic) | 火系 / 空气 / 水系 / 土系 / 灵魂 / 心智 / **肢体** / 光明 / 暗黑 魔法 |
| 其它技能 | Identify Item / Repair Item / Disarm Traps / Body Building / Armsmaster / Stealing | 物品鉴定术 / 修补术 / 陷阱拆卸术 / 健身术 / 武器使用术 / 偷窃术 |
| 属性 | Might / Intellect / Personality / Endurance / Accuracy / Luck | 力量 / 智力 / 个性 / 耐力 / 精确 / **运气** |
| 抗性 | Fire / Air / Water / Earth / Mind / Body | 火系 / **风系** / 水系 / 土系 / **心系** / **体系** 抗性 |
| 面板 | Hit Points / Spell Points / Armor Class / Skill Points | 生命值 / 魔法值 / **防御等级** / 技能点数 |
| 等级 | Expert / Master / Grandmaster | 专家 / **大师** / 宗师 |

注意「Body」的两义：作为**技能**是「肢体魔法」，作为**抗性/属性**是「体系抗性」。

## 验收流程

出包前必须都过：

```bash
python tools/dev/check_translation_rules.py   # A–E 五类，必须 0 命中
python tools/dev/audit_visible_text.py        # 可见文本，阻断性缺口必须 0
```

外加无头场景回归（在已安装游戏目录里跑）：

```bash
cd ../game
for s in item_inspect_test npc_dialog_test baa_letter_test maria_moon_test isaac_shop_test \
         skill_name_test zh_text_coverage; do
  ./app/1.19/openyamm.exe --headless-run-scenario ../openyamm-zh-cn/tests/scenarios/$s.yml
done
```

## 上游升级时

按 [docs/upgrading.md](upgrading.md) 走完三方合并后，**先跑这两个检查**。
上游新增的界面文案会集中暴露成 C 类缺口，新写的拼接会暴露成 B/D 类，
合并时把覆盖表接入点漏掉会直接体现在 A 类。
