"""Reusable functions for scratch-drawing jobs.

Survey math is NOT implemented here. It is pulled from the Boundary.IQ
parcel-engine (`/parcel-engine/engine/`), which is the single source of truth
for bearings, traverse, closure, curves and ring verification. `plugin.cogo`
re-exports it and adapts the coordinate order; see plugin/engine_link.py for
how the engine is located, and AI-Workflow/BOUNDARY-IQ-INTEGRATION.md for what
was pulled and why.

What is implemented here is what the engine has no equivalent for, because the
engine starts from deed and plat calls while these jobs start from a total
station point file:

    plugin.points   P,N,E,Z point files and the F-code field vocabulary
    plugin.frame    Frame - local parcel frame (along-front, depth)
    plugin.offsets  perpendicular offsets from the boundary (fence verification)
    plugin.cogo     engine re-exports + CAD-order bearing/dist/azimuth

Conventions shared by everything in this package:

    Coordinate system : state plane, NAD83, US survey feet
    CAD model space   : X = Easting, Y = Northing, 1 unit = 1 ft
    engine order      : Point(n, e) - converted only in plugin.cogo

Run job scripts from the repo root so `import plugin` resolves.
"""

__all__ = ["cogo", "frame", "offsets", "points", "engine_link"]
