# Job 1389 — 12418 Toucan Dr, Jacksonville FL 32223

Lot 8, Block 7, **Julington Hills Unit Two** (PB 28, pgs 35/35A/35B, Duval County)
RE# 159326-0000 · Field work 03/31/26 (book 1389-NE, P. Moore)
Prior survey: Tri-State Land Surveyors, 2-22-00, order no. 2xxxx

## What this is

The 2000 prior survey redrawn as a DXF, placed on the **measured** boundary (the
four found 1/2" iron pipes), with the 03/31/26 field work overlaid so the fences
can be checked against the lines.

## Coordinate system

Florida East zone (0901), NAD83, **US survey feet**. Model space is at true grid
coordinates — X = Easting, Y = Northing — so `1389.txt` drops straight in with no
transform. Confirmed against the FEMA lat/long for the site (30.142737, -81.626274).

## Files

| File | What it is |
|---|---|
| `1389.dxf` | The drawing. Model space = survey at grid coords; `Layout1` = the 2000 sheet reproduced, 8.5x11 portrait, viewport at 1" = 20'. |
| `geom.py` | Boundary frame + the prior-survey geometry table (edit improvements here). |
| `build_dxf.py` | Builds `1389.dxf`. Seeds layers/linetypes/styles/blocks from `training/dxf/010225.01 3RD ST-BOUNDARY-FINAL-R1.dxf`. |
| `report.py` | Prints the boundary / building / fence verification report. |
| `proof.py` | Renders a proofing PDF (`--overlay` for the field-work version). |

```
python3 jobs/1389/build_dxf.py
python3 jobs/1389/report.py
python3 jobs/1389/proof.py            # 1389_proof.pdf
python3 jobs/1389/proof.py --overlay  # 1389_proof_overlay.pdf
```

## Layers

Firm standard layers are inherited from the seed drawing. The 2000 survey is on
`PL ELINE STL BLDG CONC HATCHC FENCES TEXT BLDGTEXT BRGTXT PLTEXT ADJ SYM`.
The 2026 field work is on new layers so it can be frozen independently:

- `V-1389-PNTS` / `PNTS` — field point symbols
- `V-1389-TEXT` — point number, code, elevation
- `V-1389-FENCE` — measured fence linework (`WF` / `VF` linetypes)
- `V-1389-IMPR` — measured improvements (drive edges, septic, shed, bldg corners)
- `V-COMPARE` — measured bearings/distances and fence offset callouts

## Field code key used

`F<control>-<height>-<material>` — control `0` line, `1` end, `2` corner,
`3` gate; material `W` wood, `P` PVC/vinyl. A gate opening is only broken where
two `F3` shots are consecutive; a lone `F3` is labelled and drawn through.

Other codes: `FIP` found iron pipe · `BC` building corner · `EBC` edge broken
concrete · `EC`/`CC` edge/corner of concrete · `SEP` septic · `SHD` shed ·
`WM` water meter · `BF` backflow · `UR` utility riser · `WPP` power pole ·
`UGC` underground cable · `EA` edge asphalt · `CP` control point · `STEP` step.

## Open items

1. Fence **run connectivity** is a best read from position + control code
   (see `RUNS` in `build_dxf.py`). Confirm before the drawing goes out.
2. Point **57** (`F1-4-W`) is a single shot — a 4' wood fence end with no second
   point, so it is symbolised, not drawn as a run.
3. `EBC` (pts 30–41) runs from the street to 45 ft depth at 44–49 ft from the
   south line — that is the walk/old slab line, not the driveway edge (the drive
   edges are 47-46-45 and 48-49). Confirm the interpretation.
4. The second field-book photo (`#203`, 1-storey stucco, paver drive) is a
   different job and was not used.
