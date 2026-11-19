# Pulling from Boundary.IQ: what's there, what we reuse, what it corrected

Source: `/home/artwalk/boundary.iq.r2` (private, 1.1 GB, MIT, ~30 commits of
history). Not vendored into this repo — located at import time. See
`plugin/engine_link.py`.

---

## 1. What the existing project contains

Two engines, which matters for what we can reuse.

**Node/Express — the document pipeline** (`server/services/`)
Deed/plat extraction via Gemini *or* local Ollama, a 6-stage self-healing agent
(`agentSystem.js`), `bearingParser.js`, `deedTextSolver.js` (87 K), `repair.js`
(111 K), `traverse.js` (47 K), `legalWriter.js`, `dxfExport.js` (51 K),
`docClassifier.js`, SQLite diagnostics. This is the production path.

**Python — the deterministic COGO engine** (`parcel-engine/engine/`, ~32 modules)
Offline, no LLM. Vendored from `plat_project_2026-R0`, explicitly *"not yet
wired in"*. This is the half that matters to scratch-drawing, because
scratch-drawing is Python + ezdxf.

| Module | What it gives us |
|---|---|
| `cogo.py` | `parse_bearing`, `azimuth_to_bearing`, `Point`, `Course`, `run_traverse`, `closure_report`, `bowditch_balance` |
| `curves.py` | `Curve` (tangent, mid-ordinate, external, degree-of-curve, areas), `solve_curve_all_parameters` — **any 2 of 8 parameters, all 28 pairs** |
| `verify.py` | `verify_ring` / `verify_network` — spikes, zero-length sides, self-crossings, collinear overlap, with tolerances |
| `blunder.py` | `course_deviation` / `classify` — courses vs raster linework |
| `repair.py` | OCR digit-confusion repair, `inverse_solve_curve`, `radius_consensus` |
| `lots.py` | `shoelace_area`, `safe_area`, `is_simple_polygon` |
| `legal_text.py` | words→number, words→bearing, parenthetical cross-check |
| `audit.py` | closure/area/DXF-layer audits |
| `topology.py` | `VertexGraph`, `Parcel` — shared-edge topology |
| `solver.py` | constraint solver (`SumEquals`, `TraverseClosure`, `CurveRelation`, `TangentRelation`) |

---

## 2. What overlapped — and what that overlap cost

scratch-drawing had independently reimplemented survey math three times, and
the copies disagree.

| Function | `jobs/1389/geom.py` | `jobs/1496/build_1496.py` | `engine/cogo.py` |
|---|---|---|---|
| bearing formatting | **buggy** | correct | correct + documented |
| bearing *parsing* | — | — | present, range-checked |
| curve solving | — | hand-rolled centre/arc | `solve_curve_all_parameters` |
| closure / Bowditch | — | — | present |
| ring validity | — | — | present |

### The bug this found

`engine/cogo.py:azimuth_to_bearing` carries this note:

> Rounds in DMS space BEFORE formatting. Formatting each component
> independently produces INVALID output like `N03°08'60.00"E` — a bearing can
> never show 60 seconds, it must carry into minutes. **Measured 319 such
> invalid strings in a 200k-sample sweep of the previous implementation.**

`jobs/1389/geom.py:bearing()` formats each component independently:

```python
d = int(a); m = int((a - d) * 60); s = (a - d - m / 60) * 3600
return f"{ns} {d:02d}°{m:02d}' {s:02.0f}\" {ew}"
```

Measured, not assumed:

- **1,956 of 200,000** swept azimuths (≈1%) produce an impossible bearing.
- On job 1389's **own** point file: **16 of 2,628** point-pair bearings, e.g.
  `N 01°42' 60" E`, `N 83°23' 60" W`.
- `jobs/1496/build_1496.py` rounds in DMS space first and is correct — so the
  two jobs in this repo disagree with each other.

None of the four boundary bearings on the 1389 sheet happens to land on the bad
rounding, so the issued drawing is unaffected. The function is still wrong, and
anything new built on it inherits a 1-in-100 chance of printing a bearing that
cannot exist.

---

## 3. What was built

`plugin/` now pulls from the engine instead of duplicating it.

```
plugin/
├── engine_link.py   locate parcel-engine ($BOUNDARY_IQ_ENGINE, ~/boundary.iq.r2, ../)
├── cogo.py          engine re-exports + CAD-order bearing/dist/azimuth
├── points.py        P,N,E,Z reader + F-code vocabulary
├── frame.py         Frame - local parcel frame, generalised
└── offsets.py       perpendicular offsets, return-leg detection, summaries
```

**Coordinate order is the one real integration hazard.** The engine works in
`Point(n, e)`; the CAD code here works in `(X=Easting, Y=Northing)` tuples.
Transposing those silently mirrors a parcel. All conversion is confined to
`plugin/cogo.py` (`to_cad` / `to_survey`) and happens nowhere else.

**Not pulled, deliberately:**

- `engine/dxf_writer.py` — raw DXF text writer. scratch-drawing uses `ezdxf`
  with `Importer` to inherit the firm's layers, linetypes and text styles from
  a seed drawing. That is the better mechanism; keep it.
- `engine/georeference.py` — hardcoded Clay County GIS paths and a local GPS
  DB. Wrong county, and it reaches for machine-local data.
- Everything in `server/services/` — Node, and the document pipeline, not the
  drawing pipeline.

### Verified, not asserted

`AI-Workflow/verify_against_1389.py` runs the real 1389 field data through the
new modules and compares against the committed job code:

```
1. reader       73 points, order identical                      OK
2. frame        front 84.9721', rot 83.096116deg, 1e-9           OK
3. boundary     all four distances identical to the job          OK
4. offsets      23 fence shots, same line assignment, delta 0.0  OK
5. summary      REAR +0.16/+0.65, SOUTH -1.60/+0.28, legs 60,89  matches report.py
6. bearings     geom.py 16 impossible / plugin 0                 FIXED
```

Needs `training/TrainPDF/1389.txt`, which is gitignored — local data only.

---

## 4. This corrects my earlier write-up

`AI-Workflow/PROCEDURE.md` predicted that legal-description parsing could go
from 92.8% to "mid-to-high 90s" with a local fine-tune. **That is already done,
and with no fine-tuning at all.** From the project's own README — consecutive
batch runs over 1,390 historical deeds, per local model:

| Local model | Pass rate | PASS | FAIL |
|---|---|---|---|
| `gemma4:26b` | **96.7%** | 1,005 | 11 |
| `deepseek-r1:8b` | 96.2% | 1,000 | 13 |
| `deepseek-r1:14b` | 96.0% | 997 | 16 |
| `llama3.2:3b` | 95.5% | 992 | 32 |
| `gemma3:4b` | 94.4% | 981 | 23 |

So the honest answer to "can I train a local model to do this" is: **you are
already running local models on it, off the shelf, at 96.7%.** The question is
no longer *whether* a local model works but whether fine-tuning beats prompting
on the residual ~11–30 failures.

Three observations that change the plan in `PROCEDURE.md`:

1. **A 3 B model scores 95.5%.** The spread from `llama3.2:3b` to
   `gemma4:26b` is 1.2 points. The task is mostly not model-capacity-limited,
   so a bigger or fine-tuned model has little headroom to recover.
2. **No Qwen in the table.** Given 3 B is within 1.2 points of 26 B, a Qwen
   instruct model would most likely land in the same band. Worth benchmarking
   through the harness you already have — that is a one-line model swap and an
   afternoon, versus weeks for a fine-tune.
3. **The real ceiling is OCR, not reasoning.** `parcel-engine/README.md`
   documents hitting a hard wall on a stylized/italic plat typeface: after
   fuzzy regex, spelled-out cardinals, and OCR-confusion handling, Tesseract
   still recovered only 2 of ~18 courses. The conclusion recorded there is that
   it needs a better *reader* — a vision model or a typeface-specific
   fine-tune. **That** is where a fine-tune has a real target, and it is a
   vision problem, not a text problem.

The structural point from `PROCEDURE.md` stands and is reinforced: closure
precision is an automatic grader, so every candidate here is cheaply
measurable. Benchmark before training.

---

## 5. Next steps

1. **Fix `jobs/1389/geom.py:bearing()`** — or delete it and import
   `plugin.cogo`. The sheet is unaffected but the function is wrong.
2. **Point `jobs/1496` at `plugin.cogo`** for its hand-rolled arc, and gain
   `solve_curve_all_parameters` for free.
3. **Run `engine/verify.py:verify_ring`** on both job boundaries — spike and
   self-crossing checks neither job currently has.
4. **Add closure/Bowditch to the boundary step** via `closure_report` and
   `bowditch_balance`, which scratch-drawing has no equivalent for.
5. **Benchmark a Qwen model** through the existing Ollama harness before
   considering any fine-tune.
6. **Decide whether scratch-drawing should become a module of Boundary.IQ.**
   Its real contribution is the half Boundary.IQ lacks: point-file ingestion,
   field-code semantics, the parcel frame, offset verification, and
   firm-standard sheet production from a seed DXF. Boundary.IQ goes
   *deed → geometry*; scratch-drawing goes *field shots → sheet*. Together
   they are the whole job.
