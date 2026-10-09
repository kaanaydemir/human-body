#!/usr/bin/env python3
"""Generator for the far tunnel interior (layer 1, scroll 0.12): far_a.svg / far_b.svg.

Each 1920x1080 segment shows two receding tunnel openings (panel 4/5 of reference.png):
a few fat ring folds drawn as arches (round top, legs standing on a receding floor wedge),
band widths compressing towards a hard-edged dark arch-shaped hole. The outer folds of the
two openings meet in one shared fold with a single crease. Every tile border carries the
same seam fold (identical in all variants), so a seam reads as one more fold.

Run from the repo root:  python3 -I tools/art/far/gen_far.py [out_dir]
(default out_dir: public/assets/svg/environment). Output is deterministic (seeded).
"""
import math
import os
import random
import sys

W, H = 1920, 1080
MARGIN = 48          # tiling contract: only base + shared seam features within 48 px of a border
FADE_END = 64        # features fade in between 48 and 64 px
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
OUT_DIR = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'public', 'assets', 'svg', 'environment')

# ----------------------------------------------------------------------------- palette
# base gradient (shared by every variant; vertical only)
BASE_STOPS = [('0', '#84202d'), ('0.5', '#9a2832'), ('1', '#701a28')]
LINE = '#6e1a24'          # environment outline
RIM_HI = '#e7a99e'        # pale rim core (used sparingly)
LIP = '#e0505a'           # lit lip crescent
CEL = '#93201e'           # cel shadow
CREASE = '#771d26'        # crease gaps
CREASE_CORE = '#571522'   # darkest crease line
HAZE = '#cc4c4e'          # warm, saturated distance haze
POOL0, POOL1 = '#f06a50', '#e05a48'
HOLE_STOPS = [('0', '#5a1520'), ('0.6', '#6c1b26'), ('1', '#771e29')]
HOLE_CORE = '#4e141d'   # hue -9 deg like the reference holes (V .31)
HOLE_CELL = '#7a2a30'
FLOOR_NEAR, FLOOR_FAR = '#b0353c', '#8e2f38'   # used saturation-compensated via sat()
SEAM_BAND = '#b42c35'


# ----------------------------------------------------------------------------- helpers

def lerp(a, b, t):
    return a + (b - a) * t


def clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, v))


def smooth(t):
    t = clamp(t)
    return t * t * (3 - 2 * t)


def h2r(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def r2h(c):
    return '#%02x%02x%02x' % tuple(max(0, min(255, round(v))) for v in c)


def mix(a, b, t):
    ca, cb = h2r(a), h2r(b)
    return r2h(tuple(lerp(ca[i], cb[i], t) for i in range(3)))


def sat(hx, ds=0.065):
    """raise HSV saturation by ds (keeps hue and value): pre-compensates the mottle/grain veil"""
    import colorsys
    r, g, b = [c / 255.0 for c in h2r(hx)]
    hh, ss, vv = colorsys.rgb_to_hsv(r, g, b)
    r, g, b = colorsys.hsv_to_rgb(hh, clamp(ss + ds), vv)
    return r2h((r * 255, g * 255, b * 255))


def val(hx):
    return max(h2r(hx)) / 255.0


def darker(a, b):
    return a if val(a) <= val(b) else b


def f(v):
    s = '%.1f' % v
    if s.endswith('.0'):
        s = s[:-2]
    if s == '-0':
        s = '0'
    return s


def op_s(op):
    return ('%.2f' % op).rstrip('0').rstrip('.')


def closed_path(pts):
    """Closed Catmull-Rom spline through pts -> cubic Bezier path data."""
    n = len(pts)
    out = ['M%s %s' % (f(pts[0][0]), f(pts[0][1]))]
    for i in range(n):
        p0 = pts[(i - 1) % n]
        p1 = pts[i]
        p2 = pts[(i + 1) % n]
        p3 = pts[(i + 2) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6.0, p1[1] + (p2[1] - p0[1]) / 6.0)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6.0, p2[1] - (p3[1] - p1[1]) / 6.0)
        out.append('C%s %s %s %s %s %s' % (f(c1[0]), f(c1[1]), f(c2[0]), f(c2[1]), f(p2[0]), f(p2[1])))
    out.append('Z')
    return ''.join(out)


def poly_path(pts):
    return 'M' + 'L'.join('%s %s' % (f(x), f(y)) for (x, y) in pts) + 'Z'


def taper(pts, prof, straight=False):
    """Brush stroke: filled outline around polyline pts with width prof(t)."""
    m = len(pts)
    if m < 2:
        return None
    L, R = [], []
    for j in range(m):
        p = pts[j]
        a = pts[max(j - 1, 0)]
        b = pts[min(j + 1, m - 1)]
        tx, ty = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(tx, ty) or 1.0
        nx, ny = -ty / ln, tx / ln
        w = prof(j / (m - 1)) / 2.0
        L.append((p[0] + nx * w, p[1] + ny * w))
        R.append((p[0] - nx * w, p[1] - ny * w))
    if straight:
        poly = L + R[::-1][1:-1] if m > 2 else L + R[::-1]
        return poly_path(poly)
    return closed_path(L + R[::-1])


def bell(wmax, wmin=0.0, pw=0.8, skew=0.5):
    def prof(t):
        u = t / skew * 0.5 if t < skew else 0.5 + (t - skew) / (1 - skew) * 0.5
        return wmin + (wmax - wmin) * (math.sin(math.pi * u) ** pw)
    return prof


def norm(v):
    l = math.hypot(*v)
    return (v[0] / l, v[1] / l)


def sp(v, e):
    """signed power (superellipse helper)"""
    return math.copysign(abs(v) ** e, v)


class Svg:
    def __init__(self):
        self.parts = []

    def add(self, s):
        self.parts.append(s)

    def path(self, d, fill, op=1.0, extra=''):
        if d is None:
            return
        o = '' if op >= 0.999 else ' fill-opacity="%s"' % op_s(op)
        self.parts.append('<path d="%s" fill="%s"%s%s/>' % (d, fill, o, extra))


# ----------------------------------------------------------------------------- tunnel opening
#
# Contours i = 0..n-1 are the outer edges of the n ring bands (0 = outermost / nearest),
# contour n is the hole. Each contour is an arch: superellipse top above its springline ys,
# legs that flare slightly and stand on the floor at y = B.  Parameter phi:
#   phi in [pi/2, pi]    left leg  (pi/2 = floor contact, pi = springline)
#   phi in [pi, 2 pi]    arch top
#   phi in [2 pi, 5pi/2] right leg (5pi/2 = floor contact)
# so cos/sin(phi) double as a lighting direction (legs count as the lower quadrants).

PHI0, PHI1 = 0.5 * math.pi, 2.5 * math.pi


class Opening:
    def __init__(self, cfg, rng):
        self.cfg = cfg
        self.rng = rng
        vx, vy = cfg['V']
        self.V = (vx, vy)
        self.n = n = len(cfg['bands'])
        self.light = norm(cfg.get('light', (-0.62, -0.5)))
        self.pe = 2.0 / cfg.get('pexp', 2.25)
        hw, ht, hf = cfg['hole_w'], cfg['hole_top'], cfg['hole_floor']
        slope = cfg.get('floor_slope', 0.78)
        dx, dy = cfg['drift']
        # hand-feel: band widths not perfectly regular
        bands = [b * rng.uniform(0.93, 1.07) for b in cfg['bands']]
        self.gaps = list(cfg['gaps'])
        self.outer_gap = cfg.get('outer_gap', 14)
        X = [0.0] * (n + 1)
        T = [0.0] * (n + 1)
        X[n] = hw
        T[n] = ht
        # vertical band heights: inner folds rounder, outer folds flatter (so the whole arch set
        # fits the y 300..720 window the game shows of this layer)
        v_in, v_out = cfg.get('vr', (0.78, 0.45))
        for i in range(n - 1, -1, -1):
            X[i] = X[i + 1] + self.gaps[i] + bands[i]
            vf = lerp(v_out, v_in, i / float(max(1, n - 1)))
            T[i] = T[i + 1] + vf * (self.gaps[i] + bands[i])
        self.X = X
        self.T = T
        self.cx, self.ys, self.B, self.fl = [], [], [], []
        dmax = X[0] - hw
        if 'anchor' in cfg:
            # place the opening so that its outermost fold's outer edge sits at a given x
            side, ax = cfg['anchor']
            vx = (ax + X[0] if side == 'left' else ax - X[0]) - dx * dmax
            self.V = (vx, vy)
        yf = vy + hf
        self.yf = yf
        for i in range(n + 1):
            d = X[i] - hw
            u = d / dmax
            # the tunnel bends: centre drift grows faster near the hole
            dd = dmax * (u ** 0.8)
            self.cx.append(vx + dx * dd)
            self.ys.append(vy + dy * dd)
            self.B.append(yf + slope * d)
            self.fl.append(0.0 if i == n else cfg.get('flare', 0.14) * (0.6 + 0.4 * u))
        # wobble harmonics (correlated between neighbouring folds)
        self.harm = [(a * rng.uniform(0.7, 1.2), k, rng.uniform(0, 6.283), rng.uniform(-0.35, 0.35))
                     for (k, a) in ((2, 0.016), (3, 0.011), (5, 0.005))]
        self.lean0 = cfg.get('lean', 0.0)
        self.leans = [self.lean0 + rng.uniform(-0.012, 0.012) for _ in range(n + 1)]
        self.dents = {}
        for i in range(n + 1):
            self.dents[i] = [(rng.uniform(PHI0, PHI1), rng.uniform(0.25, 0.5), rng.uniform(-0.016, 0.02))
                             for _ in range(rng.randint(1, 2))]

    # -- geometry
    def wob(self, i, phi):
        w = 0.0
        for (a, k, ph, dp) in self.harm:
            w += a * math.sin(k * phi + ph + i * dp)
        for (pc, wd, amp) in self.dents.get(i, []):
            d = phi - pc
            w += amp * math.exp(-(d / wd) ** 2)
        if i == self.n:
            w *= 0.5
        return w

    def pt(self, i, phi, e=0.0):
        X, T, cx, ys, B, fl = self.X[i], self.T[i], self.cx[i], self.ys[i], self.B[i], self.fl[i]
        w = self.wob(i, phi)
        if phi < math.pi:          # left leg
            fr = (math.pi - phi) / (0.5 * math.pi)
            y = ys + fr * (B - ys)
            x = cx - (X * (1 + w) * (1 + fl * fr * fr) + e)
            return (x, y)
        if phi > 2 * math.pi:      # right leg
            fr = (phi - 2 * math.pi) / (0.5 * math.pi)
            y = ys + fr * (B - ys)
            x = cx + (X * (1 + w) * (1 + fl * fr * fr) + e)
            return (x, y)
        c, s = math.cos(phi), math.sin(phi)
        y = ys + (T * (1 + w) + e) * sp(s, self.pe)
        x = cx + (X * (1 + w) + e) * sp(c, self.pe) + self.leans[i] * (ys - y)
        return (x, y)

    def ext_phi(self, i, extra):
        """phi beyond the floor contact so that the leg reaches extra px below B"""
        leg = max(10.0, self.B[i] - self.ys[i])
        return 0.5 * math.pi * (1 + extra / leg)

    def contour(self, i, e=0.0, extra=70.0, step=11.0):
        """closed outline: legs extend `extra` px below the floor contact and are closed underneath
        (that part is always covered by the floor wedge or the hole floor)."""
        a = self.ext_phi(i, extra)
        lo, hi = math.pi - a, 2 * math.pi + a
        per = 2 * (self.B[i] - self.ys[i] + extra) + math.pi * (self.X[i] + self.T[i]) * 0.5
        m = int(clamp(per / step, 24, 220))
        pts = [self.pt(i, lo + (hi - lo) * j / (m - 1), e) for j in range(m)]
        # flat bottom with a couple of intermediate points (keeps the spline from overshooting)
        (x1, y1), (x0, y0) = pts[-1], pts[0]
        yb = max(y0, y1)
        pts.append((lerp(x1, x0, 0.33), yb))
        pts.append((lerp(x1, x0, 0.66), yb))
        return pts

    def band_pt(self, i, phi, t):
        """point inside band i (t=0 outer edge, t=1 lip = inner edge next to the crease)"""
        p0 = self.pt(i, phi)
        p1 = self.pt(i + 1, phi, self.gaps[i])
        return (lerp(p0[0], p1[0], t), lerp(p0[1], p1[1], t))

    def band_w(self, i, phi):
        p0 = self.pt(i, phi)
        p1 = self.pt(i + 1, phi, self.gaps[i])
        return math.hypot(p1[0] - p0[0], p1[1] - p0[1])

    def speed(self, i, phi):
        a = self.pt(i, phi - 0.01)
        b = self.pt(i, phi + 0.01)
        return math.hypot(b[0] - a[0], b[1] - a[1]) / 0.02

    def lightness(self, phi):
        lx, ly = self.light
        return 0.5 + 0.5 * (math.cos(phi) * lx + math.sin(phi) * ly)

    def visible_phi(self, phi):
        return PHI0 - 0.05 <= phi <= PHI1 + 0.05


def band_colors(u):
    """u: 0 = outermost (nearest) band .. 1 = deepest band next to the hole."""
    body = sat(mix('#b4303a', '#8e2531', u))
    return dict(
        body=body,
        valley=sat(mix(body, HOLE_CORE, lerp(0.62, 0.70, u))),
        hi=sat(mix('#d8404a', '#a62e39', u)),
        hi_op=1.0,
        hi2=sat(mix('#ec5c66', '#c03a44', u), 0.02),
        lip=mix(LIP, '#b23844', u * 0.85),
        lip_w=lerp(5.0, 3.0, u),
        rim_op=lerp(0.8, 0.2, u),
        cel=darker(CEL, mix(body, HOLE_CORE, 0.30)) if u < 0.4 else sat(mix(body, HOLE_CORE, 0.36)),
        crease=mix(CREASE, '#5a1622', 0.25 + 0.75 * u),
        core=mix(CREASE_CORE, HOLE_CORE, u),
        line=mix(LINE, CREASE_CORE, u),
        streak_hi=sat(mix('#cc3a43', '#8e2a36', u)),
        streak_lo=sat(mix('#7a1c27', '#561522', u)),
        streak_op=lerp(0.45, 0.25, u),
        fleck_op=lerp(0.20, 0.06, u),
    )


# ----------------------------------------------------------------------------- drawing

def phi_range_strokes(op, i, lo, hi, rng, min_len=0.25, max_len=0.9, gap=(0.06, 0.25)):
    """split [lo, hi] into broken stroke segments (radians)"""
    segs = []
    th = lo + rng.uniform(0.0, 0.12)
    while th < hi:
        ln = rng.uniform(min_len, max_len)
        segs.append((th, min(th + ln, hi)))
        th += ln + rng.uniform(*gap)
    return segs


def crescent(op, i, phis, t_of, t_edge=1.04):
    """closed shape inside band i between t=t_of(phi) and t=t_edge (lip side)"""
    outer = [op.band_pt(i, p, t_of(p)) for p in phis]
    inner = [op.band_pt(i, p, t_edge) for p in phis[::-1]]
    return closed_path(outer + inner)


def zone(op, i, phis, t0, t1):
    """closed shape inside band i between t0(phi) and t1(phi)"""
    a = [op.band_pt(i, p, t0(p)) for p in phis]
    b = [op.band_pt(i, p, t1(p)) for p in phis[::-1]]
    return closed_path(a + b)


def draw_band(svg, op, i, col, rng):
    """decorate band i (body already filled): highlight, cel shadow, lip, crease line, texture"""
    n = op.n
    lth = math.atan2(op.light[1], op.light[0]) % (2 * math.pi)   # lit direction (upper-left)
    m = 90
    allp = [PHI0 + (PHI1 - PHI0) * j / (m - 1) for j in range(m)]
    ph_v = rng.uniform(0, 6.28)
    # 1) valley shade: the outer part of every fold sits in the shadow of the fold in front of it
    #    (two flat cel steps, dark next to the crease)
    svg.path(zone(op, i, allp, lambda p: -0.03,
                  lambda p: 0.24 + 0.06 * math.sin(3 * p + ph_v) + 0.10 * (1 - op.lightness(p))), col['valley'])
    svg.path(zone(op, i, allp, lambda p: 0.2,
                  lambda p: 0.40 + 0.06 * math.sin(2 * p + ph_v) + 0.12 * (1 - op.lightness(p))),
             col['valley'], 0.45)
    # 2) lit face: towards the lip on the lit (upper-left) side the fold turns to the light
    lit = [p for p in allp if op.lightness(p) > 0.38]
    if len(lit) > 3:
        svg.path(zone(op, i, lit, lambda p: 1.0 - 0.60 * smooth((op.lightness(p) - 0.38) / 0.32), lambda p: 1.03),
                 col['hi'], col['hi_op'])
    # one soft highlight streak across the most lit part
    c = lth + rng.uniform(-0.15, 0.15)
    span = 0.85
    phis = [c - span + 2 * span * j / 29 for j in range(30)]
    phis = [p for p in phis if op.visible_phi(p)]
    if len(phis) > 4:
        pts = [op.band_pt(i, p, 0.70 + 0.04 * math.sin(j * 0.4 + i)) for j, p in enumerate(phis)]
        bw = op.band_w(i, c)
        svg.path(taper(pts, bell(bw * 0.26, 0.0, 0.9, rng.uniform(0.42, 0.58))), col['hi2'], 0.9)
    # 3) opaque cel shadow on the lower-right inner side (cast by the fold onto itself)
    m = 70
    phis = [PHI0 + (PHI1 - PHI0) * j / (m - 1) for j in range(m)]
    sh = [p for p in phis if op.lightness(p) < 0.40]
    if len(sh) > 3:
        def t_of(p):
            s = smooth((0.40 - op.lightness(p)) / 0.22)
            bw = op.band_w(i, p)
            return 1.0 - clamp(0.48 * s + 2.0 / max(bw, 1.0), 0.0, 0.62)
        svg.path(crescent(op, i, sh, t_of), col['cel'])
    # 4) 3 px crease line on the shadow side only, along the lip
    for (a0, a1) in phi_range_strokes(op, i, PHI0, PHI1, rng, 0.5, 1.4, (0.04, 0.12)):
        mm = max(6, int((a1 - a0) * 18))
        ps = [a0 + (a1 - a0) * j / (mm - 1) for j in range(mm)]
        if max(1.0 - op.lightness(p) for p in ps) < 0.55:
            continue
        pts = [op.band_pt(i, p, 1.0 - 1.6 / max(op.band_w(i, p), 4.0)) for p in ps]

        def prof(t, ps=ps):
            s = smooth((0.62 - op.lightness(ps[min(len(ps) - 1, int(t * (len(ps) - 1)))])) / 0.3)
            return 3.2 * s * (math.sin(math.pi * t) ** 0.35)
        svg.path(taper(pts, prof), col['line'], 0.95)
    # 5) lit lip: broken 3-5 px crescents on the upper-left of the inner edge
    lo, hi = lth - 1.45, lth + 1.25
    for (a0, a1) in phi_range_strokes(op, i, max(PHI0, lo), min(PHI1, hi), rng, 0.30, 0.95, (0.05, 0.22)):
        mm = max(6, int((a1 - a0) * 22))
        ps = [a0 + (a1 - a0) * j / (mm - 1) for j in range(mm)]

        def t_lip(p, a0=a0, a1=a1):
            lt = smooth((op.lightness(p) - 0.55) / 0.35)
            env = math.sin(math.pi * clamp((p - a0) / max(a1 - a0, 1e-6))) ** 0.6
            w = col['lip_w'] * (0.35 + 0.65 * lt) * env
            return 1.0 - w / max(op.band_w(i, p), 4.0)
        svg.path(crescent(op, i, ps, t_lip, 1.03), col['lip'])
        # pale core on the most lit bits of the near folds only
        if col['rim_op'] > 0.05 and rng.random() < 0.7:
            core = [p for p in ps if op.lightness(p) > 0.74]
            if len(core) >= 4:
                pts = [op.band_pt(i, p, 1.0 - 1.6 / max(op.band_w(i, p), 4.0)) for p in core]
                svg.path(taper(pts, bell(2.0, 0.0, 0.7)), RIM_HI, col['rim_op'])
    # 6) painterly texture: streaks along the band, hatches in shadow, a few flecks and pores
    draw_texture(svg, op, i, col, rng)


def draw_texture(svg, op, i, col, rng):
    mean_bw = sum(op.band_w(i, PHI0 + (PHI1 - PHI0) * j / 8.0) for j in range(9)) / 9.0
    per = sum(op.speed(i, PHI0 + (PHI1 - PHI0) * (j + 0.5) / 16) for j in range(16)) * (PHI1 - PHI0) / 16
    area = per * mean_bw
    ns = int(area / 2600.0)
    for _ in range(ns):
        p0 = rng.uniform(PHI0, PHI1)
        lit = op.lightness(p0)
        hi = rng.random() < 0.2 + 0.6 * lit
        t = rng.uniform(0.15, 0.55) if hi else rng.uniform(0.45, 0.85)
        L = rng.uniform(26, 90)
        span = L / max(op.speed(i, p0), 1.0)
        m = 7
        drift = rng.uniform(-0.10, 0.10)
        ps = [p0 + span * j / (m - 1) for j in range(m)]
        if not all(op.visible_phi(p) for p in ps):
            continue
        pts = [op.band_pt(i, p, clamp(t + drift * j / (m - 1), 0.08, 0.9)) for j, p in enumerate(ps)]
        w = rng.uniform(2.2, 5.0) * clamp(mean_bw / 60.0, 0.5, 1.2)
        if hi:
            svg.path(taper(pts, bell(w, 0.0, 0.8, rng.uniform(0.3, 0.7)), True), col['streak_hi'],
                     col['streak_op'] * rng.uniform(0.6, 1.1))
        else:
            svg.path(taper(pts, bell(w * 0.8, 0.0, 0.8, rng.uniform(0.3, 0.7)), True), col['streak_lo'],
                     col['streak_op'] * rng.uniform(0.6, 1.0))
    # short dark hatches in little clusters, mostly in shadow
    nh = int(area / 6500.0)
    for _ in range(nh):
        p0 = rng.uniform(PHI0, PHI1)
        if rng.random() > 0.25 + 0.75 * (1.0 - op.lightness(p0)):
            continue
        t = rng.uniform(0.25, 0.8)
        span = rng.uniform(8, 20) / max(op.speed(i, p0), 1.0)
        for c in range(rng.choice((1, 2, 2, 3))):
            tt = clamp(t + c * rng.uniform(0.06, 0.1), 0.05, 0.9)
            pts = [op.band_pt(i, p0 + span * j / 4 + c * 0.01, clamp(tt + 0.05 * math.sin(j + c), 0.04, 0.95))
                   for j in range(5)]
            svg.path(taper(pts, bell(rng.uniform(1.3, 2.4), 0.0, 0.7), True), col['streak_lo'], 0.55)
    # a few pale flecks near the lip on the lit side (sparingly: they desaturate)
    nf = int(area / 30000.0)
    for _ in range(nf):
        p0 = rng.uniform(PHI0, PHI1)
        if op.lightness(p0) < rng.uniform(0.5, 0.9):
            continue
        span = rng.uniform(5, 14) / max(op.speed(i, p0), 1.0)
        t = rng.uniform(0.6, 0.9)
        pts = [op.band_pt(i, p0 + span * j / 3, t + rng.uniform(-0.02, 0.02)) for j in range(4)]
        svg.path(taper(pts, bell(rng.uniform(1.2, 2.0)), True), RIM_HI, col['fleck_op'])
    # pores: tiny dark pits with a lit lower lip
    npo = int(area / 14000.0)
    for _ in range(npo):
        p = rng.uniform(PHI0 + 0.1, PHI1 - 0.1)
        x, y = op.band_pt(i, p, rng.uniform(0.2, 0.7))
        r = rng.uniform(1.5, 3.0)
        pts = [(x + r * 1.4 * math.cos(a) * (1 + 0.15 * math.sin(3 * a)), y + r * math.sin(a))
               for a in [k * math.pi / 4 for k in range(8)]]
        svg.path(closed_path(pts), col['streak_lo'], 0.75)
        lip = [(x + r * 1.4 * math.cos(a) + 0.3 * r, y + r * 0.8 + r * 0.4 * math.sin(a))
               for a in [k * math.pi / 4 for k in range(8)]]
        svg.path(closed_path(lip), col['streak_hi'], 0.7)


def draw_crease(svg, op, i, col, g, rng):
    """crease gap around contour i (width g): dark fill + darkest core on the shadow side"""
    svg.path(closed_path(op.contour(i, e=g)), col['crease'])
    m = 80
    phis = [PHI0 + (PHI1 - PHI0) * j / (m - 1) for j in range(m)]
    sh = [p for p in phis if op.lightness(p) < 0.62]
    if len(sh) < 4:
        return
    pts = [op.pt(i, p, g * 0.5) for p in sh]

    def prof(t):
        p = sh[min(len(sh) - 1, int(t * (len(sh) - 1)))]
        s = smooth((0.62 - op.lightness(p)) / 0.35)
        return max(0.0, g * 0.62 * s) * (math.sin(math.pi * t) ** 0.3)
    svg.path(taper(pts, prof), col['core'])


def draw_wall_fold(svg, op, rng):
    """one broad, low-contrast outer wall fold over the opening; its width tapers to nothing at
    the springline on both sides, so it melts into the outermost crease (no loose ends)."""
    g0 = op.outer_gap
    wdt = op.cfg.get('wall_w', 80.0)
    lo, hi = math.pi - 0.02, 2 * math.pi + 0.02
    m = 64
    ps = [lo + (hi - lo) * j / (m - 1) for j in range(m)]

    def w_of(p):
        u = clamp((p - lo) / (hi - lo))
        return wdt * (math.sin(math.pi * u) ** 0.55)
    outer = [op.pt(0, p, g0 + w_of(p)) for p in ps]
    inner = [op.pt(0, p, g0 - 1) for p in ps[::-1]]
    body = '#962832'
    svg.path(closed_path(outer + inner), body)
    val = [op.pt(0, p, g0 + w_of(p) * 0.55) for p in ps[::-1]]
    svg.path(closed_path(outer + val), mix(body, '#4a1220', 0.30), 0.8)
    lit = [p for p in ps if op.lightness(p) > 0.5]
    if len(lit) > 4:
        a_ = [op.pt(0, p, g0 + w_of(p) * 0.42 * smooth((op.lightness(p) - 0.5) / 0.35)) for p in lit]
        b_ = [op.pt(0, p, g0 - 1) for p in lit[::-1]]
        svg.path(closed_path(a_ + b_), '#ac2e38', 0.9)
        lip = [op.pt(0, p, g0 + 2.5) for p in lit if op.lightness(p) > 0.62]
        if len(lip) > 4:
            svg.path(taper(lip, bell(3.6, 0.0, 0.6)), '#cc444e', 0.9)
    crease = [op.pt(0, p, g0 + w_of(p)) for p in ps]
    svg.path(taper(crease, lambda t: 1.0 + 4.0 * (math.sin(math.pi * t) ** 0.8)), CREASE, 0.9)


def draw_opening(svg, op, rng, gid):
    n = op.n
    # outer crease separating the outermost fold from the wall
    wall_col = band_colors(0.0)
    draw_crease(svg, op, 0, wall_col, op.outer_gap, rng)
    for i in range(n):
        u = i / float(max(1, n - 1)) * 0.9
        col = band_colors(u)
        svg.path(closed_path(op.contour(i)), col['body'])
        draw_band(svg, op, i, col, rng)
        draw_crease(svg, op, i + 1, band_colors(min(1.0, u + 0.15)), op.gaps[i], rng)
    draw_hole(svg, op, rng, gid)


def hole_gradient(op, gid):
    vx, vy = op.V
    hw, ht = op.X[op.n], op.T[op.n]
    cx, cy = op.deep_c
    r = max(hw, ht) * 1.15
    return ('<radialGradient id="%s" gradientUnits="userSpaceOnUse" cx="%s" cy="%s" r="%s" '
            'gradientTransform="translate(%s %s) scale(%s 1) translate(%s %s)">%s</radialGradient>' % (
                gid, f(cx), f(cy), f(r), f(cx), f(cy), '%.3f' % (hw / ht), f(-cx), f(-cy),
                ''.join('<stop offset="%s" stop-color="%s"/>' % s for s in HOLE_STOPS)))


def arch_pts(cx, ys, hw, ht, yb, pe, m=40, wob=None):
    """simple closed arch: superellipse top, straight legs down to yb, flat bottom"""
    pts = []
    for j in range(m):
        phi = math.pi + math.pi * j / (m - 1)
        w = wob(phi) if wob else 0.0
        pts.append((cx + hw * (1 + w) * sp(math.cos(phi), pe), ys + ht * (1 + w) * sp(math.sin(phi), pe)))
    pts.append((cx + hw, lerp(ys, yb, 0.5)))
    pts.append((cx + hw, yb))
    pts.append((cx + hw * 0.33, yb))
    pts.append((cx - hw * 0.33, yb))
    pts.append((cx - hw, yb))
    pts.append((cx - hw, lerp(ys, yb, 0.5)))
    return pts


def draw_hole(svg, op, rng, gid):
    """hard-edged arch hole: gradient second tone, one ghost fold, a dark core window,
    the tunnel floor running into it with a few dim cell silhouettes."""
    n = op.n
    cx, ys, hw, ht, yf = op.cx[n], op.ys[n], op.X[n], op.T[n], op.yf
    svg.path(closed_path(op.contour(n, extra=30.0)), 'url(#%s)' % gid)
    dcx, dcy = op.deep_c
    ddx = dcx - cx
    lx, ly = op.light
    # ghost fold (at most one): faint lip on the upper-left + crease under it
    gs = 0.74
    g_hw, g_ht = hw * gs, ht * gs
    g_cx = cx + ddx * 0.55
    g_ys = ys + (dcy - ys) * 0.55
    g_yb = yf - (yf - ys) * 0.30
    m = 36
    top = [(g_cx + g_hw * sp(math.cos(math.pi + math.pi * j / (m - 1)), op.pe),
            g_ys + g_ht * sp(math.sin(math.pi + math.pi * j / (m - 1)), op.pe)) for j in range(m)]
    left_leg = [(g_cx - g_hw, lerp(g_yb, g_ys, j / 5.0)) for j in range(5)]
    right_leg = [(g_cx + g_hw, lerp(g_ys, g_yb, j / 5.0)) for j in range(1, 6)]
    ghost = left_leg + top + right_leg
    # crease just inside the ghost lip (shadow side heavier)
    def gprof(t):
        idx = min(len(ghost) - 1, int(t * (len(ghost) - 1)))
        x, y = ghost[idx]
        d = norm((x - g_cx + 1e-3, y - g_ys + 1e-3))
        lt = 0.5 + 0.5 * (d[0] * lx + d[1] * ly)
        return (2.0 + 5.0 * (1 - lt)) * (math.sin(math.pi * t) ** 0.4)
    svg.path(taper(ghost, gprof), '#4f1320', 0.85)
    lit = [p for p in ghost[3:-3]
           if 0.5 + 0.5 * (norm((p[0] - g_cx + 1e-3, p[1] - g_ys + 1e-3))[0] * lx +
                           norm((p[0] - g_cx + 1e-3, p[1] - g_ys + 1e-3))[1] * ly) > 0.7]
    if len(lit) > 4:
        lit_out = [(g_cx + (x - g_cx) * 1.04, g_ys + (y - g_ys) * 1.04) for (x, y) in lit]
        svg.path(taper(lit_out, bell(3.0, 0.0, 0.6)), '#8a2834', 0.9)
    # dark core window (hard edged, no blur)
    ds = 0.60
    k_hw, k_ht = hw * ds, ht * ds
    k_yb = yf - (yf - ys) * 0.42
    core = arch_pts(dcx, dcy, k_hw, k_ht, k_yb + 20, op.pe, 30,
                    wob=lambda p: 0.03 * math.sin(3 * p + 1.3))
    svg.path(closed_path(core), HOLE_CORE)
    # the tunnel floor running into the hole (continues the floor wedge, darkening with depth)
    fid = gid + 'f'
    op.defs.append('<linearGradient id="%s" x1="0" y1="%s" x2="0" y2="%s" gradientUnits="userSpaceOnUse">'
                   '<stop offset="0" stop-color="#561522"/><stop offset="1" stop-color="#8a2c36"/>'
                   '</linearGradient>' % (fid, f(k_yb - 4), f(yf)))
    fl = [(cx - hw - 4, yf + 6), (cx - hw - 2, yf - 4),
          (lerp(cx - hw, dcx - k_hw, 0.5) - 3, lerp(yf, k_yb, 0.55)),
          (dcx - k_hw * 0.9, k_yb + 1), (dcx - k_hw * 0.2, k_yb - 3),
          (dcx + k_hw * 0.5, k_yb - 1), (dcx + k_hw * 0.95, k_yb + 2),
          (lerp(cx + hw, dcx + k_hw, 0.5) + 3, lerp(yf, k_yb, 0.5)),
          (cx + hw + 2, yf - 4), (cx + hw + 4, yf + 6)]
    svg.path(closed_path(fl), 'url(#%s)' % fid)
    # 3-5 tiny dim cell silhouettes walking on the hole floor
    ncell = rng.randint(3, 5)
    for c in range(ncell):
        t = (c + rng.uniform(0.2, 0.8)) / ncell
        depth = rng.uniform(0.15, 0.8)                      # 0 = at the hole mouth, 1 = at the core
        y = lerp(yf - 3, k_yb + 2, depth)
        half = lerp(hw * 0.85, k_hw * 0.9, depth)
        x = lerp(lerp(cx, dcx, depth) - half, lerp(cx, dcx, depth) + half, t)
        s = lerp(7.5, 3.5, depth) * rng.uniform(0.85, 1.15)
        body = [(x + s * 0.9 * math.cos(a) * (1 + 0.12 * math.sin(2 * a)), y - s * 1.1 + s * 1.05 * math.sin(a))
                for a in [k * math.pi / 5 for k in range(10)]]
        svg.path(closed_path(body), HOLE_CELL)
        # little legs
        for sx in (-0.35, 0.35):
            svg.path(taper([(x + sx * s, y - 0.2 * s), (x + sx * s * 1.2, y + 0.35 * s)], lambda t_: 1.3, True),
                     HOLE_CELL)
        hl = [(x - s * 0.35 + s * 0.35 * math.cos(a), y - s * 1.55 + s * 0.22 * math.sin(a))
              for a in [k * math.pi / 4 for k in range(8)]]
        svg.path(closed_path(hl), '#8e3238', 0.8)


def floor_edge(op, side):
    """floor/wall junction points (from the hole outward) on one side (-1 left, +1 right):
    the feet of every fold, then the line continued outward."""
    pts = []
    n = op.n
    phi = PHI0 if side < 0 else PHI1
    pts.append((op.cx[n] + side * (op.X[n] + 1), op.yf))
    for i in range(n - 1, -1, -1):
        pts.append(op.pt(i, phi, op.gaps[i] * 0.5))
        pts.append(op.pt(i, phi))
    (x1, y1), (x0, y0) = pts[-1], pts[-3]
    dx, dy = x1 - x0, y1 - y0
    l = math.hypot(dx, dy) or 1.0
    for d in (150, 400, 700):
        pts.append((x1 + dx / l * d, y1 + dy / l * d))
    return pts


def draw_floor(svg, op, rng, gid):
    """receding floor wedge converging into the hole base: the folds stand on it, their bottoms
    continue across it as low ridges, plus 2-3 tiny mounds."""
    n = op.n
    L = floor_edge(op, -1)
    R = floor_edge(op, +1)
    edge = L[::-1] + R
    bottom = max(max(p[1] for p in edge) + 60, H + 40)
    poly = edge + [(R[-1][0], bottom), (lerp(R[-1][0], L[-1][0], 0.5), bottom), (L[-1][0], bottom)]
    op.defs.append('<linearGradient id="%s" x1="0" y1="%s" x2="0" y2="%s" gradientUnits="userSpaceOnUse">'
                   '<stop offset="0" stop-color="%s"/><stop offset="%.3f" stop-color="%s"/>'
                   '<stop offset="1" stop-color="#8e2530"/></linearGradient>'
                   % (gid, f(op.floor_y0), f(H), sat(FLOOR_FAR), 160.0 / (H - op.floor_y0), sat(FLOOR_NEAR)))
    svg.path(closed_path(poly), 'url(#%s)' % gid)
    # light pooling on the middle of the floor in front of the hole
    lid = gid + 'l'
    lx_, ly_ = op.cx[n], op.yf + 85
    op.defs.append('<radialGradient id="%s" gradientUnits="userSpaceOnUse" cx="%s" cy="%s" r="%s" '
                   'gradientTransform="translate(%s %s) scale(1 0.32) translate(%s %s)">'
                   '<stop offset="0" stop-color="%s" stop-opacity="0.55"/>'
                   '<stop offset="0.6" stop-color="%s" stop-opacity="0.22"/>'
                   '<stop offset="1" stop-color="%s" stop-opacity="0"/></radialGradient>'
                   % (lid, f(lx_), f(ly_), f(op.X[0] * 0.62), f(lx_), f(ly_), f(-lx_), f(-ly_),
                      sat('#cc3e46'), sat('#c03a42'), sat('#c03a42')))
    svg.path(closed_path(poly), 'url(#%s)' % lid)
    # the bottom of every fold continues across the floor as a low, soft transverse swell
    # (lit near face only, broken, fading out towards the feet)
    for i in range(n - 1, -1, -1):
        pl = op.pt(i, PHI0)
        pr = op.pt(i, PHI1)
        depth = op.B[i] - op.yf
        if depth < 18:
            continue
        sag = 0.22 * depth + 2.0
        k = clamp(depth / 120.0, 0.25, 1.0)
        t0 = rng.uniform(0.10, 0.22)
        t1 = rng.uniform(0.70, 0.88)
        m = 20
        arc = [(lerp(pl[0], pr[0], t), lerp(pl[1], pr[1], t) + sag * math.sin(math.pi * t) + 2.5 * k)
               for t in [t0 + (t1 - t0) * j / (m - 1) for j in range(m)]]
        svg.path(taper(arc, bell(lerp(3.0, 10.0, k), 0.0, 0.6, rng.uniform(0.35, 0.55))), '#bc3a42', 0.45)
        shade = [(x, y - lerp(3.0, 7.0, k)) for (x, y) in arc]
        svg.path(taper(shade, bell(lerp(1.5, 4.0, k), 0.0, 0.6)), '#7e2230', 0.35)
    # one broad, soft swell nearer to the viewer (the fold in front of this stretch of tunnel)
    pl, pr = op.pt(0, PHI0), op.pt(0, PHI1)
    m = 28
    arc = [(lerp(pl[0] - 120, pr[0] + 120, t), lerp(pl[1], pr[1], t) + 80 + 70 * math.sin(math.pi * t))
           for t in [0.08 + 0.84 * j / (m - 1.0) for j in range(m)]]
    svg.path(taper(arc, bell(18, 0.0, 0.6, rng.uniform(0.4, 0.6))), sat('#c23c44'), 0.35)
    shade = [(x, y - 11) for (x, y) in arc]
    svg.path(taper(shade, bell(8, 0.0, 0.6)), sat('#7a1f2b'), 0.3)
    # the floor is modelled too: lit along the left wall, in the legs' cel shadow along the right
    for side, pts, colr, opc in ((-1, L, sat('#c43c45'), 0.55), (1, R, sat('#7e2030'), 0.6)):
        inner = pts[:-2]
        far_ = [(x - side * lerp(10, 90, clamp((y - op.yf) / 160.0)), y + 4) for (x, y) in inner]
        svg.path(closed_path(inner + far_[::-1]), colr, opc)
    # contact shadow where the folds stand on the floor
    for side, pts in ((-1, L), (1, R)):
        svg.path(taper(pts[:-2], bell(3.4, 1.0, 0.5)), LINE, 0.8)
    # tiny mound bumps on the floor in front of the hole
    for k in range(rng.randint(2, 3)):
        side = -1 if k % 2 == 0 else 1
        depth = rng.uniform(0.3, 0.85)
        y = op.yf + lerp(10, 110, depth)
        span = op.X[n] + (y - op.yf) / max(0.2, op.cfg.get('floor_slope', 0.42)) * 0.9
        cx = op.cx[n] + side * rng.uniform(0.25, 0.75) * span
        w = lerp(14, 34, depth) * rng.uniform(0.8, 1.2)
        h = w * rng.uniform(0.30, 0.40)
        top = [(cx + w * math.cos(a), y - h * math.sin(a) * (1 + 0.1 * math.cos(3 * a)))
               for a in [math.pi * j / 10 for j in range(11)]]
        mound = top + [(cx - w * 0.6, y + 2), (cx + w * 0.6, y + 2)][::-1]
        svg.path(closed_path(mound), mix(FLOOR_NEAR, FLOOR_FAR, 0.7 - 0.6 * depth))
        lit = [(cx + w * 0.9 * math.cos(a), y - h * 0.88 * math.sin(a)) for a in
               [math.pi * (0.45 + 0.5 * j / 6) for j in range(7)]]
        svg.path(taper(lit, bell(2.4, 0.0, 0.7)), '#d0444c', 0.85)
        under = [(cx + w * math.cos(a), y + 1.5 - 0.5 * math.sin(a)) for a in [math.pi * j / 8 for j in range(9)]]
        svg.path(taper(under, bell(2.4, 0.4, 0.5, 0.3)), LINE, 0.7)


def lerp_pt(a, b, t):
    return (lerp(a[0], b[0], t), lerp(a[1], b[1], t))


# ----------------------------------------------------------------------------- shared folds

def fold_line(svg, xs, rng, lip_side=1, lit_y=(0, 620), cel_y=(380, 1140)):
    """a single crease where two folds meet: dark gap + darkest core, a lit lip on one side
    (upper part) and an opaque cel shadow on the other (lower part). xs(y) is the crease centre."""
    ys = [-40 + (H + 80) * j / 60 for j in range(61)]

    def edge(off_fn):
        return [(xs(y) + off_fn(y), y) for y in ys]
    gw = lambda y: 6.0 + 1.5 * math.sin(y / 83.0 + 0.7)
    left = edge(lambda y: -gw(y))
    right = edge(lambda y: gw(y))
    # cel shadow on the non-lip side (lower part)
    cs = -lip_side

    def cel_w(y):
        return 16.0 * smooth((y - cel_y[0]) / 160.0) * (1 - smooth((y - cel_y[1]) / 100.0))
    cel = [(xs(y) + cs * gw(y), y) for y in ys] + [(xs(y) + cs * (gw(y) + cel_w(y)), y) for y in ys[::-1]]
    svg.path(closed_path(cel), CEL)
    svg.path(closed_path(left + right[::-1]), CREASE)
    core = [(xs(y) - 1.6, y) for y in ys] + [(xs(y) + 1.6, y) for y in ys[::-1]]
    svg.path(poly_path(core), CREASE_CORE)

    def lip_w(y):
        return 4.5 * (1 - smooth((y - lit_y[1]) / 180.0)) * (0.7 + 0.3 * math.sin(y / 61.0))
    lip = [(xs(y) + lip_side * gw(y), y) for y in ys] + \
          [(xs(y) + lip_side * (gw(y) + lip_w(y)), y) for y in ys[::-1]]
    svg.path(closed_path(lip), LIP)


SEAM_SEED = 4242


def draw_seam_folds(svg):
    """identical in every variant: half of one fold at each border. The band edges mirror each
    other across the seam, so any two variants side by side form one complete fold."""
    rng = random.Random(SEAM_SEED)
    ys = [-40 + (H + 80) * j / 60 for j in range(61)]

    def bw(y):
        return 30.0 + 4.0 * math.sin(y / 97.0 + 0.4) + 2.5 * math.sin(y / 41.0 + 1.9)
    for X0, sgn in ((0.0, 1.0), (float(W), -1.0)):
        # the band is the edge of one more fold: valley-dark where it meets the wall, lit
        # (tile's left margin) or in cel shadow (tile's right margin) next to the crease
        vw = lambda y: 11.0 + 2.0 * math.sin(y / 63.0 + 1.1)
        outer = [(X0 + sgn * (bw(y) + vw(y)), y) for y in ys]
        band = [(X0, y) for y in ys] + outer[::-1]
        svg.path(closed_path(band), sat(mix(SEAM_BAND, HOLE_CORE, 0.42)))
        band = [(X0, y) for y in ys] + [(X0 + sgn * bw(y), y) for y in ys[::-1]]
        svg.path(closed_path(band), SEAM_BAND)
        mid = [(X0 + sgn * bw(y) * 0.45, y) for y in ys]
        if sgn > 0:
            # lit face of the fold to the right of the seam
            r3 = random.Random(SEAM_SEED + 7)
            y0 = -20.0
            while y0 < H:
                ln = r3.uniform(140, 300)
                seg = [(X0 + sgn * bw(y0 + ln * j / 9) * r3.uniform(0.40, 0.48), y0 + ln * j / 9) for j in range(10)]
                svg.path(taper(seg, bell(r3.uniform(7, 10), 0.0, 0.7)), sat('#d03c46'), 0.85)
                y0 += ln + r3.uniform(30, 90)
        else:
            # shadow side to the left of the seam: cel tone on the inner half, lower part
            cel = [(X0, y) for y in ys if y > 300] + \
                  [(X0 + sgn * bw(y) * 0.55 * smooth((y - 300) / 200.0), y) for y in ys[::-1] if y > 300]
            svg.path(closed_path(cel), CEL, 0.9)
        # a few streaks on the band (same on both sides of every seam)
        r2 = random.Random(SEAM_SEED + int(X0))
        for _ in range(18):
            y0 = r2.uniform(0, H)
            ln = r2.uniform(40, 120)
            t = r2.uniform(0.35, 0.8)
            pts = [(X0 + sgn * bw(y0 + ln * j / 6) * t, y0 + ln * j / 6) for j in range(7)]
            hi = r2.random() < 0.5
            svg.path(taper(pts, bell(r2.uniform(2.0, 3.4)), True), '#c8363f' if hi else '#7e1d28',
                     0.45 if hi else 0.4)
        # outer edge of the fold: thin environment line on the lower (shadow) part
        edge = [(X0 + sgn * (bw(y) + vw(y)), y) for y in ys if y > 380]
        svg.path(taper(edge, bell(2.6, 0.6, 0.4)), LINE, 0.7)
    # the crease itself, centred exactly on the border
    fold_line(svg, lambda y: 0.0, rng, lip_side=1)
    fold_line(svg, lambda y: float(W), rng, lip_side=1)


# ----------------------------------------------------------------------------- whole segment

FILTERS = '''<filter id="grain" x="0" y="0" width="100%" height="100%" filterUnits="userSpaceOnUse">
    <feTurbulence type="fractalNoise" baseFrequency="0.9 0.6" numOctaves="2" seed="7" stitchTiles="stitch" result="n"/>
    <feColorMatrix in="n" type="matrix" values="0 0 0 0 0.35  0 0 0 0 0.06  0 0 0 0 0.08  0 0 0 0.10 0"/>
    <feComposite in2="SourceGraphic" operator="in"/>
  </filter>
  <filter id="mottle" x="0" y="0" width="100%" height="100%" filterUnits="userSpaceOnUse">
    <feTurbulence type="fractalNoise" baseFrequency="0.008 0.02" numOctaves="3" seed="3" stitchTiles="stitch" result="n"/>
    <feColorMatrix in="n" type="matrix" values="0 0 0 0 0.94  0 0 0 0 0.36  0 0 0 0 0.30  0 0 0 0.08 0"/>
    <feComposite in2="SourceGraphic" operator="in"/>
  </filter>'''


def split_fn(cfg, ops):
    """the line where the outermost folds of the two openings meet (a gentle wavy vertical):
    midway between the right edge of the left opening and the left edge of the right one."""
    a, b = ops
    ra = a.cx[0] + a.X[0]
    lb = b.cx[0] - b.X[0]
    X0 = 0.5 * (ra + lb)
    amp, ph = cfg.get('split_wave', (10, 0.6))
    return lambda y: X0 + amp * math.sin(y / 230.0 + ph) + amp * 0.35 * math.sin(y / 89.0 + ph * 1.7)


def build(cfg):
    rng = random.Random(cfg['seed'])
    svg = Svg()
    defs = []
    svg.add('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d">' % (W, H, W, H))
    defs.append('<linearGradient id="base" x1="0" y1="0" x2="0" y2="%d" gradientUnits="userSpaceOnUse">%s</linearGradient>'
                % (H, ''.join('<stop offset="%s" stop-color="%s"/>' % s for s in BASE_STOPS)))
    defs.append(FILTERS)
    a0, a1 = MARGIN / W, FADE_END / W
    defs.append('<linearGradient id="edgefade" x1="0" y1="0" x2="%d" y2="0" gradientUnits="userSpaceOnUse">'
                '<stop offset="0" stop-color="#000"/><stop offset="%.4f" stop-color="#000"/>'
                '<stop offset="%.4f" stop-color="#fff"/><stop offset="%.4f" stop-color="#fff"/>'
                '<stop offset="%.4f" stop-color="#000"/><stop offset="1" stop-color="#000"/></linearGradient>'
                % (W, a0, a1, 1 - a1, 1 - a0))
    defs.append('<mask id="edgemask" maskUnits="userSpaceOnUse" x="0" y="0" width="%d" height="%d">'
                '<rect width="%d" height="%d" fill="url(#edgefade)"/></mask>' % (W, H, W, H))
    ops = []
    for k, oc in enumerate(cfg['openings']):
        op = Opening(oc, random.Random(cfg['seed'] * 31 + k))
        n = op.n
        # deep core window: shifted towards the direction the tunnel bends away
        bx, by = oc.get('bend', (-0.2, -0.1))
        op.deep_c = (op.cx[n] + bx * op.X[n], op.ys[n] + by * op.T[n])
        op.defs = defs
        ops.append(op)
    xs = split_fn(cfg, ops)
    ysamp = [-40 + (H + 80) * j / 40 for j in range(41)]
    bl = [(xs(y), y) for y in ysamp]
    defs.append('<clipPath id="cl"><path d="%s"/></clipPath>' % poly_path([(-10, -40)] + bl + [(-10, H + 40)]))
    defs.append('<clipPath id="cr"><path d="%s"/></clipPath>' % poly_path([(W + 10, -40)] + bl + [(W + 10, H + 40)]))
    bl2 = [(x + 3, y) for (x, y) in bl]
    defs.append('<clipPath id="cl2"><path d="%s"/></clipPath>' % poly_path([(-10, -40)] + bl2 + [(-10, H + 40)]))

    svg_body = Svg()
    # ---- base (identical in every variant)
    svg_body.add('<rect width="%d" height="%d" fill="url(#base)"/>' % (W, H))
    # ---- features, faded out towards both borders
    svg_body.add('<g mask="url(#edgemask)">')
    fy0 = min(op.yf for op in ops)
    rngs = [random.Random(cfg['seed'] * 101 + k) for k in range(len(ops))]
    for k, (op, clip) in enumerate(zip(ops, ('cl', 'cr'))):
        op.floor_y0 = fy0
        defs.append(hole_gradient(op, 'hole%d' % k))
        svg_body.add('<g clip-path="url(#%s)">' % clip)
        draw_wall_fold(svg_body, op, rngs[k])
        draw_opening(svg_body, op, rngs[k], 'hole%d' % k)
        svg_body.add('</g>')
    # the shared fold where the outer folds of the two openings meet: one crease
    fold_line(svg_body, xs, rng, lip_side=1)
    # the floors run in front of everything (and hide the bottom of the shared crease)
    for k, (op, clip) in enumerate(zip(ops, ('cl2', 'cr'))):
        svg_body.add('<g clip-path="url(#%s)">' % clip)
        draw_floor(svg_body, op, rngs[k], 'floor%d' % k)
        svg_body.add('</g>')
    # broad warm light pools on the lit upper-left folds (light from the viewer side)
    for k, op in enumerate(ops):
        lth = math.atan2(op.light[1], op.light[0]) % (2 * math.pi)
        px, py = op.band_pt(1, lth, 0.3)
        r = op.X[0] * 0.55
        gid = 'pool%d' % k
        defs.append('<radialGradient id="%s" gradientUnits="userSpaceOnUse" cx="%s" cy="%s" r="%s">'
                    '<stop offset="0" stop-color="%s" stop-opacity="0.10"/>'
                    '<stop offset="0.5" stop-color="%s" stop-opacity="0.05"/>'
                    '<stop offset="1" stop-color="%s" stop-opacity="0"/></radialGradient>'
                    % (gid, f(px), f(py), f(r), POOL0, POOL1, POOL1))
        svg_body.add('<rect width="%d" height="%d" fill="url(#%s)"/>' % (W, H, gid))
    # warm saturated haze on the two outer folds only (zero on the inner folds and the hole)
    for k, op in enumerate(ops):
        cx, cy = op.cx[1], op.ys[1]
        R = op.X[0] * 1.08
        s_in = op.X[2] / R
        s_pk = op.X[1] / R
        gid = 'haze%d' % k
        defs.append('<radialGradient id="%s" gradientUnits="userSpaceOnUse" cx="%s" cy="%s" r="%s" '
                    'gradientTransform="translate(%s %s) scale(1 %s) translate(%s %s)">'
                    '<stop offset="0" stop-color="%s" stop-opacity="0"/>'
                    '<stop offset="%.3f" stop-color="%s" stop-opacity="0"/>'
                    '<stop offset="%.3f" stop-color="%s" stop-opacity="0.06"/>'
                    '<stop offset="1" stop-color="%s" stop-opacity="0"/></radialGradient>'
                    % (gid, f(cx), f(cy), f(R), f(cx), f(cy), '%.3f' % (op.T[0] / op.X[0]), f(-cx), f(-cy),
                       HAZE, s_in, HAZE, s_pk, HAZE, HAZE))
        svg_body.add('<rect width="%d" height="%d" fill="url(#%s)"/>' % (W, H, gid))
    svg_body.add('</g>')
    # ---- seam folds (identical in every variant, the only features allowed in the margins)
    draw_seam_folds(svg_body)
    # ---- shared painterly grain over the whole canvas (periodic with the segment width)
    svg_body.add('<rect width="%d" height="%d" fill="#fff" filter="url(#mottle)"/>' % (W, H))
    svg_body.add('<rect width="%d" height="%d" fill="#fff" filter="url(#grain)"/>' % (W, H))

    svg.add('<defs>')
    svg.parts.extend(defs)
    svg.add('</defs>')
    svg.parts.extend(svg_body.parts)
    svg.add('</svg>')
    return '\n'.join(svg.parts) + '\n'


BIG = dict(bands=[118, 82, 56, 38, 26], gaps=[14, 12, 10, 9, 8], outer_gap=14)
SMALL = dict(bands=[118, 80, 54, 36], gaps=[12, 10, 9, 8], outer_gap=12)

VARIANTS = {
    'far_a': dict(
        seed=11,
        openings=[
            # big, higher, on the left; the tunnel bends away up-left
            dict(BIG, anchor=('left', 74), V=(0, 524), hole_w=100, hole_top=126, hole_floor=52,
                 drift=(0.16, 0.05), lean=-0.05, bend=(-0.22, -0.12), vr=(0.78, 0.45), floor_slope=0.5,
                 flare=-0.04, pexp=2.25, light=(-0.62, -0.5)),
            # small, lower, on the right; the tunnel bends away right
            dict(SMALL, anchor=('right', 1846), V=(0, 556), hole_w=86, hole_top=110, hole_floor=46,
                 drift=(-0.16, 0.03), lean=0.04, bend=(0.22, -0.06), vr=(0.80, 0.50), floor_slope=0.5,
                 flare=-0.04, pexp=2.2, light=(-0.58, -0.55)),
        ]),
    'far_b': dict(
        seed=23,
        openings=[
            # small, lower, on the left; the tunnel bends away down-left
            dict(SMALL, anchor=('left', 74), V=(0, 560), hole_w=88, hole_top=112, hole_floor=46,
                 drift=(0.15, 0.0), lean=-0.03, bend=(-0.24, 0.02), vr=(0.80, 0.50), floor_slope=0.5,
                 flare=-0.04, pexp=2.2, light=(-0.58, -0.55)),
            # big, higher, on the right; the tunnel bends away up-right
            dict(BIG, anchor=('right', 1846), V=(0, 518), hole_w=100, hole_top=128, hole_floor=52,
                 drift=(-0.16, 0.06), lean=0.05, bend=(0.22, -0.14), vr=(0.76, 0.44), floor_slope=0.5,
                 flare=-0.04, pexp=2.3, light=(-0.62, -0.5)),
        ]),
}

if __name__ == '__main__':
    os.makedirs(OUT_DIR, exist_ok=True)
    for name, cfg in VARIANTS.items():
        data = build(cfg)
        path = os.path.join(OUT_DIR, name + '.svg')
        with open(path, 'w') as fh:
            fh.write(data)
        print('%s -> %s (%d KB)' % (name, os.path.relpath(path), len(data) // 1024))
