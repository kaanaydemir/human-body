"""Tiny inking library: turns hand-authored cubic-Bezier contours into
thick-thin brush outlines (filled ribbons) for SVG cartoon art.

Only absolute M / L / C / Z commands are supported in authored paths.
"""
import math
import re

_TOK = re.compile(r'[MLCZ]|-?\d*\.?\d+(?:e-?\d+)?')


def parse(d):
    toks = _TOK.findall(d)
    subs = []
    cur = None
    last = None
    cmd = None
    i = 0
    while i < len(toks):
        t = toks[i]
        if t in 'MLCZ':
            cmd = t
            i += 1
            if cmd == 'Z':
                cur['closed'] = True
            continue
        if cmd == 'M':
            p = (float(toks[i]), float(toks[i + 1]))
            i += 2
            cur = {'start': p, 'segs': [], 'closed': False}
            subs.append(cur)
            last = p
            cmd = 'L'
        elif cmd == 'L':
            p = (float(toks[i]), float(toks[i + 1]))
            i += 2
            cur['segs'].append(('L', last, p))
            last = p
        elif cmd == 'C':
            v = [float(x) for x in toks[i:i + 6]]
            i += 6
            p = (v[4], v[5])
            cur['segs'].append(('C', last, (v[0], v[1]), (v[2], v[3]), p))
            last = p
        else:
            raise ValueError('bad path ' + d)
    return subs


def _bez(p0, p1, p2, p3, t):
    u = 1 - t
    return (u * u * u * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t * t * t * p3[0],
            u * u * u * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t * t * t * p3[1])


def dense(sub, n=60):
    pts = [sub['start']]
    for s in sub['segs']:
        if s[0] == 'L':
            a, b = s[1], s[2]
            for k in range(1, n + 1):
                t = k / n
                pts.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
        else:
            for k in range(1, n + 1):
                pts.append(_bez(s[1], s[2], s[3], s[4], k / n))
    if sub['closed']:
        a, b = pts[-1], pts[0]
        if math.hypot(b[0] - a[0], b[1] - a[1]) > 0.01:
            for k in range(1, n + 1):
                t = k / n
                pts.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
        pts.pop()  # last == first
    return pts


def resample(pts, step, closed):
    seq = pts + [pts[0]] if closed else pts
    acc = [0.0]
    for i in range(1, len(seq)):
        acc.append(acc[-1] + math.hypot(seq[i][0] - seq[i - 1][0], seq[i][1] - seq[i - 1][1]))
    L = acc[-1]
    n = max(4, int(round(L / step)))
    out = []
    j = 0
    rng = range(n) if closed else range(n + 1)
    for k in rng:
        s = L * k / n
        while j < len(acc) - 2 and acc[j + 1] < s:
            j += 1
        seg = acc[j + 1] - acc[j]
        t = 0 if seg == 0 else (s - acc[j]) / seg
        a, b = seq[j], seq[j + 1]
        out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
    return out, L


def poly(d, step=3.0):
    """Polygon (list of points) for the first closed subpath of d."""
    sub = parse(d)[0]
    pts, _ = resample(dense(sub), step, True)
    return pts


def inside(pt, pg):
    x, y = pt
    c = False
    n = len(pg)
    j = n - 1
    for i in range(n):
        xi, yi = pg[i]
        xj, yj = pg[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi:
            c = not c
        j = i
    return c


def _f(v):
    s = '%.1f' % v
    if s.endswith('.0'):
        s = s[:-2]
    if s == '-0':
        s = '0'
    return s


def smooth(pts, closed):
    """Catmull-Rom -> cubic Bezier path string."""
    n = len(pts)
    if n < 2:
        return ''
    o = ['M%s %s' % (_f(pts[0][0]), _f(pts[0][1]))]
    rng = range(n) if closed else range(n - 1)
    for i in rng:
        p0 = pts[(i - 1) % n] if closed else pts[max(i - 1, 0)]
        p1 = pts[i % n]
        p2 = pts[(i + 1) % n] if closed else pts[i + 1]
        p3 = pts[(i + 2) % n] if closed else pts[min(i + 2, n - 1)]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        o.append('C%s %s %s %s %s %s' % (_f(c1[0]), _f(c1[1]), _f(c2[0]), _f(c2[1]), _f(p2[0]), _f(p2[1])))
    if closed:
        o.append('Z')
    return ''.join(o)


def _smoothstep(a, b, x):
    t = min(1, max(0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


SHADOW_DIR = (0.36, 0.93)  # light comes from the upper left


def ink_closed(d, wmin, wmax, step=3.0, wobble=0.10, phase=0.0, inner_polys=None,
               inner_factor=0.55, shadow_dir=SHADOW_DIR, gap_lit=False):
    """Thick-thin outline ribbon of a closed contour.

    Width follows the light: thin where the outward normal faces the light,
    thick on the shadow side.  Edges whose outside lies on another part of the
    object (inner_polys) are drawn thinner (inner_factor).
    """
    sub = parse(d)[0]
    pts, L = resample(dense(sub), step, True)
    n = len(pts)
    # tangent & left normal
    nor = []
    for i in range(n):
        a = pts[(i - 1) % n]
        b = pts[(i + 1) % n]
        tx, ty = b[0] - a[0], b[1] - a[1]
        l = math.hypot(tx, ty) or 1
        nor.append((ty / l, -tx / l))
    # orient outward: majority vote
    votes = 0
    for i in range(0, n, max(1, n // 24)):
        q = (pts[i][0] + nor[i][0] * 0.8, pts[i][1] + nor[i][1] * 0.8)
        votes += -1 if inside(q, pts) else 1
    if votes < 0:
        nor = [(-x, -y) for x, y in nor]
    ws = []
    for i in range(n):
        dd = nor[i][0] * shadow_dir[0] + nor[i][1] * shadow_dir[1]
        t = _smoothstep(-0.45, 0.85, dd)
        w = wmin + (wmax - wmin) * t
        s = i * L / n
        w *= 1 + wobble * (0.6 * math.sin(s / 17.0 + phase) + 0.4 * math.sin(s / 7.3 + phase * 2.1))
        if inner_polys:
            q = (pts[i][0] + nor[i][0] * 5, pts[i][1] + nor[i][1] * 5)
            if any(inside(q, pg) for pg in inner_polys):
                w *= inner_factor
        if gap_lit and dd < -0.82:
            w *= 0.35
        ws.append(max(w, 0.25))
    # smooth widths a little (avoid steps from inner test)
    for _ in range(3):
        ws = [(ws[(i - 1) % n] + 2 * ws[i] + ws[(i + 1) % n]) / 4 for i in range(n)]
    outer = [(pts[i][0] + nor[i][0] * ws[i] / 2, pts[i][1] + nor[i][1] * ws[i] / 2) for i in range(n)]
    inner = [(pts[i][0] - nor[i][0] * ws[i] / 2, pts[i][1] - nor[i][1] * ws[i] / 2) for i in range(n)]
    return smooth(outer, True) + smooth(inner[::-1], True)


def ink_open(d, w, step=2.5, taper=(0.18, 0.18), wobble=0.08, phase=0.0, wend=0.25, profile=None):
    """Brush stroke along an open path with tapered ends."""
    out = []
    for sub in parse(d):
        pts, L = resample(dense(sub), step, False)
        n = len(pts)
        if n < 3:
            continue
        lefts, rights = [], []
        for i in range(n):
            a = pts[max(i - 1, 0)]
            b = pts[min(i + 1, n - 1)]
            tx, ty = b[0] - a[0], b[1] - a[1]
            l = math.hypot(tx, ty) or 1
            nx, ny = ty / l, -tx / l
            t = i / (n - 1)
            if profile:
                k = profile(t)
            else:
                k = 1.0
                if taper[0] > 0 and t < taper[0]:
                    k *= math.sin(t / taper[0] * math.pi / 2) ** 0.8
                if taper[1] > 0 and t > 1 - taper[1]:
                    k *= math.sin((1 - t) / taper[1] * math.pi / 2) ** 0.8
            s = t * L
            ww = w * k * (1 + wobble * math.sin(s / 11.0 + phase))
            ww = max(ww, wend)
            lefts.append((pts[i][0] + nx * ww / 2, pts[i][1] + ny * ww / 2))
            rights.append((pts[i][0] - nx * ww / 2, pts[i][1] - ny * ww / 2))
        out.append(smooth(lefts + rights[::-1], True))
    return ''.join(out)


def offset_curve(d, dist, step=3.0):
    """Points of a closed contour pushed inward (dist>0) along the normal."""
    sub = parse(d)[0]
    pts, L = resample(dense(sub), step, True)
    n = len(pts)
    nor = []
    for i in range(n):
        a = pts[(i - 1) % n]
        b = pts[(i + 1) % n]
        tx, ty = b[0] - a[0], b[1] - a[1]
        l = math.hypot(tx, ty) or 1
        nor.append((ty / l, -tx / l))
    votes = 0
    for i in range(0, n, max(1, n // 24)):
        q = (pts[i][0] + nor[i][0] * 0.8, pts[i][1] + nor[i][1] * 0.8)
        votes += -1 if inside(q, pts) else 1
    if votes < 0:
        nor = [(-x, -y) for x, y in nor]
    return [(pts[i][0] - nor[i][0] * dist, pts[i][1] - nor[i][1] * dist) for i in range(n)]


def sub_path(d, t0, t1, step=2.0):
    """Open polyline path string covering the fraction [t0,t1] of a closed contour's length
    (wraps around if t0 > t1)."""
    sub = parse(d)[0]
    pts, L = resample(dense(sub), step, True)
    n = len(pts)
    i0 = int(t0 * n)
    i1 = int(t1 * n)
    if i1 <= i0:
        i1 += n
    seg = [pts[i % n] for i in range(i0, i1 + 1)]
    return smooth(seg, False)


def pts_path(pts, closed=False):
    return smooth(pts, closed)
