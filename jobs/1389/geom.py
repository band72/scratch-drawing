"""Shared geometry for job 1389 - 12418 Toucan Dr, Lot 8 Blk 7 Julington Hills Unit Two.

Coordinate system: Florida East zone (0901), NAD83, US survey feet.
CAD model space: X = Easting, Y = Northing, 1 unit = 1 ft.

Local parcel frame L(x, y):
    origin  = SE corner (found 1/2" iron pipe, pt 1)
    x axis  = along the FRONT line (Toucan Dr) from SE toward NE  -> distance from the SOUTH line
    y axis  = perpendicular into the lot                          -> depth from the FRONT line
"""
import math

PTFILE = "training/TrainPDF/1389.txt"


def read_points(path):
    pts, order = {}, []
    with open(path) as fh:
        for line in fh:
            f = line.strip().split(",")
            if len(f) < 4 or not f[0]:
                continue
            pts[f[0]] = dict(n=float(f[1]), e=float(f[2]), z=float(f[3]),
                             code=(f[4].strip() if len(f) > 4 else ""))
            order.append(f[0])
    return pts, order


# ---- measured boundary: the four found 1/2" iron pipes -------------------
CORNER_PT = {"SE": "1", "NE": "4", "NW": "3", "SW": "2"}


class Frame:
    def __init__(self, pts):
        self.pts = pts
        self.C = {k: (pts[v]["e"], pts[v]["n"]) for k, v in CORNER_PT.items()}
        se, ne = self.C["SE"], self.C["NE"]
        dx, dy = ne[0] - se[0], ne[1] - se[1]
        L = math.hypot(dx, dy)
        self.o = se
        self.u = (dx / L, dy / L)          # toward NE  (= toward the north line)
        self.v = (-dy / L, dx / L)         # into the lot (= toward the rear)
        self.front_len = L

    def L(self, x, y):
        """local (along-front, depth) -> CAD (X=E, Y=N)"""
        return (self.o[0] + x * self.u[0] + y * self.v[0],
                self.o[1] + x * self.u[1] + y * self.v[1])

    def Lp(self, poly):
        return [self.L(*p) for p in poly]

    def inv(self, X, Y):
        """CAD (X,Y) -> local (x,y)"""
        dx, dy = X - self.o[0], Y - self.o[1]
        return (dx * self.u[0] + dy * self.u[1], dx * self.v[0] + dy * self.v[1])


def bearing(p, q):
    az = math.degrees(math.atan2(q[0] - p[0], q[1] - p[1])) % 360
    ns = "N" if (az < 90 or az > 270) else "S"
    ew = "E" if az < 180 else "W"
    a = az if az < 90 else (180 - az if az < 180 else (az - 180 if az < 270 else 360 - az))
    d = int(a); m = int((a - d) * 60); s = (a - d - m / 60) * 3600
    return f"{ns} {d:02d}°{m:02d}' {s:02.0f}\" {ew}"


def dist(p, q):
    return math.hypot(q[0] - p[0], q[1] - p[1])


# ---- PRIOR SURVEY (Tri-State Land Surveyors, 2-22-00) in local coords ----
# All values scaled/read from the recorded sheet.  Dimensions shown on the
# sheet are exact; undimensioned graphics were scaled off the 400 dpi raster.

HOUSE = [                      # 1 STY BRICK & WOOD  #12418 - closes to 0.2'
    (12.1, 39.8), (36.9, 39.8),            # 24.8'
    (36.9, 55.1), (44.4, 55.1),            # 15.3' up, 7.5' across
    (44.4, 52.1), (52.2, 52.1),            # 3.0' down, 7.8' across
    (52.2, 25.7), (75.1, 25.7),            # 26.4' down, 22.9' across
    (75.1, 78.5), (12.1, 78.5),            # 52.8' up, 62.8' back
]
WOOD_DECK   = [(36.9, 39.8), (44.4, 39.8), (44.4, 52.1), (36.9, 52.1)]
DIRT        = [(36.9, 52.1), (44.4, 52.1), (44.4, 55.1), (36.9, 55.1)]
SCREEN_PORCH= [(39.7, 78.5), (56.4, 78.5), (56.4, 88.3), (39.7, 88.3)]   # 16x10 per PRC
PATIO_CONC  = [(56.4, 78.5), (75.1, 78.5), (75.1, 92.0), (56.4, 92.0)]
ALUM_SHED   = [(1.0, 78.5), (12.1, 78.5), (12.1, 87.0), (1.0, 87.0)]
AC_PAD      = [(75.1, 41.3), (78.5, 41.3), (78.5, 47.9), (75.1, 47.9)]
DRIVE       = [(55.8, 0.0), (75.1, 0.0), (75.1, 25.6), (55.8, 25.6)]
WALK        = [(46.5, 39.8), (46.5, 26.0), (49.5, 19.0), (55.8, 15.0),
               (55.8, 20.5), (51.5, 23.5), (51.5, 39.8)]

LOT_DEPTH   = 140.0
LOT_WIDTH   = 85.0
BRL         = 25.0      # 25' building restriction line from the front
ESMT_HALF   = 7.5       # centerline of the 15' drainage & utility esm't is the REAR line
