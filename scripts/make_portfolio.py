"""Build the portfolio SVGs: one animated card per project and the experience timeline.

Standard library only. Run: python3 scripts/make_portfolio.py
Edit PROJECTS / TIMELINE below, re-run, commit. STATIC=1 writes frames without animation.
"""
import html
import os
import textwrap

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC = os.environ.get("STATIC") == "1"
FONT = "'JetBrains Mono','Fira Code',ui-monospace,SFMono-Regular,Menlo,monospace"

# (file slug, name, kind, description, stack, accent, has live demo)
PROJECTS = [
    ("sua", "San Uni Academy", "production · client", "Full LMS + merch store: marketplace, learning room, teacher studio, admin, ledger, protected video, live classes.", ["Next.js", "Express", "PostgreSQL", "Redis"], "#818cf8", True),
    ("dent-assist", "Dent-Assist", "voice AI", "AI voice dental receptionist that books appointments, triages symptoms and talks to patients live.", ["Next.js", "Vapi.ai", "OpenAI", "PostgreSQL"], "#38bdf8", True),
    ("game-point", "Hasibul Gaming Point", "e-commerce", "Digital goods store with a payment gateway, Telegram-bot fulfilment and live inventory.", ["Next.js 16", "MongoDB", "Zustand"], "#f59e0b", True),
    ("codebridge", "CodeBridge Live", "real-time", "Collaborative dev workspace with live code execution and synced editor state.", ["React", "Node.js", "WebSockets"], "#39d353", True),
    ("evidence-vault", "Evidence Vault", "SaaS", "Enterprise evidence tracking with artifact versioning and buyer request resolution.", ["Next.js", "TypeScript", "Tailwind"], "#c084fc", False),
    ("bismillah-agro", "Bismillah Agro", "dashboard", "Agricultural analytics dashboard with live farm metrics and inventory tracking.", ["Next.js", "Supabase", "Cloudinary"], "#22d3ee", True),
    ("chit-chat", "Chit-Chat", "real-time", "Low-latency messaging with typing indicators and delivery receipts.", ["React", "Socket.io", "Express"], "#f43f5e", True),
    ("project-pulse", "Project Pulse", "devtools", "Automated project health monitoring with a repository risk-scoring engine.", ["Next.js", "TypeScript", "PostgreSQL"], "#a3e635", False),
]

TIMELINE = [
    ("2024 – now", "Front-End Web Developer", "Lilium Info Tech", "Production Next.js platforms, GSAP motion, modern UI architecture", "#818cf8"),
    ("2023 – 2024", "Full-Stack Developer Intern", "IBCS PRIMEx", "Full-stack modules in Laravel, PHP and JavaScript", "#38bdf8"),
    ("2024 – 2028", "B.Sc. Computer Science & Technology", "Bangladesh University", "In progress", "#39d353"),
    ("2020 – 2024", "Diploma in Computer Science & Engineering", "Habiganj Polytechnic Institute", "Completed", "#f59e0b"),
]


def esc(s):
    return html.escape(s, quote=True)


def card(name, kind, desc, stack, accent, live):
    w, h = 425, 210
    lines = textwrap.wrap(desc, 46)[:3]
    desc_svg = "".join(f'<text x="24" y="{92 + i * 20}" class="d">{esc(l)}</text>' for i, l in enumerate(lines))
    chips, x = [], 24
    for i, s in enumerate(stack):
        cw = len(s) * 7.4 + 18
        delay = "" if STATIC else f' style="animation-delay:{500 + i * 120}ms"'
        chips.append(f'<g class="chip"{delay}><rect x="{x}" y="158" width="{cw:.0f}" height="24" rx="12" fill="{accent}" fill-opacity=".12" stroke="{accent}" stroke-opacity=".5"/>'
                     f'<text x="{x + cw / 2:.0f}" y="174" class="c" text-anchor="middle">{esc(s)}</text></g>')
        x += cw + 8
    status = ('<circle class="pulse" cx="{0}" cy="30" r="4" fill="#39d353"/><text x="{1}" y="34" class="k" text-anchor="end">live</text>'.format(w - 24, w - 34)
              if live else f'<text x="{w - 24}" y="34" class="k" text-anchor="end">source</text>')
    anim = "" if STATIC else """
.card{animation:rise .7s cubic-bezier(.2,.8,.2,1) both}
.chip{animation:pop .45s cubic-bezier(.2,.8,.2,1) both;transform-box:fill-box;transform-origin:center}
.edge{stroke-dasharray:1270;animation:draw 1.6s .2s ease-out both}
.pulse{animation:pulse 1.6s ease-in-out infinite;transform-box:fill-box;transform-origin:center}
@keyframes rise{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:none}}
@keyframes pop{from{opacity:0;transform:scale(.6)}to{opacity:1;transform:none}}
@keyframes draw{from{stroke-dashoffset:1270}to{stroke-dashoffset:0}}
@keyframes pulse{50%{opacity:.35;transform:scale(1.8)}}
@media (prefers-reduced-motion:reduce){.card,.chip,.edge,.pulse{animation:none}}"""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="{esc(name)}: {esc(desc)}">
<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{accent}" stop-opacity=".16"/><stop offset=".55" stop-color="#0d1117" stop-opacity="0"/></linearGradient></defs>
<style>
.t{{font:700 19px {FONT};fill:#e6edf3}}
.k{{font:600 11px {FONT};fill:{accent};letter-spacing:.06em;text-transform:uppercase}}
.d{{font:13px {FONT};fill:#9da7b3}}
.c{{font:600 11px {FONT};fill:#e6edf3}}{anim}
</style>
<g class="card">
<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="14" fill="#0d1117" stroke="#30363d"/>
<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="14" fill="url(#g)"/>
<rect class="edge" x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="14" fill="none" stroke="{accent}" stroke-opacity=".7"/>
<text x="24" y="34" class="k">{esc(kind)}</text>{status}
<text x="24" y="66" class="t">{esc(name)}</text>
{desc_svg}
{"".join(chips)}
</g>
</svg>
"""


def timeline():
    w, top, step = 860, 70, 74
    h = top + len(TIMELINE) * step - 10
    items = []
    for i, (when, title, org, note, accent) in enumerate(TIMELINE):
        y = top + i * step
        delay = "" if STATIC else f' style="animation-delay:{400 + i * 260}ms"'
        items.append(
            f'<g class="item"{delay}>'
            f'<circle cx="150" cy="{y}" r="9" fill="#0d1117" stroke="{accent}" stroke-width="3"/>'
            f'<circle cx="150" cy="{y}" r="3" fill="{accent}"/>'
            f'<text x="126" y="{y + 5}" class="w" text-anchor="end">{esc(when)}</text>'
            f'<text x="178" y="{y}" class="t">{esc(title)}</text>'
            f'<text x="178" y="{y + 22}" class="o"><tspan fill="{accent}">{esc(org)}</tspan> · {esc(note)}</text></g>'
        )
    anim = "" if STATIC else """
.line{stroke-dasharray:400;animation:draw 1.4s .2s ease-out both}
.item{animation:in .6s cubic-bezier(.2,.8,.2,1) both}
@keyframes draw{from{stroke-dashoffset:400}to{stroke-dashoffset:0}}
@keyframes in{from{opacity:0;transform:translateX(-12px)}to{opacity:1;transform:none}}
@media (prefers-reduced-motion:reduce){.line,.item{animation:none}}"""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="Experience and education timeline">
<style>
.h{{font:600 13px {FONT};fill:#818cf8}}
.w{{font:600 12px {FONT};fill:#7d8590}}
.t{{font:700 15px {FONT};fill:#e6edf3}}
.o{{font:12px {FONT};fill:#9da7b3}}{anim}
</style>
<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="12" fill="#0d1117" stroke="#30363d"/>
<text x="24" y="30" class="h">$ cat ~/journey.log</text>
<line class="line" x1="150" y1="{top}" x2="150" y2="{top + (len(TIMELINE) - 1) * step}" stroke="#30363d" stroke-width="2"/>
{"".join(items)}
</svg>
"""


if __name__ == "__main__":
    os.makedirs(os.path.join(ROOT, "projects"), exist_ok=True)
    for slug, *rest in PROJECTS:
        with open(os.path.join(ROOT, "projects", f"{slug}.svg"), "w") as f:
            f.write(card(*rest))
    with open(os.path.join(ROOT, "timeline.svg"), "w") as f:
        f.write(timeline())
    print(f"{len(PROJECTS)} project cards + timeline")
