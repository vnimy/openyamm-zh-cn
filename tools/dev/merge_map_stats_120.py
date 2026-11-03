"""Rebuild the translated map_stats table on top of a newer upstream base.

The zh patch ships whole-table replacements. map_stats.txt carries both the map display names (translated) and
upstream gameplay ids (MM9 monster ids in v1.20), so a 1.19 copy would revert the engine's own data. This keeps
only the translated display name of each row and takes everything else from the new base.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def read_rows(path: Path) -> tuple[list[str], list[list[str]]]:
    header: list[str] = []
    rows: list[list[str]] = []
    for line in path.read_text(encoding="utf-8", errors="surrogateescape").splitlines():
        fields = line.split("\t")
        if len(fields) >= 2 and fields[0].strip().isdigit():
            rows.append(fields)
        else:
            header.append(line)
    return header, rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-old", type=Path, required=True, help="upstream table the translation was built on")
    parser.add_argument("--translated", type=Path, required=True, help="the shipped translated table")
    parser.add_argument("--base-new", type=Path, required=True, help="new upstream table to adopt")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--report-only", action="store_true")
    arguments = parser.parse_args()

    old_header, old_rows = read_rows(arguments.base_old)
    _, translated_rows = read_rows(arguments.translated)
    new_header, new_rows = read_rows(arguments.base_new)

    old_by_id = {row[0].strip(): row for row in old_rows}
    translated_by_id = {row[0].strip(): row for row in translated_rows}
    new_by_id = {row[0].strip(): row for row in new_rows}

    only_old = sorted(set(new_by_id) - set(old_by_id), key=int)
    only_new = sorted(set(old_by_id) - set(new_by_id), key=int)
    print(f"rows: old={len(old_rows)} translated={len(translated_rows)} new={len(new_rows)}")
    print(f"ids only in new base: {only_old[:10]}{' ...' if len(only_old) > 10 else ''} ({len(only_old)})")
    print(f"ids only in old base: {only_new[:10]}{' ...' if len(only_new) > 10 else ''} ({len(only_new)})")

    changed_fields: dict[int, int] = {}
    for row_id, old in old_by_id.items():
        translated = translated_by_id.get(row_id)
        if translated is None:
            continue
        for index in range(min(len(old), len(translated))):
            if old[index] != translated[index]:
                changed_fields[index] = changed_fields.get(index, 0) + 1
    print("columns the translation changes (index: rows):", dict(sorted(changed_fields.items())))

    if arguments.report_only:
        return 0

    out_rows: list[list[str]] = []
    carried = 0
    for row in new_rows:
        row_id = row[0].strip()
        translated = translated_by_id.get(row_id)
        old = old_by_id.get(row_id)
        merged = list(row)
        if translated is not None and old is not None and len(translated) > 1 and len(old) > 1:
            if translated[1] != old[1]:
                merged[1] = translated[1]
                carried += 1
        out_rows.append(merged)

    lines = list(new_header)
    lines.extend("\t".join(row) for row in out_rows)
    arguments.out.write_text("\n".join(lines) + "\n", encoding="utf-8", errors="surrogateescape")
    print(f"wrote {arguments.out} ({len(out_rows)} rows, {carried} translated names carried over)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
