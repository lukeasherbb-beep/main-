"""Build the Thompson video from thompson_build.md + sent.json + the voiceover.

Usage: python3 thompson_build.py [--preview]

- Reads the markers in thompson_build.md; each marker fires at the start of the
  narration sentence that follows it (times from build/sent.json).
- CLIP / LET IT PLAY markers look for a file in clips/ whose name starts with the
  clip number (e.g. clips/06_ellenberger.mp4, clips/20a.mp4, clips/20b.mp4).
  * CLIP with no file: falls back to stock B-roll (see FALLBACK).
  * LET IT PLAY with no file: skipped. With a file: narration pauses and the clip
    plays full screen with its own audio.
- FE CARD and FX markers are drawn by tools/fe_cards.py.
Output: build/thompson_draft.mp4 and build/timeline.txt
"""
import glob
import json
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "tools"))
import fe_cards as fc  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps  # noqa: E402

FPS = 30
BUILD = os.path.join(HERE, "build")
SEG = os.path.join(BUILD, "seg")
CLIPS = os.path.join(HERE, "clips")
BROLL = "/home/user/wonderboy-broll/pixabay"
VO = os.path.join(BUILD, "vo.mp3")
LOGO_SECONDS = 4.0
TAIL_SECONDS = 4.0
ENC = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "25", "-pix_fmt", "yuv420p", "-r", str(FPS),
       "-video_track_timescale", "15360", "-an"]

ASSETS = os.path.join(HERE, "..", "assets")
# clip number -> (kicker, headline, sub): Wonderboy-specific card shown while the real clip is missing
MOMENT = {
    0: ("THE FINAL FIGHT", "WONDERBOY", "Age 43 · UFC 334"),
    1: ("2012 – 2026", "STEPHEN THOMPSON", "14 years in the UFC"),
    3: ("SIMPSONVILLE, SOUTH CAROLINA", "UPSTATE KARATE", "His father Ray's school"),
    4: ("UFC 143 · FEB 4, 2012", "UFC DEBUT", "Knockout win"),
    5: ("UFC 170 · 2014", "WHITTAKER", "TKO · Round 1"),
    6: ("TUF 21 FINALE · JULY 12, 2015", "ELLENBERGER", "Spinning wheel kick KO · Round 1"),
    7: ("FEBRUARY 2016", "HENDRICKS", "TKO · Round 1"),
    8: ("JUNE 2016", "MACDONALD", "Unanimous decision"),
    9: ("UFC 205 · NOV 12, 2016", "WOODLEY VS THOMPSON", "Welterweight title fight"),
    10: ("UFC 209 · MARCH 2017", "THE REMATCH", "Woodley by majority decision"),
    11: ("UFC 217 · NOV 2017", "MASVIDAL", "Thompson wins"),
    13: ("UFC 307 · OCT 2024", "BUCKLEY", "Knockout loss"),
    14: ("FATHERHOOD", "A BABY GIRL", "About five months old on fight night"),
    15: ("UPSTATE KARATE", "THE KIDS' PROGRAM", "Simpsonville, South Carolina"),
    16: ("NOV 14, 2026", "UFC 334", "Madison Square Garden"),
    17: ("THE OPPONENT", "CHARLES RADTKE", "12-5 · 5-2 in the UFC"),
    18: ("UFC 334 · ROUND 1", "TAKEDOWN", "Radtke gets him down inside a minute"),
    22: ("UFC 334", "GLOVES DOWN", "Left in the center of the octagon"),
    27: ("UFC ORLANDO · DEC 2022", "HOLLAND", "Corner stoppage after Round 4"),
    28: ("UFC 296 · DEC 2023", "RAKHMONOV", "Rear-naked choke"),
    29: ("UFC NASHVILLE · JULY 2025", "BONFIM", "Split decision loss"),
    30: ("UFC 334 · ROUND 2", "THE BODY KICK", "The fight turns"),
}
IMAGES = os.path.join(HERE, "images")
INTRO = os.path.join(ASSETS, "fe_logo_intro.mp4")
GOLD = (196, 142, 22)
# card backgrounds rotate by chapter; clips use the pairing (wide, square, vertical)
BG_ORDER = ["torn_split", "brush_chevrons", "gradient_streak", "torn_panels"]
# FE CARD / FX markers that become photo cards (key found in the marker -> one or more shots)
PHOTOS = [
    ('T("WONDERBOY")', [{"layout": "single", "img": "img1_thompson_stance.jpg",
                         "kicker": "STEPHEN THOMPSON", "title": "WONDERBOY"}]),
    ("paired-profiles", [{"layout": "pair", "items": [
        ("img2_weidman.png", "BROTHER TONY'S BROTHER-IN-LAW", "CHRIS WEIDMAN"),
        ("img3_machado.jpg", "SISTER LINDSAY'S HUSBAND · HIS BJJ COACH", "CARLOS MACHADO")]}]),
    ("quote-profile", [{"layout": "quote", "img": "img4_thompson_portrait.jpg",
                        "quote": "I don't see the title anymore.", "attr": "STEPHEN THOMPSON TO ARIEL HELWANI"}]),
    ('T("THE NMF")', [{"layout": "single", "img": "img5b_nmf_belt_closeup.jpg",
                       "kicker": "ARIEL HELWANI · 2019", "title": "THE NMF BELT"},
                      {"layout": "single", "img": "img5_helwani_belt_handoff.jpg",
                       "kicker": "THE ARIEL HELWANI MMA SHOW", "title": "NICEST MAN IN MMA"}]),
]
F_TITLE = "/usr/share/fonts/opentype/inter/InterDisplay-BlackItalic.otf"
F_KICK = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
F_QUOTE = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
# (unused now) clip number -> stock B-roll file numbers
FALLBACK = {1: [2], 3: [1, 2], 4: [17], 5: [3], 6: [4], 7: [18], 8: [3], 9: [8, 9], 10: [11], 11: [4],
            13: [19], 14: [13], 15: [1], 16: [6], 17: [17], 18: [5, 16], 22: [14], 26: [14],
            27: [3], 28: [18], 29: [7], 30: [5]}
# source labels shown on real clips (readable on mobile)
LABELS = {2: "UFC 334 · Nov 14, 2026", 4: "UFC 143 · Feb 2012", 5: "UFC 170 · Feb 2014",
          6: "TUF 21 Finale · July 2015", 7: "UFC Fight Night · Feb 2016", 8: "UFC Fight Night · June 2016",
          9: "UFC 205 · Nov 2016", 10: "UFC 209 · March 2017", 11: "UFC 217 · Nov 2017",
          12: "UFC Nashville · March 2019", 13: "UFC 307 · Oct 2024", 16: "UFC 334 walkout · Nov 14, 2026", 17: "UFC 334 weigh-ins · Nov 2026",
          18: "UFC 334 · Round 1", 20: "UFC 334 · Round 3", 21: "UFC 334 · Round 3",
          22: "UFC 334 · Nov 14, 2026", 23: "UFC 334 · Nov 14, 2026", 24: "UFC 334 · Nov 14, 2026",
          25: "UFC 334 broadcast", 26: "UFC 334 · Nov 14, 2026", 27: "UFC Orlando · Dec 2022",
          28: "UFC 296 · Dec 2023", 29: "UFC Nashville · July 2025", 30: "UFC 334 · Round 2"}


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        sys.exit("ffmpeg failed:\n" + " ".join(cmd) + "\n" + r.stderr[-1500:])


def aspect(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=width,height:stream_side_data=rotation", "-of", "json", path],
                         capture_output=True, text=True).stdout
    st = json.loads(out)["streams"][0]
    w, h = st["width"], st["height"]
    rot = abs(int(st.get("side_data_list", [{}])[0].get("rotation", 0)))
    return (h / w) if rot in (90, 270) else (w / h)


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type",
                          "-of", "json", path], capture_output=True, text=True).stdout
    j = json.loads(out)
    return float(j["format"]["duration"]), any(s["codec_type"] == "audio" for s in j["streams"])


# ---------- parse the build script ----------
def split_sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s.strip()]


def parse_markers(md_path, sents):
    body = open(md_path).read().split("\n---\n")[0].splitlines()[1:]
    groups, pending, idx = [], [], 0
    for line in body:
        line = line.strip()
        if not line:
            continue
        if line.startswith("["):
            pending.append(line)
            continue
        if pending:
            groups.append((idx, pending))
            pending = []
        for s in split_sentences(line):
            assert sents[idx]["text"] == s, f"script/alignment mismatch at sentence {idx}: {s[:50]}"
            idx += 1
    assert idx == len(sents), (idx, len(sents))
    if pending:
        groups.append((idx, pending))  # after the last sentence
    return groups


def call_args(text):
    """Return the balanced '(...)' call that starts the text, e.g. T("X", sub="Y")."""
    depth, in_str = 0, None
    for i, c in enumerate(text):
        if in_str:
            if c == in_str and text[i - 1] != "\\":
                in_str = None
        elif c in "\"'":
            in_str = c
        elif c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return text[:i + 1]
    raise ValueError(text)


def card_image(marker, dark):
    style = "dark" if dark or "dark" in marker.split("]")[-1].lower() else None
    if marker.startswith("[FE LOGO COVER"):
        return fc.logo_cover()
    if marker.startswith("[FE CARD:"):
        src = marker[len("[FE CARD:"):].strip()
        call = call_args(src)
        tail = src[len(call):].lower()
        if "dark" in tail or "black" in tail:
            style = "dark"
        fn = call[:call.index("(")]
        default = {"T": "gold", "S": "gold", "Q": "dark", "V": "dark", "TL": "dark", "Ls": "dark"}[fn]
        env = {k: getattr(fc, k) for k in ("T", "S", "Q", "V", "TL", "Ls")}
        return eval(call[:-1] + f", style={(style or default)!r})", {"__builtins__": {}}, env)
    m = re.match(r"\[FX: ([\w-]+) — (.*)$", marker)
    name, text = m.group(1), m.group(2)
    text = text[:text.rindex("]")]
    if name == "chapter-number":
        num, title = text.split(" · ", 1)
        return fc.chapter(num, title, style or "gold")
    if name == "territory-date":
        place, date = text.rsplit(" · ", 1)
        return fc.place_date(place, date, style or "dark")
    if name == "paired-profiles":
        items = [re.match(r"(.*?) \((.*)\)$", x.strip()).groups() for x in text.split(" · ")]
        return fc.pairs(items, "THE FAMILY BUSINESS", style or "dark")
    if name == "icon-bullets":
        return fc.Ls(None, [x.strip().upper() for x in text.split(" · ")], style or "dark")
    if name == "quote-profile":
        q, attr = re.match(r'"(.*)" — (.*)$', text).groups()
        return fc.Q(q, attr, style or "dark")
    if name == "two-bars":
        sections = []
        for sec in text.split(" / "):
            title, rest = sec.split(": ", 1)
            sections.append((title, [tuple(x.strip().rsplit(" ", 1)) for x in rest.split(" · ")]))
        return fc.bars(sections, style or "dark")
    if name == "stacked-highlight":
        a, b = text.split(" / ")
        return fc.stacked(a, b, style or "dark")
    raise ValueError(marker)


def clip_number(marker):
    return int(re.search(r"#(\d+)", marker).group(1))


def find_clips(n, letplay=False):
    """Files for clip number n. LET IT PLAY slots only take files with "lip" in the name
    (e.g. 09_r4_lip.mp4); plain files only fill narrated CLIP slots."""
    files = sorted(f for f in glob.glob(os.path.join(CLIPS, "*"))
                   if re.match(rf"^0*{n}(\D|$)", os.path.basename(f)))
    return [f for f in files if ("lip" in os.path.basename(f).lower()) == letplay]


def broll_file(num):
    return glob.glob(os.path.join(BROLL, f"{num:02d}-*.mp4"))[0]


# ---------- plan ----------
def plan(sents, groups, vo_dur):
    """Return items: ('narr', t0, t1, visual) and ('brk', seconds, visual). Times in narration seconds."""
    q = lambda t: round(t * FPS) / FPS
    used, broll_used, missing = {}, {}, []
    beats = []  # (time, [breaks], [visuals])
    dark = False
    chapter = 0
    for idx, markers in groups:
        t = vo_dur if idx >= len(sents) else (0.0 if idx == 0 else q(max(sents[idx]["start"] - 0.12, 0)))
        breaks, visuals = [], []
        for mk in markers:
            if "THE HARD YEARS" in mk:
                dark = True
            if "WONDERDAD" in mk and "chapter-number" in mk:
                dark = False
            if "chapter-number" in mk:
                chapter += 1
            bg = BG_ORDER[chapter % len(BG_ORDER)]
            if mk.startswith("[CLIP:") or mk.startswith("[LET IT PLAY:"):
                n = clip_number(mk)
                letplay = mk.startswith("[LET IT PLAY:")
                files = find_clips(n, letplay)
                if files:
                    f = files[used.get(n, 0) % len(files)]
                    used[n] = used.get(n, 0) + 1
                    v = {"kind": "clip", "file": f, "label": LABELS.get(n), "n": n, "desc": mk, "bg": bg, "dark": dark}
                    if letplay:
                        secs = float(re.search(r"— (\d+)s", mk).group(1))
                        breaks.append((min(secs, probe(f)[0]), v))
                    else:
                        visuals.append(v)
                else:
                    missing.append(mk)
                    if not letplay:
                        visuals.append({"kind": "card", "moment": n, "marker": "", "dark": dark, "desc": mk, "bg": bg})
            else:
                photos = next((specs for key, specs in PHOTOS if key in mk), None)
                if photos:
                    for spec in photos:
                        visuals.append({"kind": "card", "photo": spec, "marker": mk, "dark": dark, "desc": mk, "bg": bg})
                else:
                    visuals.append({"kind": "card", "marker": mk, "dark": dark, "desc": mk, "bg": bg})
        beats.append((t, breaks, visuals))
    items = []
    last_visual = None
    for i, (t, breaks, visuals) in enumerate(beats):
        t_next = beats[i + 1][0] if i + 1 < len(beats) else vo_dur
        if i == 0 and visuals and "LOGO" in visuals[0].get("marker", ""):
            items.append(("intro", LOGO_SECONDS, visuals.pop(0)))  # logo intro with its riser, before any narration
            if not visuals:
                visuals = [{"kind": "card", "moment": 0, "marker": "", "dark": False, "desc": "(opening card)", "bg": BG_ORDER[0]}]
        for secs, v in breaks:
            items.append(("brk", q(secs), v))
        if t >= vo_dur:  # markers after the last sentence: end card over a silent tail
            for v in visuals:
                items.append(("tail", TAIL_SECONDS, v))
            continue
        if not visuals:
            visuals = [last_visual]
        span = (t_next - t) / len(visuals)
        for k, v in enumerate(visuals):
            items.append(("narr", q(t + k * span), q(t + (k + 1) * span) if k + 1 < len(visuals) else t_next, v))
            last_visual = v
    return items, missing


# ---------- Faceless Studio templates ----------
FX_RENDER = os.path.join(HERE, "..", "fx", "effects", "render_effect.mjs")
FX_MAX = {"chapter-number": 12, "territory-date": 24}


def fx_spec(v):
    """(effect id, overrides) when this card should use a Faceless Studio template, else None."""
    m = re.match(r"\[FX: (chapter-number|territory-date) — (.*)$", v.get("marker", ""))
    if not m:
        return None
    name, text = m.group(1), m.group(2)
    text = text[:text.rindex("]")]
    if name == "chapter-number":
        num, title = text.split(" · ", 1)
        dark = v["dark"]  # gold for chapter headings, dark for the serious chapter
        return name, {"chapter": str(int(num)), "title": title, "subtitle": "",
                      "background": "#0e0e10" if dark else "#C48E16", "foreground": "#C48E16" if dark else "#0e0e10"}
    place, date = text.rsplit(" · ", 1)
    return name, {"title": date, "subtitle": place.title(), "accent": "#C48E16",
                  "country": "United States of America", "points": [[-82.25, 34.74]], "pointLabels": ["Simpsonville, SC"]}


def render_fx(i, frames, spec, out):
    name, overrides = spec
    dur = frames / FPS
    fx_dur = max(min(dur, FX_MAX[name]), 4 if name == "territory-date" else 2)
    js, raw = os.path.join(SEG, f"{i:03d}_fx.json"), os.path.join(SEG, f"{i:03d}_fx.mp4")
    json.dump(overrides, open(js, "w"))
    run(["node", FX_RENDER, "--id", name, "--overrides", js, "--duration", f"{fx_dur:.3f}", "--out", raw])
    ov = os.path.join(SEG, f"{i:03d}_ov.png")
    fc.overlay(None).save(ov)
    fcx = f"[0:v]fps={FPS},setsar=1,tpad=stop_mode=clone:stop_duration={max(dur - fx_dur, 0) + 1:.2f}[v];[v][1:v]overlay=0:0[o]"
    run(["ffmpeg", "-y", "-v", "error", "-i", raw, "-i", ov, "-filter_complex", fcx, "-map", "[o]",
         "-frames:v", str(frames)] + ENC + [out])
    return out


# ---------- boxes, shadows, photo cards ----------
def bg_path(name):
    return os.path.join(ASSETS, f"bg_{name}.mp4")


def add_shadow(canvas, box, offset=(14, 18), blur=18, alpha=170):
    """Soft drop shadow under a box (x0, y0, x1, y1) on an RGBA canvas."""
    sh = Image.new("L", canvas.size)
    x0, y0, x1, y1 = box
    ImageDraw.Draw(sh).rectangle([x0 + offset[0], y0 + offset[1], x1 + offset[0], y1 + offset[1]], fill=alpha)
    sh = sh.filter(ImageFilter.GaussianBlur(blur))
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    layer.putalpha(sh)
    return Image.alpha_composite(layer, canvas)


def load_photo(name):
    im = Image.open(os.path.join(IMAGES, name))
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        white = Image.new("RGBA", im.size, (255, 255, 255, 255))
        im = Image.alpha_composite(white, im)
    im = im.convert("RGB")
    if name.startswith("img2_weidman"):  # trim the rounded cut-outs in the corners
        im = im.crop((95, 0, 425, im.height))
    return im


def framed_photo(canvas, im, x, y, w, h, centering=(0.5, 0.35)):
    """Paste a photo, cover-cropped to w x h, with the gold frame and a shadow."""
    canvas = add_shadow(canvas, (x, y, x + w + 16, y + h + 16))
    frame = Image.new("RGBA", (w + 16, h + 16), GOLD + (255,))
    frame.paste(ImageOps.fit(im, (w, h), Image.LANCZOS, centering=centering), (8, 8))
    canvas.paste(frame, (x, y))
    return canvas


def caption_bar(canvas, x, y, kicker, title, max_w, size=84):
    """Lower-third style caption: black bar, gold stripe, gold kicker, white italic title."""
    d = ImageDraw.Draw(canvas)
    while size > 40 and d.textlength(title, font=ImageFont.truetype(F_TITLE, size)) > max_w - 70:
        size -= 4
    ft, fk = ImageFont.truetype(F_TITLE, size), ImageFont.truetype(F_KICK, 30)
    w = int(max(d.textlength(title, font=ft), d.textlength(kicker, font=fk) + 4 * len(kicker))) + 76
    h = int(size * 1.15) + (52 if kicker else 18)
    bar = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    bd = ImageDraw.Draw(bar)
    bd.rectangle([x, y, x + w, y + h], fill=(10, 10, 12, 240))
    bd.rectangle([x, y, x + 12, y + h], fill=GOLD + (255,))
    canvas = add_shadow(canvas, (x, y, x + w, y + h), blur=12, alpha=140)
    canvas = Image.alpha_composite(canvas, bar)
    d = ImageDraw.Draw(canvas)
    if kicker:
        cx = x + 40
        for ch in kicker:  # letter-spaced kicker
            d.text((cx, y + 18), ch, font=fk, fill=GOLD)
            cx += d.textlength(ch, font=fk) + 4
    d.text((x + 38, y + (48 if kicker else 8)), title, font=ft, fill=(245, 245, 245))
    return canvas


def photo_overlay(spec):
    """Full-frame RGBA overlay for a photo card (framed photos + captions); the background shows through."""
    c = Image.new("RGBA", (1920, 1080), (0, 0, 0, 0))
    if spec["layout"] == "single":
        im = load_photo(spec["img"])
        if im.width / im.height < 1:  # portrait photo: left, caption beside it
            h = 820
            w = int(h * im.width / im.height)
            c = framed_photo(c, im, 300, 100, w, h)
            c = caption_bar(c, 300 + w - 30, 640, spec["kicker"], spec["title"], 960, 110)
        else:
            w = 1280
            h = int(w * im.height / im.width)
            c = framed_photo(c, im, (1920 - w - 16) // 2, 70, w, h)
            c = caption_bar(c, (1920 - w) // 2 - 70, 70 + h - 60, spec["kicker"], spec["title"], 1100)
    elif spec["layout"] == "pair":
        for k, (img, kicker, title) in enumerate(spec["items"]):
            x = (300, 1020)[k]
            c = framed_photo(c, load_photo(img), x, 110, 600, 600, (0.5, 0.25))
            c = caption_bar(c, x - 30, 650, kicker, title, 700, 70)
    elif spec["layout"] == "quote":
        im = load_photo(spec["img"])
        c = framed_photo(c, im, 130, 200, 860, int(860 * im.height / im.width))
        panel = Image.new("RGBA", c.size, (0, 0, 0, 0))
        pd = ImageDraw.Draw(panel)
        x0, y0, x1, y1 = 960, 300, 1800, 800
        c = add_shadow(c, (x0, y0, x1, y1))
        pd.rectangle([x0, y0, x1, y1], fill=(10, 10, 12, 240), outline=GOLD + (255,), width=6)
        c = Image.alpha_composite(c, panel)
        d = ImageDraw.Draw(c)
        d.text((x0 + 50, y0 - 40), "\u201c", font=ImageFont.truetype(F_TITLE, 220), fill=GOLD)
        fq = ImageFont.truetype(F_QUOTE, 74)
        words, lines, cur = spec["quote"].split(), [], ""
        for wd in words:
            t = (cur + " " + wd).strip()
            if d.textlength(t, font=fq) <= x1 - x0 - 140 or not cur:
                cur = t
            else:
                lines.append(cur)
                cur = wd
        lines.append(cur)
        ty = y0 + 170
        for ln in lines:
            d.text((x0 + 70, ty), ln, font=fq, fill=(245, 245, 245))
            ty += 92
        d.rectangle([x0 + 70, ty + 24, x0 + 170, ty + 30], fill=GOLD)
        d.text((x0 + 70, ty + 50), spec["attr"], font=ImageFont.truetype(F_KICK, 32), fill=GOLD)
    return c


def whip_overlay(i, frames, bg, png, x0, y0, out, side):
    """Overlay a still (box or full-frame RGBA) that whips in from the side over a looping background."""
    fcx = (f"[0:v]fps={FPS},setsar=1[b];[b][1:v]overlay=x='{x0}+{side}*1900*pow(1-min(t/0.35\\,1)\\,3)':y={y0}[o]")
    run(["ffmpeg", "-y", "-v", "error", "-stream_loop", "-1", "-ss", f"{(i * 3.7) % 7.5:.2f}", "-i", bg, "-loop", "1",
         "-i", png, "-filter_complex", fcx, "-map", "[o]", "-frames:v", str(frames)] + ENC + [out])


# ---------- render ----------
def box_scale(v, i):
    """Card box size as a fraction of the frame: data-heavy cards big, titles/quotes/moments smaller."""
    if "moment" in v:
        return (0.70, 0.80, 0.74)[v["moment"] % 3]
    m = v.get("marker", "")
    fn = re.match(r"\[(?:FE CARD: ?(\w+)|FX: ([\w-]+))", m)
    kind = (fn.group(1) or fn.group(2)) if fn else ""
    if kind in ("S", "TL", "Ls", "bars", "pairs", "stacked"):
        return 0.80 if kind == "S" and i % 2 else 0.86
    if kind == "V":
        return 0.82
    if kind == "Q":
        return 0.72
    return (0.78, 0.68, 0.74)[i % 3]


def render_logo(i, frames, png, out):
    """Real FE logo straight on the octagon background: black keyed out, scales up into place."""
    logo = Image.open(os.path.join(ASSETS, "logo_square.png")).convert("RGB").resize((760, 760), Image.LANCZOS)
    a = np.asarray(logo, dtype=np.float32)
    alpha = np.clip((a.max(axis=2) - 18) * 3.0, 0, 255).astype(np.uint8)
    Image.fromarray(np.dstack([a.astype(np.uint8), alpha]), "RGBA").save(png)
    fcx = (f"[1:v]scale=w='760*(0.82+0.18*min(t/0.6\\,1))':h=-1:eval=frame[l];"
           f"[0:v]fps={FPS},setsar=1[b];[b][l]overlay=x='(W-w)/2':y='(H-h)/2'[o]")
    run(["ffmpeg", "-y", "-v", "error", "-stream_loop", "-1", "-i", os.path.join(ASSETS, "bg_dark.mp4"),
         "-loop", "1", "-i", png, "-filter_complex", fcx, "-map", "[o]", "-frames:v", str(frames)] + ENC + [out])
    return out


def render_item(args):
    i, kind, frames, v, offset, with_audio = args
    out = os.path.join(SEG, f"{i:03d}.mp4")
    dur = frames / FPS
    if kind == "intro":
        run(["ffmpeg", "-y", "-v", "error", "-i", INTRO, "-vf", f"fps={FPS},setsar=1,tpad=stop_mode=clone:stop_duration=1",
             "-frames:v", str(frames)] + ENC + [out])
        return out, None
    if v["kind"] == "card":
        spec = fx_spec(v)
        if spec:
            return render_fx(i, frames, spec, out), None
        png = os.path.join(SEG, f"{i:03d}.png")
        bg = bg_path(v.get("bg", BG_ORDER[0]))
        side = 1 if i % 2 else -1  # boxes whip in from alternating sides over the moving background
        if "photo" in v:
            photo_overlay(v["photo"]).save(png)
            whip_overlay(i, frames, bg, png, 0, 0, out, side)
            return out, None
        if "moment" in v:
            k, head, sub = MOMENT[v["moment"]]
            card = fc.T(head, sub=sub, kicker=k, style="dark")
        else:
            card = card_image(v["marker"], v["dark"])
        s = box_scale(v, i)
        cw, ch = int(1920 * s) // 2 * 2, int(1080 * s) // 2 * 2
        x0 = (1920 - cw - 16) // 2
        if s < 0.8:  # smaller boxes sit off-center so the layout doesn't repeat
            x0 += side * 150
        y0 = (1080 - ch - 16) // 2
        canvas = add_shadow(Image.new("RGBA", (1920, 1080), (0, 0, 0, 0)), (x0, y0, x0 + cw + 16, y0 + ch + 16))
        panel = Image.new("RGBA", (cw + 16, ch + 16), GOLD + (255,))  # gold frame around the card
        panel.paste(card.resize((cw, ch), Image.LANCZOS), (8, 8))
        canvas.paste(panel, (x0, y0))
        canvas.save(png)
        whip_overlay(i, frames, bg, png, 0, 0, out, side)
    else:
        ov = os.path.join(SEG, f"{i:03d}_ov.png")
        fc.overlay(v.get("label") if v["kind"] == "clip" else None, watermark=False).save(ov)  # the background carries the logo badge
        src_dur = probe(v["file"])[0]
        start = offset % max(src_dur - 0.5, 0.1) if src_dur > dur + 0.5 else 0
        # every clip sits in a gold-framed box with a shadow on the moving background
        a = aspect(v["file"])
        if a >= 1.5:
            bw = (1500, 1340, 1420)[i % 3]
            bh = int(bw / a) // 2 * 2
            bgname = "torn_split"
        else:
            bh = (900, 860, 880)[i % 3] if a < 0.9 else 820
            bw = int(bh * a) // 2 * 2
            bgname = "torn_panels" if a < 0.9 else "brush_chevrons"
        x0, y0 = (1920 - bw - 16) // 2, (1080 - bh - 16) // 2
        sh = os.path.join(SEG, f"{i:03d}_sh.png")
        add_shadow(Image.new("RGBA", (1920, 1080), (0, 0, 0, 0)), (x0, y0, x0 + bw + 16, y0 + bh + 16)).save(sh)
        side = 1 if i % 2 else -1
        whip = f"{side}*1900*pow(1-min(t/0.35\\,1)\\,3)"
        fcx = (f"[0:v]scale={bw}:{bh},fps={FPS},setsar=1,pad=iw+16:ih+16:8:8:color=0xC48E16[v];"
               f"[2:v]fps={FPS},setsar=1[b];[b][3:v]overlay=x='{whip}':y=0[bs];"
               f"[bs][v]overlay=x='{x0}+{whip}':y={y0}[bv];[bv][1:v]overlay=0:0[o]")
        run(["ffmpeg", "-y", "-v", "error", "-stream_loop", "-1", "-ss", f"{start:.3f}", "-i", v["file"],
             "-i", ov, "-stream_loop", "-1", "-i", bg_path(bgname), "-loop", "1", "-i", sh,
             "-filter_complex", fcx, "-map", "[o]", "-frames:v", str(frames)] + ENC + [out])
    wav = None
    if with_audio:  # LET IT PLAY: keep the clip's own audio
        wav = os.path.join(SEG, f"{i:03d}.wav")
        if probe(v["file"])[1]:
            run(["ffmpeg", "-y", "-v", "error", "-i", v["file"], "-t", f"{dur:.3f}", "-vn", "-ac", "2", "-ar", "44100",
                 "-af", f"afade=in:st=0:d=0.15,afade=out:st={max(dur - 0.25, 0):.3f}:d=0.25,apad,atrim=0:{dur:.3f}", wav])
        else:
            run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-t", f"{dur:.3f}", wav])
    return out, wav


def load_wav(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "2", "-ar", "44100", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).copy()


def mix_sfx(audio_path, events):
    """Lay transition sound effects (assets/sfx/<name>.wav) over the finished audio track in place."""
    track = load_wav(audio_path)
    cache = {}
    for t, name, gain in events:
        if name not in cache:
            cache[name] = load_wav(os.path.join(ASSETS, "sfx", f"{name}.wav"))
        fx = cache[name] * gain
        a = int(t * 44100)
        b = min(a + len(fx), len(track))
        if a < b:
            track[a:b] += fx[:b - a]
    np.clip(track, -1, 1, out=track)
    p = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "f32le", "-ac", "2", "-ar", "44100", "-i", "-",
                          "-c:a", "pcm_s16le", audio_path], stdin=subprocess.PIPE)
    p.communicate(track.tobytes())


def fit_clips(items):
    """A narrated clip slot longer than the footage left in its file plays what's left, then a card
    covers the rest (no looping). Footage is used in order across a clip's slots."""
    out, used = [], {}
    for it in items:
        if it[0] != "narr" or it[3]["kind"] != "clip":
            out.append(it)
            continue
        _, t0, t1, v = it
        f = v["file"]
        left = probe(f)[0] - used.get(f, 0.0) - 0.1
        slot = t1 - t0
        card = {"kind": "card", "moment": v["n"], "marker": "", "dark": v.get("dark", False),
                "desc": v["desc"] + " (card after footage ran out)", "bg": v.get("bg", BG_ORDER[0])}
        if v["n"] not in MOMENT:
            card["moment"] = 1
        if left + 0.4 >= slot:  # a few frames short is fine; the last frames repeat
            out.append(it)
            used[f] = used.get(f, 0.0) + slot
        elif left >= 2.5:
            cut = round((t0 + left) * FPS) / FPS
            out.append(("narr", t0, cut, v))
            out.append(("narr", cut, t1, card))
            used[f] = used.get(f, 0.0) + left
        else:
            out.append(("narr", t0, t1, card))
    return out


def main():
    preview = "--preview" in sys.argv
    os.makedirs(SEG, exist_ok=True)
    os.makedirs(CLIPS, exist_ok=True)
    sents = json.load(open(os.path.join(BUILD, "sent.json")))
    vo_dur = probe(VO)[0]
    groups = parse_markers(os.path.join(HERE, "thompson_build.md"), sents)
    items, missing = plan(sents, groups, vo_dur)
    items = fit_clips(items)
    if preview:
        items = [it for it in items if it[0] != "narr" or it[1] < 60]

    jobs, audio_parts, log, out_t, offsets, sfx = [], [], [], 0.0, {}, []
    for i, it in enumerate(items):
        if it[0] == "narr":
            _, t0, t1, v = it
            frames = round(t1 * FPS) - round(t0 * FPS)
            audio_parts.append(("vo", t0, t1))
        else:
            _, secs, v = it
            frames = round(secs * FPS)
            audio_parts.append(("clip", i) if it[0] == "brk" else ("intro", secs) if it[0] == "intro" else ("silence", secs))
        if frames <= 0:
            continue
        off = offsets.get(v.get("file"), 0.0)
        if v["kind"] != "card":
            offsets[v["file"]] = off + frames / FPS
        jobs.append((i, it[0], frames, v, off, it[0] == "brk"))
        if out_t > 0.05:  # every visual change: whoosh as it flies in, pop when a boxed card lands
            sfx.append((max(out_t - 0.05, 0), "whoosh", 0.45))
            boxed = v["kind"] == "card" and not fx_spec(v) and not v.get("marker", "").startswith("[FE LOGO COVER")
            if boxed:
                sfx.append((out_t + 0.30, "pop", 0.35))
        log.append(f"{int(out_t // 60)}:{out_t % 60:05.2f}  {frames / FPS:6.2f}s  {it[0]:4}  {v['kind']:5}  {v['desc'][:90]}")
        out_t += frames / FPS
    open(os.path.join(BUILD, "timeline.txt"), "w").write("\n".join(log) + "\n")
    longest = max(j[2] for j in jobs) / FPS
    print(f"{len(jobs)} segments, {out_t / 60:.2f} min, longest single shot {longest:.1f}s, "
          f"{len(missing)} clip markers without a file")

    with ThreadPoolExecutor(3) as ex:
        results = list(ex.map(render_item, jobs))

    # video
    lst = os.path.join(SEG, "list.txt")
    open(lst, "w").write("".join(f"file '{o}'\n" for o, _ in results))
    silent = os.path.join(BUILD, "video_only.mp4")
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", silent])

    # audio: narration pieces, clip audio at LET IT PLAY breaks, silent tail
    wavs = {j[0]: w for j, (_, w) in zip(jobs, results)}
    merged, parts = [], []
    for p in audio_parts:  # merge consecutive narration pieces
        if p[0] == "vo" and merged and merged[-1][0] == "vo" and abs(merged[-1][2] - p[1]) < 1e-6:
            merged[-1] = ("vo", merged[-1][1], p[2])
        else:
            merged.append(p)
    for k, p in enumerate(merged):
        w = os.path.join(SEG, f"a{k:03d}.wav")
        if p[0] == "vo":
            run(["ffmpeg", "-y", "-v", "error", "-ss", f"{p[1]:.4f}", "-t", f"{p[2] - p[1]:.4f}", "-i", VO,
                 "-ac", "2", "-ar", "44100", w])
        elif p[0] == "intro":
            run(["ffmpeg", "-y", "-v", "error", "-i", INTRO, "-vn", "-ac", "2", "-ar", "44100",
                 "-af", f"apad,atrim=0:{p[1]:.3f}", w])
        elif p[0] == "silence":
            run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-t", f"{p[1]:.3f}", w])
        else:
            w = wavs[p[1]]
        parts.append(w)
    alst = os.path.join(SEG, "alist.txt")
    open(alst, "w").write("".join(f"file '{w}'\n" for w in parts))
    audio = os.path.join(BUILD, "audio.wav")
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", alst, "-c:a", "pcm_s16le", audio])
    mix_sfx(audio, sfx)

    final = os.path.join(BUILD, "thompson_preview.mp4" if preview else "thompson_draft.mp4")
    run(["ffmpeg", "-y", "-v", "error", "-i", silent, "-i", audio, "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
         "-movflags", "+faststart", final])
    print("wrote", final, f"{probe(final)[0]:.1f}s")
    if missing:
        open(os.path.join(BUILD, "missing_clips.txt"), "w").write("\n".join(missing) + "\n")


if __name__ == "__main__":
    main()
