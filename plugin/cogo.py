"""Survey math for scratch-drawing, backed by the Boundary.IQ engine.

Why this module exists at all: the engine works in survey order, Point(n, e),
while the CAD code here works in drawing order, (X=Easting, Y=Northing) plain
tuples. Mixing the two silently transposes a parcel. Every conversion between
them happens here and nowhere else.

    engine : Point(n, e)        - survey / State Plane order
    CAD    : (x, y) = (e, n)    - drawing order, what ezdxf gets

Re-exported from the engine unchanged (do not reimplement these):
    parse_bearing, try_parse_bearing, azimuth_to_bearing
    Point, Course, run_traverse, closure_report, bowditch_balance
    Curve, solve_curve_all_parameters, solve_missing, verify_curve_consistency
"""
import math
import re

from .engine_link import ensure_on_path

ensure_on_path()

from engine.cogo import (  # noqa: E402
    Course,
    Point,
    azimuth_to_bearing,
    bowditch_balance,
    closure_report,
    parse_bearing,
    run_traverse,
    try_parse_bearing,
)
from engine.curves import (  # noqa: E402
    Curve,
    solve_curve_all_parameters,
    solve_missing,
    verify_curve_consistency,
)

__all__ = [
    "parse_bearing", "try_parse_bearing", "azimuth_to_bearing",
    "Point", "Course", "run_traverse", "closure_report", "bowditch_balance",
    "Curve", "solve_curve_all_parameters", "solve_missing",
    "verify_curve_consistency",
    "to_cad", "to_survey", "azimuth", "bearing", "dist",
]


# ---------------------------------------------------------------- conversion
def to_cad(p):
    """engine Point(n, e) -> CAD (x, y)."""
    return (p.e, p.n)


def to_survey(xy):
    """CAD (x, y) -> engine Point(n, e)."""
    return Point(xy[1], xy[0])


# ------------------------------------------------------- CAD-order shorthands
def azimuth(p, q):
    """Azimuth from CAD point p to q, in decimal degrees (0 = North, CW)."""
    return math.degrees(math.atan2(q[0] - p[0], q[1] - p[1])) % 360.0


def bearing(p, q, cardinal=False, seconds_decimals=0):
    """Quadrant bearing from CAD point p to q.

    Delegates the formatting to the engine's azimuth_to_bearing, which rounds
    in DMS space before formatting. The obvious implementation - rounding
    degrees, minutes and seconds independently - emits impossible strings like
    N 00°03' 60" E. jobs/1389/geom.py:bearing() does exactly that, on roughly
    1% of azimuths; use this instead.

    seconds_decimals=0 gives the whole-second form the sheets use.
    """
    s = azimuth_to_bearing(azimuth(p, q), cardinal=cardinal)
    if cardinal and s.startswith("DUE"):
        return s
    if seconds_decimals == 2:
        return s
    # engine emits N00°03'59.76"E; re-round seconds in DMS space, not in text.
    m = re.match(r"^([NS])(\d{2})°(\d{2})'([\d.]+)\"([EW])$", s)
    if not m:
        return s
    ns, d, mn, sec, ew = m.groups()
    total = round((int(d) * 3600) + (int(mn) * 60) + float(sec))
    d2, rem = divmod(total, 3600)
    m2, s2 = divmod(rem, 60)
    return f"{ns} {d2:02d}°{m2:02d}' {s2:02d}\" {ew}"


def dist(p, q):
    """Distance between two CAD points."""
    return math.hypot(q[0] - p[0], q[1] - p[1])
