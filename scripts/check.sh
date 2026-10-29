#!/usr/bin/env bash
# 提交前自检：语法、译表格式、覆盖表是否与源表一致。
# 与 GitHub Actions 里的检查等价（见 docs/ci/check.yml），本地跑不用等 CI。

set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

status=0

step() {
	printf '\n== %s\n' "$1"
}

step "语法检查"
python3 -m compileall -q tools || status=1

step "译表体检"
python3 tools/check_tables.py || status=1

step "覆盖表可重现"
before="$(python3 -c "import hashlib,sys;print(hashlib.sha256(open('corpus/overrides/ui_text.txt','rb').read()).hexdigest())")"
python3 tools/make_ui_text.py >/dev/null || status=1
after="$(python3 -c "import hashlib,sys;print(hashlib.sha256(open('corpus/overrides/ui_text.txt','rb').read()).hexdigest())")"

if [[ "$before" != "$after" ]]; then
	echo "ui_text.txt 与源表不一致，请提交重新生成的结果。"
	status=1
else
	echo "ui_text.txt 与源表一致。"
fi

step "缺口统计"
python3 tools/check_literals.py --allow-missing --show 0 | head -1 || true

if [[ $status -eq 0 ]]; then
	printf '\n全部通过。\n'
else
	printf '\n有问题，见上面的输出。\n'
fi

exit $status
