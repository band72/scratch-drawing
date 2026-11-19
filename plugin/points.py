"""Field point files and the firm's field-code vocabulary.

The engine has no equivalent: it starts from deed/plat calls, while this starts
from a total-station point file. Format is P,N,E,Z,code - the same shape the
1389 and 1496 jobs both read.

Field code key (confirmed across 1389 and 1496):

    F<control>-<height>-<material>
        control   0 line   1 end   2 corner   3 gate
        material  W wood   P PVC/vinyl   C chain link

A bare F3 (gate, no height/material) occurs in 1496. Material C was discovered
on 1496 and is not in the 1389 key - see jobs/1496/score.txt.
"""
import re

__all__ = ["read_points", "FenceCode", "parse_fence_code", "CONTROL", "MATERIAL",
           "is_fence", "is_found_monument", "group_by_code"]

CONTROL = {"0": "line", "1": "end", "2": "corner", "3": "gate"}
MATERIAL = {"W": "wood", "P": "PVC/vinyl", "C": "chain link"}

_FENCE_RE = re.compile(r"^F(?P<ctl>\d)(?:-(?P<h>[\d.]+)?(?:-(?P<mat>[A-Z]))?)?$", re.I)


def read_points(path):
    """Read a P,N,E,Z,code point file.

    Returns (pts, order):
        pts   {id: {"n","e","z","code"}}
        order [id, ...] in file order - shot order, which is the only
              connectivity hint a point file carries.
    """
    pts, order = {}, []
    with open(path) as fh:
        for line in fh:
            f = line.strip().split(",")
            if len(f) < 4 or not f[0]:
                continue
            pts[f[0]] = dict(
                n=float(f[1]), e=float(f[2]), z=float(f[3]),
                code=(f[4].strip() if len(f) > 4 else ""),
            )
            order.append(f[0])
    return pts, order


def xy(pts, pid):
    """CAD (x, y) for a point id."""
    return (pts[pid]["e"], pts[pid]["n"])


class FenceCode:
    """A parsed F-code. Falsy if the code is not a fence code."""

    __slots__ = ("raw", "control", "height", "material")

    def __init__(self, raw, control=None, height=None, material=None):
        self.raw = raw
        self.control = control
        self.height = height
        self.material = material

    def __bool__(self):
        return self.control is not None

    @property
    def control_name(self):
        return CONTROL.get(self.control)

    @property
    def material_name(self):
        return MATERIAL.get(self.material) if self.material else None

    @property
    def is_gate(self):
        return self.control == "3"

    def __repr__(self):
        if not self:
            return f"FenceCode({self.raw!r}, not a fence)"
        h = f"{self.height}'" if self.height else "-"
        return (f"FenceCode({self.raw!r}, {self.control_name}, {h}, "
                f"{self.material_name or '-'})")


def parse_fence_code(code):
    """Parse an F-code into a FenceCode. Unknown codes return a falsy one."""
    m = _FENCE_RE.match((code or "").strip())
    if not m:
        return FenceCode(code)
    g = m.groupdict()
    mat = (g["mat"] or "").upper() or None
    if mat and mat not in MATERIAL:
        # unknown material letter: keep it, flag by having no material_name
        pass
    return FenceCode(code, g["ctl"], g["h"], mat)


def is_fence(code):
    return bool(parse_fence_code(code))


def is_found_monument(code):
    """FIP / FIR / XCUT / FCM and friends - a recovered monument."""
    c = (code or "").upper()
    return c.startswith(("FIP", "FIR", "FCM", "XCUT", "FN"))


def group_by_code(pts, order, predicate):
    """[(id, code)] in shot order for points whose code satisfies predicate."""
    return [(p, pts[p]["code"]) for p in order if predicate(pts[p]["code"])]


def unknown_codes(pts, order, known):
    """Codes present in the file that aren't fence codes, monuments, or in
    `known`. Surfaces vocabulary drift - 1496 turned up BOC0/BOC2, CB, TRB."""
    out = {}
    for p in order:
        c = pts[p]["code"]
        if not c or is_fence(c) or is_found_monument(c):
            continue
        base = c.split("-")[0]
        if base in known or c in known:
            continue
        out.setdefault(c, []).append(p)
    return out
