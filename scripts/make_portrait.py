"""Turn a photo on a plain light background into an animated pixel-art SVG.

Run once per photo (needs Pillow): python3 scripts/make_portrait.py photo.jpg
Writes portrait.svg. STATIC=1 writes a frame without animation.
"""
import os
import sys
from collections import deque

from PIL import Image, ImageEnhance

GRID, PX, W, H = 60, 6, 370, 372
OX, OY = (W - GRID * PX) // 2, (H - GRID * PX) // 2
COLORS = 18
STATIC = os.environ.get("STATIC") == "1"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def background(img):
    """Flood-fill the near-white pixels that touch the border."""
    px = img.load()
    near_white = lambda x, y: min(px[x, y]) > 218
    bg, todo = set(), deque()
    for i in range(GRID):
        for p in ((i, 0), (i, GRID - 1), (0, i), (GRID - 1, i)):
            if near_white(*p) and p not in bg:
                bg.add(p)
                todo.append(p)
    while todo:
        x, y = todo.popleft()
        for n in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= n[0] < GRID and 0 <= n[1] < GRID and n not in bg and near_white(*n):
                bg.add(n)
                todo.append(n)
    return bg


def hexc(rgb, k=1.0):
    return "#%02x%02x%02x" % tuple(max(0, min(255, int(c * k))) for c in rgb)


def build(photo):
    img = Image.open(photo).convert("RGB")
    side = min(img.size)
    img = img.crop(((img.width - side) // 2, 0, (img.width + side) // 2, side))
    img = ImageEnhance.Contrast(img).enhance(1.15)
    small = img.resize((GRID, GRID), Image.LANCZOS)
    bg = background(small)
    pal = small.quantize(COLORS, method=Image.Quantize.MEDIANCUT).convert("RGB").load()
    grid = {}
    for y in range(GRID):
        for x in range(GRID):
            if (x, y) in bg:
                continue
            edge = any(n in bg or not (0 <= n[0] < GRID and 0 <= n[1] < GRID)
                       for n in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
            # dark outline on the silhouette, the classic pixel-art edge
            grid[x, y] = hexc(pal[x, y], 0.45) if edge and y < GRID - 1 else hexc(pal[x, y])
    return grid


def rows_svg(grid):
    out = []
    for y in range(GRID):
        runs, x = [], 0
        while x < GRID:
            c = grid.get((x, y))
            start = x
            while x < GRID and grid.get((x, y)) == c:
                x += 1
            if c:
                runs.append(f'<rect x="{OX + start * PX}" y="{OY + y * PX}" width="{(x - start) * PX}" height="{PX}" fill="{c}"/>')
        if runs:
            delay = "" if STATIC else f' style="animation-delay:{y * 28}ms"'
            side = "l" if y % 2 else "r"
            out.append(f'<g class="row {side}"{delay}>{"".join(runs)}</g>')
    return "".join(out)


def blink_svg(grid, eyes):
    """Cover each eye with the skin colour above it plus a lid line, shown briefly every few seconds."""
    rects = []
    for (ex, ey) in eyes:
        skin = grid.get((ex, ey - 3), "#c58d6a")
        rects.append(f'<rect x="{OX + (ex - 3) * PX}" y="{OY + (ey - 1) * PX}" width="{7 * PX}" height="{3 * PX}" fill="{skin}"/>')
        rects.append(f'<rect x="{OX + (ex - 3) * PX}" y="{OY + (ey + 1) * PX}" width="{7 * PX}" height="{PX}" fill="#2a1d18"/>')
    return f'<g class="blink" opacity="0">{"".join(rects)}</g>'


def svg(grid):
    # eye centres for this photo, in grid cells (avatar: eyes at about 40% and 61% across, 40% down)
    eyes = [(24, 24), (36, 24)]
    anim = "" if STATIC else """
.row{animation:in .55s cubic-bezier(.2,.8,.2,1) both}
.row.r{--d:24px}.row.l{--d:-24px}
.blink{opacity:0;animation:blink 5s 3s infinite}
.scan{animation:scan 4s 2.4s linear infinite}
.glow{animation:glow 3s 2s ease-in-out infinite alternate}
@keyframes in{from{opacity:0;transform:translateX(var(--d))}to{opacity:1;transform:none}}
@keyframes blink{0%,93%,100%{opacity:0}95%,97%{opacity:1}}
@keyframes scan{from{transform:translateY(-40px)}to{transform:translateY(400px)}}
@keyframes glow{from{opacity:.25}to{opacity:.6}}
@media (prefers-reduced-motion:reduce){.row,.blink,.scan,.glow{animation:none}.scan{display:none}}"""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" shape-rendering="crispEdges" role="img" aria-label="Pixel-art portrait of MD. Emon Miah">
<defs>
<radialGradient id="halo"><stop offset="0" stop-color="#818cf8" stop-opacity=".55"/><stop offset="1" stop-color="#818cf8" stop-opacity="0"/></radialGradient>
<linearGradient id="beam" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#38bdf8" stop-opacity="0"/><stop offset=".5" stop-color="#38bdf8" stop-opacity=".18"/><stop offset="1" stop-color="#38bdf8" stop-opacity="0"/></linearGradient>
<pattern id="lines" width="4" height="4" patternUnits="userSpaceOnUse"><rect width="4" height="1" fill="#000" opacity=".12"/></pattern>
<clipPath id="frame"><rect width="{W}" height="{H}" rx="12"/></clipPath>
</defs>
<style>{anim}</style>
<g clip-path="url(#frame)">
<rect width="{W}" height="{H}" fill="#0d1117"/>
<circle class="glow" cx="{W // 2}" cy="{H // 2 - 20}" r="160" fill="url(#halo)" opacity=".4"/>
{rows_svg(grid)}
{blink_svg(grid, eyes)}
<rect width="{W}" height="{H}" fill="url(#lines)"/>
<rect class="scan" y="0" width="{W}" height="40" fill="url(#beam)" transform="translate(0,-40)"/>
</g>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="12" fill="none" stroke="#30363d"/>
</svg>
"""


if __name__ == "__main__":
    g = build(sys.argv[1])
    assert len(g) > GRID * GRID // 4, "background removal ate the subject"
    with open(os.path.join(ROOT, "portrait.svg"), "w") as f:
        f.write(svg(g))
    print(f"{len(g)} pixels")
