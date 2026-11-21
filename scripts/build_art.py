"""Build the profile art: contrib-heatmap.svg and stats.svg, both from live data.

Standard library only. Run: python3 scripts/build_art.py
Set STATIC=1 to write frames without animation (for previews).
"""
import datetime as dt
import html
import json
import os
import re
import urllib.request

USER = "maremon7415"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC = os.environ.get("STATIC") == "1"
FONT = "'JetBrains Mono','Fira Code',ui-monospace,SFMono-Regular,Menlo,monospace"
PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]


def fetch_days():
    # shortcut: GitHub's public contributions fragment is undocumented, switch to the GraphQL API if it changes
    req = urllib.request.Request(
        f"https://github.com/users/{USER}/contributions",
        headers={"User-Agent": "profile-art-builder"},
    )
    page = urllib.request.urlopen(req, timeout=30).read().decode()
    cells = re.findall(r'<td[^>]*data-date="([\d-]+)"[^>]*id="([^"]+)"[^>]*data-level="(\d)"', page)
    tips = dict(re.findall(r'<tool-tip[^>]*for="([^"]+)"[^>]*>([^<]*)</tool-tip>', page))
    days = []
    for date, cid, level in cells:
        m = re.match(r"(\d+) contribution", tips.get(cid, ""))
        days.append({"date": date, "level": int(level), "count": int(m.group(1)) if m else 0})
    if len(days) < 300:
        raise SystemExit(f"only {len(days)} days parsed; page format changed, nothing written")
    return sorted(days, key=lambda d: d["date"])


def stats(days):
    total = sum(d["count"] for d in days)
    longest = run = 0
    for d in days:
        run = run + 1 if d["count"] else 0
        longest = max(longest, run)
    current = 0
    tail = days[:-1] if days[-1]["count"] == 0 else days  # today may still be empty
    for d in reversed(tail):
        if not d["count"]:
            break
        current += 1
    best = max(days, key=lambda d: d["count"])
    active = sum(1 for d in days if d["count"])
    return {"total": total, "current": current, "longest": longest, "best": best, "active": active}


def heatmap_svg(days, s):
    cell, gap, left, top = 12, 3, 38, 36
    first = dt.date.fromisoformat(days[0]["date"])
    start = first - dt.timedelta(days=(first.weekday() + 1) % 7)  # back to Sunday
    weeks = (dt.date.fromisoformat(days[-1]["date"]) - start).days // 7 + 1
    width = left + weeks * (cell + gap) + 20
    height = top + 7 * (cell + gap) + 34
    rects, months, seen = [], [], set()
    for d in days:
        day = dt.date.fromisoformat(d["date"])
        col, row = (day - start).days // 7, (day.weekday() + 1) % 7
        x, y = left + col * (cell + gap), top + row * (cell + gap)
        delay = f' style="animation-delay:{col * 18}ms"' if not STATIC else ""
        rects.append(
            f'<rect class="c" x="{x}" y="{y}" width="{cell}" height="{cell}" rx="3" '
            f'fill="{PALETTE[d["level"]]}"{delay}><title>{d["count"]} on {d["date"]}</title></rect>'
        )
        key = (day.year, day.month)
        if day.day <= 7 and key not in seen and col < weeks - 1:
            seen.add(key)
            months.append(f'<text x="{x}" y="{top - 10}" class="t">{day.strftime("%b")}</text>')
    labels = "".join(
        f'<text x="{left - 8}" y="{top + r * (cell + gap) + 10}" class="t" text-anchor="end">{n}</text>'
        for r, n in ((1, "Mon"), (3, "Wed"), (5, "Fri"))
    )
    ly = top + 7 * (cell + gap) + 12
    legend = "".join(
        f'<rect x="{width - 56 - (5 - i) * 16}" y="{ly}" width="12" height="12" rx="3" fill="{c}"/>'
        for i, c in enumerate(PALETTE)
    )
    stats_svg = f'<text x="{left}" y="{ly + 10}" class="t"><tspan fill="#e6edf3" font-weight="700">{s['total']:,}</tspan> contributions in the last year</text>'
    anim = "" if STATIC else """
.c{animation:pop .5s cubic-bezier(.2,.8,.2,1) both;transform-box:fill-box;transform-origin:center}
.s{animation:up .6s ease-out both}
@keyframes pop{from{opacity:0;transform:scale(.3)}to{opacity:1;transform:scale(1)}}
@keyframes up{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}
@media (prefers-reduced-motion:reduce){.c,.s{animation:none}}"""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}" role="img" aria-label="{s['total']} GitHub contributions in the last year">
<style>
.t{{font:11px {FONT};fill:#7d8590}}
.n{{font:700 16px {FONT};fill:#e6edf3}}
.h{{font:600 13px {FONT};fill:#818cf8}}{anim}
</style>
<rect width="100%" height="100%" rx="12" fill="#0d1117" stroke="#30363d"/>
{"".join(months)}{labels}{"".join(rects)}
<text x="{width - 56 - 5 * 16 - 6}" y="{ly + 10}" class="t" text-anchor="end">less</text>{legend}
<text x="{width - 20}" y="{ly + 10}" class="t" text-anchor="end">more</text>
{stats_svg}
</svg>
"""


def number_svg(text, x, base, size, color, delay):
    """Big number whose digits roll into place like an odometer."""
    adv, lh = size * 0.62, size * 1.2
    out, cx = [], x
    for i, ch in enumerate(text):
        if ch.isdigit() and not STATIC:
            d = int(ch)
            col = "".join(f'<text x="{cx:.1f}" y="{base + k * lh:.1f}">{k}</text>' for k in range(d + 1))
            out.append(f'<g class="roll" style="--y:{-d * lh:.1f}px;animation-delay:{delay + i * 70}ms">{col}</g>')
        else:
            out.append(f'<text x="{cx:.1f}" y="{base}">{html.escape(ch)}</text>')
        cx += adv
    return f'<g fill="{color}" font-size="{size}" font-weight="700">{"".join(out)}</g>', cx


def stats_card(days, s):
    w, h = 490, 380
    best = s["best"]
    avg = s["total"] / s["active"] if s["active"] else 0
    cells = [
        ("current streak", f"{s['current']}", "days", "#39d353"),
        ("longest streak", f"{s['longest']}", "days", "#e6edf3"),
        ("contributions", f"{s['total']:,}", "last 12 months", "#e6edf3"),
        ("best day", f"{best['count']}", dt.date.fromisoformat(best["date"]).strftime("%d %b %Y"), "#e6edf3"),
        ("active days", f"{s['active']}", f"of {len(days)}", "#e6edf3"),
        ("per active day", f"{avg:.1f}", "average", "#e6edf3"),
    ]
    parts, clips = [], []
    cw, ch, gx, gy = 213, 60, 24, 44
    for i, (label, value, unit, color) in enumerate(cells):
        x, y = gx + (i % 2) * (cw + 16), gy + (i // 2) * (ch + 10)
        clips.append(f'<clipPath id="n{i}"><rect x="{x}" y="{y + 18}" width="{cw}" height="34"/></clipPath>')
        num, end = number_svg(value, x + 14, y + 46, 26, color, 300 + i * 120)
        parts.append(
            f'<g class="cell" style="animation-delay:{150 + i * 90}ms"><rect x="{x}" y="{y}" width="{cw}" height="{ch}" rx="8" fill="#161b22" stroke="#21262d"/>'
            f'<text x="{x + 14}" y="{y + 17}" class="l">{label}</text>'
            f'<g clip-path="url(#n{i})">{num}</g>'
            f'<text x="{end + 6:.1f}" y="{y + 46}" class="u">{html.escape(unit)}</text></g>'
        )
    # contributions per month for the last 12 months
    months = {}
    for d in days:
        months[d["date"][:7]] = months.get(d["date"][:7], 0) + d["count"]
    keys = sorted(months)[-12:]
    top = max(months[k] for k in keys) or 1
    bx, base, bw, bh = gx, h - 30, 30, 58
    parts.append(f'<text x="{gx}" y="{base - bh - 12}" class="l">contributions per month</text>')
    for i, k in enumerate(keys):
        v = months[k]
        hh = max(2, v / top * bh)
        x = bx + i * (bw + 7.4)
        fill = "#39d353" if v == top else "#26a641" if v > top / 2 else "#006d32"
        parts.append(
            f'<rect class="bar" style="animation-delay:{900 + i * 70}ms" x="{x:.1f}" y="{base - hh:.1f}" width="{bw}" height="{hh:.1f}" rx="3" fill="{fill}"><title>{v} in {k}</title></rect>'
            f'<text x="{x + bw / 2:.1f}" y="{base + 16}" class="m" text-anchor="middle">{dt.date.fromisoformat(k + "-01").strftime("%b")[0]}</text>'
        )
    anim = "" if STATIC else """
.cell{animation:in .5s ease-out both}
.roll{animation:roll 1.1s cubic-bezier(.2,.8,.2,1) both}
.bar{animation:grow .7s cubic-bezier(.2,.8,.2,1) both;transform-box:fill-box;transform-origin:50% 100%}
@keyframes in{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}
@keyframes roll{from{transform:none}to{transform:translateY(var(--y))}}
@keyframes grow{from{transform:scaleY(0)}to{transform:scaleY(1)}}
@media (prefers-reduced-motion:reduce){.cell,.roll,.bar{animation:none}.roll{transform:translateY(var(--y))}}"""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="{s['total']} contributions, current streak {s['current']} days, longest {s['longest']} days">
<defs>{"".join(clips)}</defs>
<style>
text{{font-family:{FONT}}}
.h{{font-size:12px;font-weight:600;fill:#7d8590}}
.l{{font-size:10px;fill:#7d8590;text-transform:uppercase;letter-spacing:.08em}}
.u{{font-size:11px;fill:#7d8590}}
.m{{font-size:10px;fill:#7d8590}}{anim}
</style>
<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="10" fill="#0d1117" stroke="#30363d"/>
<text x="{gx}" y="28" class="h"><tspan fill="#39d353">maremon7415</tspan> ~ % gh stats</text>
{"".join(parts)}
</svg>
"""


def main():
    days = fetch_days()
    s = stats(days)
    os.makedirs(os.path.join(ROOT, "data"), exist_ok=True)
    with open(os.path.join(ROOT, "data", "contributions.json"), "w") as f:
        json.dump({"stats": s, "days": days}, f, indent=1)
    with open(os.path.join(ROOT, "contrib-heatmap.svg"), "w") as f:
        f.write(heatmap_svg(days, s))
    with open(os.path.join(ROOT, "stats.svg"), "w") as f:
        f.write(stats_card(days, s))
    print(f"{len(days)} days, {s['total']} contributions, streak {s['current']}d (best {s['longest']}d)")


if __name__ == "__main__":
    # self-check of the streak logic on a tiny series
    t = stats([{"date": "d1", "count": 1}, {"date": "d2", "count": 2}, {"date": "d3", "count": 0},
               {"date": "d4", "count": 3}, {"date": "d5", "count": 0}])
    assert (t["total"], t["current"], t["longest"], t["active"]) == (6, 1, 2, 3), t
    main()
