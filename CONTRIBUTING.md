# 参与贡献

最需要人手的其实是翻译，不需要会 C++。

## 一、补译文（最常见）

只改 `corpus/overrides/` 下的表，不碰源码。

1. 找一个还有缺口的面板：

   ```bash
   python tools/check_literals.py --files game/ui/GameplayJournalAuras.cpp --show 0
   ```

2. 在 `corpus/overrides/manual_zh.tsv` 里按 `原文<TAB>译文` 补行。
   引擎硬编码的文案都走这张表；对话正文、屋名、事件名、词缀各有自己的 tsv，别混。
   （`ui_text.txt` 是合成产物，改了会被下次生成覆盖。）
3. 重新合成并检查：

   ```bash
   python tools/make_ui_text.py        # 会打印条目数与被合并的重复
   python tools/check_tables.py        # 格式体检：漏 tab、空译文、重复键
   python tools/check_literals.py      # 缺口应当减少
   ```

4. 提 PR，说明译了哪个界面。

### 写译文时的硬规矩

- **一行一条**，用真实 `TAB` 分隔。文案里的换行写成字面 `\n`，不要敲真换行——真换行会把表切断。
- **原文必须逐字符照抄**，包括句尾句点、双空格、偏斜的引号。差一个字符就查不到。
  省事办法：从 `check_literals.py` 的输出里直接复制。
- **词缀译成能当前置定语的短词**（`of Earth Resistance` → `御土`），不要「……的」。
- **不要翻译查表键**：`stats.txt` / `skill_des.txt` / `class.txt` 第一列、技能专名列。
- 术语先查 [glossary.md](docs/glossary.md)，没有定译的就在 PR 里说明你的取舍。

## 二、改代码

工具都是 Python 3.10+，无第三方依赖。

代码风格（跟仓库现有代码保持一致）：

- 注释用中文；commit message 也用中文，说清「改了什么、为什么」。
- Python／JS 用 Tab 缩进，单行不超过 110 字符，字符串用双引号。
- 新脚本请用 `tools/paths.py` 算路径，**不要写死本机绝对路径**；
  需要外部位置的（源码树、原版安装、MMMerge）走命令行参数 + 环境变量。

提交前至少跑一遍：

```bash
scripts/check.sh
```

它做四件事：`compileall` 语法检查、`check_tables.py` 译表体检、确认 `ui_text.txt` 与源表一致、
打印当前缺口数。CI 里跑的是同一套（配置见 [docs/ci/check.yml](docs/ci/check.yml)）。

改引擎侧（C++）的话，另外看一眼 [docs/engine-changes.md](docs/engine-changes.md)，
确认没和现有改动打架——尤其是 `FontAsset` 的字形接口与 `UiText` 的查表时机（必须在测量之前）。

## 三、报问题

请带上这些信息，能省掉好几轮来回：

- 出问题的**界面名称**（不是截图也行，但要说清在哪个面板，例如「炼金台 → 试剂栏」）；
- 是**没翻译**（英文）还是**翻错了**、还是**排版坏了**（溢出／标点跑行首／方块字）；
- 游戏版本（`app/1.17/`）、补丁版本（Release 号）。

不需要截图也能定位：说清面板名，维护者跑一次
`python tools/check_literals.py --files <对应文件>` 就知道缺口在哪。

## 许可

提交的译文与代码默认以本仓库的 MIT 许可发布（见 [LICENSE](LICENSE)）。
如果你引用了他处的译文，请在 PR 里注明来源与许可。
