"""Build the static art for the README (hero/outro GIFs, dossier, headers, project cards).

Local only, not run in CI. Needs rsvg-convert, ffmpeg, Noto Serif CJK JP and JetBrains Mono.
Usage: python scripts/build_assets.py [--no-gif]
Edit PROJECTS / DOSSIER below, then rerun.
"""
import base64
import os
import subprocess
import sys
import tempfile
from html import escape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")
VIDEOS = os.path.expanduser("~/Videos/Wallpapers")

BG, PANEL, LINE = "#0a0a0a", "#101010", "#242424"
RED, DEEP, BONE, MUTED = "#e01b24", "#5c0a0d", "#ece7df", "#7d7d7d"
KANJI = "Noto Serif CJK JP"
MONO = "JetBrains Mono"
W = 900

DOSSIER = [
    ("SUBJECT", "Arpit Goswami // rarestpreet"),
    ("GRADE", "Special Grade Backend Sorcerer"),
    ("AFFILIATION", "B.Tech, Information Technology"),
    ("TECHNIQUE", "Distributed systems, rate limiting,"),
    ("", "auth, microservices"),
    ("BINDING VOW", "Java · Spring Boot · Redis"),
    ("TOOLS", "React · Node · Docker · Postgres"),
    ("STATUS", "Active. Building at scale."),
]

# name, kanji index, description lines, stack, status ("live" | "sealed" | "source"), filename
PROJECTS = [
    ("LIMITZZ", "壱", ["Distributed Rate Limiter as a Service.", "8,180+ RPS, sub-2ms P95, zero races."],
     "Java 21 · Spring Boot 3 · Redis Lua", "sealed", "limitzz"),
    ("HEARMEOUT", "弐", ["Community QnA & discussion platform", "with stateless auth and RBAC."],
     "Spring Boot · React · JWT", "live", "hearmeout"),
    ("AUTHIFY", "参", ["Full auth system: register, verify,", "reset, sessions. Spring Security."],
     "Spring Security · React", "live", "authify"),
    ("SHAWTY", "肆", ["URL shortener + link analytics.", "Base62 IDs, aliases, QR, expiry."],
     "Node · Express · MongoDB · Redis", "sealed", "shawty"),
    ("CURSOR PAGINATION", "伍", ["Keyset pagination over large datasets,", "stable while data changes."],
     "Spring Boot · PostgreSQL", "live", "cursor"),
    ("WHATSAPP BOT SIM", "陸", ["Chatbot webhook backend that", "simulates WhatsApp message flows."],
     "Spring Boot · REST", "live", "whatsapp"),
    ("SHAWTY EXTENSION", "漆", ["Manifest V3 Chrome extension that", "auto-shortens copied URLs."],
     "JavaScript · Chrome MV3", "source", "shawty-ext"),
    ("TRADING SIGNALS", "捌", ["Crypto signal listener with Binance", "API, scheduled jobs and CI/CD."],
     "Spring Boot · Redis · Docker", "source", "trading"),
]

SECTIONS = [
    ("壱", "DOSSIER", "人物記録", "01"),
    ("弐", "TECHNIQUES", "術式 — projects", "02"),
    ("参", "ARSENAL", "呪具 — languages", "03"),
    ("肆", "RECORD", "戦績 — lifetime commits", "04"),
    ("伍", "HISTORY", "歴史 — git history", "05"),
    ("陸", "CONTACT", "連絡", "06"),
]


def svg(w, h, body, bg=True):
    fill = f'<rect width="{w}" height="{h}" fill="{BG}"/>' if bg else ""
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">{fill}{body}</svg>'


def t(x, y, s, size, color, font=MONO, weight=400, anchor="start", spacing=0, opacity=1):
    return (f'<text x="{x}" y="{y}" font-family="{font}" font-size="{size}" font-weight="{weight}" fill="{color}" '
            f'text-anchor="{anchor}" letter-spacing="{spacing}" opacity="{opacity}">{escape(s)}</text>')


def brackets(x, y, w, h, n=14, color=RED, sw=2):
    p = (f"M{x},{y + n} V{y} H{x + n} M{x + w - n},{y} H{x + w} V{y + n} "
         f"M{x + w},{y + h - n} V{y + h} H{x + w - n} M{x + n},{y + h} H{x} V{y + h - n}")
    return f'<path d="{p}" fill="none" stroke="{color}" stroke-width="{sw}"/>'


def render(name, content, w, h):
    src = os.path.join(ASSETS, "src", name + ".svg")
    os.makedirs(os.path.dirname(src), exist_ok=True)
    with open(src, "w", encoding="utf-8") as f:
        f.write(content)
    out = os.path.join(ASSETS, name + ".png")
    subprocess.run(["rsvg-convert", "-w", str(w * 2), "-h", str(h * 2), src, "-o", out], check=True)
    return out


def header(kanji, title, sub, idx):
    h = 86
    body = (t(4, 66, kanji, 62, RED, KANJI, 900)
            + t(84, 40, title, 26, BONE, MONO, 800, spacing=8)
            + t(86, 66, sub, 14, MUTED, KANJI, 400, spacing=2)
            + f'<line x1="330" y1="34" x2="{W - 60}" y2="34" stroke="{LINE}" stroke-width="1"/>'
            + f'<line x1="330" y1="34" x2="390" y2="34" stroke="{RED}" stroke-width="3"/>'
            + t(W, 40, f"// {idx}", 13, MUTED, anchor="end", spacing=2))
    return svg(W, h, body, bg=False)


def dossier():
    h = 404
    with open(os.path.join(ASSETS, "profile.jpg"), "rb") as f:
        photo = base64.b64encode(f.read()).decode()
    px, py, ps = 24, 26, 352
    body = (f'<rect x="0.5" y="0.5" width="{W - 1}" height="{h - 1}" fill="{PANEL}" stroke="{LINE}"/>'
            f'<rect x="0" y="0" width="4" height="{h}" fill="{RED}"/>'
            f'<image x="{px}" y="{py}" width="{ps}" height="{ps}" href="data:image/jpeg;base64,{photo}" preserveAspectRatio="xMidYMid slice"/>'
            + brackets(px - 8, py - 8, ps + 16, ps + 16)
            + t(px + 6, py + ps - 10, "SUBJECT PHOTO // 0675", 10, BONE, spacing=2, opacity=.8))
    x0, y = 414, 52
    body += t(x0, y, "JUJUTSU HIGH — PERSONNEL FILE", 12, RED, weight=700, spacing=4)
    body += t(W - 24, y, "呪術高専", 14, MUTED, KANJI, 700, anchor="end")
    body += f'<line x1="{x0}" y1="{y + 14}" x2="{W - 24}" y2="{y + 14}" stroke="{LINE}"/>'
    y += 46
    for label, value in DOSSIER:
        if label:
            body += t(x0, y, label, 11, MUTED, weight=700, spacing=3)
        body += t(x0 + 128, y, value, 14, BONE)
        y += 29
    # stamp
    body += (f'<g transform="translate({W - 138},{h - 58}) rotate(-8)" opacity=".9">'
             f'<rect x="-104" y="-30" width="208" height="60" fill="none" stroke="{RED}" stroke-width="3"/>'
             f'<rect x="-98" y="-24" width="196" height="48" fill="none" stroke="{RED}" stroke-width="1"/>'
             + t(-58, 11, "機密", 28, RED, KANJI, 900, anchor="middle")
             + t(38, -1, "CLASSIFIED", 13, RED, weight=800, anchor="middle", spacing=2)
             + t(38, 15, "SPECIAL GRADE", 9, RED, weight=700, anchor="middle", spacing=2)
             + "</g>")
    # barcode
    bx = x0
    for i, wbar in enumerate([2, 1, 3, 1, 1, 2, 4, 1, 2, 1, 3, 2, 1, 1, 3, 1, 2, 2, 1, 4, 1, 2, 1, 3]):
        if i % 2 == 0:
            body += f'<rect x="{bx}" y="{h - 54}" width="{wbar * 1.5}" height="26" fill="{BONE}" opacity=".55"/>'
        bx += wbar * 1.5 + 1.5
    body += t(x0, h - 16, "FILE 0675-RP // GRADE 1+", 10, MUTED, spacing=2)
    return svg(W, h, body), h


def card(p):
    name, kanji, lines, stack, status, _ = p
    w, h = 440, 190
    sealed = status == "sealed"
    accent = MUTED if sealed else RED
    body = (f'<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" fill="{PANEL}" stroke="{LINE}"/>'
            f'<rect x="0" y="0" width="{w}" height="3" fill="{accent}"/>'
            + t(w - 18, h - 14, kanji, 120, "#161616", KANJI, 900, anchor="end")
            + t(22, 46, name, 22, BONE, weight=800, spacing=3))
    if status == "live":
        body += (f'<circle cx="{w - 74}" cy="34" r="4" fill="{RED}"/>'
                 + t(w - 22, 38, "LIVE", 12, RED, weight=800, anchor="end", spacing=3))
    elif sealed:
        body += t(w - 22, 38, "封印 SEALED", 12, MUTED, KANJI, 700, anchor="end", spacing=2)
    else:
        body += t(w - 22, 38, "SOURCE", 12, BONE, weight=700, anchor="end", spacing=3, opacity=.7)
    for i, line in enumerate(lines):
        body += t(22, 80 + i * 22, line, 13.5, "#b9b4ac")
    body += f'<line x1="22" y1="{h - 50}" x2="{w - 22}" y2="{h - 50}" stroke="{LINE}"/>'
    body += t(22, h - 24, stack.upper(), 11, accent if not sealed else MUTED, weight=700, spacing=1.5)
    cta = "PRIVATE" if sealed else ("OPEN ↗" if status == "live" else "REPO ↗")
    body += t(w - 22, h - 24, cta, 11, BONE, weight=700, anchor="end", spacing=2, opacity=.85)
    return svg(w, h, body), w, h


def overlay_hero():
    w, h = W, 300
    body = (f'<defs><linearGradient id="g" x1="0" x2="1"><stop offset="0" stop-color="#000" stop-opacity=".92"/>'
            f'<stop offset=".55" stop-color="#000" stop-opacity=".55"/><stop offset="1" stop-color="#000" stop-opacity="0"/></linearGradient>'
            f'<linearGradient id="v" x1="0" y1="0" x2="0" y2="1"><stop offset=".6" stop-color="#000" stop-opacity="0"/>'
            f'<stop offset="1" stop-color="#000" stop-opacity=".8"/></linearGradient></defs>'
            f'<rect width="{w}" height="{h}" fill="url(#g)"/><rect width="{w}" height="{h}" fill="url(#v)"/>'
            f'<rect width="{w}" height="18" fill="#000"/><rect y="{h - 18}" width="{w}" height="18" fill="#000"/>'
            + t(40, 52, "CASE FILE 0675  //  呪術高専", 12, MUTED, KANJI, 500, spacing=3)
            + t(40, 140, "ARPIT", 70, BONE, MONO, 800, spacing=10)
            + t(40, 208, "GOSWAMI", 70, RED, MONO, 800, spacing=10)
            + f'<rect x="42" y="226" width="70" height="3" fill="{RED}"/>'
            + t(40, 256, "BACKEND SORCERER — JAVA · SPRING BOOT · DISTRIBUTED SYSTEMS", 12, "#bdbdbd", spacing=2))
    for i, ch in enumerate("特級呪術師"):
        body += t(w - 44, 68 + i * 46, ch, 38, RED, KANJI, 900, anchor="middle", opacity=.9)
    return svg(w, h, body, bg=False), w, h


def overlay_outro():
    w, h = W, 220
    body = (f'<rect width="{w}" height="{h}" fill="#000" opacity=".35"/>'
            f'<rect width="{w}" height="14" fill="#000"/><rect y="{h - 14}" width="{w}" height="14" fill="#000"/>'
            + t(40, 128, "領域展開", 64, RED, KANJI, 900)
            + t(42, 162, "DOMAIN EXPANSION", 13, BONE, weight=700, spacing=6)
            + t(w - 40, 128, "You're already inside.", 18, BONE, anchor="end")
            + t(w - 40, 156, "SAY WHAT YOU NEED ↓", 12, MUTED, weight=700, anchor="end", spacing=4))
    return svg(w, h, body, bg=False), w, h


def gif(video, overlay_svg, w, h, out, start=0, dur=6, focus_y=0.5):
    with tempfile.TemporaryDirectory() as tmp:
        ov = os.path.join(tmp, "ov.png")
        with open(os.path.join(tmp, "ov.svg"), "w", encoding="utf-8") as f:
            f.write(overlay_svg)
        subprocess.run(["rsvg-convert", "-w", str(w), "-h", str(h), os.path.join(tmp, "ov.svg"), "-o", ov], check=True)
        crop = f"crop=iw:iw*{h}/{w}:0:(ih-iw*{h}/{w})*{focus_y}"
        vf = (f"[0:v]fps=12,{crop},scale={w}:{h}:flags=lanczos,eq=brightness=-0.04:saturation=1.1[b];"
              f"[b][1:v]overlay=0:0,split[a][c];[a]palettegen=max_colors=128:stats_mode=diff[p];"
              f"[c][p]paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle")
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", str(start), "-t", str(dur), "-i", video,
                        "-i", ov, "-filter_complex", vf, out], check=True)


def main():
    for k, title, sub, idx in SECTIONS:
        render(f"h-{idx}", header(k, title, sub, idx), W, 86)
    d, h = dossier()
    render("dossier", d, W, h)
    for p in PROJECTS:
        c, w, h = card(p)
        render(f"card-{p[5]}", c, w, h)
    if "--no-gif" not in sys.argv:
        o, w, h = overlay_hero()
        gif(os.path.join(VIDEOS, "yuji-itadori-red-dark-jujutsu-kaisen-4k-live-wallpaper.mp4"), o, w, h,
            os.path.join(ASSETS, "hero.gif"), dur=7.2, focus_y=0.35)
        o, w, h = overlay_outro()
        gif(os.path.join(VIDEOS, "jujutsu-kaisen-glowing-mahoraga-live-wallpaper.mp4"), o, w, h,
            os.path.join(ASSETS, "outro.gif"), dur=6, focus_y=0.5)


if __name__ == "__main__":
    main()
