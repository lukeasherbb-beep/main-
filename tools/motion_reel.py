"""Motion-graphics sample reel for Fight Era (Hokit vs Jones material).

Usage: python3 tools/motion_reel.py OUT.mp4
Each section is numbered on screen so the user can say which ones to keep.
Custom animations are drawn frame by frame with Pillow and piped into ffmpeg over the
FE moving backgrounds; three sections use Faceless Studio templates (fx/effects).
"""
import json
import math
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")
SFX = os.path.join(ASSETS, "sfx")
IMG = os.path.join(ROOT, "hokit", "images")
CLIPS = os.path.join(ROOT, "hokit", "clips")
FX = os.path.join(ROOT, "fx", "effects", "render_effect.mjs")
WORK = os.environ.get("REEL_WORK", "/tmp/fe_reel")
W, H, FPS = 1920, 1080, 30
GOLD, RED, INK, PAPER = (196, 142, 22), (200, 30, 30), (10, 10, 12), (243, 241, 233)
F_BLACK = "/usr/share/fonts/opentype/inter/InterDisplay-BlackItalic.otf"
F_BOLD = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
F_XB = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
ENC = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "17", "-pix_fmt", "yuv420p", "-r", str(FPS),
       "-video_track_timescale", "15360"]
_fonts = {}


def font(path, size):
    k = (path, int(size))
    if k not in _fonts:
        _fonts[k] = ImageFont.truetype(path, int(size))
    return _fonts[k]


def ease(t):  # ease-out cubic, clamped
    t = min(max(t, 0.0), 1.0)
    return 1 - (1 - t) ** 3


def back(t):  # ease-out with a little overshoot
    t = min(max(t, 0.0), 1.0)
    c = 1.9
    return 1 + (c + 1) * (t - 1) ** 3 + c * (t - 1) ** 2


def prog(t, a, b):
    return min(max((t - a) / (b - a), 0.0), 1.0)


def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, **kw)
    if r.returncode:
        sys.exit("failed: " + " ".join(map(str, cmd))[:400] + "\n" + r.stderr.decode()[-1500:])


def photo(name, size, centering=(0.5, 0.3)):
    im = Image.open(name if os.path.isabs(name) else os.path.join(IMG, name))
    if im.mode in ("RGBA", "P", "LA"):
        im = im.convert("RGBA")
        bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
        im = Image.alpha_composite(bg, im)
    return ImageOps.fit(im.convert("RGB"), size, Image.LANCZOS, centering=centering).convert("RGBA")


def shadow_box(d, box, alpha=150):
    x0, y0, x1, y1 = box
    for i in range(14, 0, -2):
        d.rectangle([x0 + 10 - i, y0 + 16 - i, x1 + 10 + i, y1 + 16 + i], fill=(0, 0, 0, int(alpha / 14)))


def custom(out, dur, bg, draw):
    """Render `draw(t) -> RGBA Image` over a looping background video."""
    n = round(dur * FPS)
    p = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-stream_loop", "-1", "-i", os.path.join(ASSETS, f"bg_{bg}.mp4"),
                          "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-filter_complex", f"[0:v]fps={FPS},setsar=1[b];[b][1:v]overlay=0:0[o]", "-map", "[o]",
                          "-frames:v", str(n)] + ENC + [out], stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    for i in range(n):
        p.stdin.write(draw(i / FPS).tobytes())
    p.stdin.close()
    if p.wait():
        sys.exit(p.stderr.read().decode()[-1500:])


def template(out, effect, overrides, dur):
    js = os.path.join(WORK, f"{effect}.json")
    json.dump(overrides, open(js, "w"))
    raw = out + ".raw.mp4"
    run(["node", FX, "--id", effect, "--overrides", js, "--duration", str(dur), "--out", raw])
    run(["ffmpeg", "-y", "-v", "error", "-i", raw, "-vf", f"fps={FPS},setsar=1,scale={W}:{H}", "-frames:v",
         str(round(dur * FPS))] + ENC + [out])


# ---------- 1. stat count-up ----------
def seg_stat(t):
    c = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(c)
    k = back(prog(t, 0, 0.45))
    pw, ph = 1400, 800
    x0 = (W - pw) // 2
    y0 = int((H - ph) // 2 + (1 - k) * 700)
    shadow_box(d, (x0, y0, x0 + pw, y0 + ph))
    d.rectangle([x0, y0, x0 + pw, y0 + ph], fill=INK + (240,), outline=GOLD + (255,), width=6)
    cx = W // 2
    a = int(255 * prog(t, 0.35, 0.6))
    d.text((cx, y0 + 80), "CIRYL GANE · SIGNIFICANT STRIKES", font=font(F_BOLD, 40), fill=(235, 235, 235, a), anchor="mm")
    num = int(round(237 * ease(prog(t, 0.5, 2.0))))
    pulse = 1 + 0.08 * max(0, 1 - abs(t - 2.05) / 0.15)
    d.text((cx, y0 + 250), str(num), font=font(F_BLACK, 250 * pulse), fill=GOLD + (a,), anchor="mm")
    if t > 2.0:  # record banner slides in
        k2 = ease(prog(t, 2.0, 2.35))
        bw = 760
        bx = int(cx - bw / 2 - (1 - k2) * 1200)
        d.rectangle([bx, y0 + 395, bx + bw, y0 + 465], fill=RED + (255,))
        d.text((bx + bw / 2, y0 + 430), "NEW UFC HEAVYWEIGHT RECORD", font=font(F_BLACK, 40), fill=(255, 255, 255, 255), anchor="mm")
    if t > 3.0:  # round 3 bars
        a3 = int(255 * prog(t, 3.0, 3.3))
        d.text((cx, y0 + 535), "ROUND 3 · TOTAL STRIKES", font=font(F_BOLD, 34), fill=(200, 200, 200, a3), anchor="mm")
        for i, (name, val, col) in enumerate([("HOKIT", 71, GOLD), ("GANE", 37, (150, 150, 155))]):
            y = y0 + 595 + i * 90
            frac = ease(prog(t, 3.3 + i * 0.25, 4.6 + i * 0.25))
            d.text((x0 + 90, y + 30), name, font=font(F_BLACK, 44), fill=(255, 255, 255, a3), anchor="lm")
            bx0, bmax = x0 + 300, 880
            d.rectangle([bx0, y + 6, bx0 + bmax, y + 54], fill=(40, 40, 44, a3))
            d.rectangle([bx0, y + 6, bx0 + int(bmax * val / 71 * frac), y + 54], fill=col + (a3,))
            d.text((bx0 + bmax + 30, y + 30), str(int(round(val * frac))), font=font(F_BLACK, 48), fill=col + (a3,), anchor="lm")
    return c


# ---------- 2. quote with line reveal + highlighter ----------
QUOTE = ("Josh, everyone in this sport has been poked in the eye. You had 25 minutes to become champion. "
         "Greg Jackson told you at the beginning of the fourth that you had 10 minutes left to become a world "
         "champion, and you absolutely folded. You can't blame that on an eye poke. You got picked apart.")
PHRASES = [("you absolutely folded.", 4.0), ("You got picked apart.", 5.4)]


def layout_quote(fq, maxw):
    d = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    words, lines, cur = QUOTE.split(), [], []
    for w in words:
        if cur and d.textlength(" ".join(cur + [w]), font=fq) > maxw:
            lines.append(cur)
            cur = []
        cur.append(w)
    lines.append(cur)
    boxes, idx = [], 0  # (line, x0, x1, word index)
    sp = d.textlength(" ", font=fq)
    for li, ln in enumerate(lines):
        x = 0
        for w in ln:
            wl = d.textlength(w, font=fq)
            boxes.append((li, x, x + wl, idx, w))
            x += wl + sp
            idx += 1
    flat = QUOTE.split()
    marks = []
    for ph, start in PHRASES:
        pw = ph.split()
        for i in range(len(flat) - len(pw) + 1):
            if flat[i:i + len(pw)] == pw:
                marks.append((set(range(i, i + len(pw))), start))
                break
    return lines, boxes, marks


FQ = None


def seg_quote(t):
    global FQ
    fq = font(F_XB, 50)
    if FQ is None:
        FQ = layout_quote(fq, 1080)
    lines, boxes, marks = FQ
    c = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(c)
    k = back(prog(t, 0, 0.45))
    pw, ph = 1300, 120 + 82 * len(lines) + 140
    x0 = int((W - pw) // 2 - (1 - k) * 1900)
    y0 = (H - ph) // 2
    shadow_box(d, (x0, y0, x0 + pw, y0 + ph))
    d.rectangle([x0, y0, x0 + pw, y0 + ph], fill=INK + (242,), outline=GOLD + (255,), width=6)
    av = photo("jones_interview.png", (84, 84), (0.5, 0.25))
    m = Image.new("L", (84, 84), 0)
    ImageDraw.Draw(m).ellipse([0, 0, 84, 84], fill=255)
    c.paste(av, (x0 + 70, y0 + 45), m)
    d.text((x0 + 175, y0 + 66), "JON JONES", font=font(F_BLACK, 40), fill=(255, 255, 255, 255), anchor="lm")
    d.text((x0 + 175, y0 + 108), "on X · Nov 17, 2026", font=font(F_BOLD, 28), fill=GOLD + (255,), anchor="lm")
    tx, ty = x0 + 110, y0 + 175
    # highlighter sweeps (drawn under the words)
    for ws, start in marks:
        kk = ease(prog(t, start, start + 0.55))
        if kk <= 0:
            continue
        segs = {}
        for li, a, b, wi, _ in boxes:
            if wi in ws:
                s = segs.setdefault(li, [a, b])
                s[0], s[1] = min(s[0], a), max(s[1], b)
        total = sum(b - a for a, b in segs.values())
        left = total * kk
        for li in sorted(segs):
            a, b = segs[li]
            w = min(b - a, left)
            if w > 0:
                d.rectangle([tx + a - 8, ty + li * 82 - 4, tx + a + w + 8, ty + li * 82 + 62], fill=GOLD + (255,))
            left -= b - a
    hi = set().union(*[ws for ws, s in marks if t >= s + 0.15]) if marks else set()
    for li, a, b, wi, w in boxes:
        ap = ease(prog(t, 0.5 + li * 0.28, 0.85 + li * 0.28))
        if ap <= 0:
            continue
        col = INK if wi in hi else (245, 245, 245)
        d.text((tx + a, ty + li * 82 + int((1 - ap) * 24)), w, font=fq, fill=col + (int(255 * ap),))
    return c


# ---------- 3. screenshot push-in ----------
XS = None


def seg_xpost(t):
    global XS
    if XS is None:
        XS = Image.open(os.path.join(IMG, "x_jones_woke_up.png")).convert("RGBA")
    c = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(c)
    k = ease(prog(t, 0, 0.4))
    s = (820 / XS.height) * (1.0 + 0.10 * prog(t, 0.3, 5.0) ** 0.8)
    im = XS.resize((int(XS.width * s), int(XS.height * s)), Image.LANCZOS)
    x = (W - im.width) // 2
    y = int((H - im.height) // 2 + (1 - k) * 900)
    shadow_box(d, (x - 8, y - 8, x + im.width + 8, y + im.height + 8))
    d.rectangle([x - 8, y - 8, x + im.width + 8, y + im.height + 8], fill=GOLD + (255,))
    c.alpha_composite(im, (x, max(y, -im.height)))
    return c


# ---------- 5. face-off ----------
FO = {}


def seg_faceoff(t):
    if not FO:
        FO["l"] = photo(os.path.join(WORK, "hokit_frame.png"), (760, 860), (0.5, 0.2))
        FO["r"] = photo("jones_interview.png", (760, 860), (0.5, 0.3))
    c = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(c)
    z = 1 + 0.035 * prog(t, 0.6, 4.5)
    for side, key, name, sub in ((-1, "l", "JOSH HOKIT", "THE CHALLENGER · 10-1"), (1, "r", "JON JONES", "THE FORMER CHAMP")):
        k = ease(prog(t, 0.0 if side < 0 else 0.12, 0.5 if side < 0 else 0.62))
        im = FO[key].resize((int(760 * z), int(860 * z)), Image.LANCZOS)
        cx = W // 2 + side * 420
        x = int(cx - im.width / 2 + side * (1 - k) * 1300)
        y = (H - im.height) // 2
        d.rectangle([x - 8, y - 8, x + im.width + 8, y + im.height + 8], fill=GOLD + (255,))
        c.alpha_composite(im, (x, y))
        kb = ease(prog(t, 1.0, 1.35))
        if kb > 0:
            by = int(H - 150 + (1 - kb) * 220)
            tw = ImageDraw.Draw(c).textlength(name, font=font(F_BLACK, 64)) + 70
            bx = int(cx - tw / 2)
            d.rectangle([bx, by, bx + tw, by + 112], fill=INK + (245,))
            d.rectangle([bx, by, bx + 10, by + 112], fill=GOLD + (255,))
            d.text((cx + 5, by + 34), sub, font=font(F_BOLD, 26), fill=GOLD + (255,), anchor="mm")
            d.text((cx + 5, by + 78), name, font=font(F_BLACK, 56), fill=(255, 255, 255, 255), anchor="mm")
    ks = ease(prog(t, 0.45, 0.75))  # gold slash wipes down the middle
    if ks > 0:
        yb = int(H * ks)
        d.polygon([(W // 2 + 30, 0), (W // 2 + 80, 0), (W // 2 - 30 + 0, yb), (W // 2 - 80, yb)], fill=GOLD + (255,))
    kv = prog(t, 0.75, 1.0)
    if kv > 0:
        sc = 2.4 - 1.4 * back(kv)
        shake = int(10 * math.sin(t * 80) * max(0, 1 - (t - 0.75) / 0.35)) if t < 1.1 else 0
        d.text((W // 2 + shake, H // 2 - 40), "VS", font=font(F_BLACK, 210 * sc), fill=(255, 255, 255, 255),
               anchor="mm", stroke_width=int(14 * sc), stroke_fill=INK + (255,))
    return c


# ---------- 7. chapter opener ----------
def seg_chapter(t):
    c = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(c)
    kin = ease(prog(t, 0, 0.35))  # gold panel wipes in diagonally
    xw = int(-400 + (W + 800) * kin)
    d.polygon([(0, 0), (xw, 0), (xw - 400, H), (0, H)], fill=GOLD + (255,))
    if t > 0.25:
        kn = ease(prog(t, 0.25, 0.8))
        sz = 330 * (1.25 - 0.25 * kn)
        if kn > 0.02:  # outlined numeral: ink stroke, gold fill on top
            d.text((W // 2, H // 2 - 200), "03", font=font(F_BLACK, sz), fill=INK + (int(255 * kn),), anchor="mm",
                   stroke_width=7, stroke_fill=INK + (int(255 * kn),))
            d.text((W // 2, H // 2 - 200), "03", font=font(F_BLACK, sz), fill=GOLD + (255,), anchor="mm")
        title = "THE WAR OF WORDS"
        n = int(len(title) * prog(t, 0.8, 1.9))
        d.text((W // 2, H // 2 + 60), title[:n], font=font(F_BLACK, 120), fill=INK + (255,), anchor="mm")
        if 0.8 < t < 2.0 and int(t * 6) % 2 == 0:  # typing cursor
            tw = d.textlength(title[:n], font=font(F_BLACK, 120))
            d.rectangle([W // 2 + tw / 2 + 10, H // 2 + 10, W // 2 + tw / 2 + 22, H // 2 + 115], fill=INK + (255,))
        a = int(255 * prog(t, 2.0, 2.4))
        d.text((W // 2, H // 2 + 175), "Jones and Hokit take it to X", font=font(F_BOLD, 44), fill=INK + (a,), anchor="mm")
    kout = ease(prog(t, 4.0, 4.5))  # black wipe out
    if kout > 0:
        xo = int(-400 + (W + 800) * kout)
        d.polygon([(0, 0), (xo, 0), (xo - 400, H), (0, H)], fill=INK + (255,))
    return c


# ---------- 9. transitions demo ----------
def boxed_clip(src, start, dur, out, crop=True):
    bw, bh = 1336, 752
    x0, y0 = (W - bw - 16) // 2, (H - bh - 16) // 2
    cr = "crop=iw-12:ih-12:6:6," if crop else ""
    fcx = (f"[0:v]{cr}scale={bw}:{bh}:force_original_aspect_ratio=increase,crop={bw}:{bh},fps={FPS},setsar=1,"
           f"pad=iw+16:ih+16:8:8:color=0xC48E16[v];[1:v]fps={FPS},setsar=1[b];[b][v]overlay={x0}:{y0}[o]")
    run(["ffmpeg", "-y", "-v", "error", "-ss", str(start), "-i", src, "-stream_loop", "-1", "-i",
         os.path.join(ASSETS, "bg_arena.mp4"), "-filter_complex", fcx, "-map", "[o]", "-t", str(dur)] + ENC + ["-an", out])


def transitions(out):
    parts = [("03_r1_wild_hooks.mp4", 2.0), ("04_r1_single_leg_slam_LIP.mp4", 1.8),
             ("12_eye_poke_replay.mp4", 6.0), ("06_r4-5_gane_jabs_uppercuts.mp4", 6.0)]
    files = []
    for i, (f, st) in enumerate(parts):
        o = os.path.join(WORK, f"tr{i}.mp4")
        boxed_clip(os.path.join(CLIPS, f), st, 3.2, o)
        files.append(o)
    # glitch (pixelize + rgb split), white flash, zoom punch
    fc = ("[0:v][1:v]xfade=transition=pixelize:duration=0.35:offset=2.85[a];"
          "[a]rgbashift=rh=-14:bh=14:enable='between(t,2.8,3.25)'[a2];"
          "[a2][2:v]xfade=transition=fadewhite:duration=0.4:offset=5.65[b];"
          "[b][3:v]xfade=transition=zoomin:duration=0.35:offset=8.5[o]")
    cmd = ["ffmpeg", "-y", "-v", "error"]
    for f in files:
        cmd += ["-i", f]
    run(cmd + ["-filter_complex", fc, "-map", "[o]"] + ENC + ["-an", out])
    return [(2.85, "glitch", 0.6), (5.65, "camera_flash", 0.6), (8.5, "whoosh", 0.8)]


def tag(src, label, out):
    """Section number for review, top centre."""
    txt = label.replace(":", r"\:").replace("'", "")
    run(["ffmpeg", "-y", "-v", "error", "-i", src, "-vf",
         f"drawbox=x=(iw-760)/2:y=24:w=760:h=64:color=0x0A0A0C@0.85:t=fill,"
         f"drawtext=fontfile={F_BLACK}:text='{txt}':fontsize=36:fontcolor=0xC48E16:x=(w-tw)/2:y=40"] + ENC + ["-an", out])


def dur_of(f):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f],
                                capture_output=True, text=True).stdout)


def main():
    out = sys.argv[1]
    os.makedirs(WORK, exist_ok=True)
    for n in ("hokit_portrait_2026.jpg", "jones_interview.png"):
        Image.open(os.path.join(IMG, n)).convert("RGB").save(os.path.join(WORK, n.split(".")[0] + ".png"))
    run(["ffmpeg", "-y", "-v", "error", "-ss", "4", "-i", os.path.join(CLIPS, "14_hokit_post_fight_LIP.mp4"),
         "-frames:v", "1", os.path.join(WORK, "hokit_frame.png")])
    S = []  # (file, label, [(t, sfx, gain)])

    def add(name, label, sfx, make):
        f = os.path.join(WORK, name + ".mp4")
        if not os.path.exists(f) or os.environ.get("REEL_REDO") in ("1", name):
            make(f)
        S.append((f, label, sfx))

    add("s1", "1 · STAT COUNT-UP", [(0.0, "whoosh", 0.5), (2.05, "bass_drop", 0.7), (2.0, "whoosh", 0.35), (3.3, "click", 0.4)],
        lambda f: custom(f, 6.5, "arena", seg_stat))
    add("s2", "2 · QUOTE REVEAL + HIGHLIGHT", [(0.0, "whoosh", 0.5), (4.0, "pop", 0.4), (5.4, "pop", 0.4)],
        lambda f: custom(f, 7.5, "arena", seg_quote))
    add("s3", "3 · SCREENSHOT PUSH-IN", [(0.0, "whoosh", 0.5)], lambda f: custom(f, 5.0, "arena", seg_xpost))
    add("s4", "4 · NAME INTRO (TEMPLATE)", [(0.0, "whoosh", 0.5)],
        lambda f: template(f, "torn-profile", {"title": "JOSH HOKIT", "subtitle": "10-1 · Former Fresno State wrestler",
                                               "label": "The Challenger", "images": ["hokit_portrait_2026.png"],
                                               "accent": "#C48E16", "background": "#121214"}, 4.5))
    add("s5", "5 · FACE-OFF", [(0.0, "whoosh", 0.5), (0.8, "bass_drop", 0.8)], lambda f: custom(f, 4.5, "arena", seg_faceoff))
    add("s6", "6 · WORD SLAM (TEMPLATE)", [(0.0, "whoosh", 0.4), (0.9, "bass_drop", 0.8)],
        lambda f: template(f, "title-hierarchy", {"title": "ROBBED?", "subtitle": "Alex Pereira thinks Hokit was",
                                                  "backgroundImage": "hokit_frame.png", "foreground": "#f3f1e9"}, 4.5))
    add("s7", "7 · CHAPTER OPENER", [(0.0, "glitch", 0.5), (0.8, "keyboard_typing", 0.5), (4.0, "whoosh", 0.5)],
        lambda f: custom(f, 4.5, "arena", seg_chapter))
    add("s8", "8 · TIMELINE (TEMPLATE)", [(0.0, "whoosh", 0.4)],
        lambda f: template(f, "milestone-path", {"title": "How the beef built",
                                                 "labels": ["Sept: Steveson KO'd", "Oct: The diss track", "Nov 14: UFC 334",
                                                            "Nov 14: Same coaches", "Nov 16: Little man", "Nov 17: Never see gold"],
                                                 "accent": "#C48E16", "secondary": "#C41E1E", "background": "#121214",
                                                 "foreground": "#f3f1e9"}, 8))
    tsfx = []
    add("s9", "9 · TRANSITIONS: GLITCH · FLASH · ZOOM", None, lambda f: tsfx.extend(transitions(f)))
    if S[-1][2] is None:
        S[-1] = (S[-1][0], S[-1][1], tsfx or [(2.85, "glitch", 0.6), (5.65, "camera_flash", 0.6), (8.5, "whoosh", 0.8)])

    tagged, events, t0 = [], [], 0.0
    for i, (f, label, sfx) in enumerate(S):
        o = os.path.join(WORK, f"tag{i}.mp4")
        tag(f, label, o)
        tagged.append(o)
        for t, s, g in sfx:
            events.append((t0 + t, s, g))
        t0 += dur_of(o)
    lst = os.path.join(WORK, "list.txt")
    open(lst, "w").write("".join(f"file '{f}'\n" for f in tagged))
    video = os.path.join(WORK, "video.mp4")
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", video])

    # audio: quiet music bed + sound effects, loudness -14 LUFS
    sr, total = 44100, dur_of(video)
    mix = np.zeros((int(total * sr) + sr, 2), np.float32)
    music = sorted(f for f in os.listdir(os.path.join(ASSETS, "music")) if f.endswith(".mp3"))
    if music:
        raw = subprocess.run(["ffmpeg", "-v", "error", "-stream_loop", "-1", "-i", os.path.join(ASSETS, "music", music[0]),
                              "-t", str(total), "-f", "f32le", "-ac", "2", "-ar", str(sr), "-"], capture_output=True).stdout
        m = np.frombuffer(raw, np.float32).reshape(-1, 2)
        mix[:len(m)] += m * 0.12
    for t, s, g in events:
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", os.path.join(SFX, s + ".wav"), "-f", "f32le", "-ac", "2",
                              "-ar", str(sr), "-"], capture_output=True).stdout
        a = np.frombuffer(raw, np.float32).reshape(-1, 2)
        i = int(t * sr)
        a = a[:len(mix) - i]
        mix[i:i + len(a)] += a * g
    wav = os.path.join(WORK, "mix.wav")
    peak = np.abs(mix).max() or 1
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "f32le", "-ac", "2", "-ar", str(sr), "-i", "-", wav],
                   input=(mix / max(peak, 1.0)).astype(np.float32).tobytes(), check=True)
    run(["ffmpeg", "-y", "-v", "error", "-i", video, "-i", wav, "-c:v", "copy", "-af", "loudnorm=I=-14:TP=-1:LRA=11",
         "-c:a", "aac", "-b:a", "256k", "-shortest", "-movflags", "+faststart", out])
    print("wrote", out, f"{dur_of(out):.1f}s")
    for (f, label, _), o in zip(S, tagged):
        print(f"  {label}: {dur_of(o):.1f}s")


if __name__ == "__main__":
    main()
