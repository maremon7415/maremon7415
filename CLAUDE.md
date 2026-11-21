# maremon7415 — GitHub profile README

This repo is the GitHub profile page of MD. Emon Miah (github.com/maremon7415). `README.md` is the page itself; every picture on it is an animated SVG built by the scripts here. Pushing to `main` publishes it at once.

## Commands

| Command | What it does |
|---|---|
| `make setup` | one time: `.venv` with Pillow (only the portrait needs it) |
| `make art` | rebuild every data-driven SVG from live GitHub data |
| `make portrait PHOTO=assets/photo.jpg` | rebuild the ASCII portrait from a photo on a plain light background |
| `make preview` | render `README.md` exactly as GitHub does (`gh api markdown`) and serve it on localhost:8765 |
| `make check` | build everything and confirm every SVG parses |
| `make publish m="msg"` | commit and push (goes live) |
| `make streak` | if GitHub shows no contribution today, refresh the art and push it (`--force` in `scripts/streak.sh` skips the check) |
| `make streak-install` | systemd user timer runs `make streak` at 18:00, 21:00 and 23:15 Dhaka; a missed run fires on wake or boot. Log: `journalctl --user -u profile-streak` |

Needs `python3`, `uv` (setup only) and the GitHub CLI `gh` signed in (preview, and a higher API limit for `make art`).

## Files

| File | Built by | Data |
|---|---|---|
| `portrait.svg` | `scripts/make_portrait.py` | `assets/photo.jpg` (run by hand) |
| `stats.svg` | `scripts/build_art.py` | public contributions page |
| `skyline.svg`, `projects/*.svg`, `stack.svg`, `journey.svg` | `scripts/build_sections.py` | contributions page + GitHub REST API |
| `data/contributions.json` | `scripts/build_art.py` | raw days and stats |

Text that is not data lives at the top of `scripts/build_sections.py`: `PROJECTS` (repo, title, one-line pitch, live link), `TOOLS`, `JOURNEY`. To add a project: add a row there, add a card cell to the `ls ~/projects` table in `README.md`, run `make art`.

`.github/workflows/update-profile-art.yml` reruns both build scripts daily at 06:17 Dhaka time and commits the result. It cannot run while the GitHub account has a billing lock (every job fails with "account is locked due to a billing issue"); then the streak timer does the refresh whenever the laptop is on in the evening. The workflow commits as the owner's noreply address so its commits count on the contribution graph.

## Rules

- **Page order:** `whoami` (portrait + stats) first, then `contributions --last-year` (skyline), projects, stack, history, contact. Section headings are `<h3><code>maremon7415 ~ % …</code></h3>`.
- **Look:** terminal style. Panels `#0d1117` with a `#30363d` border and 10px radius; text `#e6edf3`, muted `#7d8590`, accent green `#39d353`, GitHub contribution greens for data. Monospace font stack (`FONT` in `build_art.py`). Widths add up to 860 (370 + 490, or 2 × 425).
- **No invented numbers.** Every figure comes from GitHub data; no hand-set skill percentages. Language shares are real bytes across the owner's non-fork repos.
- **No repetition.** Each fact appears once on the page (the old README repeated links and badges and the owner disliked it).
- **GitHub limits:** images are `<img>`, so no hover, no JavaScript, no web fonts; animation lives inside each SVG (CSS keyframes or SMIL). Inline `style` attributes in README HTML are stripped. Every animation turns off under `prefers-reduced-motion`.
- **Stdlib only** for the build scripts (they run in the Action with plain `python3`); Pillow only for the portrait.
- **Check visually before pushing:** `make preview`, and watch the animations finish.
- GitHub's own "Pinned" repos and contribution graph below the README cannot be styled from here; pins are set in the GitHub UI (Customize your pins).
