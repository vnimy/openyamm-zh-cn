# 跟随上游升级

引擎侧的绘制、排版与接入点在每个上游版本都会变。本仓库不保存 C++ 源码——所有引擎改动都以 commit 的
形式放在 [vnimy/openyamm](https://github.com/vnimy/openyamm) 里，所以升级不是「重新移植」，
而是一次普通的 `git merge`。

## 版本对应

| 补丁版本（本仓库） | 引擎 tag（vnimy/openyamm） | 上游基线 |
|---|---|---|
| 1.19.3 | `v1.19.3-zh_cn` | `v1.19` |

两边必须成对使用：只换 `mods/` 不换 `openyamm.exe`，官方引擎会把 UTF-8 字节按 CP1252 渲染成乱码。

## 第一步：准备两个仓库

```bash
git clone https://github.com/vnimy/openyamm.git           # 同级目录，即 ../openyamm
git clone https://github.com/vnimy/openyamm-zh-cn.git
cd openyamm && git remote add upstream https://github.com/pjasicek/openyamm.git   # 只需一次
```

`tools/paths.py` 按 `../openyamm` → `../openyamm-1.19` → `../openyamm-1.18` → `../openyamm-1.17`
的顺序探测源码树；也可以用 `--openyamm` 或环境变量 `OPENYAMM_SRC` 指定。

## 第二步：把上游新版本合进 fork

```bash
cd ../openyamm
git fetch upstream --tags
git switch zh-cn
git merge upstream/v1.21     # 分支名不带版本号，跨版本只做一次 merge
```

`zh-cn` 是 `../openyamm` 里唯一的长期分支，远端对应 `origin/main`；跨大版本不新建
`fork/<版本>` 分支，只把上游 tag merge 进来。

上游每个版本改 70～90 个文件，与汉化重叠通常 6～11 个。冲突热点见下一节。

## 第三步：处理冲突

| 文件 | 为什么爱冲突 |
|---|---|
| `game/ui/MenuScreenBase.cpp` / `.h` | 上游调绘制与测宽，我们整段换成按码点取字形 |
| `game/ui/GameplayHudCommon.cpp` | HUD 的绘制、测宽、截断、折行四处都动过 |
| `game/ui/screens/LoadGameScreen.cpp` | 存档列表几乎每个大版本都重做 |
| `game/ui/screens/MainMenuScreen.cpp` | `confirm(...)` 的签名与「再按 Esc 取消」分支变过 |
| `game/tables/MergedBaseTables.cpp` | 人名 + 头衔拼接走 `titleWithName` |
| `engine/FontAsset.cpp` / `.h` | 字形接口（码点查表、freetype 描边、padding） |
| `game/CMakeLists.txt` / `tests/CMakeLists.txt` | 新增源文件的注册行 |
| `README.md` | fork 把它换成了中文；冲突时保留 fork 版本 |

合完先扫残留标记：

```bash
find . -name '*.rej' -o -name '*.orig' -o -name '*.orig.*'
git diff --check
```

**必须守住的一点**：用来比较的内部字符串不能译。比如

```cpp
if (lowerName == "day of protection") { return "Day of Protection"; }
```

前半句是查表键，译成中文逻辑直接失效；只有返回值是展示层，才由覆盖表兜住。

## 第四步：编引擎

见 [build.md](build.md)。升级后通常要新建构建目录（旧 cache 记的是旧路径）并重跑一次配置；
带 `CMAKE_SUPPRESS_REGENERATION=ON` 的构建目录在新增源文件后必须手动重跑 `cmake -B`。

## 第五步：找新版本的界面文案

上游每加一个面板就带一批硬编码文案，钩子（`UiText::translate`）也要跟着补。

```bash
cd ../openyamm-zh-cn
python tools/check_literals.py --openyamm ../openyamm --write build/lit-new.txt    # 全量缺口
git -C ../openyamm diff --name-only v1.19..v1.20 > build/changed.txt              # 本次改动过的文件
```

两份清单求交集，**只看本次改动过的文件里的条目**，其余是历史遗留。交集中还要剔掉日志字符串
（`save_migration name=...`、`turn_based_frame reason=` 这类）、switch 分支里的内部比较值、注释。
1.18→1.19 那次交集是 39 条，其中真界面文案十来条。

钩子补完后在 `corpus/overrides/` 里加译文，然后：

```bash
python tools/make_ui_text.py
python tools/check_tables.py
python tools/dev/check_translation_rules.py
```

## 第六步：验证与出包

```bash
python tools/build_patch.py --openyamm ../openyamm --out build/mods
python tools/font_subset.py --patch build/mods --openyamm ../openyamm --out build/mods/engine/fonts/truetype
python tools/build_fonts.py --font assets/fonts/NotoSansSC.ttf --license assets/fonts/OFL.txt --out build/mods
python tools/package.py --mod build/mods \
       --exe ../openyamm/build-mingw/game/openyamm.exe \
       --out dist/OpenYAMM-<版本>-zh_cn.zip
```

无头场景（不开窗口，`tests/scenarios/` 下七个）：

```bash
cd <安装目录>
./app/<版本>/openyamm.exe --headless-run-scenario <绝对路径>.yml --scenario-no-color
```

判定：退出码 0 且没有 `ASSERT fail`。**这些场景不绘制 HUD**，字体、字号、清晰度这类纯像素问题验不出来。

## 检查清单

- [ ] `find . -name '*.rej'` 为空，`git diff --check` 无空白错误
- [ ] 引擎编译通过，`openyamm.exe` 生成
- [ ] `python tools/check_tables.py` 无 error
- [ ] `python tools/dev/check_translation_rules.py` 为 0
- [ ] 无头场景全 `passed`
- [ ] 新术语进 [glossary.md](glossary.md)，引擎改动进 [engine-changes.md](engine-changes.md)，版本进 `CHANGELOG.md`
- [ ] fork 打新 tag（`v<版本>-zh_cn`），本仓库打对应 tag，两边 Release 挂同一份产物

## 附录：fork 之前的手工迁移记录

1.17 → 1.18 与 1.18 → 1.19 是在**还没有 git fork** 的时候做的：用 `curl` 拉上游 `.diff`、
从 `raw.githubusercontent.com` 逐文件取新旧内容，再用 `git merge-file -p --diff3 本地 base 上游`
三方合并。当时的约束和踩到的坑留着备查，**有 fork 之后这些做法全部作废**：

- 本机没有完整上游仓库（11.7 GB，含大量美术源文件），所以没下整包；`git archive`/`git show`
  在当时的网络下会卡住，改用 GitHub API（`gh api` 或 `raw.githubusercontent.com`）单文件取。
- 1.17 → 1.18：上游改 75 个文件，与汉化重叠 6 个。`MainMenuScreen::captureBinding` 从
  `confirm("Assign Key", body, ...)` 改成 `confirm(title, body, ...)` 并加了「再按 Esc 取消」，
  附近上下文被上游挪动，patch 拒绝，手工把两处标题与正文包成 `UiText::translate(...)` 才对齐。
- 1.18 → 1.19：上游改 87 个文件，重叠 11 个；67 个直接覆盖、6 个新增、11 个三方合并，仅 1 处冲突
  （`LoadGameScreen.cpp`：旧汉化把 "(not installed)" 包成模板，上游把 `saveData->ruleset` 改成
  `summary.ruleset`）。
- PortableGit 的 `bin` 目录元数据损坏（358 个条目读不到），bash 会优先从那里解析
  `cat`/`sed`/`head`，导致 FFmpeg 的 `version.sh` 全炸（`cat: cannot execute`），
  `version.c` 里 `FFMPEG_VERSION` 没生成出来。构建脚本里把这条 PATH 去掉了，只留 `<git>\usr\bin`。
  **这条对 Windows 构建仍然适用。**
