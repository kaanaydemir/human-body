#!/usr/bin/env python3
"""Verification for the ceiling group (needs Pillow, numpy and node + playwright for tools/render-svg.mjs).

    python3 -I tools/art/ceiling/check.py OUTDIR [--svgdir DIR] [--ctx]

Renders ceiling_a/b/c.svg and prints:
  - tiling: max pixel difference of the 48 px margins and of the shared seam zone (x<160, x>1760) across
    variants, left/right edge-column match, contour y at both borders and its flatness over 48 px;
  - colour: HSV mean / std of the opaque pixels (raw), contour range;
  - with --ctx: a composite over the current far_a + rear_a + floor_a + vignette (45 %) and the HSV of the
    ceiling zone y 0..200 in that composite.
Writes seam strips (abca, bacb, cbac, aabb, ccaa), seam close-ups, a variant sheet and the composites to OUTDIR.
"""
import itertools
import os
import subprocess
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
ENV = os.path.join(ROOT, 'public', 'assets', 'svg', 'environment')


def render(svg, png, scale=1, bg='transparent'):
    subprocess.run(['node', 'tools/render-svg.mjs', svg, png, str(scale), bg], cwd=ROOT, check=True,
                   capture_output=True)
    return Image.open(png).convert('RGBA')


def hsv_stats(rgb, mask=None):
    a = rgb.reshape(-1, 3).astype(np.float64) / 255.0
    if mask is not None:
        a = a[mask.reshape(-1)]
    mx = a.max(1)
    mn = a.min(1)
    v = mx
    s = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-9), 0)
    m = a.mean(0)
    return dict(V=v.mean(), S=s.mean(), Vstd=v.std(), mean='#%02x%02x%02x' % tuple(int(round(c * 255)) for c in m))


def main():
    args = sys.argv[1:]
    out = os.path.abspath(args[0]) if args and not args[0].startswith('--') else os.path.join(ROOT, 'tools/out/ceiling/check')
    svgdir = ENV
    if '--svgdir' in args:
        svgdir = os.path.abspath(args[args.index('--svgdir') + 1])
    os.makedirs(out, exist_ok=True)
    T = {}
    for v in 'abc':
        T[v] = render(os.path.join(svgdir, f'ceiling_{v}.svg'), os.path.join(out, f'raw_{v}.png'))
    W, H = T['a'].size
    A = {v: np.asarray(T[v]).astype(int) for v in T}

    # ---- tiling
    mx48 = 0
    mxzone = 0
    for a, b in itertools.combinations('abc', 2):
        d = np.abs(A[a] - A[b])
        mx48 = max(mx48, d[:, :48].max(), d[:, W - 48:].max())
        mxzone = max(mxzone, d[:, :160].max(), d[:, W - 160:].max())
    print(f'margin identity (48 px) max diff: {mx48}   shared seam zone (160 px) max diff: {mxzone}')
    for v in 'abc':
        e = np.abs(A[v][:, 0] - A[v][:, W - 1]).max()
        al = A[v][:, :, 3]
        cl = max(y for y in range(H) if al[y, 0] > 127)
        cr = max(y for y in range(H) if al[y, W - 1] > 127)
        prof = [max(y for y in range(H) if al[y, x] > 127) for x in range(W)]
        flat = max(prof[:48] + prof[W - 48:]) - min(prof[:48] + prof[W - 48:])
        print(f'{v}: edge columns L vs R max diff {e}; contour at border L={cl} R={cr}; spread over the 48 px margins '
              f'{flat} px; contour range {min(prof)}..{max(prof)} mean {np.mean(prof):.0f}')
        st = hsv_stats(A[v][:, :, :3], al > 250)
        print(f'   raw opaque pixels: mean {st["mean"]} V={st["V"]:.3f} S={st["S"]:.3f} Vstd={st["Vstd"]:.3f}')
        # plain base: pixels within 16 RGB units of the base gradient at their row (pores, rims, bands break it)
        import layout as LY
        stops = [(o_, tuple(int(c[i:i + 2], 16) for i in (1, 3, 5))) for o_, c in LY.BASE_STOPS]
        g = np.array([[stops[0][1][k] + (stops[-1][1][k] - stops[0][1][k]) * (y / (H - 1)) for k in range(3)]
                      for y in range(H)])
        plain = (np.abs(A[v][:, :, :3] - g[:, None, :]).max(2) < 16) & (al > 250)
        # largest plain patch: chamfer distance to the nearest non-plain pixel (2x downsampled), x2 = diameter
        pm = plain[::2, ::2]
        hh, ww = pm.shape
        INF = 10 ** 6
        dist = np.where(pm, INF, 0).astype(np.int64)
        for y in range(hh):
            row = dist[y]
            if y:
                up = dist[y - 1]
                row[:] = np.minimum(row, up + 2)
                row[1:] = np.minimum(row[1:], up[:-1] + 3)
                row[:-1] = np.minimum(row[:-1], up[1:] + 3)
            for x in range(1, ww):
                if row[x] > row[x - 1] + 2:
                    row[x] = row[x - 1] + 2
        for y in range(hh - 1, -1, -1):
            row = dist[y]
            if y < hh - 1:
                dn = dist[y + 1]
                row[:] = np.minimum(row, dn + 2)
                row[1:] = np.minimum(row[1:], dn[:-1] + 3)
                row[:-1] = np.minimum(row[:-1], dn[1:] + 3)
            for x in range(ww - 2, -1, -1):
                if row[x] > row[x + 1] + 2:
                    row[x] = row[x + 1] + 2
        # the canvas edge does not bound a patch, so measure in two zones: the top 24 px strip and below it
        tops = []
        for zone, sl in (('below y=24', slice(12, None)), ('top strip', slice(0, 12))):
            dz = dist[sl]
            yy, xx = np.unravel_index(dz.argmax(), dz.shape)
            tops.append(f'{zone}: ~{dz.max() * 2:.0f} px at x={xx * 2} y={(yy + sl.start if sl.start else yy) * 2}')
        print(f'   plain base: {plain.sum() / max(1, (al > 250).sum()):.1%} of opaque px; largest plain patch (diameter) '
              + '; '.join(tops))
        top = hsv_stats(A[v][:150, :, :3], al[:150] > 250)
        print(f'   raw top 150 px:    mean {top["mean"]} V={top["V"]:.3f} S={top["S"]:.3f}')

    # ---- seam strips and close-ups
    bg = (58, 42, 90, 255)

    def strip(order):
        im = Image.new('RGBA', (W * len(order), H), bg)
        for i, v in enumerate(order):
            im.alpha_composite(T[v], (i * W, 0))
        return im
    for o in ['abca', 'bacb', 'cbac', 'aabb', 'ccaa']:
        s = strip(o)
        s.convert('RGB').resize((s.width // 4, s.height // 4), Image.LANCZOS).save(os.path.join(out, f'strip_{o}.png'))
    tiles = []
    for p in ['ab', 'ba', 'ac', 'ca', 'bc', 'cb']:
        tiles.append(strip(p).crop((W - 300, 0, W + 300, 300)))
    grid = Image.new('RGBA', (600 * 2 + 10, 300 * 3 + 20), (30, 30, 30, 255))
    for i, t in enumerate(tiles):
        grid.alpha_composite(t, ((i % 2) * 610, (i // 2) * 310))
    grid.convert('RGB').save(os.path.join(out, 'seams.png'))
    sheet = Image.new('RGBA', (W, H * 3 + 20), (30, 30, 30, 255))
    for i, v in enumerate('abc'):
        sheet.alpha_composite(Image.alpha_composite(Image.new('RGBA', (W, H), bg), T[v]), (0, i * (H + 10)))
    sheet.convert('RGB').save(os.path.join(out, 'sheet.png'))

    # ---- context composite
    if '--ctx' in args:
        far = render(os.path.join(ENV, 'far_a.svg'), os.path.join(out, 'ctx_far_a.png'), 1, '#000000')
        rear = render(os.path.join(ENV, 'rear_a.svg'), os.path.join(out, 'ctx_rear_a.png'))
        floor = render(os.path.join(ENV, 'floor_a.svg'), os.path.join(out, 'ctx_floor_a.png'))
        vig = render(os.path.join(ENV, 'vignette.svg'), os.path.join(out, 'ctx_vignette.png'))
        va = np.asarray(vig).astype(np.float64)
        va[:, :, 3] *= 0.45
        vig45 = Image.fromarray(va.round().astype(np.uint8), 'RGBA')
        for v in 'abc':
            c = far.copy()
            c.alpha_composite(rear)
            c.alpha_composite(T[v], (0, 0))
            c.alpha_composite(floor, (0, 720))
            c.alpha_composite(vig45)
            c.convert('RGB').save(os.path.join(out, f'ctx_{v}.png'))
            c.convert('RGB').crop((0, 0, W, 560)).save(os.path.join(out, f'ctx_top_{v}.png'))
            arr = np.asarray(c.convert('RGB'))
            z = hsv_stats(arr[:200])
            m = A[v][:200, :, 3] > 250
            zc = hsv_stats(arr[:200], m)
            print(f'{v}: composite y 0..200: V={z["V"]:.3f} S={z["S"]:.3f} ({z["mean"]}); ceiling pixels only V={zc["V"]:.3f}'
                  f' S={zc["S"]:.3f}; top-left 200x120 V={hsv_stats(arr[:120, :200])["V"]:.3f}')


if __name__ == '__main__':
    main()
