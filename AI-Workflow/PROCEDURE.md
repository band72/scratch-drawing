# Scratch working drawing → DXF: the procedure, and what of it can be automated

Reconstructed from the committed code (`jobs/1389/`, `jobs/1496/`) and the batch
logs in `training/`. Numbers quoted here are measured, not estimated — they come
from `jobs/1496/score.txt` and `training/full_batch_v180.txt`.

> **Superseded in part.** Section 4's forecast for local models was written
> before reading `boundary.iq.r2`, which is already running local Ollama models
> on this corpus at up to **96.7%** — no fine-tuning. See
> [BOUNDARY-IQ-INTEGRATION.md](BOUNDARY-IQ-INTEGRATION.md) §4 for the corrected
> picture and what it changes.

---

## 1. What the two jobs actually prove

Two different problems were solved, and the difference between them is the whole
answer to the automation question.

**Job 1389** (12418 Toucan Dr) — *reproduce a 26-year-old sealed survey on today's
measured boundary.* Input: a 400 dpi raster of the 2000 Tri-State sheet, plus a
2026 point file. The prior survey's geometry had to be **read off the sheet by a
human** and typed into a table (`geom.py`, `HOUSE`, `WOOD_DECK`, `DRIVE`, `WALK`…).
Everything after that was code.

**Job 1496** (2333 Luana Dr E) — *build everything derivable from the point file
alone, with no human input, then score it against the sealed sheet.* This is the
controlled experiment. Its `score.txt` is the real automation audit.

---

## 2. The procedure, step by step

### Step 0 — Establish the coordinate frame
State plane (FL East 0901), NAD83, **US survey feet**. Model space is kept at true
grid coordinates: `X = Easting, Y = Northing`, 1 unit = 1 ft. The raw `.txt` point
file drops in with **no transform**.

This single decision removes an entire class of error. Verified independently
against the FEMA lat/long for the site.

### Step 1 — Read the point file
`geom.read_points()` — `P,N,E,Z,code` CSV → dict. 20 lines of code. Deterministic.

### Step 2 — Hold the monuments, build the boundary
The four found 1/2" iron pipes *are* the boundary. `CORNER_PT` maps corner → point
number; the polygon is drawn through them. Record bearings/distances from the plat
are stored in a `REC` table and labelled alongside the **measured** values, so the
comparison is on the face of the drawing.

### Step 3 — Build a local parcel frame
`geom.Frame` — origin at the SE corner, `+x` along the front line, `+y` into the
lot. Gives `L(x,y) → (E,N)` and its inverse.

This is the quiet workhorse. Every prior-survey dimension, every setback, every
offset callout is expressed as *(distance along the front, depth into the lot)* —
the way a surveyor reads a sheet — and the frame converts it to grid. It also makes
the rotation for the paper-space viewport fall out for free
(`view_twist_angle = 360 - ang()`, so the street plots along the bottom).

### Step 4 — Seed the drawing from the firm's standard
```python
src = ezdxf.readfile(SEED)          # training/dxf/010225.01 3RD ST-BOUNDARY-FINAL-R1.dxf
doc = ezdxf.new("R2018", setup=True)
Importer(src, doc).import_tables()  # layers, linetypes, text styles
```
Firm layers, linetypes (`WF`, `VF`, `FENCELINE1`), and text styles (`ROMANS`) are
inherited rather than redefined. Job-specific overlay layers (`V-1389-FENCE`,
`V-COMPARE`…) are added on top so the new work can be frozen independently of the
reproduced prior survey.

### Step 5 — Place geometry
Boundary, 15' drainage & utility easement (centreline = rear line), 25' B.R.L.,
building, improvements, concrete with `AR-SAND` hatch, adjoiner lot numbers, street
label. Text height is driven off the plot scale: `TH = lambda inches: inches * SCALE`,
so `1" = 20'` and `1" = 30'` sheets use the same source.

### Step 6 — Interpret the field codes
The code key is the semantic layer of the whole system:

```
F<control>-<height>-<material>
  control  0 line · 1 end · 2 corner · 3 gate
  material W wood · P PVC/vinyl · C chain link   (C discovered on 1496)
```
Plus `FIP` found iron pipe, `BC` building corner, `EBC` edge broken concrete,
`SEP` septic, `SHD` shed, `WM` water meter, `EA` edge asphalt, and the rest.

### Step 7 — Chain the shots into linework ← **this is the hard step**
`RUNS` in `build_dxf.py` is a **hand-written list** of which point numbers form
which fence run:
```python
("N LINE 6' WOOD", "WF", ["58","61","62","63","72"]),
```
The README is explicit that this is "a best read from position + control code" and
flags it as an open item to confirm before the drawing goes out. Gate logic encodes
a real-world rule: an opening is only broken between **two consecutive** `F3`
shots; a lone `F3` is labelled and drawn through.

### Step 8 — Compute and annotate the verification
`perp_off()` projects each fence shot onto the nearest boundary line → signed
perpendicular offset + station. Each shot gets a `0.42' IN` / `1.60' OUT` callout
on the `V-COMPARE` layer. `report.py` prints boundary record-vs-measured, building
corner deltas, per-shot offsets, per-line summary statistics, and findings.

### Step 9 — Lay out the sheet
Paper space at 1 unit = 1 inch, 8.5×11, title block, legend, flood note, firm band,
signature block, north arrow rotated to grid north, viewport at the plot scale.
All literal coordinates. Tedious, entirely deterministic, and **reusable** — 1496
reused it directly (`score.txt`: "template fill — proven on 1389").

### Step 10 — Proof it
`proof.py` renders to PDF via `ezdxf.addons.drawing` + matplotlib. Because
matplotlib won't render viewport *contents*, it composites: paper space on the full
page, then model space transformed into the viewport rectangle as a second axes.
`--overlay` toggles the 2026 field work on top of the prior survey.

---

## 3. How much is programmable: the measured answer

From `jobs/1496/score.txt` — built from the point file alone, scored against the
sealed sheet:

| Item | Status | Why |
|---|---|---|
| Boundary lines + curve | **AUTO** | COGO pts reproduce sealed values exactly |
| Monument recovery + deltas | **AUTO** | 7 monuments, matched the firm's own QA report |
| Area / acreage | **AUTO** | 12,047 sf vs 12,023 sealed — 0.2% |
| Road, curb, curb drain, WM | **AUTO** | coded shots |
| Lake top-of-bank / edge-of-water | **AUTO** | coded shots |
| Sheet, title block, legend, notes | **AUTO** | template fill |
| Concrete / paver areas | PARTIAL | chained by shot order, needs review |
| Sheds | PARTIAL | 2 corners each, not closed |
| House outline | **NO** | only 6 `BC` shots, all on W and N faces — E and S are **taped** |
| Fence runs | **NO** | 9 `F`-coded shots for 3 runs around the whole lot |
| ~25 tape dimensions | **NO** | field book only |
| 11 encroachment callouts | BLOCKED | computable, but only *after* the linework exists |

**AUTO 6/12 · PARTIAL 2 · NO/BLOCKED 4**

Max distance error on any boundary line: **0.00 ft**.

### The real boundary between code and judgment

Everything that is **arithmetic on coordinates** is solved, exactly, and should
never involve a model:

- bearings, distances, closure, curve solving (R/L/Δ/chord)
- coordinate transforms, local frames, sheet rotation
- perpendicular offsets, stationing, areas
- monument deltas, record-vs-measured comparison
- layer/linetype/style assignment, text sizing, sheet furniture

Three things actually block full automation, and **none of them is a geometry
problem**:

1. **Connectivity.** Which shots form a run, and in what order. The point file
   records *positions*, not *topology*. Shot order is a decent prior and the
   control digit helps, but it is a guess.
2. **Missing data.** The 1496 house has no shots on two faces — those dimensions
   exist only as tape measurements in the field book. **No amount of software
   recovers a measurement that was never taken.** This is a field-procedure
   question, not a software one.
3. **Undocumented codes.** `score.txt` lists `BOC0`/`BOC2`, `CB` vs `CC`, `CB-EC`,
   `TRB` as unresolved. The code vocabulary drifts per crew and per job.

### The other pipeline: legal descriptions
`training/full_batch_v180.txt`, run 2026-05-07 over 1,347 documents:

```
Legal docs scored : 1095
PASS              : 1014
MEANDER           :    2
FAIL              :   79
Pass Rate         : 92.8%
```

Closure precision is the automatic grader. Failures cluster into real categories,
visible in `remaining_analysis.txt`: unparseable bearings (`'North Easterly'`,
`'Southeasterly and Southerly'`, empty strings), and genuine bad deeds (closures of
8412', 1510', 258' — those documents are simply wrong, and flagging them *is* the
product). The notes in `training/*/recommendations.txt` capture the two systemic
traps: a **uniform basis-of-bearings rotation** (≈5'50" here) must be detected as
one rotation, not 6 separate busts; and curves on a plat often appear as straight
chords in the coordinate list.

---

## 4. Can a local Qwen model be trained to do this?

Short answer: **yes for the language half, no for the geometry half — and the
geometry half is most of the drawing.**

### Do not train a model to do geometry
Asking a model to emit coordinates, close a traverse, or solve a curve is strictly
worse than `ezdxf` + 40 lines of trigonometry: slower, non-reproducible, and
unverifiable. You already have 0.00 ft error. A model cannot improve on exact, and
a sealed survey cannot rest on a sampled token. Keep every number in code.

### Where a local model genuinely earns its place

1. **Legal-description parsing (highest value).** Prose → structured calls. This is
   exactly the existing "Vision fallback" / "Heavy AI Text Repair" step, and it is
   what pushes 92.8% toward the high 90s. Target the 79 failures, not the 1,014
   that already pass.
2. **Narrative bearings.** `'North Easterly'`, `'Southeasterly and Southerly'` — a
   fine-tuned model handles these; a regex never will.
3. **Scanned-document extraction.** A vision model reads the title commitment,
   prior sheet dimensions, and field-book pages. `training/TrainPDF/` and
   `training/Legal/` are already the corpus.
4. **Field-code resolution.** Mapping drifting crew vocabulary onto a canonical key,
   and proposing the `RUNS` connectivity for human confirmation.
5. **Boilerplate.** Legend, notes, certification wording per client.

### Why your situation is unusually favourable

**You have an automatic grader.** Closure precision tells you whether a parse is
right *without a human labelling anything*. That means:

- the 1,014 passing documents are **free labelled training data** (input prose →
  verified-correct structured output);
- you can generate candidate outputs, keep only those that close, and train on
  them — rejection sampling with a hard, non-gameable reward;
- a fine-tune can be evaluated honestly by re-running the 1,347-file batch and
  comparing pass rates.

Most people fine-tuning a model have no such signal. You do. That is the single
strongest argument for doing this.

### Practical shape

- **Models.** The Qwen instruct family at 7B–14B for text parsing; the Qwen-VL
  line for scanned pages. Check current releases before committing — the line moves
  fast and my information has a cutoff.
- **Method.** LoRA / QLoRA, not full fine-tuning. A few thousand examples is the
  right order of magnitude, and you have more than that.
- **Hardware.** 7B LoRA fits comfortably on a single 24 GB card; 14B wants
  quantization. Inference via llama.cpp / Ollama / vLLM. All local — which matters
  here, because the corpus is **client title and survey material that must not go
  to a hosted API**.
- **Output discipline.** Constrain decoding to a JSON schema (grammar-constrained
  sampling). Never let the model free-form a number that code could compute.
- **Architecture.** Deterministic first, model only on fallback. Parse with the
  existing rules; invoke the model on what fails; **re-check every model output
  with closure math**; escalate what still fails to a human. Same shape as the
  current pipeline — the model just replaces the weakest link.

### Realistic ceiling

Boundary geometry, monument comparison, sheet production: **already ~100%, by code.**
Legal-description parsing: **92.8% → mid-to-high 90s** with a local fine-tune, with
the remainder being genuinely defective deeds that *should* fail.
Full drawing from a point file: **capped by field data**, not software — the 1496
house cannot be drawn because two faces were taped and never shot. Richer coding
and a shot-per-corner discipline in the field would move more items from NO to AUTO
than any model will.

**The honest headline:** the drawing is a programming problem and is largely solved.
The *documents* are an AI problem, and that is where a local Qwen pays for itself.

---

## 5. Open items carried forward

From `jobs/1389/README.md` and `jobs/1496/score.txt`:

1. Fence run connectivity (`RUNS`) is inferred — confirm before any drawing goes out.
2. Pt 57 (`F1-4-W`) is a single shot: symbolised, not drawn as a run.
3. `EBC` pts 30–41 read as the walk/old slab line, not the driveway edge — confirm.
4. Unresolved codes: `BOC0`/`BOC2`, `CB` vs `CC`, `CB-EC`, `CC-CB`, `TRB`.
5. Everything in this pipeline is **draft work for a licensed surveyor to check and
   seal.** The automation produces verifiable intermediate product; it does not
   produce a signed survey.
