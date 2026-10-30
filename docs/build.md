# 从源码构建

产出一个可分发补丁 = 两件事：

1. **mods/** —— 译文数据表 + 中文字体（纯 Python 生成，不需要编译器）；
2. **openyamm.exe** —— 改过的引擎（需要 CMake + 编译器，且必须在 Windows 上编）。

只想贡献译文的话，第 1 步就够了，见 [CONTRIBUTING.md](../CONTRIBUTING.md)。

---

## 0. 准备

| 需要 | 用途 |
|---|---|
| Python 3.10+ | 所有生成脚本，无第三方依赖 |
| OpenYAMM 源码树（当前是 1.19） | 补丁要读它的 `assets_dev/engine/data_tables/` 作为底表 |
| 原版安装（≥1.19） | 取 `assets/packs/engine.core-*.zip` 里的引擎自带表（词缀、屋名、职业名） |
| MMMerge 整合版 | 只在重建 `corpus/mmmerge/` 时才需要 |

路径可以用参数指定，也可以设环境变量：`OPENYAMM_SRC`、`OPENYAMM_PACKS`、`MMMERGE_DIR`。
不指定时 `tools/paths.py` 按仓库同级目录自动探测：源码树依次找 `openyamm-1.19/`、`openyamm-1.18/`、
`openyamm/`、`openyamm-1.17/`；资产包依次找 `game/assets/packs`（本项目自带的 1.19 正式安装）、
`OpenYAMM-1.17/OpenYAMM/assets/packs`、`openyamm-1.17/build-mingw/game/assets/packs`。

### 引擎改动

本仓库不含 C++ 源码——引擎改动是在 OpenYAMM 源码树上做的，改了哪些文件、为什么改，
见 **[engine-changes.md](engine-changes.md)**。要编 exe 就得先把这些改动应用到你的源码树。

## 1. 生成 mods

```bash
# 合成覆盖表（把各路语料并成一张 ui_text.txt）
python tools/make_ui_text.py

# 译文数据表
python tools/build_patch.py --openyamm ../openyamm-1.19 --out build/mods

# 字体：先收集译文用到的码点，再烘焙成引擎要的描述文件 + 子集 TTF
python tools/font_subset.py --patch build/mods --openyamm ../openyamm-1.19 \
       --out build/mods/engine/fonts/truetype
python tools/build_fonts.py --font assets/fonts/NotoSansSC.ttf \
       --license assets/fonts/OFL.txt --out build/mods
```

`build_patch.py` 会就地覆盖同名文件，重跑即可刷新译文。跑完会打印每张表翻了多少行：

```
npc_topic_text.txt: 2680 rows translated, 1379 kept, 597 stray lines dropped
npc_professions.txt: 77 cells from npc_professions_zh.tsv
english/ui_text.txt: 4291 entries
english/pc_names.txt: 480 names in 8 columns
```

## 2. 编 exe

CMake 配置时**必须**带 `-DOPENYAMM_DEV_ASSETS_DIR:STRING=assets`。
不带这个开关，编出来的 exe 会去读源码目录下的 `assets_dev/`，永远不会挂载 `mods/`——补丁看起来「完全没生效」。

```bash
cmake -S ../openyamm-1.19 -B ../openyamm-1.19/build-mingw -G "MinGW Makefiles" \
      -DCMAKE_BUILD_TYPE=Release \
      -DOPENYAMM_DEV_ASSETS_DIR:STRING=assets \
      -DOPENYAMM_COOK_ON_BUILD=OFF \
      -DOPENYAMM_HOUSE_VIDEOS=ON
cmake --build ../openyamm-1.19/build-mingw -j 6
```

产物：`../openyamm-1.19/build-mingw/game/openyamm.exe`（约 56 MB）。

> 注意别和根目录那个 2.99 MB 的 `OpenYAMM.exe` 搞混——那个是启动器，不是引擎。

## 3. 打包

```bash
python tools/package.py --mod build/mods \
       --exe ../openyamm-1.19/build-mingw/game/openyamm.exe \
       --out dist/OpenYAMM-1.19-zh_cn.zip
```

## 一键

```powershell
scripts\build.ps1                       # Windows
```

```bash
scripts/build.sh                        # Linux / macOS（只出 mods，不出 exe）
```

脚本只做流程编排，参数照旧可以传进去。

---

## 踩过的坑

**CMake 补丁必须 LF 换行。**
`cmake/patches/*.patch` 若是 CRLF，`git apply` 会整段失败，报 `patch does not apply`。

**Windows 上 PATH 顺序有讲究。**
FFmpeg 的构建脚本要用 `sh`／`sed`，把 Git 的 `usr/bin` 排在 MinGW 前面，否则会调到 MinGW 自带的残缺工具链。
另外依赖目录可以用 `-DFETCHCONTENT_SOURCE_DIR_<NAME>=<path>` 指到本地解压好的库，免去每次重新下载。

**`OPENYAMM_HOUSE_VIDEOS`。**
房屋里的视频要 FFmpeg。没有 FFmpeg 就 `-DOPENYAMM_HOUSE_VIDEOS=OFF`，`HouseVideoPlayer` 会退化成空实现，
不影响文本。

**CMake 下载依赖时报 TLS 证书错误。**
`zstd`、`etcpak`、`etc2comp` 是配置期用 FetchContent 现下的，不在 `toolchains/deps/` 里。WinLibs 那份
CMake 自带的 curl 走 GnuTLS 且没配信任根，会报
`SSL certificate verification failed: certificate signer not trusted (CAfile: none)`。
两种做法：

1. **推荐：先把源码解压到 `toolchains/deps/`，配置时用 `-DFETCHCONTENT_SOURCE_DIR_<NAME>` 指过去**，
   完全不联网（1.19 本机构建就是这么做的）：

   ```
   -DFETCHCONTENT_SOURCE_DIR_OPENYAMM_ZSTD=.../toolchains/deps/zstd
   -DFETCHCONTENT_SOURCE_DIR_OPENYAMM_ETCPAK=.../toolchains/deps/etcpak
   -DFETCHCONTENT_SOURCE_DIR_OPENYAMM_ETC2COMP=.../toolchains/deps/etc2comp
   ```

   三个包的地址与提交号见 `cmake/SpriteAtlasCodecs.cmake`。
2. 或者手动指定证书文件（必须写正斜杠，否则 CMake 生成脚本里 `\P` 会被当转义，路径含空格时还要
   把整个 `-D` 参数用引号包住）：

   ```
   -DCMAKE_TLS_CAINFO=C:/Program Files/Git/usr/ssl/certs/ca-bundle.crt
   ```

**FFmpeg 的 `make install` 在 cmd 进程树里会截断文件列表。**
报错形如 `install: target 'd:/Proj' is not a directory`——头文件列表太长，从 `cmd.exe` 拉起时被截断。
库文件其实已经装好了，缺的只是头文件。处理办法：在 bash/pwsh 里进 `_deps/ffmpeg-build` 手动
`make install`（设 `MSYSTEM=MINGW64`），再把 `toolchains/deps/ffmpeg/libav*/*.h` 与构建目录里的
`libavutil/avconfig.h`、`ffversion.h` 拷到 `_deps/ffmpeg-install/include/`，然后重新 configure。

**别用 `-j 16`。**
这台机器上 `-j 16` 会 `cc1plus: out of memory`，链接也会被 OOM 杀掉。单实例 `-j 6` 编译约
6～10 分钟；并行开多个构建反而更慢，也更容易崩。

**改了覆盖表不生效。**
`UiText::load` 在启动时一次性载入（`s_overrides` 非空就直接返回），必须重启游戏。

**无头验证。**
只想验证译文有没有塞进表、运行时能不能查到时，可以不解包游戏、不开窗口，用
`--headless-run-scenario` 跑一遍场景脚本，见 [dev-notes.md](dev-notes.md)。

## 重建 corpus/mmmerge/

`corpus/mmmerge/` 里的 30 张表是从 MMMerge 安装解出来的，仓库里带着成品，所以平时不用重跑。
真要重建：

```bash
python tools/extract_corpus.py --mmmerge /path/to/mmmerge --out corpus/mmmerge
```

MMMerge 的本地化 LOD 把中文写成 `ESC + GBK` 字节，`tools/decode_zhcn.py` 负责还原。
