#!/usr/bin/env python3
"""
Site health check for Underground Garden.

Rebuilds the site, then verifies every internal link, image, and asset
reference across all pages actually resolves — the exact manual curl+grep
dance that used to get retyped by hand for every "review the whole site"
request. Run this instead of re-deriving it.

Requires the site to be served locally (e.g. `python3 build.py --serve` in
another terminal, or via .claude/launch.json's "underground-garden" config).

Usage:
    python3 scripts/check_site.py [--port 8743]
"""
import argparse
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parent.parent
DIST = ROOT / "dist"


def check(port):
    subprocess.run([sys.executable, str(ROOT / "build.py")], check=True, cwd=ROOT)

    html_files = sorted(DIST.glob("*.html"))
    refs = set()
    for f in html_files:
        text = f.read_text()
        for attr in ("href", "src"):
            for m in re.findall(rf'{attr}="([^"]+)"', text):
                if m.startswith("http") or m.startswith("//") or m.startswith("mailto:") or m.startswith("tel:") or m.startswith("#"):
                    continue
                refs.add(m.split("#")[0].split("?")[0])

    print(f"Checking {len(html_files)} pages, {len(refs)} unique local references...")
    bad = []
    for ref in sorted(refs):
        url = f"http://localhost:{port}/{ref.lstrip('/')}"
        try:
            req = urllib.request.Request(url, method="HEAD")
            code = urllib.request.urlopen(req, timeout=5).getcode()
            if code >= 400:
                bad.append((ref, code))
        except Exception as e:
            bad.append((ref, str(e)))

    if bad:
        print(f"\n{len(bad)} BROKEN reference(s):")
        for ref, err in bad:
            print(f"  {ref}  ->  {err}")
        sys.exit(1)
    else:
        print("All references resolve cleanly. No broken links or assets.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--port", type=int, default=8743)
    args = parser.parse_args()
    check(args.port)
