#!/usr/bin/env python3
"""
Renders the "what's in my ears" card for a GitHub profile README as one SVG.

  - top: what's playing right now (or the last thing you played), with a little
    equalizer that only moves while something is actually playing
  - below: three columns of top tracks (past year / past 6 months / past month)

Standard library only. Two data sources:

  Spotify  needs SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, SPOTIFY_REFRESH_TOKEN
           (get the refresh token once with scripts/get_spotify_token.py)
  Last.fm  needs LASTFM_API_KEY and LASTFM_USER (free, no Premium, no OAuth)

Try it without any credentials:   python3 scripts/music.py --demo
"""
import argparse
import base64
import json
import os
import struct
import sys
import urllib.parse
import urllib.request
import zlib
from xml.sax.saxutils import escape

UA = "profile-readme-music/1.0"

# ---------------------------------------------------------------- layout ----
W = 800
COL_W, COL_GAP = 250, 25
CARD_H, CARD_GAP = 52, 8
ART = 40
NOW_W, NOW_H, NOW_Y = 300, 64, 26
COLS_Y = 138           # y of first track card
H = COLS_Y + 5 * CARD_H + 4 * CARD_GAP + 10

LIGHT = dict(fg="#2a2620", dim="#6f675a", ac="#c96a00", cf="rgba(128,128,128,.08)", cs="rgba(128,128,128,.32)")
DARK = dict(fg="#e9e2d3", dim="#8d8576", ac="#ffa826", cf="#191613", cs="#2c2721")


# ------------------------------------------------------------------ http ----
def http_json(url, headers=None, data=None):
    req = urllib.request.Request(url, data=data, headers=headers or {})
    with urllib.request.urlopen(req, timeout=20) as r:
        body = r.read()
    return json.loads(body) if body else None  # 204 -> None


def fetch_art(url, cache):
    """Album art -> data URI, so the SVG has no external requests."""
    if not url:
        return None
    if url in cache:
        return cache[url]
    uri = None
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=20) as r:
            raw = r.read()
        if raw[:4] == b"\x89PNG":
            mime = "image/png"
        elif raw[:4] == b"RIFF":
            mime = "image/webp"
        else:
            mime = "image/jpeg"
        uri = f"data:{mime};base64,{base64.b64encode(raw).decode()}"
    except Exception as e:  # a missing cover should never kill the card
        print(f"art failed ({e}): {url}", file=sys.stderr)
    cache[url] = uri
    return uri


# --------------------------------------------------------------- spotify ----
def spotify():
    cid = os.environ["SPOTIFY_CLIENT_ID"]
    secret = os.environ["SPOTIFY_CLIENT_SECRET"]
    refresh = os.environ["SPOTIFY_REFRESH_TOKEN"]
    basic = base64.b64encode(f"{cid}:{secret}".encode()).decode()
    tok = http_json(
        "https://accounts.spotify.com/api/token",
        headers={
            "Authorization": f"Basic {basic}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data=urllib.parse.urlencode(
            {"grant_type": "refresh_token", "refresh_token": refresh}
        ).encode(),
    )
    auth = {"Authorization": f"Bearer {tok['access_token']}"}
    api = "https://api.spotify.com/v1"

    def cover(item):
        imgs = [i for i in (item.get("album") or {}).get("images") or [] if i.get("url")]
        imgs.sort(key=lambda i: i.get("width") or 0)
        for i in imgs:  # smallest cover that is still >= 64px
            if (i.get("width") or 0) >= 64:
                return i["url"]
        return imgs[-1]["url"] if imgs else None

    def track(item):
        return {
            "title": item["name"],
            "artist": ", ".join(a["name"] for a in item.get("artists", [])),
            "art_url": cover(item),
        }

    now = None
    cur = http_json(f"{api}/me/player/currently-playing", headers=auth)
    item = (cur or {}).get("item")
    if item and item.get("type") == "track":
        now = track(item)
        now["playing"] = bool(cur.get("is_playing"))
        dur = item.get("duration_ms") or 0
        now["progress"] = (cur.get("progress_ms") or 0) / dur if dur else None
    if not now:
        rec = http_json(f"{api}/me/player/recently-played?limit=1", headers=auth)
        items = (rec or {}).get("items") or []
        if items:
            now = track(items[0]["track"])
            now["playing"], now["progress"] = False, None

    def top(rng):
        d = http_json(f"{api}/me/top/tracks?time_range={rng}&limit=5", headers=auth)
        return [track(i) for i in (d or {}).get("items", [])]

    cols = [
        ("past year", top("long_term")),
        ("past 6 months", top("medium_term")),
        ("past month", top("short_term")),
    ]
    return now, cols


# ---------------------------------------------------------------- last.fm ----
LASTFM_PLACEHOLDER = "2a96cbd8b46e442fc41c2b86b821562f"  # the grey star image


def lastfm():
    key, user = os.environ["LASTFM_API_KEY"], os.environ["LASTFM_USER"]

    def call(method, **p):
        q = urllib.parse.urlencode({"method": method, "api_key": key, "format": "json", **p})
        return http_json("https://ws.audioscrobbler.com/2.0/?" + q, headers={"User-Agent": UA})

    def pick(images):
        for i in reversed(images or []):  # biggest first, skip the grey star
            u = i.get("#text") or ""
            if u and LASTFM_PLACEHOLDER not in u:
                return u
        return None

    def row(t):
        a = t.get("artist")
        artist = (a.get("name") or a.get("#text") or "") if isinstance(a, dict) else (a or "")
        art = pick(t.get("image"))
        if not art:  # top-track lists have no covers, so ask for the album
            try:
                info = call("track.getInfo", track=t["name"], artist=artist)
                art = pick(((info or {}).get("track", {}).get("album") or {}).get("image"))
            except Exception:
                art = None
        return {"title": t["name"], "artist": artist, "art_url": art}

    def as_list(x):
        return [x] if isinstance(x, dict) else (x or [])

    now = None
    rec = call("user.getRecentTracks", user=user, limit=1)
    items = as_list((rec or {}).get("recenttracks", {}).get("track"))
    if items:
        now = row(items[0])
        now["playing"] = (items[0].get("@attr") or {}).get("nowplaying") == "true"
        now["progress"] = None

    def top(period):
        d = call("user.getTopTracks", user=user, period=period, limit=5)
        return [row(t) for t in as_list((d or {}).get("toptracks", {}).get("track"))]

    cols = [
        ("past year", top("12month")),
        ("past 6 months", top("6month")),
        ("past month", top("1month")),
    ]
    return now, cols


# ------------------------------------------------------------------ demo ----
def solid_png(rgb, size=64):
    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)

    raw = (b"\x00" + bytes(rgb) * size) * size
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw))
        + chunk(b"IEND", b"")
    )


def demo():
    palette = [(94, 84, 142), (46, 134, 171), (199, 91, 57), (63, 125, 88), (170, 120, 60),
               (120, 70, 90), (40, 60, 110), (150, 150, 70), (80, 140, 150), (110, 90, 60)]
    n = [0]

    def t(title, artist):
        c = palette[n[0] % len(palette)]
        n[0] += 1
        uri = "data:image/png;base64," + base64.b64encode(solid_png(c)).decode()
        return {"title": title, "artist": artist, "art": uri}

    now = t("Slow Lanes", "Harbor Lights")
    now["playing"], now["progress"] = True, 0.42
    cols = [
        ("past year", [t("Slow Lanes", "Harbor Lights"), t("Paper Planes at Noon", "The Examples"),
                       t("A Very Long Song Title That Will Not Fit In The Card", "Some Band"),
                       t("Four AM", "Nova Static"), t("Glass House", "Linden")]),
        ("past 6 months", [t("Driftwood", "Marlow"), t("Cold Brew", "The Examples"), t("Static Bloom", "Nova Static"),
                           t("Ten Minutes Left", "Harbor Lights"), t("Second Wind", "Linden")]),
        ("past month", [t("Night Bus", "Marlow"), t("Overpass", "Some Band"), t("Soft Reset", "Linden"),
                        t("Daylight Savings", "The Examples"), t("Low Tide", "Nova Static")]),
    ]
    return now, cols


# ------------------------------------------------------------------- svg ----
def est(text, size, bold=False):
    """Text width in px. The card is set in a monospace font, so it is just length x 0.6em."""
    return len(text) * size * 0.6


def fit(text, max_w, size, bold=False):
    if est(text, size, bold) <= max_w:
        return text
    while text and est(text + "…", size, bold) > max_w:
        text = text[:-1]
    return text.rstrip() + "…"


def css(theme):
    def block(p):
        return (f".t{{fill:{p['fg']}}}.a,.h{{fill:{p['dim']}}}.ac{{fill:{p['ac']}}}"
                f".cd{{fill:{p['cf']};stroke:{p['cs']}}}")

    if theme == "light":
        colors = block(LIGHT)
    elif theme == "dark":
        colors = block(DARK)
    else:
        colors = block(LIGHT) + "@media (prefers-color-scheme:dark){" + block(DARK) + "}"
    return (
        'text{font-family:ui-monospace,SFMono-Regular,"JetBrains Mono","Cascadia Mono",Menlo,Consolas,"DejaVu Sans Mono","Liberation Mono",monospace}'
        ".t{font-size:13px;font-weight:600}.a{font-size:12px}.h{font-size:12px;letter-spacing:.03em}"
        ".n{font-size:14px;font-weight:600}"
        ".bar{transform-box:fill-box}.bl{transform-origin:100% 50%}.br{transform-origin:0% 50%}"
        "@keyframes e1{0%,100%{transform:scaleX(.3)}45%{transform:scaleX(1)}}"
        "@keyframes e2{0%,100%{transform:scaleX(.55)}50%{transform:scaleX(.25)}80%{transform:scaleX(.95)}}"
        "@keyframes e3{0%,100%{transform:scaleX(.4)}60%{transform:scaleX(.9)}}"
        ".p1{animation:e1 1.1s ease-in-out infinite}"
        ".p2{animation:e2 1.5s ease-in-out infinite -.4s}"
        ".p3{animation:e3 .9s ease-in-out infinite -.2s}"
        "@media (prefers-reduced-motion:reduce){.bar{animation:none!important}}"
        + colors
    )


def cover(uri, size, clip):
    if uri:
        return (f'<image width="{size}" height="{size}" preserveAspectRatio="xMidYMid slice" '
                f'xlink:href="{uri}" clip-path="url(#{clip})"/>')
    return (f'<rect width="{size}" height="{size}" rx="4" fill="#808080" fill-opacity=".22"/>'
            f'<text class="a" x="{size / 2}" y="{size / 2 + 4}" text-anchor="middle">♪</text>')


def card(x, y, tr):
    title = escape(fit(tr["title"], 184, 13, True))
    artist = escape(fit(tr["artist"], 184, 12))
    return (
        f'<g transform="translate({x},{y})">'
        f'<rect width="{COL_W}" height="{CARD_H}" rx="4" class="cd"/>'
        f'<g transform="translate(6,6)">{cover(tr.get("art"), ART, "ca")}</g>'
        f'<g transform="translate(56,0)"><g clip-path="url(#ct)">'
        f'<text class="t" y="23">{title}</text><text class="a" y="40">{artist}</text>'
        f'</g></g></g>'
    )


def build_svg(now, cols, theme="auto", panel=False):
    now = now or {"title": "nothing yet", "artist": "play something", "art": None,
                  "playing": False, "progress": None}
    playing = bool(now.get("playing"))
    nx = (W - NOW_W) // 2
    cy = NOW_Y + NOW_H / 2
    pad = 28 if panel else 0
    TW, TH = W + 2 * pad, H + 2 * pad
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'width="{TW}" height="{TH}" viewBox="0 0 {TW} {TH}" role="img">',
        f'<title>{"Playing now" if playing else "Last played"}: {escape(now["title"])} by {escape(now["artist"])}</title>',
        f"<style>{css(theme)}</style>",
        "<defs>"
        f'<clipPath id="ca"><rect width="{ART}" height="{ART}" rx="4"/></clipPath>'
        '<clipPath id="cb"><rect width="48" height="48" rx="5"/></clipPath>'
        f'<clipPath id="ct"><rect width="184" height="{CARD_H}"/></clipPath>'
        f'<clipPath id="cn"><rect width="224" height="{NOW_H}"/></clipPath>'
        "</defs>",
    ]
    if panel:
        out.append(f'<rect x=".5" y=".5" width="{TW - 1}" height="{TH - 1}" rx="6" fill="#12100e" stroke="#2c2721"/>')
    out.append(f'<g transform="translate({pad},{pad})">')
    out.append(f'<text class="h" x="{W / 2}" y="14" text-anchor="middle">{"playing now" if playing else "last played"}</text>')

    # equalizer bars, mirrored either side of the now-playing card
    lens_left, lens_right = (110, 70, 92), (92, 70, 110)
    for i in range(3):
        y = cy - 14 + i * 11 - 3
        for side, ln in (("bl", lens_left[i]), ("br", lens_right[i])):
            x = nx - ln if side == "bl" else nx + NOW_W
            anim = f"p{i + 1}" if playing else ""
            style = "" if playing else ' style="transform:scaleX(.3);opacity:.55"'
            out.append(f'<rect class="bar ac {side} {anim}" x="{x}" y="{y}" width="{ln}" height="6" rx="3"{style}/>')

    # now playing card
    out.append(
        f'<g transform="translate({nx},{NOW_Y})">'
        f'<rect width="{NOW_W}" height="{NOW_H}" rx="4" class="cd"/>'
        f'<g transform="translate(8,8)">{cover(now.get("art"), 48, "cb")}</g>'
        f'<g transform="translate(66,0)"><g clip-path="url(#cn)">'
        f'<text class="n t" y="27">{escape(fit(now["title"], 224, 14, True))}</text>'
        f'<text class="a" y="43">{escape(fit(now["artist"], 224, 12))}</text>'
        f"</g>"
    )
    if playing and now.get("progress") is not None:
        p = max(0.0, min(1.0, now["progress"]))
        out.append(f'<rect y="52" width="224" height="3" rx="1.5" fill="#808080" fill-opacity=".25"/>'
                   f'<rect class="ac" y="52" width="{224 * p:.1f}" height="3" rx="1.5"/>')
    out.append("</g></g>")

    # three columns
    for ci, (label, tracks) in enumerate(cols):
        x = ci * (COL_W + COL_GAP)
        out.append(f'<text class="h" x="{x + COL_W / 2}" y="{COLS_Y - 14}" text-anchor="middle">{escape(label)}</text>')
        for ri, tr in enumerate(tracks[:5]):
            out.append(card(x, COLS_Y + ri * (CARD_H + CARD_GAP), tr))

    out.append("</g></svg>")
    return "".join(out)


# ------------------------------------------------------------------ main ----
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default="music.svg")
    ap.add_argument("--demo", action="store_true", help="render fake data, no credentials needed")
    ap.add_argument("--provider", choices=["auto", "spotify", "lastfm"], default="auto")
    ap.add_argument("--panel", action="store_true", help="draw a dark card behind everything (use with --theme dark)")
    ap.add_argument("--theme", choices=["auto", "light", "dark"], default="auto",
                    help="auto follows the viewer's light/dark setting")
    a = ap.parse_args()

    if a.demo:
        now, cols = demo()
    else:
        provider = a.provider
        if provider == "auto":
            if os.environ.get("SPOTIFY_REFRESH_TOKEN"):
                provider = "spotify"
            elif os.environ.get("LASTFM_API_KEY"):
                provider = "lastfm"
            else:
                sys.exit("No credentials found. Set the Spotify or Last.fm variables (see top of file), or try --demo.")
        now, cols = spotify() if provider == "spotify" else lastfm()
        cache = {}
        for t in ([now] if now else []) + [t for _, ts in cols for t in ts]:
            t["art"] = fetch_art(t.pop("art_url", None), cache)

    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        f.write(build_svg(now, cols, a.theme, a.panel))
    print(f"wrote {a.out} ({os.path.getsize(a.out) / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
