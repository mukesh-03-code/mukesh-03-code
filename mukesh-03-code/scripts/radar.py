#!/usr/bin/env python3
"""
radar.py — renders the profile's radar charts.

  assets/radar-dark.svg        <- assets/skills.json (self-rated axes)
  assets/radar-light.svg
  assets/radar-langs-dark.svg  <- live language byte counts across your
  assets/radar-langs-light.svg    public repos via the GitHub REST API

The skill radar gets a rotating sweep + pulsing vertices; the language
radar stays calm. All effects are static-safe (base opacity 0).
stdlib only.
"""
import json
import math
import os
import urllib.request

OWNER = "mukesh-03-code"
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(HERE, "assets")

THEMES = {
    "dark":  {"bg": "#0d1117", "border": "#30363d", "grid": "#30363d",
              "axis": "#21262d", "text": "#8b949e", "muted": "#8b949e",
              "green": "#39d353", "title": "#39d353"},
    "light": {"bg": "#ffffff", "border": "#d0d7de", "grid": "#d0d7de",
              "axis": "#eaeef2", "text": "#57606a", "muted": "#57606a",
              "green": "#2ea043", "title": "#1a7f37"},
}


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def radar_svg(title, axes, theme, sweep=False, pulse=False, w=440, h=400):
    t = THEMES[theme]
    n = len(axes)
    cx, cy, r = w / 2, 218, 120

    def pt(i, frac):
        ang = -math.pi / 2 + 2 * math.pi * i / n
        return cx + r * frac * math.cos(ang), cy + r * frac * math.sin(ang)

    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
         f'viewBox="0 0 {w} {h}" role="img" aria-label="{title}">',
         '<defs>'
         f'<linearGradient id="grn" x1="0" y1="0" x2="0" y2="1">'
         f'<stop offset="0%" stop-color="{t["green"]}" stop-opacity="0.55"/>'
         f'<stop offset="100%" stop-color="{t["green"]}" stop-opacity="0.10"/></linearGradient>'
         f'<linearGradient id="sweepG" x1="0" y1="0" x2="1" y2="0">'
         f'<stop offset="0%" stop-color="{t["green"]}" stop-opacity="0.55"/>'
         f'<stop offset="100%" stop-color="{t["green"]}" stop-opacity="0.02"/></linearGradient>'
         '</defs>',
         f'<rect width="{w}" height="{h}" rx="12" fill="{t["bg"]}" stroke="{t["border"]}"/>',
         f'<text x="{cx}" y="34" text-anchor="middle" font-family="\'Courier New\',monospace" '
         f'font-size="16" font-weight="bold" fill="{t["title"]}">{title}</text>',
         f'<rect x="{cx-34}" y="44" width="68" height="3" rx="1.5" fill="{t["green"]}"/>']

    for frac in (0.25, 0.5, 0.75, 1.0):
        pts = " ".join(f"{pt(i, frac)[0]:.1f},{pt(i, frac)[1]:.1f}" for i in range(n))
        p.append(f'<polygon points="{pts}" fill="none" stroke="{t["grid"]}" stroke-width="1" stroke-dasharray="3 4"/>')
    for i in range(n):
        x, y = pt(i, 1)
        p.append(f'<line x1="{cx}" y1="{cy}" x2="{x:.1f}" y2="{y:.1f}" stroke="{t["axis"]}" stroke-width="1"/>')

    if sweep:
        a2 = math.radians(64)
        x2, y2 = cx + r * math.cos(a2), cy + r * math.sin(a2)
        p.append('<g opacity="0">'
                 f'<path d="M{cx} {cy} L{cx+r} {cy} A {r} {r} 0 0 1 {x2:.1f} {y2:.1f} Z" fill="url(#sweepG)"/>'
                 '<animate attributeName="opacity" values="0;1" dur="0.9s" fill="freeze"/>'
                 f'<animateTransform attributeName="transform" type="rotate" values="0 {cx} {cy};360 {cx} {cy}" '
                 'dur="6s" repeatCount="indefinite" calcMode="linear"/></g>')

    dpts = " ".join(f"{pt(i, v/100)[0]:.1f},{pt(i, v/100)[1]:.1f}" for i, (_, v) in enumerate(axes))
    p.append(f'<polygon points="{dpts}" fill="{t["green"]}" fill-opacity="0.18"/>')
    p.append(f'<polygon points="{dpts}" fill="url(#grn)" stroke="{t["green"]}" stroke-width="2.5" stroke-linejoin="round"/>')

    for idx, (_, v) in enumerate(axes):
        x, y = pt(idx, v / 100)
        puls = ""
        if pulse:
            puls = (f'<animate attributeName="r" values="4.5;7;4.5" dur="2.4s" '
                    f'begin="{idx * 0.35:.2f}s" repeatCount="indefinite"/>')
        p.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.5" fill="{t["bg"]}" '
                 f'stroke="{t["green"]}" stroke-width="2.5">{puls}</circle>')
    for i, (lab, v) in enumerate(axes):
        x, y = pt(i, 1.17)
        anchor = "start" if x > cx + 4 else ("end" if x < cx - 4 else "middle")
        p.append(f'<text x="{x:.1f}" y="{y + 4:.1f}" text-anchor="{anchor}" '
                 f'font-family="\'Courier New\',monospace" font-size="11.5" fill="{t["text"]}">'
                 f'{lab} <tspan fill="{t["green"]}" font-weight="bold">{v}</tspan></text>')
    p.append("</svg>")
    return "".join(p)


def lang_bars_svg(entries, theme):
    """Fallback for <3 languages: a radar needs at least a triangle."""
    t = THEMES[theme]
    w, h = 440, 400
    peak = max((b for _, b in entries), default=1)
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
         f'viewBox="0 0 {w} {h}" role="img" aria-label="TOP LANGUAGES">',
         f'<rect width="{w}" height="{h}" rx="12" fill="{t["bg"]}" stroke="{t["border"]}"/>',
         f'<text x="{w/2}" y="34" text-anchor="middle" font-family="\'Courier New\',monospace" '
         f'font-size="16" font-weight="bold" fill="{t["title"]}">TOP LANGUAGES</text>',
         f'<rect x="{w/2-34}" y="44" width="68" height="3" rx="1.5" fill="{t["green"]}"/>']
    from cards import LANG_COLORS  # colour map lives next door
    y = 84
    for lang, bytes_ in entries:
        frac = max(0.06, bytes_ / peak)
        bar_w = int((w - 150) * frac)
        p.append(f'<text x="24" y="{y + 4}" font-family="\'Courier New\',monospace" font-size="12.5" '
                 f'fill="{t["text"]}">{esc(lang)}</text>')
        p.append(f'<rect x="120" y="{y - 12}" width="{bar_w}" height="16" rx="4" '
                 f'fill="{LANG_COLORS.get(lang, t["green"])}" fill-opacity="0.9"/>')
        p.append(f'<text x="{128 + bar_w}" y="{y + 2}" font-family="\'Courier New\',monospace" '
                 f'font-size="11" fill="{t["muted"]}">{bytes_ // 1024} KB</text>')
        y += 44
    p.append('</svg>')
    return "".join(p)


def api(path):
    req = urllib.request.Request(
        f"https://api.github.com{path}",
        headers={"User-Agent": OWNER, "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def language_axes():
    total = {}
    for repo in api(f"/users/{OWNER}/repos?per_page=100"):
        if repo.get("fork"):
            continue
        for lang, bytes_ in api(f"/repos/{OWNER}/{repo['name']}/languages").items():
            total[lang] = total.get(lang, 0) + bytes_
    top = sorted(total.items(), key=lambda kv: kv[1], reverse=True)[:6]
    peak = top[0][1] if top else 1
    return [(lang, max(8, round(100 * b / peak))) for lang, b in top]


def main():
    with open(os.path.join(ASSETS, "skills.json")) as f:
        skills = json.load(f)
    axes = [(a["label"], a["value"]) for a in skills["axes"]]
    langs = language_axes()
    for theme in ("dark", "light"):
        out = os.path.join(ASSETS, f"radar-{theme}.svg")
        with open(out, "w") as f:
            f.write(radar_svg(skills.get("title", "SKILL RADAR").upper(), axes, theme,
                              sweep=True, pulse=True))
        print(f"wrote {out}")
        out = os.path.join(ASSETS, f"radar-langs-{theme}.svg")
        with open(out, "w") as f:
            if len(langs) >= 3:
                f.write(radar_svg("LANGUAGE RADAR", langs, theme))
            else:
                f.write(lang_bars_svg(langs, theme))
        print(f"wrote {out}")


if __name__ == "__main__":
    main()
