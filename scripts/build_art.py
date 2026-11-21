"""Build the profile art: contrib-heatmap.svg (live data) and info-card.svg.

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
    cell, gap, left, top = 12, 3, 38, 56
    first = dt.date.fromisoformat(days[0]["date"])
    start = first - dt.timedelta(days=(first.weekday() + 1) % 7)  # back to Sunday
    weeks = (dt.date.fromisoformat(days[-1]["date"]) - start).days // 7 + 1
    width = left + weeks * (cell + gap) + 20
    height = top + 7 * (cell + gap) + 78
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
    best = s["best"]
    footer = [
        (f"{s['total']:,}", "contributions"),
        (f"{s['current']}d", "current streak"),
        (f"{s['longest']}d", "longest streak"),
        (f"{best['count']}", f"best day · {dt.date.fromisoformat(best['date']).strftime('%d %b')}"),
        (f"{s['active']}", "active days"),
    ]
    fw = (width - left - 20) / len(footer)
    stats_svg = "".join(
        f'<g class="s" style="animation-delay:{900 + i * 120}ms">'
        f'<text x="{left + i * fw}" y="{ly + 44}" class="n">{html.escape(v)}</text>'
        f'<text x="{left + i * fw}" y="{ly + 60}" class="t">{html.escape(k)}</text></g>'
        for i, (v, k) in enumerate(footer)
    )
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
<text x="{left}" y="20" class="h">$ git log --author={USER} --since="1 year ago"</text>
{"".join(months)}{labels}{"".join(rects)}
<text x="{width - 56 - 5 * 16 - 6}" y="{ly + 10}" class="t" text-anchor="end">less</text>{legend}
<text x="{width - 20}" y="{ly + 10}" class="t" text-anchor="end">more</text>
{stats_svg}
</svg>
"""


CARD = [
    ("OS", "Full-Stack Software Engineer"),
    ("Host", "Lilium Info Tech · Dhaka, Bangladesh"),
    ("Now", "San Uni Academy, a production LMS + store"),
    ("Prev", "Full-Stack Intern @ IBCS PRIMEx"),
    ("Stack", "Next.js · TypeScript · Node.js · Express"),
    ("Data", "PostgreSQL · Prisma · Redis · MongoDB"),
    ("Focus", "Real-time systems · voice AI agents"),
    ("Money", "Payments, append-only ledgers, payouts"),
    ("Infra", "AWS · Cloudflare R2 · Nginx · PM2"),
    ("Study", "B.Sc. CST, Bangladesh University"),
    ("Open", "Freelance · AI products · collaboration"),
]


def card_svg():
    width, top, line = 490, 74, 22
    height = top + len(CARD) * line + 56
    rows = []
    for i, (k, v) in enumerate(CARD):
        y = top + i * line
        delay = "" if STATIC else f' style="animation-delay:{300 + i * 110}ms"'
        rows.append(
            f'<g class="r"{delay}><text x="24" y="{y}" class="k">{k}</text>'
            f'<text x="96" y="{y}" class="v">{html.escape(v)}</text></g>'
        )
    swatch = "".join(
        f'<rect x="{24 + i * 26}" y="{height - 36}" width="20" height="12" rx="3" fill="{c}"/>'
        for i, c in enumerate(["#818cf8", "#c084fc", "#38bdf8", "#39d353", "#f59e0b", "#f43f5e", "#e6edf3"])
    )
    anim = "" if STATIC else """
.r{animation:in .45s ease-out both}
.cur{animation:blink 1s steps(1) infinite}
@keyframes in{from{opacity:0;transform:translateX(-8px)}to{opacity:1;transform:none}}
@keyframes blink{50%{opacity:0}}
@media (prefers-reduced-motion:reduce){.r,.cur{animation:none}}"""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}" role="img" aria-label="About MD. Emon Miah">
<style>
.k{{font:700 13px {FONT};fill:#818cf8}}
.v{{font:13px {FONT};fill:#c9d1d9}}
.p{{font:600 13px {FONT};fill:#39d353}}
.u{{font:700 15px {FONT};fill:#e6edf3}}{anim}
</style>
<rect width="100%" height="100%" rx="12" fill="#0d1117" stroke="#30363d"/>
<circle cx="22" cy="18" r="5" fill="#ff5f57"/><circle cx="40" cy="18" r="5" fill="#febc2e"/><circle cx="58" cy="18" r="5" fill="#28c840"/>
<text x="24" y="46" class="p">emon@bangladesh<tspan fill="#7d8590">:~$</tspan> <tspan fill="#c9d1d9">neofetch</tspan></text>
<line x1="24" y1="56" x2="{width - 24}" y2="56" stroke="#30363d"/>
{"".join(rows)}
{swatch}
<rect class="cur" x="{24 + 7 * 26 + 6}" y="{height - 38}" width="8" height="16" fill="#39d353"/>
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
    with open(os.path.join(ROOT, "info-card.svg"), "w") as f:
        f.write(card_svg())
    print(f"{len(days)} days, {s['total']} contributions, streak {s['current']}d (best {s['longest']}d)")


if __name__ == "__main__":
    # self-check of the streak logic on a tiny series
    t = stats([{"date": "d1", "count": 1}, {"date": "d2", "count": 2}, {"date": "d3", "count": 0},
               {"date": "d4", "count": 3}, {"date": "d5", "count": 0}])
    assert (t["total"], t["current"], t["longest"], t["active"]) == (6, 1, 2, 3), t
    main()
