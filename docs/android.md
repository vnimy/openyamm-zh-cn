
> **2026-11-04 状态**：Android arm64 包已随 1.20.0 发布，重打包流程与 1.19 相同，只是**基底 APK 换成官方
> `OpenYAMM-1.20-android-arm64.apk`**（1.19 的壳会让应用按 1.19 的清单去下内容，引擎与内容版本对不上）。
> 引擎改动在 [vnimy/openyamm](https://github.com/vnimy/openyamm)（tag `v1.20.0-zh_cn`），
> 本页只讲 Android 端的打包与 mods 挂载。
- 只把 `mods/` 放进 APK 或设备不会生效——官方引擎会把 UTF-8 字节按 CP1252 渲染成乱码。
- 重编量很小：汉化引擎改动本来就在 `openyamm` 源码树里，Android 构建工程（`android/`）也是上游现成的。
  本次新增的只是「让 Android 也能加载 mods」的 4 处改动（见下）。
- 产物：`build-android/artifacts/OpenYAMM-1.20-android-arm64-zh.apk`（51,188,902 B，versionName 1.20，
  versionCode 26166819，自签名 v1/v2/v3，zipalign 4 KB / 16 KB 页对齐校验均通过）。
  当前构建（含 1.20.1 译文修复）SHA256 `96ABD6B17A6B95502F4125EA34F366ADCB86A95BB90CAE6638E1C5B14D311062`；
  1.20.0 首发那版是 `3210AECD0DD9BC93A275694388800DC953E3DB05C907B0B5C1032F05710EB2FA`。
- 内容包：首次启动由应用按 `android-arm64.json` 下到 `Android/data/org.openyamm.android/files/content/`；
  1.19 → 1.20 只有 13 个包变化（0.141 GiB），已下过 1.19 内容的手机换这 13 个包与 `index.json` 即可。

### 打包必须遵守的两条压缩规则

第一次打出来的 APK 在手机上装不上（「安装包无效或不完整」），原因是重打包时把两类条目压成了 DEFLATE：

| 条目 | 要求 | 违反后果 |
|---|---|---|
| `lib/**/*.so` | **STORED（不压缩）** + 页对齐 | manifest 里 `android:extractNativeLibs="false"`，系统直接从 APK mmap 加载；压缩后安装器判为无效包 |
| `resources.arsc` | **STORED（不压缩）** | targetSdk ≥ 30 强制要求；`res/**` 里官方以 STORED 存放的 PNG 同理 |

所以重打包脚本（`build-android/repack_apk.py`）对**未改动的条目一律沿用官方包的压缩方式**，只有自己写入的条目
按上面的规则选：`lib/` 与 `resources.arsc` 用 STORED，其余 deflate。签名前会自检这两条，签名后再跑
`zipalign -c -p 4` 与 `apksigner verify`。**别用 PowerShell 的 `ZipArchive` 直接改官方 APK**——它的
`CompressionLevel.NoCompression` 在本机实测并没有真正写成 STORED。

## 引擎侧新增改动（相对 `openyamm` 树）

| 文件 | 改动 | 原因 |
|---|---|---|
| `game/app/main.cpp` | `config.installedContent.modsRoot` 原来被 `#if !defined(__ANDROID__)` 排除，删掉该条件 | Android 上也要拿到 `modsRoot`（等于外部存储工作目录下的 `mods/`），桌面行为不变 |
| `engine/AssetFileSystem.cpp` | Android APK 资产根分支在 `validateTierDirectoriesInMountedPackages()` 之后补 `mountMods()` | 原来只有桌面 packaged 分支挂 mods，Android 分支没有挂载点 |
| `android/app/src/main/cpp/openyamm_android_entry.cpp` | 启动时按 `assets/mods_index.txt` 把 APK 里的 `assets/mods/**` 逐个解压到外部存储的 `mods/`（大小+内容未变则跳过）；`readApkAsset` 上限 16 MiB → 64 MiB | NDK 的 `AAssetManager_openDir` 只能列文件、不能列子目录，递归必须靠构建期清单；CJK 字体 17.7 MB 超过原上限 |
| `game/audio/MusicStream.cpp`、`game/app/main.cpp` | `OPENYAMM_HOUSE_VIDEOS=0` 时提供无 FFmpeg 实现 | 本次构建环境跑不了 FFmpeg 的 MSYS `configure`（见「环境限制」），先保证能编出验证版；桌面默认 `ON` 不受影响 |

`android/app/build.gradle` 增加了把 `mods/`（默认 `<repo>/mods`，可用 `-Popenyamm.android.modsDir=...` 覆盖）
和 `mods_index.txt` 打进每个 APK（含 thin release）的逻辑。`build-android/pack_zh_apk.ps1` 是等价的本地重打包路径
（实际重打包由 `build-android/repack_apk.py` 完成，见下面的压缩规则）。

### 想保留已下载的内容包，就把 APK 签成官方签名

官方 APK 是 thin 包，内容包在首次启动时下到
`Android/data/org.openyamm.android/files/content/`。而「卸载官方版 → 装自签名汉化包」会把这份内容一起删掉。

要避免重下，唯一正规做法是**用与官方相同的签名密钥重签**（`apksigner sign --ks <官方 keystore>`）：
Android 只校验签名一致，不关心谁签的。官方 `android-release.jks` 不在本项目里，所以默认的自签名只适合
「可以重下一次内容包」的情况。另一条路是 bundled 构建（内容包直接打进 APK，见「已知限制」）。

## 构建

### 依赖（本工作区已就位）

| 依赖 | 位置 / 来源 |
|---|---|
| Android NDK r28c（28.2.13676358） | `build-android/android-sdk/ndk/android-ndk-r28c`（`dl.google.com/android/repository/android-ndk-r28c-windows.zip`） |
| build-tools 35（zipalign/apksigner） | `build-android/android-sdk/build-tools/android-15` |
| JDK 17 | `build-android/tools/jdk-17.0.20.1+1`（Adoptium） |
| C/C++ 依赖源码 | `toolchains/deps/`（SDL3、fmt、spdlog、freetype、physfs、yaml-cpp、imgui、bx、bimg、bgfx、monocypher、lua、ffmpeg） |
| zstd/etcpak/etc2comp 源码 | 复用桌面构建缓存 `openyamm/build-mingw/_deps` |
| host shaderc | `openyamm/build-mingw/openyamm_shaderc.exe`（桌面构建产物） |

下载走 `build-android/fetch.js`（Node.js 自实现 TLS，可直连或 `127.0.0.1:10808` SOCKS5）。
本机 `curl`/`Invoke-WebRequest` 因 schannel 不可用而失败。

### 步骤

```bat
:: 1. 配置（MinGW Makefiles，不是 Ninja；脚本名里的版本跟引擎版本走）
build-android\configure-android-1.20.bat

:: 2. 构建 arm64 目标
cd build-android\native-1.20
D:\Projects\MM678\toolchains\mingw64\bin\make.exe -j 8

:: 3. 去掉调试符号（未 strip 时 libmain.so 约 450-470 MB）
<ndk>\toolchains\llvm\prebuilt\windows-x86_64\bin\llvm-strip.exe --strip-unneeded ^
    android\app\src\main\cpp\libmain.so sdl3\libSDL3.so

:: 4. 准备 mods（从汉化发布包解出）
::    openyamm-zh-cn\dist\OpenYAMM-<版本>-zh_cn.zip → build-android\artifacts\mods

:: 5. 重打包 + 对齐 + 签名（基于官方同版本 arm64 APK）
::    内部顺序：repack_apk.py（按规则选压缩方式）→ zipalign -p 4 → apksigner sign → 三项自检
powershell -NoProfile -ExecutionPolicy Bypass -File build-android\pack_zh_apk.ps1 -Version 1.20
```

### 环境限制（本机 DSH 沙箱，踩过的坑）

- **Ninja + CMake 4.4 会卡死**：沙箱下它的 build lock / jobserver 等不到子进程，配置阶段就挂住。
  必须用 `-G "MinGW Makefiles"`。
- **MSYS bash 无法启动**：`couldn't create signal pipe, Win32 error 5`。FFmpeg 的 `configure` 是 MSYS 脚本，
  所以 FFmpeg 编不了 → `OPENYAMM_HOUSE_VIDEOS=OFF`。切到「完全权限」会话后可以改回 `ON` 重编，
  就能得到带音乐与房屋视频的完整版。
- **只有工作区根目录可写**：`pwsh` 在 `workspace-write` 沙箱下只能写 `D:\Projects\MM678` 根下新建的目录，
  已有子目录（如 `.workbuddy`）会 `Access denied`。所以构建/下载/产物都放在 `build-android/`。
- FFmpeg 的 `libav*` 头文件在 `HouseVideoPlayer`/`MusicStream`/`main` 里由 `OPENYAMM_HOUSE_VIDEOS` 控制；
  关掉后必须三处都有兜底实现，缺一处就是 `fatal error: 'libavutil/log.h' file not found`。

## 安装

1. **卸载官方版**。自签名与官方签名不同，不能覆盖安装；卸载会删掉 `Android/data/org.openyamm.android/files/`
   （已下载的内容包与存档，可先备份 `saves/`）。
   > 如果卸载后不想重下内容包：先只装官方版下载内容，再用**同签名**的汉化包覆盖；或者直接用
   > bundled 构建（内容包打进 APK）。
2. 安装 `OpenYAMM-<版本>-android-arm64-zh.apk`（`adb install -r` 或手机直接点安装）。
   装不上时先看 `adb install` 的原始报错：`INSTALL_PARSE_FAILED_*` 多为打包/压缩问题，
   `INSTALL_FAILED_UPDATE_INCOMPATIBLE` 是签名冲突（卸载官方版即可）。
3. 首次启动：官方是 **thin APK**，按屏幕提示下载内容包（体积随版本变动，从官方服务器下）。
   若官方已停止提供该版本内容，需要改成 bundled 构建（见下）。
4. 确认汉化生效：

```sh
adb logcat -s OpenYAMM | grep -E 'Android mods|Mods:'
# 首次启动应看到：Android mods: 44 updated, 0 current in /storage/emulated/0/Android/data/org.openyamm.android/files/mods
# 第二次启动：Android mods: 0 updated, 44 current
# 引擎随后打印：Mods: 44 files from /storage/emulated/0/Android/data/org.openyamm.android/files/mods
```

进入主菜单、设置、角色创建、物品栏应为中文。

## 已知限制

- **音乐与房屋视频**：1.20 的配置带 `-DOPENYAMM_HOUSE_VIDEOS=ON`（FFmpeg 一起编），两者都有；
  1.18 时代那份是 `OFF`，只有文本与界面。
- **thin APK 依赖官方内容包**：内容未下完进不了游戏。要离线安装需用 bundled 模式重编（APK 带上 ~2.8 GB
  Android 内容包，参考 `android/repack_runtime_assets.sh` 与 `-Popenyamm.android.content=bundled`）。
- **版本绑定**：APK 与引擎 tag 一一对应（1.19.3 ↔ `v1.19.3-zh_cn`）。升级不用「重新打」，先按 [upgrading.md](upgrading.md)
  在 fork 里 merge 上游新版，再重编 Android 版。
- 用户自己放进 `Android/data/org.openyamm.android/files/mods/` 的文件仍可用：启动解压只写清单里的 44 个文件，
  不覆盖其它文件。

## 回到桌面构建

Android 的几处改动对桌面二进制无影响（`isAndroidApkAssetRoot()` 在桌面恒为 false，
`OPENYAMM_HOUSE_VIDEOS` 桌面默认 `ON`）。桌面仍按 [build.md](build.md) 构建。
