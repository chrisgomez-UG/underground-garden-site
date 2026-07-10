#!/usr/bin/env python3
"""
Video compression helper for Underground Garden assets.

No system ffmpeg is available in this environment, so this uses the
imageio-ffmpeg package instead, which bundles a static ffmpeg binary —
`pip3 install imageio-ffmpeg` once, then this just works.

Usage:
    python3 scripts/prep_video.py compress input.mp4 output.mp4 --width 640 --crf 30
        Re-encode (H.264/AAC) at a target width, keeping aspect ratio. CRF
        18-23 = high quality/larger file, 28-32 = smaller/lower quality.
        30 at 640px width is a good default for a background/recap clip
        that isn't the main hero content.
"""
import argparse
import subprocess
import sys
from pathlib import Path


def cmd_compress(args):
    import imageio_ffmpeg
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()

    src = Path(args.input)
    out = Path(args.output)
    before = src.stat().st_size

    cmd = [
        ffmpeg, "-i", str(src),
        "-vcodec", "libx264", "-crf", str(args.crf), "-preset", "slow",
        "-vf", f"scale={args.width}:-2",
        "-movflags", "+faststart",
        "-acodec", "aac", "-b:a", "96k",
        str(out), "-y",
    ]
    subprocess.run(cmd, check=True, capture_output=True)

    after = out.stat().st_size
    print(f"{src.name}: {before // 1024 // 1024}MB -> {out.name}: {after // 1024 // 1024}MB "
          f"(width={args.width}, crf={args.crf})")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    p_compress = sub.add_parser("compress", help="re-encode a video at a smaller width/quality")
    p_compress.add_argument("input", help="source video file")
    p_compress.add_argument("output", help="output video file")
    p_compress.add_argument("--width", type=int, default=640, help="target width in px, height auto (default 640)")
    p_compress.add_argument("--crf", type=int, default=30, help="quality 18-32, higher=smaller/lower quality (default 30)")
    p_compress.set_defaults(func=cmd_compress)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    sys.exit(main())
