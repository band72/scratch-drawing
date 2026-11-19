"""Local parcel frame: express geometry the way a surveyor reads a sheet.

Generalised from jobs/1389/geom.py:Frame, which hardcoded job 1389's corner
point numbers. Here the corners are passed in.

    origin  = the reference corner
    +x      = along the front line, toward the far front corner
    +y      = perpendicular into the lot

So a point is (distance along the front, depth into the lot), and L() converts
it to CAD (X=Easting, Y=Northing). Every prior-survey dimension, setback and
offset in job 1389 is written in this frame; it is also what makes the paper
space viewport rotation fall out for free.
"""
import math

from .cogo import azimuth, bearing, dist

__all__ = ["Frame"]


class Frame:
    """A right-handed local frame on a parcel's front line.

    corners: {"SE": (x, y), "NE": ..., "NW": ..., "SW": ...} in CAD order,
             or any four labels - `origin` and `front_to` name which two
             define the front line.
    """

    def __init__(self, corners, origin="SE", front_to="NE"):
        if origin not in corners or front_to not in corners:
            raise KeyError(
                f"origin {origin!r} and front_to {front_to!r} must be in "
                f"corners {sorted(corners)}"
            )
        self.C = dict(corners)
        self.origin_key = origin
        self.front_to_key = front_to
        o = corners[origin]
        f = corners[front_to]
        dx, dy = f[0] - o[0], f[1] - o[1]
        L = math.hypot(dx, dy)
        if L < 1e-9:
            raise ValueError("origin and front_to are the same point")
        self.o = o
        self.u = (dx / L, dy / L)          # along the front
        self.v = (-dy / L, dx / L)         # into the lot
        self.front_len = L

    # ------------------------------------------------------------ transforms
    def L(self, x, y):
        """local (along-front, depth) -> CAD (X=E, Y=N)"""
        return (self.o[0] + x * self.u[0] + y * self.v[0],
                self.o[1] + x * self.u[1] + y * self.v[1])

    def Lp(self, poly):
        """Map a whole polyline of local points."""
        return [self.L(*p) for p in poly]

    def inv(self, X, Y):
        """CAD (X, Y) -> local (along-front, depth)"""
        dx, dy = X - self.o[0], Y - self.o[1]
        return (dx * self.u[0] + dy * self.u[1],
                dx * self.v[0] + dy * self.v[1])

    # --------------------------------------------------------------- helpers
    @property
    def rotation_deg(self):
        """Rotation of local +x in CAD, degrees CCW from +X. Paper space
        viewport twist is (360 - this) % 360."""
        return math.degrees(math.atan2(self.u[1], self.u[0]))

    def viewport_twist(self):
        """view_twist_angle that puts the front line along the bottom."""
        return (360.0 - self.rotation_deg) % 360.0

    def depth_sign_check(self, interior_point):
        """True if +y points into the lot. Pass any point known to be inside;
        a parcel built with the frame inverted is the classic silent failure."""
        return self.inv(*interior_point)[1] > 0

    @classmethod
    def from_points(cls, pts, corner_pt, origin="SE", front_to="NE"):
        """Build from a point file dict plus {"SE": "1", "NE": "4", ...}."""
        corners = {k: (pts[v]["e"], pts[v]["n"]) for k, v in corner_pt.items()}
        return cls(corners, origin=origin, front_to=front_to)

    def side(self, a, b):
        """(bearing, distance) of the measured line between two corner keys."""
        pa, pb = self.C[a], self.C[b]
        return bearing(pa, pb), dist(pa, pb)

    def sides(self, loop):
        """[(name, bearing, distance)] around a loop of corner keys."""
        out = []
        for a, b in zip(loop, loop[1:] + loop[:1]):
            br, d = self.side(a, b)
            out.append((f"{a}-{b}", br, d))
        return out
