#!/usr/bin/env python3
"""
Image prep helper for Underground Garden assets.

Wraps the recipes that used to get retyped by hand each session (see README.md
history) into one CLI so future edits are a single command instead of an
improvised Pillow snippet.

Usage:
    python3 scripts/prep_image.py stretch photo.jpg --ratio 4:5
        Crop off any solid-color padding bars, then non-uniformly stretch the
        remaining artwork to fill an exact W:H canvas. Use for flyers/posters
        that need to fill a .media-card tile with no dead space (see the
        "Past Events flyers" section in README.md).

    python3 scripts/prep_image.py trim logo.psd out.png --max-width 640
        Flatten to RGBA, trim to the non-transparent content bounding box,
        and downsize to max-width. Use for logo/wordmark crops like
        assets/img/brand/ug-wordmark-vine.png.

Requires Pillow (`pip install pillow` if not already present).
"""
import argparse
import sys
from pathlib import Path

from PIL import Image

PAD_COLOR = (18, 18, 16)  # matches --black-soft
TOL = 10
FRAC = 0.97


def _row_is_pad(px, w, y):
    xs = range(0, w, max(1, w // 200))
    match = sum(1 for x in xs if all(abs(px[x, y][i] - PAD_COLOR[i]) <= TOL for i in range(3)))
    return match / len(list(xs)) >= FRAC


def _col_is_pad(px, h, x):
    ys = range(0, h, max(1, h // 200))
    match = sum(1 for y in ys if all(abs(px[x, y][i] - PAD_COLOR[i]) <= TOL for i in range(3)))
    return match / len(list(ys)) >= FRAC


def cmd_stretch(args):
    path = Path(args.path)
    im = Image.open(path).convert("RGB")
    w, h = im.size
    px = im.load()

    top = 0
    while top < h and _row_is_pad(px, w, top):
        top += 1
    bot = h - 1
    while bot > top and _row_is_pad(px, w, bot):
        bot -= 1
    left = 0
    while left < w and _col_is_pad(px, h, left):
        left += 1
    right = w - 1
    while right > left and _col_is_pad(px, h, right):
        right -= 1

    pt, pb, pl, pr = top, h - 1 - bot, left, w - 1 - right
    vpad = min(pt, pb) if (pt / h > 0.02 and pb / h > 0.02) else 0
    hpad = min(pl, pr) if (pl / w > 0.02 and pr / w > 0.02) else 0

    if vpad == 0 and hpad == 0:
        print(f"{path.name}: no real padding detected, left untouched")
        return

    box = (hpad, vpad, w - hpad, h - vpad)
    cropped = im.crop(box)
    stretched = cropped.resize((w, h), Image.LANCZOS)
    stretched.save(path, quality=90)
    print(f"{path.name}: cropped padding {box} -> stretched back to {w}x{h}")


def cmd_trim(args):
    src = Path(args.path)
    out = Path(args.out)
    im = Image.open(src).convert("RGBA")
    bbox = im.getbbox()
    if bbox:
        im = im.crop(bbox)
    if args.max_width and im.width > args.max_width:
        new_h = round(im.height * args.max_width / im.width)
        im = im.resize((args.max_width, new_h), Image.LANCZOS)
    out.parent.mkdir(parents=True, exist_ok=True)
    im.save(out, optimize=True)
    print(f"{src.name}: trimmed to {im.size} -> {out}")


def _parse_ratio(s):
    w, h = s.split(":")
    return float(w) / float(h)


def cmd_crop_bars(args):
    """Remove solid-color letterbox bars (e.g. a phone screenshot with black
    top/bottom bars) by cropping them off — unlike `stretch`, this does NOT
    resize back afterward, so use it for photos where losing a few px of
    canvas is fine (cover-fit photos), not flyers that need an exact size."""
    path = Path(args.path)
    im = Image.open(path).convert("RGB")
    w, h = im.size
    px = im.load()
    bar = tuple(args.color) if args.color else px[0, 0]

    def row_is_bar(y):
        xs = range(0, w, max(1, w // 200))
        match = sum(1 for x in xs if all(abs(px[x, y][i] - bar[i]) <= args.tol for i in range(3)))
        return match / len(list(xs)) >= 0.97

    top = 0
    while top < h and row_is_bar(top):
        top += 1
    bot = h - 1
    while bot > top and row_is_bar(bot):
        bot -= 1

    cropped = im.crop((0, top, w, bot + 1))
    cropped.save(path, quality=92)
    print(f"{path.name}: cropped bars, {w}x{h} -> {cropped.size}")


def cmd_poster(args):
    """Grab a frame from a video at a timestamp, crop it to a target aspect
    ratio (center crop), and save as a poster/thumbnail JPG. Requires
    opencv-python-headless (`pip3 install opencv-python-headless`)."""
    import cv2

    cap = cv2.VideoCapture(args.video)
    cap.set(cv2.CAP_PROP_POS_MSEC, args.at * 1000)
    ok, frame = cap.read()
    if not ok:
        print(f"Couldn't read a frame at {args.at}s from {args.video}", file=sys.stderr)
        sys.exit(1)
    cv2.imwrite(args.out, frame)

    im = Image.open(args.out)
    w, h = im.size
    ratio = _parse_ratio(args.ratio)
    target_h = round(w / ratio)
    if target_h <= h:
        top = (h - target_h) // 2
        im = im.crop((0, top, w, top + target_h))
    else:
        target_w = round(h * ratio)
        left = (w - target_w) // 2
        im = im.crop((left, 0, left + target_w, h))
    im.save(args.out, quality=90)
    print(f"{args.video} @ {args.at}s -> {args.out} ({im.size}, {args.ratio})")


def cmd_matte(args):
    """Remove a solid background color, making it transparent — via flood-fill
    from the image edges, NOT a global color threshold. A global threshold
    would also erase any interior pixels that happen to match (e.g. dark
    shadow/reflection detail inside a chrome or black-ink logo); flood-fill
    only removes background that's actually connected to the border, so
    interior detail survives. Use for a logo exported on a solid mat instead
    of a transparent canvas."""
    from collections import deque

    src = Path(args.path)
    out = Path(args.out)
    im = Image.open(src).convert("RGBA")
    w, h = im.size
    px = im.load()
    bg = tuple(args.color) if args.color else px[0, 0][:3]
    tol = args.tol

    def matches(p):
        return all(abs(p[i] - bg[i]) <= tol for i in range(3))

    seen = bytearray(w * h)
    q = deque()
    for x in range(w):
        for y in (0, h - 1):
            if not seen[y * w + x] and matches(px[x, y]):
                seen[y * w + x] = 1
                q.append((x, y))
    for y in range(h):
        for x in (0, w - 1):
            if not seen[y * w + x] and matches(px[x, y]):
                seen[y * w + x] = 1
                q.append((x, y))

    while q:
        x, y = q.popleft()
        r, g, b, a = px[x, y]
        px[x, y] = (r, g, b, 0)
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < w and 0 <= ny < h and not seen[ny * w + nx] and matches(px[nx, ny]):
                seen[ny * w + nx] = 1
                q.append((nx, ny))

    bbox = im.getbbox()
    if bbox:
        im = im.crop(bbox)
    if args.max_width and im.width > args.max_width:
        new_h = round(im.height * args.max_width / im.width)
        im = im.resize((args.max_width, new_h), Image.LANCZOS)
    out.parent.mkdir(parents=True, exist_ok=True)
    im.save(out, optimize=True)
    print(f"{src.name}: matted bg {bg} (tol {tol}) + trimmed -> {im.size} -> {out}")


def cmd_compress(args):
    """Recompress a JPG in place at a lower quality to shrink file size —
    use on any photo that's grown past ~500KB (check with `du -sh`)."""
    path = Path(args.path)
    before = path.stat().st_size
    im = Image.open(path)
    im.save(path, quality=args.quality, optimize=True)
    after = path.stat().st_size
    print(f"{path.name}: {before//1024}KB -> {after//1024}KB (quality={args.quality})")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    p_stretch = sub.add_parser("stretch", help="de-pad + stretch a flyer to fill its canvas")
    p_stretch.add_argument("path", help="image file to process in place")
    p_stretch.set_defaults(func=cmd_stretch)

    p_trim = sub.add_parser("trim", help="trim transparent margins and downsize a logo/PSD export")
    p_trim.add_argument("path", help="source image (PSD, PNG, etc.)")
    p_trim.add_argument("out", help="output PNG path")
    p_trim.add_argument("--max-width", type=int, default=640, help="downsize if wider than this (default 640)")
    p_trim.set_defaults(func=cmd_trim)

    p_crop = sub.add_parser("crop-bars", help="crop off solid-color letterbox bars from a photo")
    p_crop.add_argument("path", help="image file to process in place")
    p_crop.add_argument("--color", type=int, nargs=3, metavar=("R", "G", "B"), help="bar color (default: sample top-left pixel)")
    p_crop.add_argument("--tol", type=int, default=10, help="color match tolerance (default 10)")
    p_crop.set_defaults(func=cmd_crop_bars)

    p_poster = sub.add_parser("poster", help="grab a video frame as a cropped poster/thumbnail image")
    p_poster.add_argument("video", help="source video file")
    p_poster.add_argument("out", help="output JPG path")
    p_poster.add_argument("--at", type=float, default=3.0, help="timestamp in seconds (default 3)")
    p_poster.add_argument("--ratio", default="16:9", help="target aspect ratio, e.g. 16:9 or 4:5 (default 16:9)")
    p_poster.set_defaults(func=cmd_poster)

    p_matte = sub.add_parser("matte", help="flood-fill a solid background to transparent, then trim")
    p_matte.add_argument("path", help="source image (logo on a solid-color mat)")
    p_matte.add_argument("out", help="output PNG path")
    p_matte.add_argument("--color", type=int, nargs=3, metavar=("R", "G", "B"), help="background color (default: sample top-left pixel)")
    p_matte.add_argument("--tol", type=int, default=12, help="color match tolerance (default 12)")
    p_matte.add_argument("--max-width", type=int, default=640, help="downsize if wider than this (default 640)")
    p_matte.set_defaults(func=cmd_matte)

    p_compress = sub.add_parser("compress", help="recompress a JPG in place to shrink file size")
    p_compress.add_argument("path", help="JPG file to recompress in place")
    p_compress.add_argument("--quality", type=int, default=82, help="JPEG quality 1-95 (default 82)")
    p_compress.set_defaults(func=cmd_compress)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    sys.exit(main())
