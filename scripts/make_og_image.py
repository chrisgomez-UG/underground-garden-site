#!/usr/bin/env python3
"""Rebuild assets/img/brand/og-image.jpg (1200x630) from a real event photo
with the bone wordmark overlaid — replaces the generic gradient card."""
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

ROOT = "/Users/christophergomez/Claude/Projects/Website"
BONE = (243, 234, 217)

# 1. Photo: DJ overlooking packed warehouse crowd, cropped to 1.905:1
photo = Image.open(f"{ROOT}/assets/img/warehouse-skypbr.jpg").convert("RGB")
w, h = photo.size                       # 1400x934
target_h = round(w / (1200 / 630))      # 735
top = (h - target_h) // 3               # bias crop upward to keep the DJ + rig
photo = photo.crop((0, top, w, top + target_h)).resize((1200, 630), Image.LANCZOS)

# 2. Darken for wordmark legibility: global dim + soft dark blob behind the mark
photo = ImageEnhance.Brightness(photo).enhance(0.8)
blob = Image.new("L", (1200, 630), 0)
bd = ImageDraw.Draw(blob)
bd.ellipse([160, 60, 1040, 480], fill=110)
blob = blob.filter(ImageFilter.GaussianBlur(80))
black = Image.new("RGB", (1200, 630), (10, 10, 10))
photo = Image.composite(black, photo, blob)

# 3. Wordmark: black-ink-on-transparent source, recolored bone via its alpha
mark = Image.open(f"{ROOT}/assets/img/brand/wordmark.png").convert("RGBA")
alpha = mark.split()[3]
mark_w = 440
mark_h = round(mark.height * mark_w / mark.width)
alpha = alpha.resize((mark_w, mark_h), Image.LANCZOS)
bone_mark = Image.new("RGBA", (mark_w, mark_h), BONE + (0,))
bone_mark.putalpha(alpha)

x = (1200 - mark_w) // 2
y = (630 - mark_h) // 2 - 25
canvas = photo.convert("RGBA")
canvas.alpha_composite(bone_mark, (x, y))

out = canvas.convert("RGB")
out.save(f"{ROOT}/assets/img/brand/og-image.jpg", quality=88, optimize=True)
print("wrote og-image.jpg", out.size, "mark", (mark_w, mark_h), "at", (x, y))
