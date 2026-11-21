"""Turn a photo on a plain light background into an animated ASCII-art SVG.

Run once per photo (needs Pillow): python3 scripts/make_portrait.py photo.jpg
Writes portrait.svg. STATIC=1 writes a frame without animation.
"""
import os
import sys
from collections import deque

from PIL import Image, ImageFilter, ImageOps

COLS, ROWS = 100, 53
W, H = 370, 380
CW, LH = 3.5, 6.8  # character cell, px
OX, OY = (W - COLS * CW) / 2, 20
RAMP = " .`:-=+*cs#%@"  # light to dark: dark photo pixels get dense characters
STATIC = os.environ.get("STATIC") == "1"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT = "'JetBrains Mono','Fira Code',ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"


def subject_mask(gray):
    """Flood-fill the near-white background from the border; everything else is the subject."""
    w, h = gray.size
    px = gray.load()
    bg = [[False] * w for _ in range(h)]
    todo = deque((x, y) for x in range(w) for y in (0, h - 1)) + deque((x, y) for y in range(h) for x in (0, w - 1))
    while todo:
        x, y = todo.popleft()
        if 0 <= x < w and 0 <= y < h and not bg[y][x] and px[x, y] > 225:
            bg[y][x] = True
            todo.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
    return bg


def ascii_rows(photo):
    img = Image.open(photo).convert("L")
    side = min(img.size)
    img = img.crop(((img.width - side) // 2, 0, (img.width + side) // 2, side)).resize((230, 230))
    bg = subject_mask(img)
    subject = Image.new("L", img.size, 0)
    sp = subject.load()
    for y in range(230):
        for x in range(230):
            sp[x, y] = 0 if bg[y][x] else 255
    # contrast from the subject's own histogram, then sharpen so eyes and mouth survive the downscale
    img = ImageOps.equalize(img, mask=subject).filter(ImageFilter.UnsharpMask(2, 160, 2))
    px = img.load()
    for y in range(230):  # white out the background so it becomes spaces
        for x in range(230):
            if bg[y][x]:
                px[x, y] = 255
    small = img.resize((COLS, ROWS), Image.LANCZOS).load()
    rows = []
    for y in range(ROWS):
        line = "".join(RAMP[(255 - small[x, y]) * (len(RAMP) - 1) // 255] for x in range(COLS))
        rows.append(line)
    return rows


def svg(rows):
    clips, texts = [], []
    for i, line in enumerate(rows):
        if not line.strip():
            continue
        y = OY + (i + 1) * LH
        esc = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        if STATIC:
            texts.append(f'<text x="{OX}" y="{y:.1f}" textLength="{COLS * CW}" lengthAdjust="spacing" xml:space="preserve">{esc}</text>')
            continue
        clips.append(
            f'<clipPath id="r{i}"><rect x="0" y="{y - LH:.1f}" width="0" height="{LH + 1:.1f}">'
            f'<animate attributeName="width" from="0" to="{W}" dur=".55s" begin="{0.25 + i * 0.045:.2f}s" fill="freeze"/></rect></clipPath>'
        )
        texts.append(f'<text clip-path="url(#r{i})" x="{OX}" y="{y:.1f}" textLength="{COLS * CW}" lengthAdjust="spacing" xml:space="preserve">{esc}</text>')
    done = 0.25 + len(rows) * 0.045 + 0.6
    shine = "" if STATIC else f"""
<mask id="band"><rect x="-120" y="0" width="120" height="{H}" fill="url(#bandg)">
<animateTransform attributeName="transform" type="translate" values="0 0;{W + 240} 0;{W + 240} 0" keyTimes="0;.45;1" dur="6s" begin="{done:.1f}s" repeatCount="indefinite"/></rect></mask>
<linearGradient id="bandg"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>"""
    glow = "" if STATIC else '<use href="#art" fill="#39d353" mask="url(#band)"/>'
    return f"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="ASCII-art portrait of MD. Emon Miah">
<defs>{"".join(clips)}{shine}</defs>
<style>text{{font:6px {FONT};white-space:pre}}</style>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="10" fill="#0d1117" stroke="#30363d"/>
<g id="art" fill="#c9d1d9">{"".join(texts)}</g>
{glow}
</svg>
"""


if __name__ == "__main__":
    rows = ascii_rows(sys.argv[1])
    ink = sum(c != " " for r in rows for c in r)
    assert ink > COLS * ROWS // 5, "background removal ate the subject"
    with open(os.path.join(ROOT, "portrait.svg"), "w") as f:
        f.write(svg(rows))
    print("\n".join(rows[::3]))
