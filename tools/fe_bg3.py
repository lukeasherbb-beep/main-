"""FE Arena: the single Fight Era background (user, Nov 18: one high-quality background to build on).

Usage: python3 tools/fe_bg3.py assets/bg_arena.mp4 [--preview]
Seamless 16 s loop, 1920x1080, 30 fps. Palette from the logo intro: near-black board (no scratches),
light grey paper, brand gold, dark grey outlines. Most of the centre is covered by clip/card boxes
(max 1336x836, centred), so the motion lives in the margins and in the depth behind the boxes:
  breathing gold top light, slow diagonal light sweep, FIGHT ERA text waves scrolling in the back (replaced the octagons, user Nov 18),
  rising gold dust and bokeh (user, Nov 18: left grey paper strip removed, "too much going on"),
  drifting gold slashes and twinkling plus grid on the right (ghost logo removed, user Nov 18), corner logo badge,
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


class WaveText:
    """Repeated 'FIGHT ERA  •  ' set along a sine wave, scrolling sideways; seamless over one loop."""

    def __init__(self, y, amp, wavelength, size, rgba, speed, wave_cycles, phase):
        from PIL import ImageFont
        self.f = ImageFont.truetype(b2.FONT_BI, size)
        self.y, self.amp, self.L, self.rgba = y, amp, wavelength, rgba
        self.speed, self.cyc, self.phase = speed, wave_cycles, phase
        unit = "FIGHT ERA  \u2022  "
        dd = ImageDraw.Draw(Image.new("L", (1, 1)))
        self.chars, x = [], 0.0
        for ch in unit:
            adv = dd.textlength(ch, font=self.f)
            self.chars.append((ch, x + adv / 2))  # centre of each letter along the line
            x += adv
        self.tile = x
        self.cache = {}

    def glyph(self, ch, ang):
        k = (ch, ang)
        if k not in self.cache:
            s = int(self.f.size * 1.6)
            im = Image.new("RGBA", (s, s))
            ImageDraw.Draw(im).text((s / 2, s / 2), ch, font=self.f, fill=self.rgba, anchor="mm")
            self.cache[k] = im.rotate(-ang, resample=Image.BICUBIC)
        return self.cache[k]

    def draw(self, im, ph):
        off = (ph * self.speed * self.tile) % self.tile  # whole tiles per loop: seamless
        wp = 2 * math.pi * (ph * self.cyc + self.phase)
        x0 = -self.tile + off
        while x0 < W + self.tile:
            for ch, dx in self.chars:
                x = x0 + dx
                if ch == " " or x < -80 or x > W + 80:
                    continue
                th = 2 * math.pi * x / self.L + wp
                y = self.y + self.amp * math.sin(th)
                ang = round(math.degrees(math.atan(self.amp * 2 * math.pi / self.L * math.cos(th))))
                g = self.glyph(ch, ang)
                im.alpha_composite(g, (int(x - g.width / 2), int(y - g.height / 2)))
            x0 += self.tile


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
    # user, Nov 18: "very grainy": smooth the board noise, keep its soft mottled texture
    board = np.asarray(Image.fromarray(np.clip(b2.BOARD, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2.5)), np.float32) * 0.92
    base = Image.fromarray(np.clip(board, 0, 255).astype(np.uint8)).convert("RGBA")

    glow = np.exp(-(((XX - W / 2) / 900) ** 2 + ((YY + 120) / 520) ** 2))[..., None] * np.array(GOLD, np.float32)
    global DIAG
    DIAG = XX * 0.8 + YY * 0.6
    vign = (1 - 0.55 * (((XX - W / 2) / (W * 0.62)) ** 2 + ((YY - H / 2) / (H * 0.75)) ** 2))[..., None].clip(0.35, 1)
    grains = [r.normal(0, 0.8, (H, W, 1)).astype(np.float32) for _ in range(8)]  # just enough to stop banding

    waves = [WaveText(250, 55, 1500, 74, GREY + (120,), 1, 1, 0.0),          # back: faint grey, drifts right
             WaveText(560, 70, 1800, 92, (150, 104, 12, 70), -1, 1, 0.35),    # middle: dim gold, drifts left
             WaveText(860, 50, 1350, 74, GREY + (110,), 2, -1, 0.7)]
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
        for wv in waves:  # FIGHT ERA wave lines moving in the back
            wv.draw(im, ph)
        d = ImageDraw.Draw(im)
        for k in range(3):  # gold slashes on the right edge, drifting down one spacing per loop
            y0 = int(-260 + 420 * k + 420 * ph)
            for yy in (y0, y0 + 1260):
                d.polygon([(1790, yy), (1830, yy), (1920, yy + 200), (1880, yy + 200)], fill=GOLD + (90,))
        for x, y, p in plus:
            a = 0.35 + 0.65 * (0.5 + 0.5 * math.sin(2 * math.pi * (ph * 3 + p)))
            b2.plus(d, x, y, 9, GOLD + (int(210 * a),), w=4)
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
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "18",
                           "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    for n in range(frames):
        ff.stdin.write(frame(n).tobytes())
    ff.stdin.close()
    ff.wait()
    print("wrote", out)


if __name__ == "__main__":
    main()
