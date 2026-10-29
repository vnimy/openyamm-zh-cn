"""Write the CJK font faces and their descriptors into the patch.

Every text face of OpenYAMM is switched to an outline face at the same cell geometry (logical height and baseline stay
as they were), so the existing layout keeps its metrics while the glyphs come from a Simplified Chinese font with a
baked subset. One shared TTF serves all faces; each face only differs in height, baseline and weight.
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path
from typing import Sequence, Tuple

# face name, logical height, baseline, optional weight
FACES: Sequence[Tuple[str, int, int, int]] = (
    ("arrus", 19, 14, 0),
    ("comic", 19, 14, 0),
    ("lucida", 17, 13, 0),
    ("book2", 30, 23, 0),
    ("autonote", 18, 15, 0),
    ("smallnum", 14, 11, 0),
    ("spell", 16, 12, 0),
    ("create", 18, 13, 0),
    ("endgame", 20, 16, 0),
    ("menu_lucida", 17, 13, 0),
    ("menu_arrus", 19, 14, 0),
    ("fondamento", 32, 25, 0),
    ("alegreya_semibold", 24, 18, 600),
)

FONT_FILE = "openyamm_cjk.ttf"
SUBSET_FILE = "cjk_glyphs.txt"


def descriptor_for(logical_height: int, baseline: int, weight: int) -> str:
    lines = [
        "# Simplified Chinese patch: Noto Sans SC outlines at this face's native cell geometry.",
        f"file: {FONT_FILE}",
        "metrics: freetype",
    ]

    if weight:
        lines.append(f"weight: {weight}")

    lines.extend([
        f"logical_height: {logical_height}",
        f"baseline: {baseline}",
        "encoding: utf-8",
        f"glyphs: {SUBSET_FILE}",
        # Two pixels of padding are enough for CJK strokes; the atlas holds thousands of cells.
        "padding: 2",
    ])

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--font", type=Path, required=True, help="the CJK TTF to ship")
    parser.add_argument("--license", type=Path, help="the font's OFL license text")
    parser.add_argument("--out", type=Path, required=True, help="patch asset root (mod directory)")
    arguments = parser.parse_args()

    truetype = arguments.out / "engine/fonts/truetype"
    truetype.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(arguments.font, truetype / FONT_FILE)

    if arguments.license and arguments.license.exists():
        shutil.copyfile(arguments.license, truetype / "openyamm_cjk_ofl.txt")

    for name, logical_height, baseline, weight in FACES:
        (truetype / f"{name}.yml").write_text(
            descriptor_for(logical_height, baseline, weight), encoding="utf-8", newline="")

    print(f"{len(FACES)} faces written to {truetype}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
