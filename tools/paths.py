"""仓库内的路径约定。

各工具算默认位置的地方集中在这一个模块，免得每个脚本各写一份 `D:/projects/...`。
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


def engine_source(explicit=None) -> Path:
	"""OpenYAMM 源码树。默认找仓库的同级目录 `../openyamm`、`../openyamm-1.17`。"""
	path = _first_existing(
		[
			explicit,
			os.environ.get("OPENYAMM_SRC"),
			REPO.parent / "openyamm",
			REPO.parent / "openyamm-1.17",
		]
	)
	if path is None:
		raise SystemExit(
			"找不到 OpenYAMM 源码树，请用 --openyamm 指定，或设环境变量 OPENYAMM_SRC。"
		)
	return path


def asset_packs(explicit=None) -> Path:
	"""原版安装的资产包目录（`assets/packs`）。默认找仓库同级的 OpenYAMM-1.17 安装。"""
	path = _first_existing(
		[
			explicit,
			os.environ.get("OPENYAMM_PACKS"),
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
