#!/usr/bin/env python3
"""Verification for the near floor (run from the repo root after gen_floor.py).

    python3 -I tools/art/floor/check.py OUTDIR [SVG_DIR]

Renders floor_a/b/c.svg (default SVG_DIR = public/assets/svg/environment) with tools/render-svg.mjs and
writes into OUTDIR:
  floor_<v>.png              raw render (transparent)
  strip_<order>.png          tiled strips (50 %), on a dark blue background so the skyline reads
  seams_<order>.png          1:1 crops +-300 px around every seam
  cmp_<v>.png                reference floor (p4 + p6 crops) above the raw render
and prints: shared-zone identity, seam continuity, zone-edge (x=150/1770) cut check, HSV stats of the
opaque pixels and V percentiles / edge strength (to compare with the reference floor).
Needs numpy + Pillow + node (playwright).
"""
import itertools
import os
import subprocess
import sys

import numpy as np
from PIL import Image

W, H, ZONE = 1920, 360, 150
out = sys.argv[1]
svgdir = sys.argv[2] if len(sys.argv) > 2 else 'public/assets/svg/environment'
os.makedirs(out, exist_ok=True)
CROPS = os.environ.get('FLOOR_REF_CROPS', '')


def render(svg, png, scale='1'):
    subprocess.run(['node', 'tools/render-svg.mjs', svg, png, scale, 'transparent'], check=True,
                   stdout=subprocess.DEVNULL)


for v in 'abc':
    render(f'{svgdir}/floor_{v}.svg', f'{out}/floor_{v}.png')
ims = {v: Image.open(f'{out}/floor_{v}.png').convert('RGBA') for v in 'abc'}
A = {v: np.asarray(ims[v]).astype(int) for v in 'abc'}

# ------------------------------------------------------------------ tiling
mx = 0
for v1, v2 in itertools.combinations('abc', 2):
    d = np.abs(A[v1] - A[v2])
    mx = max(mx, d[:, :ZONE].max(), d[:, W - ZONE:].max())
print(f'shared zone identity (x<{ZONE}, x>={W - ZONE}) max channel diff across variants: {mx}')
inner = np.mean([np.abs(A[v][:, 1000] - A[v][:, 1001]).mean() for v in 'abc'])
for v1, v2 in itertools.permutations('abc', 2):
    seam = np.abs(A[v1][:, -1] - A[v2][:, 0]).mean()
    print(f'  seam {v1}|{v2}: mean |col1919-col0| = {seam:.2f}  (typical neighbour columns {inner:.2f})')
for v in 'abc':
    for x in (ZONE, W - ZONE):
        c = np.abs(A[v][:, x - 1, :3] - A[v][:, x, :3]).max(axis=1)
        ref = np.abs(A[v][:, x - 6, :3] - A[v][:, x - 5, :3]).max(axis=1)
        print(f'  zone edge {v} x={x}: rows with a >40 jump {int((c > 40).sum())} (control {int((ref > 40).sum())}), '
              f'mean jump {c.mean():.2f} (control {ref.mean():.2f})')
for v in 'abc':
    al = A[v][:, :, 3]
    tops = [int(np.argmax(al[:, x] > 127)) for x in (0, 1, 1918, 1919)]
    print(f'  contour {v}: first opaque y at x=0,1,1918,1919 -> {tops}')

# ------------------------------------------------------------------ strips / seams
bg = (31, 48, 82, 255)
for o in ('abc', 'bca', 'cab', 'aba', 'cbc'):
    s = Image.new('RGBA', (W * len(o), H), bg)
    for i, k in enumerate(o):
        s.alpha_composite(ims[k], (W * i, 0))
    s.convert('RGB').resize((W * len(o) // 2, H // 2), Image.LANCZOS).save(f'{out}/strip_{o}.png')
    crops = [s.crop((W * i - 300, 0, W * i + 300, H)).convert('RGB') for i in range(1, len(o))]
    sv = Image.new('RGB', (610 * len(crops) - 10, H), (0, 0, 0))
    for i, c in enumerate(crops):
        sv.paste(c, (610 * i, 0))
    sv.save(f'{out}/seams_{o}.png')


# ------------------------------------------------------------------ colour / value
def hsv(rgb):
    rgb = rgb.astype(float) / 255
    mxv = rgb.max(1)
    mnv = rgb.min(1)
    s = np.where(mxv > 0, (mxv - mnv) / np.maximum(mxv, 1e-6), 0)
    return mxv, s


def edge_strength(rgb2d):
    g = rgb2d.astype(float).mean(2)
    gx = np.abs(np.diff(g, axis=1))[:-1, :]
    gy = np.abs(np.diff(g, axis=0))[:, :-1]
    return float(np.hypot(gx, gy).mean())


for v in 'abc':
    a = A[v]
    m = a[:, :, 3] > 250
    rgb = a[:, :, :3][m]
    V, S = hsv(rgb)
    mean = rgb.mean(0)
    p = np.percentile(V, [2, 10, 50, 90, 98])
    # contiguous opaque window for edge strength: y 150..360 (below every contour)
    es = edge_strength(a[150:360, ZONE:W - ZONE, :3])
    print(f'{v}: mean #{int(mean[0]):02x}{int(mean[1]):02x}{int(mean[2]):02x}  V {V.mean():.3f}  S {S.mean():.3f}  '
          f'Vstd {V.std():.3f}  V p2/10/50/90/98 {" ".join(f"{q:.2f}" for q in p)}  edge {es:.2f}')

if CROPS and os.path.isdir(CROPS):
    p4 = Image.open(os.path.join(CROPS, 'p4_vessel.png')).convert('RGB')
    s4 = 1920 / p4.width
    r4 = p4.resize((1920, round(p4.height * s4))).crop((0, round(250 * s4), 1920, round(530 * s4)))
    p6 = Image.open(os.path.join(CROPS, 'p6_vitamins.png')).convert('RGB')
    s6 = 1920 / p6.width
    r6 = p6.resize((1920, round(p6.height * s6))).crop((0, round(300 * s6), 1920, round(510 * s6)))
    a4 = np.asarray(r4).astype(int)
    print('reference p4 floor crop edge strength (same metric):', round(edge_strength(a4[a4.shape[0] // 2:, :, :]), 2))
    for v in 'abc':
        fl = Image.new('RGBA', (W, H), bg)
        fl.alpha_composite(ims[v])
        im = Image.new('RGB', (1920, r4.height + r6.height + H + 20), (34, 34, 34))
        im.paste(r4, (0, 0))
        im.paste(r6, (0, r4.height + 10))
        im.paste(fl.convert('RGB'), (0, r4.height + r6.height + 20))
        im.save(f'{out}/cmp_{v}.png')
