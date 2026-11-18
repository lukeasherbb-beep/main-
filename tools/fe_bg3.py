"""FE Arena: the single Fight Era background (user, Nov 18: one high-quality background to build on).

Usage: python3 tools/fe_bg3.py assets/bg_arena.mp4 [--preview]
Seamless 16 s loop, 1920x1080, 30 fps. Palette from the logo intro: near-black board (no scratches),
light grey paper, brand gold, dark grey outlines. Most of the centre is covered by clip/card boxes
(max 1336x836, centred), so the motion lives in the margins and in the depth behind the boxes:
  breathing gold top light, slow diagonal light sweep, counter-rotating octagon rings,
  rising gold dust and bokeh, left torn-paper strip with a vertical FIGHT ERA ticker,
  drifting gold slashes and twinkling plus grid on the right, ghost logo, corner logo badge,
  vignette and film grain.
"""
import math
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fe_bg2 as b2  # noqa: E402  board, paper, ticker, logo helpers

W, H, FPS, SECONDS = 1920, 1080, 30, 16
N = FPS * SECONDS
GOLD = (196, 142, 22)
GREY = (70, 70, 74)
YY, XX = b2.YY, b2.XX


def octagon_ring(r, width, rgba):
    size = int(r * 2 + 40)
    im = Image.new("RGBA", (size, size))
    d = ImageDraw.Draw(im)
    c = size / 2
    pts = [(c + r * math.cos(math.pi / 8 + k * math.pi / 4), c + r * math.sin(math.pi / 8 + k * math.pi / 4)) for k in range(8)]
    d.line(pts + [pts[0]], fill=rgba, width=width, joint="curve")
    return im


def sprite(radius, alpha):
    """Soft round gold particle (bokeh when radius is large)."""
    s = int(radius * 4 + 4)
    g = np.exp(-(((np.mgrid[0:s, 0:s] - s / 2) ** 2).sum(0)) / (2 * (radius * 0.7) ** 2))
    if radius > 6:  # bokeh: flatter disc with a soft edge
        dist = np.sqrt(((np.mgrid[0:s, 0:s] - s / 2) ** 2).sum(0))
        g = np.clip((radius - dist) / 2.5, 0, 1) * 0.55 + g * 0.45
    out = np.zeros((s, s, 4), np.uint8)
    out[..., 0], out[..., 1], out[..., 2] = 236, 184, 70
    out[..., 3] = np.clip(g * alpha, 0, 255).astype(np.uint8)
    return Image.fromarray(out, "RGBA")


def build():
    r = b2.rng(77)
    board = b2.BOARD * 0.92
    # left torn paper strip (x 0..~150) with a torn right edge
    edge = 128 + b2.jagged(r, H, 16) + 10 * np.sin(np.linspace(0, 3 * math.pi, H))
    pmask = np.clip((edge[:, None] - XX) / 2.0, 0, 1)
    static = b2.blend(board, b2.paper(r, 0.95), pmask)
    rim = np.clip(1 - np.abs(XX - edge[:, None] + 3) / 4, 0, 1) * 0.45
    static = b2.blend(static, np.full_like(static, 235), rim)
    base = Image.fromarray(np.clip(static, 0, 255).astype(np.uint8)).convert("RGBA")
    ghost = b2.ghost_logo(560, (120, 120, 118), 34)
    base.alpha_composite(ghost, (W - ghost.width + 120, 300))

    glow = np.exp(-(((XX - W / 2) / 900) ** 2 + ((YY + 120) / 520) ** 2))[..., None] * np.array(GOLD, np.float32)
    global DIAG
    DIAG = XX * 0.8 + YY * 0.6
    vign = (1 - 0.55 * (((XX - W / 2) / (W * 0.62)) ** 2 + ((YY - H / 2) / (H * 0.75)) ** 2))[..., None].clip(0.35, 1)
    grains = [r.normal(0, 5.0, (H, W, 1)).astype(np.float32) for _ in range(8)]

    rings = [(octagon_ring(560, 3, GREY + (150,)), 5.0, 0.0), (octagon_ring(720, 2, GOLD + (70,)), -4.0, 1.3),
             (octagon_ring(900, 4, GREY + (110,)), 3.0, 2.1)]
    tile = b2.ticker("FIGHT ERA", 58, GREY, 170)
    parts = []
    for _ in range(70):
        rad = float(r.choice([1.5, 2, 2.5, 3, 4, 9, 14, 20], p=[.2, .2, .15, .15, .1, .1, .06, .04]))
        parts.append(dict(x=r.random() * W, y=r.random() * H, k=int(r.integers(1, 3)), sway=r.random() * 30,
                          ph=r.random(), tw=int(r.integers(1, 4)), spr=sprite(rad, 230 if rad < 6 else 80)))
    plus = b2.grid_pts(r, 1652, 150, 3, 7, lambda c, rr: 0.8 - 0.1 * c)
    bug = b2.logo_bug(110)

    def frame(n):
        ph = n / N
        im = base.copy()
        for ring, amp, off in rings:  # slow counter-rotation, centred slightly above middle
            rot = ring.rotate(amp * math.sin(2 * math.pi * ph + off), resample=Image.BICUBIC)
            im.alpha_composite(rot, (int(W / 2 - rot.width / 2), int(H / 2 - 30 - rot.height / 2)))
        d = ImageDraw.Draw(im)
        for k in range(3):  # gold slashes on the right edge, drifting down one spacing per loop
            y0 = int(-260 + 420 * k + 420 * ph)
            for yy in (y0, y0 + 1260):
                d.polygon([(1790, yy), (1830, yy), (1920, yy + 200), (1880, yy + 200)], fill=GOLD + (90,))
        for x, y, p in plus:
            a = 0.35 + 0.65 * (0.5 + 0.5 * math.sin(2 * math.pi * (ph * 3 + p)))
            b2.plus(d, x, y, 9, GOLD + (int(210 * a),), w=4)
        st = b2.scroll_strip(tile, H + 200, ph * 4 % 1.0).rotate(90, expand=True)  # 4 tiles per loop
        im.alpha_composite(st, (24, -100))
        for p in parts:
            y = (p["y"] - p["k"] * (H + 120) * ph) % (H + 120) - 60
            x = p["x"] + p["sway"] * math.sin(2 * math.pi * (ph * 2 + p["ph"]))
            tw = 0.45 + 0.55 * (0.5 + 0.5 * math.sin(2 * math.pi * (ph * p["tw"] + p["ph"])))
            spr = p["spr"]
            if tw < 0.98:
                a = np.asarray(spr).copy()
                a[..., 3] = (a[..., 3] * tw).astype(np.uint8)
                spr = Image.fromarray(a, "RGBA")
            ix, iy = int(x - spr.width / 2), int(y - spr.height / 2)
            if -spr.width < ix < W and -spr.height < iy < H:
                l, t = max(ix, 0), max(iy, 0)
                rr, bb = min(ix + spr.width, W), min(iy + spr.height, H)
                im.alpha_composite(spr.crop((l - ix, t - iy, rr - ix, bb - iy)), (l, t))
        f = np.asarray(im.convert("RGB"), np.float32)
        f += glow * (0.17 + 0.07 * math.sin(2 * math.pi * ph))  # breathing top light
        c = (-0.3 + 1.6 * ph) * (W * 0.8 + H * 0.6)  # one soft diagonal sweep per loop
        band = np.exp(-((DIAG - c) / 220) ** 2)
        f += band[..., None] * np.array([70, 52, 16], np.float32) * 0.55
        f = f * vign + grains[n % 8]
        out = Image.fromarray(np.clip(f, 0, 255).astype(np.uint8)).convert("RGBA")
        out.alpha_composite(bug, (W - bug.width - 36, H - bug.height - 30))
        return out.convert("RGB")
    return frame


def main():
    out = sys.argv[1]
    frames = N if "--preview" not in sys.argv else FPS * 4
    frame = build()
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "15",
                           "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    for n in range(frames):
        ff.stdin.write(frame(n).tobytes())
    ff.stdin.close()
    ff.wait()
    print("wrote", out)


if __name__ == "__main__":
    main()
