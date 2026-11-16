"""Fight Era card renderer (PIL). Each function returns a 1920x1080 RGB image.

Stand-in for the original build7.py / Faceless Studio templates until those are uploaded.
Styles: "gold" (chapter headings, major numbers) and "dark" (setbacks, serious passages).
"""
import os
import re
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")

W, H = 1920, 1080
GOLD = (196, 142, 22)  # #C48E16
FONT_X = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
FONT_B = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
FONT_S = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"
PAL = {
    "dark": dict(bg=(11, 11, 13), fg=(245, 245, 245), accent=GOLD, dim=(150, 150, 155), panel=(26, 26, 30)),
    "gold": dict(bg=GOLD, fg=(14, 14, 14), accent=(14, 14, 14), dim=(70, 50, 8), panel=(214, 163, 48)),
}
WATERMARK = "© FightEraTv"


def font(path, size):
    return ImageFont.truetype(path, size)


def tw(d, text, f, spacing=0):
    if spacing:
        return sum(d.textlength(c, font=f) for c in text) + spacing * (len(text) - 1)
    return d.textlength(text, font=f)


def wrap(d, text, f, max_w):
    lines, cur = [], ""
    for word in text.split():
        t = (cur + " " + word).strip()
        if d.textlength(t, font=f) <= max_w or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def fit(d, text, path, max_w, max_h, hi, lo=36, max_lines=4):
    """Largest font size at which the wrapped text fits the box."""
    for size in range(hi, lo - 1, -4):
        f = font(path, size)
        lines = wrap(d, text, f, max_w)
        if len(lines) <= max_lines and all(d.textlength(l, font=f) <= max_w for l in lines) \
                and len(lines) * size * 1.12 <= max_h:
            return f, lines
    f = font(path, lo)
    return f, wrap(d, text, f, max_w)


def spaced(d, xy, text, f, fill, spacing=6, anchor="l"):
    x, y = xy
    total = tw(d, text, f, spacing)
    if anchor == "m":
        x -= total / 2
    elif anchor == "r":
        x -= total
    for c in text:
        d.text((x, y), c, font=f, fill=fill)
        x += d.textlength(c, font=f) + spacing


def block(d, lines, f, cx, cy, fill, lh=1.12):
    """Draw centered lines around (cx, cy)."""
    step = f.size * lh
    y = cy - step * len(lines) / 2
    for l in lines:
        d.text((cx, y + step / 2), l, font=f, fill=fill, anchor="mm")
        y += step


def base(style="dark", kicker=None):
    p = PAL[style]
    im = Image.new("RGB", (W, H), p["bg"])
    glow = Image.new("RGB", (W, H), p["bg"])
    gd = ImageDraw.Draw(glow)
    if style == "dark":
        gd.ellipse((W // 2 - 900, H // 2 - 520, W // 2 + 900, H // 2 + 520), fill=(52, 38, 8))
    else:
        gd.ellipse((W // 2 - 1000, H // 2 - 600, W // 2 + 1000, H // 2 + 600), fill=(206, 152, 32))
    im = Image.blend(im, glow.filter(ImageFilter.GaussianBlur(220)), 0.9)
    d = ImageDraw.Draw(im)
    d.rectangle((60, 60, W - 60, H - 60), outline=p["accent"], width=3)
    d.rectangle((60, 60, 260, 72), fill=p["accent"])
    d.rectangle((W - 260, H - 72, W - 60, H - 60), fill=p["accent"])
    spaced(d, (100, H - 128), "FIGHT ERA", font(FONT_X, 30), p["accent"], spacing=8)
    d.text((W - 100, H - 112), WATERMARK, font=font(FONT_S, 30), fill=p["dim"], anchor="rm")
    if kicker:
        spaced(d, (W // 2, 128), kicker.upper(), font(FONT_B, 44), p["accent"], spacing=10, anchor="m")
        d.rectangle((W // 2 - 60, 204, W // 2 + 60, 210), fill=p["accent"])
    return im, d, p


def T(head, sub=None, kicker=None, style="gold"):
    im, d, p = base(style, kicker)
    box_h = 520 if sub else 640
    f, lines = fit(d, head, FONT_X, 1560, box_h, 300, 80, 3)
    cy = 520 if sub else 540
    block(d, lines, f, W // 2, cy, p["fg"] if style == "gold" else GOLD)
    if sub:
        y = cy + f.size * 1.12 * len(lines) / 2 + 70
        spaced(d, (W // 2, y - 30), sub.upper(), font(FONT_B, 60), p["fg"], spacing=8, anchor="m")
    return im


def Q(quote, attr, style="dark"):
    im, d, p = base(style)
    d.text((150, 120), "“", font=font(FONT_X, 320), fill=p["accent"])
    f, lines = fit(d, quote, FONT_X, 1440, 480, 120, 56, 5)
    block(d, lines, f, W // 2, 520, p["fg"])
    d.rectangle((W // 2 - 60, 820, W // 2 + 60, 826), fill=p["accent"])
    d.text((W // 2, 880), attr, font=font(FONT_B, 46), fill=p["accent"], anchor="mm")
    return im


def S(kicker, items, note=None, style="gold"):
    im, d, p = base(style, kicker)
    n = len(items)
    col = 1640 / n
    size = 220
    while size > 80 and any(d.textlength(v, font=font(FONT_X, size)) > col - 60 for v, _ in items):
        size -= 8
    fv, fl = font(FONT_X, size), font(FONT_B, 44)
    for i, (value, label) in enumerate(items):
        cx = 140 + col * (i + 0.5)
        d.text((cx, 520), value, font=fv, fill=p["fg"] if style == "gold" else GOLD, anchor="mm")
        if label:
            d.text((cx, 520 + size * 0.62 + 40), label.upper(), font=fl, fill=p["dim"], anchor="mm")
        if i:
            x = 140 + col * i
            d.rectangle((x - 2, 380, x + 2, 700), fill=p["accent"])
    if note:
        d.text((W // 2, 860), note, font=font(FONT_S, 40), fill=p["dim"], anchor="mm")
    return im


def _name_and_record(text):
    m = re.match(r"^(.*?)\s+(\d+-\d+(?:-\d+)?)$", text)
    return (m.group(1), m.group(2)) if m else (text, None)


def V(kicker, side_a, side_b, style="dark"):
    im, d, p = base(style, kicker)
    sides = [_name_and_record(x) for x in (side_a, side_b)]
    size = min(fit(d, name, FONT_X, 640, 260, 150, 60, 1)[0].size for name, _ in sides)
    for cx, (name, rec) in zip((520, 1400), sides):
        d.text((cx, 520), name, font=font(FONT_X, size), fill=p["fg"], anchor="mm")
        if rec:
            d.text((cx, 660), rec, font=font(FONT_X, 76), fill=p["accent"], anchor="mm")
    d.ellipse((W // 2 - 90, 430, W // 2 + 90, 610), fill=p["accent"])
    d.text((W // 2, 520), "VS", font=font(FONT_X, 84), fill=p["bg"], anchor="mm")
    return im


def TL(kicker, events, style="dark"):
    im, d, p = base(style, kicker)
    top, step = 290, min(160, 620 / len(events))
    d.rectangle((398, top, 402, top + step * (len(events) - 1) + 100), fill=p["dim"])
    fy, ft = font(FONT_X, 60), font(FONT_B, 62)
    for i, (when, what) in enumerate(events):
        y = top + step * i
        d.rounded_rectangle((280, y, 520, y + 100), 12, fill=p["accent"])
        d.text((400, y + 50), when, font=fy, fill=p["bg"], anchor="mm")
        f = ft
        while d.textlength(what, font=f) > 1160 and f.size > 36:
            f = font(FONT_B, f.size - 4)
        d.text((580, y + 50), what, font=f, fill=p["fg"], anchor="lm")
    return im


def Ls(kicker, rows, style="dark"):
    im, d, p = base(style, kicker)
    step = min(170, 640 / len(rows))
    top = 560 - step * len(rows) / 2
    for i, row in enumerate(rows):
        y = top + step * i + step / 2
        d.rectangle((300, y - 22, 344, y + 22), fill=p["accent"])
        f = font(FONT_X, 80)
        while d.textlength(row, font=f) > 1240 and f.size > 40:
            f = font(FONT_X, f.size - 4)
        d.text((400, y), row, font=f, fill=p["fg"], anchor="lm")
    return im


def chapter(number, title, style="gold"):
    im, d, p = base(style)
    spaced(d, (W // 2, 250), "CHAPTER " + number, font(FONT_B, 46), p["accent"], spacing=12, anchor="m")
    f, lines = fit(d, title, FONT_X, 1560, 360, 170, 70, 2)
    block(d, lines, f, W // 2, 620, p["fg"])
    d.rectangle((W // 2 - 90, 800, W // 2 + 90, 808), fill=p["accent"])
    return im


def place_date(place, date, style="dark"):
    im, d, p = base(style)
    f, lines = fit(d, place, FONT_B, 1500, 160, 72, 40, 2)
    y = 330
    for l in lines:
        spaced(d, (W // 2, y - f.size / 2), l.upper(), f, p["fg"], spacing=8, anchor="m")
        y += f.size * 1.2
    d.rectangle((W // 2 - 60, y + 10, W // 2 + 60, y + 16), fill=p["accent"])
    d.text((W // 2, 660), date, font=font(FONT_X, 360), fill=GOLD if style == "dark" else p["fg"], anchor="mm")
    return im


def pairs(items, kicker=None, style="dark"):
    """items = [(name, description), (name, description)]"""
    im, d, p = base(style, kicker)
    for (x0, x1), (name, desc) in zip(((140, 930), (990, 1780)), items):
        d.rounded_rectangle((x0, 300, x1, 800), 18, fill=p["panel"], outline=p["accent"], width=3)
        cx = (x0 + x1) // 2
        f, lines = fit(d, name, FONT_X, x1 - x0 - 80, 220, 110, 50, 2)
        block(d, lines, f, cx, 460, GOLD if style == "dark" else p["fg"])
        f2, lines2 = fit(d, desc, FONT_S, x1 - x0 - 100, 190, 48, 30, 3)
        block(d, lines2, f2, cx, 670, p["fg"], lh=1.25)
    return im


def bars(sections, style="dark"):
    """sections = [(title, [(label, value_text), ...]), ...]; two numeric values draw as bars."""
    im, d, p = base(style)
    y = 200
    for title, vals in sections:
        spaced(d, (W // 2, y), title.upper(), font(FONT_B, 46), p["accent"], spacing=10, anchor="m")
        y += 100
        nums = [float(v) if re.fullmatch(r"[\d.]+", v) else None for _, v in vals]
        if len(vals) >= 2 and all(n is not None for n in nums):
            top = max(nums)
            for (label, v), n in zip(vals, nums):
                d.text((560, y + 55), label.upper(), font=font(FONT_X, 54), fill=p["fg"], anchor="rm")
                w = int(900 * n / top)
                d.rounded_rectangle((600, y + 10, 600 + max(w, 24), y + 100), 10,
                                    fill=GOLD if n == top else p["dim"])
                d.text((600 + max(w, 24) + 30, y + 55), v, font=font(FONT_X, 84), fill=p["fg"], anchor="lm")
                y += 130
        else:
            for label, v in vals:
                d.text((W // 2, y + 60), f"{label.upper()}  {v}", font=font(FONT_X, 96), fill=p["fg"], anchor="mm")
                y += 140
        y += 50
    return im


def stacked(top, bottom, style="dark"):
    im, d, p = base(style)
    f1, l1 = fit(d, top, FONT_X, 1500, 200, 150, 60, 1)
    d.text((W // 2, 400), l1[0], font=f1, fill=p["dim"], anchor="mm")
    d.text((W // 2, 540), "OR", font=font(FONT_B, 48), fill=p["accent"], anchor="mm")
    f2, l2 = fit(d, bottom, FONT_X, 1400, 200, 150, 60, 1)
    w = d.textlength(l2[0], font=f2)
    d.rounded_rectangle((W / 2 - w / 2 - 50, 690 - f2.size * 0.7, W / 2 + w / 2 + 50, 690 + f2.size * 0.7), 14, fill=GOLD)
    d.text((W // 2, 690), l2[0], font=f2, fill=(14, 14, 14), anchor="mm")
    return im


def logo_cover():
    """FE logo cover using the real logo file."""
    im = Image.new("RGB", (W, H), (0, 0, 0))
    logo_path = os.path.join(ASSETS, "logo_square.png")
    if os.path.exists(logo_path):
        logo = Image.open(logo_path).convert("RGBA")
        logo = logo.resize((640, 640), Image.LANCZOS)
        x = (W - 640) // 2
        y = (H - 640) // 2
        im.paste(logo, (x, y), logo)
    else:
        d = ImageDraw.Draw(im)
        d.rounded_rectangle((W // 2 - 190, 250, W // 2 + 190, 630), 40, fill=GOLD)
        d.text((W // 2, 440), "FE", font=font(FONT_X, 250), fill=(11, 11, 13), anchor="mm")
        spaced(d, (W // 2, 700), "FIGHT ERA", font(FONT_X, 110), (245, 245, 245), spacing=22, anchor="m")
    return im


def overlay(label=None):
    """Transparent 1920x1080 overlay for full-screen clips: watermark + optional source label."""
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    f = font(FONT_S, 30)
    d.text((W - 48 + 2, H - 44 + 2), WATERMARK, font=f, fill=(0, 0, 0, 150), anchor="rm")
    d.text((W - 48, H - 44), WATERMARK, font=f, fill=(255, 255, 255, 170), anchor="rm")
    if label:
        fl = font(FONT_B, 44)  # large enough to read on a phone
        w = d.textlength(label, font=fl)
        d.rounded_rectangle((40, H - 110, 40 + w + 68, H - 34), 10, fill=(0, 0, 0, 190))
        d.rectangle((40, H - 110, 52, H - 34), fill=GOLD + (255,))
        d.text((76, H - 72), label, font=fl, fill=(255, 255, 255, 255), anchor="lm")
    return im
