#!/usr/bin/env python3
"""Render 1389.dxf to a proofing PDF: the paper-space sheet with the model
viewport composited in (matplotlib does not render viewport contents itself)."""
import math, os, sys
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import ezdxf
from ezdxf.math import Matrix44
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import geom

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
DXF  = os.path.join(HERE, "1389.dxf")
OVERLAY = "--overlay" in sys.argv
OUT  = os.path.join(HERE, "1389_proof_overlay.pdf" if OVERLAY else "1389_proof.pdf")

pts, _ = geom.read_points(os.path.join(ROOT, geom.PTFILE))
F = geom.Frame(pts)
SCALE = 20.0
PRIOR = {"PL", "ELINE", "STL", "BLDG", "CONC", "HATCHC", "FENCES",
         "TEXT", "BLDGTEXT", "BRGTXT", "PLTEXT", "ADJ", "SYM"}
OVER  = {"V-1389-PNTS", "V-1389-FENCE", "V-1389-IMPR", "V-1389-TEXT",
         "V-COMPARE", "PNTS"}

fig = plt.figure(figsize=(8.5, 11))

# ---- paper-space sheet (full page, 1 unit = 1 inch) --------------------
doc = ezdxf.readfile(DXF)
psp = doc.layout("Layout1")
for e in list(psp):
    if e.dxftype() == "VIEWPORT":
        psp.delete_entity(e)
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 8.5); ax.set_ylim(0, 11)
ax.set_aspect("equal"); ax.axis("off")
Frontend(RenderContext(doc), MatplotlibBackend(ax)).draw_layout(psp, finalize=False)

# ---- model space, rotated into the viewport rectangle ------------------
VW, VH, VCX, VCY = 7.40, 7.82, 4.25, 5.69
doc2 = ezdxf.readfile(DXF)
msp = doc2.modelspace()
keep = PRIOR | (OVER if OVERLAY else set())
M = Matrix44.chain(Matrix44.translate(-F.o[0], -F.o[1], 0),
                   Matrix44.z_rotate(-math.atan2(F.u[1], F.u[0])))
for e in list(msp):
    if e.dxf.layer not in keep:
        msp.delete_entity(e); continue
    try: e.transform(M)
    except Exception: pass
ax2 = fig.add_axes([(VCX - VW / 2) / 8.5, (VCY - VH / 2) / 11.0, VW / 8.5, VH / 11.0])
cx, cy = F.inv(*F.L(42.5, 70.0))
ax2.set_xlim(cx - VW * SCALE / 2, cx + VW * SCALE / 2)
ax2.set_ylim(cy - VH * SCALE / 2, cy + VH * SCALE / 2)
ax2.set_aspect("equal"); ax2.axis("off"); ax2.patch.set_alpha(0)
Frontend(RenderContext(doc2), MatplotlibBackend(ax2)).draw_layout(msp, finalize=False)

fig.savefig(OUT, facecolor="#101010")
print("wrote", OUT, "(overlay)" if OVERLAY else "(prior survey only)")
