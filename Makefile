# GitHub profile README. Run `make help`.
PY      ?= python3
VENV    := .venv
PHOTO   ?= assets/photo.jpg
PORT    ?= 8765
TOKEN    = $(shell gh auth token 2>/dev/null)

.PHONY: help setup art portrait preview check publish streak streak-install

help:
	@echo "make setup            one-time: create .venv with Pillow (for the portrait only)"
	@echo "make art              rebuild stats, skyline, project cards, stack, history from live GitHub data"
	@echo "make portrait         rebuild the ASCII portrait from PHOTO=$(PHOTO)"
	@echo "make preview          render README.md like GitHub does and serve it on http://localhost:$(PORT)/.preview.html"
	@echo "make check            build everything and confirm every SVG parses"
	@echo "make publish m=\"msg\"  commit everything and push (goes live on github.com/maremon7415)"
	@echo "make streak           if GitHub shows no contribution today, refresh the art and push it"
	@echo "make streak-install   run make streak automatically at 18:00, 21:00 and 23:15 (systemd user timer)"

setup:
	uv venv --quiet $(VENV)
	uv pip install --quiet --python $(VENV)/bin/python -r requirements-dev.txt
	@command -v gh >/dev/null || echo "note: install the GitHub CLI (gh) for previews and a higher API limit"
	@echo "ready"

art:
	$(PY) scripts/build_art.py
	GITHUB_TOKEN=$(TOKEN) $(PY) scripts/build_sections.py

portrait:
	$(VENV)/bin/python scripts/make_portrait.py $(PHOTO) >/dev/null
	@echo "portrait.svg rebuilt from $(PHOTO)"

preview:
	gh api markdown -f mode=gfm -f context=maremon7415/maremon7415 -F text=@README.md > .preview.body
	$(PY) scripts/preview.py .preview.body .preview.html
	@echo "open http://localhost:$(PORT)/.preview.html  (Ctrl+C to stop)"
	$(PY) -m http.server $(PORT) --bind 127.0.0.1

check: art
	$(PY) -c "import glob, xml.dom.minidom as m; fs = glob.glob('*.svg') + glob.glob('projects/*.svg'); [m.parse(f) for f in fs]; print(len(fs), 'SVGs parse')"

publish:
	@test -n "$(m)" || (echo 'usage: make publish m="what changed"' && exit 1)
	git add -A
	git commit -m "$(m)"
	git push

streak:
	scripts/streak.sh

streak-install:
	mkdir -p $(HOME)/.config/systemd/user
	cp scripts/systemd/profile-streak.service scripts/systemd/profile-streak.timer $(HOME)/.config/systemd/user/
	systemctl --user daemon-reload
	systemctl --user enable --now profile-streak.timer
	systemctl --user list-timers profile-streak.timer
