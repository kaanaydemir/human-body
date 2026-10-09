#!/usr/bin/env python3
"""Verification for the rear wall layer (run from the repo root after gen.py).

    python3 -I tools/art/rear/check.py OUTDIR

Renders rear_a/rear_b (+ the far layer and the gen.py --debug masks) with tools/render-svg.mjs and writes:
  OUTDIR/rear_<v>.png           raw render (transparent)
  OUTDIR/comp_<v>.png           rear over the current far_<v> render
  OUTDIR/strip_<order>.png      a|b|a, b|a|b, a|a|b, b|b|a strips (25 %)
  OUTDIR/seam_<order>.png       1:1 crops around each seam
and prints: margin identity, seam continuity, strip contour ranges / flat runs, HSV stats
(strips, ribs, whole layer) and the pale-rim area fraction.
Needs numpy + Pillow.
"""
import os
import subprocess
import sys

import numpy as np
from PIL import Image

W, H = 1920, 1080
out = sys.argv[1]
os.makedirs(out, exist_ok=True)
ENV = 'public/assets/svg/environment'


def render(svg, png):
    subprocess.run(['node', 'tools/render-svg.mjs', svg, png, '1', 'transparent'], check=True,
                   stdout=subprocess.DEVNULL)


subprocess.run([sys.executable, '-I', 'tools/art/rear/gen.py', '--debug', out], check=True, stdout=subprocess.DEVNULL)
for v in 'ab':
    render('%s/rear_%s.svg' % (ENV, v), '%s/rear_%s.png' % (out, v))
    render('%s/far_%s.svg' % (ENV, v), '%s/far_%s.png' % (out, v))
    for m in ('ribmask', 'echomask'):
        render('%s/rear_%s_%s.svg' % (out, v, m), '%s/rear_%s_%s.png' % (out, v, m))

L = {v: Image.open('%s/rear_%s.png' % (out, v)).convert('RGBA') for v in 'ab'}
F = {v: Image.open('%s/far_%s.png' % (out, v)).convert('RGBA') for v in 'ab'}
A = {v: np.asarray(L[v]).astype(int) for v in 'ab'}
MK = {(v, m): np.asarray(Image.open('%s/rear_%s_%s.png' % (out, v, m)).convert('L')) > 127
      for v in 'ab' for m in ('ribmask', 'echomask')}

# ---------------------------------------------------------------- composites
for v in 'ab':
    c = F[v].copy()
    c.alpha_composite(L[v])
    c.convert('RGB').save('%s/comp_%s.png' % (out, v))


def strip(order):
    n = len(order)
    s = Image.new('RGBA', (W * n, H))
    for i, v in enumerate(order):
        s.paste(F['a' if i % 2 == 0 else 'b'], (i * W, 0))
    for i, v in enumerate(order):
        s.alpha_composite(L[v], (i * W, 0))
    s = s.convert('RGB')
    s.resize((W * n // 4, H // 4), Image.LANCZOS).save('%s/strip_%s.png' % (out, order))
    crops = [s.crop((i * W - 360, 160, i * W + 360, 900)) for i in range(1, n)]
    sc = Image.new('RGB', (sum(c.width for c in crops) + 10 * (len(crops) - 1), crops[0].height), (255, 255, 255))
    x = 0
    for c in crops:
        sc.paste(c, (x, 0))
        x += c.width + 10
    sc.save('%s/seam_%s.png' % (out, order))


for o in ('aba', 'bab', 'aab', 'bba'):
    strip(o)

# ---------------------------------------------------------------- tiling contract
a, b = A['a'], A['b']
print('margin identity  left max|a-b| = %d   right max|a-b| = %d' % (np.abs(a[:, :48] - b[:, :48]).max(),
                                                                     np.abs(a[:, -48:] - b[:, -48:]).max()))
for name, X, Y in (('a|b', a, b), ('b|a', b, a), ('a|a', a, a), ('b|b', b, b)):
    seam = np.abs(X[:, -1, :] - Y[:, 0, :]).mean()
    inner = np.abs(X[:, 1000, :] - X[:, 1001, :]).mean()
    print('seam %s mean|col1919-col0| = %.2f (typical adjacent columns %.2f)' % (name, seam, inner))


def contours(X):
    """Edges of the see-through lumen gap: per column, the transparent run that contains y=560."""
    al = X[:, :, 3] > 127
    top, bot = [], []
    for x in range(W):
        col = al[:, x]
        if col[560]:
            top.append(None)
            bot.append(None)
            continue
        y0 = 560
        while y0 > 0 and not col[y0 - 1]:
            y0 -= 1
        y1 = 560
        while y1 < H - 1 and not col[y1 + 1]:
            y1 += 1
        top.append(y0)
        bot.append(y1 + 1)
    return top, bot


def runs(vals, target, tol=1):
    best, cur = 0, 0
    for v in vals:
        if v is not None and abs(v - target) <= tol:
            cur += 1
            best = max(best, cur)
        else:
            cur = 0
    return best


for v in 'ab':
    top, bot = contours(A[v])
    ok = [x for x in range(W) if top[x] is not None and bot[x] - top[x] >= 80]
    tv = [top[x] for x in ok]
    bv = [bot[x] for x in ok]
    print('%s: see-through gap (columns with a gap >= 80 px): top edge p5/50/95 %d/%d/%d (min %d), '
          'bottom edge p5/50/95 %d/%d/%d (max %d)' % (v, *np.percentile(tv, [5, 50, 95]).astype(int), min(tv),
                                                    *np.percentile(bv, [5, 50, 95]).astype(int), max(bv)))
    print('%s: x=0 top %s bot %s | x=120 top %s bot %s | x=1800 top %s bot %s' % (
        v, top[0], bot[0], top[120], bot[120], top[1800], bot[1800]))
    print('%s: longest run at y=300+-1: %d px, at y=720+-1: %d px (single tile; doubles across a seam)' % (
        v, runs(top, 300), runs(bot, 719)))
    # flat runs anywhere (any y, within +-2 px over a 60 px window)
    for nm, arr in (('top', top), ('bot', bot)):
        longest = 0
        start = 0
        for x in range(1, W):
            if arr[x] is None or arr[start] is None or abs(arr[x] - arr[start]) > 2:
                start = x
            longest = max(longest, x - start)
        print('%s: longest near-flat (+-2px) %s contour run: %d px' % (v, nm, longest))


# ---------------------------------------------------------------- HSV
def hsv(rgb):
    rgb = rgb.astype(float) / 255
    mx, mn = rgb.max(-1), rgb.min(-1)
    return mx, np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)


def stat(name, X, m):
    rgb = X[:, :, :3][m]
    V, S = hsv(rgb)
    mean = rgb.mean(0)
    p = np.percentile(V, [5, 25, 50, 75, 95])
    print('  %-22s n=%7d mean #%02x%02x%02x  V %.3f  S %.3f  Vstd %.3f  p5/25/50/75/95 %s' % (
        name, m.sum(), int(mean[0]), int(mean[1]), int(mean[2]), V.mean(), S.mean(), V.std(),
        '/'.join('%.2f' % q for q in p)))


for v in 'ab':
    X = A[v]
    op = X[:, :, 3] > 250
    rib = MK[(v, 'ribmask')] & op
    echo = MK[(v, 'echomask')] & op
    ys = np.arange(H)[:, None] * np.ones((1, W), bool)
    print('HSV %s' % v)
    stat('all opaque', X, op)
    stat('top strip y<290', X, op & (ys < 290))
    stat('bottom strip y>760', X, op & (ys > 760))
    stat('strips (no rib/echo)', X, op & ~rib & ~echo & ((ys < 290) | (ys > 640)))
    stat('ribs (visible hero)', X, rib)
    stat('ribs y 300-720', X, rib & (ys >= 300) & (ys <= 720))
    stat('echo rings', X, echo)
    V, S = hsv(X[:, :, :3])
    pale = op & (V > 0.88) & (S < 0.45)
    print('  pale (V>.88,S<.45) fraction of opaque: %.2f %%   of ribs: %.2f %%' % (
        100 * pale.sum() / op.sum(), 100 * (pale & rib).sum() / max(1, rib.sum())))
    # bright 5 % of the ribs
    rv = V[rib]
    thr = np.percentile(rv, 95)
    rgb = X[:, :, :3][rib & (V >= thr)].mean(0)
    print('  ribs brightest 5%% mean #%02x%02x%02x' % tuple(int(c) for c in rgb))
    # rib widths at mid-height, crowns
    cols = np.where(rib[530])[0]
    segs = np.split(cols, np.where(np.diff(cols) > 1)[0] + 1) if len(cols) else []
    print('  rib segments at y=530: %s' % ', '.join('%d-%d (%d px)' % (s[0], s[-1], s[-1] - s[0] + 1) for s in segs))

# ---------------------------------------------------------------- variant overlap (repeat visibility)
op = (a[:, :, 3] > 250) & (b[:, :, 3] > 250)
same = (np.abs(a[:, :, :3] - b[:, :, :3]).max(-1) <= 4) & op
for nm, y0, y1 in (('bottom strip y 640-1080', 640, 1080), ('bottom strip y 640-900 (visible in game)', 640, 900),
                   ('top strip y 0-300', 0, 300)):
    m = op[y0:y1]
    print('a/b pixel-identical (|d|<=4) in %s: %.1f %% of jointly opaque pixels' % (nm, 100 * same[y0:y1].sum() / max(1, m.sum())))


# ---------------------------------------------------------------- edge orientation in the lumen band
def edge_hist(rgb, y0, y1, thr=0.06):
    V = rgb.astype(float).max(-1) / 255.0
    V = V[y0:y1]
    gx = np.zeros_like(V)
    gy = np.zeros_like(V)
    gx[1:-1, 1:-1] = (V[1:-1, 2:] - V[1:-1, :-2]) * 2 + (V[:-2, 2:] - V[:-2, :-2]) + (V[2:, 2:] - V[2:, :-2])
    gy[1:-1, 1:-1] = (V[2:, 1:-1] - V[:-2, 1:-1]) * 2 + (V[2:, :-2] - V[:-2, :-2]) + (V[2:, 2:] - V[:-2, 2:])
    mag = np.hypot(gx, gy) / 8
    m = mag > thr
    ang = np.degrees(np.arctan2(gy[m], gx[m])) % 180     # gradient direction
    # edge is perpendicular to the gradient: gradient ~0/180 => vertical edge
    vert = ((ang < 22.5) | (ang >= 157.5)).mean()
    hor = ((ang >= 67.5) & (ang < 112.5)).mean()
    return vert, hor, 1 - vert - hor, mag.mean()


for v in 'ab':
    rgb = np.asarray(Image.open('%s/comp_%s.png' % (out, v)).convert('RGB'))
    vt, hz, dg, em = edge_hist(rgb, 260, 720)
    print('edges comp_%s (rear over far) y260-720: vertical %.0f %%  horizontal %.0f %%  diagonal %.0f %%  mean|grad| %.3f'
          % (v, 100 * vt, 100 * hz, 100 * dg, em))
