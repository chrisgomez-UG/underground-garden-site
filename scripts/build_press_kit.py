#!/usr/bin/env python3
"""
Rebuilds assets/press/ug-press-kit.zip from the current brand assets.

Run this after swapping any of the source files below (e.g. a new wordmark
or a refreshed og-image) so the downloadable press kit on the Contact page
stays in sync.

Usage:
    python3 scripts/build_press_kit.py
"""
import zipfile
from pathlib import Path

ROOT = Path(__file__).parent.parent
BRAND = ROOT / "assets/img/brand"
OUT = ROOT / "assets/press/ug-press-kit.zip"

BOILERPLATE = """UNDERGROUND GARDEN — PRESS / BRAND BOILERPLATE

About
-----
Underground Garden is South Florida's home for underground electronic
music — pool parties, beach parties, warehouse nights, and donation events
across Miami and Fort Lauderdale. Built by the community, for the community.
Every event is a chapter on the road to Subtropics, a sunset-into-night
flagship festival launching 2028 at Virginia Key Beach, Miami.

Contact
-------
Booking, sponsorship & press: info@ugevents.com

Brand colors
------------
Black       #0a0a0a
Black Soft  #121210
Forest      #1f3d2b
Forest Lt   #3c6a49
Bone        #f3ead9
Amber       #e0a237

Typography
----------
Display:   Anton
Secondary: Cormorant Garamond (italic)
Utility:   Space Mono

Assets included in this kit
----------------------------
ug-mark.png   — circular "U" brand mark, transparent background
wordmark.png  — full "Underground Garden" wordmark, transparent background
og-image.jpg  — branded 1200x630 social/share card
"""


def build():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(BRAND / "ug-mark.png", "ug-mark.png")
        z.write(BRAND / "wordmark.png", "wordmark.png")
        z.write(BRAND / "og-image.jpg", "og-image.jpg")
        z.writestr("brand-boilerplate.txt", BOILERPLATE)
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    build()
