"""Fight Era motion graphics (approved by the user Nov 18, 2026: "keep all of them").

Used by the video builders through [MG: ...] markers in the build script, and by
tools/motion_reel.py for the sample reel. Every graphic is full frame (1920x1080).

Marker syntax (fields separated by " | "):
  [MG: stat — KICKER | 237 | BANNER | BARS TITLE | NAME 71, NAME 37]
        number counts up (non-numbers such as 48-47 just pop in); banner, bars title and bars optional
  [MG: quote — NAME | meta line | avatar.png | quote text | phrase to highlight / second phrase]
        lines reveal one by one, then a gold highlighter sweeps over each phrase (avatar may be "-")
  [MG: post — screenshot.png]
        X/Instagram screenshot slides up, then a slow push-in
  [MG: name — NAME | label | subtitle | photo.png]
        torn-paper name intro (Faceless Studio torn-profile)
  [MG: faceoff — left.png | LEFT NAME | left sub | right.png | RIGHT NAME | right sub]
        two portraits slide in, gold slash, "VS" slams in
  [MG: slam — WORD | setup line | background.png]
        full-screen word slam over a photo (Faceless Studio title-hierarchy)
  [MG: timeline — title | label · label · label · label · label · label]
        camera travels along a gold path of milestones (Faceless Studio milestone-path, exactly 6 labels)
Chapter openers: the builders turn [FX: chapter-number — 03 · TITLE] into chapter(…) automatically.
Transitions (builders): glitch is part of the chapter opener, a white flash opens every LET IT PLAY
clip, and every third narrated clip enters with a zoom punch instead of the side whip.
"""
import json
import math
import os
import re
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")
FX = os.path.join(ROOT, "fx", "effects", "render_effect.mjs")
W, H, FPS = 1920, 1080, 30
GOLD, RED, INK = (196, 142, 22), (200, 30, 30), (10, 10, 12)
F_BLACK = "/usr/share/fonts/opentype/inter/InterDisplay-BlackItalic.otf"
F_BOLD = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
F_XB = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
ENC = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "17", "-pix_fmt", "yuv420p", "-r", str(FPS),
       "-video_track_timescale", "15360", "-an"]
TEMPLATES = {"name": "torn-profile", "slam": "title-hierarchy", "timeline": "milestone-path"}
_fonts = {}


def font(path, size):
    k = (path, int(size))
    if k not in _fonts:
        _fonts[k] = ImageFont.truetype(path, max(int(size), 1))
    return _fonts[k]


def ease(t):
    t = min(max(t, 0.0), 1.0)
    return 1 - (1 - t) ** 3


def back(t):
    t = min(max(t, 0.0), 1.0)
    c = 1.9
    return 1 + (c + 1) * (t - 1) ** 3 + c * (t - 1) ** 2


def prog(t, a, b):
    return min(max((t - a) / (b - a), 0.0), 1.0)


def run(cmd):
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode:
        sys.exit("failed: " + " ".join(map(str, cmd))[:400] + "\n" + r.stderr.decode()[-1500:])


def load(path, size, centering=(0.5, 0.3)):
    im = Image.open(path)
    if im.mode in ("RGBA", "P", "LA"):
        im = im.convert("RGBA")
        im = Image.alpha_composite(Image.new("RGBA", im.size, (255, 255, 255, 255)), im)
    return ImageOps.fit(im.convert("RGB"), size, Image.LANCZOS, centering=centering).convert("RGBA")


def paste(c, im, x, y):
    """alpha_composite that tolerates images partly or fully off the canvas."""
    l, t = max(x, 0), max(y, 0)
    r, b = min(x + im.width, W), min(y + im.height, H)
    if r > l and b > t:
        c.alpha_composite(im.crop((l - x, t - y, r - x, b - y)), (l, t))


def shadow_box(d, box, alpha=150):
    x0, y0, x1, y1 = box
    for i in range(14, 0, -2):
        d.rectangle([x0 + 10 - i, y0 + 16 - i, x1 + 10 + i, y1 + 16 + i], fill=(0, 0, 0, int(alpha / 14)))


# ---------- marker parsing ----------
def parse(marker):
    """'[MG: kind — a | b | c]' -> (kind, [a, b, c])."""
    m = re.match(r"\[MG: ?(\w+) — (.*)\]\s*$", marker.strip())
    if not m:
        raise ValueError(f"bad MG marker: {marker}")
    return m.group(1), [x.strip() for x in m.group(2).split(" | ")]


def chapter_params(number, title, sub=""):
    return [number, title, sub]


# ---------- 1. stat ----------
def stat(p, dur):
    kicker, number = p[0], p[1]
    banner = p[2] if len(p) > 2 else ""
    bars_title = p[3] if len(p) > 3 else ""
    bars = []
    if len(p) > 4 and p[4]:
        for item in p[4].split(","):
            name, val = item.strip().rsplit(" ", 1)
            bars.append((name, float(val)))
    target = int(number) if number.isdigit() else None
    pw, ph = 1400, 520 + (90 * len(bars) + 90 if bars else 0)

    def draw(t):
        c = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(c)
        k = back(prog(t, 0, 0.45))
        x0 = (W - pw) // 2
        y0 = int((H - ph) // 2 + (1 - k) * 700)
        shadow_box(d, (x0, y0, x0 + pw, y0 + ph))
        d.rectangle([x0, y0, x0 + pw, y0 + ph], fill=INK + (240,), outline=GOLD + (255,), width=6)
        cx = W // 2
        a = int(255 * prog(t, 0.35, 0.6))
        d.text((cx, y0 + 80), kicker, font=font(F_BOLD, 40), fill=(235, 235, 235, a), anchor="mm")
        if target is not None:
            txt = str(int(round(target * ease(prog(t, 0.5, 2.0)))))
        else:
            txt = number
        pulse = 1 + 0.08 * max(0, 1 - abs(t - 2.05) / 0.15)
        size = 250 * pulse
        while d.textlength(txt, font=font(F_BLACK, size)) > pw - 120:
            size -= 10
        d.text((cx, y0 + 250), txt, font=font(F_BLACK, size), fill=GOLD + (a,), anchor="mm")
        if banner and t > 2.0:
            k2 = ease(prog(t, 2.0, 2.35))
            bw = d.textlength(banner, font=font(F_BLACK, 40)) + 80
            bx = int(cx - bw / 2 - (1 - k2) * 1400)
            d.rectangle([bx, y0 + 395, bx + bw, y0 + 465], fill=RED + (255,))
            d.text((bx + bw / 2, y0 + 430), banner, font=font(F_BLACK, 40), fill=(255, 255, 255, 255), anchor="mm")
        if bars and t > 3.0:
            a3 = int(255 * prog(t, 3.0, 3.3))
            d.text((cx, y0 + 535), bars_title, font=font(F_BOLD, 34), fill=(200, 200, 200, a3), anchor="mm")
            top = max(v for _, v in bars) or 1
            for i, (name, val) in enumerate(bars):
                col = GOLD if i == 0 else (150, 150, 155)
                y = y0 + 595 + i * 90
                frac = ease(prog(t, 3.2 + i * 0.2, 4.1 + i * 0.2))
                d.text((x0 + 90, y + 30), name, font=font(F_BLACK, 44), fill=(255, 255, 255, a3), anchor="lm")
                bx0, bmax = x0 + 330, 850
                d.rectangle([bx0, y + 6, bx0 + bmax, y + 54], fill=(40, 40, 44, a3))
                d.rectangle([bx0, y + 6, bx0 + int(bmax * val / top * frac), y + 54], fill=col + (a3,))
                shown = val * frac
                d.text((bx0 + bmax + 30, y + 30), f"{shown:.0f}" if val == int(val) else f"{shown:.1f}",
                       font=font(F_BLACK, 48), fill=col + (a3,), anchor="lm")
        return c
    sfx = [(2.05, "bass_drop", 0.6)] if target is not None else [(0.5, "bass_drop", 0.5)]
    if banner:
        sfx.append((2.0, "whoosh", 0.3))
    if bars:
        sfx.append((3.3, "click", 0.35))
    return draw, sfx


# ---------- 2. quote ----------
def norm(w):
    return w.strip(".,!?;:\"'\u201c\u201d\u2019").lower()


def quote(p, dur, images):
    name, meta, avatar, text = p[0], p[1], p[2], p[3]
    phrases = [x.strip() for x in p[4].split(" / ")] if len(p) > 4 and p[4] else []
    fq = font(F_XB, 50)
    dd = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    size = 50
    while True:  # shrink long quotes to fit
        fq = font(F_XB, size)
        lines, cur = [], []
        for w in text.split():
            if cur and dd.textlength(" ".join(cur + [w]), font=fq) > 1080:
                lines.append(cur)
                cur = []
            cur.append(w)
        lines.append(cur)
        lh = int(size * 1.64)
        if 120 + lh * len(lines) + 140 <= 1000 or size <= 30:
            break
        size -= 4
    boxes, sp, idx = [], dd.textlength(" ", font=fq), 0
    for li, ln in enumerate(lines):
        x = 0
        for w in ln:
            wl = dd.textlength(w, font=fq)
            boxes.append((li, x, x + wl, idx, w))
            x += wl + sp
            idx += 1
    flat = text.split()
    reveal_end = 0.85 + (len(lines) - 1) * 0.28
    marks = []
    for n, ph in enumerate(phrases):
        pw_ = ph.split()
        start = min(reveal_end + 0.5 + n * 1.3, max(dur - 1.2, 0.5))
        for i in range(len(flat) - len(pw_) + 1):
            if [norm(x) for x in flat[i:i + len(pw_)]] == [norm(x) for x in pw_]:
                marks.append((set(range(i, i + len(pw_))), start))
                break
    av = None
    if avatar and avatar != "-":
        av = load(images(avatar), (84, 84), (0.5, 0.25))
        mask = Image.new("L", (84, 84), 0)
        ImageDraw.Draw(mask).ellipse([0, 0, 84, 84], fill=255)
    pw, ph = 1300, 120 + lh * len(lines) + 140

    def draw(t):
        c = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(c)
        k = back(prog(t, 0, 0.45))
        x0 = int((W - pw) // 2 - (1 - k) * 1900)
        y0 = (H - ph) // 2
        shadow_box(d, (x0, y0, x0 + pw, y0 + ph))
        d.rectangle([x0, y0, x0 + pw, y0 + ph], fill=INK + (242,), outline=GOLD + (255,), width=6)
        nx = x0 + 70
        if av is not None:
            c.paste(av, (x0 + 70, y0 + 45), mask)
            nx = x0 + 175
        d.text((nx, y0 + 66), name, font=font(F_BLACK, 40), fill=(255, 255, 255, 255), anchor="lm")
        d.text((nx, y0 + 108), meta, font=font(F_BOLD, 28), fill=GOLD + (255,), anchor="lm")
        tx, ty = x0 + 110, y0 + 175
        for ws, start in marks:
            kk = ease(prog(t, start, start + 0.55))
            if kk <= 0:
                continue
            segs = {}
            for li, a, b, wi, _ in boxes:
                if wi in ws:
                    s = segs.setdefault(li, [a, b])
                    s[0], s[1] = min(s[0], a), max(s[1], b)
            left = sum(b - a for a, b in segs.values()) * kk
            for li in sorted(segs):
                a, b = segs[li]
                w = min(b - a, left)
                if w > 0:
                    d.rectangle([tx + a - 8, ty + li * lh - 4, tx + a + w + 8, ty + li * lh + size * 1.24],
                                fill=GOLD + (255,))
                left -= b - a
        hi = set()
        for ws, s in marks:
            if t >= s + 0.15:
                hi |= ws
        for li, a, b, wi, w in boxes:
            ap = ease(prog(t, 0.5 + li * 0.28, 0.85 + li * 0.28))
            if ap > 0:
                col = INK if wi in hi else (245, 245, 245)
                d.text((tx + a, ty + li * lh + int((1 - ap) * 24)), w, font=fq, fill=col + (int(255 * ap),))
        return c
    return draw, [(s, "pop", 0.4) for _, s in marks]


# ---------- 3. screenshot push-in ----------
def post(p, dur, images):
    src = Image.open(images(p[0])).convert("RGBA")
    base = min(820 / src.height, 1300 / src.width)

    def draw(t):
        c = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(c)
        k = ease(prog(t, 0, 0.4))
        s = base * (1.0 + 0.10 * prog(t, 0.3, max(dur, 1.0)) ** 0.8)
        im = src.resize((int(src.width * s), int(src.height * s)), Image.BILINEAR)
        x = (W - im.width) // 2
        y = int((H - im.height) // 2 + (1 - k) * 900)
        shadow_box(d, (x - 8, y - 8, x + im.width + 8, y + im.height + 8))
        d.rectangle([x - 8, y - 8, x + im.width + 8, y + im.height + 8], fill=GOLD + (255,))
        paste(c, im, x, y)
        return c
    return draw, [(0.0, "whoosh", 0.35)]


# ---------- 5. face-off ----------
def faceoff(p, dur, images):
    sides = [(-1, images(p[0]), p[1], p[2]), (1, images(p[3]), p[4], p[5])]
    pics = [load(path, (760, 860), (0.5, 0.25)) for _, path, _, _ in sides]

    def draw(t):
        c = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(c)
        z = 1 + 0.035 * prog(t, 0.6, max(dur, 1.0))
        for (side, _, name, sub), pic in zip(sides, pics):
            k = ease(prog(t, 0.0 if side < 0 else 0.12, 0.5 if side < 0 else 0.62))
            im = pic.resize((int(760 * z), int(860 * z)), Image.BILINEAR)
            cx = W // 2 + side * 420
            x = int(cx - im.width / 2 + side * (1 - k) * 1300)
            y = (H - im.height) // 2
            d.rectangle([x - 8, y - 8, x + im.width + 8, y + im.height + 8], fill=GOLD + (255,))
            paste(c, im, x, y)
            kb = ease(prog(t, 1.0, 1.35))
            if kb > 0:
                by = int(H - 150 + (1 - kb) * 220)
                tw = d.textlength(name, font=font(F_BLACK, 56)) + 80
                bx = int(cx - tw / 2)
                d.rectangle([bx, by, bx + tw, by + 112], fill=INK + (245,))
                d.rectangle([bx, by, bx + 10, by + 112], fill=GOLD + (255,))
                d.text((cx + 5, by + 34), sub, font=font(F_BOLD, 26), fill=GOLD + (255,), anchor="mm")
                d.text((cx + 5, by + 78), name, font=font(F_BLACK, 56), fill=(255, 255, 255, 255), anchor="mm")
        ks = ease(prog(t, 0.45, 0.75))
        if ks > 0:
            yb = int(H * ks)
            d.polygon([(W // 2 + 30, 0), (W // 2 + 80, 0), (W // 2 - 30, yb), (W // 2 - 80, yb)], fill=GOLD + (255,))
        kv = prog(t, 0.75, 1.0)
        if kv > 0:
            sc = 2.4 - 1.4 * back(kv)
            shake = int(10 * math.sin(t * 80) * max(0, 1 - (t - 0.75) / 0.35)) if t < 1.1 else 0
            d.text((W // 2 + shake, H // 2 - 40), "VS", font=font(F_BLACK, 210 * sc), fill=(255, 255, 255, 255),
                   anchor="mm", stroke_width=int(14 * sc), stroke_fill=INK + (255,))
        return c
    return draw, [(0.8, "bass_drop", 0.7)]


# ---------- 7. chapter opener ----------
def chapter(p, dur, images=None):
    number, title = p[0], p[1].upper()
    sub = p[2] if len(p) > 2 else ""
    tsize = 120
    dd = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    while dd.textlength(title, font=font(F_BLACK, tsize)) > 1700:
        tsize -= 6
    type_end = 0.8 + min(1.1, 0.06 * len(title))

    def draw(t):
        c = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(c)
        kin = ease(prog(t, 0, 0.35))
        xw = int(-400 + (W + 800) * kin)
        d.polygon([(0, 0), (xw, 0), (xw - 400, H), (0, H)], fill=GOLD + (255,))
        if t > 0.25:
            kn = ease(prog(t, 0.25, 0.8))
            sz = 330 * (1.25 - 0.25 * kn)
            if kn > 0.02:
                d.text((W // 2, H // 2 - 200), number, font=font(F_BLACK, sz), fill=INK + (int(255 * kn),), anchor="mm",
                       stroke_width=7, stroke_fill=INK + (int(255 * kn),))
                d.text((W // 2, H // 2 - 200), number, font=font(F_BLACK, sz), fill=GOLD + (255,), anchor="mm")
            n = int(len(title) * prog(t, 0.8, type_end))
            d.text((W // 2, H // 2 + 60), title[:n], font=font(F_BLACK, tsize), fill=INK + (255,), anchor="mm")
            if 0.8 < t < type_end + 0.2 and int(t * 6) % 2 == 0:
                tw = d.textlength(title[:n], font=font(F_BLACK, tsize))
                d.rectangle([W // 2 + tw / 2 + 10, H // 2 + 10, W // 2 + tw / 2 + 22, H // 2 + 115], fill=INK + (255,))
            if sub:
                a = int(255 * prog(t, type_end + 0.1, type_end + 0.5))
                d.text((W // 2, H // 2 + 175), sub, font=font(F_BOLD, 44), fill=INK + (a,), anchor="mm")
        kout = ease(prog(t, dur - 0.5, dur))
        if kout > 0:
            xo = int(-400 + (W + 800) * kout)
            d.polygon([(0, 0), (xo, 0), (xo - 400, H), (0, H)], fill=INK + (255,))
        return c
    return draw, [(0.0, "glitch", 0.45), (0.8, "keyboard_typing", 0.45)]


CUSTOM = {"stat": lambda p, d, img: stat(p, d), "quote": quote, "post": post, "faceoff": faceoff, "chapter": chapter}
BG = {"stat": "brush_chevrons", "quote": "gradient_streak", "post": "torn_panels", "faceoff": "gradient_streak",
      "chapter": "brush_chevrons"}


def template_overrides(kind, p, images, workdir):
    """Faceless Studio overrides; image slots are copied next to the overrides file."""
    def place(name):
        dst = os.path.join(workdir, os.path.basename(name).rsplit(".", 1)[0] + ".png")
        Image.open(images(name)).convert("RGB").save(dst)
        return os.path.basename(dst)
    if kind == "name":
        return {"title": p[0], "label": p[1], "subtitle": p[2] if len(p) > 2 else "",
                "images": [place(p[3])], "accent": "#C48E16", "background": "#121214"}
    if kind == "slam":
        return {"title": p[0], "subtitle": p[1], "backgroundImage": place(p[2]), "foreground": "#f3f1e9"}
    if kind == "timeline":
        labels = [x.strip() for x in p[1].split(" · ")]
        if len(labels) != 6:
            sys.exit(f"MG timeline needs exactly 6 labels (the template always draws 6), got {len(labels)}: {p[1]}")
        return {"title": p[0], "labels": labels, "accent": "#C48E16",
                "secondary": "#C41E1E", "background": "#121214", "foreground": "#f3f1e9"}
    raise ValueError(kind)


TEMPLATE_SFX = {"name": [(0.0, "whoosh", 0.35)], "slam": [(0.9, "bass_drop", 0.7)], "timeline": [(0.0, "whoosh", 0.3)]}
TEMPLATE_RANGE = {"name": (2, 12), "slam": (3, 18), "timeline": (2, 12)}


def sfx_for(kind, p, dur, images):
    """Sound effects (time, name, gain) relative to the graphic's start."""
    if kind in TEMPLATES:
        return TEMPLATE_SFX[kind]
    return CUSTOM[kind](p, dur, images)[1]


def render(kind, p, frames, out, images, workdir, bg=None):
    """Render one graphic of `frames` frames to out (video only). images(name) -> absolute path."""
    dur = frames / FPS
    if kind in TEMPLATES:
        os.makedirs(workdir, exist_ok=True)
        js = os.path.join(workdir, os.path.basename(out) + ".json")
        json.dump(template_overrides(kind, p, images, workdir), open(js, "w"))
        lo, hi = TEMPLATE_RANGE[kind]
        tdur = min(max(dur, lo), hi)
        raw = out + ".raw.mp4"
        run(["node", FX, "--id", TEMPLATES[kind], "--overrides", js, "--duration", f"{tdur:.3f}", "--out", raw])
        run(["ffmpeg", "-y", "-v", "error", "-i", raw, "-vf",
             f"fps={FPS},setsar=1,scale={W}:{H},tpad=stop_mode=clone:stop_duration={max(dur - tdur, 0) + 1:.2f}",
             "-frames:v", str(frames)] + ENC + [out])
        return out
    draw, _ = CUSTOM[kind](p, dur, images)
    bgfile = os.path.join(ASSETS, f"bg_{bg or BG[kind]}.mp4")
    proc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-stream_loop", "-1", "-i", bgfile,
                             "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                             "-filter_complex", f"[0:v]fps={FPS},setsar=1[b];[b][1:v]overlay=0:0[o]", "-map", "[o]",
                             "-frames:v", str(frames)] + ENC + [out], stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    for i in range(frames):
        proc.stdin.write(draw(i / FPS).tobytes())
    proc.stdin.close()
    if proc.wait():
        sys.exit(proc.stderr.read().decode()[-1500:])
    return out
