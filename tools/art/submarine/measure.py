"""HSV checks of the submarine in a game screenshot (or any composite) against the art-direction targets.

usage: python3 tools/art/submarine/measure.py <shot.png> <sub_screen_x> <sub_screen_y> [scale=0.85] [rot=0]
       [--geom DIR]   (use another geom.py, e.g. the previous round's, for a before/after comparison)

Regions are taken from geom.py (frame 520x300, origin at the frame centre) and mapped to the screen:
  dome  : the glass polygon (incl. the explorer)          targets: mean V ~.60, Vstd >= .22, darkest 5% <= .25
  hull  : low-saturation light pixels of the hull body   target : ~#e8d5cc (V .90-.92, S .13-.15, H +15..+24)
  red   : saturated red pixels of nose ball, band, fin    target : ~#da403c / #d14438 (H 0..+5)
"""
import colorsys
import math
import os
import sys

from PIL import Image, ImageDraw

sys.dont_write_bytecode = True  # keep the tools/art tree free of __pycache__
HERE = os.path.dirname(os.path.abspath(__file__))
GEOM_DIR = HERE
if '--geom' in sys.argv:
    i = sys.argv.index('--geom')
    GEOM_DIR = os.path.abspath(sys.argv[i + 1])
    del sys.argv[i:i + 2]
sys.path.insert(0, HERE)
sys.path.insert(0, GEOM_DIR)
from ink import poly  # noqa: E402
import geom  # noqa: E402
from svgkit import cr, wobble_ellipse  # noqa: E402


def to_screen(pts, sx, sy, S, rot):
    c, s = math.cos(rot), math.sin(rot)
    out = []
    for x, y in pts:
        dx, dy = (x - 260) * S, (y - 150) * S
        out.append((sx + dx * c - dy * s, sy + dx * s + dy * c))
    return out


def hsv(rgb):
    h, s, v = colorsys.rgb_to_hsv(*(c / 255 for c in rgb))
    h *= 360
    return (h - 360 if h > 180 else h), s, v


def stats(im, mask, label, sel=None):
    px = im.load()
    mk = mask.load()
    W, H = im.size
    vals = []
    for y in range(H):
        for x in range(W):
            if mk[x, y]:
                c = px[x, y][:3]
                hv = hsv(c)
                if sel is None or sel(hv):
                    vals.append((c, hv))
    if not vals:
        print('%-6s no pixels' % label)
        return
    n = len(vals)
    mr = sum(v[0][0] for v in vals) / n
    mg = sum(v[0][1] for v in vals) / n
    mb = sum(v[0][2] for v in vals) / n
    vs = sorted(v[1][2] for v in vals)
    mv = sum(vs) / n
    sd = (sum((v - mv) ** 2 for v in vs) / n) ** 0.5
    ms = sum(v[1][1] for v in vals) / n
    # circular mean hue
    hx = sum(math.cos(math.radians(v[1][0])) for v in vals)
    hy = sum(math.sin(math.radians(v[1][0])) for v in vals)
    mh = math.degrees(math.atan2(hy, hx))
    peri = sum(1 for v in vals if 200 <= (v[1][0] % 360) <= 250 and v[1][1] > 0.2) / n
    print('%-6s n=%6d mean #%02x%02x%02x  H%+.0f S%.2f V%.2f  Vstd %.2f  dark5%% V%.2f  blue-ish %.0f%%' % (
        label, n, int(mr), int(mg), int(mb), mh, ms, mv, sd, vs[int(n * 0.05)], peri * 100))


def main():
    shot, sx, sy = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
    S = float(sys.argv[4]) if len(sys.argv) > 4 else 0.85
    rot = float(sys.argv[5]) if len(sys.argv) > 5 else 0.0
    im = Image.open(shot).convert('RGB')

    def mask(polys):
        m = Image.new('L', im.size, 0)
        d = ImageDraw.Draw(m)
        for p in polys:
            d.polygon(to_screen(p, sx, sy, S, rot), fill=1)
        return m

    if hasattr(geom, 'NOSE_C'):
        nose = poly(wobble_ellipse(geom.NOSE_C[0], geom.NOSE_C[1], geom.NOSE_R[0], geom.NOSE_R[1], geom.NOSE_ROT,
                                   amp=0.012, n=10, phase=0.6))
    else:
        nose = poly(geom.NOSE)
    fin = poly(cr(geom.FIN_PTS)) if hasattr(geom, 'FIN_PTS') else poly(geom.FIN)
    band = [poly(geom.BAND)] if hasattr(geom, 'BAND') else []
    stats(im, mask([poly(geom.GLASS)]), 'dome')
    hull = mask([poly(geom.HULL_D)])
    hull.paste(0, mask=mask([poly(geom.DOME), nose]))
    stats(im, hull, 'hull', sel=lambda h: h[1] < 0.30 and h[2] > 0.55)
    red_sel = lambda h: h[1] > 0.55 and h[2] > 0.45 and -25 < h[0] < 25  # noqa: E731
    stats(im, mask([nose, fin] + band), 'red', sel=red_sel)
    stats(im, mask([nose]), 'nose', sel=red_sel)


if __name__ == '__main__':
    main()
