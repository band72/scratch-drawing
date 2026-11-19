"""Perpendicular offsets from a boundary - the fence/improvement verification.

Generalised from the perp_off()/FENCE_LINE block in jobs/1389/build_dxf.py and
the offset table in jobs/1389/report.py.

Sign convention: positive offset = INSIDE the parcel. Station is measured from
the first corner of the line, along it.
"""
import math

__all__ = ["offset_from_line", "nearest_line", "offset_table", "summarise",
           "RETURN_LEG_FT"]

# Beyond this, a shot is a return leg / cross fence running away from the
# boundary, not a point on the boundary fence. 1389 used 1.8 ft.
RETURN_LEG_FT = 1.8


def offset_from_line(P, a, b):
    """(offset, station) of CAD point P relative to the line a->b.

    offset  + = left of travel a->b.  For a boundary loop walked clockwise,
            left of travel is into the parcel, so + = inside.
    station distance along a->b from a.
    """
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    L = math.hypot(dx, dy)
    if L < 1e-9:
        raise ValueError("degenerate line")
    cross = (P[0] - ax) * dy - (P[1] - ay) * dx
    along = (P[0] - ax) * dx + (P[1] - ay) * dy
    return (-cross / L, along / L)


def nearest_line(P, lines):
    """Pick the line a shot belongs to, by smallest |offset|.

    lines: {name: (a, b)} of CAD corner pairs.
    Returns (name, offset, station).
    """
    best = None
    for name, (a, b) in lines.items():
        o, t = offset_from_line(P, a, b)
        if best is None or abs(o) < abs(best[1]):
            best = (name, o, t)
    return best


def offset_table(pts, order, lines, predicate):
    """Offsets for every shot whose code satisfies predicate, in shot order.

    Returns [{"pt","code","line","offset","station","is_return_leg"}].
    """
    rows = []
    for p in order:
        code = pts[p]["code"]
        if not predicate(code):
            continue
        P = (pts[p]["e"], pts[p]["n"])
        name, o, t = nearest_line(P, lines)
        rows.append({
            "pt": p, "code": code, "line": name,
            "offset": o, "station": t,
            "is_return_leg": abs(o) > RETURN_LEG_FT,
        })
    return rows


def summarise(rows, exclude_return_legs=True):
    """Per-line min/max/mean offset. Return legs excluded by default - they
    are cross fences and would swamp the statistic."""
    by = {}
    for r in rows:
        if exclude_return_legs and r["is_return_leg"]:
            continue
        by.setdefault(r["line"], []).append(r["offset"])
    out = {}
    for name, vs in by.items():
        out[name] = {
            "n": len(vs), "min": min(vs), "max": max(vs),
            "mean": sum(vs) / len(vs),
        }
    return out


def label(offset, decimals=2):
    """The sheet callout: 0.42' IN / 1.60' OUT."""
    return f"{abs(offset):.{decimals}f}' {'IN' if offset >= 0 else 'OUT'}"
