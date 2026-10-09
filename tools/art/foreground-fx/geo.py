"""Small geometry toolkit for hand-designed cartoon SVG shapes (foreground-fx group).

Everything is cubic Beziers: centripetal Catmull-Rom through hand-placed anchors, variable width
ribbons (thick-thin ink lines, rim crescents, brush strokes) built from offset samples.
"""
import math

GRAIN_FILTERS = '''  <filter id="grain" x="0" y="0" width="100%" height="100%" filterUnits="userSpaceOnUse">
    <feTurbulence type="fractalNoise" baseFrequency="0.9 0.6" numOctaves="2" seed="7" stitchTiles="stitch" result="n"/>
    <feColorMatrix in="n" type="matrix" values="0 0 0 0 0.35  0 0 0 0 0.06  0 0 0 0 0.08  0 0 0 0.10 0"/>
    <feComposite in2="SourceGraphic" operator="in"/>
  </filter>
  <filter id="mottle" x="0" y="0" width="100%" height="100%" filterUnits="userSpaceOnUse">
    <feTurbulence type="fractalNoise" baseFrequency="0.008 0.02" numOctaves="3" seed="3" stitchTiles="stitch" result="n"/>
    <feColorMatrix in="n" type="matrix" values="0 0 0 0 0.98  0 0 0 0 0.55  0 0 0 0 0.55  0 0 0 0.16 0"/>
    <feComposite in2="SourceGraphic" operator="in"/>
  </filter>
'''


# Foreground plane texture: the shared grain from ART_DIRECTION.md section 7 plus the lower-saturation
# mottle matrix that far_* and floor_* adopted after the colour-value review (the original pink mottle
# washed the reds out to S .73).  The foreground does not tile, so stitching does not matter here.
FILTERS_FG = '''<filter id="grain" x="0" y="0" width="100%" height="100%" filterUnits="userSpaceOnUse">
<feTurbulence type="fractalNoise" baseFrequency="0.9 0.6" numOctaves="2" seed="7" stitchTiles="stitch" result="n"/>
<feColorMatrix in="n" type="matrix" values="0 0 0 0 0.35  0 0 0 0 0.06  0 0 0 0 0.08  0 0 0 0.10 0"/>
<feComposite in2="SourceGraphic" operator="in"/>
</filter>
<filter id="mottle" x="0" y="0" width="100%" height="100%" filterUnits="userSpaceOnUse">
<feTurbulence type="fractalNoise" baseFrequency="0.008 0.02" numOctaves="3" seed="3" stitchTiles="stitch" result="n"/>
<feColorMatrix in="n" type="matrix" values="0 0 0 0 0.94  0 0 0 0 0.36  0 0 0 0 0.30  0 0 0 0.08 0"/>
<feComposite in2="SourceGraphic" operator="in"/>
</filter>'''


def fmt(v):
    s = f"{v:.1f}"
    if s.endswith('.0'):
        s = s[:-2]
    if s == '-0':
        s = '0'
    return s


def P(p):
    return f"{fmt(p[0])} {fmt(p[1])}"


def add(a, b):
    return (a[0] + b[0], a[1] + b[1])


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1])


def mul(a, k):
    return (a[0] * k, a[1] * k)


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1]


def length(a):
    return math.hypot(a[0], a[1])


def unit(a):
    l = math.hypot(a[0], a[1]) or 1e-9
    return (a[0] / l, a[1] / l)


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def smoothstep(e0, e1, x):
    if e0 == e1:
        return 1.0 if x >= e1 else 0.0
    t = clamp((x - e0) / (e1 - e0))
    return t * t * (3 - 2 * t)


def rot(p, ang, c=(0, 0)):
    s, co = math.sin(ang), math.cos(ang)
    x, y = p[0] - c[0], p[1] - c[1]
    return (c[0] + x * co - y * s, c[1] + x * s + y * co)


# ------------------------------------------------------------------ Catmull-Rom -> cubic Bezier
def _cr(p0, p1, p2, p3, alpha=0.5):
    d1 = length(sub(p1, p0)) ** alpha
    d2 = length(sub(p2, p1)) ** alpha
    d3 = length(sub(p3, p2)) ** alpha
    eps = 1e-6
    if d2 < eps:
        return (p1, p1, p2, p2)
    if d1 < eps:
        c1 = lerp(p1, p2, 1 / 3)
    else:
        a = d1 * d1
        b = d2 * d2
        k = 2 * a + 3 * d1 * d2 + b
        den = 3 * d1 * (d1 + d2)
        c1 = ((a * p2[0] - b * p0[0] + k * p1[0]) / den, (a * p2[1] - b * p0[1] + k * p1[1]) / den)
    if d3 < eps:
        c2 = lerp(p2, p1, 1 / 3)
    else:
        a = d3 * d3
        b = d2 * d2
        k = 2 * a + 3 * d3 * d2 + b
        den = 3 * d3 * (d3 + d2)
        c2 = ((a * p1[0] - b * p3[0] + k * p2[0]) / den, (a * p1[1] - b * p3[1] + k * p2[1]) / den)
    return (p1, c1, c2, p2)


def spline(pts, closed=False, phantoms=False):
    """Segments through pts.  open+phantoms: first/last points only steer the end tangents.
    open without phantoms: end neighbours are reflected."""
    pts = list(pts)
    segs = []
    if closed:
        n = len(pts)
        for i in range(n):
            segs.append(_cr(pts[i - 1], pts[i], pts[(i + 1) % n], pts[(i + 2) % n]))
        return segs
    if not phantoms:
        if len(pts) == 2:
            return [(pts[0], lerp(pts[0], pts[1], 1 / 3), lerp(pts[0], pts[1], 2 / 3), pts[1])]
        pts = [sub(mul(pts[0], 2), pts[1])] + pts + [sub(mul(pts[-1], 2), pts[-2])]
    for i in range(1, len(pts) - 2):
        segs.append(_cr(pts[i - 1], pts[i], pts[i + 1], pts[i + 2]))
    return segs


def bez(s, t):
    p0, c1, c2, p3 = s
    mt = 1 - t
    a, b, c, d = mt * mt * mt, 3 * mt * mt * t, 3 * mt * t * t, t * t * t
    return (a * p0[0] + b * c1[0] + c * c2[0] + d * p3[0], a * p0[1] + b * c1[1] + c * c2[1] + d * p3[1])


def bezd(s, t):
    p0, c1, c2, p3 = s
    mt = 1 - t
    a, b, c = 3 * mt * mt, 6 * mt * t, 3 * t * t
    return (a * (c1[0] - p0[0]) + b * (c2[0] - c1[0]) + c * (p3[0] - c2[0]),
            a * (c1[1] - p0[1]) + b * (c2[1] - c1[1]) + c * (p3[1] - c2[1]))


def seg_len(s):
    n = 12
    L = 0
    prev = s[0]
    for i in range(1, n + 1):
        q = bez(s, i / n)
        L += length(sub(q, prev))
        prev = q
    return L


def sample(segs, step=3.0):
    """List of (point, unit tangent).  Continuous along the whole chain."""
    out = []
    for si, s in enumerate(segs):
        n = max(2, int(math.ceil(seg_len(s) / step)))
        for i in range(0 if si == 0 else 1, n + 1):
            t = i / n
            d = bezd(s, t)
            if length(d) < 1e-6:
                d = bezd(s, min(1, max(0, t + (0.01 if t < 0.5 else -0.01))))
            out.append((bez(s, t), unit(d)))
    return out


def d_segs(segs, move=True, close=False):
    out = []
    if move:
        out.append('M' + P(segs[0][0]))
    for (_, c1, c2, p) in segs:
        out.append('C' + P(c1) + ' ' + P(c2) + ' ' + P(p))
    if close:
        out.append('Z')
    return ''.join(out)


def d_closed(pts):
    return d_segs(spline(pts, closed=True), close=True)


def d_poly(pts, close=True):
    s = 'M' + 'L'.join(P(p) for p in pts)
    return s + ('Z' if close else '')


def decimate(seq, every):
    if every <= 1 or len(seq) < 4:
        return list(seq)
    out = seq[::every]
    if out[-1] is not seq[-1]:
        out.append(seq[-1])
    return out


def ribbon_d(pts, normals, widths, bias=0.5, every=2):
    """Closed filled ribbon. bias = fraction of width put on the -normal (inner) side."""
    idx = list(range(len(pts)))
    idx = decimate(idx, every)
    outer = [add(pts[i], mul(normals[i], widths[i] * (1 - bias))) for i in idx]
    inner = [sub(pts[i], mul(normals[i], widths[i] * bias)) for i in idx]
    if len(outer) < 2:
        return ''
    a = spline(outer)
    b = spline(inner[::-1])
    return d_segs(a) + 'L' + P(inner[-1]) + d_segs(b, move=False) + 'Z'


def runs(widths, thr=0.25):
    res = []
    start = None
    for i, w in enumerate(widths):
        if w > thr and start is None:
            start = i
        elif w <= thr and start is not None:
            if i - start >= 3:
                res.append((start, i))
            start = None
    if start is not None and len(widths) - start >= 3:
        res.append((start, len(widths)))
    return res


def ribbon_runs(pts, normals, widths, bias=0.5, every=2, thr=0.25):
    ds = []
    for a, b in runs(widths, thr):
        ds.append(ribbon_d(pts[a:b], normals[a:b], widths[a:b], bias, every))
    return ''.join(ds)


def pip(pt, poly):
    x, y = pt
    inside = False
    n = len(poly)
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y):
            xin = (xj - xi) * (y - yi) / ((yj - yi) or 1e-9) + xi
            if x < xin:
                inside = not inside
        j = i
    return inside


def min_dist(pt, pts):
    return min(length(sub(pt, q)) for q in pts)


def stroke_along(points, wmax, power=0.8, bias=0.5, every=1, profile=None):
    """Brush stroke following a polyline: tapered at both ends."""
    if len(points) < 3:
        return ''
    # normals from neighbours
    nrm = []
    for i in range(len(points)):
        a = points[max(0, i - 1)]
        b = points[min(len(points) - 1, i + 1)]
        t = unit(sub(b, a))
        nrm.append((t[1], -t[0]))
    n = len(points)
    ws = []
    for i in range(n):
        s = i / (n - 1)
        if profile:
            ws.append(wmax * profile(s))
        else:
            ws.append(wmax * (math.sin(math.pi * s) ** power))
    return ribbon_d(points, nrm, ws, bias, every)


def ellipse_pts(c, rx, ry, ang=0.0, n=8, wobble=None, start=0.0):
    pts = []
    for i in range(n):
        a = start + 2 * math.pi * i / n
        k = 1.0 if wobble is None else wobble[i % len(wobble)]
        p = (c[0] + math.cos(a) * rx * k, c[1] + math.sin(a) * ry * k)
        pts.append(rot(p, ang, c))
    return pts
