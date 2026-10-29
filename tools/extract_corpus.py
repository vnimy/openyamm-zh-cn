"""Extract the MMMerge Chinese corpus into UTF-8 tables.

Two inputs of the MMMerge build carry the translation:

* `10 LocZHCN.EnglishT.lod` — the localized MM8 tables, stored as zlib streams in the game's LOD container; every
  entry is announced by its file name in the 200 bytes before the stream;
* `Data/Text localization/ZHCN_*.txt` — override tables keyed by record ID for names the LOD does not carry
  (items, monsters, maps, houses, place monsters, NPC names).

Both were written for the engine's GBK renderer: each wide character is stored as `0x0E <GBK lead> <GBK trail> 0x07`
followed by a spacer space, and the text ends with 0x0F. Dropping those bytes and decoding GB18030 yields the text.
"""

from __future__ import annotations

import argparse
import re
import zlib
from pathlib import Path

NAME_PATTERN = re.compile(rb"[A-Za-z0-9_\-]{2,20}\.(?:txt|TXT)")
# The LOD keeps its file directory in front of the first compressed entry.
DATA_SEARCH_START = 40000
MAX_STREAM_BYTES = 4_000_000


def strip_wide_char_escapes(raw: bytes) -> bytes:
    raw = raw.replace(b"\x07 ", b"")
    raw = raw.replace(b"\x07", b"").replace(b"\x0e", b"").replace(b"\x0f", b"")
    return raw


def extract_lod(lod_path: Path, output_dir: Path) -> list[str]:
    data = lod_path.read_bytes()
    extracted: list[str] = []
    position = DATA_SEARCH_START

    while position < len(data):
        start = data.find(b"\x78\x9c", position)

        if start < 0:
            break

        decompressor = zlib.decompressobj()
        chunk = data[start:start + MAX_STREAM_BYTES]

        try:
            payload = decompressor.decompress(chunk)
        except zlib.error:
            position = start + 1
            continue

        if not decompressor.eof:
            position = start + 1
            continue

        window = data[max(0, start - 200):start]
        match = None

        for candidate in NAME_PATTERN.finditer(window):
            match = candidate

        if match is None:
            position = start + 1
            continue

        name = match.group().decode()
        text = strip_wide_char_escapes(payload).decode("gb18030", errors="replace")
        (output_dir / name).write_text(text, encoding="utf-8", newline="")
        extracted.append(name)
        position = start + len(chunk) - len(decompressor.unused_data)

    return extracted


def convert_overrides(source_dir: Path, output_dir: Path) -> list[str]:
    converted: list[str] = []

    for path in sorted(source_dir.glob("ZHCN*.txt")):
        text = strip_wide_char_escapes(path.read_bytes()).decode("gb18030", errors="replace")
        (output_dir / path.name).write_text(text, encoding="utf-8", newline="")
        converted.append(path.name)

    return converted


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mmmerge", type=Path, required=True, help="MMMerge installation directory")
    parser.add_argument("--out", type=Path, required=True, help="corpus output directory")
    arguments = parser.parse_args()

    arguments.out.mkdir(parents=True, exist_ok=True)
    lod = arguments.mmmerge / "Data/10 LocZHCN.EnglishT.lod"

    if not lod.exists():
        raise SystemExit(f"missing {lod}")

    extracted = extract_lod(lod, arguments.out)
    converted = convert_overrides(arguments.mmmerge / "Data/Text localization", arguments.out)

    print(f"{len(extracted)} tables from {lod.name}, {len(converted)} override tables")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
