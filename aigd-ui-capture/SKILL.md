---
name: aigd-ui-capture
description: AIGD · UI screenshot → UI DSL (knowledge-base capture / tool 1). Use this when you want to turn a game UI screenshot (a competitor's or your own) into structured md (type/hierarchy/geometry/interaction/state), so ui_render.py can restore it to a wireframe and it can be accumulated into the patterns/UI-paradigm knowledge base. The authority for the read-the-image recipe and grammar is in ../aigd/references/ui-dsl-spec.md; this skill only orchestrates the flow, it doesn't duplicate the grammar. Part of the aigd package.
---

# UI screenshot → UI DSL (tool 1 · capturer)

Reads a UI screenshot into one **UI DSL** (.md): structure / type / hierarchy / geometry / interaction. It is the input to the deterministic scripts `ui_render.py` (tool 2, restore) and `ui_slice.py` (tool 3, slice). **This skill orchestrates the flow; the grammar / recipe always defers to `../aigd/references/ui-dsl-spec.md`** (no need to change this doc when the spec updates).

---

## Step 0: read the source of truth (do every time, use Read, don't go from memory)

| File | What to take |
|------|--------|
| `../aigd/references/ui-dsl-spec.md` | File skeleton + Layout-line grammar + type table + z layering + shapes + source semantics + **read-the-image recipe (§7)** + **skin/theme (§9)** |
| `../aigd/references/scripts/ui_render.py` | Restore + missing-z reminder + calibration export (for verifying the artifact) |
| `../aigd/references/scripts/ui_palette.py` | Sample colors from the original image → write a `## Skin` section (for adding color schemes to the library) |
| `../aigd/references/scripts/ui_slice.py` | Image + DSL → per-element slices + index.md contact sheet (extract assets, optional) |
| `../aigd/references/ui-dsl-example.md` | The shape of one package-compliant DSL (example screen) |

## Step 1: confirm the input

Need **one screenshot** + `screen ID` + `source (competitor name / own)` + a one-line `purpose`. Ask if missing. Competitor images default to "discard the original once converted, the DSL goes into the library".

## Step 2: produce the DSL per the read-the-image recipe (spec §7)

Strictly follow the order of spec §7: screen header → palette → Layout (outer to inner / top to bottom: containers before leaves) → Events → design review. **Every element must be tagged `type + @{x y w h} + z=N`** (the renderer allows omitting z, but **capture into the library must tag it fully** — you're transcribing a real image, the hierarchy must be recorded accurately); a circle is tagged `shape=circle`, selected/locked tagged `[state]`, a full-screen base image `@{0 0 100 100} z=1`. Competitor data is only tagged `:observed` / `:inferred`, **never write `:canonical`**. Eyeballing the geometry as a percentage is fine (precision is handled by the calibration in step 3). **Colors don't go into element lines** — step 3 uses `ui_palette.py --merge` to sample colors and write them into a `## Skin` section (spec §9).

## Step 3: run tool 2 to verify (mandatory, closed loop)

```
python ../aigd/references/scripts/ui_render.py <screen ID>.md <out>.html --svg <out>.svg
python ../aigd/references/scripts/ui_palette.py <screen ID>.md <original image> --merge   # sample colors into a ## Skin section
```

- **Missing z is flagged** (lists which aren't tagged) → **go back and complete** before capturing into the library (rendering itself isn't blocked, but the library wants it standard).
- Open `<out>.html` in a browser, **eyeball against the original**: are the hierarchy / region proportions / text / interaction right; toggle wireframe / skin / mood to see the structure (after sampling, the skin layer uses the real colors).
- If it's off, use the html "**calibrate**" drag to fine-tune → "**export DSL**" to paste the corrected coordinates back into `<screen ID>.md` → run it again.
- The verification scope is **structure / proportion / hierarchy / text / interaction, not art** (art swaps in your own assets, see spec §5).

## Step 4: into the library

Once it passes, store at `patterns/ui-patterns/<game>/<screen ID>.{md, html, svg(optional)}`, and add a row in that directory's `INDEX.md` (screen ID / source / layout pattern / tags), for concept/system to retrieve similar references at design time.

**When you need to extract assets (optional)**: `ui_slice.py <screen ID>.md <original image> [outdir]` slices the original into per-element png + an `index.md` contact sheet (`--only bgSlot,artSlot,iconSlot` slices only the art slots), handy for referencing / replacing competitor parts; run it once before discarding the original (spec §8).

---

## Hard constraints (don't break)

- **Capture into the library must tag `z=`** (this is tool 1's discipline, not enforced by the renderer — the renderer allows omitting z and falls back to indentation / document order, but transcribing a real image means recording the hierarchy accurately).
- **Don't rely on guessing**: shapes and hierarchy follow only the md declaration, the renderer doesn't infer from aspect ratio / geometry — so tool 1 must write `shape=` / `z=` in full.
- **Competitor sources** use only `:observed` / `:inferred`, don't fabricate `:canonical`.
- **Colors go into the skin section**: don't write them into element lines; use `ui_palette.py --merge` to sample them into a `## Skin` section (by id), the whole section is swappable / deletable (spec §9).
- **Restoring structure, not art**: don't chase pixel-perfect replication, leave art slots empty to swap in assets.
- Files are **UTF-8 without BOM** (adding a BOM to Chinese makes downstream garble); per-harness writing methods are in `../aigd/references/harness-adapt.md`.
- This skill only **orchestrates**; the grammar / recipe always **defers to `ui-dsl-spec.md`**.
