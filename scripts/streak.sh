#!/usr/bin/env bash
# Keep the contribution streak: if GitHub shows no contribution today, refresh the profile art and push it.
set -euo pipefail
cd "$(dirname "$0")/.."

today=$(date +%F)
count=$(python3 -c "import sys; sys.path.insert(0, 'scripts'); from build_art import fetch_days; print({d['date']: d['count'] for d in fetch_days()}.get('$today', 0))")
if [ "$count" -gt 0 ] && [ "${1:-}" != "--force" ]; then
  echo "$today: already $count contribution(s), nothing to do"
  exit 0
fi

git pull --rebase --autostash --quiet
make --no-print-directory art >/dev/null
git add -- '*.svg' projects data   # generated files only, never half-done README edits
git commit --quiet --allow-empty -m "chore: refresh profile art"
git push --quiet
echo "$today: pushed $(git rev-parse --short HEAD)"
