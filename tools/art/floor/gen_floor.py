#!/usr/bin/env python3
"""Near-floor generator (layer 4, main plane, scroll 1.0) - floor_a/b/c.svg, 1920x360.

    python3 -I tools/art/floor/gen_floor.py            # writes public/assets/svg/environment/floor_*.svg
    python3 -I tools/art/floor/gen_floor.py OUT_DIR    # writes OUT_DIR/floor_*.svg instead
    python3 -I tools/art/floor/gen_floor.py OUT_DIR a  # only variant a

The floor of panel 4 of reference.png is a field of long, low, overlapping dunes that sweep diagonally
into the distance. Every dune here is a `Ridge` hand-placed in layouts.py: an asymmetric superellipse
cap (exponent ~1.4-1.6, one slope 2x longer than the other, tilted so it rises 30-60 px across its
length) whose flanks keep diving at a finite slope below the canvas. Ridges are painted back to front;
for each one this script paints, in cel style:

  trough   opaque cel shadow on the dune *behind*, just above this ridge's contour (the valley)
  body     flat lit colour of the row
  shadow   one opaque cel shadow (#93201e) on the steep / lower side
  crest    one opaque pale crest band (#e8705f) over the top ~20 % of the ridge height,
           with a #f3b8a6 dry-brush rim and streaks
  marks    2-3 clusters of short comma / dash strokes
  crease   #6e1a24 ink, 2-4 px, opaque, ONLY along the lower overlap crease (where this ridge's top
           passes in front of a farther dune), tapered, stopping 15-30 % short of that dune's ends.
           Lit top silhouettes (the floor's skyline) get no outline.

Tiling contract (shared seam motif): every variant draws the same seam stack (SEAM in layouts.py,
seam-mound apex at y=SEAM_Y with a horizontal tangent exactly on the border) at x=0 and again at
x=1920, from identical path data. Variant art is clipped to [ZONE, W-ZONE], so the outer ZONE px on
each side are pixel-identical in every variant and a dune always spans the join.
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
DEFAULT_OUT = os.path.join(ROOT, 'public', 'assets', 'svg', 'environment')

W, H = 1920, 360
SEAM_Y = 72          # contour y on both borders (apex of the shared seam mound, horizontal tangent)
ZONE = 150           # shared seam zone: x < ZONE and x > W - ZONE are identical in every variant
BOTTOM = 470         # ridge bodies extend below the canvas
BASE_STOPS = (('0', '#d83635'), ('1', '#9b2023'))  # manifest base gradient (unchanged)

MOTTLE = '0 0 0 0 0.94  0 0 0 0 0.36  0 0 0 0 0.30  0 0 0 0.08 0'  # shared mottle (new values)


# ----------------------------------------------------------------------------- helpers
def fmt(v):
    s = f"{v:.1f}"
    if s.endswith('.0'):
        s = s[:-2]
    if s == '-0':
        s = '0'
    return s


def bez(p0, c1, c2, p3, t):
    mt = 1 - t
    a, b, c, d = mt * mt * mt, 3 * mt * mt * t, 3 * mt * t * t, t * t * t
    return (a * p0[0] + b * c1[0] + c * c2[0] + d * p3[0], a * p0[1] + b * c1[1] + c * c2[1] + d * p3[1])


def smooth_segs(pts, k=1 / 3):
    """Catmull-Rom style cubic fit through pts with chord-weighted unit tangents (no overshoot)."""
    n = len(pts)
    tans = []
    for i in range(n):
        if i == 0:
            a, b = pts[0], pts[1]
        elif i == n - 1:
            a, b = pts[-2], pts[-1]
        else:
            p0, p1, p2 = pts[i - 1], pts[i], pts[i + 1]
            d0 = math.hypot(p1[0] - p0[0], p1[1] - p0[1]) or 1e-6
            d1 = math.hypot(p2[0] - p1[0], p2[1] - p1[1]) or 1e-6
            tx = (p1[0] - p0[0]) / d0 + (p2[0] - p1[0]) / d1
            ty = (p1[1] - p0[1]) / d0 + (p2[1] - p1[1]) / d1
            L = math.hypot(tx, ty) or 1e-6
            tans.append((tx / L, ty / L))
            continue
        L = math.hypot(b[0] - a[0], b[1] - a[1]) or 1e-6
        tans.append(((b[0] - a[0]) / L, (b[1] - a[1]) / L))
    segs = []
    for i in range(n - 1):
        p1, p2 = pts[i], pts[i + 1]
        d = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
        a, b = tans[i], tans[i + 1]
        segs.append((p1, (p1[0] + a[0] * d * k, p1[1] + a[1] * d * k), (p2[0] - b[0] * d * k, p2[1] - b[1] * d * k), p2))
    return segs


def segs_d(segs, move=True):
    out = []
    if move:
        out.append(f"M{fmt(segs[0][0][0])} {fmt(segs[0][0][1])}")
    for (_, c1, c2, p) in segs:
        out.append(f"C{fmt(c1[0])} {fmt(c1[1])} {fmt(c2[0])} {fmt(c2[1])} {fmt(p[0])} {fmt(p[1])}")
    return ''.join(out)


def smooth_path(pts):
    if len(pts) == 2:
        return f"M{fmt(pts[0][0])} {fmt(pts[0][1])}L{fmt(pts[1][0])} {fmt(pts[1][1])}"
    return segs_d(smooth_segs(pts))


def normals(pts):
    out = []
    n = len(pts)
    for i in range(n):
        a = pts[max(0, i - 1)]
        b = pts[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy) or 1e-6
        out.append((dy / L, -dx / L))  # "up/out" for a left->right contour
    return out


def resample(pts, step):
    out = [pts[0]]
    acc = 0.0
    for i in range(1, len(pts)):
        a, b = pts[i - 1], pts[i]
        d = math.hypot(b[0] - a[0], b[1] - a[1])
        if d == 0:
            continue
        s = 0.0
        while acc + (d - s) >= step:
            s += step - acc
            t = s / d
            out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
            acc = 0.0
        acc += d - s
    if math.hypot(out[-1][0] - pts[-1][0], out[-1][1] - pts[-1][1]) > step * 0.35:
        out.append(pts[-1])
    else:
        out[-1] = pts[-1]
    return out


def ribbon(center, w_in, w_out, step=3):
    """Closed ribbon around a centre line; w_in / w_out: per-point widths towards -normal / +normal."""
    nr = normals(center)
    outer = [(p[0] + n[0] * wo, p[1] + n[1] * wo) for p, n, wo in zip(center, nr, w_out)]
    inner = [(p[0] - n[0] * wi, p[1] - n[1] * wi) for p, n, wi in zip(center, nr, w_in)]
    idx = list(range(0, len(center), step))
    if idx[-1] != len(center) - 1:
        idx.append(len(center) - 1)
    o = [outer[i] for i in idx]
    i_ = [inner[i] for i in idx][::-1]
    d = smooth_path(o)
    d += f"L{fmt(i_[0][0])} {fmt(i_[0][1])}" + (segs_d(smooth_segs(i_), move=False) if len(i_) > 2 else f"L{fmt(i_[1][0])} {fmt(i_[1][1])}") + 'Z'
    return d


def stroke(center, widths, step=2):
    return ribbon(center, [w * 0.5 for w in widths], [w * 0.5 for w in widths], step=step)


def smoothstep(e0, e1, x):
    t = min(1.0, max(0.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


def window(u, a, b, c, d):
    return smoothstep(a, b, u) * (1 - smoothstep(c, d, u))


def _s(v):
    return max(0.0, math.sin(v))


def pieces(pts, ws, thr=0.12, minlen=4, extra=None):
    """Split a polyline into runs where the width is above thr (optionally also by a key per point)."""
    out, cur, cw, key = [], [], [], None
    for i, (p, w) in enumerate(zip(pts, ws)):
        k = extra[i] if extra else None
        if w < thr or (cur and k != key):
            if len(cur) >= minlen:
                out.append((cur, cw, key))
            cur, cw = [], []
        if w >= thr:
            cur.append(p)
            cw.append(w)
            key = k
    if len(cur) >= minlen:
        out.append((cur, cw, key))
    return out


def taper_ends(ws, k=2.4):
    n = len(ws)
    return [w * min(1.0, _s(math.pi * i / max(1, n - 1)) * k) for i, w in enumerate(ws)]


# ----------------------------------------------------------------------------- styles
# back = hazy (mixed toward the distance haze #c86a6e), thinner/lighter ink; mid + front = full strength.
ROWS = {
    'back': dict(lit='#cd3237', shadow='#9a2530', deep='#86212d', crest='#e56b5d', dry='#f0bcae', ink='#80283a',
                 inkw=2.4, trough=6.0, rimw=1.5, smax=0.5, wob=0.0, marks=(1, 2), mlen=(6, 9), mw=1.3, streaks=(1, 2)),
    'mid': dict(lit='#d2292f', shadow='#93201e', deep='#771d26', crest='#e8705f', dry='#f3b8a6', ink='#6e1a24',
                inkw=3.2, trough=9.0, rimw=2.1, smax=0.6, wob=0.0, marks=(2, 3), mlen=(7, 12), mw=1.7, streaks=(2, 3)),
    'front': dict(lit='#d5292f', shadow='#93201e', deep='#771d26', crest='#e8705f', dry='#f3b8a6', ink='#6e1a24',
                  inkw=4.0, trough=13.0, rimw=2.8, smax=0.7, wob=0.0, marks=(2, 3), mlen=(9, 14), mw=2.2, streaks=(3, 4)),
}


# ----------------------------------------------------------------------------- ridge
class Ridge:
    """Long low dune. Crest at (xc, yc); the cap is a superellipse of exponent m with half-widths al/ar and
    drops hl/hr to its left/right feet (hl != hr tilts the dune so it rises across its length). Past the
    point where the cap gets steeper than smax the flank keeps diving at that slope (no vertical walls)."""

    def __init__(self, key, row, xc, yc, al, ar, hl, hr, m=1.5, smax=None, lobes=(), wob=None, seed=0,
                 lim_l=None, lim_r=None, soft=14, tuck=1.2, band=None, s_end=None, xmin=None, xmax=None,
                 shared=False):
        self.key, self.row = key, row
        self.xc, self.yc, self.al, self.ar, self.hl, self.hr, self.m = xc, yc, al, ar, hl, hr, m
        self.st = ROWS[row]
        self.smax = smax if smax is not None else self.st['smax']
        self.lobes = lobes
        self.lim_l, self.lim_r, self.soft, self.tuck = lim_l, lim_r, soft, tuck
        self.shared = shared
        self.small = False
        self.seed = seed
        self.rng = random.Random(seed)
        # gentle crest undulation (keeps long crests from reading as flat plateaus)
        self.wob = wob if wob is not None else self.st['wob']
        self.wph = self.rng.uniform(0, 6.28)
        self.wf = self.rng.uniform(1 / 160, 1 / 110)
        self.h = max(hl, hr)
        self.band = band if band is not None else self.rng.uniform(0.18, 0.21)
        self.s_end = s_end if s_end is not None else self.rng.uniform(0.15, 0.27)
        self.x0, self.x1 = xc - al, xc + ar
        self.uc = al / (al + ar)
        self.tstar = {}
        for side, a, b in (('l', al, hl), ('r', ar, hr)):
            t, prev = 0.0, 0.0
            while t < a:
                d = self._se(t + 0.5, a, b)
                if (d - prev) / 0.5 >= self.smax:
                    break
                prev = d
                t += 0.5
            self.tstar[side] = (t, prev)
        x = xc
        while self.y(x) < BOTTOM and x > -600:
            x -= 2
        self.xl = x
        x = xc
        while self.y(x) < BOTTOM and x < W + 600:
            x += 2
        self.xr = x
        self.build(xmin, xmax)
        # visible length of the dune (cap + the first part of the flank dives) for end tapers
        lim = self.yc + 1.3 * self.h
        x = xc
        while x > self.xl and self.y(x) < lim:
            x -= 1
        self.e0 = x
        x = xc
        while x < self.xr and self.y(x) < lim:
            x += 1
        self.e1 = x

    def ue(self, x):
        return (x - self.e0) / max(1.0, self.e1 - self.e0)

    # --- geometry
    def _se(self, t, a, b):
        v = min(1.0, abs(t) / a)
        return b * (1 - max(0.0, 1 - v ** self.m) ** (1 / self.m))

    def _base(self, t):
        side = 'l' if t < 0 else 'r'
        a, b = (self.al, self.hl) if t < 0 else (self.ar, self.hr)
        ts, ds = self.tstar[side]
        at = abs(t)
        if at <= ts:
            return self._se(at, a, b)
        dt = at - ts
        return ds + self.smax * dt + 0.0015 * dt * dt

    def D(self, x):
        t = x - self.xc
        d = self._base(t)
        a = self.al if t < 0 else self.ar
        fade = 1 - smoothstep(0.85, 1.1, abs(t) / a)
        for (lx, amp, lw) in self.lobes:
            d -= amp * math.exp(-((x - (self.xc + lx)) / lw) ** 2) * fade
        d += self.wob * math.sin(2 * math.pi * self.wf * x + self.wph) * fade
        return d

    def y(self, x):
        return self.yc + self.D(x)

    def u_at(self, x):
        return (x - self.x0) / (self.al + self.ar)

    def _clampx(self, x):
        s = self.soft
        if self.lim_l is not None:
            z = (x - self.lim_l) / s
            x = x if z > 30 else self.lim_l + s * math.log1p(math.exp(z))
        if self.lim_r is not None:
            z = (self.lim_r - x) / s
            x = x if z > 30 else self.lim_r - s * math.log1p(math.exp(z))
        return x

    def build(self, xmin=None, xmax=None):
        raw = []
        x = self.xl
        while x < self.xr:
            raw.append((x, min(BOTTOM, self.y(x))))
            x += 1.5
        raw.append((self.xr, min(BOTTOM, self.y(self.xr))))
        yeq_l = min(BOTTOM, self.y(self.lim_l)) if self.lim_l is not None and self.xl < self.lim_l else None
        yeq_r = min(BOTTOM, self.y(self.lim_r)) if self.lim_r is not None and self.xr > self.lim_r else None
        pts, us = [], []
        for (x, y) in raw:
            xx = self._clampx(x)
            if yeq_l is not None and x < self.xc and y > yeq_l:
                xx += self.tuck * 10 * ((y - yeq_l) / 100) ** 2
            if yeq_r is not None and x > self.xc and y > yeq_r:
                xx -= self.tuck * 10 * ((y - yeq_r) / 100) ** 2
            pts.append((xx, y))
            us.append(self.u_at(x))
        # resample (keeping the parameter u attached to each knot)
        knots, ku = [pts[0]], [us[0]]
        acc = 0.0
        for i in range(1, len(pts)):
            acc += math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1])
            if acc >= 10 or i == len(pts) - 1:
                knots.append(pts[i])
                ku.append(us[i])
                acc = 0.0
        self.segs = smooth_segs(knots)
        dense, du = [], []
        for si, sg in enumerate(self.segs):
            for i in range(5):
                dense.append(bez(*sg, i / 5))
                du.append(ku[si] + (ku[si + 1] - ku[si]) * i / 5)
        dense.append(self.segs[-1][3])
        du.append(ku[-1])
        self.dense, self.us = dense, du
        self.nr = normals(dense)
        top = {}
        for a, b in zip(dense, dense[1:]):
            x0, x1 = sorted((a[0], b[0]))
            for xi in range(math.ceil(x0), math.floor(x1) + 1):
                t = 0.0 if b[0] == a[0] else (xi - a[0]) / (b[0] - a[0])
                yy = a[1] + (b[1] - a[1]) * t
                if xi not in top or yy < top[xi]:
                    top[xi] = yy
        if xmin is not None:
            top = {k: v for k, v in top.items() if xmin <= k <= xmax}
        self.top = top

    def shape_d(self):
        return segs_d(self.segs) + f"L{fmt(self.dense[-1][0])} {BOTTOM + 40}L{fmt(self.dense[0][0])} {BOTTOM + 40}Z"

    def visible(self, pad=24):
        return [(p, n, u) for p, n, u in zip(self.dense, self.nr, self.us) if p[1] < H + pad]

    def flank_fade(self, x):
        u = self.ue(x)
        return smoothstep(0.0, 0.1, u) * (1 - smoothstep(0.9, 1.0, u))

    def end_window(self, x, k=1.0):
        u = self.ue(x)
        s = self.s_end * k
        return window(u, s, s + 0.1, 1 - s - 0.1, 1 - s)

    def term_depth(self, u):
        """Cel-shadow terminator depth below the contour. Light from the upper left: the long left slope is
        lit deep down, the right flank turns into shadow (the terminator exits through it)."""
        uc = self.uc
        a = 0.74 * self.h
        b = 0.42 * self.h if uc > 0.5 else 0.55 * self.h
        if u <= uc:
            return a
        return a + (b - a) * smoothstep(uc, 1.0, u)

    def band_w(self, u):
        uc = self.uc
        end = uc + (1 - uc) * (0.5 if uc > 0.5 else 0.68)
        return self.band * self.h * window(u, 0.05, 0.28, uc + 0.02, end)


class Nodule:
    """Small oval lump lying on a parent ridge (the little lump on the panel-4 floor)."""

    def __init__(self, parent, cx, w, h, depth, seed=0):
        self.parent, self.row, self.st = parent, parent.row, parent.st
        self.small = True
        self.key = parent.key + '_n'
        self.rng = random.Random(seed)
        self.cx, self.w, self.h = cx, w, h
        self.by = parent.y(cx) + depth
        hw = w / 2
        top = []
        for i in range(25):
            t = i / 24
            x = cx - hw + w * t
            v = abs(2 * t - 1)
            prof = max(0.0, 1 - v ** 2.0) ** 0.55
            y = self.by - h * prof * (1 + 0.14 * (0.5 - t)) + 0.15 * h * (t - 0.5)
            top.append((x, y))
        self.topc = top
        e, s = top[-1], top[0]
        self.under = [e, (e[0] + 2, e[1] + h * 0.3), (cx + hw * 0.5, self.by + h * 0.45), (cx, self.by + h * 0.45),
                      (cx - hw * 0.6, self.by + h * 0.42), (s[0] - 2, s[1] + h * 0.22), s]

    def shape_d(self):
        return smooth_path(self.topc) + segs_d(smooth_segs(self.under), move=False)[0:] + 'Z'


# ----------------------------------------------------------------------------- painter
class Painter:
    def __init__(self, prefix):
        self.prefix = prefix
        self.defs = []
        self.n = 0

    def clip(self, d):
        self.n += 1
        cid = f"{self.prefix}{self.n}"
        self.defs.append(f'<clipPath id="{cid}"><path d="{d}"/></clipPath>')
        return cid

    # --- what lies just above ridge k's contour (painted before k)?
    def crease_profile(self, k, prev):
        prof = []
        for p, n, u in k.visible(30):
            xi = int(round(p[0]))
            best = None
            for j in prev:
                t = j.top.get(xi)
                if t is not None and t < p[1] - 1.0:
                    best = j
            if best is None:
                prof.append((p, n, u, None, 0.0))
                continue
            prof.append((p, n, u, best, p[1] - best.top[xi]))
        return prof

    def trough(self, k, prof, out):
        """Cel shadow on the farther dune, in the valley right above k's contour."""
        pts, ws, keys = [], [], []
        for (p, n, u, j, g) in prof:
            if j is None:
                w = 0.0
            else:
                w = j.st['trough'] * j.end_window(p[0], 0.6) * smoothstep(2, 12, g) * k.flank_fade(p[0])
                w *= 0.85 + 0.15 * math.sin(p[0] / 21 + k.wph)
                w = min(w, 0.5 * g)
            pts.append(p)
            ws.append(w)
            keys.append(j.row if j is not None else None)
        for pc, pw, row in pieces(pts, ws, thr=0.6, minlen=4, extra=keys):
            out.append(f'<path d="{ribbon(pc, [1.5] * len(pc), taper_ends(pw, 3.0), step=4)}" fill="{ROWS[row]["shadow"]}"/>')

    def crease(self, k, prof, out):
        """Ink only along the lower overlap crease: where k passes in front of a farther dune."""
        pts, ws = [], []
        for (p, n, u, j, g) in prof:
            if j is None:
                w = 0.0
            else:
                wmax = min(k.st['inkw'], max(j.st['inkw'], 0.5 * (k.st['inkw'] + j.st['inkw'])))
                w = wmax * j.end_window(p[0]) * smoothstep(1.5, 8, g) * k.flank_fade(p[0])
                w *= 0.82 + 0.18 * math.sin(p[0] / 15 + k.wph) + 0.05 * math.sin(p[0] / 4.7)
            pts.append(p)
            ws.append(w)
        for pc, pw, _ in pieces(pts, ws, thr=0.35, minlen=4):
            pw = taper_ends(pw, 2.0)
            out.append(f'<path d="{ribbon(pc, [w * 0.45 for w in pw], [w * 0.55 for w in pw], step=3)}" fill="{k.st["ink"]}"/>')

    def ridge(self, k, out):
        st, rng = k.st, k.rng
        sd = k.shape_d()
        cid = self.clip(sd)
        g = [f'<g clip-path="url(#{cid})">', f'<path d="{sd}" fill="{st["lit"]}"/>']
        vp = k.visible(40)
        cen = [p for p, n, u in vp]

        # one opaque cel shadow: terminator below the lit slope, exits through the right flank
        term = []
        for p, n, u in vp:
            d = k.term_depth(u)
            wob = 1.6 * math.sin(p[0] / 19.0 + k.wph) + 0.9 * math.sin(p[0] / 7.0 + k.wph * 2)
            term.append((p[0], p[1] + d + wob))
        term = resample(term, 8)
        x0, y0 = term[0]
        x1, y1 = term[-1]
        g.append(f'<path d="{smooth_path(term)}L{fmt(x1 + 400)} {fmt(y1)}L{fmt(x1 + 400)} {BOTTOM + 80}'
                 f'L{fmt(x0 - 400)} {BOTTOM + 80}L{fmt(x0 - 400)} {fmt(y0)}Z" fill="{st["shadow"]}"/>')

        # opaque pale crest band over the top ~20 % (broken lower edge)
        bw = []
        for p, n, u in vp:
            w = k.band_w(u)
            w *= 1 + 0.12 * math.sin(p[0] / 37 + k.wph) + 0.05 * math.sin(p[0] / 13 + 2 * k.wph)
            bw.append(max(0.0, w))
        for pc, pw, _ in pieces(cen, bw, thr=0.25, minlen=4):
            if max(pw) > 1.5:
                g.append(f'<path d="{ribbon(pc, pw, [2.0] * len(pc), step=4)}" fill="{st["crest"]}"/>')
        bmax = max(bw)

        # dry-brush drags hanging below the band (crest colour) and pale streaks inside it
        def along(u0, L, depth_fn, n=None):
            xs0 = k.x0 + u0 * (k.al + k.ar)
            n = n or max(5, int(L / 4))
            c = []
            for i in range(n + 1):
                x = xs0 + L * i / n
                c.append((x, k.y(x) + depth_fn(i / n)))
            return c

        for _ in range(rng.randint(*st['streaks'])):
            u0 = rng.uniform(0.08, max(0.1, k.uc - 0.05))
            L = rng.uniform(0.08, 0.2) * (k.al + k.ar)
            bwu = k.band_w(u0 + L / (k.al + k.ar) / 2)
            if bwu < 2:
                continue
            dd = bwu + rng.uniform(1.0, 3.5)
            sl = rng.uniform(-0.25, 0.25) * bwu
            c = along(u0, L, lambda t: dd + sl * (t - 0.5))
            ww = [rng.uniform(0.9, 1.3) * st['rimw'] * 0.9 * _s(math.pi * i / (len(c) - 1)) ** 0.7 for i in range(len(c))]
            g.append(f'<path d="{stroke(c, ww)}" fill="{st["crest"]}"/>')
        for _ in range(rng.randint(*st['streaks']) + 1):
            u0 = rng.uniform(0.06, max(0.08, k.uc - 0.02))
            L = rng.uniform(0.05, 0.16) * (k.al + k.ar)
            bwu = k.band_w(u0 + L / (k.al + k.ar) / 2)
            if bwu < 4:
                continue
            dd = rng.uniform(0.3, 0.65) * bwu
            c = along(u0, L, lambda t: dd)
            ww = [rng.uniform(0.6, 1.0) * st['rimw'] * 0.7 * _s(math.pi * i / (len(c) - 1)) ** 0.8 for i in range(len(c))]
            g.append(f'<path d="{stroke(c, ww)}" fill="{st["dry"]}" opacity="{rng.uniform(0.45, 0.7):.2f}"/>')

        # dry-brush rim on the lit top edge, broken into a few pieces
        gaps = [(rng.uniform(0.15, k.uc), rng.uniform(0.015, 0.035)) for _ in range(rng.randint(1, 3))]
        rp, rw = [], []
        for p, n, u in vp:
            w = st['rimw'] * window(u, 0.04, 0.16, k.uc - 0.02, k.uc + 0.12) * (0.75 + 0.25 * math.sin(p[0] / 11 + k.wph))
            for (c, gw) in gaps:
                if abs(u - c) < gw:
                    w *= smoothstep(0, gw, abs(u - c)) ** 2
            rp.append((p[0] - n[0] * 1.4, p[1] - n[1] * 1.4))
            rw.append(w)
        for pc, pw, _ in pieces(rp, rw, thr=0.25, minlen=4):
            g.append(f'<path d="{ribbon(pc, taper_ends(pw), [0.0] * len(pc), step=3)}" fill="{st["dry"]}" opacity="0.8"/>')

        # 2-3 clusters of short comma / dash marks
        span = k.al + k.ar
        for _ in range(rng.randint(*st['marks'])):
            uc0 = rng.uniform(0.15, 0.85)
            dc = rng.uniform(0.15, 0.85)
            for _m in range(rng.randint(3, 6)):
                u = uc0 + rng.uniform(-0.06, 0.06) * (420 / max(200, span))
                x = k.x0 + u * span
                ymax = H - 6
                bwu = k.band_w(u)
                depth = rng.uniform(0.2, 1.1) * max(bwu * 0.6, (dc + rng.uniform(-0.15, 0.15)) * k.h)
                y = k.y(x) + max(2.0, depth)
                if y > ymax or (k.shared is False and not (ZONE + 6 < x < W - ZONE - 6)):
                    continue
                L = rng.uniform(*st['mlen'])
                slope = (k.y(x + 4) - k.y(x - 4)) / 8 * 0.6 + rng.uniform(-0.1, 0.1)
                bend = rng.uniform(-1.6, 1.6)
                c = [(x + L * t, y + slope * L * t + bend * _s(math.pi * t)) for t in (0, 0.2, 0.45, 0.7, 1)]
                head = rng.random() < 0.6
                ww = [0.5, 1.0, 0.85, 0.55, 0.15] if head else [0.2, 0.8, 1.0, 0.8, 0.2]
                ww = [w * st['mw'] * rng.uniform(0.8, 1.15) for w in ww]
                on_band = depth < bwu * 0.95
                in_shadow = depth > k.term_depth(u)
                if on_band:
                    g.append(f'<path d="{stroke(c, ww, step=1)}" fill="{st["dry"]}" opacity="0.6"/>')
                elif in_shadow:
                    g.append(f'<path d="{stroke(c, ww, step=1)}" fill="{st["deep"]}" opacity="0.85"/>')
                else:
                    g.append(f'<path d="{stroke(c, ww, step=1)}" fill="{st["shadow"]}"/>')
        g.append('</g>')
        out.append(''.join(g))

    def nodule(self, nd, out):
        st = nd.st
        cx, w, h, by = nd.cx, nd.w, nd.h, nd.by
        # cast cel shadow on the parent (lower right), clipped to the parent
        pc = self.clip(nd.parent.shape_d())
        ccx, ccy, rx, ry = cx + w * 0.14, by + h * 0.3, w * 0.6, h * 0.42
        d = (f"M{fmt(ccx - rx)} {fmt(ccy)}C{fmt(ccx - rx)} {fmt(ccy - ry * 1.3)} {fmt(ccx + rx)} {fmt(ccy - ry * 1.3)} {fmt(ccx + rx)} {fmt(ccy)}"
             f"C{fmt(ccx + rx)} {fmt(ccy + ry * 1.25)} {fmt(ccx - rx)} {fmt(ccy + ry * 1.25)} {fmt(ccx - rx)} {fmt(ccy)}Z")
        out.append(f'<path d="{d}" fill="{st["shadow"]}" clip-path="url(#{pc})"/>')
        sd = nd.shape_d()
        cid = self.clip(sd)
        g = [f'<g clip-path="url(#{cid})">', f'<path d="{sd}" fill="{st["lit"]}"/>']
        top = nd.topc
        bw = [h * 0.32 * window(i / 24, 0.0, 0.25, 0.6, 0.9) for i in range(25)]
        g.append(f'<path d="{ribbon(top, bw, [2.0] * 25, step=2)}" fill="{st["crest"]}"/>')
        rim = [(p[0], p[1] + 1.3) for p in top[3:14]]
        g.append(f'<path d="{stroke(rim, [st["rimw"] * 0.8 * _s(math.pi * i / 10) for i in range(11)], step=1)}" fill="{st["dry"]}" opacity="0.9"/>')
        und = []
        for sg in smooth_segs(nd.under):
            for i in range(6):
                und.append(bez(*sg, i / 6))
        sh = [(p[0], p[1] - h * 0.18) for p in und]
        g.append(f'<path d="{stroke(sh, [h * 0.36] * len(sh), step=2)}" fill="{st["shadow"]}"/>')
        g.append('</g>')
        out.append(''.join(g))
        n = len(und)
        ww = [st['inkw'] * 0.8 * (1.0 - 0.9 * smoothstep(0.45, 1.0, i / (n - 1))) * min(1, i / 4 + 0.25) for i in range(n)]
        out.append(f'<path d="{stroke(und, ww, step=2)}" fill="{st["ink"]}"/>')


# ----------------------------------------------------------------------------- scene assembly
def make_ridge(spec, seed, dx=0.0, shared=False, xmin=None, xmax=None):
    _, key, row, xc, yc, al, ar, hl, hr = spec[:9]
    opts = dict(spec[9]) if len(spec) > 9 else {}
    for lk in ('lim_l', 'lim_r'):
        if opts.get(lk) is not None:
            opts[lk] += dx
    if 'lobes' in opts:
        opts['lobes'] = tuple(opts['lobes'])
    s = sum(ord(c) * (i + 5) for i, c in enumerate(key)) + seed * 131
    return Ridge(key, row, xc + dx, yc, al, ar, hl, hr, seed=s, shared=shared, xmin=xmin, xmax=xmax, **opts)


def paint_sequence(painter, ridges):
    """Paint ridges in order; returns a list of svg fragments (one string per ridge)."""
    frags = []
    for i, k in enumerate(ridges):
        out = []
        prev = ridges[:i]
        prof = painter.crease_profile(k, prev)
        painter.trough(k, prof, out)
        painter.ridge(k, out)
        painter.crease(k, prof, out)
        frags.append(''.join(out))
    return frags


def build_seam(layouts_mod):
    """The shared seam stack, painted once in seam coordinates (border at x=0)."""
    pt = Painter('s')
    ridges = [make_ridge(sp, 5, shared=True) for sp in layouts_mod.SEAM]
    frags = paint_sequence(pt, ridges)
    nods = []
    for spec in getattr(layouts_mod, 'SEAM_NODULES', []):
        _, parent, cx, w, h, depth = spec
        par = next(r for r in ridges if r.key == parent)
        nd = Nodule(par, cx, w, h, depth)
        o = []
        pt.nodule(nd, o)
        nods.append((parent, ''.join(o)))
    return ridges, frags, pt.defs, nods


def flat_runs(xs, ys, win=40, tol=2.0):
    """Runs where the contour stays within a tol px band (|dy| < tol) for more than win px. Each run is
    classified: 'shelf' = flat AND straight (it never bows more than 0.35 px away from its chord - the old
    y=120 seam trench, or any plain-base stretch); 'curved' = a rounded dune crest / gentle shoulder.
    Shelves are rejected by build()."""
    bad = []
    n = len(xs)
    i = 0
    while i < n:
        j = i
        lo = hi = ys[i]
        while j + 1 < n:
            lo2, hi2 = min(lo, ys[j + 1]), max(hi, ys[j + 1])
            if hi2 - lo2 >= tol:
                break
            lo, hi = lo2, hi2
            j += 1
        if xs[j] - xs[i] > win:
            x0, y0, x1, y1 = xs[i], ys[i], xs[j], ys[j]
            dev = max(abs(ys[q] - (y0 + (y1 - y0) * (xs[q] - x0) / (x1 - x0))) for q in range(i, j + 1))
            bad.append(('curved' if dev > 0.35 else 'shelf', round(xs[i]), round(xs[j]), round(xs[j] - xs[i])))
        i = j + 1 if j > i else i + 1
    return bad


def build(name, layout, seam, layouts_mod):
    seed = layout.get('seed', 1)
    s_ridges, s_frags, s_defs, s_nods = seam
    s_keys = [r.key for r in s_ridges]
    # instantiate draw list: shared copies at x=0 and x=W, variant ridges clipped to [ZONE, W-ZONE]
    items = []          # (kind, obj) in draw order; kind: 'S' (shared copy), 'V' (variant), 'N' (nodule)
    allr = []           # every ridge in draw order (for occlusion)
    bykey = {}
    for spec in layout['items']:
        if spec[0] == 'S':
            idx = s_keys.index(spec[1])
            sp = layouts_mod.SEAM[idx]
            for dx in (0.0, float(W)):
                r = make_ridge(sp, 5, dx=dx, shared=True)
                items.append(('S', (r, idx, dx)))
                allr.append(r)
        elif spec[0] == 'r':
            r = make_ridge(spec, seed, xmin=ZONE, xmax=W - ZONE)
            items.append(('V', r))
            allr.append(r)
            bykey[r.key] = r
        elif spec[0] == 'n':
            _, parent, cx, w, h, depth = spec
            items.append(('N', Nodule(bykey[parent], cx, w, h, depth, seed=int(cx) * 7 + seed)))

    pt = Painter('k')
    order = []          # list of ('shared', svg) / ('variant', svg)
    warn = []
    ri = 0
    for kind, obj in items:
        if kind == 'S':
            r, idx, dx = obj
            order.append(('shared', f'<g transform="translate({fmt(dx)} 0)">{s_frags[idx]}</g>'))
            for (pk, frag) in s_nods:
                if pk == r.key:
                    order.append(('shared', f'<g transform="translate({fmt(dx)} 0)">{frag}</g>'))
            # creases / troughs of this shared ridge against VARIANT dunes behind it (outside the zone)
            prev_v = [q for q in allr[:ri] if not q.shared]
            if prev_v:
                prof = pt.crease_profile(r, prev_v)
                # a shared dune right above it wins: those creases are already in the shared fragment
                prev_all = allr[:ri]
                prof2 = pt.crease_profile(r, prev_all)
                prof = [a if (b[3] is not None and not b[3].shared) else (a[0], a[1], a[2], None, 0.0)
                        for a, b in zip(prof, prof2)]
                o = []
                pt.trough(r, prof, o)
                pt.crease(r, prof, o)
                if o:
                    order.append(('variant', ''.join(o)))
            ri += 1
        elif kind == 'V':
            r = obj
            prev = allr[:ri]
            prof = pt.crease_profile(r, prev)
            o = []
            pt.trough(r, prof, o)
            pt.ridge(r, o)
            pt.crease(r, prof, o)
            order.append(('variant', ''.join(o)))
            # zone rule: inside the shared zone this dune must be hidden by shared dunes drawn later
            later_shared = [q for q in allr[ri + 1:] if q.shared]
            for p in r.dense:
                if p[1] >= H:
                    continue
                xi = int(round(p[0]))
                if ZONE - 40 <= xi < ZONE or W - ZONE < xi <= W - ZONE + 40:
                    env = min([q.top[xi] for q in later_shared if xi in q.top] or [1e9])
                    if p[1] < env - 0.5:
                        warn.append(('zone', r.key, xi, round(p[1]), round(env)))
                        break
            ri += 1
        else:
            o = []
            pt.nodule(obj, o)
            order.append(('variant', ''.join(o)))

    # silhouette = min of every visible ridge contour (variants only inside their clip)
    sil = []
    src = []
    for xi in range(0, W + 1):
        y, who = BOTTOM, None
        for r in allr:
            t = r.top.get(xi)
            if t is not None and t < y:
                y, who = t, r.key
        sil.append((float(xi), y))
        src.append(who)
    ys = [y for x, y in sil]
    if any(w is None for w in src):
        warn.append(('hole', sum(1 for w in src if w is None)))
    if abs(sil[0][1] - SEAM_Y) > 0.3 or abs(sil[-1][1] - SEAM_Y) > 0.3:
        warn.append(('border-y', round(sil[0][1], 2), round(sil[-1][1], 2)))
    fr = flat_runs([x for x, y in sil], ys)
    # visible contour flat runs (each ridge where it is not covered by a later one)
    vis_flat = []
    for i, r in enumerate(allr):
        later = allr[i + 1:]
        xs_, ys_ = [], []
        for xi in sorted(r.top):
            if not (0 <= xi <= W):
                continue
            y = r.top[xi]
            if y > H:
                continue
            if any((xi in q.top and q.top[xi] <= y + 0.5) for q in later):
                if len(xs_) > 1:
                    vis_flat += [(r.key,) + b for b in flat_runs(xs_, ys_)]
                xs_, ys_ = [], []
                continue
            xs_.append(xi)
            ys_.append(y)
        if len(xs_) > 1:
            vis_flat += [(r.key,) + b for b in flat_runs(xs_, ys_)]
    shelves = [f for f in fr if f[0] == 'shelf'] + [f for f in vis_flat if f[1] == 'shelf']
    if shelves:
        warn.append(('flat-shelf', shelves[:6]))
    stats = dict(sil_min=round(min(ys), 1), sil_max=round(max(ys), 1), sil_mean=round(sum(ys) / len(ys), 1),
                 sil_longest_flat_run=max([f[3] for f in fr] or [0]), warn=warn[:10])

    # three separate pieces split exactly on the integer zone borders: the two shared-zone pieces are the
    # same path data in every variant, so they rasterise identically (no AA dependence on the middle)
    def piece(x0, x1):
        pts = [p for p in sil if x0 <= p[0] <= x1]
        return 'M' + 'L'.join(f"{fmt(x)} {fmt(y)}" for x, y in pts) + f"L{x1} {H + 1}L{x0} {H + 1}Z"
    sil_parts = [piece(0, ZONE), piece(ZONE, W - ZONE), piece(W - ZONE, W)]

    # merge consecutive variant fragments into clipped groups (keeps global painter order)
    groups = []
    cur = []
    for kind, svg in order:
        if kind == 'variant':
            cur.append(svg)
        else:
            if cur:
                groups.append(f'<g clip-path="url(#zoneClip)">{"".join(cur)}</g>')
                cur = []
            groups.append(svg)
    if cur:
        groups.append(f'<g clip-path="url(#zoneClip)">{"".join(cur)}</g>')

    stops = ''.join(f'<stop offset="{o}" stop-color="{c}"/>' for o, c in BASE_STOPS)
    defs = [
        f'<linearGradient id="base" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="0" y2="{H}">{stops}</linearGradient>',
        '''<filter id="grain" x="0" y="0" width="100%" height="100%" filterUnits="userSpaceOnUse">
    <feTurbulence type="fractalNoise" baseFrequency="0.9 0.6" numOctaves="2" seed="7" stitchTiles="stitch" result="n"/>
    <feColorMatrix in="n" type="matrix" values="0 0 0 0 0.35  0 0 0 0 0.06  0 0 0 0 0.08  0 0 0 0.10 0"/>
    <feComposite in2="SourceGraphic" operator="in"/>
  </filter>
  <filter id="mottle" x="0" y="0" width="100%" height="100%" filterUnits="userSpaceOnUse">
    <feTurbulence type="fractalNoise" baseFrequency="0.008 0.02" numOctaves="3" seed="3" stitchTiles="stitch" result="n"/>
    <feColorMatrix in="n" type="matrix" values="''' + MOTTLE + '''"/>
    <feComposite in2="SourceGraphic" operator="in"/>
  </filter>''',
        ''.join(f'<path id="sil{i}" d="{d}"/>' for i, d in enumerate(sil_parts)),
        f'<clipPath id="zoneClip"><rect x="{ZONE}" y="-100" width="{W - 2 * ZONE}" height="{H + 200}"/></clipPath>',
    ] + s_defs + pt.defs

    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">\n'
           '<defs>\n' + '\n'.join(defs) + '\n</defs>\n'
           '<g fill="url(#base)"><use href="#sil0"/><use href="#sil1"/><use href="#sil2"/></g>\n'
           '<g>\n' + '\n'.join(groups) + '\n</g>\n'
           '<g fill="#000" filter="url(#mottle)"><use href="#sil0"/><use href="#sil1"/><use href="#sil2"/></g>\n'
           '<g fill="#000" filter="url(#grain)"><use href="#sil0"/><use href="#sil1"/><use href="#sil2"/></g>\n'
           '</svg>\n')
    return svg, stats


def main(argv):
    sys.dont_write_bytecode = True
    sys.path.insert(0, HERE)
    import layouts as L
    args = [a for a in argv if not a.startswith('--')]
    outdir = args[0] if args else DEFAULT_OUT
    which = args[1:] or list(L.LAYOUTS)
    seam = build_seam(L)
    for nm in which:
        svg, stats = build(nm, L.LAYOUTS[nm], seam, L)
        path = os.path.join(outdir, f"floor_{nm}.svg")
        with open(path, 'w') as f:
            f.write(svg)
        print(path, round(len(svg) / 1024), 'KB', stats)


if __name__ == '__main__':
    main(sys.argv[1:])
