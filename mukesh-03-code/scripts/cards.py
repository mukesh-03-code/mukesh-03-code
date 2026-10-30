#!/usr/bin/env python3
"""
cards.py — renders the profile's SVG cards (self-hosted, like the
original theme: deliberately NOT github-readme-stats, so a slow public
instance can never take the section down).

  assets/card-stats-dark.svg / card-stats-light.svg
      repos / stars / followers / following, live from the API.
  assets/card-<name>-dark.svg / card-<name>-light.svg
      one card per entry in assets/projects.json. Entries with a "repo"
      get live stars / forks / primary language; entries with a "link"
      (e.g. the portfolio) render as a static call-to-card.

stdlib only.
"""
import json
import os
import textwrap
import urllib.request

OWNER = "mukesh-03-code"
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(HERE, "assets")

LANG_COLORS = {"Python": "#3572A5", "C++": "#f34b7d", "C": "#555555",
               "JavaScript": "#f1e05a", "TypeScript": "#3178c6",
               "HTML": "#e34c26", "CSS": "#563d7c", "Java": "#b07219",
               "Shell": "#89e051", "Ruby": "#701516", "Go": "#00ADD8"}

THEMES = {
    "dark": {"bg": "#0d1117", "border": "#30363d", "title": "#39d353",
             "text": "#c9d1d9", "muted": "#8b949e", "chip": "#161b22"},
    "light": {"bg": "#ffffff", "border": "#d0d7de", "title": "#1a7f37",
              "text": "#1f2328", "muted": "#57606a", "chip": "#f6f8fa"},
}


def api(path):
    req = urllib.request.Request(
        f"https://api.github.com{path}",
        headers={"User-Agent": OWNER, "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def stats_card(theme):
    t = THEMES[theme]
    me = api(f"/users/{OWNER}")
    repos = api(f"/users/{OWNER}/repos?per_page=100")
    stars = sum(r.get("stargazers_count", 0) for r in repos if not r.get("fork"))
    since = me["created_at"][:4]
    w, h = 480, 160
    stats = [("REPOS", me["public_repos"]), ("STARS", stars),
             ("FOLLOWERS", me["followers"]), ("SINCE", since)]
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
         f'viewBox="0 0 {w} {h}" role="img" aria-label="GitHub statistics">',
         f'<rect width="{w}" height="{h}" rx="12" fill="{t["bg"]}" stroke="{t["border"]}"/>',
         f'<text x="20" y="34" font-family="\'Courier New\',monospace" font-size="15" '
         f'font-weight="bold" fill="{t["title"]}">// {esc((me.get("name") or OWNER).upper())}</text>',
         f'<text x="{w-20}" y="34" text-anchor="end" font-family="\'Courier New\',monospace" '
         f'font-size="12" fill="{t["muted"]}">@{OWNER}</text>']
    box_w = (w - 40 - 3 * 10) / 4
    for i, (label, val) in enumerate(stats):
        x = 20 + i * (box_w + 10)
        p.append(f'<rect x="{x:.0f}" y="52" width="{box_w:.0f}" height="84" rx="8" '
                 f'fill="{t["chip"]}" stroke="{t["border"]}"/>')
        p.append(f'<text x="{x + box_w/2:.0f}" y="90" text-anchor="middle" font-family="\'Courier New\',monospace" '
                 f'font-size="24" font-weight="bold" fill="{t["title"]}">{esc(val)}</text>')
        p.append(f'<text x="{x + box_w/2:.0f}" y="115" text-anchor="middle" font-family="\'Courier New\',monospace" '
                 f'font-size="11" fill="{t["muted"]}" letter-spacing="1">{label}</text>')
    p.append("</svg>")
    return "".join(p)


def project_card(name, meta, theme, live):
    t = THEMES[theme]
    w, h = 420, 190
    title = meta.get("title", name.replace("-", " ").replace("_", " "))
    desc = textwrap.wrap(meta.get("description", ""), width=46)[:3]
    accent = meta.get("color", t["title"])
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
         f'viewBox="0 0 {w} {h}" role="img" aria-label="{esc(title)}">',
         f'<rect width="{w}" height="{h}" rx="12" fill="{t["bg"]}" stroke="{t["border"]}"/>',
         f'<rect x="0" y="0" width="6" height="{h}" rx="3" fill="{accent}"/>',
         f'<text x="22" y="34" font-family="\'Courier New\',monospace" font-size="15" '
         f'font-weight="bold" fill="{accent}">{esc(title)}</text>']
    y = 62
    for line in desc:
        p.append(f'<text x="22" y="{y}" font-family="\'Courier New\',monospace" font-size="11.5" '
                 f'fill="{t["text"]}">{esc(line)}</text>')
        y += 18
    if live:
        lang = live.get("language") or ""
        stars = live.get("stargazers_count", 0)
        forks = live.get("forks_count", 0)
        chip_y = h - 40
        if lang:
            lc = LANG_COLORS.get(lang, t["muted"])
            p.append(f'<circle cx="28" cy="{chip_y - 4}" r="5" fill="{lc}"/>')
            p.append(f'<text x="40" y="{chip_y}" font-family="\'Courier New\',monospace" '
                     f'font-size="11" fill="{t["muted"]}">{esc(lang)}</text>')
        p.append(f'<text x="{w-22}" y="{chip_y}" text-anchor="end" font-family="\'Courier New\',monospace" '
                 f'font-size="11" fill="{t["muted"]}">★ {stars}  ⑂ {forks}</text>')
    else:
        p.append(f'<text x="22" y="{h-36}" font-family="\'Courier New\',monospace" font-size="11" '
                 f'fill="{t["muted"]}">↗ {esc(meta.get("link", ""))}</text>')
    p.append("</svg>")
    return "".join(p)


def main():
    with open(os.path.join(ASSETS, "projects.json")) as f:
        projects = json.load(f)["projects"]
    cache = {r["name"]: r for r in api(f"/users/{OWNER}/repos?per_page=100")}
    for theme in ("dark", "light"):
        out = os.path.join(ASSETS, f"card-stats-{theme}.svg")
        with open(out, "w") as f:
            f.write(stats_card(theme))
        print(f"wrote {out}")
        for proj in projects:
            live = cache.get(proj.get("repo", ""), None) if proj.get("repo") else None
            out = os.path.join(ASSETS, f"card-{proj['name']}-{theme}.svg")
            with open(out, "w") as f:
                f.write(project_card(proj["name"], proj, theme, live))
            print(f"wrote {out}")


if __name__ == "__main__":
    main()
