"""仓库内的路径约定。

各工具算默认位置的地方集中在这一个模块，免得每个脚本各写一份硬编码的绝对路径。
所有默认值都可以用命令行参数或环境变量覆盖：

- `OPENYAMM_SRC`      OpenYAMM 源码树（要有 `assets_dev/engine/data_tables/`）
- `OPENYAMM_PACKS`    原版安装的资产包目录（`assets/packs/*.zip`），取引擎自带表用
- `MMMERGE_DIR`       MMMerge 整合版安装目录，取官方简中语料用
"""

from __future__ import annotations

import os
from pathlib import Path

# 仓库根：本文件在 tools/ 下，往上一层就是仓库根。
REPO = Path(__file__).resolve().parent.parent

# corpus 分三层：
#   mmmerge/    MMMerge 官方简中包解出来的原始表（tools/extract_corpus.py 产出，可重建）
#   overrides/  展示层覆盖表，汉化的主要工作面（ui_text.txt 与各 *_zh.tsv）
#   reports/    缺口清单与中间稿（可从上面两层重建）
CORPUS = REPO / "corpus"
MMMERGE = CORPUS / "mmmerge"
OVERRIDES = CORPUS / "overrides"
REPORTS = CORPUS / "reports"

BUILD = REPO / "build"


def _first_existing(candidates) -> Path | None:
	for candidate in candidates:
		if candidate is None:
			continue
		path = Path(candidate)
		if path.exists():
			return path
	return None


def _has_data_tables(path: Path) -> bool:
	"""源码树里是否真的有 `assets_dev/engine/data_tables/english/` 的英文表。

	1.19 的源码树是「1.18 树 + 上游 87 个源码文件三方合并」拼出来的，**不带 assets_dev 数据表**
	（那些表只存在于内容包里）。所以「查源码」和「取数据表骨架」要找的不是同一棵树。
	"""
	return (path / "assets_dev/engine/data_tables/english/autonote.txt").exists()


def engine_source(explicit=None) -> Path:
	"""OpenYAMM 源码树（用于读/改 C++ 源码与做源码类检查）。优先当前版本。"""
	path = _first_existing(
		[
			explicit,
			os.environ.get("OPENYAMM_SRC"),
			REPO.parent / "openyamm",
			REPO.parent / "openyamm-1.19",
			REPO.parent / "openyamm-1.18",
			REPO.parent / "openyamm-1.17",
		]
	)
	if path is None:
		raise SystemExit(
			"找不到 OpenYAMM 源码树，请用 --openyamm 指定，或设环境变量 OPENYAMM_SRC。"
		)
	return path


def data_table_source(explicit=None) -> Path:
	"""带数据表骨架的那棵树（build_patch 从这里读英文原表再打补丁）。

	优先当前版本；当前版本的树若不含 `assets_dev` 数据表，退回上一个含表的版本。
	实测 1.18 源表与 1.19 内容包内的 98 张表**逐字节相同**，退回 1.18 不会引入版本漂移。
	"""
	candidates = [
		explicit,
		os.environ.get("OPENYAMM_SRC"),
		REPO.parent / "openyamm",
		REPO.parent / "openyamm-1.19",
		REPO.parent / "openyamm-1.18",
		REPO.parent / "openyamm-1.17",
	]
	for candidate in candidates:
		if candidate is None:
			continue
		path = Path(candidate)
		if path.exists() and _has_data_tables(path):
			return path
	raise SystemExit(
		"找不到带 assets_dev/engine/data_tables 的 OpenYAMM 源码树，"
		"请用 --openyamm 指定，或设环境变量 OPENYAMM_SRC。"
	)


def asset_packs(explicit=None) -> Path:
	"""原版安装的资产包目录（`assets/packs`）。

	默认依次找：仓库同级 `game/assets/packs`（本项目自带的 1.18 正式安装）、
	旧布局 `OpenYAMM-1.17/OpenYAMM/assets/packs`、以及 1.17 构建树下的 `build-mingw/game/assets/packs`。
	"""
	path = _first_existing(
		[
			explicit,
			os.environ.get("OPENYAMM_PACKS"),
			REPO.parent / "game" / "assets" / "packs",
			REPO.parent / "OpenYAMM-1.17" / "OpenYAMM" / "assets" / "packs",
			REPO.parent / "openyamm-1.17" / "build-mingw" / "game" / "assets" / "packs",
		]
	)
	if path is None:
		raise SystemExit(
			"找不到 OpenYAMM 资产包目录，请用 --packs 指定，或设环境变量 OPENYAMM_PACKS。"
		)
	return path


def mmmerge(explicit=None) -> Path:
	"""MMMerge 安装目录。默认找仓库同级的 mmmerge。"""
	path = _first_existing([explicit, os.environ.get("MMMERGE_DIR"), REPO.parent / "mmmerge"])
	if path is None:
		raise SystemExit(
			"找不到 MMMerge 安装目录，请用 --mmmerge 指定，或设环境变量 MMMERGE_DIR。"
		)
	return path


def ensure_build_dir() -> Path:
	"""中间产物目录，已被 .gitignore 忽略。"""
	BUILD.mkdir(parents=True, exist_ok=True)
	return BUILD
