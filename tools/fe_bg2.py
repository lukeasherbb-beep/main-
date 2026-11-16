"""Second set of FE box backgrounds (seamless 8 s loops, 1920x1080, 30 fps).

Usage: python3 fe_bg2.py OUT_DIR [name ...]
Palette matches the logo intro: scratched near-black board, light grey paper for big shapes,
brand gold for plus signs and highlights, dark grey for outlines.
Styles (layouts modelled on reference channels):
  torn_split      black board torn over a grey paper half, plus-sign grids
  brush_chevrons  black board, vertical paper brush splash, chevrons down/up
  gradient_streak black board, diagonal paper brush streak, hash bars
  torn_panels     dark slate, paper side panels with torn edges, tall center slot
"""
import math
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

W, H, FPS, SECONDS = 1920, 1080, 30, 8
N = FPS * SECONDS
GOLD = np.array([196, 142, 22], np.float32)
ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")
YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fe_logo_intro  # noqa: E402  same scratched board as the logo intro

GREY = (70, 70, 74)  # intro octagon grey
GOLD_DIM = (150, 104, 12)  # intro plus colour over paper
BOARD = np.asarray(fe_logo_intro.backdrop(), np.float32)


def paper(r, shade=None):
    """Intro paper: light grey grain, a touch cooler in blue, optional shading map."""
    g = np.asarray(Image.fromarray((200 + r.random((H, W)) * 30).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2)), np.float32)
    if shade is not None:
        g = g * shade
    return np.dstack([g, g, g - 4])


def rng(seed):
    return np.random.default_rng(seed)


def smooth_noise(r, w, h, blur):
    im = Image.fromarray((r.random((h, w)) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(blur))
    return np.asarray(im.resize((W, H), Image.BICUBIC), np.float32) / 255


def crumple(r, strength=1.0):
    """Crumpled paper/fabric shading, centred on 0 (about -1..1)."""
    big = Image.fromarray((r.random((18, 32)) * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC)
    mid = Image.fromarray((r.random((60, 106)) * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC)
    big = big.filter(ImageFilter.GaussianBlur(6)).filter(ImageFilter.EMBOSS)
    mid = mid.filter(ImageFilter.GaussianBlur(3)).filter(ImageFilter.EMBOSS)
    a = np.asarray(big, np.float32) + 0.35 * np.asarray(mid, np.float32)
    a = np.asarray(Image.fromarray(np.clip(a / 1.35, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(4)), np.float32)
    a = (a - a.mean()) / (a.std() + 1e-6)
    return np.clip(a * strength, -2.5, 2.5)


def jagged(r, n, amp, fine=1.0):
    """1-D torn edge profile of length n: coarse wander + fine tearing + spikes."""
    x = np.linspace(0, 1, n)
    prof = np.zeros(n, np.float32)
    for k, a in ((3, 1.0), (9, 0.45), (40, 0.22 * fine), (160, 0.12 * fine)):
        pts = r.normal(0, a, k + 2)
        prof += np.interp(x * (k + 1), np.arange(k + 2), pts)
    spikes = r.random(n) < 0.012
    prof[spikes] += r.normal(0, 1.2, spikes.sum())
    prof = np.convolve(prof, np.ones(5) / 5, mode="same")  # no single-row slivers
    return prof * amp


def brush_edge(r, n, amp):
    """Dry-brush edge: many thin streak lengths (high frequency)."""
    base = jagged(r, n, amp * 0.5, 0.3)
    streak = (r.random(n) ** 3) * amp * 1.4
    streak = np.convolve(streak, np.ones(6) / 6, mode="same")
    return base + streak


def vignette(strength=0.5):
    return 1 - strength * (((XX - W / 2) / (W * 0.7)) ** 2 + ((YY - H / 2) / (H * 0.8)) ** 2)


def to_rgb(gray, tint=(1.0, 1.0, 1.0)):
    return gray[..., None] * np.array(tint, np.float32)


def blend(dst, rgb, mask):
    m = mask[..., None]
    return dst * (1 - m) + rgb * m


def plus(d, x, y, s, col, w=5):
    d.line([(x - s, y), (x + s, y)], fill=col, width=w)
    d.line([(x, y - s), (x, y + s)], fill=col, width=w)


def xmark(d, x, y, s, col, w=6):
    d.line([(x - s, y - s), (x + s, y + s)], fill=col, width=w)
    d.line([(x - s, y + s), (x + s, y - s)], fill=col, width=w)


def chevron(d, cx, y, half, depth, thick, up, col):
    if up:
        pts = [(cx - half, y + depth), (cx, y), (cx + half, y + depth),
               (cx + half, y + depth + thick), (cx, y + thick), (cx - half, y + depth + thick)]
    else:
        pts = [(cx - half, y), (cx, y + depth), (cx + half, y),
               (cx + half, y + thick), (cx, y + depth + thick), (cx - half, y + thick)]
    d.polygon(pts, fill=col)


def logo_bug(size):
    im = Image.open(os.path.join(ASSETS, "logo_square.png")).convert("RGB")
    a = np.asarray(im)
    bbox = Image.fromarray((a.max(axis=2) > 30).astype(np.uint8) * 255).getbbox()
    im = im.crop(bbox)
    im.thumbnail((size, size), Image.LANCZOS)
    a = np.asarray(im, np.float32)
    alpha = np.clip((a.max(axis=2) - 14) * 4.0, 0, 255).astype(np.uint8)
    return Image.fromarray(np.dstack([a.astype(np.uint8), alpha]), "RGBA")


def grid_pts(r, x0, y0, cols, rows, keep, step=48):
    return [(x0 + c * step, y0 + rr * step, r.random()) for rr in range(rows) for c in range(cols)
            if r.random() < keep(c, rr)]


# ---------------------------------------------------------------- styles
def torn_split():
    r = rng(21)
    dark = BOARD
    edge = 820 + jagged(r, H, 38) + np.linspace(-60, 90, H)  # tear runs top to bottom, leaning right
    gmask = np.clip((XX - edge[:, None]) / 2.0, 0, 1)
    gold = paper(r, 0.93 + 0.05 * (1 - YY / H))
    rim = np.clip(1 - np.abs(XX - edge[:, None] - 4) / 5, 0, 1) * 0.5  # paper fibre along the tear
    static = blend(dark, gold, gmask)
    static = blend(static, np.full_like(static, 235), rim)
    tr = grid_pts(r, 1280, 120, 9, 5, lambda c, rr: 0.9 - 0.12 * rr - 0.03 * c)
    bl = grid_pts(r, 160, 640, 6, 6, lambda c, rr: 0.25 + 0.1 * rr)
    bug = logo_bug(110)

    def frame(n):
        ph = n / N
        im = Image.fromarray(np.clip(static, 0, 255).astype(np.uint8))
        ov = Image.new("RGBA", (W, H))
        d = ImageDraw.Draw(ov)
        for x, y, p in tr:
            a = 0.45 + 0.55 * (0.5 + 0.5 * math.sin(2 * math.pi * (ph * 2 + p)))
            plus(d, x, y, 10, GOLD_DIM + (int(255 * a),))
        for x, y, p in bl:
            a = 0.4 + 0.6 * (0.5 + 0.5 * math.sin(2 * math.pi * (ph * 3 + p)))
            plus(d, x, y, 10, tuple(GOLD.astype(int)) + (int(230 * a),))
        im.paste(ov, (0, 0), ov)
        im.paste(bug, (W - bug.width - 36, H - bug.height - 30), bug)
        return im
    return frame


def brush_chevrons():
    r = rng(33)
    base = BOARD.copy()
    lines = Image.new("L", (W, H))
    d = ImageDraw.Draw(lines)
    for cx, cy, rad in ((420, 260, 120), (1700, 820, 160), (980, 980, 90), (300, 900, 70)):
        d.ellipse([cx - rad, cy - rad, cx + rad, cy + rad], outline=22, width=3)
    for k in range(10):
        x = r.uniform(-400, W)
        d.line([(x, H), (x + 700, 0)], fill=10, width=2)
    base += np.asarray(lines, np.float32)[..., None]
    # vertical brush splash behind the box (right of centre)
    left = 1180 + brush_edge(r, H, 70) + jagged(r, H, 40)
    right = 1580 + brush_edge(r, H, 70) + jagged(r, H, 40)
    pap = paper(r)

    spat = Image.new("L", (W, H))
    sd = ImageDraw.Draw(spat)
    for _ in range(140):
        side = left if r.random() < 0.5 else right
        y = r.uniform(0, H)
        x = side[int(y)] + r.normal(0, 60) * (1 if side is right else -1)
        s = r.uniform(1.5, 7)
        sd.ellipse([x - s, y - s, x + s, y + s], fill=255)
    spat = np.asarray(spat, np.float32) / 255
    bug = logo_bug(150)

    def frame(n):
        ph = n / N
        wob = 6 * math.sin(2 * math.pi * ph)
        m = np.clip((XX - (left[:, None] + wob)) / 2.5, 0, 1) * np.clip(((right[:, None] - wob) - XX) / 2.5, 0, 1)
        m = np.clip(m + spat, 0, 1)
        im = Image.fromarray(np.clip(blend(base, pap, m), 0, 255).astype(np.uint8))
        ov = Image.new("RGBA", (W, H))
        d = ImageDraw.Draw(ov)
        for k in range(3):  # chevrons down, left side; highlight walks downward
            lit = max(0.0, 1 - abs((ph * 3 * 3) % 3 - k))
            c = tuple(int(g + (a - g) * lit) for g, a in zip(GREY, GOLD.astype(int)))
            chevron(d, 230, 400 + k * 92, 95, 62, 34, False, c + (255,))
        for k in range(3):  # chevrons up, right side; highlight walks upward
            lit = max(0.0, 1 - abs((ph * 3 * 3) % 3 - (2 - k)))
            c = tuple(int(g + (a - g) * lit) for g, a in zip(GREY, GOLD.astype(int)))
            chevron(d, 1790, 150 + k * 56, 60, 40, 20, True, c + (255,))
        im.paste(ov, (0, 0), ov)
        im.paste(bug, (130, H - bug.height - 90), bug)
        return im
    return frame


def gradient_streak():
    r = rng(47)
    base = BOARD
    ang = math.radians(20)
    u = (XX - W * 0.5) * math.cos(ang) - (YY - H * 0.5) * math.sin(ang)  # across the streak
    v = ((XX - W * 0.5) * math.sin(ang) + (YY - H * 0.5) * math.cos(ang))
    vi = np.clip((v + 1300) / 2600 * 1199, 0, 1199).astype(int)
    eL, eR = brush_edge(r, 1200, 85), brush_edge(r, 1200, 85)
    half = 330
    m = np.clip((u + half + eL[vi]) / 3, 0, 1) * np.clip((half + eR[vi] - u) / 3, 0, 1)
    pap = paper(r)
    bug = logo_bug(150)

    def frame(n):
        ph = n / N
        shade = 0.84 + 0.14 * np.clip(XX / W + 0.1 * math.sin(2 * math.pi * ph) - YY / H * 0.25 + 0.1, 0, 1)
        im = Image.fromarray(np.clip(blend(base, pap * shade[..., None], m), 0, 255).astype(np.uint8))
        ov = Image.new("RGBA", (W, H))
        d = ImageDraw.Draw(ov)
        off = (ph * 4 * 34) % 34  # hash bars slide down, right side
        for k in range(-1, 6):
            y = 640 + k * 34 + off
            a = int(200 * max(0.0, min(1.0, (y - 620) / 30, (850 - y) / 30)))
            if a > 0:
                d.polygon([(1690, y + 22), (1790, y - 4), (1790, y + 10), (1690, y + 36)], fill=GREY + (a,))
        for k, (x, y) in enumerate([(210, 650), (210, 720), (1500, 150)]):  # X and + marks blink
            a = int(110 + 120 * (0.5 + 0.5 * math.sin(2 * math.pi * (ph * 2 - k / 3))))
            (plus if k == 0 else xmark)(d, x, y, 18, (tuple(GOLD.astype(int)) if k == 0 else GREY) + (a,), 8)
        im.paste(ov, (0, 0), ov)
        im.paste(bug, (130, H - bug.height - 70), bug)
        return im
    return frame


def torn_panels():
    r = rng(59)
    base = BOARD
    cols = np.zeros((H, W), np.float32)
    for x0, x1 in ((0, 690), (1230, W)):
        top = 190 + jagged(r, W, 22)
        bot = 880 + jagged(r, W, 22)
        cols = np.maximum(cols, (XX >= x0) * (XX < x1) * np.clip((YY - top[None, :]) / 2, 0, 1) * np.clip((bot[None, :] - YY) / 2, 0, 1))
    # grey torn paper layers peeking along the gold edges
    grey = np.zeros((H, W), np.float32)
    for yb, sgn in ((190, -1), (880, 1)):
        e = yb + sgn * (46 + jagged(r, W, 22, 1.6))
        band = np.clip((sgn * (e[None, :] - YY)) / 2, 0, 1) * np.clip((sgn * (YY - yb) + 4) / 2, 0, 1)
        grey = np.maximum(grey, band * ((XX < 690) | (XX >= 1230)))
    # black torn shapes overlapping the panels at top and bottom
    blk = np.zeros((H, W), np.float32)
    for yb, sgn in ((150, -1), (925, 1)):
        e = yb + sgn * np.abs(jagged(r, W, 45, 1.2))
        blk = np.maximum(blk, np.clip(sgn * (YY - e[None, :]) / 2, 0, 1) * ((XX < 690) | (XX >= 1230)))
    static = blend(base, paper(r, 0.95 + 0.05 * (YY / H)), cols)
    static = blend(static, np.broadcast_to(np.array(GREY, np.float32), static.shape), grey * (1 - cols))
    static = blend(static, to_rgb(np.full((H, W), 14, np.float32)), blk)
    dots = [(1880, 520 + k * 46) for k in range(9)]
    bug = logo_bug(110)

    def frame(n):
        ph = n / N
        im = Image.fromarray(np.clip(static, 0, 255).astype(np.uint8))
        ov = Image.new("RGBA", (W, H))
        d = ImageDraw.Draw(ov)
        for k in range(7):  # thin light streaks sliding diagonally across the panels
            x = (k * 330 + ph * 330 * 2) % 2310 - 200
            d.line([(x, 860), (x + 180, 230)], fill=GOLD_DIM + (90,), width=3)
        for k, (x, y) in enumerate(dots):
            a = int(120 + 135 * (0.5 + 0.5 * math.sin(2 * math.pi * (ph * 2 - k / 9))))
            d.ellipse([x - 5, y - 5, x + 5, y + 5], fill=tuple(GOLD.astype(int)) + (a,))
        xmark(d, 1660, 80, 16, GREY + (230,), 4)
        im.paste(ov, (0, 0), ov)
        im.paste(bug, (W - bug.width - 30, H - bug.height - 24), bug)
        return im
    return frame


STYLES = {"torn_split": torn_split, "brush_chevrons": brush_chevrons,
          "gradient_streak": gradient_streak, "torn_panels": torn_panels}


def render(name, out_dir):
    frame = STYLES[name]()
    out = os.path.join(out_dir, f"bg_{name}.mp4")
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                           "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    for n in range(N):
        ff.stdin.write(frame(n).tobytes())
    ff.stdin.close()
    ff.wait()
    print("wrote", out)


if __name__ == "__main__":
    out_dir = sys.argv[1]
    os.makedirs(out_dir, exist_ok=True)
    for name in sys.argv[2:] or STYLES:
        render(name, out_dir)
