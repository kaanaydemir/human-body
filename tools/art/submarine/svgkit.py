"""Helpers shared by the submarine generator."""
import math

from ink import _f

GRAIN_DEFS = '''<filter id="grain" x="0" y="0" width="100%" height="100%" filterUnits="userSpaceOnUse">
    <feTurbulence type="fractalNoise" baseFrequency="0.9 0.6" numOctaves="2" seed="7" stitchTiles="stitch" result="n"/>
    <feColorMatrix in="n" type="matrix" values="0 0 0 0 0.35  0 0 0 0 0.06  0 0 0 0 0.08  0 0 0 0.10 0"/>
    <feComposite in2="SourceGraphic" operator="in"/>
  </filter>
  <filter id="mottle" x="0" y="0" width="100%" height="100%" filterUnits="userSpaceOnUse">
    <feTurbulence type="fractalNoise" baseFrequency="0.008 0.02" numOctaves="3" seed="3" stitchTiles="stitch" result="n"/>
    <feColorMatrix in="n" type="matrix" values="0 0 0 0 0.98  0 0 0 0 0.55  0 0 0 0 0.55  0 0 0 0.16 0"/>
    <feComposite in2="SourceGraphic" operator="in"/>
  </filter>'''


def cr(points, closed=True, tension=1.0):
    """Hand-placed key points -> smooth cubic path.  A point (x, y, 1) is a sharp corner."""
    pts = [(p[0], p[1]) for p in points]
    corner = [len(p) > 2 and p[2] for p in points]
    n = len(pts)
    o = ['M%s %s' % (_f(pts[0][0]), _f(pts[0][1]))]
    rng = range(n) if closed else range(n - 1)
    k = tension / 6.0
    for i in rng:
        i0 = (i - 1) % n if closed else max(i - 1, 0)
        i1 = i % n
        i2 = (i + 1) % n if closed else i + 1
        i3 = (i + 2) % n if closed else min(i + 2, n - 1)
        p0, p1, p2, p3 = pts[i0], pts[i1], pts[i2], pts[i3]
        if corner[i1]:
            c1 = (p1[0] + (p2[0] - p1[0]) * 0.25, p1[1] + (p2[1] - p1[1]) * 0.25)
        else:
            c1 = (p1[0] + (p2[0] - p0[0]) * k, p1[1] + (p2[1] - p0[1]) * k)
        if corner[i2]:
            c2 = (p2[0] - (p2[0] - p1[0]) * 0.25, p2[1] - (p2[1] - p1[1]) * 0.25)
        else:
            c2 = (p2[0] - (p3[0] - p1[0]) * k, p2[1] - (p3[1] - p1[1]) * k)
        o.append('C%s %s %s %s %s %s' % (_f(c1[0]), _f(c1[1]), _f(c2[0]), _f(c2[1]), _f(p2[0]), _f(p2[1])))
    if closed:
        o.append('Z')
    return ''.join(o)


def ellipse_path(cx, cy, rx, ry, rot=0.0):
    """Ellipse as 4 cubic segments (rotated by rot degrees)."""
    k = 0.5523
    a = math.radians(rot)
    ca, sa = math.cos(a), math.sin(a)

    def P(x, y):
        return (cx + x * ca - y * sa, cy + x * sa + y * ca)

    pts = [
        (P(rx, 0), P(rx, ry * k), P(rx * k, ry), P(0, ry)),
        (P(0, ry), P(-rx * k, ry), P(-rx, ry * k), P(-rx, 0)),
        (P(-rx, 0), P(-rx, -ry * k), P(-rx * k, -ry), P(0, -ry)),
        (P(0, -ry), P(rx * k, -ry), P(rx, -ry * k), P(rx, 0)),
    ]
    o = ['M%s %s' % (_f(pts[0][0][0]), _f(pts[0][0][1]))]
    for s in pts:
        o.append('C%s %s %s %s %s %s' % (_f(s[1][0]), _f(s[1][1]), _f(s[2][0]), _f(s[2][1]), _f(s[3][0]), _f(s[3][1])))
    o.append('Z')
    return ''.join(o)


def wobble_ellipse(cx, cy, rx, ry, rot=0.0, amp=0.04, n=10, phase=0.0, corner=None):
    """Hand-drawn-ish ellipse through n key points with slight radius variation."""
    a = math.radians(rot)
    ca, sa = math.cos(a), math.sin(a)
    pts = []
    for i in range(n):
        t = 2 * math.pi * i / n
        r = 1 + amp * math.sin(3 * t + phase) + amp * 0.5 * math.sin(5 * t + phase * 1.7)
        x, y = rx * r * math.cos(t), ry * r * math.sin(t)
        pts.append((cx + x * ca - y * sa, cy + x * sa + y * ca))
    return cr(pts, True)


class Doc:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.defs = []
        self.body = []

    def d(self, s):
        self.defs.append(s)

    def a(self, s):
        self.body.append(s)

    def path(self, d, fill, extra=''):
        self.body.append('<path d="%s" fill="%s"%s/>' % (d, fill, (' ' + extra) if extra else ''))

    def clip(self, cid, d):
        self.defs.append('<clipPath id="%s"><path d="%s"/></clipPath>' % (cid, d))

    def render(self):
        return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d">\n'
                '<defs>\n  %s\n</defs>\n%s\n</svg>\n') % (
            self.w, self.h, self.w, self.h, '\n  '.join(self.defs), '\n'.join(self.body))
