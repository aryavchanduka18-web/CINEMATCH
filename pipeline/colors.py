"""Dominant color of an image, used to tint the hero (spec section 8.5)."""
import colorsys
from pathlib import Path

from PIL import Image


def dominant_color(path: Path) -> str:
    """Hex color that best represents the image.

    The image is shrunk and reduced to 6 colors (median cut). Each color is scored by how much
    of the image it covers, boosted when it is colorful; near-black and near-white colors only
    win if nothing else is present (otherwise most dark movie stills would all tint black).
    """
    with Image.open(path) as img:
        small = img.convert("RGB").resize((96, 54))
    quant = small.quantize(colors=6, method=Image.Quantize.MEDIANCUT)
    palette = quant.getpalette()
    best, best_score, fallback = None, -1.0, None
    for count, idx in sorted(quant.getcolors(), reverse=True):
        r, g, b = palette[idx * 3: idx * 3 + 3]
        _, light, sat = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
        fallback = fallback or (r, g, b)
        if light < 0.08 or light > 0.92:
            continue
        score = count * (0.35 + sat)
        if score > best_score:
            best, best_score = (r, g, b), score
    r, g, b = best or fallback
    return f"#{r:02x}{g:02x}{b:02x}"