#!/usr/bin/env python3
"""Build 1389.dxf - prior survey (Tri-State 2-22-00) reproduced on the measured
boundary, with the 1389.txt field work overlaid for fence verification."""
import math, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import ezdxf
from ezdxf.addons.importer import Importer
import geom
from geom import bearing, dist

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SEED = os.path.join(ROOT, "training", "dxf",
                    "010225.01 3RD ST-BOUNDARY-FINAL-R1.dxf")
OUT  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "1389.dxf")

SCALE = 20.0            # 1" = 20'
TH    = lambda inches: round(inches * SCALE, 3)   # text height in model units

# ---------------------------------------------------------------- document
src = ezdxf.readfile(SEED)
doc = ezdxf.new("R2018", setup=True)
doc.header["$INSUNITS"] = 2          # feet
doc.header["$LUNITS"], doc.header["$LUPREC"] = 2, 2
doc.header["$AUNITS"], doc.header["$AUPREC"] = 0, 4
imp = Importer(src, doc)
imp.import_tables()                  # firm layers / linetypes / text styles
imp.finalize()

msp = doc.modelspace()

EXTRA = [("V-1389-PNTS", 1), ("V-1389-FENCE", 3), ("V-1389-IMPR", 30),
         ("V-1389-TEXT", 2), ("V-COMPARE", 6)]
for name, col in EXTRA:
    if name not in doc.layers:
        doc.layers.add(name, color=col)
for name in ("PL", "ELINE", "STL", "BLDG", "CONC", "FENCES", "TEXT",
             "BLDGTEXT", "BRGTXT", "PLTEXT", "SYM", "PNTS", "ADJ", "TITLE"):
    if name not in doc.layers:
        doc.layers.add(name)

def add(kind, layer, **kw):
    kw.setdefault("dxfattribs", {})["layer"] = layer
    return getattr(msp, kind)(**kw)

def line(a, b, layer, lt=None):
    at = {"layer": layer}
    if lt: at["linetype"] = lt
    return msp.add_line(a, b, dxfattribs=at)

def poly(pts, layer, close=True, lt=None):
    at = {"layer": layer}
    if lt: at["linetype"] = lt
    return msp.add_lwpolyline(pts, close=close, dxfattribs=at)

def text(s, pos, h, layer, rot=0.0, align="MIDDLE_CENTER", style="ROMANS"):
    st = style if style in doc.styles else "Standard"
    t = msp.add_text(s, height=h, rotation=rot,
                     dxfattribs={"layer": layer, "style": st})
    t.set_placement(pos, align=ezdxf.enums.TextEntityAlignment[align])
    return t

# ---------------------------------------------------------------- data
pts, order = geom.read_points(os.path.join(ROOT, geom.PTFILE))
F = geom.Frame(pts)
L, Lp = F.L, F.Lp
C = F.C
ang = lambda: math.degrees(math.atan2(F.u[1], F.u[0]))   # rotation of local +x

# =============================== BOUNDARY (measured - hold the four pipes)
bnd = [C["SE"], C["NE"], C["NW"], C["SW"]]
poly(bnd, "PL", close=True)

SIDES = [("SE", "NE", "FRONT"), ("NE", "NW", "NORTH"),
         ("NW", "SW", "REAR"),  ("SW", "SE", "SOUTH")]
REC = {"FRONT": ("S 06°47' 00\" W", "85.00'"),
       "NORTH": ("N 83°12' 52\" W", "140.00'"),
       "REAR":  ("N 06°47' 08\" E", "85.00'"),
       "SOUTH": ("S 83°12' 52\" E", "140.00'")}

# =============================== 15' DRAINAGE & UTILITY EASEMENT (c/l = rear)
poly(Lp([(-3, geom.LOT_DEPTH - geom.ESMT_HALF),
         (geom.LOT_WIDTH + 3, geom.LOT_DEPTH - geom.ESMT_HALF)]),
     "ELINE", close=False, lt="DASHED")
poly(Lp([(-3, geom.LOT_DEPTH + geom.ESMT_HALF),
         (geom.LOT_WIDTH + 3, geom.LOT_DEPTH + geom.ESMT_HALF)]),
     "ELINE", close=False, lt="DASHED")
text("℄ 15' DRAIN & UTLY ESM'T", L(30, geom.LOT_DEPTH - 4.8),
     TH(0.10), "PLTEXT", rot=ang())

# =============================== 25' B.R.L.
poly(Lp([(-6, geom.BRL), (geom.LOT_WIDTH + 6, geom.BRL)]),
     "STL", close=False, lt="DASHED")
text("25'",   L(30, geom.BRL + 1.6), TH(0.10), "PLTEXT", rot=ang())
text("B.R.L.", L(30, geom.BRL - 2.2), TH(0.10), "PLTEXT", rot=ang())

# =============================== BUILDING + IMPROVEMENTS
poly(Lp(geom.HOUSE), "BLDG")
poly(Lp(geom.WOOD_DECK), "BLDG")
poly(Lp(geom.DIRT), "BLDG")
poly(Lp(geom.SCREEN_PORCH), "BLDG")
poly(Lp(geom.ALUM_SHED), "BLDG")
for p, lay in ((geom.PATIO_CONC, "CONC"), (geom.AC_PAD, "CONC"),
               (geom.DRIVE, "CONC"), (geom.WALK, "CONC")):
    poly(Lp(p), lay)
    h = msp.add_hatch(color=254, dxfattribs={"layer": "HATCHC"
                      if "HATCHC" in doc.layers else "CONC"})
    h.set_pattern_fill("AR-SAND", scale=0.35)
    h.paths.add_polyline_path(Lp(p), is_closed=True)

for s, xy, rot in [("1 STY BRICK &", (43, 72), 0), ("WOOD  #12418", (43, 67), 0),
                   ("SCREEN", (48, 84), 0), ("PORCH", (48, 80.5), 0),
                   ("ALUM.", (6.5, 84), 0), ("SHED", (6.5, 80.5), 0),
                   ("DIRT", (40.6, 53.6), 0), ("WOOD DECK", (40.6, 46), 90)]:
    text(s, L(*xy), TH(0.09), "BLDGTEXT", rot=ang() + rot)

# =============================== PRIOR-SURVEY DIMENSION ANNOTATION
DIMS = [("12.1'", (6.0, 76.0), 0), ("12.1'", (6.0, 41.5), 0),
        ("62.8'", (29.0, 76.3), 0), ("38.8'", (10.3, 59.0), 90),
        ("24.8'", (24.5, 37.6), 0), ("15.3'", (35.0, 47.5), 90),
        ("7.5'",  (40.6, 57.0), 0), ("3.0",  (45.9, 53.6), 90),
        ("7.8'",  (49.0, 54.8), 0), ("26.4'", (53.9, 39.0), 90),
        ("22.9'", (63.5, 27.4), 0), ("52.8'", (73.4, 52.0), 90),
        ("9.9'",  (80.0, 27.4), 0), ("25.6'", (80.0, 12.8), 90),
        ("39.8'", (10.3, 20.0), 90), ("0.1'", (-2.4, 136.0), 90),
        ("0.3'",  (79.0, 44.0), 90)]
for s, xy, rot in DIMS:
    text(s, L(*xy), TH(0.09), "TEXT", rot=ang() + rot)

# front setback / side tie witness lines
line(L(12.1, 0), L(12.1, 39.8), "TEXT", lt="DASHED")
line(L(0, 0), L(-57.63, 0), "TEXT")
text("57.63'", L(-22.0, 1.6), TH(0.10), "TEXT", rot=ang())

# =============================== PRIOR-SURVEY FENCE (x-x-x on the lines)
def fence_sym(a, b, layer, lt, step=6.0):
    poly([a, b], layer, close=False, lt=lt)

for a, b in [(L(0, geom.LOT_DEPTH - .6), L(geom.LOT_WIDTH, geom.LOT_DEPTH - .6)),
             (L(.6, geom.LOT_DEPTH), L(.6, 0.0)),
             (L(geom.LOT_WIDTH - .6, geom.LOT_DEPTH), L(geom.LOT_WIDTH - .6, 41.0))]:
    fence_sym(a, b, "FENCES", "FENCELINE1")

# =============================== ADJOINERS / STREET
for s, xy in [("21", (12, 145.2)), ("22", (44, 145.2)), ("23", (76, 145.2)),
              ("9", (-14, 70)), ("7", (99, 70))]:
    text(s, L(*xy), TH(0.14), "ADJ", rot=ang())
text("TOUCAN      (60' R/W)      DRIVE", L(42, -6.8), TH(0.13), "TEXT", rot=ang())

# =============================== BEARING & DISTANCE LABELS (record + meas.)
for a, b, nm in SIDES:
    pa, pb = C[a], C[b]
    mid = ((pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2)
    la, lb = F.inv(*pa), F.inv(*pb)
    lmid = ((la[0] + lb[0]) / 2, (la[1] + lb[1]) / 2)
    nx, ny = (pb[1] - pa[1]), -(pb[0] - pa[0])
    nl = math.hypot(nx, ny); nx, ny = nx / nl, ny / nl
    sgn = 1          # right-hand normal of the CW loop -> always outside
    rb, rd = REC[nm]
    rot = math.degrees(math.atan2(pb[1] - pa[1], pb[0] - pa[0]))
    if 90 < rot % 360 < 270: rot += 180
    off = 3.2 * sgn
    text(f"{rb}      {rd}", (mid[0] + nx * off, mid[1] + ny * off),
         TH(0.11), "BRGTXT", rot=rot)
    mb = bearing(pb, pa) if nm in ("FRONT", "REAR") else bearing(pa, pb)
    text(f"(M) {mb}   {dist(pa, pb):.2f}'",      # inside, clear of sheet furniture
         (mid[0] - nx * 3.6, mid[1] - ny * 3.6),
         TH(0.085), "V-COMPARE", rot=rot)

# =============================== 1389 FIELD POINTS
PSIZE = 0.9
for p in order:
    d = pts[p]
    if not d["code"]:
        continue
    X, Y = d["e"], d["n"]
    lay = "PNTS" if not d["code"].startswith("FIP") else "SYM"
    msp.add_circle((X, Y), PSIZE * 0.45, dxfattribs={"layer": lay})
    line((X - PSIZE, Y), (X + PSIZE, Y), lay)
    line((X, Y - PSIZE), (X, Y + PSIZE), lay)
    text(f"{p}  {d['code']}", (X + 1.6, Y + 1.1), TH(0.065),
         "V-1389-TEXT", align="MIDDLE_LEFT")
    text(f"{d['z']:.2f}", (X + 1.6, Y - 1.1), TH(0.055),
         "V-1389-TEXT", align="MIDDLE_LEFT")

# =============================== 1389 FENCE LINEWORK
#  F0 = line   F1 = end   F2 = corner   F3 = gate      W = wood   P = PVC/vinyl
RUNS = [
    ("N LINE 6' WOOD",      "WF", ["58", "61", "62", "63", "72"]),
    ("N LINE 6' PVC",       "VF", ["59", "64", "73", "74"]),
    ("N LINE PVC RETURN",   "VF", ["59", "60"]),
    ("REAR 6' WOOD",        "WF", ["80", "79"]),
    ("S LINE 6' WOOD",      "WF", ["82", "81", "78", "85", "86"]),
    ("S LINE 6' WOOD (fwd)","WF", ["87", "88"]),
    ("S LINE WOOD JOG",     "WF", ["83", "84"]),
    ("S LINE WOOD RETURN",  "WF", ["88", "89"]),
]
GATE = {"61", "78", "81"}        # F3
# A gate needs two shots to define its opening, so only the segment BETWEEN
# two consecutive F3 points is left open; a lone F3 is labelled and drawn through.
for name, lt, ids in RUNS:
    co = [(pts[i]["e"], pts[i]["n"]) for i in ids]
    lt2 = lt if lt in doc.linetypes else "FENCELINE1"
    for i in range(len(co) - 1):
        if ids[i] in GATE and ids[i + 1] in GATE:
            continue                      # gate opening
        poly([co[i], co[i + 1]], "V-1389-FENCE", close=False, lt=lt2)
    if len(co) < 2:
        continue
    j = len(co) // 2
    a, b = co[j - 1], co[j]
    mx_, my_ = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    dx_, dy_ = b[0] - a[0], b[1] - a[1]
    nl_ = math.hypot(dx_, dy_) or 1.0
    ox, oy = dy_ / nl_ * 5.0, -dx_ / nl_ * 5.0
    rot_ = math.degrees(math.atan2(dy_, dx_))
    if 90 < rot_ % 360 < 270:
        rot_ += 180
    text(name, (mx_ + ox, my_ + oy), TH(0.065), "V-1389-FENCE", rot=rot_)
for g in GATE:
    text("GATE", (pts[g]["e"], pts[g]["n"] + 2.4), TH(0.07),
         "V-1389-FENCE", rot=ang(), align="MIDDLE_CENTER")

# =============================== FENCE OFFSET CALLOUTS
def perp_off(P, a, b):
    ax, ay = C[a]; bx, by = C[b]
    dx, dy = bx - ax, by - ay; Ln = math.hypot(dx, dy)
    s = ((P[0] - ax) * dy - (P[1] - ay) * dx) / Ln
    t = ((P[0] - ax) * dx + (P[1] - ay) * dy) / Ln
    return -s, t          # + = inside the lot

FENCE_RE = re.compile(r"^F\d+-")
FENCE_LINE = {}
for p in order:
    if not FENCE_RE.match(pts[p]["code"]):
        continue
    P = (pts[p]["e"], pts[p]["n"])
    best = min((("FRONT", "SE", "NE"), ("NORTH", "NE", "NW"),
                ("REAR", "NW", "SW"), ("SOUTH", "SW", "SE")),
               key=lambda s: abs(perp_off(P, s[1], s[2])[0]))
    o, t = perp_off(P, best[1], best[2])
    FENCE_LINE[p] = (best[0], o, t)
    tag = f"{abs(o):.2f}' {'IN' if o >= 0 else 'OUT'}"
    text(tag, (P[0], P[1] - 2.6), TH(0.065), "V-COMPARE",
         rot=ang(), align="MIDDLE_CENTER")

# =============================== MEASURED IMPROVEMENTS FROM 1389
GROUPS = [("EBC", [str(i) for i in range(30, 42)]),
          ("SEP", ["67", "68", "66", "65"]),
          ("SHD", ["75", "76", "77"])]
for nm, ids in GROUPS:
    ids = [i for i in ids if i in pts]
    poly([(pts[i]["e"], pts[i]["n"]) for i in ids], "V-1389-IMPR", close=False)
poly([(pts[i]["e"], pts[i]["n"]) for i in ["47", "46", "45"]],
     "V-1389-IMPR", close=False)
poly([(pts[i]["e"], pts[i]["n"]) for i in ["48", "49"]],
     "V-1389-IMPR", close=False)
for i in ["69", "70", "71"]:
    msp.add_circle((pts[i]["e"], pts[i]["n"]), 1.4,
                   dxfattribs={"layer": "V-1389-IMPR"})

# ============================================================== PAPER SHEET
# Reproduction of the Tri-State Land Surveyors sheet, 8.5 x 11 portrait,
# model viewport at 1" = 20'.
psp = doc.layout("Layout1")
psp.page_setup(size=(8.5, 11.0), margins=(0, 0, 0, 0), units="inch")
for nm, col in (("Tblock", 7), ("TXT-TITLE-NOTES", 7), ("ViewPort", 7)):
    if nm not in doc.layers:
        doc.layers.add(nm, color=col)

def pl(pts, layer="Tblock", close=False, lw=None):
    e = psp.add_lwpolyline(pts, close=close, dxfattribs={"layer": layer})
    if lw: e.dxf.const_width = lw
    return e

def pt_(s, pos, h, align="MIDDLE_CENTER", layer="TXT-TITLE-NOTES", rot=0.0):
    st = "ROMANS" if "ROMANS" in doc.styles else "Standard"
    t = psp.add_text(s, height=h, rotation=rot,
                     dxfattribs={"layer": layer, "style": st})
    t.set_placement(pos, align=ezdxf.enums.TextEntityAlignment[align])
    return t

BL, BR, BB, BT = 0.25, 8.25, 0.25, 10.75
pl([(BL, BB), (BR, BB), (BR, BT), (BL, BT)], close=True, lw=0.02)

# ---- title block -------------------------------------------------------
pt_("MAP SHOWING BOUNDARY SURVEY OF", (4.25, 10.50), 0.160)
pt_("LOT   8        BLOCK   7        AS SHOWN ON MAP OF", (4.25, 10.28), 0.110)
pt_("JULINGTON HILLS UNIT TWO", (4.25, 10.09), 0.110)
pt_("AS RECORDED IN PLAT BOOK 28, PAGES 35-35B OF THE PUBLIC RECORDS OF DUVAL, COUNTY, FLORIDA",
    (4.25, 9.93), 0.070)
pt_("CERTIFIED FOR:  GLEN & CHARLENE AYERS;  ESTATE TITLE & TRUST;  FIRST AMERICAN",
    (0.60, 9.79), 0.078, align="MIDDLE_LEFT")
pt_("TITLE INS. CO.;  NORWEST MORTGAGE INC.", (1.60, 9.67), 0.078,
    align="MIDDLE_LEFT")
for y in (10.37, 9.60):
    pl([(BL, y), (BR, y)])

# ---- viewport ----------------------------------------------------------
VW, VH = 7.40, 7.82
VCX, VCY = 4.25, 5.69
mx, my = F.L(42.5, 70.0)
vp = psp.add_viewport(center=(VCX, VCY), size=(VW, VH),
                      view_center_point=(mx, my), view_height=VH * SCALE)
vp.dxf.view_twist_angle = (360.0 - ang()) % 360.0   # Toucan Dr to the bottom
vp.dxf.layer = "ViewPort"
pl([(VCX - VW / 2, VCY - VH / 2), (VCX + VW / 2, VCY - VH / 2),
    (VCX + VW / 2, VCY + VH / 2), (VCX - VW / 2, VCY + VH / 2)], close=True)

# north arrow - grid north plots 6.90 deg above sheet-right
na = math.radians(90.0 - ang())
ax_, ay_ = 7.38, 9.24
psp.add_line((ax_, ay_), (ax_ + 0.55 * math.cos(na), ay_ + 0.55 * math.sin(na)),
             dxfattribs={"layer": "Tblock"})
for d in (150, -150):
    a2 = na + math.radians(d)
    psp.add_line((ax_ + 0.55 * math.cos(na), ay_ + 0.55 * math.sin(na)),
                 (ax_ + 0.55 * math.cos(na) + 0.14 * math.cos(a2),
                  ay_ + 0.55 * math.sin(na) + 0.14 * math.sin(a2)),
                 dxfattribs={"layer": "Tblock"})
pt_("N", (ax_ + 0.74 * math.cos(na), ay_ + 0.74 * math.sin(na)), 0.11)

# ---- flood note --------------------------------------------------------
pl([(BL, 1.78), (BR, 1.78)])
pl([(BL, 1.46), (BR, 1.46)])
for i, s_ in enumerate([
    "THE PROPERTY SHOWN HEREON APPEARS TO LIE WITHIN FLOOD HAZARD ZONE    X    AS SCALED FROM FLOOD",
    "INSURANCE RATE MAP  212  FOR THE CITY OF JACKSONVILLE, FLORIDA, DATED   8-15-89   AND",
    "IS SHOWN AS A COURTESY ONLY AND DOES NOT CONSTITUTE A CERTIFCATION OF SAME."]):
    pt_(s_, (0.33, 1.71 - i * 0.100), 0.060, align="MIDDLE_LEFT")

# ---- firm band ---------------------------------------------------------
pt_("TRI-STATE LAND SURVEYORS, INC.", (4.25, 1.34), 0.145)
pt_("8411 BAYMEADOWS WAY SUITE #2, JACKSONVILLE, FLORIDA 32256  (904) 731-7235",
    (4.25, 1.19), 0.070)
pl([(BL, 1.12), (BR, 1.12)])
pl([(2.05, BB), (2.05, 1.12)])
pl([(5.00, BB), (5.00, 1.12)])

# ---- legend ------------------------------------------------------------
pt_("LEGEND", (1.15, 1.04), 0.065)
LEG = ["CONC. MON.", "IRON COR.", "(SET IR.CAP # LS 4144)", "FENCE",
       "IRON COR. (FOUND)", "CROSS CUT", "B.R.L. BUILDING RESTRICTION LINE",
       "ESM'T  EASEMENT", "R/W  RIGHT-OF-WAY", "COV.  COVERED AREA",
       "℄  CENTERLINE", "A/C  AIR CONDITIONING PAD",
       "(N)  RADIAL DISTANCE", "CONCRETE"]
for i, s_ in enumerate(LEG):
    pt_(s_, (0.40, 1.00 - i * 0.054), 0.044, align="MIDDLE_LEFT")

# ---- notes -------------------------------------------------------------
for i, s_ in enumerate(["BEARINGS BASED ON   R/W   LINE AS SHOWN.",
                        "THIS SURVEY DOES NOT REFLECT OR DETERMINE OWNERSHIP.",
                        "NOT VALID WITHOUT THE SIGNATURE AND THE ORIGINAL RAISED SEAL",
                        "OF A FLORIDA LICENSED SURVEYOR AND MAPPER."]):
    pt_(s_, (2.14, 1.04 - i * 0.088), 0.058, align="MIDDLE_LEFT")
for i, (k, v) in enumerate([("SCALE:", "1\" = 20'"), ("DATE:", "2-22-00")]):
    pt_(k, (2.14, 0.60 - i * 0.20), 0.070, align="MIDDLE_LEFT")
    pt_(v, (2.72, 0.60 - i * 0.20), 0.070, align="MIDDLE_LEFT")
    pl([(2.66, 0.53 - i * 0.20), (3.55, 0.53 - i * 0.20)])
pl([(2.05, 0.73), (5.00, 0.73)])

# ---- signature ---------------------------------------------------------
pt_("LARRY G. EDDY, P.L.S. No. 4144", (5.15, 0.97), 0.068, align="MIDDLE_LEFT")
pt_("GLENN M. BROADSTREET, P.S.M. No. 5814", (5.15, 0.87), 0.068,
    align="MIDDLE_LEFT")
pl([(5.15, 0.52), (7.60, 0.52)])
pt_("REGISTERED SURVEYOR AND MAPPER,", (5.15, 0.44), 0.068, align="MIDDLE_LEFT")
pt_("STATE OF FLORIDA  (LB #4921)", (5.15, 0.34), 0.068, align="MIDDLE_LEFT")
pt_("ORDER NO. 2", (8.18, 0.31), 0.062, align="MIDDLE_RIGHT")
pt_("614564", (0.33, 10.68), 0.055, align="MIDDLE_LEFT")

doc.saveas(OUT)
print("wrote", OUT)
print("modelspace entities:", len(msp))
