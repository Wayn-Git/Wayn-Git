"""Shared helpers for build_assets.py: palette, ordered dithering, pixel text, SVG shell."""
import base64
import io

import numpy as np
from PIL import Image, ImageDraw, ImageFont

# warm near-black + paper + one amber accent. no purple, no blue.
C = dict(
    bg="#0b0a09", panel="#12100e", panel2="#191613", line="#2c2721",
    fg="#e9e2d3", dim="#8d8576", faint="#4b453c",
    amber="#ffa826", ember="#ff5d2a", ok="#8fbf7a", paper="#f5ecd7",
)
MONO = ('ui-monospace,SFMono-Regular,"JetBrains Mono","Cascadia Mono",Menlo,Consolas,'
        '"DejaVu Sans Mono","Liberation Mono",monospace')
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"


def hexrgb(h):
    return np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], float)


def bayer(n):
    if n == 1:
        return np.array([[0]])
    m = bayer(n // 2)
    return np.block([[4 * m, 4 * m + 2], [4 * m + 3, 4 * m + 1]])


B4 = (bayer(4) + .5) / 16
B8 = (bayer(8) + .5) / 64


def ramp(stops):
    """stops: [(pos, '#hex'), ...] -> f(t) giving rgb arrays."""
    xs = [s[0] for s in stops]
    cols = [hexrgb(s[1]) for s in stops]

    def f(t):
        t = np.clip(t, 0, 1)
        return np.stack([np.interp(t, xs, [c[i] for c in cols]) for i in range(3)], -1)
    return f


def dither(t, levels, rampf, bayer_t=B4):
    """Ordered-dither a 0..1 field into `levels` ramp steps -> uint8 rgb."""
    h, w = t.shape
    th = np.tile(bayer_t, (h // bayer_t.shape[0] + 1, w // bayer_t.shape[1] + 1))[:h, :w]
    x = np.clip(t, 0, 1) * (levels - 1)
    lo = np.floor(x)
    q = (lo + ((x - lo) > th)).clip(0, levels - 1) / (levels - 1)
    return rampf(q).astype("uint8")


def png_uri(arr, colors=48, scale=1):
    """numpy rgb/rgba -> data URI (palette PNG, nearest-neighbour upscale)."""
    im = Image.fromarray(arr)
    if scale != 1:
        im = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
    if im.mode == "RGB":
        im = im.quantize(colors=colors, dither=Image.NONE)
    buf = io.BytesIO()
    im.save(buf, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def pixel_text(text, x, y, px=3, size=11, fill="#fff", anchor="start"):
    """Rasterise text with a real 1-bit font, emit as SVG rects. Returns (svg, w, h)."""
    font = ImageFont.truetype(FONT_BOLD, size)
    l, t, r, b = font.getbbox(text)
    img = Image.new("L", (r - l + 8, b - t + 8), 0)
    d = ImageDraw.Draw(img)
    d.fontmode = "1"
    d.text((4 - l, 4 - t), text, font=font, fill=255)
    a = np.array(img) > 127
    ys, xs = np.where(a)
    a = a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    h, w = a.shape
    if anchor == "end":
        x -= w * px
    elif anchor == "middle":
        x -= w * px / 2
    parts = []
    for ry in range(h):
        row = a[ry]
        cx = 0
        while cx < w:
            if row[cx]:
                s = cx
                while cx < w and row[cx]:
                    cx += 1
                parts.append(f"M{x + s * px:g} {y + ry * px:g}h{(cx - s) * px}v{px}h-{(cx - s) * px}z")
            else:
                cx += 1
    return f'<path d="{"".join(parts)}" fill="{fill}"/>', w * px, h * px


BASE_CSS = (
    f".m{{font-family:{MONO}}}"
    "@keyframes blink{0%,49%{opacity:1}50%,100%{opacity:0}}"
    "@keyframes pulse{0%,100%{opacity:.35}50%{opacity:1}}"
    "@media (prefers-reduced-motion:reduce){*{animation:none!important}.ln{opacity:1!important}}"
)


def svg(w, h, body, css="", defs="", title="", desc=""):
    t = f"<title>{title}</title>" if title else ""
    d = f"<desc>{desc}</desc>" if desc else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img">{t}{d}'
            f"<style>{BASE_CSS}{css}</style><defs>{defs}</defs>{body}</svg>")
