#!/usr/bin/env python3
"""Generator for the hand-drawn UI kit (group: ui).

Emits public/assets/svg/ui/{panel,badge,key_e,key_space,icon_objective,icon_progress}.svg.
Shapes are hand-designed (explicit coordinates); helpers only turn centre-lines with
width profiles into filled brush strokes and smooth anchor loops into cubic Beziers.

    python3 -I tools/art/ui/gen_ui.py                  # all six, into public/assets/svg/ui/
    python3 -I tools/art/ui/gen_ui.py panel badge      # only some
    python3 -I tools/art/ui/gen_ui.py --out DIR        # somewhere else (scratch / diffing)

Standard library only; deterministic (no clock, no RNG), so re-runs are byte-identical.
"""
import math
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
OUT = os.path.join(ROOT, 'public', 'assets', 'svg', 'ui')

# Shared filters, copied verbatim from ART_DIRECTION.md section 7.
SHARED_FILTERS = '''<filter id="grain" x="0" y="0" width="100%" height="100%" filterUnits="userSpaceOnUse">
    <feTurbulence type="fractalNoise" baseFrequency="0.9 0.6" numOctaves="2" seed="7" stitchTiles="stitch" result="n"/>
    <feColorMatrix in="n" type="matrix" values="0 0 0 0 0.35  0 0 0 0 0.06  0 0 0 0 0.08  0 0 0 0.10 0"/>
    <feComposite in2="SourceGraphic" operator="in"/>
  </filter>
  <filter id="mottle" x="0" y="0" width="100%" height="100%" filterUnits="userSpaceOnUse">
    <feTurbulence type="fractalNoise" baseFrequency="0.008 0.02" numOctaves="3" seed="3" stitchTiles="stitch" result="n"/>
    <feColorMatrix in="n" type="matrix" values="0 0 0 0 0.98  0 0 0 0 0.55  0 0 0 0 0.55  0 0 0 0.16 0"/>
    <feComposite in2="SourceGraphic" operator="in"/>
  </filter>'''


# ----------------------------------------------------------------------------- helpers
def f(v):
    s = ('%.2f' % v).rstrip('0').rstrip('.')
    return '0' if s in ('-0', '') else s


def P(x, y):
    return f(x) + ' ' + f(y)


def smooth_closed(pts, tension=1.0):
    """Closed Catmull-Rom spline through anchors -> cubic Bezier path data."""
    n = len(pts)
    d = 'M' + P(*pts[0])
    for i in range(n):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[(i + 1) % n], pts[(i + 2) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6 * tension, p1[1] + (p2[1] - p0[1]) / 6 * tension)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6 * tension, p2[1] - (p3[1] - p1[1]) / 6 * tension)
        d += 'C' + P(*c1) + ' ' + P(*c2) + ' ' + P(*p2)
    return d + 'Z'


def smooth_open(pts, tension=1.0):
    n = len(pts)
    d = 'M' + P(*pts[0])
    for i in range(n - 1):
        p0 = pts[i - 1] if i > 0 else pts[i]
        p1, p2 = pts[i], pts[i + 1]
        p3 = pts[i + 2] if i + 2 < n else pts[i + 1]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6 * tension, p1[1] + (p2[1] - p0[1]) / 6 * tension)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6 * tension, p2[1] - (p3[1] - p1[1]) / 6 * tension)
        d += 'C' + P(*c1) + ' ' + P(*c2) + ' ' + P(*p2)
    return d


def bez(p0, p1, p2, p3, n):
    out = []
    for i in range(n + 1):
        t = i / n
        a = (1 - t) ** 3
        b = 3 * (1 - t) ** 2 * t
        c = 3 * (1 - t) * t * t
        e = t ** 3
        out.append((a * p0[0] + b * p1[0] + c * p2[0] + e * p3[0],
                    a * p0[1] + b * p1[1] + c * p2[1] + e * p3[1]))
    return out


def brush(center, widths, cap_steps=6, simplify=1):
    """Variable-width brush stroke: centre-line points + full widths -> closed filled path.
    Round caps. Output is a smooth Catmull-Rom loop through the offset points."""
    n = len(center)
    left, right = [], []
    for i in range(n):
        a = center[max(i - 1, 0)]
        b = center[min(i + 1, n - 1)]
        tx, ty = b[0] - a[0], b[1] - a[1]
        L = math.hypot(tx, ty) or 1.0
        nx, ny = -ty / L, tx / L
        w = widths[i] / 2
        left.append((center[i][0] + nx * w, center[i][1] + ny * w))
        right.append((center[i][0] - nx * w, center[i][1] - ny * w))
    pts = left[::simplify]
    if pts[-1] != left[-1]:
        pts.append(left[-1])
    # end cap: from left[-1] around to right[-1]
    cx, cy = center[-1]
    a0 = math.atan2(left[-1][1] - cy, left[-1][0] - cx)
    w = widths[-1] / 2
    for k in range(1, cap_steps):
        ang = a0 - math.pi * k / cap_steps
        pts.append((cx + math.cos(ang) * w, cy + math.sin(ang) * w))
    rr = right[::-1][::simplify]
    if rr[-1] != right[0]:
        rr.append(right[0])
    pts += rr
    cx, cy = center[0]
    a0 = math.atan2(right[0][1] - cy, right[0][0] - cx)
    w = widths[0] / 2
    for k in range(1, cap_steps):
        ang = a0 - math.pi * k / cap_steps
        pts.append((cx + math.cos(ang) * w, cy + math.sin(ang) * w))
    return smooth_closed(pts, 0.9)


def profile(n, w0, w1, wmid=None, ease=1.0):
    """width profile across n+1 samples: w0 -> (wmid) -> w1."""
    out = []
    for i in range(n + 1):
        t = i / n
        if wmid is None:
            out.append(w0 + (w1 - w0) * t)
        else:
            if t < 0.5:
                s = (t / 0.5) ** ease
                out.append(w0 + (wmid - w0) * math.sin(s * math.pi / 2))
            else:
                s = ((1 - t) / 0.5) ** ease
                out.append(w1 + (wmid - w1) * math.sin(s * math.pi / 2))
    return out


def arc_pts(cx, cy, rx, ry, a0, a1, n, rot=0.0):
    out = []
    cr, sr = math.cos(rot), math.sin(rot)
    for i in range(n + 1):
        t = math.radians(a0 + (a1 - a0) * i / n)
        x, y = math.cos(t) * rx, math.sin(t) * ry
        out.append((cx + x * cr - y * sr, cy + x * sr + y * cr))
    return out


def loop(cx, cy, rx, ry, n=16, rot=0.0, wob=(), start=0.0):
    """Closed organic loop: anchors on an ellipse with low-frequency radial wobble.
    wob = ((amp, freq, phase), ...) in fractions of the radius."""
    pts = []
    cr, sr = math.cos(rot), math.sin(rot)
    for i in range(n):
        t = 2 * math.pi * i / n + math.radians(start)
        k = 1.0 + sum(a * math.sin(fq * t + ph) for a, fq, ph in wob)
        x, y = math.cos(t) * rx * k, math.sin(t) * ry * k
        pts.append((cx + x * cr - y * sr, cy + x * sr + y * cr))
    return pts


def rrect(L, T, R, B, corners):
    """Rounded rectangle with exactly straight edges and per-corner elliptical corners.
    corners = dict tl/tr/br/bl -> (rx, ry, k, (dx, dy) wobble of the corner's mid-control)."""
    def c(name):
        v = corners[name]
        rx, ry, k = v[0], v[1], v[2]
        w = v[3] if len(v) > 3 else (0, 0)
        return rx, ry, k, w
    rx, ry, k, w = c('tl')
    d = 'M' + P(L + rx, T)
    rx2, ry2, k2, w2 = c('tr')
    d += 'L' + P(R - rx2, T)
    d += 'C' + P(R - rx2 + rx2 * k2 + w2[0], T + w2[1]) + ' ' + P(R + w2[0], T + ry2 - ry2 * k2 + w2[1]) + ' ' + P(R, T + ry2)
    rx3, ry3, k3, w3 = c('br')
    d += 'L' + P(R, B - ry3)
    d += 'C' + P(R + w3[0], B - ry3 + ry3 * k3 + w3[1]) + ' ' + P(R - rx3 + rx3 * k3 + w3[0], B + w3[1]) + ' ' + P(R - rx3, B)
    rx4, ry4, k4, w4 = c('bl')
    d += 'L' + P(L + rx4, B)
    d += 'C' + P(L + rx4 - rx4 * k4 + w4[0], B + w4[1]) + ' ' + P(L + w4[0], B - ry4 + ry4 * k4 + w4[1]) + ' ' + P(L, B - ry4)
    d += 'L' + P(L, T + ry)
    d += 'C' + P(L + w[0], T + ry - ry * k + w[1]) + ' ' + P(L + rx - rx * k + w[0], T + w[1]) + ' ' + P(L + rx, T)
    return d + 'Z'


def rquad(C, radii, k=0.56, bow=(0, 0, 0, 0)):
    """Rounded quadrilateral through 4 corner points C=[tl,tr,br,bl] (any skew).
    radii per corner; bow = outward sag (px) of each edge tl-tr, tr-br, br-bl, bl-tl,
    so the edges feel hand-drawn instead of ruled."""
    n = 4
    T_in, T_out = [], []
    for i in range(n):
        c, pv, nx = C[i], C[i - 1], C[(i + 1) % n]
        r = radii[i]
        dv = math.hypot(pv[0] - c[0], pv[1] - c[1])
        dn = math.hypot(nx[0] - c[0], nx[1] - c[1])
        T_in.append((c[0] + (pv[0] - c[0]) * r / dv, c[1] + (pv[1] - c[1]) * r / dv))
        T_out.append((c[0] + (nx[0] - c[0]) * r / dn, c[1] + (nx[1] - c[1]) * r / dn))
    d = 'M' + P(*T_out[0])
    for i in range(n):
        j = (i + 1) % n
        a, b = T_out[i], T_in[j]
        if bow[i]:
            ex, ey = b[0] - a[0], b[1] - a[1]
            L = math.hypot(ex, ey)
            nx_, ny_ = ey / L, -ex / L  # outward normal for clockwise loop
            d += 'C' + P(a[0] + ex / 3 + nx_ * bow[i], a[1] + ey / 3 + ny_ * bow[i]) + ' ' + \
                 P(a[0] + ex * 2 / 3 + nx_ * bow[i], a[1] + ey * 2 / 3 + ny_ * bow[i]) + ' ' + P(*b)
        else:
            d += 'L' + P(*b)
        c = C[j]
        d += 'C' + P(b[0] + (c[0] - b[0]) * k, b[1] + (c[1] - b[1]) * k) + ' ' + \
             P(T_out[j][0] + (c[0] - T_out[j][0]) * k, T_out[j][1] + (c[1] - T_out[j][1]) * k) + ' ' + P(*T_out[j])
    return d + 'Z'


def svg(w, h, body, defs='', filters=True):
    if not filters and not defs:
        return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d">\n'
                '%s\n</svg>\n') % (w, h, w, h, body)
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d">\n'
            '<defs>\n  %s\n%s\n</defs>\n%s\n</svg>\n') % (w, h, w, h, SHARED_FILTERS if filters else '', defs, body)


def write(name, text):
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, name)
    with open(p, 'w') as fh:
        fh.write(text)
    print('wrote', p, len(text.encode()) // 1024, 'KB')


# ============================================================================= PANEL
def panel():
    """Printed caption box, as in every numbered caption of reference.png: one flat cream
    fill, one thin even near-black line, round corners. No bevel, no highlight, no lip.
    Reference (caption 4, 1536 px sheet): line ~1.4 px, radius ~7 px on a 56 px box;
    the game's caption is ~2.5x that size, hence 3.5 px and r=20 here."""
    W, H = 600, 200
    BASE = PANEL_BASE          # lifted a hair so that base + grain averages #f9ead2
    INK = PANEL_INK
    LW = PANEL_LINE            # even on all four sides
    R = PANEL_R                # outer corner radius; inner radius = R - LW (concentric)
    k = 0.5523                 # circular-arc Bezier constant
    o = 1.0                    # 1 px transparent margin so bilinear sampling never clips the line
    outer = rrect(o, o, W - o, H - o, {c: (R, R, k) for c in ('tl', 'tr', 'br', 'bl')})
    ri = R - LW
    inner = rrect(o + LW, o + LW, W - o - LW, H - o - LW, {c: (ri, ri, k) for c in ('tl', 'tr', 'br', 'bl')})

    defs = ('<clipPath id="pin"><path d="%s"/></clipPath>' % inner)
    body = []
    body.append('<path d="%s" fill="%s"/>' % (outer, INK))
    body.append('<path d="%s" fill="%s"/>' % (inner, BASE))
    # very light paper grain only (shared filter, full-canvas region); no mottle
    body.append('<g clip-path="url(#pin)">')
    body.append('  <rect x="0" y="0" width="%d" height="%d" fill="%s" filter="url(#grain)" opacity="%s"/>' % (W, H, BASE, GRAIN_OP))
    body.append('</g>')
    return svg(W, H, '\n'.join(body), defs)



# ============================================================================= BADGE
def badge():
    """Flat printed number disc, as in the reference captions: one navy-black fill, no
    outline ring, no bevel, no specular. Colour sampled from the interior of badges
    1/4/5/9 in reference.png (mean #0c1322); the white numeral is printed by the game."""
    W = H = 96
    # a barely-there hand wobble (<0.3 px) so it is not a compass circle, still reads round
    wob = ((0.004, 3, 0.4), (0.003, 5, 1.3))
    disc = loop(48.0, 48.0, BADGE_R, BADGE_R, n=18, wob=wob)
    b = ['<path d="%s" fill="%s"/>' % (smooth_closed(disc), BADGE_FILL)]
    return svg(W, H, '\n'.join(b), filters=False)


# ============================================================================= KEYCAPS
KEY_INK = '#463d32'
KEY_TOP = '#fdf4e4'
KEY_TOP_SH = '#f3e5cb'
KEY_SIDE = '#ead6b5'
KEY_LIP = '#d9bd95'
KEY_LIP_DEEP = '#c9a87e'
KEY_FACE_LINE = '#7a6650'


def keycap(W, face_only=True):
    """Shared keycap drawing (3/4 front view): outline, side skirt, darker front lip,
    lighter top face with a soft concave shade and an upper-left highlight."""
    H = 96
    R = W - 96   # extra width compared to the square key
    # --- silhouette / ink line (heavier at the bottom)
    oC = [(7.5, 7.5), (88.5 + R, 7), (91 + R, 87.5), (5, 88)]
    oR = [19, 19, 16, 16]
    iC = [(12.5, 12), (83.8 + R, 11.6), (85 + R, 81.3), (11.2, 81.6)]
    iR = [15, 15, 12, 12]
    outer = rquad(oC, oR, 0.58, bow=(0.6, 0.5, 0.5, 0.5))
    inner = rquad(iC, iR, 0.58, bow=(0.5, 0.4, 0.4, 0.4))
    # --- top face (slightly narrower toward the back = perspective)
    fC = [(16.5, 13.6), (79.5 + R, 13.2), (80.5 + R, 68.5), (15.6, 68.9)]
    fR = [12, 12, 11, 11]
    face = rquad(fC, fR, 0.6, bow=(0.5, 0.3, 0.6, 0.3))
    faceline = rquad([(15.3, 12.6), (80.7 + R, 12.2), (81.9 + R, 70.6), (14.2, 71)], [13, 13, 12.5, 12.5], 0.6,
                     bow=(0.5, 0.3, 0.6, 0.3))
    # --- front lip region (between face bottom and body bottom, bounded by the corner creases)
    lip = 'M%s L%s L%s L%s Z' % (P(17.5, 64), P(2, 96), P(94 + R, 96), P(78.5 + R, 64))
    # right side of the skirt sits in shadow too (light from the upper left)
    rside = 'M%s L%s L%s L%s Z' % (P(78 + R, 14), P(100 + R, 0), P(100 + R, 96), P(80 + R, 66))
    # lip bottom cel line (deeper tone hugging the lower ink line)
    lipdeep = smooth_open([(12, 78.6), (30, 79.6), (48 + R / 2, 79.9), (66 + R, 79.6), (84 + R, 78.4)])
    # crease strokes from the face's bottom corners down to the body's corners
    cl = brush(bez((16.4, 66.5), (14.5, 70.5), (13.6, 74), (12.6, 77.2), 10), profile(10, 1.6, 0.4))
    cr = brush(bez((80 + R, 66.3), (81.6 + R, 70.2), (82.6 + R, 73.6), (83.6 + R, 76.8), 10), profile(10, 1.8, 0.5))
    # concave shade on the top face (lower-right crescent) + highlight
    face_sh = rquad([(22, 20), (85 + R, 18.5), (86 + R, 76), (21, 76)], [12, 12, 11, 11], 0.6)
    hl = brush(smooth_pts([(21.5, 52), (20.6, 36), (22.6, 23.4), (31, 18.6), (44, 18)], 18),
               profile(18, 0.8, 0.9, 3.0))
    hl_dot = loop(51.5, 18.1, 1.4, 1.2, n=8)
    # rim light on the lip's lower edge (bounce from the panel below)
    bounce = brush(bez((22, 84.2), (36, 85.4), (60 + R, 85.4), (76 + R, 84), 16), profile(16, 0.4, 0.4, 1.4))
    # soft contact shadow
    contact = loop(48 + R / 2, 88.8, 42 + R / 2, 3.4, n=14)

    defs = ('<clipPath id="kin"><path d="%s"/></clipPath>'
            '<clipPath id="kface"><path d="%s"/></clipPath>'
            '<filter id="ksoft" x="-10" y="60" width="%d" height="50" filterUnits="userSpaceOnUse">'
            '<feGaussianBlur stdDeviation="1.4"/></filter>') % (inner, face, W + 20)
    b = []
    b.append('<path d="%s" fill="%s" opacity=".24" filter="url(#ksoft)"/>' % (smooth_closed(contact), KEY_INK))
    b.append('<path d="%s" fill="%s"/>' % (outer, KEY_INK))
    b.append('<g clip-path="url(#kin)">')
    b.append('  <rect x="0" y="0" width="%d" height="96" fill="%s"/>' % (W, KEY_SIDE))
    b.append('  <path d="%s" fill="%s"/>' % (rside, '#e0c7a2'))
    b.append('  <path d="%s" fill="%s"/>' % (lip, KEY_LIP))
    b.append('  <path d="%s" fill="none" stroke="%s" stroke-width="3.2" stroke-linecap="round"/>' % (lipdeep, KEY_LIP_DEEP))
    b.append('  <path d="%s" fill="#f6e8cf" opacity=".85"/>' % bounce)
    b.append('  <rect x="0" y="0" width="%d" height="96" fill="%s" filter="url(#mottle)" opacity=".35"/>' % (W, KEY_SIDE))
    b.append('  <rect x="0" y="0" width="%d" height="96" fill="%s" filter="url(#grain)" opacity=".8"/>' % (W, KEY_SIDE))
    b.append('</g>')
    b.append('<path d="%s" fill="%s" opacity=".9"/>' % (cl, KEY_FACE_LINE))
    b.append('<path d="%s" fill="%s" opacity=".9"/>' % (cr, KEY_FACE_LINE))
    b.append('<path d="%s" fill="%s"/>' % (faceline, KEY_FACE_LINE))
    b.append('<path d="%s" fill="%s"/>' % (face, KEY_TOP_SH))
    b.append('<g clip-path="url(#kface)">')
    # the lit part of the dish: the face shifted up-left, leaving a soft shade crescent bottom-right
    b.append('  <path d="%s" fill="%s"/>' % (rquad([(11, 9), (79.5 + R, 8.5), (79 + R, 64.5), (10.5, 65)], [12, 12, 11, 11], 0.6), KEY_TOP))
    b.append('  <rect x="0" y="0" width="%d" height="96" fill="%s" filter="url(#grain)" opacity=".55"/>' % (W, KEY_TOP))
    b.append('</g>')
    b.append('<path d="%s" fill="#ffffff" opacity=".78"/>' % hl)
    b.append('<path d="%s" fill="#ffffff" opacity=".7"/>' % smooth_closed(hl_dot))
    return b, defs


def smooth_pts(anchors, n):
    """Sample a Catmull-Rom curve through anchors into n+1 points (for brush centre-lines)."""
    segs = len(anchors) - 1
    out = []
    for i in range(n + 1):
        u = i / n * segs
        k = min(int(u), segs - 1)
        t = u - k
        p0 = anchors[k - 1] if k > 0 else anchors[k]
        p1, p2 = anchors[k], anchors[k + 1]
        p3 = anchors[k + 2] if k + 2 <= segs else anchors[k + 1]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        out.append(_bez_at(p1, c1, c2, p2, t))
    return out


def _bez_at(p0, p1, p2, p3, t):
    a = (1 - t) ** 3
    b = 3 * (1 - t) ** 2 * t
    c = 3 * (1 - t) * t * t
    e = t ** 3
    return (a * p0[0] + b * p1[0] + c * p2[0] + e * p3[0], a * p0[1] + b * p1[1] + c * p2[1] + e * p3[1])


def letter_e(dx=0.0, dy=0.0):
    """Hand-lettered capital E as filled brush strokes (thicker stem foot, slightly
    tapering arms, a little lift at the arm ends)."""
    def sh(p):
        return (p[0] + dx, p[1] + dy)
    strokes = [
        (bez(sh((37.6, 25.4)), sh((36.7, 35)), sh((36.9, 46)), sh((37.3, 55.4)), 16), profile(16, 6.6, 7.6)),
        (bez(sh((37.8, 25.2)), sh((45, 24.3)), sh((53, 25.2)), sh((59.6, 24.0)), 16), profile(16, 7.0, 5.9)),
        (bez(sh((37.4, 40.3)), sh((43, 39.8)), sh((49.5, 40.9)), sh((55.2, 40.0)), 14), profile(14, 6.8, 5.7)),
        (bez(sh((37.4, 55.5)), sh((45, 56.2)), sh((53, 55.7)), sh((60.6, 54.6)), 16), profile(16, 7.6, 6.2)),
    ]
    return [brush(c, w) for c, w in strokes]


def key_e():
    b, defs = keycap(96)
    # engraved / printed feel: a pale edge below-right of the glyph, then the ink glyph
    for d in letter_e(0.7, 1.3):
        b.append('<path d="%s" fill="#fffaf0" opacity=".9"/>' % d)
    for d in letter_e():
        b.append('<path d="%s" fill="#3a3128"/>' % d)
    # tiny highlight nick on the stem (keeps the glyph from reading as a flat font)
    nick = brush(bez((35.9, 29), (35.6, 32), (35.6, 35), (35.7, 37.5), 6), profile(6, 0.5, 0.4, 1.1))
    b.append('<path d="%s" fill="#8a7660" opacity=".7"/>' % nick)
    return svg(96, 96, '\n'.join(b), defs)


def key_space():
    b, defs = keycap(220)
    # a second, longer streak along the top of the wide face (wide keys catch more light)
    streak = brush(bez((60, 17.6), (90, 16.6), (130, 16.8), (158, 17.6), 20), profile(20, 0.5, 0.5, 2.0))
    b.append('<path d="%s" fill="#ffffff" opacity=".6"/>' % streak)
    return svg(220, 96, '\n'.join(b), defs)


# ============================================================================= OBJECTIVE ICON
def ell_pts(cx, cy, rx, ry, rot_deg, n, extra=None, wob=()):
    """Anchors around a rotated ellipse; extra(t, nx, ny) -> (dx, dy) offsets per anchor."""
    rot = math.radians(rot_deg)
    cr, sr = math.cos(rot), math.sin(rot)
    pts = []
    for i in range(n):
        t = 2 * math.pi * i / n
        k = 1.0 + sum(a * math.sin(fq * t + ph) for a, fq, ph in wob)
        lx, ly = math.cos(t) * rx * k, math.sin(t) * ry * k
        x, y = cx + lx * cr - ly * sr, cy + lx * sr + ly * cr
        # outward normal of the ellipse (rotated)
        nlx, nly = math.cos(t) / rx, math.sin(t) / ry
        nx, ny = nlx * cr - nly * sr, nlx * sr + nly * cr
        L = math.hypot(nx, ny)
        nx, ny = nx / L, ny / L
        if extra:
            dx, dy = extra(t, nx, ny)
            x, y = x + dx, y + dy
        pts.append((x, y))
    return pts


def smoothstep(e0, e1, x):
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


def ell_frame(cx, cy, rx, ry, rot_deg, n, wob=()):
    """Points + outward screen normals around a rotated (slightly wobbly) ellipse."""
    rot = math.radians(rot_deg)
    cr, sr = math.cos(rot), math.sin(rot)
    pts, nrm = [], []
    for i in range(n):
        t = 2 * math.pi * i / n
        k = 1.0 + sum(a * math.sin(fq * t + ph) for a, fq, ph in wob)
        lx, ly = math.cos(t) * rx * k, math.sin(t) * ry * k
        pts.append((cx + lx * cr - ly * sr, cy + lx * sr + ly * cr))
        nlx, nly = math.cos(t) / rx, math.sin(t) / ry
        nx, ny = nlx * cr - nly * sr, nlx * sr + nly * cr
        L = math.hypot(nx, ny)
        nrm.append((nx / L, ny / L))
    return pts, nrm


def arc_where(pts, nrm, cond):
    """Longest contiguous (cyclic) run of points whose normal satisfies cond."""
    n = len(pts)
    ok = [cond(*nrm[i]) for i in range(n)]
    if all(ok):
        return pts[:]
    s0 = next(i for i in range(n) if not ok[i])
    best, cur = [], []
    for k in range(1, n + 1):
        i = (s0 + k) % n
        if ok[i]:
            cur.append(pts[i])
        else:
            if len(cur) > len(best):
                best = cur
            cur = []
    if len(cur) > len(best):
        best = cur
    return best


def taper(n, w, lo=0.35):
    """Brush profile that swells in the middle and tapers at both ends."""
    return [lo + (w - lo) * math.sin(math.pi * i / max(n - 1, 1)) for i in range(n)]


def red_cell(cx, cy, rx, ry, rot, depth, uid):
    """Plain biconcave red blood cell disc in 3/4 view, same construction as
    environment/disc_cell: puffy torus top, sunken dimple, shallow side band."""
    wob = ((0.012, 2, 0.6), (0.008, 3, 2.1))
    pts, nrm = ell_frame(cx, cy, rx, ry, rot, 40, wob)
    drop = [depth * smoothstep(-0.3, 0.4, ny) for nx, ny in nrm]
    top = pts
    hull = [(x, y + d) for (x, y), d in zip(pts, drop)]
    heavy = [1.9 + 1.4 * max(0.0, nx * .55 + ny * .83) for nx, ny in nrm]
    ink = [(x + nx * w, y + ny * w + d) for (x, y), (nx, ny), w, d in zip(pts, nrm, heavy, drop)]
    # torus shading: lit crescent upper-left, cel shade lower-right on the top face
    lit_in, _ = ell_frame(cx + 2.2, cy + 2.4, rx - 1.2, ry - 1.4, rot, 40, wob)
    shade_out, _ = ell_frame(cx - 1.6, cy - 1.9, rx - 0.6, ry - 0.8, rot, 40, wob)
    # dimple, a little above centre (we look down onto the disc)
    dcx, dcy = cx - 0.6, cy - 1.2
    drx, dry = rx * 0.56, ry * 0.52
    dpts, dnrm = ell_frame(dcx, dcy, drx, dry, rot, 32)
    dim_floor, _ = ell_frame(dcx + 1.1, dcy + 1.9, drx - 0.4, dry - 0.5, rot, 32)
    # line strokes
    sep = arc_where(*ell_frame(cx, cy, rx - 0.3, ry - 0.3, rot, 64, wob), lambda nx, ny: ny > 0.12)
    rim = arc_where(*ell_frame(cx, cy, rx - 2.2, ry - 2.0, rot, 64, wob), lambda nx, ny: nx * -.55 + ny * -.83 > 0.42)
    d_up = arc_where(*ell_frame(dcx, dcy, drx, dry, rot, 48), lambda nx, ny: ny < -0.2)
    d_lo = arc_where(*ell_frame(dcx, dcy, drx + 1.2, dry + 1.1, rot, 48), lambda nx, ny: nx * .4 + ny * .92 > 0.55)

    g = []
    g.append('<path d="%s" fill="#5a1a1c"/>' % smooth_closed(ink))
    g.append('<path d="%s" fill="#c4281f"/>' % smooth_closed(hull))
    g.append('<clipPath id="hull%s"><path d="%s"/></clipPath>' % (uid, smooth_closed(hull)))
    g.append('<clipPath id="top%s"><path d="%s"/></clipPath>' % (uid, smooth_closed(top)))
    g.append('<clipPath id="dim%s"><path d="%s"/></clipPath>' % (uid, smooth_closed(dpts)))
    # deep tone hugging the bottom of the side band
    g.append('<g clip-path="url(#hull%s)"><path d="%s" fill="#a3241c"/></g>' % (
        uid, smooth_closed([(x + 0.6, y + d + 2.2) for (x, y), d in zip(pts, drop)])))
    # top face: base, lower-right shade, upper-left lit crescent
    g.append('<path d="%s" fill="#de3326"/>' % smooth_closed(top))
    g.append('<g clip-path="url(#top%s)">' % uid)
    g.append('  <path d="%s" fill="#f43a2e"/>' % smooth_closed(shade_out))
    g.append('  <path d="%s" fill="#fb5541"/>' % smooth_closed(
        [p for p in ell_frame(cx - 0.4, cy - 0.5, rx, ry, rot, 40, wob)[0]]))
    g.append('  <path d="%s" fill="#f43a2e"/>' % smooth_closed(lit_in))
    g.append('</g>')
    # broad soft sheen on the upper-left of the torus (between rim and dimple)
    sheen = arc_where(*ell_frame(cx - 0.4, cy - 0.6, rx * 0.79, ry * 0.76, rot, 64, wob), lambda nx, ny: nx * -.62 + ny * -.78 > 0.18)
    g.append('<path d="%s" fill="#fd5e49" opacity=".9"/>' % brush(sheen, taper(len(sheen), ry * 0.3, 0.6)))
    # glossless 'paint' streak on the far left of the rim (like environment/disc_cell)
    streak = arc_where(*ell_frame(cx, cy, rx - 3.6, ry - 3.2, rot, 64, wob), lambda nx, ny: nx < -0.86 and ny < 0.2)
    g.append('<path d="%s" fill="#ff9580" opacity=".7"/>' % brush(streak, taper(len(streak), 1.7, 0.4)))
    # dimple: shaded upper wall, flat floor, bright lower lip
    g.append('<path d="%s" fill="#b8271e"/>' % smooth_closed(dpts))
    g.append('<g clip-path="url(#dim%s)"><path d="%s" fill="#e3372a"/></g>' % (uid, smooth_closed(dim_floor)))
    g.append('<path d="%s" fill="#8f2119" opacity=".8"/>' % brush(d_up, taper(len(d_up), 1.5)))
    g.append('<path d="%s" fill="#ff8a72" opacity=".9"/>' % brush(d_lo, taper(len(d_lo), 1.6)))
    # rim highlight + separation line
    g.append('<path d="%s" fill="#ffa08a" opacity=".8"/>' % brush(rim, taper(len(rim), 1.9)))
    g.append('<path d="%s" fill="#8f2119" opacity=".75"/>' % brush(sep, taper(len(sep), 1.4, 0.3)))
    g.append('<path d="%s" fill="#f43a2e" filter="url(#grain)" opacity=".7"/>' % smooth_closed(hull))
    return '\n'.join(g)


def icon_objective():
    W = H = 96
    INK = '#3b2a22'
    GOLD, GOLD_SH, GOLD_HI = '#e2b33c', '#b8862a', '#f6d77c'
    RED, RED_SH, RED_HI = '#a8613a', '#7a4024', '#d39a6e'   # warm wooden grip
    LX, LY = ICON_LENS
    R_OUT, R_IN = ICON_R
    CELL = ICON_CELL
    ang = math.radians(ICON_HANDLE_DEG)
    ux, uy = math.cos(ang), math.sin(ang)
    at = lambda r: (LX + ux * r, LY + uy * r)

    b = []
    defs = []
    # contact shadows on the panel
    b.append('<path d="%s" fill="#463d32" opacity=".2" filter="url(#isoft)"/>' % smooth_closed(ICON_SHADOW_A))
    b.append('<path d="%s" fill="#463d32" opacity=".16" filter="url(#isoft)"/>' % smooth_closed(loop(at(R_OUT + 24)[0] + 1, 87, 8, 2.4, n=10)))
    b.append(red_cell(*CELL, uid='a'))

    # ---- handle (behind the rim): ferrule + red grip, ink first
    h0, h1, h2 = at(R_OUT - 2), at(R_OUT + 6.5), at(R_OUT + 24)
    grip_c = bez(h1, at(R_OUT + 12), at(R_OUT + 18), h2, 12)
    fer_c = bez(h0, at(R_OUT + 1), at(R_OUT + 4), at(R_OUT + 7.5), 6)
    ink_c = bez(h0, at(R_OUT + 8), at(R_OUT + 16), h2, 16)
    b.append('<path d="%s" fill="%s"/>' % (brush([(x + .5, y + .6) for x, y in ink_c], profile(16, 13.6, 15.8, 14.8)), INK))
    b.append('<path d="%s" fill="%s"/>' % (brush(grip_c, profile(12, 9.6, 11.3, 10.6)), RED))
    off = lambda pts, d: [(x - uy * d, y + ux * d) for x, y in pts]
    b.append('<path d="%s" fill="%s"/>' % (brush(off(grip_c, -2.9)[1:], profile(11, 3.6, 4.4, 4.2)), RED_SH))
    b.append('<path d="%s" fill="%s" opacity=".9"/>' % (brush(off(grip_c, 2.6)[2:10], profile(7, 0.8, 0.8, 1.9)), RED_HI))
    b.append('<path d="%s" fill="#f3d2b4" opacity=".8"/>' % smooth_closed(loop(*off([at(R_OUT + 22.2)], 2.2)[0], 1.0, 0.9, n=8)))
    b.append('<path d="%s" fill="%s"/>' % (brush(fer_c, profile(6, 10.8, 11.6)), GOLD))
    b.append('<path d="%s" fill="%s"/>' % (brush(off(fer_c, -3.1), profile(6, 3.2, 3.6)), GOLD_SH))
    for r in (R_OUT + 3.2, R_OUT + 7.4):
        c = at(r)
        p1 = (c[0] - uy * 5.4, c[1] + ux * 5.4)
        p2 = (c[0] + uy * 5.4, c[1] - ux * 5.4)
        b.append('<path d="%s" fill="%s"/>' % (brush(bez(p1, p1, p2, p2, 6), profile(6, 1.6, 1.2)), INK))

    # ---- lens rim
    wob = ((0.006, 3, 0.9), (0.004, 5, 2.0))
    rim_ink = smooth_closed(loop(LX + 0.5, LY + 0.6, R_OUT + 2.4, R_OUT + 2.3, n=16, wob=wob))
    rim = smooth_closed(loop(LX, LY, R_OUT, R_OUT, n=16, wob=wob))
    rim_lit = smooth_closed(loop(LX - 1.3, LY - 1.3, R_OUT - 0.6, R_OUT - 0.6, n=16, wob=wob))
    glass_ink = smooth_closed(loop(LX + 0.25, LY + 0.3, R_IN + 1.5, R_IN + 1.5, n=16, wob=wob))
    glass = smooth_closed(loop(LX, LY, R_IN, R_IN, n=16, wob=wob))
    defs.append('<clipPath id="rim"><path d="%s"/></clipPath>' % rim)
    defs.append('<clipPath id="glass"><path d="%s"/></clipPath>' % glass)
    defs.append('<radialGradient id="gtint" gradientUnits="userSpaceOnUse" cx="%s" cy="%s" r="%s">'
                '<stop offset="0" stop-color="#d6e7f7" stop-opacity=".03"/>'
                '<stop offset=".66" stop-color="#bcd8f2" stop-opacity=".08"/>'
                '<stop offset="1" stop-color="#7aa6d6" stop-opacity=".45"/></radialGradient>' % (f(LX - 2), f(LY - 2), f(R_IN + 2)))
    b.append('<path d="%s" fill="%s"/>' % (rim_ink, INK))
    b.append('<path d="%s" fill="%s"/>' % (rim, GOLD_SH))
    b.append('<g clip-path="url(#rim)"><path d="%s" fill="%s"/></g>' % (rim_lit, GOLD))
    b.append('<path d="%s" fill="%s"/>' % (brush(arc_pts(LX, LY, R_OUT - 2.6, R_OUT - 2.6, 160, 268, 18), profile(18, 0.6, 0.6, 2.4)), GOLD_HI))
    b.append('<path d="%s" fill="#fff4d0" opacity=".9"/>' % brush(arc_pts(LX, LY, R_OUT - 2.4, R_OUT - 2.4, 214, 236, 6), profile(6, 0.5, 0.5, 1.6)))
    b.append('<path d="%s" fill="%s"/>' % (glass_ink, INK))
    # ---- glass: panel seen through it, the magnified cell, then tint + shines
    b.append('<path d="%s" fill="#f9e9d0"/>' % glass)
    b.append('<g clip-path="url(#glass)">')
    b.append('<g transform="translate(%s) scale(%s) translate(%s)">' % (P(LX, LY), f(ICON_MAG), P(-LX, -LY)))
    b.append(red_cell(*CELL, uid='m'))
    b.append('</g>')
    b.append('<path d="%s" fill="url(#gtint)"/>' % glass)
    b.append('<path d="%s" fill="#ffffff" opacity=".85"/>' % brush(arc_pts(LX, LY, R_IN - 4.4, R_IN - 4.4, 194, 252, 16), profile(16, 0.8, 0.9, 3.2)))
    b.append('<path d="%s" fill="#ffffff" opacity=".8"/>' % smooth_closed(loop(LX + (R_IN - 4.4) * math.cos(math.radians(266)), LY + (R_IN - 4.4) * math.sin(math.radians(266)), 1.5, 1.4, n=8)))
    b.append('<path d="%s" fill="#ffffff" opacity=".5"/>' % brush(arc_pts(LX, LY, R_IN - 3.2, R_IN - 3.2, 20, 60, 10), profile(10, 0.5, 0.5, 1.8)))
    b.append('</g>')
    defs.append('<filter id="isoft" x="-10" y="60" width="116" height="50" filterUnits="userSpaceOnUse"><feGaussianBlur stdDeviation="1.5"/></filter>')
    return svg(W, H, '\n'.join(b), '\n'.join(defs))


# ============================================================================= PROGRESS ICON
def icon_progress():
    """Dedicated 64x36 progress-bar marker: the submarine reduced to four readable
    shapes (cream teardrop hull, light-blue dome, red nose ball, small red tail fin),
    no explorer, one cel shade + one highlight per shape, 3 px #3b2a22 outer line and
    ~1.8 px inner separation lines. Faces right like the player sub."""
    W, H = 64, 36
    INK = '#3b2a22'
    OUT = 3.0                      # visible outer line
    IN = 1.8                       # inner separation lines (centred on the shape edge)
    UNDER = 2 * (OUT - IN / 2)     # under-stroke width so outer line = OUT exactly
    HULL, HULL_SH, HULL_HI = '#f2e3d6', '#cdb8aa', '#fffaf3'
    GLASS, GLASS_SH, GLASS_DEEP = '#b9d6f1', '#8db4dd', '#6f98c9'
    RED, RED_SH, RED_HI = '#cf2c43', '#9e1f33', '#f5838c'

    # teardrop: thin tapered tail on the left at mid height, deep blunt front under the dome
    hull_pts = [(3.8, 23.8), (5.9, 20.6), (12.5, 18.4), (26.0, 17.0), (40.0, 16.8), (49.5, 18.4),
                (53.5, 22.8), (51.5, 28.9), (41.0, 32.1), (26.0, 32.1), (13.5, 30.4), (6.0, 27.3)]
    dome_pts = [(17.0, 20.5), (17.6, 13.8), (21.8, 7.6), (29.6, 4.2), (39.0, 3.8), (46.6, 6.6),
                (51.0, 12.0), (52.2, 17.6), (52.0, 21.0), (34.0, 22.0)]
    nose = loop(54.4, 24.6, 6.2, 6.0, n=10, wob=((0.01, 3, 0.5),))
    # swept-back tail fin rising from the top of the tail
    fin = [(8.2, 21.8), (5.6, 16.8), (5.0, 12.8), (6.8, 10.6), (9.8, 11.0), (13.4, 14.2), (16.8, 18.0), (16.6, 21.0)]
    hull = smooth_closed(hull_pts)
    dome = smooth_closed(dome_pts)
    nose_d = smooth_closed(nose)
    fin_d = smooth_closed(fin)

    defs = ('<clipPath id="ph"><path d="%s"/></clipPath>'
            '<clipPath id="pd"><path d="%s"/></clipPath>'
            '<clipPath id="pn"><path d="%s"/></clipPath>'
            '<clipPath id="pf"><path d="%s"/></clipPath>') % (hull, dome, nose_d, fin_d)
    b = []
    # 1. outer line: every part under-stroked so the union gets one even 3 px contour
    b.append('<g fill="%s" stroke="%s" stroke-width="%s" stroke-linejoin="round">' % (INK, INK, f(UNDER)))
    for d in (fin_d, dome, hull, nose_d):
        b.append('  <path d="%s"/>' % d)
    b.append('</g>')
    line = 'stroke="%s" stroke-width="%s" stroke-linejoin="round"' % (INK, f(IN))
    # 2. tail fin (behind the hull)
    b.append('<path d="%s" fill="%s"/>' % (fin_d, RED_SH))
    b.append('<g clip-path="url(#pf)"><path d="%s" fill="%s"/></g>' % (
        smooth_closed([(x - 1.1, y - 1.2) for x, y in fin]), RED))
    b.append('<path d="%s" fill="none" %s/>' % (fin_d, line))
    # 3. dome glass: deep tone at the back-bottom, lit body, shade crescent, specular
    b.append('<path d="%s" fill="%s"/>' % (dome, GLASS_SH))
    b.append('<g clip-path="url(#pd)">')
    b.append('  <path d="%s" fill="%s"/>' % (smooth_closed([(x - 1.6, y - 1.4) for x, y in dome_pts]), GLASS))
    b.append('  <path d="%s" fill="%s" opacity=".7"/>' % (smooth_closed(loop(20.4, 19.2, 6.0, 4.6, n=10)), GLASS_DEEP))
    b.append('</g>')
    b.append('<path d="%s" fill="#ffffff" opacity=".92"/>' % brush(
        smooth_pts([(21.6, 14.2), (23.6, 9.4), (28.4, 6.4)], 10), profile(10, 0.7, 0.6, 2.2)))
    b.append('<path d="%s" fill="#ffffff" opacity=".85"/>' % smooth_closed(loop(32.4, 5.8, 1.1, 1.0, n=8)))
    b.append('<path d="%s" fill="none" %s/>' % (dome, line))
    # 4. hull: cel shade along the belly, lit body, one soft highlight along the top
    b.append('<path d="%s" fill="%s"/>' % (hull, HULL_SH))
    b.append('<g clip-path="url(#ph)">')
    b.append('  <path d="%s" fill="%s"/>' % (smooth_closed([(x - 0.6, y - 3.4) for x, y in hull_pts]), HULL))
    b.append('</g>')
    hi = brush(smooth_pts([(9.0, 21.4), (15.0, 20.1), (23.0, 19.6)], 10), profile(10, 0.6, 0.6, 1.9))
    b.append('<path d="%s" fill="%s" opacity=".95"/>' % (hi, HULL_HI))
    b.append('<path d="%s" fill="none" %s/>' % (hull, line))
    # 5. red nose ball
    b.append('<path d="%s" fill="%s"/>' % (nose_d, RED_SH))
    b.append('<g clip-path="url(#pn)"><path d="%s" fill="%s"/></g>' % (
        smooth_closed([(x - 1.3, y - 1.4) for x, y in nose]), RED))
    b.append('<path d="%s" fill="%s" opacity=".95"/>' % (smooth_closed(loop(52.4, 21.6, 1.7, 1.3, n=8, rot=math.radians(-30))), RED_HI))
    b.append('<path d="%s" fill="none" %s/>' % (nose_d, line))
    return svg(W, H, '\n'.join(b), defs, filters=False)


ICON_LENS = (54.0, 40.5)
ICON_R = (22.5, 17.0)
ICON_CELL = (35.5, 59.0, 28.5, 19.0, -17.0, 3.8)
ICON_MAG = 1.35
ICON_HANDLE_DEG = 56
ICON_SHADOW_A = loop(34, 84, 26, 3.6, n=14)

BADGE_FILL = '#0d1424'
BADGE_R = 45.0

PANEL_BASE = '#fcedd6'
PANEL_INK = '#2e241c'
PANEL_LINE = 3.5
PANEL_R = 24.0
GRAIN_OP = '.35'


ALL = ['panel', 'badge', 'key_e', 'key_space', 'icon_objective', 'icon_progress']

if __name__ == '__main__':
    args = sys.argv[1:]
    if '--out' in args:
        i = args.index('--out')
        OUT = os.path.abspath(args[i + 1])
        del args[i:i + 2]
    for name in args or ALL:
        if name not in ALL:
            sys.exit('unknown asset %r (choose from %s)' % (name, ', '.join(ALL)))
        write(name + '.svg', globals()[name]())
