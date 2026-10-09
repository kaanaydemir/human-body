#!/usr/bin/env python3
"""Generates public/assets/svg/environment/ceiling_{a,b,c}.svg (near ceiling, main plane, 1920x340).

Run from the repo root (stdlib only, deterministic, byte-identical on every run):
    python3 -I tools/art/ceiling/gen_ceiling.py [a b c] [--out DIR]

Composition (back to front), all hand placed in layout.py:
  1. base   : union silhouette (body rectangle + every fold outline) filled with the shared vertical base
              gradient.
  2. backs  : far vault arcs, visible only in the V gaps above the pillars.
  3. arcs   : the vault arcade overhead. Each arc is an upward-convex ring fold: lit face above its lower edge,
              a broken 3 px #e7a99e rim on that edge, a #771d26 -> #93201e recess under it and one nested inner
              ring. An arc fills its own "tombstone" with the base gradient, which hides the farther arcs.
              Feet taper out on the top of a fold's round end (the notch-side leg) or on a fold face.
  4. mottle : the shared `mottle` overlay over the union silhouette.
  5. folds  : the long overhanging folds whose lower edges form the contour: lit band, #d8635f ledge with broken
              #e7a99e streaks, opaque #93201e underside, tapered #6e1a24 ink that runs up the round end as a
              short crease. A fold's paint is clipped by the outlines of the folds in front of it.
  6. marks  : pores and 2-3 long streaks.
  7. grain  : the shared `grain` overlay over the union silhouette.

Tiling: every piece that crosses a border belongs to the SEAM_* set and is painted identically at x=0 and
x=1920 in every variant; variant pieces stay inside layout.SAFE (checked, 'MARGIN VIOLATION' on stderr).
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from geom import cr_param, at, snormals, band_poly, poly_d, lin_d, blob_d, smooth  # noqa: E402
import layout as LY  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
W, H = 1920, 340

C_INK = '#6e1a24'
C_DEEP = '#771d26'
C_SHADOW = '#93201e'
C_LIT = '#d73b3d'      # wall base (lit), a touch above the palette's #ce3a3e
C_LEDGE = '#d8635f'    # fold rim / ledge
C_RIM = '#e7a99e'      # pale rim light
C_STREAK = '#e65450'
C_FACE = '#db3a3d'     # lit face of a vault arc
C_FACE_SH = '#a8272f'  # its cel shadow (the leg turned away from the upper-left light)
C_EDGE = '#93201e'     # outer edge of a leg where it overlaps the neighbouring leg
C_HOLLOW = '#8a1d28'
C_CREASE = '#8f212b'   # thin crease along the back (outer) edge of a vault arc  # concave vault surface under the recess (one cel tone)
C_IFACE = '#bd3139'    # nested inner ring: hazier
C_IREC = '#8a2028'
C_BFACE = '#b52e37'    # far arcs
C_BFACE_SH = '#9d252e'
C_BREC = '#8a2028'

FILTERS = '''<filter id="grain" x="0" y="0" width="100%" height="100%" filterUnits="userSpaceOnUse">
    <feTurbulence type="fractalNoise" baseFrequency="0.9 0.6" numOctaves="2" seed="7" stitchTiles="stitch" result="n"/>
    <feColorMatrix in="n" type="matrix" values="0 0 0 0 0.35  0 0 0 0 0.06  0 0 0 0 0.08  0 0 0 0.10 0"/>
    <feComposite in2="SourceGraphic" operator="in"/>
  </filter>
  <filter id="mottle" x="0" y="0" width="100%" height="100%" filterUnits="userSpaceOnUse">
    <feTurbulence type="fractalNoise" baseFrequency="0.008 0.02" numOctaves="3" seed="3" stitchTiles="stitch" result="n"/>
    <feColorMatrix in="n" type="matrix" values="0 0 0 0 0.98  0 0 0 0 0.55  0 0 0 0 0.55  0 0 0 0.16 0"/>
    <feComposite in2="SourceGraphic" operator="in"/>
  </filter>'''


def P(d, fill, op=None):
    if not d:
        return ''
    o = f' opacity="{op:.2f}"' if op is not None and op < 0.995 else ''
    return f'<path d="{d}" fill="{fill}"{o}/>'


def wob(ph, f=0.9, a=0.08):
    """Hand-drawn thickness wobble as a function of the control-point index s."""
    return lambda s: 1 + a * math.sin(s * f * 6.28 + ph) + a * 0.5 * math.sin(s * f * 14.1 + ph * 1.7)


def sub(samples, s0, s1):
    return [p for p in samples if s0 <= p[2] <= s1]


def taper(s0, s1, s, k=0.35):
    """0 at both ends of [s0, s1], 1 in the middle (ramps over k index units)."""
    return smooth((s - s0) / k) * smooth((s1 - s) / k)


def inside(poly, x, y):
    c = False
    n = len(poly)
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi:
            c = not c
        j = i
    return c


def band(samples, fa, fb, k=2):
    """Closed path between offset fa(s) along +normal and fb(s) along -normal."""
    return poly_d(band_poly(samples, lambda s, x, y: fa(s), lambda s, x, y: fb(s)), k)


def dash_band(samples, s0, s1, centre, wd, k=0.35):
    """A tapered stroke of width wd whose centre lies centre(s) px along +normal."""
    seg = sub(samples, s0, s1)
    if len(seg) < 4:
        return ''
    return band(seg, lambda s: centre(s) + wd * 0.5 * taper(s0, s1, s, k),
                lambda s: -centre(s) + wd * 0.5 * taper(s0, s1, s, k))


# ---------------------------------------------------------------- pieces

class Fold:
    def __init__(self, spec, rng):
        self.spec = spec
        self.rng = rng
        self.low = cr_param(spec['low'], 2.0)
        self.top = cr_param(spec['top'], 2.0)
        self.ph = rng.uniform(0, 6.28)
        self.outline = [(x, y) for x, y, _ in self.low] + [(x, y) for x, y, _ in self.top]
        self.bbox = (min(p[0] for p in self.outline), max(p[0] for p in self.outline))
        sp = spec
        w1 = wob(self.ph, 0.55, 0.10)
        w2 = wob(self.ph + 2.1, 0.8, 0.12)
        self.under = lambda s: at(sp['under'], s) * w1(s)
        self.ledge = lambda s: self.under(s) + at(sp['ledge'], s) * w2(s)
        self.lit = lambda s: self.ledge(s) + at(sp['lit'], s) * w1(s + 0.7)
        self.ink = lambda s: at(sp['ink'], s) * (0.92 + 0.08 * w2(s))

    def paint(self, out):
        sp = self.spec
        L = self.low
        z0 = lambda s: 0.0  # noqa: E731
        # round-end caps: the body of a round end is filled, so arc feet and tucked folds disappear behind it
        for (s0, s1) in sp.get('cap', []):
            seg = [(x, y) for x, y, s in L if s0 <= s <= s1]
            if len(seg) > 3:
                out.append(P(lin_d(seg[::2] + [seg[-1]]), 'url(#base)'))
        for (s0, s1) in sp.get('caprim', []):
            out.append(P(dash_band(L, s0, s1, lambda s: 2.2, 2.6, 0.5), C_LEDGE))
        out.append(P(band(L, self.lit, z0), C_LIT))
        out.append(P(band(L, self.ledge, z0), C_LEDGE))
        for (s0, s1, pos) in sp.get('dash', []):
            wd = self.rng.uniform(2.0, 2.8)
            out.append(P(dash_band(L, s0, s1, lambda s, pos=pos: self.under(s) + (self.ledge(s) - self.under(s)) * pos, wd),
                         C_RIM))
        out.append(P(band(L, self.under, z0), C_SHADOW))
        out.append(P(band(L, lambda s: self.ink(s) * 0.45, lambda s: self.ink(s) * 0.55), C_INK))

    def face_depth(self, s):
        return self.lit(s)


class Arc:
    def __init__(self, spec, rng):
        self.spec = spec
        self.rng = rng
        self.low = cr_param(spec['low'], 2.0)
        self.n = len(spec['low']) - 1
        self.ph = rng.uniform(0, 6.28)
        sp = spec
        n = self.n
        w1 = wob(self.ph, 0.6, 0.06)
        # feet taper to nothing over the first/last control segment
        kl, kr = spec.get('ft', (1.0, 1.0))
        self.foot = lambda s: smooth(s / kl) * smooth((n - s) / kr)
        # the recess and hollow fade out before the feet (so a cap or the arc in front can cut the leg cleanly)
        hl, hr = spec.get('hft', (max(kl, 1.6), max(kr, 1.6)))
        self.hfoot = lambda s: smooth(s / hl) * smooth((n - s) / hr)
        self.T = lambda s: at(sp['T'], s) * w1(s) * (0.25 + 0.75 * self.foot(s))
        ns = snormals(self.low)
        self.outer = [(x + nx * self.T(s), y + ny * self.T(s)) for (x, y, s), (nx, ny) in zip(self.low, ns)]
        self.outline = self.outer
        self.bbox = (min(p[0] for p in self.outer), max(p[0] for p in self.outer))
        self.inner = []
        for r in spec.get('inner', []):
            # nested ring: the rim offset into the arch by d (px), over the index range r['s']
            s0, s1 = r['s']
            dd = r['d']

            def off(s, dd=dd, s0=s0, s1=s1):
                if isinstance(dd, (int, float)):
                    return float(dd)
                return at(dd, (s - s0) / (s1 - s0) * (len(dd) - 1))
            pts = [(x - nx * off(s), y - ny * off(s)) for (x, y, s), (nx, ny) in zip(self.low, ns) if s0 <= s <= s1]
            ctrl = pts[::max(1, len(pts) // 9)]
            if ctrl[-1] != pts[-1]:
                ctrl.append(pts[-1])
            self.inner.append(Ring(dict(r, low=ctrl), rng))

    def paint(self, out):
        sp = self.spec
        back = sp.get('back', False)
        L = self.low
        n = self.n
        T = self.T
        z0 = lambda s: 0.0  # noqa: E731
        # tombstone: everything under the outer edge belongs to this arc (hides the farther arcs)
        out.append(P(poly_d(self.outer, 2), 'url(#base)'))
        for r in self.inner:
            r.paint(out)
        # concave vault surface under the recess: one cel tone, edge wobbles gently (absolute px, low frequency)
        if not back and sp.get('hollow'):
            hol = lambda s: max(0.0, at(sp['hollow'], s) * 1.15 + 4.0 * math.sin(s * 1.9 + self.ph) * self.foot(s)) * self.hfoot(s)  # noqa: E731
            out.append(P(band(L, z0, hol), C_HOLLOW))
        rw = lambda s: max(0.0, at(sp['rw'], s) + 2.5 * math.sin(s * 2.7 + self.ph * 1.3)) * self.hfoot(s)  # noqa: E731
        rc = lambda s: max(0.0, at(sp['rc'], s) + 1.5 * math.sin(s * 3.9 + self.ph * 0.7)) * self.hfoot(s)  # noqa: E731
        out.append(P(band(L, z0, rw), C_BREC if back else C_SHADOW))
        out.append(P(band(L, z0, rc), C_DEEP))
        # face: the crest next to the rim catches the light; the back of the fold keeps the wall tone and ends
        # in a thin crease. The leg turned away from the light carries one cel shadow.
        crest = sp.get('crest', 0.55)
        if back:
            out.append(P(band(L, T, z0), C_BFACE))
        else:
            cw = lambda s: T(s) * (crest + 0.08 * math.sin(s * 2.3 + self.ph))  # noqa: E731
            out.append(P(band(L, cw, z0), C_FACE))
            out.append(P(band(L, lambda s: T(s) + 0.6, lambda s: -(T(s) - 2.2 * self.foot(s))), C_CREASE))
        s_sh = sp.get('shade', n * 0.7)
        seg = sub(L, s_sh - 0.8, n)
        if len(seg) > 3:
            g = lambda s: smooth((s - (s_sh - 0.8)) / 1.6)  # noqa: E731
            top = (lambda s: T(s) + 0.3) if back else (lambda s: T(s) * (crest + 0.08 * math.sin(s * 2.3 + self.ph)) + 0.3)
            out.append(P(band(seg, top, lambda s: -top(s) * (1 - g(s))), C_BFACE_SH if back else C_FACE_SH))
        if not back:
            for (s0, s1, pos) in sp.get('dash', []):
                out.append(P(dash_band(L, s0, s1, lambda s, pos=pos: T(s) * crest * pos, 2.4, 0.4), C_STREAK))
            for (s0, s1) in sp.get('edge', []):
                out.append(P(dash_band(L, s0, s1, lambda s: T(s) - 0.6, 2.4, 0.5), C_EDGE))
        # pale rim on the lower edge, broken
        rimw = lambda s: at(sp['rim'], s)  # noqa: E731
        col = C_LEDGE if back else C_RIM
        for (s0, s1) in sp.get('rims', [(0.5, n - 0.5)]):
            seg = sub(L, s0, s1)
            if len(seg) > 3:
                out.append(P(band(seg, lambda s, s0=s0, s1=s1: rimw(s) * taper(s0, s1, s, 0.3) + 0.2, lambda s: 0.5), col))


class Ring:
    """Nested inner ring inside an arch: same build as an arc, thinner and hazier, no tombstone."""

    def __init__(self, spec, rng):
        self.spec = spec
        self.low = cr_param(spec['low'], 2.0)
        self.n = len(spec['low']) - 1
        self.ph = rng.uniform(0, 6.28)

    def paint(self, out):
        sp = self.spec
        L = self.low
        n = self.n
        foot = lambda s: smooth(s / 1.2) * smooth((n - s) / 1.2)  # noqa: E731
        T = lambda s: at(sp.get('T', 16), s) * foot(s)  # noqa: E731
        rw = lambda s: at(sp.get('rw', 13), s) * foot(s) * wob(self.ph, 1.1, 0.15)(s)  # noqa: E731
        z0 = lambda s: 0.0  # noqa: E731
        out.append(P(band(L, z0, rw), C_IREC))
        out.append(P(band(L, z0, lambda s: rw(s) * 0.35), C_DEEP))
        out.append(P(band(L, T, z0), C_IFACE))
        for (a, b) in sp.get('rims', [(0.15, 0.6)]):
            s0, s1 = a * n, b * n
            seg = sub(L, s0, s1)
            if len(seg) > 3:
                out.append(P(band(seg, lambda s, s0=s0, s1=s1: 2.0 * taper(s0, s1, s, 0.4) + 0.2, lambda s: 0.4), C_LEDGE))


# ---------------------------------------------------------------- marks

def pore(cx, cy, r, rot, rng, out):
    rx, ry = r, r * rng.uniform(0.5, 0.68)
    out.append(P(blob_d(cx, cy, rx, ry, rot, rng, 0.12, 7), C_INK))
    a = math.radians(rot)
    pts = []
    for i in range(6):
        t = math.radians(30 + 120 * i / 5)
        x, y = math.cos(t) * rx * 0.95, math.sin(t) * ry * 1.05
        pts.append((cx + x * math.cos(a) - y * math.sin(a), cy + x * math.sin(a) + y * math.cos(a)))
    samples = cr_param(pts, 1.0)
    out.append(P(band(samples, lambda s: 0.15, lambda s: 0.5 * math.sin(math.pi * s / 5), 1), C_LEDGE))


def place_pores(pieces, blockers, n, rng, out, xr, depth):
    """Pores on the faces of `pieces` (folds: above the lit band; arcs: below the recess)."""
    placed = 0
    tries = 0
    while placed < n and tries < n * 60:
        tries += 1
        pc = rng.choice(pieces)
        L = pc.low
        i = rng.randrange(len(L) // 6, len(L) - len(L) // 6)
        x, y, s = L[i]
        a = L[max(0, i - 2)]
        b = L[min(len(L) - 1, i + 2)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(dx, dy) or 1
        nx, ny = dy / ln, -dx / ln
        d = depth(pc, s, rng)
        px, py = x + nx * d, y + ny * d
        if not (xr[0] + 10 < px < xr[1] - 10) or py < 12:
            continue
        if isinstance(pc, Fold) and not inside(pc.outline, px, py):
            continue
        if any(inside(bk.outline, px, py) for bk in blockers(pc)):
            continue
        r = rng.uniform(1.6, 3.4)
        rot = math.degrees(math.atan2(dy, dx)) + rng.uniform(-12, 12)
        pore(px, py, r, rot, rng, out)
        placed += 1
        if rng.random() < 0.35:
            pore(px + dx / ln * rng.uniform(8, 16), py + dy / ln * rng.uniform(-3, 3), r * 0.6, rot, rng, out)


def spot(x, y, rx, ry, rot, rng, out):
    """Flat dark blotch in the wall (the dark ovals of panel 7): shadow tone, deeper core, rim on its lower lip."""
    out.append(P(blob_d(x, y, rx, ry, rot, rng, 0.08, 10), C_SHADOW))
    out.append(P(blob_d(x + rx * 0.08, y + ry * 0.12, rx * 0.66, ry * 0.56, rot, rng, 0.1, 9), C_DEEP))
    a = math.radians(rot)
    pts = []
    for i in range(7):
        t = math.radians(25 + 130 * i / 6)
        px, py = math.cos(t) * rx * 1.02, math.sin(t) * ry * 1.04
        pts.append((x + px * math.cos(a) - py * math.sin(a), y + px * math.sin(a) + py * math.cos(a)))
    samples = cr_param(pts, 1.0)
    out.append(P(band(samples, lambda s: 0.2, lambda s: 1.3 * math.sin(math.pi * s / 6), 1), C_LEDGE))


def streak(fold, s0, s1, off, wd, out):
    out.append(P(dash_band(fold.low, s0, s1, lambda s: fold.lit(s) + off, wd, 0.8), C_STREAK))


# ---------------------------------------------------------------- assemble

def translated(parts, dx):
    body = ''.join(x for x in parts if x)
    if not body:
        return ''
    if dx == 0:
        return f'<g>{body}</g>'
    return f'<g transform="translate({dx} 0)">{body}</g>'


def check_safe(name, pieces):
    lo, hi = LY.SAFE
    for pc in pieces:
        if pc.spec.get('hidden'):
            continue  # starts behind the seam arc; the pixel check in check.py covers it
        a, b = pc.bbox
        if a < lo or b > hi:
            sys.stderr.write(f'MARGIN VIOLATION ceiling_{name} {pc.spec["name"]}: x {a:.0f}..{b:.0f} outside {lo}..{hi}\n')


def shifted(poly, dx):
    return [(x + dx, y) for x, y in poly]


def build(name, out_dir):
    spec = LY.VARIANTS[name]
    rng = random.Random(spec['seed'])
    srng = random.Random(9001)
    s_backs = [Arc(b, srng) for b in LY.SEAM_BACK]
    s_arc = Arc(LY.SEAM_ARC, srng)
    s_fold = Fold(LY.SEAM_FOLD, srng)
    backs = [Arc(b, rng) for b in spec.get('backs', [])]
    arcs = sorted([Arc(a, rng) for a in spec['arcs']], key=lambda a: a.spec.get('z', 0))
    folds = sorted([Fold(f, rng) for f in spec['folds']], key=lambda f: f.spec.get('z', 0))
    check_safe(name, backs + arcs + folds)
    byname = {f.spec['name']: f for f in folds}

    def paint(pcs):
        o = []
        for pc in pcs:
            pc.paint(o)
        return o

    o = []
    o.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">')
    o.append('<defs>')
    o.append(f'<linearGradient id="base" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="0" y2="{H}">'
             + ''.join(f'<stop offset="{off}" stop-color="{c}"/>' for off, c in LY.BASE_STOPS) + '</linearGradient>')
    o.append('  ' + FILTERS)
    s_out = poly_d(s_fold.outline, 2)
    sil = [f'<rect x="-400" y="-10" width="{W + 800}" height="{LY.BODY_Y + 10}"/>']
    for f in folds:
        sil.append(f'<path d="{poly_d(f.outline, 2)}"/>')
    sil.append(f'<path d="{s_out}"/><path transform="translate({W} 0)" d="{s_out}"/>')
    o.append('<clipPath id="sil">' + ''.join(sil) + '</clipPath>')
    # occlusion: a fold's paint is clipped by the outlines of the folds in front of it. The shared seam lobe is
    # in front of the first variant fold (its round end at x~130-180) and behind the last one (x~1750).
    big = f'M-600 -200H{W + 600}V{H + 200}H-600Z'
    seam0 = poly_d(s_fold.outline, 2)
    occ = {}
    for f in folds:
        fr = [poly_d(g.outline, 2) for g in folds if g.spec['z'] > f.spec['z']] + [seam0]
        cid = f'occ_{f.spec["name"]}'
        o.append(f'<clipPath id="{cid}"><path clip-rule="evenodd" d="{big}{"".join(fr)}"/></clipPath>')
        occ[f.spec['name']] = cid
    d = big + ''.join(poly_d([(x - W, y) for x, y in g.outline], 2) for g in folds)
    o.append(f'<clipPath id="occ_seam"><path clip-rule="evenodd" d="{d}"/></clipPath>')
    o.append('</defs>')
    o.append('<!-- base: shared gradient over the union silhouette -->')
    o.append(f'<rect width="{W}" height="{H}" fill="url(#base)" clip-path="url(#sil)"/>')
    o.append('<g clip-path="url(#sil)">')
    o.append('<!-- far vault arcs (shared seam pair first) -->')
    sb = paint(s_backs)
    o.append(translated(sb, 0))
    o.append(translated(sb, W))
    o.extend(paint(backs))
    o.append('<!-- vault arcade -->')
    o.extend(paint(arcs))
    sa = paint([s_arc])
    o.append(translated(sa, 0))
    o.append(translated(sa, W))
    o.append('</g>')
    o.append('<!-- overhanging folds: shared seam lobe, then the variant folds by depth -->')
    sf = paint([s_fold])
    # the copy at x=1920 sits behind the last variant fold: clip it in its own (translated) coordinates
    o.append(f'<g transform="translate({W} 0)"><g clip-path="url(#occ_seam)">' + ''.join(x for x in sf if x) + '</g></g>')
    for f in folds:
        fo = []
        f.paint(fo)
        o.append(f'<g clip-path="url(#{occ[f.spec["name"]]})">' + ''.join(x for x in fo if x) + '</g>')
    o.append(translated(sf, 0))
    o.append('<!-- marks -->')
    mk = []
    for (fn, s0, s1, off, wd) in spec.get('streaks', []):
        streak(byname[fn], s0, s1, off, wd, mk)
    pr = spec.get('pores', {})
    place_pores(folds, lambda pc: [g for g in folds if g.spec['z'] > pc.spec['z']] + arcs, pr.get('fold', 20), rng, mk,
                LY.SAFE, lambda pc, s, r: pc.lit(s) + r.uniform(8, 62))
    place_pores(arcs, lambda pc: [a for a in arcs if a.spec.get('z', 0) > pc.spec.get('z', 0)],
                pr.get('arc', 12), rng, mk, LY.SAFE, lambda pc, s, r: -(at(pc.spec['rw'], s) + r.uniform(6, 22)))
    for sp_ in spec.get('spots', []):
        spot(*sp_, rng, mk)
    o.append('<g clip-path="url(#sil)">' + ''.join(x for x in mk if x) + '</g>')
    sm = []
    smr = random.Random(4242)
    place_pores([s_fold], lambda pc: [], 6, smr, sm, (-140, 140), lambda pc, s, r: pc.lit(s) + r.uniform(8, 36))
    place_pores([s_arc], lambda pc: [], 4, smr, sm, (-130, 130), lambda pc, s, r: -(at(pc.spec['rw'], s) + r.uniform(6, 22)))
    o.append(translated(sm, 0))
    o.append(translated(sm, W))
    o.append('<!-- shared mottle + grain over the union silhouette -->')
    o.append(f'<g clip-path="url(#sil)" opacity="0.3"><rect width="{W}" height="{H}" fill="#000" filter="url(#mottle)"/></g>')
    o.append(f'<g clip-path="url(#sil)"><rect width="{W}" height="{H}" fill="#000" filter="url(#grain)"/></g>')
    o.append('</svg>')
    svg = '\n'.join(x for x in o if x) + '\n'
    path = os.path.join(out_dir, f'ceiling_{name}.svg')
    with open(path, 'w') as fh:
        fh.write(svg)
    print(path, f'{len(svg) / 1024:.0f} KB')


if __name__ == '__main__':
    args = sys.argv[1:]
    out_dir = os.path.join(ROOT, 'public', 'assets', 'svg', 'environment')
    if '--out' in args:
        i = args.index('--out')
        out_dir = args[i + 1]
        del args[i:i + 2]
    os.makedirs(out_dir, exist_ok=True)
    for nm in (args or sorted(LY.VARIANTS)):
        build(nm, out_dir)
