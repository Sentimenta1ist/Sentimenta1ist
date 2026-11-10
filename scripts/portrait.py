"""Turn a photo into the ASCII portrait used by neofetch.py.

Usage: python portrait.py <photo> <out.txt> [cols]
Needs Pillow and numpy. Run locally once; the output is committed,
so the daily workflow stays stdlib-only.
Bright pixels become dense glyphs (the card is dark), sky becomes blank,
and a thin outline keeps dark hair and clothes from disappearing.
"""
import sys

import numpy as np
from PIL import Image, ImageFilter

RAMP = " .:-=+*#%@"
CROP = (80, 990, 480, 1460)  # head and shoulders in the current photo (920x2000)


def main(photo, out, cols=84):
    src = Image.open(photo).convert("RGB").crop(CROP)
    rows = int(cols * src.height / src.width * 0.5)
    lum = np.asarray(src.convert("L"), dtype=float) / 255
    rgb = np.asarray(src, dtype=float) / 255
    sky = (((rgb[..., 2] - rgb[..., 0]) > -0.01) & (lum > 0.5)) | (lum > 0.8)  # grey-blue sky, not skin
    fig = Image.fromarray(((~sky) * 255).astype("uint8")).filter(ImageFilter.MedianFilter(7))

    def small(img):
        return np.asarray(img.resize((cols, rows), Image.BOX), dtype=float) / 255

    mask = small(fig)
    gray = small(src.convert("L").filter(ImageFilter.UnsharpMask(25, 120, 0)))  # local contrast
    lo, hi = np.percentile(gray[mask > 0.6], [5, 99.5])
    val = np.clip((gray - lo) / (hi - lo), 0, 1) ** 0.85
    edges = np.asarray(fig.filter(ImageFilter.FIND_EDGES)).copy()
    edges[:3], edges[-3:], edges[:, :3], edges[:, -3:] = 0, 0, 0, 0  # crop border is not an edge
    outline = small(Image.fromarray(edges).filter(ImageFilter.MaxFilter(7)))
    val = np.maximum(val, np.clip(outline * 1.5, 0, 0.4))
    val = np.where(mask > 0.35, np.maximum(val, 0.06), 0)
    lines = ["".join(RAMP[min(len(RAMP) - 1, int(x * len(RAMP)))] for x in r).rstrip() for r in val]
    with open(out, "w") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], *(int(a) for a in sys.argv[3:4]))
