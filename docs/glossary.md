# 术语表

> 术语的核对方法、五类根因与验收流程见 [汉化原则](translation-principles.md)。

统一译名是汉化最容易散架的地方。这一页记录核心术语的定译与取舍理由，便于新译文对齐。
完整对照（4000+ 条）直接在 `corpus/overrides/ui_text.txt` 里搜。

## 属性

| 原文 | 定译 | 备注 |
|---|---|---|
| Might | 力量 | |
| Intellect | 智力 | |
| Personality | 个性 | 不是「魅力」——原版属性影响的是交涉与部分法术效果，沿用 MMMerge |
| Endurance | 耐力 | |
| Accuracy | 精确 | |
| Speed | 速度 | |
| Luck | 运气 | |
| Hit Points | 生命值 |
| Armor Class | 防御等级 |
| Skill Points | 技能点数 | |
| Spell Points | 魔法值 | |

## 抗性

| 原文 | 定译 |
|---|---|
| Fire Resistance | 火系抗性 |
| Air Resistance | 风系抗性 |
| Water Resistance | 水系抗性 |
| Earth Resistance | 土系抗性 |
| Mind Resistance | 心系抗性 |
| Body Resistance | 体系抗性 |

抗性名以官方表为准：按**古典四元素+心/体**的固定说法，风、心、体三项不是「气系/心智/肢体」。
注意 `Body` 的两义：作为**技能**是「肢体魔法」，作为**抗性**是「体系抗性」——不要混。

## 魔法学派

| 原文 | 定译 |
|---|---|
| Fire Magic | 火系魔法 |
| Air Magic | 空气魔法 |
| Water Magic | 水系魔法 |
| Earth Magic | 土系魔法 |
| Spirit Magic | 灵魂魔法 |
| Mind Magic | 心智魔法 |
| **Body Magic** | **肢体魔法** |
| Light Magic | 光明魔法 |
| Dark Magic | 暗黑魔法 |

`Body Magic` 只能叫「肢体魔法」。曾出现「身体魔法」的混用，已统一；
验收脚本 E 项会拦住这类回潮。

## 职业与种族

| 原文 | 定译 |
|---|---|
| Knight | 骑士 |
| Cleric | 牧师 |
| Necromancer | 死灵法师 |
| Vampire | 吸血鬼 |
| Dragon | 龙 |
| Dark Elf | 黑暗精灵 |
| Troll | 巨魔 |
| Minotaur | 牛头人 |

## 技能等级

| 原文 | 定译 | 覆盖表键 |
|---|---|---|
| Normal | 普通 | `SkillMastery: Normal` |
| Expert | 专家 | `SkillMastery: Expert` |
| Master | **大师** | `SkillMastery: Master` |
| Grandmaster | 宗师（技能页缩写为「宗师」） | `SkillMastery: Grandmaster` |

**`Master` 必须分两个键。** 它同时是僧侣最终职业名（官方译「智者」）和技能等级名（官方译「大师」）。
共用一个键会把职业名也翻成「大师」，或把等级翻成「智者」——这正是 2026-11-03 反馈里的问题。

所以源码里显示等级名一律走 `localizedMasteryName()` / `localizedMasteryEntry()`，
它们查 `SkillMastery: <英文名>` 前缀键；`masteryDisplayName()` 保留英文原文，只给代码做判断用。

## 常见界面词

| 原文 | 定译 | 说明 |
|---|---|---|
| Inventory | 物品栏 | 不用「背包」——「背包」留给 `packs`（负重容器） |
| Journal | 日志 | |
| Rest | 休息 | |
| Identify | 鉴定 | 动词与名词同形 |
| Repair | 修理 | |
| Train | 训练 | 公会里学技能是「学习」，升等级是「训练」 |
| Gold | 金币 | |

## 词缀：语序要反过来

英文词缀是后置修饰，中文得前置。引擎侧走模板 `"{item} {suffix}"` → `"{suffix}{item}"`，
所以词缀译名必须是**能直接当前置定语的短词**：

| 原文 | 定译 | 组合结果 |
|---|---|---|
| of Earth Resistance | 御土 | 御土青铜戒指 |
| of Carnage | 屠戮 | 屠戮青铜戒指 |
| of Frost | 寒霜 | 寒霜长剑 |

不要译成「……的」——「大地的青铜戒指」既不像装备名，也会让物品栏排不下。

## 几条原则

1. **专有名词跟 MMMerge，不自创。** 人名、地名、神殿名一律沿用官方简中包的译法，
   否则玩家对照攻略会找不到地方。译文主体就是按记录 ID 从那份包里取的。
2. **界面文案要短。** 按钮只有那么宽，宁可省字也不要溢出。测量与截断由引擎按中文字形宽度做，
   但译文本身太长时仍然会被截掉尾部。
3. **同一英文在不同语境可以有不同译法，但不能在同一条目里摇摆。** 例如 `Master` 在技能等级里是「大师」，
   在僧侣职业名里是「智者」——用两个独立的键（`SkillMastery: Master` 与裸 `Master`），互不影响。
   新出现的多义词照此办理，不要让一个键承担两种含义。
4. **不译保持英文的**：技能专名（`Arms Master`、`Disarm Trap` 等作为查表键的列）、
   表头第一列、内部占位名（`_misc191`、`quest item 600`）。
