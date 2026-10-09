#!/usr/bin/env python3
"""REAR VESSEL WALL generator (layer 2, scroll 0.35).

Writes public/assets/svg/environment/rear_a.svg and rear_b.svg.

    cd /home/user/human-body
    python3 -I tools/art/rear/gen.py                 # write the two SVGs
    python3 -I tools/art/rear/gen.py --debug DIR     # also write mask SVGs used by check.py

Design (art-director round 2):
- Every rib is a FULL ring arch (fat crescent: thick crown, tapering legs that lean 20-35 deg).
  The crown underside sits at y 300-380 so it is visible below the main ceiling.
- Each hero arch has one hazy, outline-free echo ring tucked behind its inner edge (stacked rings).
- Cel shading is computed from a front/upper-left light on a tube cross-section: one opaque shadow
  shape (#93201e), one opaque highlight shape, a saturated lit-edge stroke, a broken pale rim and an
  opaque tapered ink line (#6e1a24) only on the shadow side.  No blur, no translucent stacks.
- Top strip: receding vaults between the ribs (apex 280-300) with nested arch soffits (rim #d8635f,
  recess #771d26).  Bottom strip: fleshy mound rows that swell up to 640-660 over the rib feet and
  dip to 720-740 between them.
- Tiling: both strips are exactly at y=300 / y=720 and flat for the 48 px border margins.  A shared
  seam motif (vault + soffits on top, valley + low mound + two foot mounds at the bottom) is defined
  in seam coordinates and drawn identically at x=0 and x=1920 in BOTH files, so every border column
  is pixel-identical across variants and the seam never shows a long flat run.
A seeded RNG only adds small variation (dash placement, terminator wobble).
"""
import math
import os
import random
import sys

W, H = 1920, 1080
M = 48              # tiling margin: base (+ shared seam motif) only within M px of the borders
SAFE = 60           # variant features keep at least this far from the borders
TOP_Y, BOT_Y = 300, 720
CY = 790            # centre height of the arch ellipses (hidden behind the floor)

# ---------------------------------------------------------------- palette
LINE = '#6e1a24'
DEEP = '#771d26'
SHADOW = '#93201e'
RIM_OUT = '#d8635f'
RIM_PALE = '#f4a69c'
TOP_STOPS = ('#b42c35', '#9a2530')     # base gradient, offset 0 (strip lip) -> 1 (canvas edge)

RIB = dict(lit='#d13b3f', hi='#f34f49', edge='#f66a62', sh=SHADOW, deep=DEEP,
           d_light='#f0605a', d_dark='#b5333b', d_sh='#7a1d25')
ECHO = dict(lit='#c44a4f', sh='#a3383e', edge='#d6625f')
ROWS = [
    dict(lit='#c63c44', sh='#9b2b32', rim=RIM_OUT, pale=None, hatch='#a3303a', line=(0.0, 2.2)),   # back
    dict(lit='#cb383e', sh=SHADOW, rim=RIM_OUT, pale=None, hatch='#a12b35', line=(0.0, 2.8)),      # mid
    dict(lit='#d3373c', sh=SHADOW, rim=RIM_OUT, pale=RIM_PALE, hatch='#9e2832', line=(0.0, 3.6)),  # front
    dict(lit='#d6383b', sh=SHADOW, rim=RIM_OUT, pale=RIM_PALE, hatch='#9e2832', line=(0.0, 4.0)),  # front-most
]

# light: from the front / upper-left (screen coords, y down)
_l = math.hypot(0.78, 0.62)
L2 = (-0.78 / _l, -0.62 / _l)
K2, LZ = 0.78, 0.62
T_SH, T_HI = 0.10, 0.86

FEATURE_PTS = []    # variant feature points (must stay out of the margins)
MOTIF = [False]     # True while drawing the shared seam motif


# ---------------------------------------------------------------- small math
def f1(v):
    s = '%.1f' % v
    if s.endswith('.0'):
        s = s[:-2]
    if s == '-0':
        s = '0'
    return s


def add(a, b):
    return (a[0] + b[0], a[1] + b[1])


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1])


def mul(a, k):
    return (a[0] * k, a[1] * k)


def unit(a):
    l = math.hypot(a[0], a[1]) or 1.0
    return (a[0] / l, a[1] / l)


def lerp(a, b, t):
    return a + (b - a) * t


def clamp(x, a, b):
    return max(a, min(b, x))


def smooth01(e0, e1, x):
    t = clamp((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def interp_keys(keys, s):
    """Smooth (cosine) interpolation through (s, v) keys."""
    if s <= keys[0][0]:
        return keys[0][1]
    for (s0, v0), (s1, v1) in zip(keys, keys[1:]):
        if s <= s1:
            t = (s - s0) / (s1 - s0)
            t = 0.5 - 0.5 * math.cos(math.pi * t)
            return v0 + (v1 - v0) * t
    return keys[-1][1]


def ends_taper(t, a=0.08, b=0.08, p=0.8):
    t = clamp(t, 0.0, 1.0)
    va = smooth01(0, a, t) if a > 0 else 1.0
    vb = (1 - smooth01(1 - b, 1, t)) if b > 0 else 1.0
    return (va * vb) ** p


# ---------------------------------------------------------------- path tools
def tangents(pts, closed, k=1.0, start_tan=None, end_tan=None):
    n = len(pts)
    T = []
    for i in range(n):
        if closed:
            t = mul(sub(pts[(i + 1) % n], pts[(i - 1) % n]), 0.5 * k)
        elif i == 0:
            t = start_tan if start_tan is not None else mul(sub(pts[1], pts[0]), k)
        elif i == n - 1:
            t = end_tan if end_tan is not None else mul(sub(pts[-1], pts[-2]), k)
        else:
            t = mul(sub(pts[i + 1], pts[i - 1]), 0.5 * k)
        T.append(t)
    return T


def nf(t):
    """Number in tenths (int) -> compact string."""
    neg = t < 0
    t = abs(t)
    a, b = divmod(t, 10)
    if b == 0:
        s = str(a)
    elif a == 0:
        s = '.%d' % b
    else:
        s = '%d.%d' % (a, b)
    return '-' + s if neg and s != '0' else s


def nums(vals):
    out = ''
    prev = ''
    for v in vals:
        s = nf(v)
        if out and not s.startswith('-') and not (s.startswith('.') and '.' in prev):
            out += ' '
        out += s
        prev = s
    return out


def T10(v):
    return int(round(v * 10))


def bez_d(pts, closed=False, k=1.0, start_tan=None, end_tan=None):
    """Catmull-Rom through pts -> cubic Bezier path data (relative, drift-free)."""
    n = len(pts)
    T = tangents(pts, closed, k, start_tan, end_tan)
    cx, cy = T10(pts[0][0]), T10(pts[0][1])
    out = ['M' + nums([cx, cy])]
    seg = []
    for i in range(n if closed else n - 1):
        j = (i + 1) % n
        c1 = add(pts[i], mul(T[i], 1 / 3))
        c2 = sub(pts[j], mul(T[j], 1 / 3))
        a = [T10(c1[0]), T10(c1[1]), T10(c2[0]), T10(c2[1]), T10(pts[j][0]), T10(pts[j][1])]
        seg += [a[0] - cx, a[1] - cy, a[2] - cx, a[3] - cy, a[4] - cx, a[5] - cy]
        cx, cy = a[4], a[5]
    if seg:
        out.append('c' + nums(seg))
    if closed:
        out.append('Z')
    return ''.join(out)


class PB:
    """Absolute path builder (used for the long strip silhouettes)."""

    def __init__(self, p):
        self.d = ['M%s %s' % (f1(p[0]), f1(p[1]))]

    def L(self, pts):
        for p in pts:
            self.d.append('L%s %s' % (f1(p[0]), f1(p[1])))

    def CR(self, pts, start_tan=None, end_tan=None):
        """Catmull-Rom from the current point pts[0] through pts."""
        T = tangents(pts, False, 1.0, start_tan, end_tan)
        for i in range(len(pts) - 1):
            c1 = add(pts[i], mul(T[i], 1 / 3))
            c2 = sub(pts[i + 1], mul(T[i + 1], 1 / 3))
            self.d.append('C' + ' '.join(f1(v) for v in (c1[0], c1[1], c2[0], c2[1], pts[i + 1][0], pts[i + 1][1])))

    def done(self):
        return ''.join(self.d) + 'Z'


def sample_cr(pts, per=24, k=1.0, start_tan=None, end_tan=None):
    T = tangents(pts, False, k, start_tan, end_tan)
    out = []
    for i in range(len(pts) - 1):
        p0, p3 = pts[i], pts[i + 1]
        p1 = add(p0, mul(T[i], 1 / 3))
        p2 = sub(p3, mul(T[i + 1], 1 / 3))
        for j in range(per):
            t = j / per
            u = 1 - t
            out.append((u * u * u * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t * t * t * p3[0],
                        u * u * u * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t * t * t * p3[1]))
    out.append(pts[-1])
    return out


def resample(poly, n):
    d = [0.0]
    for a, b in zip(poly, poly[1:]):
        d.append(d[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    L = d[-1]
    out = []
    j = 0
    for i in range(n):
        target = L * i / (n - 1)
        while j < len(d) - 2 and d[j + 1] < target:
            j += 1
        seg = d[j + 1] - d[j] or 1.0
        t = (target - d[j]) / seg
        out.append((lerp(poly[j][0], poly[j + 1][0], t), lerp(poly[j][1], poly[j + 1][1], t)))
    return out


def normals(poly):
    out = []
    n = len(poly)
    for i in range(n):
        a = poly[max(0, i - 1)]
        b = poly[min(n - 1, i + 1)]
        t = unit(sub(b, a))
        out.append((t[1], -t[0]))      # left-hand normal (screen coords)
    return out


def pick(poly, count):
    """Evenly pick `count` points from a dense polyline (keeps ends)."""
    if len(poly) <= count:
        return poly
    return [poly[round(i * (len(poly) - 1) / (count - 1))] for i in range(count)]


def polylen(poly):
    return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(poly, poly[1:]))


def track(pts):
    if not MOTIF[0]:
        FEATURE_PTS.extend(pts)
    return pts


def ranges(flags, minlen=3):
    """Contiguous index ranges [i0, i1] where flags[i] is True."""
    out = []
    i0 = None
    for i, f in enumerate(flags + [False]):
        if f and i0 is None:
            i0 = i
        elif not f and i0 is not None:
            if i - 1 - i0 + 1 >= minlen:
                out.append((i0, i - 1))
            i0 = None
    return out


# ---------------------------------------------------------------- output
class Out:
    def __init__(self):
        self.parts = []
        self.defs = []
        self.nid = 0

    def add(self, s):
        self.parts.append(s)

    def path(self, d, fill, extra=''):
        self.parts.append('<path d="%s" fill="%s"%s/>' % (d, fill, extra))

    def defpath(self, d, pid=None):
        if pid is None:
            self.nid += 1
            pid = 'p%d' % self.nid
        self.defs.append('<path id="%s" d="%s"/>' % (pid, d))
        return pid

    def use(self, pid, fill):
        self.parts.append('<use href="#%s" fill="%s"/>' % (pid, fill))


def closed_between(A, B, cnt=None):
    """Closed shape between two polylines running the same direction."""
    if cnt is None:
        cnt = max(6, min(40, int(polylen(A) / 22) + 4))
    ring = pick(A, cnt) + pick(B[::-1], cnt)[1:-1]
    track(ring)
    return bez_d(ring, closed=True)


def tapered(poly, wfun, cnt=None):
    """Closed brush-stroke polygon around a polyline; wfun(t)->full width."""
    nr = normals(poly)
    n = len(poly)
    Lp, Rp = [], []
    for i, (p, nn) in enumerate(zip(poly, nr)):
        t = i / (n - 1)
        w = max(0.0, wfun(t)) / 2
        Lp.append(add(p, mul(nn, w)))
        Rp.append(sub(p, mul(nn, w)))
    if cnt is None:
        cnt = max(5, min(30, int(polylen(poly) / 20) + 4))
    ring = pick(Lp, cnt) + pick(Rp[::-1], cnt)[1:-1]
    track(ring)
    return bez_d(ring, closed=True)


def tick(c, ang, length, width, curve=0.0, lop=0.6):
    """Lens-shaped brush tick (hatch stroke)."""
    d = (math.cos(ang), math.sin(ang))
    nn = (-d[1], d[0])
    p0 = sub(c, mul(d, length / 2))
    p1 = add(c, mul(d, length / 2))
    m = add(c, mul(nn, curve))
    q1 = add(m, mul(nn, width))
    q2 = sub(m, mul(nn, width * lop))
    track([p0, p1])
    x0, y0 = T10(p0[0]), T10(p0[1])
    v = [T10(q1[0]) - x0, T10(q1[1]) - y0, T10(p1[0]) - x0, T10(p1[1]) - y0]
    w = [T10(q2[0]) - x0 - v[2], T10(q2[1]) - y0 - v[3], -v[2], -v[3]]
    return 'M%sq%sZ' % (nums([x0, y0]), nums(v + w))


# ---------------------------------------------------------------- ARCH (ring rib)
class Arch:
    """A full ring arch.  Spine runs left foot -> crown -> right foot along an ellipse centred at
    (cx, CY).  f = 0 is the OUTER edge, f = 1 the INNER edge (towards the opening)."""

    def __init__(self, xl, xr, yc, wc, wm, wf, wob=(), bl=(), br=(), skew=0.0, ybot=772, n=240, yf=690.0):
        cx = (xl + xr) / 2.0
        ry = CY - yc
        sf = (CY - yf) / ry
        rx = (cx - xl) / math.sqrt(1 - sf * sf)
        self.cx, self.rx, self.ry = cx, rx, ry
        phi0 = math.asin(clamp((CY - ybot) / ry, -1, 1))
        K = 30
        pts = []
        for k in range(K + 1):
            ph = phi0 + (math.pi - 2 * phi0) * k / K
            r = 1.0 + sum(a * math.sin(f * ph + o) for a, f, o in wob)
            x = cx - rx * r * math.cos(ph) + skew * math.sin(ph) ** 4
            y = CY - ry * r * math.sin(ph)
            pts.append((x, y))
        self.p = resample(sample_cr(pts, 10), n)
        self.nr = normals(self.p)
        self.n = n
        self.s = [i / (n - 1) for i in range(n)]
        hf = sf
        hm = (CY - 530.0) / ry
        self.hl, self.hr = [], []
        for i, (x, y) in enumerate(self.p):
            h = (CY - y) / ry
            w = interp_keys([(hf, wf), (hm, wm), (1.0, wc)], h)
            s = self.s[i]
            bL = sum(a * math.exp(-((s - c) / wd) ** 2) for c, a, wd in bl)
            bR = sum(a * math.exp(-((s - c) / wd) ** 2) for c, a, wd in br)
            self.hl.append(w / 2 + bL)
            self.hr.append(w / 2 + bR)

    def width(self, i):
        return self.hl[i] + self.hr[i]

    def pt(self, i, f):
        off = self.hl[i] - f * (self.hl[i] + self.hr[i])
        return add(self.p[i], mul(self.nr[i], off))

    def ept(self, i, side, off):
        """Point at `off` px outside edge `side` (0 outer, 1 inner); negative = inside the band."""
        if side == 0:
            return add(self.p[i], mul(self.nr[i], self.hl[i] + off))
        return sub(self.p[i], mul(self.nr[i], self.hr[i] + off))

    def shape(self):
        Lp = [self.pt(i, 0.0) for i in range(self.n)]
        Rp = [self.pt(i, 1.0) for i in range(self.n)]
        ring = pick(Lp, 48) + pick(Rp[::-1], 48)[1:-1]
        track(ring)
        return bez_d(ring, closed=True)

    def band(self, fa, fb, i0, i1, cnt=None):
        ii = range(i0, i1 + 1)
        A = [self.pt(i, fa(i)) for i in ii]
        B = [self.pt(i, fb(i)) for i in ii]
        return closed_between(A, B, cnt)

    def eband(self, side, oa, ob, i0, i1, cnt=None):
        ii = range(i0, i1 + 1)
        A = [self.ept(i, side, oa(i)) for i in ii]
        B = [self.ept(i, side, ob(i)) for i in ii]
        return closed_between(A, B, cnt)

    def idx_at_y(self, y, leg):
        """Spine index where the centreline crosses height y on the left (leg=0) or right (1) leg."""
        rng_ = range(self.n // 2) if leg == 0 else range(self.n - 1, self.n // 2, -1)
        for i in rng_:
            if self.p[i][1] <= y:
                return i
        return self.n // 2

    def edge_x_at_y(self, y, leg, side=0):
        """x of edge `side` on leg `leg` at height y (scan)."""
        best = None
        rng_ = range(0, self.n // 2 + 20) if leg == 0 else range(self.n // 2 - 20, self.n)
        for i in rng_:
            a = self.ept(i, side, 0)
            if best is None or abs(a[1] - y) < abs(best[1] - y):
                best = a
        return best[0]

    def light(self, ph):
        """Per-sample cel lighting: a = edge term, (fa, fb) lit interval, hi interval or None."""
        res = []
        for i in range(self.n):
            nx, ny = self.nr[i]
            a = K2 * (nx * L2[0] + ny * L2[1])
            R = math.hypot(a, LZ)
            d = math.atan2(LZ, a)
            c = math.acos(clamp(T_SH / R, -1, 1))
            s = self.s[i]
            wob = 0.035 * math.sin(s * 14 + ph) + 0.02 * math.sin(s * 33 + 2 * ph)
            fa = (d - c) / math.pi + wob
            fb = (d + c) / math.pi + wob
            # keep each cel shadow band a readable 25-40 px wide (thickness face / shadow side)
            w = self.width(i)
            cap = (38.0 + 4.0 * math.sin(s * 9 + ph)) / w
            fb = max(fb, 1.0 - cap)
            fa = min(fa, cap)
            hi = None
            if R > T_HI:
                ch = math.acos(T_HI / R)
                hi = ((d - ch) / math.pi + wob * 0.6, (d + ch) / math.pi + wob * 0.6)
            res.append((a, fa, fb, hi))
        return res


def arch_spine_pts(arch, i0, i1, step=6):
    return [arch.p[i] for i in range(i0, i1 + 1, step)] + [arch.p[i1]]


def draw_echo(o, arch, rng):
    bid = o.defpath(arch.shape())
    o.use(bid, ECHO['lit'])
    lt = arch.light(rng.uniform(0, 6.28))
    n = arch.n
    # one cel shadow (inner side / outer side), no outline
    fl = [lt[i][2] < 0.97 for i in range(n)]
    for i0, i1 in ranges(fl):
        o.path(arch.band(lambda i: clamp(lt[i][2], 0, 1), lambda i: 1.01, i0, i1), ECHO['sh'])
    fl = [lt[i][1] > 0.03 for i in range(n)]
    for i0, i1 in ranges(fl):
        o.path(arch.band(lambda i: -0.01, lambda i: clamp(lt[i][1], 0, 1), i0, i1), ECHO['sh'])
    # thin soft lit edge (outer edge where it faces the light, inner edge on the right leg)
    for side, sgn in ((0, 1), (1, -1)):
        fl = [sgn * lt[i][0] > 0.3 for i in range(n)]
        for i0, i1 in ranges(fl, 6):
            m = i1 - i0
            o.path(arch.eband(side, lambda i: 0.3,
                              lambda i, i0=i0, m=m: -0.3 - 3.2 * ends_taper((i - i0) / max(1, m), 0.2, 0.2, 0.7),
                              i0, i1), ECHO['edge'])
    return bid


def draw_arch(o, arch, cfg, rng):
    """Hero ring arch, all opaque cel shapes."""
    bid = o.defpath(arch.shape())
    n = arch.n
    lt = arch.light(rng.uniform(0, 6.28))
    o.use(bid, RIB['lit'])

    # --- one opaque highlight shape on the lit face (upper-left)
    fl = [lt[i][3] is not None and (lt[i][3][1] - lt[i][3][0]) * arch.width(i) > 3 for i in range(n)]
    for i0, i1 in ranges(fl, 4):
        o.path(arch.band(lambda i: clamp(lt[i][3][0], 0.03, 0.97), lambda i: clamp(lt[i][3][1], 0.03, 0.97),
                         i0, i1), RIB['hi'])

    # --- one opaque cel shadow per side
    fl = [lt[i][2] < 0.985 for i in range(n)]
    for i0, i1 in ranges(fl):
        o.path(arch.band(lambda i: clamp(lt[i][2], 0, 1), lambda i: 1.01, i0, i1), RIB['sh'])
    fl = [lt[i][1] > 0.015 for i in range(n)]
    for i0, i1 in ranges(fl):
        o.path(arch.band(lambda i: -0.01, lambda i: clamp(lt[i][1], 0, 1), i0, i1), RIB['sh'])

    # --- crease (#771d26) hugging the shadow edge, inside the shadow band
    for side, sgn in ((1, -1), (0, 1)):
        sh = [smooth01(0.0, -0.35, sgn * lt[i][0]) for i in range(n)]
        fl = [v > 0.05 for v in sh]
        for i0, i1 in ranges(fl, 5):
            o.path(arch.eband(side, lambda i: 0.5, lambda i: -(2.0 + 7.0 * sh[i]), i0, i1), RIB['deep'])

    # --- dashes following the curve (30-90 px, with gaps), clustered on the lit shoulder
    lo, hi_ = cfg.get('dash_s', (0.1, 0.48))
    for k in range(cfg.get('dashes', 16)):
        on_right = rng.random() < 0.2
        s0 = rng.uniform(0.6, 0.82) if on_right else rng.triangular(lo, hi_, lo + (hi_ - lo) * 0.45)
        i0 = int(s0 * (n - 1))
        ln = rng.uniform(30, 90)
        acc, i1 = 0.0, i0
        while i1 < n - 2 and acc < ln:
            acc += math.hypot(arch.p[i1 + 1][0] - arch.p[i1][0], arch.p[i1 + 1][1] - arch.p[i1][1])
            i1 += 1
        a, fa, fb, hi = lt[i0]
        r = rng.random()
        if r < 0.7:       # on the lit face
            f = rng.uniform(max(0.1, fa + 0.06), max(0.12, fb - 0.08))
            col = RIB['d_light'] if rng.random() < 0.5 else RIB['d_dark']
        else:             # in the shadow band
            if fb < 0.9:
                f = rng.uniform(fb + 0.04, min(0.93, fb + 0.18))
            elif fa > 0.1:
                f = rng.uniform(max(0.07, fa - 0.18), fa - 0.04)
            else:
                continue
            col = RIB['d_sh']
        wig = rng.uniform(0, 6.28)
        w = rng.uniform(2.8, 5.2)
        for rep in range(2 if rng.random() < 0.3 else 1):     # sometimes a paired stroke
            ff = f + rep * 9.0 / arch.width(i0)
            j0 = i0 + rep * 3
            j1 = max(j0 + 3, i1 - rep * 6)
            poly = [arch.pt(i, ff + 0.012 * math.sin(i * 0.15 + wig)) for i in range(j0, j1 + 1)]
            o.path(tapered(poly, lambda t, w=w * (1 - 0.3 * rep): w * ends_taper(t, 0.3, 0.45, 0.8), 10), col)

    # --- saturated lit-edge stroke (#f66a62) along the edges that face the light
    for side, sgn in ((0, 1), (1, -1)):
        lv = [smooth01(0.28, 0.6, sgn * lt[i][0]) for i in range(n)]
        fl = [v > 0.04 for v in lv]
        for i0, i1 in ranges(fl, 6):
            o.path(arch.eband(side, lambda i: -0.6, lambda i: -0.6 - 7.5 * lv[i], i0, i1), RIB['edge'])

    # --- broken pale rim (#f4a69c), 4-6 px, only on strongly lit stretches (<= ~1 % of the area)
    for (side, s0, s1, w) in cfg['rims']:
        i0, i1 = int(s0 * (n - 1)), int(s1 * (n - 1))
        m = i1 - i0
        o.path(arch.eband(side, lambda i: -1.0,
                          lambda i, i0=i0, m=m, w=w: -1.0 - w * ends_taper((i - i0) / m, 0.25, 0.3, 0.7),
                          i0, i1, 12), RIM_PALE)

    # --- ink: opaque tapered #6e1a24, only on the shadow side (3-4 px)
    for side, sgn in ((1, -1), (0, 1)):
        wv = [0.0 if sgn * lt[i][0] > 0.1 else 1.0 + 3.0 * smooth01(0.1, -0.4, sgn * lt[i][0]) for i in range(n)]
        # fade in/out
        fl = [v > 0.3 for v in wv]
        for i0, i1 in ranges(fl, 5):
            m = i1 - i0
            o.path(arch.eband(side, lambda i: 0.4 * wv[i] * ends_taper((i - i0) / m, 0.06, 0.06, 0.6),
                              lambda i, i0=i0, m=m: -0.6 * wv[i] * ends_taper((i - i0) / m, 0.06, 0.06, 0.6),
                              i0, i1), LINE)
    return bid


# ---------------------------------------------------------------- MOUNDS (bottom strip)
def mound_pts(x0, x1, peak, foot_l, foot_r, skew=0.0, shoulder=0.0):
    w = x1 - x0
    px = x0 + w * (0.5 + 0.22 * skew)
    return [
        (x0, foot_l + 26),
        (x0 + w * 0.06, foot_l + 4),
        (x0 + w * 0.2, lerp(foot_l, peak, 0.62)),
        (lerp(x0 + w * 0.2, px, 0.55), peak + 3 + shoulder),
        (px, peak),
        (lerp(px, x1 - w * 0.18, 0.5), lerp(peak, foot_r, 0.25) - shoulder * 0.5),
        (x1 - w * 0.17, lerp(peak, foot_r, 0.62)),
        (x1 - w * 0.05, foot_r + 4),
        (x1, foot_r + 26),
    ]


def mound(o, contour, pal, rng, cap, hatch=3, front=False, occl=0.0):
    """Opaque cel mound: body (base gradient) + lit cap + one shadow crescent + rim + tapered ink."""
    dense = resample(sample_cr(contour, 20), 90)
    n = len(dense)
    nr = normals(dense)
    inward = [mul(v, -1) for v in nr]
    ph = rng.uniform(0, 6.28)
    if occl > 0:
        # opaque contact crease cast on whatever lies behind (clipped to the strip so it never adds silhouette)
        outer = [add(p, mul(v, -occl * ends_taper(i / (n - 1), 0.12, 0.06, 0.7)
                            * (0.5 + 0.5 * smooth01(0.15, 0.8, i / (n - 1)))))
                 for i, (p, v) in enumerate(zip(dense, inward))]
        o.add('<g clip-path="url(#botClip)">')
        o.path(closed_between(dense, outer, 26), DEEP)
        o.add('</g>')
    body = pick(dense, 26)
    track(body)
    d = bez_d(body) + 'L%s %sL%s %sZ' % (f1(body[-1][0]), f1(H), f1(body[0][0]), f1(H))
    bid = o.defpath(d)
    o.use(bid, 'url(#botBase)')
    o.use(bid, 'url(#hazeBot)')     # same distance haze on every body => no seams between bodies
    # lit cap: thick on the left/centre, thinning to the right
    inner = []
    for i, (p, v) in enumerate(zip(dense, inward)):
        t = i / (n - 1)
        dep = cap * smooth01(0.0, 0.09, t) ** 0.7 * (1.0 - 0.75 * smooth01(0.4, 1.0, t)) \
            * (1 + 0.14 * math.sin(t * 11 + ph) + 0.06 * math.sin(t * 29 + ph))
        inner.append(add(p, mul(v, dep)))
    o.path(closed_between(dense, inner, 24), pal['lit'])
    # one shadow crescent on the right flank
    a0 = int(0.55 * n)
    seg, segn = dense[a0:], inward[a0:]
    m = len(seg)
    inner2 = [add(p, mul(v, cap * 1.25 * ends_taper(j / (m - 1), 0.45, 0.1, 0.9))) for j, (p, v) in enumerate(zip(seg, segn))]
    o.path(closed_between(seg, inner2, 12), pal['sh'])
    # rim light along the lit part of the edge
    seg = dense[int(0.07 * n): int(0.52 * n)]
    segn = inward[int(0.07 * n): int(0.52 * n)]
    poly = [add(p, mul(v, 1.9)) for p, v in zip(seg, segn)]
    o.path(tapered(poly, lambda t: (3.6 if front else 3.0) * ends_taper(t, 0.25, 0.4, 0.8)), pal['rim'])
    if pal['pale']:
        m = len(seg)
        poly = [add(p, mul(v, 1.6)) for p, v in zip(seg[m // 4: m * 3 // 5], segn[m // 4: m * 3 // 5])]
        o.path(tapered(poly, lambda t: 1.8 * ends_taper(t, 0.35, 0.35, 0.8), 8), pal['pale'])
    # outline: absent on the lit left, heavier on the shadow side
    w0, w1 = pal['line']
    a0 = int(0.3 * n)
    o.path(tapered(dense[a0:], lambda t: (0.8 + (w1 - 0.8) * smooth01(0.0, 0.6, t)) * ends_taper(t, 0.12, 0.08, 0.6)),
           LINE)
    # painterly dashes following the contour inside the body (opaque, light + dark)
    for k in range(hatch + 1):
        t0 = rng.uniform(0.12, 0.7)
        t1 = min(0.95, t0 + rng.uniform(0.12, 0.3))
        dep = rng.uniform(cap * 1.05, cap * 1.9)
        ii = range(int(t0 * (n - 1)), int(t1 * (n - 1)) + 1)
        poly = [add(dense[i], mul(inward[i], dep + 2.0 * math.sin(i * 0.3 + ph))) for i in ii]
        col = pal['lit'] if k % 2 == 0 else pal['hatch']
        o.path(tapered(poly, lambda t, w=rng.uniform(2.4, 4.0): w * ends_taper(t, 0.3, 0.4, 0.8), 10), col)
    # a few opaque hatch ticks on the body below the cap
    for k in range(hatch):
        t = rng.uniform(0.18, 0.85)
        i = int(t * (n - 1))
        c = add(dense[i], mul(inward[i], rng.uniform(cap * 1.1, cap * 2.0)))
        tv = sub(dense[min(n - 1, i + 2)], dense[max(0, i - 2)])
        ang = math.atan2(tv[1], tv[0]) + rng.uniform(-0.1, 0.1)
        o.path(tick(c, ang, rng.uniform(12, 26), rng.uniform(0.9, 1.4), rng.uniform(-1.5, 1.5)), pal['hatch'])
    return bid


# ---------------------------------------------------------------- TOP STRIP vaults + soffits
def vault_pts(xa, xb, spring, apex, ext=0.1, n=15, p=0.55):
    out = []
    for k in range(n):
        t = -ext + (1 + 2 * ext) * k / (n - 1)
        x = lerp(xa, xb, t)
        y = spring - (spring - apex) * max(0.0, math.sin(math.pi * clamp(t, 0, 1))) ** p
        out.append((x, y))
    return out


def soffit(o, curve, recess, rim_w=3.0):
    """Receding arch soffit: rim (#d8635f) on its lower edge, recess (#771d26) under it.
    `recess` = px depth of the dark band below the curve (clipped to the strip)."""
    dense = resample(sample_cr(curve, 16), 80)
    below = [(x, y + recess) for (x, y) in dense]
    o.path(closed_between(dense, below, 26), DEEP)
    nr = normals(dense)   # left normal of a left->right curve over the top = up (into the soffit face)
    poly = [add(p, mul(v, rim_w * 0.5)) for p, v in zip(dense, nr)]
    o.path(tapered(poly, lambda t: rim_w * ends_taper(t, 0.06, 0.06, 0.5), 30), RIM_OUT)


def crown_arcs(o, arch, rng, arcs=((42, None, 3.2, ()), (94, 18, 2.8, ((0.0, 0.42), (0.55, 1.0)))),
               s0=0.3, s1=0.7):
    """Receding outer ring soffits above a hero crown (inside the top strip, clipped to it):
    each is a curve offset outward from the crown's outer edge, rim on its lower edge, recess under it.
    recess None = dark groove all the way down to the crown edge.  `breaks` = rim pieces (t ranges)."""
    n = arch.n
    i0, i1 = int(s0 * (n - 1)), int(s1 * (n - 1))
    m = i1 - i0
    for (d, rec, rw, breaks) in arcs:
        ph = rng.uniform(0, 6.28)
        ii = list(range(i0, i1 + 1, 2))
        tp = [ends_taper((i - i0) / m, 0.28, 0.28, 0.6) * (1 + 0.16 * math.sin(i * 0.05 + ph)) for i in ii]
        curve = [arch.ept(i, 0, d * t) for i, t in zip(ii, tp)]
        if rec is None:
            low = [arch.ept(i, 0, -3) for i in ii]
        else:
            low = [arch.ept(i, 0, max(-3.0, (d - rec) * t)) for i, t in zip(ii, tp)]
        o.path(closed_between(curve, low, 30), DEEP)
        nr = normals(curve)
        poly = [add(p, mul(v, rw * 0.5)) for p, v in zip(curve, nr)]
        for (a, b) in (breaks or ((0.0, 1.0),)):
            seg = poly[int(a * (len(poly) - 1)): int(b * (len(poly) - 1)) + 1]
            if len(seg) > 3:
                o.path(tapered(seg, lambda t: rw * ends_taper(t, 0.2, 0.2, 0.6), 20), RIM_OUT)


# ---------------------------------------------------------------- SHARED SEAM MOTIF (identical in all variants)
# seam coordinates: u = 0 is the border; u > 0 shows at the LEFT edge of a segment, u < 0 at the RIGHT edge.
SEAM_C0 = [(48, 300), (118, 342), (172, 382)]                    # strip contour, then into the first leg
SEAM_S1 = [(u, round(291 + 0.002 * u * u, 1)) for u in range(-330, 331, 55)]     # small soffit straddling the seam
SEAM_S2 = [(u, round(262 + 0.0016 * u * u, 1)) for u in range(-360, 361, 60)]
SEAM_VALLEY = [(-175, 805), (-130, 776), (-90, 749), (-48, 729), (0, 721), (48, 729), (90, 749), (130, 773),
               (176, 801)]                                     # low mound whose top kisses the 720 lip at the seam
SEAM_FOOT_R = (50, 372, 650, 712, 800, -0.3, 3)       # mound_pts args, u > 0  (under the first leg)
SEAM_FOOT_L = (-380, -50, 652, 802, 712, 0.35, 0)      # u < 0 (under the last leg)


def seam_motif_top(o):
    """Soffits of the seam vault (clipped to the top strip)."""
    MOTIF[0] = True
    for X in (0, W):
        soffit(o, [(u + X, y) for (u, y) in SEAM_S2], 13)
        soffit(o, [(u + X, y) for (u, y) in SEAM_S1], 90)
    MOTIF[0] = False


def seam_motif_recess(o):
    MOTIF[0] = True
    for X in (0, W):
        o.path(bez_d([(X - 90, 716), (X - 30, 716), (X + 30, 716), (X + 90, 716), (X + 90, 790), (X - 90, 790)],
                     closed=True), DEEP)
    MOTIF[0] = False


def seam_motif_feet(o, sil, rng_seed):
    MOTIF[0] = True
    for X in (0, W):
        for spec in (SEAM_FOOT_R, SEAM_FOOT_L):
            x0, x1, pk, fl, fr, sk, sh = spec
            bid = mound(o, mound_pts(x0 + X, x1 + X, pk, fl, fr, sk, sh), ROWS[2], random.Random(rng_seed), 38,
                        hatch=3, front=True, occl=11)
            sil.append(bid)
    MOTIF[0] = False


def seam_motif_valley(o, sil, rng_seed):
    MOTIF[0] = True
    for X in (0, W):
        o.add('<g clip-path="url(#botClip)">')      # never lifts the silhouette above the 720 lip
        bid = mound(o, [(u + X, y) for (u, y) in SEAM_VALLEY], ROWS[1], random.Random(rng_seed), 22, hatch=2, occl=8)
        o.add('</g>')
        sil.append(bid)
    MOTIF[0] = False


# ---------------------------------------------------------------- DEFS
def defs_head():
    return '''<defs>
  <filter id="grain" x="0" y="0" width="100%" height="100%" filterUnits="userSpaceOnUse">
    <feTurbulence type="fractalNoise" baseFrequency="0.9 0.6" numOctaves="2" seed="7" stitchTiles="stitch" result="n"/>
    <feColorMatrix in="n" type="matrix" values="0 0 0 0 0.35  0 0 0 0 0.06  0 0 0 0 0.08  0 0 0 0.10 0"/>
    <feComposite in2="SourceGraphic" operator="in"/>
  </filter>
  <filter id="mottle" x="0" y="0" width="100%" height="100%" filterUnits="userSpaceOnUse">
    <feTurbulence type="fractalNoise" baseFrequency="0.008 0.02" numOctaves="3" seed="3" stitchTiles="stitch" result="n"/>
    <feColorMatrix in="n" type="matrix" values="0 0 0 0 0.98  0 0 0 0 0.55  0 0 0 0 0.55  0 0 0 0.16 0"/>
    <feComposite in2="SourceGraphic" operator="in"/>
  </filter>
  <linearGradient id="topBase" gradientUnits="userSpaceOnUse" x1="0" y1="300" x2="0" y2="0">
    <stop offset="0" stop-color="@S0@"/>
    <stop offset="1" stop-color="@S1@"/>
  </linearGradient>
  <linearGradient id="botBase" gradientUnits="userSpaceOnUse" x1="0" y1="720" x2="0" y2="1080">
    <stop offset="0" stop-color="@S0@"/>
    <stop offset="1" stop-color="@S1@"/>
  </linearGradient>
  <linearGradient id="hazeBot" gradientUnits="userSpaceOnUse" x1="0" y1="640" x2="0" y2="800">
    <stop offset="0" stop-color="#cc4c4e" stop-opacity="0.12"/>
    <stop offset="1" stop-color="#cc4c4e" stop-opacity="0"/>
  </linearGradient>
'''.replace('@S0@', TOP_STOPS[0]).replace('@S1@', TOP_STOPS[1])


# ---------------------------------------------------------------- BUILD
def build(spec, seed, debug=None):
    global FEATURE_PTS
    FEATURE_PTS = []
    rng = random.Random(seed)
    o = Out()
    sil = []
    heroes = [Arch(**a['geo']) for a in spec['arches']]
    echoes = [Arch(**a['echo']) for a in spec['arches']]

    # ======== TOP STRIP silhouette: seam vault -> arch 1 (hidden under its crown) -> spandrel vault -> ...
    YJ = spec.get('yj', 440)
    first, last = heroes[0], heroes[-1]
    pb = PB((0, 0))
    pb.L([(0, TOP_Y), (M, TOP_Y)])
    j0 = first.idx_at_y(YJ, 0)
    pts = list(SEAM_C0) + spec['c0_left'] + [first.p[j0]]
    pb.CR(pts, start_tan=(70.0, 0.0))
    spans = []
    for k, arch in enumerate(heroes):
        ja = arch.idx_at_y(YJ, 0)
        jb = arch.idx_at_y(YJ, 1)
        pb.L(arch_spine_pts(arch, ja, jb, 5)[1:])
        if k + 1 < len(heroes):
            nxt = heroes[k + 1]
            sp = spec['spandrels'][k]
            xa = arch.edge_x_at_y(sp['spring'], 1, 0)
            xb = nxt.edge_x_at_y(sp['spring'], 0, 0)
            v = vault_pts(xa, xb, sp['spring'], sp['apex'], ext=0.0, p=sp.get('p', 0.55))
            jn = nxt.idx_at_y(YJ, 0)
            pb.CR([arch.p[jb], (xa - 14, sp['spring'] + 8)] + v + [(xb + 14, sp['spring'] + 8), nxt.p[jn]])
            spans.append((arch, nxt, sp))
    jl = last.idx_at_y(YJ, 1)
    pts = [last.p[jl]] + spec['c0_right'] + [(W - u, y) for (u, y) in reversed(SEAM_C0)]
    pb.CR(pts, end_tan=(70.0, 0.0))
    pb.L([(W, TOP_Y), (W, 0)])
    d_top = pb.done()
    o.defs.append('<path id="topStrip" d="%s"/>' % d_top)
    o.add('<use href="#topStrip" fill="url(#topBase)"/>')
    sil.append('topStrip')

    # vault soffits (clipped to the top strip): shared seam motif + the variant's spandrel vaults
    o.add('<g clip-path="url(#topClip)">')
    seam_motif_top(o)
    for k, a in enumerate(heroes):
        crown_arcs(o, a, random.Random(seed * 10 + k))
    for (a, b, sp) in spans:
        for (dy_apex, dy_spring, rec) in ((-58, -118, 13), (-28, -58, 90)):
            spring = sp['spring'] + dy_spring
            xa = a.edge_x_at_y(spring, 1, 0)
            xb = b.edge_x_at_y(spring, 0, 0)
            curve = vault_pts(xa, xb, spring, sp['apex'] + dy_apex, ext=0.22, n=17, p=sp.get('p', 0.55) + 0.1)
            soffit(o, curve, rec)
    # a few opaque hatch ticks on the strip face high up (mostly behind the main ceiling)
    for k in range(spec.get('top_ticks', 48)):
        x = rng.uniform(SAFE + 30, W - SAFE - 30)
        y = rng.uniform(30, 240)
        o.path(tick((x, y), rng.uniform(-0.2, 0.2), rng.uniform(14, 30), rng.uniform(1.0, 1.6)),
               '#851f2c' if k % 3 else '#c13a40')
    o.add('</g>')

    # ======== BOTTOM STRIP base
    pb = PB((0, H))
    pb.L([(0, BOT_Y), (M, BOT_Y)])
    pts = [(M, BOT_Y)] + spec['bot_contour'] + [(W - M, BOT_Y)]
    pb.CR(pts, start_tan=(60.0, 0.0), end_tan=(60.0, 0.0))
    pb.L([(W, BOT_Y), (W, H)])
    d_bot = pb.done()
    o.defs.append('<path id="botStrip" d="%s"/>' % d_bot)
    o.add('<use href="#botStrip" fill="url(#botBase)"/>')
    sil.append('botStrip')
    o.add('<g clip-path="url(#botClip)">')
    seam_motif_recess(o)
    o.add('</g>')

    def row(r, items, capd, front=False, occl=0.0):
        ids = []
        for it in items:
            x0, x1, peak, fl, fr, skew = it[:6]
            sh = it[6] if len(it) > 6 else 0.0
            small = (x1 - x0) < 150
            bid = mound(o, mound_pts(x0, x1, peak, fl, fr, skew, sh), ROWS[r], rng, capd * (0.7 if small else 1.0),
                        hatch=1 if small else 3, front=front, occl=occl)
            sil.append(bid)
            ids.append(bid)
        return ids

    o.use('botStrip', 'url(#hazeBot)')
    back_ids = row(0, spec['rows'][0], 20)

    # ======== ECHO rings (behind the heroes), then the mid mound row
    echo_ids = []
    for k, e in enumerate(echoes):
        echo_ids.append(draw_echo(o, e, random.Random(seed * 100 + 50 + k)))
        sil.append(echo_ids[-1])
    mid_ids = row(1, spec['rows'][1], 30, occl=9)

    # ======== HERO arches
    hero_ids = []
    for k, (arch, a) in enumerate(zip(heroes, spec['arches'])):
        hero_ids.append(draw_arch(o, arch, a, random.Random(seed * 100 + k)))
        sil.append(hero_ids[-1])

    # ======== front mounds: shared seam feet + variant foot mounds/rows, shared valley mound, front-most row
    front_ids = []
    nfeet = len(sil)
    seam_motif_feet(o, sil, 4242)
    front_ids += sil[nfeet:]
    front_ids += row(2, spec['rows'][2], 38, front=True, occl=11)
    nv = len(sil)
    seam_motif_valley(o, sil, 777)
    front_ids += sil[nv:]
    front_ids += row(3, spec['rows'][3], 40, front=True, occl=12)
    front_ids += row(3, spec['rows'][4], 40, front=True, occl=12)
    front_ids += row(3, spec['rows'][5], 40, front=True, occl=12)

    # ======== shared grain + mottle overlay (full-canvas filter region => seamless)
    defs_extra = list(o.defs)
    defs_extra.append('<clipPath id="topClip"><use href="#topStrip"/></clipPath>')
    defs_extra.append('<clipPath id="botClip"><use href="#botStrip"/></clipPath>')
    defs_extra.append('<g id="sil">%s</g>' % ''.join('<use href="#%s"/>' % s for s in sil))
    o.add('<g filter="url(#mottle)" opacity="%s"><use href="#sil"/></g>' % spec.get('mottle_op', 0.5))
    o.add('<g filter="url(#grain)"><use href="#sil"/></g>')

    bad = [p for p in FEATURE_PTS if p[0] < SAFE - 6 or p[0] > W - SAFE + 6]
    if bad:
        print('MARGIN VIOLATION', spec['name'], len(bad), bad[:5], file=sys.stderr)

    head = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d">' % (W, H, W, H)
    svg = [head, defs_head() + '  ' + '\n  '.join(defs_extra) + '\n</defs>'] + o.parts + ['</svg>']

    if debug:
        dd = defs_head() + '  ' + '\n  '.join(defs_extra) + '\n</defs>'

        def mask(white, black, name):
            body = ['<rect width="%d" height="%d" fill="#000"/>' % (W, H)]
            body += ['<use href="#%s" fill="#fff"/>' % s for s in white]
            body += ['<use href="#%s" fill="#000"/>' % s for s in black]
            with open(os.path.join(debug, '%s_%s.svg' % (spec['name'], name)), 'w') as fh:
                fh.write('\n'.join([head, dd] + body + ['</svg>']) + '\n')
        mask(hero_ids, front_ids, 'ribmask')
        mask(echo_ids, mid_ids + hero_ids + front_ids, 'echomask')
        for k, a in enumerate(heroes):
            for leg in (0, 1):
                xs = {y: a.p[a.idx_at_y(y, leg)][0] for y in (340, 380, 530, 680, 700)}
                ang = []
                for y in range(380, 681, 20):
                    i = a.idx_at_y(y, leg)
                    t = sub(a.p[min(a.n - 1, i + 1)], a.p[max(0, i - 1)])
                    ang.append(math.degrees(math.atan2(abs(t[0]), abs(t[1]))))
                print('%s arch %d leg %d: bow(340->700) %.0f px, lean y380-680 mean %.0f deg (min %.0f max %.0f),'
                      ' width@530 %.0f' % (spec['name'], k, leg, abs(xs[340] - xs[700]), sum(ang) / len(ang),
                                           min(ang), max(ang), a.width(a.idx_at_y(530, leg))))
            print('%s arch %d: outer span %.0f px (feet, y=690)' % (spec['name'], k,
                  a.edge_x_at_y(690, 1, 0) - a.edge_x_at_y(690, 0, 0)))
            print('%s arch %d: cx %.0f rx %.0f ry %.0f | crown underside y %.0f | legs@530 x %.0f / %.0f'
                  ' | outer@410 %.0f/%.0f | outer@300 %.0f/%.0f' % (
                      spec['name'], k, a.cx, a.rx, a.ry, a.pt(a.n // 2, 1.0)[1],
                      a.p[a.idx_at_y(530, 0)][0], a.p[a.idx_at_y(530, 1)][0],
                      a.edge_x_at_y(410, 0), a.edge_x_at_y(410, 1), a.edge_x_at_y(300, 0), a.edge_x_at_y(300, 1)))
    return '\n'.join(svg) + '\n'


# ====================================================================== VARIANTS
def arch_spec(xl, xr, yc, wc, wm=124, wf=86, wob=(), bl=(), br=(), skew=0.0, ewc=66, ewf=50, tuck=12, **cfg):
    geo = dict(xl=xl, xr=xr, yc=yc, wc=wc, wm=wm, wf=wf, wob=wob, bl=bl, br=br, skew=skew)
    # echo ring: concentric, tucked ~12 px behind the hero's inner edge
    dfoot = wf / 2 + ewf / 2 - tuck
    dcrown = wc / 2 + ewc / 2 - tuck
    echo = dict(xl=xl + dfoot, xr=xr - dfoot, yc=yc + dcrown, wc=ewc, wm=(ewc + ewf) / 2 + 2, wf=ewf,
                wob=wob, skew=skew * 0.8, ybot=760)
    base = dict(rims=[], dashes=16)
    base.update(cfg)
    return dict(geo=geo, echo=echo, **base)


SPEC_A = dict(
    name='rear_a',
    arches=[
        arch_spec(175, 978, 232, 172, wm=128, wf=88, wob=[(0.012, 3, 0.4), (0.006, 7, 1.0)],
                  bl=[(0.3, 5, 0.04), (0.62, -4, 0.05)], br=[(0.22, 6, 0.035), (0.45, 7, 0.04), (0.78, 5, 0.03)],
                  skew=-14, rims=[(0, 0.13, 0.22, 5.5), (0, 0.27, 0.36, 6.0), (1, 0.7, 0.78, 4.5)], dashes=34),
        arch_spec(1132, 1748, 268, 150, wm=118, wf=82, wob=[(0.012, 5, 0.3)],
                  bl=[(0.4, 5, 0.04)], br=[(0.25, 6, 0.04), (0.58, 5, 0.035)], skew=10,
                  rims=[(0, 0.16, 0.26, 5.0), (1, 0.68, 0.76, 4.5), (1, 0.81, 0.86, 4.0)], dashes=28),
    ],
    spandrels=[dict(spring=408, apex=286, p=0.5)],
    c0_left=[(226, 414)],
    c0_right=[(1694, 414)],
    bot_contour=[(110, 726), (170, 736), (300, 738), (520, 742), (760, 736), (940, 740), (1060, 728),
                 (1180, 738), (1400, 742), (1600, 736), (1750, 736), (1810, 726)],
    rows=[
        # back row: tops 700-735 inside the openings (defines the dipping contour)
        [(262, 470, 708, 732, 726, 0.2), (420, 640, 710, 730, 734, -0.3), (590, 790, 703, 734, 728, 0.25),
         (740, 930, 716, 728, 734, -0.1), (1180, 1350, 711, 734, 728, 0.15), (1300, 1480, 700, 728, 734, -0.25),
         (1440, 1620, 718, 734, 730, 0.2), (1580, 1700, 708, 730, 736, -0.1)],
        # mid row: in front of the echo feet
        [(212, 420, 742, 772, 766, 0.3, 4), (380, 660, 752, 766, 774, -0.15), (600, 850, 738, 774, 768, 0.2, 5),
         (800, 960, 750, 768, 776, -0.2), (1150, 1420, 744, 776, 768, 0.1, 4), (1380, 1560, 754, 768, 774, -0.2),
         (1520, 1720, 740, 774, 770, 0.25)],
        # front row: big foot mound over A1-right / A2-left (+ mounds between)
        [(856, 1270, 644, 800, 804, 0.0, 3), (330, 640, 782, 812, 806, 0.2, 5), (560, 900, 772, 806, 814, -0.2),
         (1180, 1480, 784, 812, 806, 0.25, 4), (1420, 1680, 774, 806, 812, -0.15)],
        # front-most row (mostly under the near floor)
        [(64, 470, 842, 880, 874, 0.1, 6), (410, 860, 830, 874, 884, -0.2), (800, 1290, 846, 884, 876, 0.2, 5),
         (1230, 1560, 834, 876, 882, -0.1), (1500, 1858, 846, 882, 878, 0.15, 5)],
        [(64, 560, 930, 968, 962, -0.1, 6), (500, 1020, 916, 962, 972, 0.2), (960, 1400, 934, 972, 964, -0.2, 5),
         (1340, 1858, 922, 964, 970, 0.1, 6)],
        [(64, 700, 1004, 1046, 1040, 0.15), (640, 1240, 1012, 1040, 1050, -0.1, 6), (1180, 1858, 1000, 1050, 1044, 0.2)],
    ],
)

SPEC_B = dict(
    name='rear_b',
    arches=[
        arch_spec(170, 788, 280, 148, wm=116, wf=80, wob=[(0.012, 4, 1.1), (0.006, 9, 0.3)],
                  bl=[(0.36, 5, 0.04)], br=[(0.2, 6, 0.04), (0.52, 6, 0.035)], skew=12,
                  rims=[(0, 0.15, 0.25, 5.0), (1, 0.7, 0.8, 4.5)], dashes=26),
        arch_spec(952, 1752, 222, 178, wm=130, wf=90, wob=[(0.01, 3, 0.9), (0.007, 8, 2.1)],
                  bl=[(0.28, 6, 0.04), (0.55, 4, 0.05)], br=[(0.2, 7, 0.035), (0.4, 6, 0.03), (0.7, 6, 0.04)],
                  skew=-16, rims=[(0, 0.12, 0.2, 5.5), (0, 0.25, 0.33, 6.0), (0, 0.38, 0.42, 4.0),
                                  (1, 0.72, 0.8, 4.5)], dashes=36),
    ],
    spandrels=[dict(spring=418, apex=282, p=0.6)],
    c0_left=[(226, 416)],
    c0_right=[(1694, 414)],
    bot_contour=[(110, 726), (170, 736), (330, 740), (470, 734), (640, 742), (780, 736), (850, 724),
                 (930, 736), (1100, 740), (1300, 734), (1480, 742), (1640, 736), (1750, 736), (1810, 726)],
    rows=[
        [(248, 400, 712, 734, 728, -0.2), (360, 560, 702, 728, 734, 0.3), (520, 690, 720, 734, 730, -0.1),
         (1010, 1160, 716, 732, 728, 0.1), (1120, 1330, 704, 728, 734, -0.2), (1290, 1430, 722, 734, 728, 0.2),
         (1390, 1580, 706, 728, 734, 0.15), (1540, 1690, 718, 734, 730, -0.25)],
        [(230, 470, 748, 770, 774, -0.2), (430, 700, 740, 774, 768, 0.25, 4), (818, 922, 730, 760, 756, 0.0),
         (990, 1220, 746, 768, 776, 0.1), (1180, 1450, 738, 776, 768, -0.25, 5), (1410, 1710, 750, 768, 774, 0.2)],
        [(664, 900, 652, 802, 744, 0.15, 2), (850, 1086, 660, 742, 804, -0.15, 2), (300, 560, 776, 806, 812, -0.1),
         (500, 700, 786, 812, 806, 0.3), (1020, 1300, 772, 806, 812, 0.2, 4), (1250, 1640, 782, 812, 806, -0.2, 5)],
        [(64, 330, 816, 852, 860, -0.15, 5), (290, 760, 848, 884, 876, 0.2), (700, 1060, 832, 876, 882, -0.1, 6),
         (1000, 1480, 844, 882, 878, 0.15), (1520, 1858, 858, 892, 886, -0.2, 5), (1400, 1600, 836, 876, 880, 0.1)],
        [(64, 360, 952, 990, 984, 0.2, 5), (300, 900, 934, 970, 962, -0.15), (840, 1240, 918, 962, 968, 0.1, 6),
         (1240, 1858, 904, 944, 952, -0.2)],
        [(64, 480, 1030, 1066, 1060, -0.2, 5), (420, 1100, 998, 1050, 1042, 0.15), (1100, 1858, 990, 1030, 1040, -0.1)],
    ],
)


def main():
    root = os.getcwd()
    outdir = os.path.join(root, 'public', 'assets', 'svg', 'environment')
    if not os.path.isdir(outdir):
        sys.exit('run from the repo root (public/assets/svg/environment not found)')
    debug = None
    if '--debug' in sys.argv:
        debug = sys.argv[sys.argv.index('--debug') + 1]
        os.makedirs(debug, exist_ok=True)
    for spec, seed in ((SPEC_A, 11), (SPEC_B, 23)):
        svg = build(spec, seed, debug)
        path = os.path.join(outdir, spec['name'] + '.svg')
        with open(path, 'w') as fh:
            fh.write(svg)
        print('%s  %.1f KB' % (os.path.relpath(path, root), len(svg.encode()) / 1024))


if __name__ == '__main__':
    main()
