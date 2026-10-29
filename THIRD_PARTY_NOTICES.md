# 第三方声明

本仓库的脚本、文档与译文表以 MIT 发布（见 [LICENSE](LICENSE)），但下面这些内容另有归属与限制。

## 思源黑体 / Noto Sans SC

- 文件：`assets/fonts/NotoSansSC.ttf`
- 许可：SIL Open Font License 1.1，全文见 `assets/fonts/OFL.txt`
- 用途：补丁里所有中文面都从这份字体取字形，构建时只烘焙译文实际用到的码点子集

OFL 允许随软件再分发与嵌入，保留许可证文件即可；字体本身不得单独售卖。

## MMMerge 官方简体中文语言包

- 来源：MMMerge 整合版安装目录下的 `10 LocZHCN.EnglishT.lod` 与 `Data/Text localization/ZHCN_*.txt`
- 内容：`corpus/mmmerge/` 下的 30 张表，是本项目译文的主体
- 归属：Might and Magic Unofficial Translation Team 及相关贡献者

这些译文是社区多年积累的成果，本项目按记录 ID 对齐后复用到 OpenYAMM 上，**未做重新翻译**。
如果原作者要求撤下，请开 issue，会立即处理。

## Might and Magic 系列游戏文本

Might and Magic、Heroes of Might and Magic 及相关名称、角色、文本的著作权归
Ubisoft Entertainment（原 New World Computing）所有。

本仓库只包含**用于本地化适配的文本键与译文**，不包含游戏本体、美术、音效、地图或任何原始资源。
使用者需自行合法拥有游戏。本项目为非官方玩家作品，与 Ubisoft 无任何关联。

## OpenYAMM

- 仓库：<https://github.com/OpenYAMM/OpenYAMM>
- 许可：GNU GPL v3.0 or later

Release 中附带的 `openyamm.exe` 是 OpenYAMM 1.17 的**修改版本**（改动见
[docs/engine-changes.md](docs/engine-changes.md)），因此同样受 GPL-3.0-or-later 约束。
按 GPL 要求，相应的修改后源码可通过 issue 索取；改动本身在 `docs/engine-changes.md` 中有完整的文件级说明。

`mods/` 下的数据表与字体是独立的数据资产，不是 OpenYAMM 的衍生代码。

## mm678-i18n

- 仓库：<https://github.com/might-and-magic/mm678-i18n>
- 用途：术语参考（人名、地名、技能名的定译）

未直接复制其文件内容；如发现某条译法与该项目一致，属于术语统一的自然结果。

## 第三方库

构建引擎时会拉取 OpenYAMM 自带的第三方依赖（SDL、FFmpeg 等），各自保留原许可。
本仓库不包含这些库的源码或二进制。
