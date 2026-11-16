"""Render the Fight Era animated backgrounds (seamless loops).

Usage: python3 fe_bg.py OUT_DIR
Writes bg_gold.mp4 and bg_dark.mp4 (1920x1080, 30 fps, 12 s loops).

Look: crumpled dark paper, a diagonal dry-brush paint band in brand gold whose edges
crawl and which sways, a light sheen sweeping across it, plus moving accents
(chevron stack, rotating octagon, flickering plus-grid, sliding hash bars, blinking X marks).
"""
import math
import subprocess
import sys

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

W, H, FPS, SECONDS = 1920, 1080, 30, 12
N = FPS * SECONDS
GOLD = np.array([196, 142, 22], dtype=np.float32)
rng = np.random.default_rng(7)


def noise(w, h, blur):
    im = Image.fromarray((rng.random((h, w)) * 255).astype(np.uint8))
    return im.filter(ImageFilter.GaussianBlur(blur))


def paper():
    """Crumpled-paper luminance map, 0..1, tileable enough for a static layer."""
    big = noise(96, 54, 2).resize((W, H), Image.BICUBIC)
    mid = noise(480, 270, 3).resize((W, H), Image.BICUBIC)
    creases = ImageChops.add(big.filter(ImageFilter.EMBOSS), mid.filter(ImageFilter.EMBOSS), 2.0)
    a = np.asarray(creases, dtype=np.float32) / 255.0
    a = (a - a.mean()) / (a.std() + 1e-6)
    return np.clip(0.5 + 0.22 * a, 0, 1)


def streak_noise():
    """Noise stretched along the band direction: gives dry-brush streaks. Periodic in v."""
    base = rng.random((300, 64)).astype(np.float32)  # (u, v) coarse
    im = Image.fromarray((base * 255).astype(np.uint8)).resize((2048, 300), Image.BICUBIC)
    a = np.asarray(im, dtype=np.float32) / 255.0
    return np.concatenate([a, a], axis=1)  # tile so rolls wrap cleanly


def octagon(d, cx, cy, r, rot, color, width):
    pts = [(cx + r * math.cos(rot + k * math.pi / 4), cy + r * math.sin(rot + k * math.pi / 4)) for k in range(8)]
    d.line(pts + [pts[0]], fill=color, width=width, joint="curve")


def accents(n, accent, grey):
    """Animated decorations for frame n, as an RGBA image."""
    ph = n / N
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    # chevron stack, left: a highlight travels downward (3 passes per loop)
    for k in range(6):
        y = 150 + k * 120
        lit = max(0.0, 1 - abs(((ph * 3 * 6) % 6) - k) / 1.3)
        col = tuple(int(g + (a - g) * lit) for g, a in zip(grey, accent)) + (int(110 + 145 * lit),)
        d.polygon([(70, y), (150, y + 55), (230, y), (230, y + 45), (150, y + 100), (70, y + 45)], fill=col)
    # octagon outlines, top right: counter-rotating, one turn per loop
    octagon(d, 1690, 250, 150, 2 * math.pi * ph, grey + (200,), 12)
    octagon(d, 1690, 250, 105, -2 * math.pi * ph * 2, accent + (170,), 5)
    # plus grid, bottom right: each plus flickers on its own phase
    r2 = np.random.default_rng(3)
    for gx in range(9):
        for gy in range(6):
            p0, cyc = r2.random(), r2.integers(2, 6)
            a = 0.5 + 0.5 * math.sin(2 * math.pi * (ph * cyc + p0))
            if a < 0.35:
                continue
            x, y = 1480 + gx * 44, 800 + gy * 44
            col = accent + (int(255 * a),)
            d.line([(x - 9, y), (x + 9, y)], fill=col, width=4)
            d.line([(x, y - 9), (x, y + 9)], fill=col, width=4)
    # hash bars, right edge: slide upward continuously (4 steps per loop)
    off = (ph * 4 * 46) % 46
    for k in range(-1, 7):
        y = 480 + k * 46 - off
        alpha = int(190 * max(0.0, min(1.0, (y - 440) / 40, (760 - y) / 40)))
        if alpha > 0:
            d.polygon([(1800, y + 22), (1880, y), (1880, y + 20), (1800, y + 42)], fill=grey + (alpha,))
    # X marks, left: blink in sequence
    for k, (x, y) in enumerate([(330, 820), (330, 880), (330, 940), (390, 880)]):
        a = 0.5 + 0.5 * math.sin(2 * math.pi * (ph * 6 - k / 4))
        col = grey + (int(60 + 180 * a),)
        d.line([(x - 13, y - 13), (x + 13, y + 13)], fill=col, width=7)
        d.line([(x - 13, y + 13), (x + 13, y - 13)], fill=col, width=7)
    # thin scan line sweeping top to bottom twice per loop
    y = int((ph * 2 % 1) * H)
    d.line([(0, y), (W, y)], fill=accent + (38,), width=2)
    return im


def render(out, band_rgb, accent, grey, band_gain):
    tex = paper()
    st = streak_noise()
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    ang = math.radians(-20)  # band leans like "/"
    ca, sa = math.cos(ang), math.sin(ang)
    u0 = (xx - W / 2) * ca + (yy - H / 2) * sa  # across the band
    v = -(xx - W / 2) * sa + (yy - H / 2) * ca  # along the band
    vi = ((v + 1200) / 2400 * 1024).astype(np.int32) % 1024
    base = (18 + 44 * tex)[..., None] * np.array([1.0, 1.0, 1.04], dtype=np.float32)
    grad = 0.82 + 0.3 * (v / 1200)  # lighter toward the bottom
    cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", out]
    ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for n in range(N):
        ph = n / N
        sway = 46 * math.sin(2 * math.pi * ph)
        half = 520 + 26 * math.sin(2 * math.pi * ph * 2)
        u = u0 - sway
        shift = int(ph * 1024)  # edge texture crawls along the band, one wrap per loop
        ui = np.clip(((np.abs(u) - half + 190) / 380 * 300), 0, 299).astype(np.int32)
        edge = st[ui, (vi + np.where(u > 0, shift, -shift)) % 1024]
        dist = np.abs(u) - half  # <0 inside
        mask = np.clip((-(dist) + 150 * (edge - 0.5)) / 14, 0, 1)
        mask *= np.where(dist > -170, np.clip((edge - 0.18) * 4, 0, 1), 1)  # dry gaps near the edges
        sheen_pos = -1300 + 2600 * ((ph * 2) % 1)  # light sweep along the band, twice per loop
        sheen = 0.34 * np.exp(-((v - sheen_pos) / 150) ** 2)
        paint = band_rgb[None, None, :] * ((0.72 + 0.56 * tex) * grad * band_gain + sheen)[..., None]
        frame = base * (1 - mask[..., None]) + paint * mask[..., None]
        im = Image.fromarray(np.clip(frame, 0, 255).astype(np.uint8))
        acc = accents(n, accent, grey)
        im.paste(acc, (0, 0), acc)
        ff.stdin.write(im.tobytes())
    ff.stdin.close()
    ff.wait()


if __name__ == "__main__":
    out = sys.argv[1]
    render(f"{out}/bg_gold.mp4", GOLD, (196, 142, 22), (120, 120, 126), 1.0)
    render(f"{out}/bg_dark.mp4", np.array([74, 54, 12], dtype=np.float32), (150, 110, 20), (84, 84, 90), 0.9)
