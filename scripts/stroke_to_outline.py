"""
Step 1: converts the stroked design drawings into the single filled outline that Phosphor assets use.

    python scripts/stroke_to_outline.py

Input  : design/<name>.stroke.svg   stroked paths (stroke-width, round caps/joins), viewBox 0 0 256 256
Output : glyphs/<name>.svg          one filled path, same format as @phosphor-icons/core/assets/regular/*.svg

Every <path> of the design is stroked, then all strokes are merged into one outline (union).
Rounded caps and corners come out as quadratic curves, which can go into a TrueType font as they are.
"""

import re
import sys
from pathlib import Path

import pathops
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.svgLib.path import parse_path

ROOT = Path(__file__).resolve().parent.parent
# Max deviation (in 256 grid units) when approximating the round caps with quadratic curves.
CURVE_TOLERANCE = 0.25
MITER_LIMIT = 4  # irrelevant for round joins, required by the API


def format_number(value: float) -> str:
    return f"{value:.2f}".rstrip("0").rstrip(".")


def outline(design: str) -> str:
    stroke_width = float(re.search(r'stroke-width="([\d.]+)"', design).group(1))
    strokes = []
    for path_data in re.findall(r'<path d="([^"]+)"', design):
        path = pathops.Path()
        parse_path(path_data, path.getPen())
        path.stroke(stroke_width, pathops.LineCap.ROUND_CAP, pathops.LineJoin.ROUND_JOIN, MITER_LIMIT)
        path.convertConicsToQuads(CURVE_TOLERANCE)
        strokes.append(path)

    builder = pathops.OpBuilder(fix_winding=True, keep_starting_points=False)
    for stroke in strokes:
        builder.add(stroke, pathops.PathOp.UNION)
    pen = SVGPathPen(None, ntos=format_number)
    builder.resolve().draw(pen)
    return pen.getCommands()


def main() -> None:
    designs = sorted((ROOT / "design").glob("*.stroke.svg"))
    if not designs:
        sys.exit("no design/*.stroke.svg found")
    for design_file in designs:
        name = design_file.name.removesuffix(".stroke.svg")
        path_data = outline(design_file.read_text(encoding="utf-8"))
        svg = (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" fill="currentColor">'
            f'<path d="{path_data}"/></svg>'
        )
        (ROOT / "glyphs" / f"{name}.svg").write_text(svg, encoding="utf-8", newline="\n")
        print(f"glyphs/{name}.svg")


if __name__ == "__main__":
    main()
