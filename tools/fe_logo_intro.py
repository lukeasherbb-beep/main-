"""FE logo intro (Full Mount-style ident), standalone clip.

Usage: python3 fe_logo_intro.py OUT.mp4 [SECONDS]
Dark scratched backdrop, gold plus-sign clusters, grey octagon outline, light paper corner,
the FE logo punched in at center with a shine sweep, and a small logo bug bottom-right.
"""
import math
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

W, H, FPS = 1920, 1080, 30
GOLD = (196, 142, 22)
ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")
rng = np.random.default_rng(11)


def ease_out_back(t, s=1.7):
    t -= 1
    return t * t * ((s + 1) * t + s) + 1


def keyed_logo(size):
    """Logo with its black background turned transparent (alpha from brightness)."""
    im = Image.open(os.path.join(ASSETS, "logo_square.png")).convert("RGB")
    bbox = Image.fromarray((np.asarray(im).max(axis=2) > 30).astype(np.uint8) * 255).getbbox()
    im = im.crop(bbox)
    im.thumbnail((size, size), Image.LANCZOS)
    a = np.asarray(im, dtype=np.float32)
    alpha = np.clip((a.max(axis=2) - 14) * 4.0, 0, 255).astype(np.uint8)
    return Image.fromarray(np.dstack([a.astype(np.uint8), alpha]), "RGBA")


def backdrop():
    """Near-black grungy board: noise, scratches, faint panel lines, vignette."""
    base = np.full((H, W), 22.0, dtype=np.float32)
    n = Image.fromarray((rng.random((H // 4, W // 4)) * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC)
    base += (np.asarray(n, dtype=np.float32) / 255 - 0.5) * 14
    grain = rng.normal(0, 4, (H, W)).astype(np.float32)
    lines = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(lines)
    for _ in range(260):  # scratches
        x, y = rng.uniform(0, W), rng.uniform(0, H)
        ang = rng.normal(0, 0.25) + (math.pi / 2 if rng.random() < 0.3 else 0)
        ln = rng.uniform(40, 420)
        d.line([(x, y), (x + ln * math.cos(ang), y + ln * math.sin(ang))], fill=int(rng.uniform(10, 40)), width=1)
    for _ in range(14):  # faint panel/frame lines like a worn print
        x0, y0 = rng.uniform(0, W), rng.uniform(0, H)
        d.rectangle([x0, y0, x0 + rng.uniform(200, 900), y0 + rng.uniform(80, 400)], outline=14, width=2)
    base += np.asarray(lines.filter(ImageFilter.GaussianBlur(0.6)), dtype=np.float32)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    vig = 1 - 0.55 * (((xx - W / 2) / (W * 0.7)) ** 2 + ((yy - H / 2) / (H * 0.75)) ** 2)
    rgb = np.clip((base + grain) * vig, 0, 255)[..., None] * np.array([1.0, 0.99, 0.97])
    return Image.fromarray(rgb.astype(np.uint8))


def paper_corner():
    """Light grey torn-paper shape cutting into the bottom-right corner."""
    m = Image.new("L", (W, H), 0)
    pts = [(1500, 1080), (1680, 700), (1920, 600), (1920, 1080)]
    ImageDraw.Draw(m).polygon(pts, fill=255)
    tex = Image.fromarray((200 + rng.random((H, W)) * 30).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2))
    layer = Image.merge("RGBA", (tex, tex, tex.point(lambda v: v - 4), m))
    return layer


def plus_cluster(spec):
    """spec: list of (x, y). Returns positions with a random pop-in delay each."""
    return [(x, y, rng.uniform(0.15, 0.9), rng.uniform(0, 1)) for x, y in spec]


def grid(x0, y0, cols, rows, keep, step=44):
    pts = []
    for r in range(rows):
        for c in range(cols):
            if rng.random() < keep(c, r, cols, rows):
                pts.append((x0 + c * step, y0 + r * step))
    return pts


def octagon(d, cx, cy, r, rot, fill, width):
    pts = [(cx + r * math.cos(rot + k * math.pi / 4 + math.pi / 8),
            cy + r * math.sin(rot + k * math.pi / 4 + math.pi / 8)) for k in range(8)]
    d.line(pts + [pts[0]], fill=fill, width=width, joint="curve")


def main():
    out = sys.argv[1]
    secs = float(sys.argv[2]) if len(sys.argv) > 2 else 4.0
    frames = int(secs * FPS)
    bg = backdrop()
    corner = paper_corner()
    logo = keyed_logo(860)
    bug = keyed_logo(120)
    la = np.asarray(logo)[..., 3].astype(np.float32) / 255
    tl = plus_cluster(grid(230, 70, 11, 5, lambda c, r, C, R: 0.85 - 0.16 * r - 0.04 * c))
    br = plus_cluster(grid(1500, 500, 9, 9, lambda c, r, C, R: 0.15 + 0.09 * (c + r)))
    proc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                             "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "16",
                             "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    for f in range(frames):
        t = f / FPS
        fr = bg.copy()
        # paper corner slides in
        k = min(1, max(0, (t - 0.1) / 0.4))
        fr.paste(corner, (int(260 * (1 - ease_out_back(k, 1.2))), 0), corner)
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(ov)
        # octagon outline, top right: draws in then rotates slowly
        ok = min(1, t / 0.5)
        octagon(d, 1600, 200, 150 * ease_out_back(ok, 1.4) if ok > 0 else 0, 0.35 + t * 0.12, (70, 70, 74, 255), 18)
        # plus clusters: each pops in on its own delay, then gently flickers
        for pts in (tl, br):
            for x, y, delay, ph in pts:
                p = min(1, max(0, (t - delay) / 0.18))
                if p <= 0:
                    continue
                a = int(255 * p * (0.75 + 0.25 * math.sin(2 * math.pi * (t * 0.8 + ph))))
                s = 9 * p
                over_paper = x > 1700 and y > 1500 - x * 0.45
                col = (150, 104, 12, a) if over_paper else GOLD + (a,)
                d.line([(x - s, y), (x + s, y)], fill=col, width=5)
                d.line([(x, y - s), (x, y + s)], fill=col, width=5)
        fr.paste(ov, (0, 0), ov)
        # logo: punch in with overshoot, slight shake on impact, then a slow push
        lk = min(1, max(0, (t - 0.2) / 0.45))
        if lk > 0:
            sc = (0.55 + 0.45 * ease_out_back(lk, 2.2)) * (1 + 0.012 * max(0, t - 0.65))
            lw = max(2, int(logo.width * sc))
            lh = max(2, int(logo.height * sc))
            im = logo.resize((lw, lh), Image.LANCZOS)
            sweep = (t - 1.1) / 0.7  # shine sweep across the logo
            if 0 < sweep < 1:
                arr = np.asarray(im).astype(np.float32)
                xs = np.arange(lw)[None, :] + np.arange(lh)[:, None] * 0.5
                band = np.exp(-((xs - (-0.3 + 1.6 * sweep) * lw) / (lw * 0.06)) ** 2)
                arr[..., :3] = np.clip(arr[..., :3] + 150 * band[..., None], 0, 255)
                im = Image.fromarray(arr.astype(np.uint8), "RGBA")
            if lk < 1:
                a = np.asarray(im).copy()
                a[..., 3] = (a[..., 3] * min(1, lk * 2.5)).astype(np.uint8)
                im = Image.fromarray(a, "RGBA")
            shake = 6 * math.exp(-(t - 0.65) * 14) * math.sin(t * 90) if t > 0.65 else 0
            fr.paste(im, (int((W - lw) / 2 + shake), int((H - lh) / 2 - 20)), im)
        # impact flash
        if 0.6 < t < 0.85:
            fl = 1 - (t - 0.6) / 0.25
            fr = Image.blend(fr, Image.new("RGB", (W, H), (255, 225, 150)), 0.22 * fl)
        # small logo bug, bottom right
        bk = min(1, max(0, (t - 0.9) / 0.3))
        if bk > 0:
            b = bug.copy()
            arr = np.asarray(b).copy()
            arr[..., 3] = (arr[..., 3] * bk).astype(np.uint8)
            b = Image.fromarray(arr, "RGBA")
            fr.paste(b, (W - b.width - 40, H - b.height - 40), b)
        # fade out at the end
        if t > secs - 0.35:
            fr = Image.blend(fr, Image.new("RGB", (W, H)), (t - (secs - 0.35)) / 0.35)
        proc.stdin.write(fr.tobytes())
    proc.stdin.close()
    proc.wait()
    print("wrote", out)


if __name__ == "__main__":
    main()
