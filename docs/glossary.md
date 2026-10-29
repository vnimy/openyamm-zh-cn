# 术语表

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
| Luck | 幸运 | |
| Hit Points | 生命值 | |
| Spell Points | 法术值 | |

## 抗性

| 原文 | 定译 |
|---|---|
| Fire Resistance | 火系抗性 |
| Air Resistance | 气系抗性 |
| Water Resistance | 水系抗性 |
| Earth Resistance | 土系抗性 |
| Mind Resistance | 心智抗性 |
| Body Resistance | 肢体抗性 |

元素名单独出现时用单字：`Fire` 火、`Air` 气、`Water` 水、`Earth` 土、`Mind` 心智、`Body` 身体、
`Light` 光、`Dark` 暗。带 `Resistance` 时统一加「系」和「抗性」，避免界面里出现「火抗性」这种半截词。

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

| 原文 | 定译 |
|---|---|
| Basic | 基础 |
| Expert | 专家 |
| Master | 智者 |
| Grandmaster | 宗师 |

`Master` 译「智者」是 MMMerge 的既有译法，虽然单看容易和 NPC 头衔的「大师」混淆，
但技能界面里它总是与另外三级并列出现，歧义不大；NPC 头衔那半句走 `titleWithName`，另有对照。

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
3. **同一英文在不同语境可以有不同译法，但不能在同一条目里摇摆。** 例如 `Master` 在技能等级里是「智者」，
   在 NPC 头衔里是「大师」——两条独立条目，互不影响。
4. **不译保持英文的**：技能专名（`Arms Master`、`Disarm Trap` 等作为查表键的列）、
   表头第一列、内部占位名（`_misc191`、`quest item 600`）。
