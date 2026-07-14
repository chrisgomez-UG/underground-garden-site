#!/usr/bin/env python3
"""
Static site builder for Underground Garden.

Assembles page sources (pages/*.html) with the shared layout (partials/layout.html)
into the final static HTML files in dist/ — a clean, self-contained folder that's
the actual deploy artifact (this is what Netlify publishes; nothing outside dist/
is meant to be public — see the README's "Deploying" section). Edit nav/footer/
social links ONCE in partials/layout.html and every page picks it up on the next
build. Edit page content in pages/*.html.

Usage:
    python3 build.py            build once into dist/
    python3 build.py --watch    rebuild automatically whenever a source file changes
    python3 build.py --serve    watch + serve dist/ on http://localhost:8743 in one process
                                (add a port number to use a different one, e.g. --serve 8800)
"""
import hashlib
import http.server
import os
import re
import shutil
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).parent
BUILD_FILE = Path(__file__).resolve()
PAGES_DIR = ROOT / "pages"
PARTIALS_DIR = ROOT / "partials"
LAYOUT_FILE = PARTIALS_DIR / "layout.html"
ASSETS_DIR = ROOT / "assets"
CSS_FILE = ASSETS_DIR / "css/style.css"
JS_FILE = ASSETS_DIR / "js/main.js"
DIST_DIR = ROOT / "dist"


def file_hash(path):
    """Short content hash used as a cache-busting query param — changes
    automatically whenever the file's content changes, so there's nothing
    to remember to bump by hand."""
    return hashlib.sha1(path.read_bytes()).hexdigest()[:8]

# Set this once the site has a real domain (e.g. "https://undergroundgarden.com",
# no trailing slash) and rebuild — it feeds canonical links and Open Graph/Twitter
# card URLs. Left blank, those tags still render (as relative paths), but social
# previews and search engines want absolute URLs to work correctly.
SITE_URL = "https://ugevents.com"

# (label, href, key) — single source of truth for primary navigation.
# `key` must match a page's `active:` front-matter value.
NAV_ITEMS = [
    ("Home", "index.html", "home"),
    ("Events", "events.html", "events"),
    ("Subtropics", "subtropics.html", "subtropics"),
    ("About", "about.html", "about"),
    ("Gallery", "gallery.html", "gallery"),
    ("Merch", "merch.html", "merch"),
    ("FAQ", "safety.html", "safety"),
    ("Contact", "contact.html", "contact"),
]

SECTION_MARKERS = {"head", "body", "scripts"}


def render_nav_links(active):
    lines = []
    for label, href, key in NAV_ITEMS:
        current = ' aria-current="page"' if key == active else ""
        lines.append(f'      <a href="{href}"{current}>{label}</a>')
    return "\n".join(lines)


def render_mobile_menu_links(active):
    lines = []
    for label, href, key in NAV_ITEMS:
        current = ' aria-current="page"' if key == active else ""
        lines.append(f'    <li><a href="{href}"{current}>{label}</a></li>')
    return "\n".join(lines)


def parse_page(path):
    """Split a pages/*.html source file into front-matter + head/body/scripts sections."""
    text = path.read_text()

    fm_match = re.match(r"^---\n(.*?\n)---\n", text, re.DOTALL)
    if not fm_match:
        raise ValueError(f"{path}: missing '---' front-matter block at top of file")
    front_matter = {}
    for line in fm_match.group(1).splitlines():
        if not line.strip():
            continue
        key, _, value = line.partition(":")
        front_matter[key.strip()] = value.strip()

    rest = text[fm_match.end():]

    sections = {"head": "", "body": "", "scripts": ""}
    current = None
    buf = []
    for line in rest.splitlines():
        marker = re.match(r"^<!--\s*(head|body|scripts)\s*-->\s*$", line.strip())
        if marker:
            if current:
                sections[current] = "\n".join(buf).strip("\n")
            current = marker.group(1)
            buf = []
        else:
            buf.append(line)
    if current:
        sections[current] = "\n".join(buf).strip("\n")

    if not sections["body"]:
        raise ValueError(f"{path}: no '<!-- body -->' section found")

    required = {"title", "description", "active", "nav_cta_label", "nav_cta_href"}
    missing = required - front_matter.keys()
    if missing:
        raise ValueError(f"{path}: front-matter missing keys: {', '.join(sorted(missing))}")

    return front_matter, sections


def build_page(path, layout):
    front_matter, sections = parse_page(path)
    active = front_matter["active"]

    extra_head = sections["head"]
    extra_head = (extra_head + "\n") if extra_head else ""
    extra_scripts = sections["scripts"]
    extra_scripts = (extra_scripts + "\n") if extra_scripts else ""

    html = layout
    html = html.replace("{{TITLE}}", front_matter["title"])
    html = html.replace("{{DESCRIPTION}}", front_matter["description"])
    html = html.replace("{{EXTRA_HEAD}}", extra_head)
    html = html.replace("{{NAV_LINKS}}", render_nav_links(active))
    html = html.replace("{{NAV_CTA_HREF}}", front_matter["nav_cta_href"])
    html = html.replace("{{NAV_CTA_LABEL}}", front_matter["nav_cta_label"])
    html = html.replace("{{MOBILE_MENU_LINKS}}", render_mobile_menu_links(active))
    html = html.replace("{{BODY}}", sections["body"])
    html = html.replace("{{EXTRA_SCRIPTS}}", extra_scripts)
    html = html.replace("{{CSS_VER}}", file_hash(CSS_FILE))
    html = html.replace("{{JS_VER}}", file_hash(JS_FILE))
    html = html.replace("{{SITE_URL}}", SITE_URL)
    # The homepage's canonical URL is the bare domain root ("/"), not
    # "/index.html" — the live site serves it at both, and search engines
    # treat those as two different pages unless the canonical/sitemap
    # consistently point at one. netlify.toml also 301s /index.html -> /.
    html = html.replace("{{PAGE_FILE}}", "" if path.name == "index.html" else path.name)

    out_path = DIST_DIR / path.name
    out_path.write_text(html)
    return out_path


def build_all():
    DIST_DIR.mkdir(parents=True, exist_ok=True)

    layout = LAYOUT_FILE.read_text()
    page_files = sorted(PAGES_DIR.glob("*.html"))
    if not page_files:
        print(f"No page sources found in {PAGES_DIR}", file=sys.stderr)
        return
    for page_path in page_files:
        try:
            out_path = build_page(page_path, layout)
        except ValueError as e:
            print(f"Build error — {e}", file=sys.stderr)
            sys.exit(1)
        print(f"  {page_path.relative_to(ROOT)} -> {out_path.relative_to(ROOT)}")
    print(f"Built {len(page_files)} page(s).")

    write_robots_and_sitemap(page_files)

    shutil.copytree(ASSETS_DIR, DIST_DIR / "assets", dirs_exist_ok=True)
    print("  copied assets/ -> dist/assets/")


def write_robots_and_sitemap(page_files):
    base = SITE_URL or ""
    # index.html is listed as the bare root URL, matching its canonical tag.
    urls = [f"{base}/" if p.name == "index.html" else f"{base}/{p.name}"
            for p in page_files if p.name != "404.html"]

    sitemap = ['<?xml version="1.0" encoding="UTF-8"?>',
               '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for url in urls:
        sitemap.append(f"  <url><loc>{url}</loc></url>")
    sitemap.append("</urlset>\n")
    (DIST_DIR / "sitemap.xml").write_text("\n".join(sitemap))

    sitemap_line = f"Sitemap: {base}/sitemap.xml" if base else "# Set SITE_URL in build.py to enable the Sitemap: line here."
    robots = f"User-agent: *\nAllow: /\n\n{sitemap_line}\n"
    (DIST_DIR / "robots.txt").write_text(robots)
    print("  wrote sitemap.xml and robots.txt")


def watched_files():
    """Everything a --serve/--watch rebuild should react to: page/layout/CSS/JS
    source, plus every file under assets/ (images, video, press kit, etc.) since
    those now get copied into dist/assets/ on each build too."""
    return [LAYOUT_FILE, *PAGES_DIR.glob("*.html"), *(p for p in ASSETS_DIR.rglob("*") if p.is_file())]


def watch_loop(stop_event=None):
    build_mtime = BUILD_FILE.stat().st_mtime
    mtimes = {p: p.stat().st_mtime for p in watched_files()}
    build_all()
    while stop_event is None or not stop_event.is_set():
        time.sleep(1)

        # build.py itself changed (NAV_ITEMS, SITE_URL, new page added, etc.) —
        # restart the whole process so the new logic actually takes effect,
        # instead of silently continuing to run stale code.
        if BUILD_FILE.stat().st_mtime != build_mtime:
            print("\nbuild.py changed — restarting server to pick it up...")
            os.execv(sys.executable, [sys.executable] + sys.argv)

        changed = False
        current = watched_files()
        for p in current:
            mtime = p.stat().st_mtime
            if mtime != mtimes.get(p):
                mtimes[p] = mtime
                changed = True
        if changed:
            print("\nChange detected, rebuilding...")
            build_all()


def watch():
    print("Watching for changes (Ctrl+C to stop)...")
    try:
        watch_loop()
    except KeyboardInterrupt:
        print("\nStopped.")


def serve(port=8743):
    stop_event = threading.Event()
    watcher = threading.Thread(target=watch_loop, args=(stop_event,), daemon=True)
    watcher.start()

    handler = lambda *args, **kwargs: http.server.SimpleHTTPRequestHandler(
        *args, directory=str(DIST_DIR), **kwargs
    )
    httpd = http.server.ThreadingHTTPServer(("", port), handler)
    print(f"Watching for changes and serving http://localhost:{port} (Ctrl+C to stop)...")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        stop_event.set()
        httpd.server_close()


if __name__ == "__main__":
    if "--serve" in sys.argv:
        idx = sys.argv.index("--serve")
        port_arg = sys.argv[idx + 1] if len(sys.argv) > idx + 1 and sys.argv[idx + 1].isdigit() else None
        serve(int(port_arg)) if port_arg else serve()
    elif "--watch" in sys.argv:
        watch()
    else:
        build_all()
