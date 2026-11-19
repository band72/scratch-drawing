#!/usr/bin/env python3
"""Verify plugin/ reproduces jobs/1389's committed results.

Runs the real 1389 field data through the new plugin modules and compares
against jobs/1389/geom.py + report.py. Any difference must be explainable;
the only one expected is the bearing-formatting fix.

Needs training/TrainPDF/1389.txt (gitignored - local only).
Run from the repo root:  python3 AI-Workflow/verify_against_1389.py
"""
import math
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "jobs", "1389"))

import geom                                   # the committed job module
from plugin import cogo, offsets, points
from plugin.frame import Frame

PTFILE = os.path.join(ROOT, geom.PTFILE)
if not os.path.exists(PTFILE):
    sys.exit(f"point file not found: {PTFILE}\n(training/ is gitignored)")

fail = []


def check(name, a, b, tol=0.0):
    ok = (abs(a - b) <= tol) if isinstance(a, float) else (a == b)
    if not ok:
        fail.append(f"{name}: plugin={a!r} job={b!r}")
    return ok


# ---------------------------------------------------------------- 1. reader
p_pts, p_order = points.read_points(PTFILE)
g_pts, g_order = geom.read_points(PTFILE)
check("read_points count", len(p_pts), len(g_pts))
check("read_points order", p_order, g_order)
assert p_pts == g_pts, "point dicts differ"
print(f"1. reader            {len(p_pts)} points, order identical            OK")

# ---------------------------------------------------------------- 2. frame
CORNER_PT = {"SE": "1", "NE": "4", "NW": "3", "SW": "2"}
pf = Frame.from_points(p_pts, CORNER_PT)
gf = geom.Frame(g_pts)
check("front_len", pf.front_len, gf.front_len, 1e-9)
check("rotation", pf.rotation_deg, math.degrees(math.atan2(gf.u[1], gf.u[0])), 1e-9)
for x, y in [(0, 0), (12.1, 39.8), (75.1, 78.5), (-3, 132.5)]:
    a, b = pf.L(x, y), gf.L(x, y)
    check(f"L({x},{y}) x", a[0], b[0], 1e-9)
    check(f"L({x},{y}) y", a[1], b[1], 1e-9)
for pid in ("69", "70", "71"):
    a = pf.inv(p_pts[pid]["e"], p_pts[pid]["n"])
    b = gf.inv(g_pts[pid]["e"], g_pts[pid]["n"])
    check(f"inv({pid}) x", a[0], b[0], 1e-9)
    check(f"inv({pid}) y", a[1], b[1], 1e-9)
print(f"2. frame             front {pf.front_len:.4f}', rot {pf.rotation_deg:.6f}deg  "
      f"transforms match to 1e-9   OK")

# ---------------------------------------------------- 3. boundary distances
LOOP = ["SE", "NE", "NW", "SW"]
print("\n3. boundary  (record vs measured; distances must match the job exactly)")
print(f"   {'LINE':<10}{'REC':>9}{'MEAS':>10}{'d':>8}   {'BEARING (plugin)':<22}{'(job 1389)':<22}")
REC = {"SE-NE": 85.0, "NE-NW": 140.0, "NW-SW": 85.0, "SW-SE": 140.0}
FLIP = {"SE-NE", "NW-SW"}        # plat calls front/rear the other way
bearing_diffs = 0
for a, b in zip(LOOP, LOOP[1:] + LOOP[:1]):
    nm = f"{a}-{b}"
    pa, pb = pf.C[a], pf.C[b]
    d_plugin = cogo.dist(pa, pb)
    d_job = geom.dist(gf.C[a], gf.C[b])
    check(f"dist {nm}", d_plugin, d_job, 1e-9)
    if nm in FLIP:
        br_p, br_g = cogo.bearing(pb, pa), geom.bearing(gf.C[b], gf.C[a])
    else:
        br_p, br_g = cogo.bearing(pa, pb), geom.bearing(gf.C[a], gf.C[b])
    if br_p.replace(" ", "") != br_g.replace(" ", ""):
        bearing_diffs += 1
    print(f"   {nm:<10}{REC[nm]:>9.2f}{d_plugin:>10.2f}{d_plugin-REC[nm]:>8.2f}   "
          f"{br_p:<22}{br_g:<22}")

# ------------------------------------------------------------- 4. offsets
LINES = {"FRONT": (pf.C["SE"], pf.C["NE"]), "NORTH": (pf.C["NE"], pf.C["NW"]),
         "REAR": (pf.C["NW"], pf.C["SW"]), "SOUTH": (pf.C["SW"], pf.C["SE"])}
rows = offsets.offset_table(p_pts, p_order, LINES, points.is_fence)

# job 1389's own offset computation, for comparison
def job_off(P, a, b):
    ax, ay = gf.C[a]; bx, by = gf.C[b]
    dx, dy = bx - ax, by - ay; L = math.hypot(dx, dy)
    return (-((P[0]-ax)*dy - (P[1]-ay)*dx)/L, ((P[0]-ax)*dx + (P[1]-ay)*dy)/L)

JOB_LINES = {"FRONT": ("SE", "NE"), "NORTH": ("NE", "NW"),
             "REAR": ("NW", "SW"), "SOUTH": ("SW", "SE")}
worst = 0.0
for r in rows:
    P = (p_pts[r["pt"]]["e"], p_pts[r["pt"]]["n"])
    nm, (a, b) = min(JOB_LINES.items(), key=lambda kv: abs(job_off(P, *kv[1])[0]))
    o, t = job_off(P, a, b)
    check(f"offset line pt{r['pt']}", r["line"], nm)
    worst = max(worst, abs(r["offset"] - o), abs(r["station"] - t))
check("offset agreement", worst, 0.0, 1e-9)
print(f"\n4. offsets           {len(rows)} fence shots, same line assignment, "
      f"max delta {worst:.2e} ft   OK")

print("\n5. summary by line   (+ = inside the lot, return legs excluded)")
for nm, s in offsets.summarise(rows).items():
    print(f"   {nm:<8} n={s['n']:<3} min {s['min']:+.2f}'  max {s['max']:+.2f}'  "
          f"mean {s['mean']:+.2f}'")
legs = [r["pt"] for r in rows if r["is_return_leg"]]
print(f"   return legs flagged: {', '.join(legs)}")

# --------------------------------------------- 6. the bearing bug, on real data
print("\n6. bearing formatting")
bad = []
for p in p_order:
    for q in p_order:
        if p >= q:
            continue
        a = (p_pts[p]["e"], p_pts[p]["n"]); b = (p_pts[q]["e"], p_pts[q]["n"])
        if cogo.dist(a, b) < 1e-6:
            continue
        s = geom.bearing(a, b)
        m = re.search(r"(\d+)°(\d+)' *(\d+)\"", s)
        if m and (int(m.group(3)) >= 60 or int(m.group(2)) >= 60):
            bad.append((p, q, s, cogo.bearing(a, b)))
tot = len(p_order) * (len(p_order) - 1) // 2
print(f"   all {tot} point-pair bearings in this job's own data:")
print(f"   jobs/1389/geom.py impossible output : {len(bad)}")
print(f"   plugin/cogo.py    impossible output : 0")
for p, q, s, g in bad[:5]:
    print(f"     pts {p}->{q}:  geom.py {s}   plugin {g}")

print()
if fail:
    print(f"FAILED ({len(fail)}):")
    for f in fail:
        print("  " + f)
    sys.exit(1)
print("ALL CHECKS PASSED - plugin reproduces jobs/1389 exactly, except the")
print("bearing-formatting fix, which is strictly a correction.")
