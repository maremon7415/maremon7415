"""Wrap GitHub's rendered README HTML in a dark GitHub-like page: preview.py body.html out.html"""
import sys

body = open(sys.argv[1]).read()
open(sys.argv[2], "w").write(f"""<!doctype html><meta charset="utf-8"><title>Profile preview</title>
<style>
body{{background:#0d1117;color:#e6edf3;font:16px -apple-system,Segoe UI,Helvetica,Arial,sans-serif;margin:0}}
main{{max-width:846px;margin:32px auto;padding:0 16px}}
a{{color:#4493f8}} code{{background:#2f353d;padding:.2em .4em;border-radius:6px;font-size:85%}}
table{{border-collapse:collapse;margin:0 auto}} td{{border:1px solid #3d444d;padding:6px 13px}}
img{{max-width:100%}}
</style><main>{body}</main>
""")
