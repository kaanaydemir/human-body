# Geometry helpers for the hand-designed ceiling generator (stdlib only).
# Everything is cubic Bezier / Catmull-Rom based so the output reads as brushed, organic line work.
import math


def fmt(v):
    s = f"{v:.1f}"
    if s.endswith('.0'):
        s = s[:-2]
    if s in ('-0', '-0.0'):
        s = '0'
    return s


def cubic_pt(p0, p1, p2, p3, t):
    mt = 1 - t
    a = mt * mt * mt
    b = 3 * mt * mt * t
    c = 3 * mt * t * t
    d = t * t * t
    return (a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0],
            a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1])


class N:
    """Contour node: position, incoming/outgoing tangent angle (deg, y down) and optional handle lengths."""

    def __init__(self, x, y, a=0.0, b=None, li=None, lo=None, cusp=False):
        self.x, self.y = x, y
        self.ain = a
        self.aout = a if b is None else b
        self.li, self.lo = li, lo
        self.cusp = cusp


def nodes_to_segs(nodes, k=0.4):
    segs = []
    for i in range(len(nodes) - 1):
        n0, n1 = nodes[i], nodes[i + 1]
        ch = math.hypot(n1.x - n0.x, n1.y - n0.y)
        lo = n0.lo if n0.lo is not None else k * ch
        li = n1.li if n1.li is not None else k * ch
        ao, ai = math.radians(n0.aout), math.radians(n1.ain)
        p0 = (n0.x, n0.y)
        p1 = (n0.x + lo * math.cos(ao), n0.y + lo * math.sin(ao))
        p2 = (n1.x - li * math.cos(ai), n1.y - li * math.sin(ai))
        p3 = (n1.x, n1.y)
        segs.append((p0, p1, p2, p3))
    return segs


def segs_to_d(segs, move=True):
    out = []
    if move:
        out.append(f"M{fmt(segs[0][0][0])} {fmt(segs[0][0][1])}")
    for (p0, p1, p2, p3) in segs:
        out.append(f"C{fmt(p1[0])} {fmt(p1[1])} {fmt(p2[0])} {fmt(p2[1])} {fmt(p3[0])} {fmt(p3[1])}")
    return ''.join(out)


def resample(dense, step):
    out = [dense[0]]
    acc = 0.0
    prev = dense[0]
    for p in dense[1:]:
        d = math.hypot(p[0] - prev[0], p[1] - prev[1])
        while acc + d >= step and d > 0:
            t = (step - acc) / d
            q = (prev[0] + (p[0] - prev[0]) * t, prev[1] + (p[1] - prev[1]) * t)
            out.append(q)
            d = math.hypot(p[0] - q[0], p[1] - q[1])
            prev = q
            acc = 0.0
        acc += d
        prev = p
    if math.hypot(out[-1][0] - dense[-1][0], out[-1][1] - dense[-1][1]) > step * 0.3:
        out.append(dense[-1])
    else:
        out[-1] = dense[-1]
    return out


def sample_segs(segs, step=3.0, reverse=False):
    dense = []
    for s in segs:
        approx = sum(math.hypot(s[i + 1][0] - s[i][0], s[i + 1][1] - s[i][1]) for i in range(3))
        n = max(10, int(approx / 0.5))
        for k in range(n):
            dense.append(cubic_pt(*s, k / n))
    dense.append(segs[-1][3])
    if reverse:
        dense.reverse()
    return resample(dense, step)


def cr_open_dense(pts, per=12):
    """Dense samples of an open Catmull-Rom spline through pts."""
    out = []
    n = len(pts)
    for i in range(n - 1):
        p0 = pts[i - 1] if i > 0 else pts[i]
        p1 = pts[i]
        p2 = pts[i + 1]
        p3 = pts[i + 2] if i + 2 < n else pts[i + 1]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        L = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
        m = max(per, int(L / 0.6))
        for k in range(m):
            out.append(cubic_pt(p1, c1, c2, p2, k / m))
    out.append(pts[-1])
    return out


def curve(pts, step=3.0):
    return resample(cr_open_dense(pts), step)


def normals(pts):
    ns = []
    n = len(pts)
    for i in range(n):
        a = pts[max(0, i - 1)]
        b = pts[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy) or 1.0
        ns.append((dy / L, -dx / L))
    return ns


def tangents(pts):
    out = []
    n = len(pts)
    for i in range(n):
        a = pts[max(0, i - 1)]
        b = pts[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy) or 1.0
        out.append((dx / L, dy / L))
    return out


def ribbon_poly(pts, prof):
    """prof(u, p) -> (a, b): offset along +normal (left of travel, 'up' for a left->right curve) and along -normal."""
    ns = normals(pts)
    n = len(pts)
    L, R = [], []
    for i, (p, nn) in enumerate(zip(pts, ns)):
        u = i / (n - 1) if n > 1 else 0
        a, b = prof(u, p)
        L.append((p[0] + nn[0] * a, p[1] + nn[1] * a))
        R.append((p[0] - nn[0] * b, p[1] - nn[1] * b))
    return L, R


def _dedupe(pts, eps=0.15):
    out = []
    for p in pts:
        if not out or math.hypot(p[0] - out[-1][0], p[1] - out[-1][1]) > eps:
            out.append(p)
    if len(out) > 2 and math.hypot(out[0][0] - out[-1][0], out[0][1] - out[-1][1]) <= eps:
        out.pop()
    return out


def cr_closed_d(pts):
    pts = _dedupe(pts)
    n = len(pts)
    if n < 3:
        return ''
    d = [f"M{fmt(pts[0][0])} {fmt(pts[0][1])}"]
    for i in range(n):
        p0 = pts[i - 1]
        p1 = pts[i]
        p2 = pts[(i + 1) % n]
        p3 = pts[(i + 2) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d.append(f"C{fmt(c1[0])} {fmt(c1[1])} {fmt(c2[0])} {fmt(c2[1])} {fmt(p2[0])} {fmt(p2[1])}")
    d.append('Z')
    return ''.join(d)


def thin(pts, k):
    if k <= 1:
        return list(pts)
    out = pts[::k]
    if out[-1] != pts[-1]:
        out.append(pts[-1])
    return out


def ribbon_d(pts, prof, k=2, blunt=False):
    """Closed brush-stroke path around pts. k = keep every k-th sample for the output spline."""
    L, R = ribbon_poly(pts, prof)
    if k == 2 and len(pts) > 90:   # long smooth ribbons: a vertex every ~12px is plenty for the spline
        k = 4
    L = thin(L, k)
    R = thin(R, k)
    poly = L + R[::-1]
    return cr_closed_d(poly)


def sub_range(pts, u0, u1):
    n = len(pts)
    i0 = max(0, int(round(u0 * (n - 1))))
    i1 = min(n - 1, int(round(u1 * (n - 1))))
    return pts[i0:i1 + 1]


def smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def bell(u, peak=0.5, p=1.0):
    """0 at u=0 and u=1, 1 at u=peak; smooth, skewable."""
    if u <= 0 or u >= 1:
        return 0.0
    if u < peak:
        t = u / peak
    else:
        t = (1 - u) / (1 - peak)
    return math.sin(t * math.pi / 2) ** p


def blob_d(cx, cy, rx, ry, rot, rng, jitter=0.12, n=9):
    pts = []
    c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    ph = rng.random() * 6.28
    for i in range(n):
        a = 2 * math.pi * i / n
        r = 1 + jitter * (rng.random() * 2 - 1) + 0.05 * math.sin(2 * a + ph)
        x = math.cos(a) * rx * r
        y = math.sin(a) * ry * r
        pts.append((cx + x * c - y * s, cy + x * s + y * c))
    return cr_closed_d(pts)


# ---------------------------------------------------------------- parametric splines (v2)
# A curve is a Catmull-Rom spline through hand-placed control points. cr_param() keeps, for every resampled
# vertex, the fractional control-point index s (segment i + local t), so per-control-point values (band
# thickness, ink width, ...) can be interpolated along the curve with at().


def cr_param(pts, step=2.0):
    n = len(pts)
    dense = []
    for i in range(n - 1):
        p0 = pts[i - 1] if i > 0 else pts[i]
        p1 = pts[i]
        p2 = pts[i + 1]
        p3 = pts[i + 2] if i + 2 < n else pts[i + 1]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        L = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
        m = max(8, int(L / 0.4))
        for k in range(m):
            x, y = cubic_pt(p1, c1, c2, p2, k / m)
            dense.append((x, y, i + k / m))
    dense.append((pts[-1][0], pts[-1][1], float(n - 1)))
    out = [dense[0]]
    acc = 0.0
    for a, b in zip(dense, dense[1:]):
        acc += math.hypot(b[0] - a[0], b[1] - a[1])
        if acc >= step:
            out.append(b)
            acc = 0.0
    if out[-1] is not dense[-1]:
        if math.hypot(out[-1][0] - dense[-1][0], out[-1][1] - dense[-1][1]) < step * 0.4:
            out[-1] = dense[-1]
        else:
            out.append(dense[-1])
    return out


def at(vals, s):
    """Value of a per-control-point list at fractional index s (smoothstep between neighbours)."""
    if isinstance(vals, (int, float)):
        return float(vals)
    n = len(vals) - 1
    if s <= 0:
        return float(vals[0])
    if s >= n:
        return float(vals[n])
    i = int(s)
    t = s - i
    t = t * t * (3 - 2 * t)
    return vals[i] * (1 - t) + vals[i + 1] * t


def snormals(samples):
    """Unit normals of a sampled curve: left of travel (up for a left->right curve, y down)."""
    out = []
    n = len(samples)
    for i in range(n):
        a = samples[max(0, i - 2)]
        b = samples[min(n - 1, i + 2)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy) or 1.0
        out.append((dy / L, -dx / L))
    return out


def band_poly(samples, fa, fb):
    """fa(s, x, y) / fb(s, x, y): offsets along +normal and -normal. Returns the closed outline polygon."""
    ns = snormals(samples)
    L, R = [], []
    for (x, y, s), (nx, ny) in zip(samples, ns):
        a = fa(s, x, y)
        b = fb(s, x, y)
        L.append((x + nx * a, y + ny * a))
        R.append((x - nx * b, y - ny * b))
    return L + R[::-1]


def poly_d(poly, k=3):
    """Smooth closed path through every k-th vertex of a dense polygon."""
    if len(poly) > 3 * k:
        poly = poly[::k]
    return cr_closed_d(poly)


def lin_d(poly):
    """Closed polyline path (for dense polygons that must match an edge exactly)."""
    if not poly:
        return ''
    o = [f"M{fmt(poly[0][0])} {fmt(poly[0][1])}"]
    for p in poly[1:]:
        o.append(f"L{fmt(p[0])} {fmt(p[1])}")
    o.append('Z')
    return ''.join(o)
