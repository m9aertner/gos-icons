"""
Step 2: builds the @m9aertner/gos-icons npm package (icon font + SVG assets) and packs it as a .tgz.

    pip install -r requirements.txt
    python scripts/build_gos_icons.py

Input  : glyphs/<name>.svg   single filled path on a 256 x 256 viewbox (Phosphor "regular" grid),
                             produced from design/ by scripts/stroke_to_outline.py
         glyphs.json         name -> private-use codepoint (hex). Never change an assigned codepoint.
         package/            package.json (version!), README.md; LICENSE is taken from the repo root
Output : dist/m9aertner-gos-icons-<version>.tgz  (dist/ is git-ignored)

The package layout mirrors @phosphor-icons/web (src/regular/style.css + font files) and
@phosphor-icons/core (assets/regular/<name>.svg), so consumers use both in the same way.
"""

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.reverseContourPen import ReverseContourPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.svgLib.path import parse_path
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "dist"
STAGE_DIR = OUT_DIR / "package"

FAMILY = "GosIcons"
# Same vertical metrics as Phosphor.ttf: 256 grid scaled by 4, baseline 64 units above the grid bottom.
UNITS_PER_EM = 1024
ASCENT = 960
DESCENT = -64
SCALE = UNITS_PER_EM // 256
# Fixed timestamp (2026-01-01 UTC, seconds since 1904-01-01) so identical input gives an identical font.
FIXED_TIMESTAMP = 1767225600 + 2082844800


def read_path_data(svg_file: Path) -> str:
    match = re.search(r' d="([^"]+)"', svg_file.read_text(encoding="utf-8"))
    if match is None:
        sys.exit(f"{svg_file.name}: no <path d=...> found")
    return match.group(1)


def build_glyph(path_data: str):
    """SVG y axis points down, font y axis up: flip, scale, and put the baseline at ASCENT."""
    pen = TTGlyphPen(None)
    parse_path(path_data, TransformPen(ReverseContourPen(pen), (SCALE, 0, 0, -SCALE, 0, ASCENT)))
    return pen.glyph()


def build_font(codepoints: dict, glyph_data: dict) -> TTFont:
    glyph_order = [".notdef"] + sorted(codepoints)
    fb = FontBuilder(UNITS_PER_EM, isTTF=True)
    fb.setupGlyphOrder(glyph_order)
    fb.setupCharacterMap({int(code, 16): name for name, code in codepoints.items()})
    glyphs = {".notdef": TTGlyphPen(None).glyph()}
    glyphs.update({name: build_glyph(glyph_data[name]) for name in codepoints})
    fb.setupGlyf(glyphs)
    fb.setupHorizontalMetrics({name: (UNITS_PER_EM, 0) for name in glyph_order})
    fb.setupHorizontalHeader(ascent=ASCENT, descent=DESCENT)
    fb.setupNameTable({"familyName": FAMILY, "styleName": "Regular"})
    fb.setupOS2(
        sTypoAscender=ASCENT,
        sTypoDescender=DESCENT,
        sTypoLineGap=0,
        usWinAscent=ASCENT,
        usWinDescent=-DESCENT,
    )
    fb.setupPost()
    font = fb.font
    font.recalcTimestamp = False
    font["head"].created = font["head"].modified = FIXED_TIMESTAMP
    return font


def style_css(codepoints: dict) -> str:
    rules = "\n".join(
        f'.ph.ph-{name}:before {{\n  font-family: "{FAMILY}" !important;\n  content: "\\{code}";\n}}'
        for name, code in sorted(codepoints.items())
    )
    return f"""@font-face {{
  font-family: "{FAMILY}";
  src:
    url("./{FAMILY}.woff2") format("woff2"),
    url("./{FAMILY}.woff") format("woff"),
    url("./{FAMILY}.ttf") format("truetype");
  font-weight: normal;
  font-style: normal;
  font-display: block;
}}

/* Used together with the "ph" base class of @phosphor-icons/web/regular; only the glyph font differs. */
{rules}
"""


def main() -> None:
    codepoints = json.loads((ROOT / "glyphs.json").read_text(encoding="utf-8"))
    svg_files = {f.stem: f for f in (ROOT / "glyphs").glob("*.svg")}
    if set(svg_files) != set(codepoints):
        sys.exit(f"glyphs/*.svg and glyphs.json disagree: {sorted(set(svg_files) ^ set(codepoints))}")
    glyph_data = {name: read_path_data(file) for name, file in svg_files.items()}

    shutil.rmtree(OUT_DIR, ignore_errors=True)
    font_dir = STAGE_DIR / "src" / "regular"
    asset_dir = STAGE_DIR / "assets" / "regular"
    font_dir.mkdir(parents=True)
    asset_dir.mkdir(parents=True)

    font = build_font(codepoints, glyph_data)
    font.save(font_dir / f"{FAMILY}.ttf")
    for flavor in ("woff", "woff2"):
        flavored = TTFont(font_dir / f"{FAMILY}.ttf", recalcTimestamp=False)
        flavored.flavor = flavor
        flavored.save(font_dir / f"{FAMILY}.{flavor}")
    (font_dir / "style.css").write_text(style_css(codepoints), encoding="utf-8", newline="\n")

    for name, file in svg_files.items():
        shutil.copyfile(file, asset_dir / f"{name}.svg")
    for file in (ROOT / "package").iterdir():
        shutil.copyfile(file, STAGE_DIR / file.name)
    shutil.copyfile(ROOT / "LICENSE", STAGE_DIR / "LICENSE")

    subprocess.run(
        ["npm", "pack", str(STAGE_DIR), "--pack-destination", str(OUT_DIR)],
        check=True,
        shell=sys.platform == "win32",
    )


if __name__ == "__main__":
    main()
