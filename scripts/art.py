"""Raster art for the README: hands banner, pixel figure, night-scene footer."""
import numpy as np
from PIL import Image, ImageFilter

from pixel import B4, C, dither, hexrgb, ramp

# ------------------------------------------------------------- hands banner --
G = {  # tiny 3x5 font, only to redraw the window title the source JPEG smeared
    "P": ["111", "101", "111", "100", "100"], "R": ["110", "101", "110", "101", "101"],
    "O": ["111", "101", "101", "101", "111"], "J": ["001", "001", "001", "101", "111"],
    "E": ["111", "100", "110", "100", "111"], "C": ["111", "100", "100", "100", "111"],
    "T": ["111", "010", "010", "010", "010"], "X": ["101", "101", "010", "101", "101"],
    ".": ["0", "0", "0", "0", "1"],
}
WARM = ramp([(0, "#070605"), (.3, "#120e0a"), (.55, "#26170c"), (.75, "#5a2c0e"), (.9, "#a4490f"), (1, "#e0701a")])
PAPER = hexrgb(C["paper"]).astype("uint8")
CROP_Y = (110, 700)          # rows kept from the 2x image (drops the empty black top/bottom)
SPARK = (758, 436 - CROP_Y[0])  # gap between the two fingertips, in cropped 2x pixels


def hero_mask():
    src = Image.open("assets/source/hands.jpg").convert("L")
    big = src.resize((src.width * 2, src.height * 2), Image.LANCZOS)
    mask = np.array(big) > 128
    mask[232:253, 560:700] = False
    px, py, cell = 566, 236, 2
    for ch in "PROJECT.EXE":
        g = G[ch]
        for ry, row in enumerate(g):
            for rx, bit in enumerate(row):
                if bit == "1":
                    mask[py + ry * cell: py + (ry + 1) * cell, px + rx * cell: px + (rx + 1) * cell] = True
        px += (len(g[0]) + 1) * cell
    return mask


def hero_frames(seeds=(7, 13)):
    """Two grain variants of the same banner, so the texture can shimmer."""
    mask = hero_mask()
    H, W = mask.shape
    blk = 3
    gh, gw = H // blk + 1, W // blk + 1
    ys, xs = np.mgrid[0:gh, 0:gw]
    base = ((0.45 * xs / gw + 0.55 * ys / gh) ** 2.0) * 0.95
    out = []
    for s in seeds:
        t = base + np.random.default_rng(s).normal(0, 0.035, base.shape)
        bg = dither(t, 12, WARM, B4)
        bg = np.kron(bg, np.ones((blk, blk, 1), "uint8"))[:H, :W]
        bg[mask] = PAPER
        out.append(bg[CROP_Y[0]:CROP_Y[1]])
    return out


# ------------------------------------------------------------ pixel figure --
def figure(scale=2):
    """The pixel figure from the reference, recoloured to a warm duotone, bg transparent."""
    im = Image.open("assets/source/figure.png").convert("L").filter(ImageFilter.MedianFilter(3))
    g = np.array(im).astype(int)
    levels = np.digitize(g, [34, 78, 122, 170, 214])          # 0 = background
    tones = ["#000000", "#2b251e", "#51473b", "#8c7e69", "#cdbd9f", "#ffb02e"]
    rgb = np.stack([np.array([hexrgb(tones[l])[c] for l in range(6)])[levels] for c in range(3)], -1)
    a = (levels > 0).astype("uint8") * 255
    rgba = np.dstack([rgb.astype("uint8"), a])
    ys, xs = np.where(a > 0)
    rgba = rgba[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    return Image.fromarray(rgba, "RGBA").resize((rgba.shape[1] * scale, rgba.shape[0] * scale), Image.NEAREST)


# ------------------------------------------------------------ footer scene --
W, H, HOR = 200, 75, 54
SUN, SUN_R = (112, 37), 11


def scene():
    yy, xx = np.mgrid[0:H, 0:W].astype(float)
    xi, yi = xx.astype(int), yy.astype(int)
    xs1 = np.arange(W, dtype=float)
    rng = np.random.default_rng(5)

    SKY = ramp([(0, "#080605"), (.3, "#110b07"), (.55, "#25140a"), (.75, "#4a220c"), (.9, "#86400f"), (1, "#c8661a")])
    d = np.hypot(xx - SUN[0], yy - SUN[1])
    t_full = np.clip((np.clip(yy, 0, HOR) / HOR) ** 1.8 + 0.42 * np.exp(-(d / 26) ** 2), 0, 1)
    img = dither(t_full, 10, SKY, B4)

    sunramp = ramp([(0, "#e86f17"), (.5, "#ff9f1f"), (1, "#ffd77a")])
    disc = d <= SUN_R
    img[disc] = dither(1 - d / SUN_R, 5, sunramp, B4)[disc]

    def ridge(base, comps, seed):
        r = np.random.default_rng(seed)
        y = np.full(W, float(base))
        for f, a in comps:
            y += a * np.sin(xs1 * f + r.uniform(0, 6.28))
        return y

    for top, (c1, c2) in [
        (ridge(45, [(.045, 4.5), (.11, 2.5), (.29, 1.1)], 1), ("#4a2410", "#2a150a")),
        (ridge(49, [(.06, 3.5), (.17, 2.0), (.37, .9)], 2), ("#2a150a", "#150b06")),
    ]:
        m = (yy >= top[None, :]) & (yy < HOR)
        tt = np.clip((yy - top[None, :]) / 14, 0, 1)
        rgb = dither(tt, 4, ramp([(0, c1), (1, c2)]), B4)
        img[m] = rgb[m]

    # ---- silhouettes (everything near-black in the foreground)
    sil = np.zeros((H, W), bool)
    top_l = np.where(xs1 < 36, 56 + (xs1 / 36) ** 2 * 20, 99)
    top_r = np.where(xs1 > 140, 55 + ((W - 1 - xs1) / 60) ** 2 * 22, 99)
    land_top = np.minimum(top_l, top_r)
    sil |= yy >= land_top[None, :]

    def put(y0, y1, x0, x1):
        sil[max(y0, 0):max(y1, 0), max(x0, 0):max(x1, 0)] = True

    def pine(cx, h):
        base = int(land_top[cx]) + 1
        q = max(2, h // 4)
        for r in range(h):
            within = (r % q) / q
            half = int((0.25 + 0.75 * within) * (0.15 + 0.85 * r / h) * h * 0.28)
            put(base - h + r, base - h + r + 1, cx - half, cx + half + 1)
        put(base - 2, base + 1, cx, cx + 1)

    lights = []

    def pagoda(cx, h_ground):
        y = h_ground
        for wd in (15, 12, 9):
            put(y - 5, y, cx - wd // 2 + 1, cx + wd // 2)
            lights.append((cx, y - 4))
            y -= 5
            rw = wd + 6
            put(y - 1, y, cx - rw // 2, cx + rw // 2 + 1)
            put(y - 2, y - 1, cx - rw // 2 + 2, cx + rw // 2 - 1)
            put(y - 2, y - 1, cx - rw // 2, cx - rw // 2 + 1)
            put(y - 2, y - 1, cx + rw // 2, cx + rw // 2 + 1)
            y -= 2
        put(y - 5, y, cx, cx + 1)

    def torii(cx, base, top):
        for x0 in (cx - 10, cx + 9):
            put(top + 4, base + 1, x0, x0 + 2)
        put(top, top + 2, cx - 16, cx + 17)
        put(top - 1, top, cx - 16, cx - 13)
        put(top - 1, top, cx + 14, cx + 17)
        put(top + 2, top + 3, cx - 13, cx + 14)
        put(top + 8, top + 10, cx - 13, cx + 14)
        put(top + 3, top + 8, cx - 1, cx + 2)

    for cx, h in [(5, 22), (13, 16), (21, 19), (29, 12)]:
        pine(cx, h)
    for cx, h in [(163, 14), (170, 18), (192, 17), (197, 22)]:
        pine(cx, h)
    pagoda(181, int(land_top[181]))
    torii(70, 64, 40)

    # ---- water: darker mirrored sky + sun glitter + broken reflections + ripples
    wm = yy >= HOR
    k = (yy - HOR).astype(int)
    src = np.clip(HOR - 1 - k, 0, H - 1)
    shift = np.round(1.3 * np.sin(k * 0.9)).astype(int)
    xsrc = np.clip(xi + shift, 0, W - 1)
    t_w = t_full[src, xsrc] * 0.58
    water = dither(t_w, 8, SKY, B4)
    hw = 2 + k * 0.35
    glit = wm & (np.abs(xx - SUN[0]) <= hw) & (((xi + 2 * k) % 5) < 2) & (rng.random((H, W)) < 0.55)
    water[glit] = dither(np.full((H, W), .22), 4, sunramp, B4)[glit]
    above = sil.copy()
    above[HOR:, :] = False
    refl = np.zeros((H, W), bool)
    for kk in range(H - HOR):
        sy = HOR - 1 - kk
        if sy >= 0:
            refl[HOR + kk] = np.roll(above[sy], int(round(1.3 * np.sin(kk * 0.9))))
    refl &= (((xi + yi) % 2) == 0) | (rng.random((H, W)) < 0.2)
    water[refl & wm] = hexrgb("#170c06").astype("uint8")
    for kk in range(H - HOR):
        for _ in range(int(1 + kk * 0.35)):
            x0 = int(rng.integers(0, W - 10))
            ln = int(rng.integers(3, 9))
            col = "#2a160b" if rng.random() < 0.7 else "#5a2a0e"
            water[HOR + kk, x0:x0 + ln] = hexrgb(col).astype("uint8")
    img[wm] = water[wm]

    img[sil] = hexrgb("#090605").astype("uint8")
    right_e = sil & ~np.roll(sil, -1, axis=1)
    left_e = sil & ~np.roll(sil, 1, axis=1)
    lit = np.where(xx < SUN[0], right_e, left_e) & (yy < HOR)
    top_e = sil & ~np.roll(sil, 1, axis=0) & (yy < HOR)
    img[top_e] = hexrgb("#4a220c").astype("uint8")
    img[lit] = hexrgb("#6e3410").astype("uint8")

    meta = dict(lights=lights, sun=SUN, hor=HOR, W=W, H=H, rng_seed=11)
    return img, meta
