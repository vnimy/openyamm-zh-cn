# 旧存档载入不了

**先给结论：新版引擎能读旧版 `.oysav`。** 1.19 时期写的 version 140 存档，在 1.20 引擎上读档是通过的——
实测（1.20 headless 场景，直接用 `game/saves/save2.oysav`）：

```text
User data folder: C:\Users\<user>\AppData\Local\Temp\oyscheck\ud
Scenario validated: local.save_load_check_v140 steps=1
Scenario passed: local.save_load_check_v140
```

所以「换 1.20 之后旧档打不开」基本不是版本太旧，而是下面四条分支之一。按顺序查。

## 第一步：永远先跑 check_save.py

```bash
python tools/dev/check_save.py ../game/saves/save2.oysav
```

```text
存档：..\game\saves\save2.oysav
  大小：1,750,745 字节
  修改时间：2026-10-31 22:11:52
  文件头：b'OYSAVE1\x00' ✓
  版本：140
  结论：当前引擎可读

合计 1 个文件，退出码 0（0 = 全部引擎可读，1 = 有读不了或由更新版本写入的）
```

它只读头部 12 字节与安装清单，不反序列化内容，也不改文件。可以一次给多个文件。
加上 `--game-dir <安装根>` 还能顺带查安装侧——包数、每个 package 的 `contentSchemaVersion`、
引擎实际会扫的 `saves` 目录，以及你给的这个档在不在那个目录里：

```bash
python tools/dev/check_save.py ../game/saves/save2.oysav ../game/saves/save1.oysav \
       --game-dir D:/Projects/MM678/game
```

```text
安装根：D:\Projects\MM678\game
  版式：发布版安装（app/current 存在），当前版本 1.20
  内容清单：D:\Projects\MM678\game\app\1.20\index.json —— 166 个包，4 个 package
    engine     34 个包   contentSchemaVersion 1，包内没有 world.yml，引擎取缺省 1
    mm6        56 个包   contentSchemaVersion 1，world.yml 无该键，引擎取缺省 1
    mm7        33 个包   contentSchemaVersion 1，world.yml 无该键，引擎取缺省 1
    mm8        43 个包   contentSchemaVersion 1，world.yml 无该键，引擎取缺省 1
  User data 目录：D:\Projects\MM678\game
  读档列表扫：D:\Projects\MM678\game\saves\*.oysav —— 2 个文件
```

结论只有四种，各自对应下面一条分支：

| check_save.py 的结论 | 含义 | 看哪条 |
|---|---|---|
| 当前引擎可读 | 版本 140-142，引擎与 save-tools 都能处理 | 不是版本问题，往下看 A/B |
| 旧格式但引擎可读（save-tools 不可解码） | 版本 < 140，引擎仍读得动（旧摘要布局），但 save-tools 只吃 140-142 | 能玩就行；想让存档工具读，用引擎重新存一次 |
| 由更新版本写入 | 版本 > 142 | C |
| 不是 OpenYAMM 存档（invalid save header） | 前 8 字节不是 `OYSAVE1\0` | D |

## A · 读档列表里看不到这个档

**症状**：`saves` 里明明有文件，读档界面空着；或者列表里少了几个档但界面没报错。

**怎么确认**：看日志 `<user data 目录>\openyamm.log` 里的 `User data folder:` 那一行，它写的就是引擎认定的 user data 目录
（命令行启动时这行也直接打在控制台）：

```text
User data folder: D:\Projects\MM678\game
```

引擎只扫 **`<user data 目录>\saves\*.oysav`**，不看别的目录，也不递归子目录。user data 目录的规则
（`openyamm/engine/UserDataPaths.h`）：

1. 命令行给了 `--user-data <目录>` → 就用它；
2. 否则是**发布版安装**（安装根里有 `assets/index.json` 或 `app/current`）→ 取安装根；
3. 否则（开发构建）→ 取当前工作目录。

Windows 版式安装是第 2 条：

```text
OpenYAMM\                 ← 安装根 = user data 目录
  OpenYAMM.exe
  app\current             ← 内容是版本号，如 1.20
  app\1.20\openyamm.exe
  assets\packs\
  saves\save1.oysav       ← 引擎扫这里
  settings.ini
  openyamm.log            ← 日志，含 User data folder 那一行
```

**怎么修**，三选一：

- **Import Saves**（最省事）：读档界面上的这个按钮，选一个目录——它自己、或者它里面的 `saves` 子目录都行——
  引擎把 `*.oysav` 拷进当前 `saves`。同名文件跳过，不覆盖。
- **直接拷**：把 `.oysav` 拖进 `<user data 目录>\saves\`。
- **换目录**：`openyamm.exe --user-data "D:\旧存档目录"` 启动，让引擎去那儿找。

`check_save.py --game-dir` 会把这件事直接点出来：

```text
  在游戏扫的目录里：否
  ⚠ 游戏扫的是 D:\Projects\MM678\game\saves，你的档在 C:\Users\<user>\AppData\Local\Temp\oyscheck\v143.oysav —— 用读档界面的 Import Saves，或把文件拷进 D:\Projects\MM678\game\saves
```

另外两种情况也表现为「列表里没有」：

- 版本 > 142 的档**不显示**，界面只在底部给一句「有 N 个存档需要更新的 OpenYAMM 版本、因此未列出」的提示，
  见分支 C。
- 引擎不递归子目录：档放在 `saves\old\` 这类子目录里同样看不到，必须直接在 `saves\` 这一层。

**Android**：user data 目录是 `/sdcard/Android/data/<包名>/files/`（`settings.ini`、`saves/` 都在里面，
包名如 `org.openyamm.android`）。用文件管理器把 `.oysav` 拷进那里的 `saves/` 即可。
注意**卸载重装会连这个目录一起删**，升级前先把 `saves` 拷出来。

## B · 列表里能看到，点了报错

**症状**：档列出来了（有缩略图、有地名），点载入弹一句英文错误。

**怎么确认**：错误原文就是判定依据，对照下表。这四条来自 `openyamm/game/maps/SaveGame.cpp`
（`validateRequiredContentPackages`）。

| 错误原文 | 含义 | 怎么修 |
|---|---|---|
| `save requires missing content package '<id>'` | 存档记录了自己用到的内容包，当前安装里没有这个包 | 补内容包：主菜单 *Update to OpenYAMM 1.20* 让它把缺的包下齐，或把别人同版本的 `assets/packs` 拷过来 |
| `save requires content package '<id>' schema N, loaded schema is M` | 存档要求这个包的内容 schema 是 N，本地加载的是 M，两边不是一代内容 | 对齐版本：`index.json` 与包要成套。别只换 `index.json`、也别只换几个 zip——用同一版本渠道整体更新 |
| `save references missing item definition N` | 存档里的物品 ID N 在当前物品表里查不到（多半是物品表来自别的内容包版本，或混了旧包） | 先按上一条对齐 `assets/packs`；还缺就是这个包没下全，重下该 package |
| `save references missing vendor definition N` | 存档里商人 N 的库存状态在当前商人表里查不到，原因同上 | 同上 |

文件本身坏了是另一类，报的是 `save data is corrupted`（或带具体原因），这种不用查包，直接换个备份。

关于汉化补丁：它通过 `mods/engine/` 替换数据表与字体，**其中就有 `items.txt` 与 `house_data.txt`**——
而这两张正是存档校验会查的表。所以判断能不能接着玩英文版的档，要真去比这两张表的 ID 集合，不能想当然。

1.20 实测（本机安装）是**对得上**的：`items.txt` 两边 2203 行、`house_data.txt` 两边 1609 行，ID 差集为空，
物品行的 `packageId` 两边都取自 engine，所以上面那两条 `missing item/vendor definition` 不会由汉化触发。
换句话说：**同一版本（1.20 对 1.20）的英文版存档，可以直接在汉化版里接着玩**。
但只要有人把不同版本的补丁与内容包混装，这两张表就可能缺 ID——那时报的就是这两条错。

## C · 存档比 exe 新（version > 142）

**症状**：`check_save.py` 报「由更新版本写入」，退出码 1；读档列表里干脆看不到它。

**怎么确认**：

```text
  版本：143
  结论：由更新版本写入
  → 这个档由比当前引擎更新的版本写入；只能升级引擎，手改版本字节会把档改坏。
```

引擎读到 `version > SaveVersion`（1.20 是 142）就直接拒绝，错误原文 `written by a newer version of OpenYAMM`，
读档列表不回显这条错误，只把它计数、不在列表里列出（界面底部那句提示就是它）。

实测：把 `save2.oysav` 的版本字节改成 143（只改这 4 字节），1.20 headless 载入被拒（场景里 `expect_failure` 通过）：

```text
User data folder: C:\Users\<user>\AppData\Local\Temp\oyscheck\ud
Scenario passed: local.save_load_check_v143
```

**怎么修**：只能升级引擎（换更新的 `openyamm.exe` / 更新的版式目录）。

**不要手改版本号字节。** 头部只是第一道门：后面每一段读不读、怎么读，都由版本号决定。改成 142 之后，
引擎会按 142 的布局去解一份 143 写出来的字节流，字段整体错位——能不能过反序列化全看运气，
就算过了也是坏的档。而且原文件一旦被这样覆盖就没了，所以真要试也先复制一份。

## D · 根本不是 `.oysav`

**症状**：`check_save.py` 报「不是 OpenYAMM 存档（invalid save header）」，退出码 1：

```text
  文件头：b'hello wo' ✗（期望 b'OYSAVE1\x00'）
  版本：读不到
  结论：不是 OpenYAMM 存档（invalid save header）
```

**怎么确认**：文件头前 8 字节不是 `OYSAVE1\0`。原版 MM6/7/8 的存档、MMMerge 官方中文版的存档，
格式与 OpenYAMM 完全不同。

**怎么修**：导入不了，只能新开一局。OpenYAMM 只认自己的 `OYSAVE1` 容器，没有「原版存档转换」这条路。
（如果只是想把队伍捞回来，同一检出目录下的 `save-tools/tools/save_tool.py`（不在本仓库里）能改 OpenYAMM
存档里的金币、技能等数值——但它同样只吃 `OYSAVE1`，帮不了原版档。）

## E · 非标准规则集（MAW / Beyond Madness）的档 —— 唯一由汉化引起的载入失败

**症状**：同一个档在英文版能载入，装汉化后点载入没反应、或闪一下退回主菜单；而 `check_save.py` 报「当前引擎可读」。

**怎么确认**：`check_save.py` 现在会打印一行 `规则集：`。只有 `mmerge` 是标准规则集，出现别的值（如 `maw`）就是这一条。
日志里能对上这样的行：

```text
Failed to apply ruleset table engine/rulesets/maw/patches/spells.txt: override line 2: key 'Fire Spike' must match exactly one row
New game: the MAW ruleset tables could not be loaded
```

**原因**：规则集补丁按 `ruleset.yml` 的 `keyColumn` 在目标表里找**唯一一行**改值，一条匹配不上整份规则集就失败；
汉化把 `data_tables/spells.txt` 的法术名翻成中文后，按英文名定位的补丁（MAW 有 188 条）一条也匹配不上。
读档路径同样要先 `activateRuleset`，所以**这种失败与存档文件本身无关**——换成标准规则集的档就能进。

**怎么修**：把补丁的键列改写成译名（`tools/ruleset_patch_keys.py`，见 CHANGELOG 1.20.3），重新出包后 MAW 的档即可载入；
在那之前，MAW 的档只能回英文版接着玩。

## 让对方回传什么

报 issue 或找人看的时候，三样东西就够定位：

1. `check_save.py` 对那个档的输出——含**头 8 字节与版本号**（有 `--game-dir` 更好，连包数一起）；
2. 日志里的 `User data folder: <路径>` 那一行——它决定引擎到底扫了哪个目录；
3. 报错**原文**（照抄英文那一句，不要转述）——B 的四条错误对应四种完全不同的修法。

存档本身能不发就不发。