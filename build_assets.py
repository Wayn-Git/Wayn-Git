#!/usr/bin/env python3
"""
Regenerates every image the README uses into ./assets (run from the repo root):

    pip install numpy pillow
    python3 scripts/build_assets.py

Edit the TEXT constants near the top of each function, re-run, commit the SVGs.
Sources live in assets/source/ (hands.jpg = banner, figure.png = the pixel figure).
"""
import os
import random
import sys
import textwrap

import numpy as np
from xml.sax.saxutils import escape

sys.path.insert(0, os.path.dirname(__file__))
import art  # noqa: E402
from pixel import C, MONO, pixel_text, png_uri, svg  # noqa: E402

OUT = "assets"


def t(x, y, s, size=13, fill=C["fg"], weight=None, anchor=None, extra=""):
    a = f' text-anchor="{anchor}"' if anchor else ""
    w = f' font-weight="{weight}"' if weight else ""
    return f'<text class="m" x="{x:g}" y="{y:g}" font-size="{size}" fill="{fill}"{w}{a}{extra}>{escape(s)}</text>'


def save(name, content):
    path = os.path.join(OUT, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  {name:28s} {os.path.getsize(path) / 1024:6.1f} KB")


def panel(w, h, r=6, fill=C["panel"]):
    return f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="{r}" fill="{fill}" stroke="{C["line"]}"/>'


# --------------------------------------------------------------------- hero --
def hero():
    W, TOP = 800, 72
    imgW, imgH = 798, round(798 * 590 / 1472)
    H = TOP + imgH + 138
    A, B = (png_uri(f, colors=32) for f in art.hero_frames())
    sx = 1 + art.SPARK[0] * imgW / 1472
    sy = TOP + art.SPARK[1] * imgH / 590

    chrome = (
        f'<rect width="{W}" height="36" fill="#0d0b09"/>'
        f'<circle cx="22" cy="18" r="5" fill="#d9532c"/><circle cx="40" cy="18" r="5" fill="#e0a030"/>'
        f'<circle cx="58" cy="18" r="5" fill="#6f9a5e"/>'
        f'<path d="M84 36V12a6 6 0 0 1 6-6H270a6 6 0 0 1 6 6V36Z" fill="{C["panel"]}"/>'
        f'<rect x="96" y="15" width="8" height="8" fill="{C["amber"]}"/>'
        + t(114, 24.5, "index.html", 12, C["fg"])
        + f'<path d="M256 14l8 8m0-8l-8 8" stroke="{C["dim"]}" stroke-width="1.4"/>'
        + t(292, 25, "+", 16, C["dim"])
        + f'<rect y="36" width="{W}" height="36" fill="{C["panel"]}"/>'
        f'<path d="M30 47l-6 7 6 7M50 47l6 7-6 7" stroke="{C["dim"]}" stroke-width="1.6" fill="none"/>'
        f'<path d="M80 50a6 6 0 1 0 2 5M82 47v4h-4" stroke="{C["dim"]}" stroke-width="1.5" fill="none"/>'
        f'<rect x="108" y="42" width="600" height="24" rx="12" fill="{C["bg"]}" stroke="{C["line"]}"/>'
        f'<text class="m" x="128" y="58" font-size="12.5"><tspan fill="{C["dim"]}">file:///home/bilal/</tspan>'
        f'<tspan fill="{C["fg"]}">index.html</tspan></text>'
        f'<circle cx="772" cy="48" r="1.7" fill="{C["dim"]}"/><circle cx="772" cy="54" r="1.7" fill="{C["dim"]}"/>'
        f'<circle cx="772" cy="60" r="1.7" fill="{C["dim"]}"/>'
        f'<path d="M0 72.5H{W}" stroke="{C["line"]}"/>'
    )
    image = (
        f'<g clip-path="url(#ic)"><g style="animation:flick 7s linear infinite">'
        f'<image x="1" y="{TOP}" width="{imgW}" height="{imgH}" xlink:href="{A}"/>'
        f'<image class="gb" x="1" y="{TOP}" width="{imgW}" height="{imgH}" xlink:href="{B}"/></g>'
        f'<rect x="1" y="{TOP}" width="{imgW}" height="{imgH}" fill="url(#sl)"/>'
        f'<rect class="scan" x="1" y="{TOP}" width="{imgW}" height="2" fill="#fff" fill-opacity=".08"/></g>'
    )
    # the spark of creation, between the fingertips
    arms = "".join(f'<rect x="{x}" y="{y}" width="3" height="3" fill="{C["amber"]}"/>'
                   for x, y in [(-1.5, -10.5), (-1.5, 7.5), (-10.5, -1.5), (7.5, -1.5), (-1.5, -6), (-1.5, 3), (-6, -1.5), (3, -1.5)])
    dirs = [(14, 0), (-14, 0), (0, 14), (0, -14), (10, 10), (-10, 10), (10, -10), (-10, -10)]
    burst = "".join(
        f'<rect class="bu" x="-1" y="-1" width="2.4" height="2.4" fill="{C["ember"]}" '
        f'style="--dx:{dx}px;--dy:{dy}px;animation-delay:{i * 0.04:.2f}s"/>' for i, (dx, dy) in enumerate(dirs))
    spark = (f'<g transform="translate({sx:.1f},{sy:.1f})"><g class="sp">{arms}'
             f'<rect x="-2" y="-2" width="4" height="4" fill="{C["paper"]}"/></g>{burst}</g>')

    hy = TOP + imgH
    name, nw, nh = pixel_text("hey, i'm bilal", 36, hy + 28, px=4, size=11, fill=C["paper"])
    phrases = ["building Amethyst, a local-first personal AI OS", "learning how inference gets served (KV caches, batching)",
               "breaking things on CachyOS, then fixing them", "student, builder, linux person"]
    ph = "".join(f'<text class="m ph" x="62" y="{hy + 104}" font-size="16" fill="{C["fg"]}" '
                 f'style="animation-delay:{i * 3.5}s">{escape(p)}</text>' for i, p in enumerate(phrases))
    head = (
        f'<rect y="{hy}" width="{W}" height="{H - hy}" fill="{C["panel"]}"/>' + name
        + f'<rect class="cur" x="{36 + nw + 12}" y="{hy + 28}" width="16" height="{nh}" fill="{C["amber"]}"/>'
        + t(36, hy + 104, ">", 16, C["amber"], "bold") + ph
        + t(764, hy + 42, "student, india", 12, C["dim"], anchor="end")
        + t(764, hy + 60, "CachyOS · GNOME · fish", 12, C["dim"], anchor="end")
    )
    css = (
        f"@keyframes scan{{from{{transform:translateY(0)}}to{{transform:translateY({imgH - 2}px)}}}}.scan{{animation:scan 6s linear infinite}}"
        "@keyframes grain{0%,49.9%{opacity:0}50%,100%{opacity:1}}.gb{animation:grain 1.2s linear infinite}"
        "@keyframes flick{0%,92%,100%{opacity:1}93%{opacity:.93}94%{opacity:1}96%{opacity:.95}97%{opacity:1}}"
        "@keyframes sp{0%,100%{transform:scale(.55);opacity:.55}50%{transform:scale(1.2);opacity:1}}"
        ".sp{animation:sp 2.4s ease-in-out infinite;transform-box:fill-box;transform-origin:center}"
        "@keyframes bu{0%{transform:translate(0,0);opacity:0}15%{opacity:1}100%{transform:translate(var(--dx),var(--dy));opacity:0}}"
        ".bu{animation:bu 2.4s ease-out infinite}"
        "@keyframes ph{0%{opacity:0}3%,22%{opacity:1}25%,100%{opacity:0}}.ph{opacity:0;animation:ph 14s linear infinite backwards}"
        ".cur{animation:blink 1.05s steps(1) infinite}"
    )
    defs = (f'<clipPath id="ic"><rect x="1" y="{TOP}" width="{imgW}" height="{imgH}"/></clipPath>'
            f'<pattern id="sl" width="4" height="3" patternUnits="userSpaceOnUse"><rect y="2" width="4" height="1" fill="#000" fill-opacity=".18"/></pattern>')
    body = panel(W, H, 8, C["bg"]) + chrome + image + spark + head
    return svg(W, H, body, css, defs, "bilal, index.html",
               "Two dithered pixel hands reaching toward each other inside a pixel window, with a spark between the fingertips. hey, i'm bilal.")


# ------------------------------------------------------------- small pieces --
NAV = [("about", "about"), ("projects", "projects"), ("stack", "stack"), ("music", "music"), ("log", "log"), ("contact", "contact")]


def nav_pill(label):
    s = "./" + label
    w = round(len(s) * 7.4 + 30)
    body = (f'<rect x=".5" y=".5" width="{w - 1}" height="29" rx="14.5" fill="{C["panel"]}" stroke="{C["line"]}"/>'
            + t(w / 2, 19.5, s, 12, C["dim"], anchor="middle"))
    return svg(w, 30, body, "", "", label), w


def contact_pill(label):
    w = round(len(label) * 9.2 + 56)
    body = (f'<rect x=".5" y=".5" width="{w - 1}" height="35" rx="3" fill="{C["bg"]}" stroke="{C["amber"]}"/>'
            f'<rect x="14" y="14" width="8" height="8" fill="{C["amber"]}" class="dot"/>'
            + t(32, 23, label, 12.5, C["amber"], "bold", extra=' letter-spacing="1.2"')
            + t(w - 16, 23, "↗", 13, C["amber"], anchor="end"))
    css = ".dot{animation:pulse 2s ease-in-out infinite}"
    return svg(w, 36, body, css, "", label), w


def heading(idx, title):
    W = 800
    tx, tw, th = pixel_text(title, 44, 8, px=3, size=11, fill=C["fg"])
    x0 = 44 + tw + 20
    L = W - x0
    css = (f"@keyframes run{{0%{{transform:translateX(0);opacity:0}}12%,88%{{opacity:1}}100%{{transform:translateX({L - 26}px);opacity:0}}}}"
           ".run{animation:run 3.6s linear infinite}")
    body = (t(0, 33, idx, 15, C["amber"], "bold")
            + tx
            + f'<line x1="{x0}" y1="30" x2="{W}" y2="30" stroke="{C["faint"]}" stroke-dasharray="2 5"/>'
            + f'<rect class="run" x="{x0}" y="28.5" width="26" height="3" fill="{C["amber"]}"/>')
    return svg(W, 56, body, css, "", f"{idx} {title}")


# -------------------------------------------------------------------- about --
def about():
    W, H = 800, 296
    fig = art.figure()
    uri = png_uri(np.array(fig), scale=1)
    fw = 252
    fh = round(fw * fig.height / fig.width)
    fx, fy = 516, 34
    lines = []
    y = 46

    def para(s, width=50):
        nonlocal y
        for ln in textwrap.wrap(s, width):
            lines.append(t(28, y, ln, 14, C["fg"]))
            y += 22
        y += 12

    para("Student and developer in India. I learn by building things, then finding out why they broke.")
    para("Mostly LLMs, agents and retrieval, plus the backend plumbing that makes them actually run. "
         "I'd rather know how a thing works than just call its API.")
    for k, v in [("now", "building Amethyst, a local-first AI OS"), ("", "learning how inference gets served"),
                 ("off", "PC games, and GNOME that looks like macOS")]:
        if k:
            lines.append(t(28, y, k, 14, C["amber"], "bold"))
        lines.append(t(76, y, v, 14, C["fg"]))
        y += 22
    css = ("@keyframes fs{from{transform:translateY(0)}to{transform:translateY(%dpx)}}.fs{animation:fs 4.5s linear infinite}"
           ".rec{animation:blink 1.4s steps(1) infinite}") % (fh - 2)
    x0, y0, x1, y1, d = fx - 8, fy - 8, fx + fw + 8, fy + fh + 8, 14
    corners = "".join(f'<path d="{p}" stroke="{C["amber"]}" stroke-width="2" fill="none"/>' for p in [
        f"M{x0} {y0 + d}V{y0}H{x0 + d}", f"M{x1 - d} {y0}H{x1}V{y0 + d}",
        f"M{x0} {y1 - d}V{y1}H{x0 + d}", f"M{x1 - d} {y1}H{x1}V{y1 - d}"])
    body = (panel(W, H) + "".join(lines)
            + f'<g clip-path="url(#fc)"><image x="{fx}" y="{fy}" width="{fw}" height="{fh}" xlink:href="{uri}"/>'
            f'<rect class="fs" x="{fx}" y="{fy}" width="{fw}" height="2" fill="{C["amber"]}" fill-opacity=".35"/></g>'
            + corners
            + f'<rect class="rec" x="{fx + 12}" y="{fy + 12}" width="7" height="7" fill="{C["ember"]}"/>'
            + t(fx + 26, fy + 19, "REC", 11, C["ember"], "bold")
            + t(fx + fw / 2, fy + fh + 30, "fig.01 · pixel-me.png", 11, C["dim"], anchor="middle"))
    defs = f'<clipPath id="fc"><rect x="{fx}" y="{fy}" width="{fw}" height="{fh}"/></clipPath>'
    return svg(W, H, body, css, defs, "about",
               "Student and developer in India. Mostly LLMs, agents and retrieval, plus backend plumbing. Now: building Amethyst, learning how inference gets served. Off: PC games, GNOME that looks like macOS.")


# -------------------------------------------------------------------- cards --
CARDS = [
    ("amethyst", "Amethyst", "open source", "Open-source, local-first personal AI OS. A markdown vault on your machine with an agent working on top. Knowledge base first, agent second.",
     ["FastAPI", "React", "SQLite", "MCP"]),
    ("gpt", "GPT from Scratch", "from scratch", "A GPT-style model in PyTorch, written to understand it instead of just using it. Tokenizer, attention, transformer blocks, generation.",
     ["PyTorch", "attention", "tokenizer", "generation"]),
    ("sif", "SIF", "retrieval", "Hybrid retrieval for RAG. Dense search for meaning, keyword search for exact terms, merged with RRF, then reranked.",
     ["dense", "sparse", "RRF", "rerank"]),
]


def card(key, name, kind, desc, tags):
    W, H = 270, 278
    folder = (f'<rect x="18" y="19" width="6" height="3" fill="{C["amber"]}"/><rect x="18" y="22" width="15" height="10" fill="{C["amber"]}"/>')
    d = "".join(t(18, 76 + i * 19, ln, 12.5, C["fg"]) for i, ln in enumerate(textwrap.wrap(desc, 30)))
    rows, cur, x = [], [], 18
    for tag in tags:  # lay chips out in rows first, then pin the block just above the footer
        cw = round(len(tag) * 7 + 16)
        if x + cw > W - 14:
            rows.append(cur)
            cur, x = [], 18
        cur.append((tag, x, cw))
        x += cw + 6
    rows.append(cur)
    y0 = H - 40 - 12 - 25 * len(rows) + 6
    chips = []
    for ri, row in enumerate(rows):
        for tag, cx, cw in row:
            y = y0 + ri * 25
            chips.append(f'<rect x="{cx + .5}" y="{y + .5}" width="{cw}" height="19" rx="2" fill="none" stroke="{C["line"]}"/>'
                         + t(cx + cw / 2 + .5, y + 14, tag, 11, C["dim"], anchor="middle"))
    css = (f"@keyframes sw{{from{{transform:translateX(0)}}to{{transform:translateX({W - 64}px)}}}}.sw{{animation:sw 3.4s ease-in-out infinite alternate}}"
           ".dot{animation:pulse 2s ease-in-out infinite}"
           "@keyframes nudge{0%,100%{transform:translateX(0)}50%{transform:translateX(5px)}}.ar{animation:nudge 1.6s ease-in-out infinite}")
    body = (panel(W, H, 4) + f'<rect class="sw" x="2" y="1" width="60" height="2" fill="{C["amber"]}"/>'
            + folder + t(42, 31, name, 15, C["fg"], "bold")
            + f'<path d="M0 50.5H{W}" stroke="{C["line"]}"/>'
            + d + "".join(chips)
            + f'<path d="M0 {H - 40}.5H{W}" stroke="{C["line"]}"/>'
            + t(18, H - 15, "open repo", 12.5, C["amber"], "bold")
            + f'<text class="m ar" x="98" y="{H - 15}" font-size="12.5" fill="{C["amber"]}">→</text>'
            + t(W - 18, H - 15, kind, 11, C["dim"], anchor="end")
            + f'<circle class="dot" cx="{W - 22}" cy="26" r="3.5" fill="{C["amber"]}"/>')
    return svg(W, H, body, css, "", name, f"{name}: {desc}")


# -------------------------------------------------------------------- stack --
STACK = [
    ("ok", "python.service", "the language I think in"),
    ("ok", "typescript.service", "frontends and glue"),
    ("ok", "pytorch.service", "models, training loops, surgical video"),
    ("ok", "fastapi.service", "backends, including Amethyst's"),
    ("ok", "react.service", "UIs"),
    ("ok", "sqlite.service", "boring storage that works"),
    ("ok", "docker.service", "things that behave"),
    ("ok", "git.service", "GitHub, OAuth flows"),
    ("ok", "mcp.service", "tools for agents"),
    ("ok", "rag.service", "dense + sparse + RRF + rerank"),
    ("ok", "llm-providers.service", "Groq, NVIDIA, Cerebras, Google, OpenRouter"),
    ("ok", "earth-engine.service", "Sentinel-2, Dynamic World (GeoVision)"),
    ("ok", "linux.service", "CachyOS, GNOME, fish"),
    ("warn", "kv-cache.service", "still learning"),
    ("wait", "inference-batching.service", "starting..."),
]


def stack():
    W, ROW, Y0 = 800, 22, 96
    H = Y0 + (len(STACK) + 1) * ROW + 28
    T = 22.0  # seconds per loop
    kfs, rows = [], []

    def kf(name, a, b, c):
        pa, pb, pc = a / T * 100, b / T * 100, c / T * 100
        kfs.append(f"@keyframes {name}{{0%,{pa:.2f}%{{opacity:0}}{pa + .6:.2f}%,{pb:.2f}%{{opacity:1}}{pc:.2f}%,100%{{opacity:0}}}}")

    kf("p0", 0.4, 18.5, 19.5)
    rows.append(f'<g class="ln" style="animation:p0 {T}s linear infinite">' + t(24, 68, "$", 14, C["amber"], "bold")
                + t(44, 68, "systemctl start bilal.target", 14, C["fg"]) + "</g>")
    tag = {"ok": ("OK", C["ok"]), "warn": ("WARN", C["amber"]), "wait": ("....", C["dim"])}
    for i, (st, unit, desc) in enumerate(STACK + [("ok", "", "")]):
        y = Y0 + i * ROW
        last = i == len(STACK)
        kf(f"l{i}", 2.4 + 0.42 * i, 18.5, 19.5)
        label, col = tag[st]
        pad = (" " * ((6 - len(label)) // 2), " " * (6 - len(label) - (6 - len(label)) // 2))
        status = (f'<text class="m" x="24" y="{y}" font-size="13" xml:space="preserve"><tspan fill="{C["dim"]}">[</tspan>'
                  f'<tspan fill="{col}" font-weight="bold">{pad[0]}{label}{pad[1]}</tspan><tspan fill="{C["dim"]}">]</tspan></text>')
        if last:
            body = (f'<text class="m" x="112" y="{y}" font-size="13" fill="{C["fg"]}">Reached target '
                    f'<tspan fill="{C["amber"]}" font-weight="bold">Bilal</tspan>.</text>')
        else:
            word = "Started" if st != "wait" else "Starting"
            body = (f'<text class="m" x="112" y="{y}" font-size="13"><tspan fill="{C["dim"]}">{word} </tspan>'
                    f'<tspan fill="{C["fg"]}">{unit}</tspan></text>' + t(430, y, desc, 13, C["dim"] if st == "ok" else col))
        rows.append(f'<g class="ln" style="animation:l{i} {T}s linear infinite">{status}{body}</g>')
    yc = Y0 + (len(STACK) + 1) * ROW + 2
    kf("lc", 2.4 + 0.42 * (len(STACK) + 1), 18.5, 19.5)
    rows.append(f'<g class="ln" style="animation:lc {T}s linear infinite">' + t(24, yc, "$", 13, C["amber"], "bold")
                + f'<rect class="cur" x="42" y="{yc - 12}" width="8" height="15" fill="{C["amber"]}"/></g>')
    css = "".join(kfs) + ".ln{opacity:0}.cur{animation:blink 1s steps(1) infinite}"
    bar = (f'<rect x=".5" y=".5" width="{W - 1}" height="35" fill="#0d0b09" stroke="{C["line"]}"/>'
           f'<circle cx="22" cy="18" r="5" fill="#d9532c"/><circle cx="40" cy="18" r="5" fill="#e0a030"/><circle cx="58" cy="18" r="5" fill="#6f9a5e"/>'
           + t(W / 2, 23, "bilal@cachyos: ~/stack", 12, C["dim"], anchor="middle"))
    body = f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="6" fill="#0c0b09" stroke="{C["line"]}"/>' + bar + "".join(rows)
    alt = "boot log: " + ", ".join(u.replace(".service", "") for _, u, _ in STACK)
    return svg(W, H, body, css, "", "stack", alt)


# ----------------------------------------------------------------- timeline --
LOG = [
    ("student club", "President, Intellix AI Club", ["Running a student AI club."]),
    ("Jul 2026", "Snowflake Northstar, Pune", ["Attended."]),
    ("Oct 2025 - Apr 2026", "AI/ML intern, DeepSurg AI",
     ["Surgical video analysis (laparoscopic and endoscopic) with PyTorch.", "Annotated data, checked results against surgical validation."]),
    ("2025", "3rd place, Best AI Tool", ["RITECH 2K25."]),
]


def timeline():
    W, X = 800, 200
    y, items, ys = 40, [], []
    for date, title, sub in LOG:
        ys.append(y)
        items.append(t(X - 28, y + 4, date, 12, C["dim"], anchor="end") + t(X + 28, y + 4, title, 15, C["fg"], "bold")
                     + "".join(t(X + 28, y + 28 + i * 19, s, 12.5, C["dim"]) for i, s in enumerate(sub)))
        y += 28 + 19 * len(sub) + 34
    H = y - 6
    nodes = "".join(f'<rect x="{X - 4}" y="{yy - 4}" width="9" height="9" fill="{C["bg"]}" stroke="{C["amber"]}" stroke-width="1.5"/>'
                    f'<rect x="{X - 1.5}" y="{yy - 1.5}" width="4" height="4" fill="{C["amber"]}"/>' for yy in ys)
    run = ys[-1] - ys[0]
    css = (f"@keyframes pk{{0%{{transform:translateY(0);opacity:0}}10%,90%{{opacity:1}}100%{{transform:translateY({run}px);opacity:0}}}}"
           ".pk{animation:pk 4.5s linear infinite}")
    body = (panel(W, H) + f'<line x1="{X + .5}" y1="{ys[0]}" x2="{X + .5}" y2="{ys[-1]}" stroke="{C["faint"]}" stroke-dasharray="2 4"/>'
            + nodes + f'<rect class="pk" x="{X - 1.5}" y="{ys[0]}" width="4" height="10" fill="{C["amber"]}"/>' + "".join(items))
    return svg(W, H, body, css, "", "log", "; ".join(f"{d}: {ti}" for d, ti, _ in LOG))


# ------------------------------------------------------------- view-source --
COMMENTS = [
    "one gradient per page, max",
    "glowing blobs are not a personality",
    "if setup needs fourteen env vars, setup is the bug",
    "i should be able to explain my code without an AI bailing me out. working on it.",
]


def comments():
    W, ROW = 800, 24
    H = 72 + (len(COMMENTS) + 1) * ROW + 12
    tab = (f'<rect x=".5" y=".5" width="{W - 1}" height="35" fill="#0d0b09" stroke="{C["line"]}"/>'
           f'<path d="M16 36V12a6 6 0 0 1 6-6H250a6 6 0 0 1 6 6V36Z" fill="#0c0b09"/>'
           f'<rect x="28" y="15" width="8" height="8" fill="{C["amber"]}"/>' + t(46, 24.5, "view-source:index.html", 12, C["fg"]))
    lines = []
    for i, c in enumerate(COMMENTS):
        y = 36 + 36 + i * ROW
        lines.append(t(44, y, str(i + 1), 12.5, C["faint"], anchor="end")
                     + f'<text class="m" x="64" y="{y}" font-size="13"><tspan fill="{C["amber"]}">&lt;!--</tspan>'
                     f'<tspan fill="{C["dim"]}"> {escape(c)} </tspan><tspan fill="{C["amber"]}">--&gt;</tspan></text>')
    cy = 36 + 36 + len(COMMENTS) * ROW
    css = ".cur{animation:blink 1s steps(1) infinite}"
    body = (f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="6" fill="#0c0b09" stroke="{C["line"]}"/>' + tab + "".join(lines)
            + t(44, cy, str(len(COMMENTS) + 1), 12.5, C["faint"], anchor="end") + f'<rect class="cur" x="64" y="{cy - 12}" width="8" height="15" fill="{C["amber"]}"/>')
    return svg(W, H, body, css, "", "view source", "HTML comments: " + "; ".join(COMMENTS))


# ------------------------------------------------------------------- footer --
def footer():
    img, meta = art.scene()
    W, H, S = 800, 300, 4
    uri = png_uri(img, colors=64, scale=8)
    rnd = random.Random(11)
    ov, css = [], []

    stars = []
    while len(stars) < 34:
        x, y = rnd.randint(2, 197), rnd.randint(2, 28)
        if abs(x - meta["sun"][0]) < 22 and y > 10:
            continue
        stars.append((x, y))
    for i, (x, y) in enumerate(stars):
        d, delay = rnd.uniform(2.2, 6), -rnd.uniform(0, 6)
        ov.append(f'<rect class="tw" x="{x * S}" y="{y * S}" width="{S}" height="{S}" fill="#ffe7b8" style="animation-duration:{d:.1f}s;animation-delay:{delay:.1f}s"/>')
        if i % 6 == 0:  # a few plus-shaped ones
            ov.append(f'<rect class="tw" x="{x * S - S}" y="{y * S}" width="{S}" height="{S}" fill="#ffe7b8" style="animation-duration:{d:.1f}s;animation-delay:{delay:.1f}s"/>'
                      f'<rect class="tw" x="{x * S + S}" y="{y * S}" width="{S}" height="{S}" fill="#ffe7b8" style="animation-duration:{d:.1f}s;animation-delay:{delay:.1f}s"/>')
    for _ in range(26):
        k = rnd.randint(1, 18)
        hw = 2 + k * 0.35
        x = int(meta["sun"][0] + rnd.uniform(-hw, hw))
        ov.append(f'<rect class="gl" x="{x * S}" y="{(meta["hor"] + k) * S}" width="{rnd.choice([2, 3, 4]) * S}" height="{S}" fill="#ffb44a" '
                  f'style="animation-duration:{rnd.uniform(1.6, 4):.1f}s;animation-delay:{-rnd.uniform(0, 4):.1f}s"/>')
    for x, y in meta["lights"]:
        ov.append(f'<rect class="fl" x="{x * S}" y="{y * S}" width="{S}" height="{2 * S}" fill="#ffb02e" style="animation-delay:{-rnd.uniform(0, 3):.1f}s"/>')
    for i in range(16):
        x, y = rnd.randint(160, 197) * S, rnd.randint(40, 58) * S
        ov.append(f'<rect class="em" x="{x}" y="{y}" width="{S}" height="{S}" fill="{rnd.choice(["#ff8a2a", "#ffb02e", "#ff5d2a"])}" '
                  f'style="--dx:{rnd.randint(-40, 30)}px;animation-duration:{rnd.uniform(5, 9):.1f}s;animation-delay:{-rnd.uniform(0, 9):.1f}s"/>')
    for i, (row, dur, shape) in enumerate([(24, 95, [(3, 8), (0, 16), (2, 11)]), (30, 130, [(2, 10), (0, 20), (4, 12)]), (17, 160, [(4, 9), (0, 14), (3, 9)])]):
        rects = "".join(f'<rect x="{xo * S}" y="{(row + j) * S}" width="{w * S}" height="{S}" fill="#3d1f0e" fill-opacity=".85"/>' for j, (xo, w) in enumerate(shape))
        rects += f'<rect x="{shape[0][0] * S}" y="{row * S}" width="{shape[0][1] * S}" height="{S}" fill="#8a4210" fill-opacity=".6"/>'
        ov.append(f'<g class="cl" style="animation-duration:{dur}s;animation-delay:{-i * dur / 3:.0f}s">{rects}</g>')
    for i, (row, dur) in enumerate([(13, 38), (19, 52), (9, 66)]):
        ov.append(f'<g class="bd" style="animation-duration:{dur}s;animation-delay:{-i * 17}s"><path transform="translate(0,{row * S})" d="M0 0h4v4h-4zM4 4h4v4h-4zM8 0h4v4h-4z" fill="#0d0705"/></g>')

    css = (
        "@keyframes tw{0%,100%{opacity:.15}50%{opacity:1}}.tw{animation:tw 4s ease-in-out infinite;opacity:.15}"
        "@keyframes gl{0%,100%{opacity:.1}50%{opacity:.9}}.gl{animation:gl 3s ease-in-out infinite}"
        "@keyframes fl{0%,100%{opacity:.95}18%{opacity:.6}34%{opacity:1}58%{opacity:.7}76%{opacity:.9}}.fl{animation:fl 2.6s linear infinite}"
        "@keyframes em{0%{transform:translate(0,0);opacity:0}12%{opacity:1}100%{transform:translate(var(--dx),-110px);opacity:0}}.em{animation:em 7s linear infinite}"
        "@keyframes cl{from{transform:translateX(-120px)}to{transform:translateX(900px)}}.cl{animation:cl 100s linear infinite}"
        "@keyframes bd{from{transform:translateX(-40px)}to{transform:translateX(860px)}}.bd{animation:bd 50s linear infinite}"
    )
    body = f'<image width="{W}" height="{H}" xlink:href="{uri}"/>' + "".join(ov)
    return svg(W, H, body, css, "", "footer", "A pixel-art dusk scene: a large amber sun behind mountains, a torii gate standing in still water, pine trees and a pagoda on the shore. Stars twinkle and embers drift upward.")


# --------------------------------------------------------------------- main --
def main():
    os.makedirs(OUT, exist_ok=True)
    print("writing assets/")
    save("hero.svg", hero())
    for key, label in NAV:
        save(f"nav-{key}.svg", nav_pill(label)[0])
    for i, (key, title) in enumerate([("about", "about"), ("projects", "projects"), ("stack", "the stack"),
                                      ("music", "music"), ("log", "the log"), ("contact", "say hi")], 1):
        save(f"h-{key}.svg", heading(f"{i:02d}", title))
    save("about.svg", about())
    for c in CARDS:
        save(f"card-{c[0]}.svg", card(*c))
    save("stack.svg", stack())
    save("timeline.svg", timeline())
    save("comments.svg", comments())
    for label in ("AMETHYST", "LINKEDIN", "EMAIL", "RESUME"):
        save(f"pill-{label.lower()}.svg", contact_pill(label)[0])
    save("footer.svg", footer())


if __name__ == "__main__":
    main()
