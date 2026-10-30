#!/usr/bin/env python3
"""
dotify.py — photo -> animated matrix-duotone pixel portrait (SVG).

Used by this profile to render assets/portrait.svg from assets/mukesh.png.
Pipeline: grayscale -> autocontrast -> downscale -> gradient flood-fill
background removal -> quantize to a green ramp -> run-length encode rows
-> one <path> per palette colour. With --animate it adds a boot-wipe
reveal, a looping scanline, random pixel sparkles/dropouts and a HUD
frame. Every animated element degrades to a clean static state if the
animation is stripped (base opacity 0 on effects, base visible pixels).

Usage:
    python scripts/dotify.py assets/mukesh.png -o assets/portrait.svg \
        --cols 64 --cell 7 --animate

stdlib only — no third-party dependencies.
"""
import argparse
import random
from collections import deque
from PIL import Image, ImageOps, ImageEnhance

RAMP = [(0, (8, 19, 13)), (40, (15, 45, 26)), (90, (24, 90, 46)),
        (140, (34, 150, 68)), (185, (57, 211, 83)), (255, (126, 231, 135))]
HEX = ["#08130d", "#0f2d1a", "#185a2e", "#229644", "#39d353", "#7ee787"]
BG = "#0d1117"
BORDER = "#30363d"
GREEN = "#39d353"
MUTED = "#8b949e"
SPARKLE = "#b7f7c1"


def build_grid(path, n, t1=175, floor=130, delta=60):
    img = Image.open(path).convert("L")
    img = ImageOps.autocontrast(img, cutoff=2)
    img = ImageEnhance.Contrast(img).enhance(1.10)
    small = img.resize((n, n), Image.LANCZOS)
    px = small.load()

    # flood from the borders: eat bright bg, follow the soft shadow
    # gradient, stop at hard dark edges (hair / glasses / shirt)
    skip = [[False] * n for _ in range(n)]
    q = deque()

    def seed(x, y):
        if px[x, y] >= t1 and not skip[x][y]:
            skip[x][y] = True
            q.append((x, y))

    for i in range(n):
        seed(i, 0); seed(i, n - 1); seed(0, i); seed(n - 1, i)
    while q:
        x, y = q.popleft()
        base = px[x, y]
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < n and 0 <= ny < n and not skip[nx][ny]:
                v = px[nx, ny]
                if v >= floor and v >= base - delta:
                    skip[nx][ny] = True
                    q.append((nx, ny))

    anchors = [a for a, _ in RAMP]
    grid, kept = [[None] * n for _ in range(n)], []
    for y in range(n):
        for x in range(n):
            if not skip[x][y]:
                ci = min(range(len(anchors)), key=lambda i: abs(px[x, y] - anchors[i]))
                grid[y][x] = ci
                kept.append((x, y, ci))
    return grid, kept


def rle_paths(grid, n, cell, gap):
    runs = {i: [] for i in range(len(HEX))}
    for y in range(n):
        x = 0
        while x < n:
            ci = grid[y][x]
            if ci is None:
                x += 1
                continue
            x0 = x
            while x < n and grid[y][x] == ci:
                x += 1
            w = (x - x0) * cell - gap
            runs[ci].append(f"M{x0*cell} {y*cell}h{w:.1f}v{cell-gap:.1f}h-{w:.1f}z")
    return "".join(
        f'<path d="{"".join(runs[c])}" fill="{HEX[c]}"/>'
        for c in range(len(HEX)) if runs[c]
    )


def sparkle_overlays(kept, cell, seed=20261029, n_spark=20, n_drop=10):
    rng = random.Random(seed)
    bright = [p for p in kept if p[2] >= 3]
    dark = [p for p in kept if p[2] <= 4]
    spark = rng.sample(bright, min(n_spark, len(bright)))
    used = set(spark)
    pool = [p for p in dark if p not in used]
    drop = rng.sample(pool, min(n_drop, len(pool)))
    out = ""
    for i, (x, y, _) in enumerate(spark):
        out += (f'<rect x="{x*cell}" y="{y*cell}" width="{cell}" height="{cell}" fill="{SPARKLE}" opacity="0">'
                f'<animate attributeName="opacity" values="0;0;1;1;0" keyTimes="0;0.72;0.78;0.94;1" '
                f'dur="{3.2 + (i % 5) * 0.7:.1f}s" begin="{1.9 + i*0.21:.2f}s" repeatCount="indefinite"/></rect>')
    for i, (x, y, _) in enumerate(drop):
        out += (f'<rect x="{x*cell}" y="{y*cell}" width="{cell}" height="{cell}" fill="{BG}" opacity="0">'
                f'<animate attributeName="opacity" values="0;0;1;1;0" keyTimes="0;0.55;0.62;0.9;1" '
                f'dur="{4.0 + (i % 4) * 0.9:.1f}s" begin="{2.3 + i*0.37:.2f}s" repeatCount="indefinite"/></rect>')
    return out


def portrait_svg(path, cols=64, cell=7, animate=True, gap=0.6):
    grid, kept = build_grid(path, cols)
    n, z0 = cols, 10
    w = cols * cell + 2 * z0
    h = w + 28  # pixel zone + label band
    z1 = z0 + n * cell
    paths = rle_paths(grid, n, cell, gap)
    fx0, fw = 6, w - 12

    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
           f'viewBox="0 0 {w} {h}" role="img" aria-label="Animated pixel portrait of Mukesh">',
           f'<rect x="{fx0}" y="{fx0}" width="{fw}" height="{fw}" rx="12" fill="{BG}" stroke="{BORDER}"/>',
           f'<g transform="translate({z0},{z0})">{paths}']
    if animate:
        svg.append(sparkle_overlays(kept, cell))
    svg.append('</g>')
    # HUD corner brackets
    a, b, c = z0 - 4, z0 + n * cell + 4, z0 + 24
    svg.append(f'<g stroke="{GREEN}" stroke-width="3" fill="none" stroke-linecap="square">'
               f'<path d="M{a} {c} V{a} H{c}"/><path d="M{b} {c} V{a} H{b-24}"/>'
               f'<path d="M{a} {b-24} V{b} H{c}"/><path d="M{b} {b-24} V{b} H{b-24}"/></g>')
    # REC indicator + labels
    rec = f'<circle cx="{w-22}" cy="24" r="5" fill="{GREEN}"/>'
    if animate:
        rec = (f'<circle cx="{w-22}" cy="24" r="5" fill="{GREEN}">'
               '<animate attributeName="opacity" values="1;1;0;0;1" keyTimes="0;0.5;0.56;0.94;1" '
               'dur="1.6s" repeatCount="indefinite"/></circle>')
    svg.append(rec)
    svg.append(f'<text x="{w-34}" y="28" text-anchor="end" font-family="\'Courier New\',monospace" '
               f'font-size="11" fill="{GREEN}" letter-spacing="2">REC</text>')
    svg.append(f'<text x="16" y="{h-9}" font-family="\'Courier New\',monospace" font-size="11" '
               f'fill="{MUTED}">SCAN://IDENT_MUKESH</text>')
    svg.append(f'<text x="{w-16}" y="{h-9}" text-anchor="end" font-family="\'Courier New\',monospace" '
               f'font-size="11" fill="{MUTED}">{cols}x{cols} · MATRIX DUOTONE</text>')
    if animate:
        # boot wipe (base opacity 0 -> static-safe)
        svg.append(f'<g opacity="0">'
                   f'<rect x="4" y="4" width="{w-8}" height="{w-8}" fill="{BG}"/>'
                   f'<rect x="4" y="4" width="{w-8}" height="3" fill="{GREEN}"/>'
                   '<animate attributeName="opacity" values="0;1;1" keyTimes="0;0.005;1" dur="1.5s" fill="freeze"/>'
                   f'<animateTransform attributeName="transform" type="translate" values="0 0;0 {h+20}" dur="1.5s" fill="freeze"/>'
                   '</g>')
        # idle scanline (base opacity 0 -> static-safe)
        svg.append(f'<g opacity="0">'
                   f'<rect x="{z0}" y="-18" width="{n*cell}" height="18" fill="{GREEN}" fill-opacity="0.32"/>'
                   '<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;0.06;0.94;1" dur="2.6s" begin="1.8s" repeatCount="indefinite"/>'
                   f'<animateTransform attributeName="transform" type="translate" values="0 {z0};0 {z1}" dur="2.6s" begin="1.8s" repeatCount="indefinite"/>'
                   '</g>')
    svg.append('</svg>')
    return "".join(svg)


def main():
    ap = argparse.ArgumentParser(description="Photo -> animated pixel portrait SVG")
    ap.add_argument("input")
    ap.add_argument("-o", "--output", default="assets/portrait.svg")
    ap.add_argument("--cols", type=int, default=64)
    ap.add_argument("--cell", type=int, default=7)
    ap.add_argument("--animate", action="store_true")
    args = ap.parse_args()
    svg = portrait_svg(args.input, cols=args.cols, cell=args.cell, animate=args.animate)
    with open(args.output, "w") as f:
        f.write(svg)
    print(f"wrote {args.output} ({len(svg)} bytes)")


if __name__ == "__main__":
    main()
