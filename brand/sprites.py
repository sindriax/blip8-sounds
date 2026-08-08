"""Cut web sized sprites out of the Echo originals, for whichever repo asks.

The originals here are the single source of truth. Each is a square of art with
the product name burned in underneath, so this finds the blank band between the
two and crops them apart: the art becomes a sprite, the title becomes a wordmark,
and the consuming page supplies its own headings.

    uv run brand/sprites.py lab --out ../blip8-lab/public
    uv run brand/sprites.py hub --out ../blip8-hub/img

Outputs land in brand/web/ when --out is left off. Consumers commit the files
they serve, so their builds never need this repo; re-run only when the art
changes.
"""

# /// script
# requires-python = ">=3.12"
# dependencies = ["pillow>=11.0", "numpy>=2.0"]
# ///

import argparse
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).parent

# (output name, source, part, width)
TARGETS: dict[str, list[tuple[str, str, str, int]]] = {
    "lab": [
        ("echo.png", "echo-lab", "art", 320),
        ("wordmark.png", "echo-lab", "title", 420),
    ],
    "hub": [
        ("echo-og.png", "echo-og", "art", 360),
        ("echo-lab.png", "echo-lab", "art", 360),
        ("echo-sounds.png", "echo-sounds", "art", 360),
        ("echo-flyer.png", "echo-og", "art", 72),
        ("wordmark.png", "echo-og", "title", 420),
    ],
}

COLORS = 64
KEY = (255, 0, 255)
KEY_THRESHOLD = 60


def split(img: Image.Image) -> tuple[Image.Image, Image.Image]:
    """The art and the burned-in title, split at the blank band between them."""
    bright = np.asarray(img.convert("RGB")).sum(axis=2) > 260
    rows = bright.sum(axis=1)
    quiet = rows < img.width * 0.05

    runs: list[list[int]] = []
    for y in range(img.height // 2, img.height):
        if quiet[y]:
            if runs and runs[-1][1] == y - 1:
                runs[-1][1] = y
            else:
                runs.append([y, y])
    runs = [r for r in runs if r[1] - r[0] >= 10]
    if len(runs) < 2:
        raise SystemExit(f"cannot find the title band, found {len(runs)} blank runs")

    # The last run is the bottom margin, so the one before it is the split. Faint
    # pixels inside it are the dotted shadow under Echo's feet, worth keeping.
    band_start, band_end = runs[-2]
    faint = [y for y in range(band_start, band_end + 1) if rows[y] > 0]
    art_bottom = (faint[-1] if faint else band_start) + 1

    columns = np.where(bright[:art_bottom].any(axis=0))[0]
    left, right = int(columns.min()) - 8, int(columns.max()) + 8
    top = max(0, int(np.argmax(bright.any(axis=1))) - 8)

    art = cut_background(img.crop((left, top, right, art_bottom)))
    title = cut_dark(img.crop((left, art_bottom + 4, right, img.height)))
    return art, title


def cut_background(img: Image.Image) -> Image.Image:
    """Flood the grid backdrop away from the corners, keeping the dark outline."""
    flat = img.convert("RGB")
    corners = [(0, 0), (flat.width - 1, 0), (0, flat.height - 1), (flat.width - 1, flat.height - 1)]
    for corner in corners:
        ImageDraw.floodfill(flat, corner, KEY, thresh=KEY_THRESHOLD)
    rgb = np.asarray(flat).copy()
    keyed = (rgb == KEY).all(axis=2)
    # Zero the keyed pixels too: left magenta they would eat palette slots that
    # the visible colours need.
    rgb[keyed] = 0
    alpha = np.where(keyed, 0, 255).astype(np.uint8)
    return Image.fromarray(np.dstack([rgb, alpha]), "RGBA")


def cut_dark(img: Image.Image, low: int = 150, high: int = 320) -> Image.Image:
    """Key by brightness, for the wordmarks: flooding leaves specks in the text."""
    pixels = np.asarray(img.convert("RGB")).astype(np.int32)
    alpha = np.clip((pixels.sum(axis=2) - low) * 255 // max(1, high - low), 0, 255)
    return Image.fromarray(np.dstack([pixels, alpha]).astype(np.uint8), "RGBA")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("consumer", choices=sorted(TARGETS))
    parser.add_argument("--out", type=Path, default=HERE / "web")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    cache: dict[str, tuple[Image.Image, Image.Image]] = {}
    for name, source, part, width in TARGETS[args.consumer]:
        if source not in cache:
            original = HERE / f"{source}.png"
            if not original.exists():
                raise SystemExit(f"missing {original}")
            cache[source] = split(Image.open(original).convert("RGB"))

        piece = cache[source][0 if part == "art" else 1]
        # Not NEAREST: the shrink is not a whole-number ratio and would tear.
        height = round(piece.height * width / piece.width)
        small = piece.resize((width, height), Image.Resampling.LANCZOS)
        target = args.out / name
        small.quantize(colors=COLORS, method=Image.Quantize.FASTOCTREE).save(target, optimize=True)
        print(f"{target}  {width}x{height}  {target.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main()
