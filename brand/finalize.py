# /// script
# requires-python = ">=3.12"
# dependencies = ["pillow"]
# ///
"""Pad the Echo originals into every size the label needs. Never crops.

Run from brand/: uv run finalize.py
Outputs land in brand/final/.
"""

from pathlib import Path

from PIL import Image

HERE = Path(__file__).parent
OUT = HERE / "final"
OUT.mkdir(exist_ok=True)

SOURCES = ["echo-og", "echo-lab", "echo-sounds"]

# (suffix, width, height)
TARGETS = [
    ("cover", 630, 500),       # itch cover
    ("social", 1280, 640),     # GitHub social preview
    ("thumb", 315, 250),       # itch browse-grid size, for eyeballing only
    ("tiny", 180, 143),        # itch search-result size, for eyeballing only
]


def edge_color(img: Image.Image) -> tuple[int, int, int]:
    """Median of the left edge column: the flat background green."""
    rgb = img.convert("RGB")
    pixels = [rgb.getpixel((2, y)) for y in range(0, rgb.height, 7)]
    pixels.sort(key=lambda p: sum(p))
    return pixels[len(pixels) // 2]


for name in SOURCES:
    src = Image.open(HERE / f"{name}.png").convert("RGB")
    bg = edge_color(src)
    for suffix, w, h in TARGETS:
        scale = h / src.height if (w / h) > (src.width / src.height) else w / src.width
        art = src.resize((round(src.width * scale), round(src.height * scale)), Image.LANCZOS)
        canvas = Image.new("RGB", (w, h), bg)
        canvas.paste(art, ((w - art.width) // 2, (h - art.height) // 2))
        canvas.save(OUT / f"{name}-{suffix}.png")
    print(f"{name}: bg {bg}, 4 sizes")

print(f"done -> {OUT}")
