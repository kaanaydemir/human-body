"""Samples a game screenshot along the headlight axis and around it (HSV), for comparison with reference p7.

usage: python3 tools/art/submarine/beam_check.py <shot.png> <sub_screen_x> <sub_screen_y> [scale=0.85]
Prints 8 samples on the beam axis from the lens outward, and the colour 80 px above/below the axis at mid-beam.
"""
import colorsys
import sys

from PIL import Image

shot, sx, sy = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
S = float(sys.argv[4]) if len(sys.argv) > 4 else 0.85
im = Image.open(shot).convert('RGB')
px = im.load()
lx, ly = sx + (498 - 6 - 260) * S, sy + (178 - 150) * S


def avg(x, y, r=5):
    acc = [0, 0, 0]
    n = 0
    for dx in range(-r, r + 1):
        for dy in range(-r, r + 1):
            c = px[int(x + dx), int(y + dy)]
            for i in range(3):
                acc[i] += c[i]
            n += 1
    return tuple(a / n for a in acc)


def fmt(c):
    h, s, v = colorsys.rgb_to_hsv(*(v / 255 for v in c))
    h = h * 360
    h = h - 360 if h > 180 else h
    return '#%02x%02x%02x(H%+.0f S%.2f V%.2f)' % (tuple(int(round(v)) for v in c) + (h, s, v))


L = 560 * S
print('axis :', ' '.join(fmt(avg(lx + L * i / 7 + 8, ly)) for i in range(8)))
mid = lx + L * 0.45
print('mid-beam x=%d: above-80 %s  axis %s  below-80 %s' % (mid, fmt(avg(mid, ly - 80)), fmt(avg(mid, ly)), fmt(avg(mid, ly + 80))))
print('far walls (no beam) at x=%d: above-80 %s below-80 %s' % (lx - 380, fmt(avg(lx - 380, ly - 80)), fmt(avg(lx - 380, ly + 80))))
