"""Build the sections below the hero, in the hero's style, from live GitHub data:
skyline.svg (3D contributions), projects/*.svg, stack.svg, journey.svg.

Standard library only. Run: GITHUB_TOKEN=... python3 scripts/build_sections.py
(the token only raises the API rate limit; public data works without it). STATIC=1 freezes animation.
"""
import datetime as dt
import html
import json
import math
import os
import sys
import textwrap
import time
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_art import FONT, PALETTE, ROOT, STATIC, USER, fetch_days, stats  # noqa: E402

BG, LINE, MUTED, TEXT, GREEN = "#0d1117", "#30363d", "#7d8590", "#e6edf3", "#39d353"
W = 860

# repo, title, one-line pitch, live link (None = use the repo's homepage)
PROJECTS = [
    ("dent_assis", "Dent-Assist", "AI voice receptionist for dental clinics: books visits, triages symptoms, talks live.", None),
    ("project-pulse", "Project Pulse", "Project health monitoring with automated health checks and a repository risk-scoring engine.", None),
    ("codeBridge_live", "CodeBridge Live", "Collaborative dev workspace with live code execution and synced editor state.", None),
    ("bismillah_agro", "Bismillah Agro", "Agricultural analytics dashboard with live farm metrics and inventory tracking.", None),
    ("EvidenceVault_RequestFulfillmentUI", "Evidence Vault", "Enterprise evidence tracking with artifact versioning and buyer request resolution.", None),
    ("FullStackEcommece", "Full-Stack Store", "Clothing store with catalog, cart and checkout on a Node and Express API.", None),
    ("chat_app", "Chit-Chat", "Real-time messaging with typing indicators and delivery receipts.", "https://chitchat-1h8wz.sevalla.app"),
    ("holy_quran", "Holy Quran", "A fast, clean Quran reader for the web.", None),
]

TOOLS = [
    ("frontend", ["Next.js", "React", "Tailwind", "Redux", "GSAP"]),
    ("backend", ["Node.js", "Express", "Socket.io", "Laravel"]),
    ("data", ["PostgreSQL", "Prisma", "Redis", "MongoDB", "Supabase"]),
    ("cloud", ["AWS", "Cloudflare R2", "Nginx", "PM2", "Vercel"]),
    ("ai & media", ["OpenAI", "Vapi.ai", "LiveKit", "Bunny Stream"]),
    ("payments", ["Stripe", "SSLCommerz"]),
]

JOURNEY = [
    ("2024 – now", "Front-End Web Developer", "Lilium Info Tech", "production Next.js platforms, GSAP motion, UI architecture"),
    ("2023 – 2024", "Full-Stack Developer Intern", "IBCS PRIMEx", "full-stack modules in Laravel, PHP and JavaScript"),
    ("2024 – 2028", "B.Sc. Computer Science & Technology", "Bangladesh University", "in progress"),
    ("2020 – 2024", "Diploma in Computer Science & Engineering", "Habiganj Polytechnic Institute", "completed"),
]

LANG_COLORS = {"TypeScript": "#3178c6", "JavaScript": "#f1e05a", "HTML": "#e34c26", "CSS": "#663399",
               "Python": "#3572A5", "PHP": "#4F5D95", "Shell": "#89e051"}


def esc(s):
    return html.escape(str(s), quote=True)


def api(path, retries=3):
    req = urllib.request.Request(f"https://api.github.com/{path}", headers={"User-Agent": "profile-art-builder", "Accept": "application/vnd.github+json"})
    if os.environ.get("GITHUB_TOKEN"):
        req.add_header("Authorization", f"Bearer {os.environ['GITHUB_TOKEN']}")
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read() or "null")
        except (TimeoutError, urllib.error.URLError) as e:
            if isinstance(e, urllib.error.HTTPError) or attempt == retries - 1:
                raise
            time.sleep(2)


def shade(hexc, k):
    r, g, b = (int(hexc[i:i + 2], 16) for i in (1, 3, 5))
    return "#%02x%02x%02x" % tuple(max(0, min(255, int(c * k))) for c in (r, g, b))


def frame(w, h, body, style, label):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="{esc(label)}">
<style>text{{font-family:{FONT}}}{style}</style>
<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="10" fill="{BG}" stroke="{LINE}"/>
{body}
</svg>
"""


def motion(css):
    return "" if STATIC else css


# ---------- contributions as a 3D skyline ----------
def skyline(days, s):
    h = 400
    ux, uy, vx, vy = 12.6, 3.3, -9.0, 5.0  # one week along u, one weekday along v
    ox, oy, maxh = 96, 150, 120
    first = dt.date.fromisoformat(days[0]["date"])
    start = first - dt.timedelta(days=(first.weekday() + 1) % 7)
    top = max(d["count"] for d in days) or 1
    cells = []
    for d in days:
        day = dt.date.fromisoformat(d["date"])
        w, wd = (day - start).days // 7, (day.weekday() + 1) % 7
        cells.append((w, wd, d, day))
    cells.sort(key=lambda c: (c[0] + c[1], c[0]))  # painter's order: back to front
    k = 0.84
    out = []
    best_top = None
    for w, wd, d, day in cells:
        px, py = ox + w * ux + wd * vx, oy + w * uy + wd * vy
        b = [(px, py), (px + ux * k, py + uy * k), (px + (ux + vx) * k, py + (uy + vy) * k), (px + vx * k, py + vy * k)]
        hh = 2 if not d["count"] else 4 + math.sqrt(d["count"] / top) * maxh
        t = [(x, y - hh) for x, y in b]
        col = PALETTE[d["level"]] if d["count"] else "#1b222c"
        pts = lambda ps: " ".join(f"{x:.1f},{y:.1f}" for x, y in ps)
        faces = (f'<polygon points="{pts([t[1], t[2], b[2], b[1]])}" fill="{shade(col, .55)}"/>'
                 f'<polygon points="{pts([t[3], t[2], b[2], b[3]])}" fill="{shade(col, .78)}"/>'
                 f'<polygon points="{pts(t)}" fill="{shade(col, 1.15)}"><title>{d["count"]} on {d["date"]}</title></polygon>')
        if d["count"]:
            delay = "" if STATIC else f' style="animation-delay:{w * 28 + wd * 12}ms"'
            out.append(f'<g class="b"{delay}>{faces}</g>')
        else:
            out.append(faces)
        if d is s["best"]:
            best_top = ((t[0][0] + t[2][0]) / 2, (t[0][1] + t[2][1]) / 2)
    # month labels along the front edge
    months, seen = [], set()
    for w, wd, d, day in sorted(cells):
        if wd == 6 and day.day <= 7 and (day.year, day.month) not in seen:
            seen.add((day.year, day.month))
            x, y = ox + w * ux + 7 * vx, oy + w * uy + 7 * vy
            months.append(f'<text x="{x - 4:.0f}" y="{y + 16:.0f}" class="m">{day.strftime("%b")}</text>')
    pin = ""
    if best_top:
        bx, by = best_top
        pin = (f'<g class="pin"><line x1="{bx:.0f}" y1="{by - 4:.0f}" x2="{bx:.0f}" y2="{by - 34:.0f}" stroke="{GREEN}" stroke-dasharray="2 3"/>'
               f'<circle cx="{bx:.0f}" cy="{by - 3:.0f}" r="2.5" fill="{GREEN}"/>'
               f'<text x="{bx - 8:.0f}" y="{by - 40:.0f}" class="p" text-anchor="end">best day · {s["best"]["count"]} on {dt.date.fromisoformat(s["best"]["date"]).strftime("%d %b")}</text></g>')
    legend = "".join(f'<rect x="{24 + i * 15}" y="{h - 34}" width="11" height="11" rx="2" fill="{c}"/>' for i, c in enumerate(PALETTE))
    body = (f'<text x="24" y="34" class="t">{s["total"]:,}</text>'
            f'<text x="24" y="54" class="m">contributions in the last year</text>'
            f'<text x="24" y="76" class="m">tallest towers = busiest days</text>'
            f'{"".join(out)}{"".join(months)}{pin}{legend}'
            f'<text x="{24 + 5 * 15 + 6}" y="{h - 25}" class="m">less → more</text>')
    style = f""".t{{font-size:26px;font-weight:700;fill:{TEXT}}}.m{{font-size:10px;fill:{MUTED}}}.p{{font-size:11px;font-weight:600;fill:{GREEN}}}""" + motion(f"""
.b{{animation:rise .9s cubic-bezier(.2,.8,.2,1) both;transform-box:fill-box;transform-origin:50% 100%}}
.pin{{animation:fade .6s 2.2s both}}
@keyframes rise{{from{{transform:scaleY(0);opacity:0}}to{{transform:none;opacity:1}}}}
@keyframes fade{{from{{opacity:0}}to{{opacity:1}}}}
@media (prefers-reduced-motion:reduce){{.b,.pin{{animation:none}}}}""")
    return frame(W, h, body, style, f"{s['total']} contributions in the last year as a 3D skyline")


# ---------- project cards ----------
def ago(iso):
    days = (dt.datetime.now(dt.timezone.utc) - dt.datetime.fromisoformat(iso.replace("Z", "+00:00"))).days
    return "today" if days < 1 else f"{days}d ago" if days < 31 else f"{days // 30}mo ago" if days < 365 else f"{days // 365}y ago"


def project_card(repo, title, pitch, link, info, weeks, commits, first, last):
    w, h = 425, 196
    lang = info.get("language") or "—"
    lc = LANG_COLORS.get(lang, MUTED)
    host = (link or info.get("homepage") or "").replace("https://", "").replace("http://", "").rstrip("/")
    desc = "".join(f'<text x="22" y="{86 + i * 18}" class="d">{esc(l)}</text>' for i, l in enumerate(textwrap.wrap(pitch, 52)[:2]))
    # commit sparkline, last 26 weeks
    top = max(weeks) or 1
    sx, sy, sw, sh = 22, 162, w - 44, 26
    pts = [(sx + i * sw / (len(weeks) - 1), sy - v / top * sh) for i, v in enumerate(weeks)]
    line = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    area = f"{sx},{sy} {line} {sx + sw},{sy}"
    period = f"{first:%b %Y} – {last:%b %Y}" if first else "no commits yet"
    stars = f" · ★ {info['stargazers_count']}" if info.get("stargazers_count") else ""
    body = (f'<text x="22" y="30" class="r"><tspan fill="{GREEN}">~/</tspan>{esc(repo)}</text>'
            f'<text x="{w - 22}" y="30" class="l" text-anchor="end">{"↗ " + esc(host) if host else "↗ source"}</text>'
            f'<text x="22" y="60" class="t">{esc(title)}</text>{desc}'
            f'<text x="{w - 22}" y="{sy - sh - 8}" class="m" text-anchor="end">{commits}{"+" if commits >= 500 else ""} commits · {period}</text>'
            f'<polygon class="a" points="{area}" fill="{GREEN}" fill-opacity=".12"/>'
            f'<polyline class="s" points="{line}" fill="none" stroke="{GREEN}" stroke-width="1.6" stroke-linejoin="round" pathLength="1"/>'
            f'<circle cx="27" cy="{h - 20}" r="5" fill="{lc}"/>'
            f'<text x="38" y="{h - 16}" class="m">{esc(lang)} · last commit {ago(last.isoformat() if last else info["pushed_at"])}{stars}</text>')
    style = f""".r{{font-size:11px;fill:{MUTED}}}.t{{font-size:18px;font-weight:700;fill:{TEXT}}}.d{{font-size:12px;fill:#9da7b3}}.m{{font-size:10px;fill:{MUTED}}}.l{{font-size:10px;font-weight:600;fill:{GREEN}}}""" + motion("""
.s{stroke-dasharray:1;animation:draw 1.6s .3s cubic-bezier(.4,0,.2,1) both}
.a{animation:fade 1s 1.2s both}
@keyframes draw{from{stroke-dashoffset:1}to{stroke-dashoffset:0}}
@keyframes fade{from{opacity:0}to{opacity:1}}
@media (prefers-reduced-motion:reduce){.s,.a{animation:none}}""")
    return frame(w, h, body, style, f"{title}: {pitch}")


# ---------- stack ----------
def stack(langs, repo_count):
    h = 300
    total = sum(langs.values()) or 1
    top = sorted(langs.items(), key=lambda kv: -kv[1])[:7]
    parts = [f'<text x="24" y="34" class="h">languages · share of code across {repo_count} repos</text>']
    for i, (name, n) in enumerate(top):
        y = 62 + i * 32
        pct = n / total * 100
        bw = max(3, pct / 100 * 300)
        c = LANG_COLORS.get(name, MUTED)
        delay = "" if STATIC else f' style="animation-delay:{200 + i * 110}ms"'
        parts.append(f'<text x="24" y="{y + 10}" class="n">{esc(name)}</text>'
                     f'<rect x="120" y="{y}" width="300" height="12" rx="6" fill="#161b22"/>'
                     f'<rect class="bar"{delay} x="120" y="{y}" width="{bw:.1f}" height="12" rx="6" fill="{c}"/>'
                     f'<text x="430" y="{y + 10}" class="v">{pct:.1f}%</text>')
    parts.append(f'<line x1="484" y1="24" x2="484" y2="{h - 24}" stroke="#21262d"/>')
    y = 34
    for gi, (group, items) in enumerate(TOOLS):
        parts.append(f'<text x="508" y="{y}" class="h">{esc(group)}</text>')
        x = 508
        y += 10
        for j, t in enumerate(items):
            cw = len(t) * 6.6 + 16
            if x + cw > W - 20:
                x, y = 508, y + 26
            delay = "" if STATIC else f' style="animation-delay:{300 + gi * 140 + j * 50}ms"'
            parts.append(f'<g class="chip"{delay}><rect x="{x:.0f}" y="{y}" width="{cw:.0f}" height="20" rx="10" fill="#161b22" stroke="{LINE}"/>'
                         f'<text x="{x + cw / 2:.0f}" y="{y + 14}" class="c" text-anchor="middle">{esc(t)}</text></g>')
            x += cw + 6
        y += 40
    style = f""".h{{font-size:10px;fill:{MUTED};text-transform:uppercase;letter-spacing:.08em}}.n{{font-size:12px;fill:{TEXT}}}.v{{font-size:11px;fill:{MUTED}}}.c{{font-size:11px;fill:#c9d1d9}}""" + motion("""
.bar{animation:grow 1s cubic-bezier(.2,.8,.2,1) both;transform-box:fill-box;transform-origin:0 50%}
.chip{animation:pop .45s cubic-bezier(.2,.8,.2,1) both;transform-box:fill-box;transform-origin:center}
@keyframes grow{from{transform:scaleX(0)}to{transform:none}}
@keyframes pop{from{opacity:0;transform:scale(.7)}to{opacity:1;transform:none}}
@media (prefers-reduced-motion:reduce){.bar,.chip{animation:none}}""")
    return frame(W, max(h, y), "".join(parts), style, "Languages by share of code, and the tools I use")


# ---------- journey ----------
def journey():
    top, step = 40, 64
    h = top + len(JOURNEY) * step - 8
    items = []
    for i, (when, title, org, note) in enumerate(JOURNEY):
        y = top + i * step
        now = i == 0
        delay = "" if STATIC else f' style="animation-delay:{300 + i * 220}ms"'
        dot = (f'<circle class="pulse" cx="150" cy="{y}" r="9" fill="{GREEN}" fill-opacity=".25"/>' if now else "") + \
              f'<circle cx="150" cy="{y}" r="5" fill="{GREEN if now else BG}" stroke="{GREEN}" stroke-width="2"/>'
        items.append(f'<g class="it"{delay}>{dot}'
                     f'<text x="128" y="{y + 4}" class="w" text-anchor="end">{esc(when)}</text>'
                     f'<text x="176" y="{y + 1}" class="t">{esc(title)}</text>'
                     f'<text x="176" y="{y + 21}" class="o"><tspan fill="{GREEN}">{esc(org)}</tspan> · {esc(note)}</text></g>')
    body = (f'<line class="ln" x1="150" y1="{top}" x2="150" y2="{top + (len(JOURNEY) - 1) * step}" stroke="{LINE}" stroke-width="2" pathLength="1"/>'
            + "".join(items))
    style = f""".w{{font-size:11px;font-weight:600;fill:{MUTED}}}.t{{font-size:14px;font-weight:700;fill:{TEXT}}}.o{{font-size:11px;fill:#9da7b3}}""" + motion("""
.ln{stroke-dasharray:1;animation:draw 1.2s .1s ease-out both}
.it{animation:in .6s cubic-bezier(.2,.8,.2,1) both}
.pulse{animation:pulse 1.8s ease-in-out infinite;transform-box:fill-box;transform-origin:center}
@keyframes draw{from{stroke-dashoffset:1}to{stroke-dashoffset:0}}
@keyframes in{from{opacity:0;transform:translateX(-10px)}to{opacity:1;transform:none}}
@keyframes pulse{50%{transform:scale(1.7);opacity:.2}}
@media (prefers-reduced-motion:reduce){.ln,.it,.pulse{animation:none}}""")
    return frame(W, h, body, style, "Experience and education")


def commit_history(repo, bins=40):
    """Commits bucketed over the repo's life (first to last commit), plus the first and last dates."""
    dates = []
    try:
        for page in range(1, 6):
            batch = api(f"repos/{USER}/{repo}/commits?per_page=100&page={page}") or []
            dates += [dt.datetime.fromisoformat(c["commit"]["author"]["date"].replace("Z", "+00:00")) for c in batch]
            if len(batch) < 100:
                break
    except urllib.error.HTTPError:  # an empty repo answers 409
        pass
    if not dates:
        return [0] * bins, 0, None, None
    first, last = min(dates), max(dates)
    span = max((last - first).total_seconds(), 1)
    counts = [0] * bins
    for d in dates:
        counts[min(bins - 1, int((d - first).total_seconds() / span * bins))] += 1
    return counts, len(dates), first, last


def write(name, text):
    path = os.path.join(ROOT, name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(text)


def main():
    days = fetch_days()
    write("skyline.svg", skyline(days, stats(days)))
    repos = {r["name"]: r for r in api(f"users/{USER}/repos?per_page=100&type=owner")}
    own = [r for r in repos.values() if not r["fork"] and r["name"] != USER]
    langs = {}
    for r in own:
        for k, v in (api(f"repos/{USER}/{r['name']}/languages") or {}).items():
            langs[k] = langs.get(k, 0) + v
    write("stack.svg", stack(langs, len(own)))
    for repo, title, pitch, link in PROJECTS:
        if repo not in repos:
            print(f"skip {repo}: not found")
            continue
        write(f"projects/{repo}.svg", project_card(repo, title, pitch, link, repos[repo], *commit_history(repo)))
    write("journey.svg", journey())
    print(f"skyline, stack ({len(own)} repos), {len(PROJECTS)} cards, journey")


if __name__ == "__main__":
    assert shade("#808080", .5) == "#404040"
    assert ago(dt.datetime.now(dt.timezone.utc).isoformat()) == "today"
    main()
