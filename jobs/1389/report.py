#!/usr/bin/env python3
"""Fence / boundary / building verification report for job 1389."""
import math, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import geom

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
pts, order = geom.read_points(os.path.join(ROOT, geom.PTFILE))
F = geom.Frame(pts); C = F.C
LINES = {"FRONT (Toucan)": ("SE", "NE"), "NORTH SIDE": ("NE", "NW"),
         "REAR": ("NW", "SW"), "SOUTH SIDE": ("SW", "SE")}
# the plat calls FRONT and REAR in the opposite direction to the loop:
FLIP = {"FRONT (Toucan)", "REAR"}
REC = {"FRONT (Toucan)": ("S 06°47'00\" W", 85.0),
       "NORTH SIDE": ("N 83°12'52\" W", 140.0),
       "REAR": ("N 06°47'08\" E", 85.0),
       "SOUTH SIDE": ("S 83°12'52\" E", 140.0)}

def off(P, a, b):
    ax, ay = C[a]; bx, by = C[b]
    dx, dy = bx - ax, by - ay; L = math.hypot(dx, dy)
    return (-((P[0]-ax)*dy - (P[1]-ay)*dx)/L, ((P[0]-ax)*dx + (P[1]-ay)*dy)/L)

W = 78
def hdr(t): print("\n" + t); print("-" * W)

print("=" * W)
print("JOB 1389  -  12418 TOUCAN DR, JACKSONVILLE FL 32223")
print("LOT 8, BLOCK 7, JULINGTON HILLS UNIT TWO  (PB 28, PGS 35, 35A, 35B)")
print("RE# 159326-0000   Field work 03/31/26   Prior survey Tri-State 2-22-00")
print("Florida East (0901) NAD83, US survey feet")
print("=" * W)

hdr("1. BOUNDARY  -  measured between the four found 1/2\" iron pipes")
print(f"{'LINE':<16}{'RECORD':<22}{'REC':>8}{'MEASURED':>22}{'MEAS':>9}{'D':>7}")
for nm, (a, b) in LINES.items():
    pa, pb = C[a], C[b]
    rb, rd = REC[nm]; md = geom.dist(pa, pb)
    mb = geom.bearing(pb, pa) if nm in FLIP else geom.bearing(pa, pb)
    print(f"{nm:<16}{rb:<22}{rd:>8.2f}{mb:>22}{md:>9.2f}{md-rd:>7.2f}")
print("\nFound monuments: pt 1 = SE, pt 4 = NE, pt 3 = NW, pt 2 = SW  (all FIP 1/2\" NO-ID)")
print("Grid bearings run ~0 deg 07' clockwise of the platted bearings.")

hdr("2. BUILDING  -  2026 corner shots vs the 2000 survey, in the parcel frame")
print("   (x = from the SOUTH line, y = depth from the FRONT line)")
EXP = {"69": ("house rear-S corner", 12.1, 78.5),
       "70": ("house rear-N corner", 75.1, 78.5),
       "71": ("house front-N corner", 75.1, 25.7)}
print(f"{'PT':>4}  {'DESCRIPTION':<24}{'MEAS x':>9}{'MEAS y':>9}{'2000 x':>9}{'2000 y':>9}{'dx':>7}{'dy':>7}")
for p, (d, ex, ey) in EXP.items():
    x, y = F.inv(pts[p]["e"], pts[p]["n"])
    print(f"{p:>4}  {d:<24}{x:>9.2f}{y:>9.2f}{ex:>9.2f}{ey:>9.2f}{x-ex:>7.2f}{y-ey:>7.2f}")
print("\nThe 2000 house dimension chain (62.8/38.8/24.8/15.3/7.5/3.0/7.8/26.4/22.9/52.8)")
print("closes to 0.2 ft and the three 2026 corners fall on it within 0.33 ft, so the")
print("prior survey and the new field work are on the same building.")

hdr("3. FENCES  -  perpendicular offset from the measured boundary")
print("   codes  F0 line / F1 end / F2 corner / F3 gate  -  W wood, P PVC")
print(f"{'PT':>4} {'CODE':<10}{'LINE':<14}{'OFFSET':>9}  {'SIDE':<5}{'STATION':>9}  NOTE")
FR = re.compile(r"^F\d+-")
CTL = {"0": "line", "1": "end", "2": "corner", "3": "GATE"}
rows = {}
for p in order:
    c = pts[p]["code"]
    if not FR.match(c):
        continue
    P = (pts[p]["e"], pts[p]["n"])
    nm, (a, b) = min(LINES.items(), key=lambda kv: abs(off(P, *kv[1])[0]))
    o, t = off(P, a, b)
    note = CTL.get(c[1], "")
    if abs(o) > 1.8:
        note += "  <-- RETURN LEG / off-line"
    print(f"{p:>4} {c:<10}{nm:<14}{abs(o):>8.2f}' {'IN ' if o>=0 else 'OUT':<5}{t:>9.2f}  {note}")
    rows.setdefault(nm, []).append(o)

hdr("4. SUMMARY BY LINE  (main-run points only, returns excluded)")
for nm, vs in rows.items():
    m = [v for v in vs if abs(v) <= 1.8]
    if not m: continue
    print(f"{nm:<14} n={len(m):<3} min {min(m):+.2f}'  max {max(m):+.2f}'  "
          f"mean {sum(m)/len(m):+.2f}'   (+ = inside the lot)")

hdr("5. FINDINGS")
for s in [
 "a. No fence encroaches materially. Every main-run shot is within 1.6 ft of the",
 "   line it follows, which is normal post-setting tolerance for a 1970s-80s fence.",
 "b. NORTH side: the fence sits just INSIDE the lot, +0.45 to +1.31 ft, for the",
 "   first 78 ft of depth, then crosses to 0.06-0.25 ft OUTSIDE near the rear",
 "   corner (pts 72, 73). Two parallel runs - 6' wood and 6' PVC - about 1 ft apart.",
 "c. SOUTH side: the fence is consistently OUTSIDE the lot, on the Lot 9 side, by",
 "   0.10 to 1.60 ft the full length. It is the neighbour's fence or a shared fence",
 "   set off the line; it does not take land from Lot 8.",
 "d. REAR: on line, +0.16 to +0.65 ft inside. The 2000 survey annotated 0.1' and",
 "   0.3' at the rear corners, so the rear fence has not moved measurably in 26 yrs.",
 "e. Two shots are return legs, not boundary fence: pt 60 (2.01' out, north) and",
 "   pt 89 (4.39' out, south). Both are cross fences running away from the lot.",
 "f. The north fence now runs to 19.9 ft from the front line (pt 57, 4' wood); the",
 "   2000 survey showed it stopping about 41 ft back. The fence was extended.",
 "g. The alum. shed shown in 2000 at the rear-south corner of the house is gone.",
 "   A plastic shed on a wood floor (pts 75-77) now sits in the rear-south corner,",
 "   4-9 ft off the rear line and 8-15 ft off the south line.",
 "h. The driveway has been reworked: in 2000 it met the front line between 55.8 and",
 "   75.1 ft from the south line; in 2026 it meets it between about 52 and 71 ft.",
 "i. The rear 7.5 ft of the lot lies in the 15 ft drainage & utility easement whose",
 "   centreline is the rear lot line. The rear fence stands inside that easement.",
]:
    print(s)
print()
