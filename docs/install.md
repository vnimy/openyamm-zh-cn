# 安装

## 适用版本

- Windows 10／11 x64
- OpenYAMM **官方 1.17**（即 `OpenYAMM-1.17-windows-x64.zip` 解压后的那份安装）
- 已经至少完整启动过一次，内容包（约 5.8 GB）下载完毕

版本对不上会出问题：启动器升级到 `app/1.18/` 之后，1.17 的 `openyamm.exe` 与 mods 都不再被加载。

## 步骤

1. **先启动一次原版游戏**，等它把内容包下完，然后退出。
   补丁只替换文本与字形，不碰内容包；但没下完的话 `assets/` 里没有 `engine.core`，补丁挂不上去。

2. 解压 `OpenYAMM-<版本>-zh_cn.zip`，会得到三样东西：

   ```
   mods/                 ← 译文表 + 中文字体
   openyamm.exe          ← 重编的引擎（56 MB）
   安装说明.txt
   ```

3. 把 **`mods` 整个文件夹**复制到「有 `settings.ini` 和 `saves` 的那一层」，也就是解压出来的
   `OpenYAMM` 目录。最终路径应为：

   ```
   OpenYAMM/mods/engine/data_tables/english/ui_text.txt
   OpenYAMM/mods/engine/fonts/truetype/openyamm_cjk.ttf
   ```

   > 注意是 `OpenYAMM/mods/`，不是 `OpenYAMM/app/1.17/mods/`。

4. 备份原引擎，再把 `openyamm.exe` 覆盖到 `OpenYAMM/app/1.17/openyamm.exe`：

   ```bat
   ren "OpenYAMM\app\1.17\openyamm.exe" openyamm.exe.orig
   copy openyamm.exe "OpenYAMM\app\1.17\openyamm.exe"
   ```

5. 照常双击 `OpenYAMM.exe` 启动。

## 怎么确认生效

启动日志（`OpenYAMM/logs/` 或控制台）里应当出现两行：

```
Mods: <n> file(s) from .../mods
Development assets: assets
```

进入游戏后主菜单标题、设置项、角色创建界面应当都是中文。

**只换 mods 不换 exe 会看到乱码／方块**——原版引擎把 UTF-8 字节当 CP1252 画。这是最常见的失败原因。

## 排错

| 现象 | 原因 | 处理 |
|---|---|---|
| 中文变成方块或问号 | exe 没换，或换成了别的版本 | 确认 `app/1.17/openyamm.exe` 是补丁里的那份（约 56 MB） |
| 中文变成「æ­¦å™¨」这类乱码 | 同上；也可能是补丁表被编辑器存成了 GBK | 重装一次，别用记事本改表 |
| 部分文字仍是英文 | 该条还没译 | 跑 `python tools/check_literals.py` 看缺口，或提 issue |
| 文字溢出按钮、标点跑到行首 | 用了原版 exe（不按中文断行） | 换 exe |
| 启动闪退 | 内容包没下完／exe 与版本不匹配 | 恢复 `openyamm.exe.orig`，跑一次原版确认能进，再重装补丁 |
| 改完译文没变化 | 覆盖表启动时一次性载入 | 退出游戏重开 |

## 卸载

```bat
rmdir /s /q "OpenYAMM\mods"
```

再把 `app\1.17\openyamm.exe.orig` 改名回 `openyamm.exe` 即可。存档在 `saves/`，补丁不会动它。
