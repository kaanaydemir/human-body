#!/usr/bin/env python3
"""foreground-fx verification: renders the fg pieces with tools/render-svg.mjs and prints, per piece, the
flat-edge contract (fully opaque edge row, nothing cut by the side borders), the content bbox (fg_top must
stay <= 560 x 150) and raw HSV stats of the opaque pixels with the cel-shadow coverage.

    python3 -I tools/art/foreground-fx/check.py [SVG_DIR]     (needs numpy, Pillow, node + playwright)
"""
import os
import subprocess
import sys
import tempfile
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
SVG = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.join(ROOT, 'public', 'assets', 'svg', 'environment')
sys.path.insert(0, HERE)
from gen_fg import PAL, PAL_TOP  # noqa: E402


def hsv_stats(rgb):
    mx, mn = rgb.max(-1), rgb.min(-1)
    s = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-9), 0)
    return float(s.mean()), float(mx.mean())


def hexrgb(h):
    return np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], float)


with tempfile.TemporaryDirectory() as tmp:
    for n, edge in [('fg_bottom_1', 'bottom'), ('fg_bottom_2', 'bottom'), ('fg_bottom_3', 'bottom'),
                    ('fg_top_1', 'top'), ('fg_top_2', 'top')]:
        png = os.path.join(tmp, n + '.png')
        subprocess.run(['node', os.path.join(ROOT, 'tools', 'render-svg.mjs'), os.path.join(SVG, n + '.svg'), png, '1',
                        'transparent'], check=True, cwd=ROOT, stdout=subprocess.DEVNULL)
        px = np.asarray(Image.open(png).convert('RGBA')).astype(float)
        a = px[..., 3]
        H, W = a.shape
        row = a[H - 1] if edge == 'bottom' else a[0]
        nz = np.nonzero(row > 0)[0]
        inner = row[nz.min() + 8:nz.max() - 7]
        ys, xs = np.nonzero(a > 8)
        op = a >= 250
        S, V = hsv_stats(px[..., :3][op] / 255)
        sh = hexrgb((PAL_TOP if edge == 'top' else PAL)['shadow'])
        cover = (op & (np.abs(px[..., :3] - sh).max(-1) < 14)).sum() / op.sum()
        ok = inner.min() == 255 and a[:, 0].max() == 0 and a[:, W - 1].max() == 0
        if edge == 'top':
            ok = ok and (xs.max() - xs.min() + 1) <= 560 and (ys.max() - ys.min() + 1) <= 150
        print(f'{n:12s} {W}x{H} {"OK  " if ok else "FAIL"} {edge} edge opaque x {nz.min()}-{nz.max()}, '
              f'bbox {xs.max() - xs.min() + 1}x{ys.max() - ys.min() + 1}, side cols alpha {int(a[:, 0].max())}/'
              f'{int(a[:, W - 1].max())} | raw S={S:.2f} V={V:.2f} shadow {cover:.0%}')
