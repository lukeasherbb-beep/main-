"""Render the Fight Era animated backgrounds (seamless loops).

Usage: python3 fe_bg.py OUT_DIR
Writes bg_gold.mp4 (chevrons going down) and bg_dark.mp4 (octagons).
Both 1920x1080, 30 fps, 12 s loops, with the FE logo watermarked center.
"""
import math
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

W, H, FPS, SECONDS = 1920, 1080, 30, 12
N = FPS * SECONDS
GOLD = np.array([196, 142, 22], dtype=np.float32)
rng = np.random.default_rng(7)

ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")


def load_logo(size=280):
    path = os.path.join(ASSETS, "logo_square.png")
    if not os.path.exists(path):
        return None
    logo = Image.open(path).convert("RGBA")
    logo = logo.resize((size, size), Image.LANCZOS)
    arr = np.array(logo)
    arr[..., 3] = (arr[..., 3].astype(np.float32) * 0.12).clip(0, 255).astype(np.uint8)
    return Image.fromarray(arr)


def noise(w, h, blur):
    im = Image.fromarray((rng.random((h, w)) * 255).astype(np.uint8))
    return im.filter(ImageFilter.GaussianBlur(blur))


def paper():
    big = noise(96, 54, 2).resize((W, H), Image.BICUBIC)
    mid = noise(480, 270, 3).resize((W, H), Image.BICUBIC)
    creases = ImageChops.add(big.filter(ImageFilter.EMBOSS), mid.filter(ImageFilter.EMBOSS), 2.0)
    a = np.asarray(creases, dtype=np.float32) / 255.0
    a = (a - a.mean()) / (a.std() + 1e-6)
    return np.clip(0.5 + 0.22 * a, 0, 1)


def streak_noise():
    base = rng.random((300, 64)).astype(np.float32)
    im = Image.fromarray((base * 255).astype(np.uint8)).resize((2048, 300), Image.BICUBIC)
    a = np.asarray(im, dtype=np.float32) / 255.0
    return np.concatenate([a, a], axis=1)


# --------------- CHEVRONS (arrows going down) ---------------

def chevrons_down(n, accent, grey):
    """Chevron arrows cascading downward across the full frame."""
    ph = n / N
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cols = 7
    rows = 9
    col_w = W // cols
    row_h = 130
    offset_y = (ph * rows * row_h) % row_h
    for col in range(cols):
        cx = col * col_w + col_w // 2
        for row in range(-1, rows + 1):
            y = row * row_h + offset_y
            wave_delay = col * 0.14
            lit = max(0.0, 1 - abs(((ph * 4 + wave_delay) * rows % rows) - (row % rows)) / 1.8)
            col_rgba = tuple(int(g + (a - g) * lit) for g, a in zip(grey, accent))
            alpha = int(60 + 195 * lit)
            half_w = col_w // 2 - 16
            tip_y = y + 50
            d.polygon([
                (cx - half_w, y),
                (cx, tip_y),
                (cx + half_w, y),
                (cx + half_w, y + 14),
                (cx, tip_y + 14),
                (cx - half_w, y + 14),
            ], fill=col_rgba + (alpha,))
    return im


# --------------- OCTAGONS (rotating rings) ---------------

def octagon_pts(cx, cy, r, rot):
    return [(cx + r * math.cos(rot + k * math.pi / 4),
             cy + r * math.sin(rot + k * math.pi / 4)) for k in range(8)]


def octagons_pattern(n, accent, grey):
    """Multiple rotating octagons spread across the frame."""
    ph = n / N
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    placements = [
        (W // 2, H // 2, 320, 1.0, 0.6),
        (W // 2, H // 2, 220, -1.5, 0.45),
        (W // 2, H // 2, 130, 2.0, 0.3),
        (260, 200, 120, 0.8, 0.35),
        (1660, 200, 120, -0.8, 0.35),
        (260, 880, 120, -1.2, 0.35),
        (1660, 880, 120, 1.2, 0.35),
        (260, 540, 80, 1.6, 0.25),
        (1660, 540, 80, -1.6, 0.25),
    ]
    for cx, cy, r, speed, base_alpha in placements:
        rot = 2 * math.pi * ph * speed
        pts = octagon_pts(cx, cy, r, rot)
        pulse = 0.7 + 0.3 * math.sin(2 * math.pi * ph * abs(speed) * 2)
        alpha = int(255 * base_alpha * pulse)
        is_accent = r > 150
        col = accent if is_accent else grey
        width = max(3, int(r / 30))
        d.line(pts + [pts[0]], fill=col + (alpha,), width=width, joint="curve")
    return im


# --------------- RENDER ---------------

def render(out, band_rgb, accent, grey, band_gain, accent_fn):
    tex = paper()
    st = streak_noise()
    logo = load_logo(280)
    logo_pos = ((W - 280) // 2, (H - 280) // 2) if logo else None
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    ang = math.radians(-20)
    ca, sa = math.cos(ang), math.sin(ang)
    u0 = (xx - W / 2) * ca + (yy - H / 2) * sa
    v = -(xx - W / 2) * sa + (yy - H / 2) * ca
    vi = ((v + 1200) / 2400 * 1024).astype(np.int32) % 1024
    base = (18 + 44 * tex)[..., None] * np.array([1.0, 1.0, 1.04], dtype=np.float32)
    grad = 0.82 + 0.3 * (v / 1200)
    cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", out]
    ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for n in range(N):
        ph = n / N
        sway = 46 * math.sin(2 * math.pi * ph)
        half = 520 + 26 * math.sin(2 * math.pi * ph * 2)
        u = u0 - sway
        shift = int(ph * 1024)
        ui = np.clip(((np.abs(u) - half + 190) / 380 * 300), 0, 299).astype(np.int32)
        edge = st[ui, (vi + np.where(u > 0, shift, -shift)) % 1024]
        dist = np.abs(u) - half
        mask = np.clip((-(dist) + 150 * (edge - 0.5)) / 14, 0, 1)
        mask *= np.where(dist > -170, np.clip((edge - 0.18) * 4, 0, 1), 1)
        sheen_pos = -1300 + 2600 * ((ph * 2) % 1)
        sheen = 0.34 * np.exp(-((v - sheen_pos) / 150) ** 2)
        paint = band_rgb[None, None, :] * ((0.72 + 0.56 * tex) * grad * band_gain + sheen)[..., None]
        frame = base * (1 - mask[..., None]) + paint * mask[..., None]
        im = Image.fromarray(np.clip(frame, 0, 255).astype(np.uint8))
        if logo:
            im.paste(logo, logo_pos, logo)
        acc = accent_fn(n, accent, grey)
        im.paste(acc, (0, 0), acc)
        ff.stdin.write(im.tobytes())
    ff.stdin.close()
    ff.wait()


if __name__ == "__main__":
    out = sys.argv[1]
    print("Rendering bg_gold.mp4 (chevrons down)...")
    render(f"{out}/bg_gold.mp4", GOLD, (196, 142, 22), (120, 120, 126), 1.0, chevrons_down)
    print("Rendering bg_dark.mp4 (octagons)...")
    render(f"{out}/bg_dark.mp4", np.array([74, 54, 12], dtype=np.float32), (150, 110, 20), (84, 84, 90), 0.9, octagons_pattern)
    print("Done.")
