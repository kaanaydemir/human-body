"""In-context mock: paste the layered sub (+ jet, ring bubbles, headlight) onto a reference panel.

usage: python3 tools/art/submarine/context.py <svgdir> <bg.png> <scale> <cx> <cy> <out.png> [thrust=1] [light=normal|add]

<scale>  : sub container scale on the background (0.85 in game; ~0.68 on the 2x p4 crop)
<cx, cy> : where the frame centre (260,150) goes on the background
light    : normal = the runtime this art is authored for (NORMAL blend, no tint, alpha 0.95)
           add    = today's Submarine.ts (ADD blend, tint 0xffa848, alpha 0.8)
Jet: scale (0.35 + 0.8*thrust, 0.75 + 0.35*thrust) as in Submarine.ts; alpha 0.5 + 0.45*thrust (recommended).
Bubbles: a fixed, seeded fan of ring bubbles (16-28 px at game scale, +-70 px) trailing the jet, for the mock only.
"""
import os
import random
import subprocess
import sys

import numpy as np
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
svgdir, bgp, S, cx, cy, outp = sys.argv[1:7]
S, cx, cy = float(S), float(cx), float(cy)
thrust = float(sys.argv[7]) if len(sys.argv) > 7 else 1.0
mode = sys.argv[8] if len(sys.argv) > 8 else 'normal'
tmp = os.path.join(os.path.dirname(os.path.abspath(outp)), '_ctx')
os.makedirs(tmp, exist_ok=True)
L = {}
for n in ['sub_back', 'explorer', 'sub_front', 'sub_light', 'jet', 'jet_bubble']:
    p = os.path.join(tmp, n + '.png')
    subprocess.run(['node', 'tools/render-svg.mjs', os.path.join(os.path.abspath(svgdir), n + '.svg'), p, '2',
                    'transparent'], cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
    L[n] = Image.open(p).convert('RGBA')
canvas = Image.open(bgp).convert('RGBA')


def paste(im, ax, ay, ox, oy, sx, sy, alpha=1.0):
    """im rendered at 2x; (ox,oy) = its origin in its own 1x units; (ax,ay) = frame position of that origin."""
    global canvas
    s = im.resize((max(1, int(im.width / 2 * sx)), max(1, int(im.height / 2 * sy))), Image.LANCZOS)
    if alpha < 1:
        a = np.array(s)
        a[..., 3] = (a[..., 3] * alpha).astype(np.uint8)
        s = Image.fromarray(a)
    x = int(round(cx + (ax - 260) * S - ox * sx))
    y = int(round(cy + (ay - 150) * S - oy * sy))
    layer = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
    layer.paste(s, (x, y))
    canvas = Image.alpha_composite(canvas, layer)


# bubbles (world space, behind the sub): a seeded fan trailing ~1 sub length behind the jet
rnd = random.Random(3)
for i in range(26):
    t = rnd.random()
    d = 40 + t * 420
    fan = 70 * min(1.0, d / 260)
    bx = 24 - d
    by = 168 + rnd.uniform(-fan, fan)
    size = rnd.uniform(16, 28) / 0.85 / 32  # 16-28 px at game scale
    alpha = 1 - t ** 2
    paste(L['jet_bubble'], bx, by, 16, 16, S * size, S * size, alpha)
paste(L['jet'], 24, 168, 160, 45, S * (0.35 + 0.8 * thrust), S * (0.75 + 0.35 * thrust), 0.5 + 0.45 * thrust)
for n in ['sub_back', 'explorer', 'sub_front']:
    paste(L[n], 260, 150, 260, 150, S, S)
lt = L['sub_light'].resize((int(640 * S), int(320 * S)), Image.LANCZOS)
x0 = int(round(cx + (498 - 6 - 260) * S))
y0 = int(round(cy + (178 - 150) * S - 160 * S))
if mode == 'normal':
    a = np.array(lt).astype(np.float32)
    a[..., 3] *= 0.95
    layer = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
    layer.paste(Image.fromarray(a.astype(np.uint8)), (x0, y0))
    canvas = Image.alpha_composite(canvas, layer)
    out = canvas.convert('RGB')
else:
    base = np.asarray(canvas.convert('RGB')).astype(np.float32)
    la = np.asarray(lt).astype(np.float32)
    tint = np.array([0xff, 0xa8, 0x48], np.float32) / 255
    h, w = la.shape[:2]
    x1, y1 = min(base.shape[1], x0 + w), min(base.shape[0], y0 + h)
    base[y0:y1, x0:x1] += la[:y1 - y0, :x1 - x0, :3] * tint * (la[:y1 - y0, :x1 - x0, 3:4] / 255) * 0.8
    out = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8))
out.save(outp)
print('ok', outp)
