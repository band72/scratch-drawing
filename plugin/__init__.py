"""Reusable functions for scratch-drawing jobs.

Job scripts under jobs/<n>/ import from here instead of carrying their own
copies. Conventions shared by everything in this package:

    Coordinate system : state plane, NAD83, US survey feet
    CAD model space   : X = Easting, Y = Northing, 1 unit = 1 ft

Run job scripts from the repo root so `import plugin` resolves.
"""
