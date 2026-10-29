#!/usr/bin/env bash
# 一键生成 mods（Linux / macOS 上不编 exe，只出数据与字体）。
#
#   scripts/build.sh                        # 自动探测源码树
#   scripts/build.sh --openyamm ../openyamm-1.17 --exe /path/to/openyamm.exe --dist dist/x.zip
#
# 需要：Python 3.10+。

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

OPENYAMM=""
EXE=""
OUT_DIR="build/mods"
DIST=""

while [[ $# -gt 0 ]]; do
	case "$1" in
		--openyamm) OPENYAMM="$2"; shift 2 ;;
		--exe)      EXE="$2"; shift 2 ;;
		--out)      OUT_DIR="$2"; shift 2 ;;
		--dist)     DIST="$2"; shift 2 ;;
		-h|--help)  sed -n '2,10p' "$0"; exit 0 ;;
		*)          echo "未知参数：$1" >&2; exit 2 ;;
	esac
done

step() {
	printf '\n== %s\n' "$1"
}

step "合成覆盖表"
python3 tools/make_ui_text.py

step "体检覆盖表"
python3 tools/check_tables.py

patch_args=(tools/build_patch.py --out "$OUT_DIR")
[[ -n "$OPENYAMM" ]] && patch_args+=(--openyamm "$OPENYAMM")
step "生成译文数据表"
python3 "${patch_args[@]}"

step "收集字形子集"
subset_args=(tools/font_subset.py --patch "$OUT_DIR" --out "$OUT_DIR/engine/fonts/truetype")
[[ -n "$OPENYAMM" ]] && subset_args+=(--openyamm "$OPENYAMM")
python3 "${subset_args[@]}"

step "烘焙字体描述"
python3 tools/build_fonts.py \
	--font assets/fonts/NotoSansSC.ttf \
	--license assets/fonts/OFL.txt \
	--out "$OUT_DIR"

printf '\nmods 已生成：%s\n' "$OUT_DIR"

if [[ -n "$EXE" ]]; then
	[[ -z "$DIST" ]] && DIST="dist/OpenYAMM-117-zh_cn.zip"
	step "打包"
	python3 tools/package.py --mod "$OUT_DIR" --exe "$EXE" --out "$DIST"
	printf '已打包：%s\n' "$DIST"
else
	echo "未指定 --exe，跳过打包。"
fi
