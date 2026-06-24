# AIGD toolchain (references/scripts)

The **deterministic scripts** bundled with the AIGD methodology. Two main lines:

- **UI knowledge base**: screenshot → UI DSL → restore to html/svg, sample colors, slice assets (accumulate a searchable UI-paradigm library).
- **Config / handoff validation**: turn the consistency of "config-spec ↔ xlsx ↔ acceptance cases" into a machine check, wired into the finalization gate; and generate a planner-version checklist from the acceptance cases.

## Design principles (upheld by all scripts)

- **argv-driven, zero project hard-coding** — paths all go through arguments, portable; project-specific maps go in the config directory (see below).
- **Deterministic** — same input, same output (no `Date.now`/randomness), CI-able, diff-able.
- **Pure stdlib where possible** — reading xlsx always goes via `xlsx_dump` (`zipfile`+`ElementTree`), **bypassing openpyxl's `Colors must be aRGB hex values` error on reading domestic-export xlsx**; only "writing xlsx" uses openpyxl.
- **No silent misses** — for items that "look like they should be checked but weren't," the validator explicitly records `FK_SKIP`/`RULE_SKIP` (info), not treated as a pass.
- **No fabrication, prefer under-reporting over false-reporting** — can't find / can't resolve → mark, don't guess a value (false reports hurt the validator's credibility most).
- **Self-describing header convention** (xlsx): row 1 = the table's English name (codegen class name), row 2 = field type, row 3 = field English key (arrays use `field[ … ]`), row 4 = Chinese name (annotations write enums/conventions), rows 5+ = data.

## Dependencies

| Dependency | Who uses it | Install |
|------|------|------|
| Pure stdlib | `ui_render` `xlsx_dump` `resolve_loc` `config_index` `config_check` `value_check` `manifest_check` `ref_lib` `ref_graph` | no install needed |
| Pillow≥9 | `ui_palette` `ui_slice` (image color-sampling/slicing) | `pip install Pillow` |
| openpyxl≥3 | `gherkin_to_checklist` (**writes** xlsx) | `pip install openpyxl` |

> See `requirements.txt`. When a dependency is missing, the related tests **skip gracefully** (not counted as a failure).

---

## A. UI knowledge-base toolchain

> Tool 1 = the **`aigd-ui-capture` skill** (not a script): reads a screenshot into a UI DSL (`.md`). The grammar contract is in `../ui-dsl-spec.md`. The scripts below consume this DSL.

### `ui_render.py` — tool 2 · DSL → html/svg (pure stdlib, deterministic)
```
python ui_render.py <DSL.md> <out.html> [--svg <out.svg>] [--skin <skin.json>] [--modules <moduleDir>]
```
- **In**: UI DSL (`# screenHeader` + `## Layout` indented tree + `## Events` + optional `## Skin`/`## Refs`).
- **Out**: clickable vector html (with "calibrate" drag + "Export DSL" to paste corrected coordinates back) + optional svg.
- Supports screen/module/instance references (`resolve` pre-render flatten), skin section/theme (`@canvas`), missing `z` falling back to indent + document order.
- Compare structure/layering/proportion/text/interaction against the image — **no pixel-perfect replication** (art swaps in its own assets).

### `ui_palette.py` — tool 3 · sample colors from the original image → skin section (Pillow)
```
python ui_palette.py <DSL.md> <originalImage> --merge
```
- Samples the main color from the original image by element id, written as a `## Skin` section pasted back into the DSL (**not written into the element line**, the whole section can be swapped or deleted). Art slots like bgSlot/artSlot are not sampled.

### `ui_slice.py` — tool 3 · image + DSL → per-element slices (Pillow)
```
python ui_slice.py <DSL.md> <originalImage> [outdir] [--only bgSlot,artSlot,iconSlot]
```
- Slices the original image into per-element png by element bbox + an `index.md` contact sheet, for referencing/replacing competitor parts. `--only` slices only the specified type slots.

---

## B. Config / handoff validation toolchain

### `config_check.py` — tool 4 · config-spec ↔ xlsx **schema drift** (pure stdlib)
```
python config_check.py <config-spec.md> <table.xlsx>
```
Manages "**is the structure right**": columns/types/table names/declared domain. Non-zero exit code = has major.

| Category | What it catches | Severity |
|------|--------|--------|
| `UNDOC_COL` | xlsx has a column, the config-spec didn't record it (the typical trace of changing the xlsx without backfilling) | major |
| `MISSING_COL` | the config-spec declares a field, the xlsx has no such column | major |
| `TYPE` | same-named field, doc type ≠ xlsx type | major |
| `RENAME` | the doc's table name finds no same-named sheet, gives the closest one (suspected rename) | major |
| `MISSING_TABLE` | the doc declares a table, the xlsx has no sheet | major |
| `DOMAIN` | the declared domain (parseable like `0/1`, `1~5`) doesn't match the actual data, gives an out-of-range sample | advisory (human judgment) |

### `value_check.py` — tool 5 · config **data integrity** (pure stdlib)
```
python value_check.py <config-spec.md> <configDir> \
  [--acc <acceptance.md>] [--rules <system.checks.json>] \
  [--enums <enums.md>] [--keymap <composite-key-map.json>] [--refmap <ref-table-map.json>]
```
Manages "**is the data itself / between data right**." The composite-key map `composite-key-map.json` and reference-table map `ref-table-map.json` are **auto-loaded** when in the config directory (no need to pass explicitly). Non-zero exit code = has major.

| Category | What it catches | Severity |
|------|--------|--------|
| `FK_BREAK` | reference column `table.field` broken foreign key: the source has a value not found in the target column (array sources validated member by member; cross-file via refmap) | major |
| `RULE_CARDINALITY` | array member count vs another table's value (e.g. evolution chain length−1 ≤ quality evolvable count) | rule-configurable `severity` |
| `ACC_DANGLING` | an acceptance case's `table[primaryKey].field` reference can't resolve to a config row (missing row = dangling; empty field doesn't count) | advisory |
| `RULE_MONOTONIC` / `RULE_COVERAGE` | a field monotonically non-decreasing with tier / integer primary key contiguously covered with no gap | advisory |
| `FK_SKIP` / `RULE_SKIP` / `UNDOC_TABLE` | cross-doc/unregistered reference, unrecognized array column, no corresponding sheet — **explicitly recorded, not silently missed** | info |
| `0` / empty | foreign-key empty sentinel (when the id domain is always positive, `0`=no reference) → not counted in the break check | — |

**Rule file** `checks/<system>.checks.json` (sample `checks/example.checks.json`, table/field names are all illustrative):
```json
{ "rules": [
  {"type":"cardinality","severity":"advisory","array_table":"evolveLine","array_field":"unit",
   "member_table":"unit","member_rarity_field":"rarity","limit_table":"rarityCap","limit_field":"evolution"},
  {"type":"coverage","table":"levelTable","field":"id","min":1,"max":200},
  {"type":"monotonic","table":"starTable","field":"HpPercentage","order_field":"star","group_fields":["rarity","element"]}
] }
```

### `manifest_check.py` — tool 6 · spine **manifest internal consistency** (pure stdlib)
```
python manifest_check.py <manifest.md>
```
Manages "**is the spine itself right**": whether the cross-table references of the 6 strongly-typed tables (A–F) are self-consistent. `config_check`/`value_check` manage "config ↔ doc," this one manages "spine internals." Non-zero exit code = has major.

| Category | What it catches | Severity |
|------|--------|--------|
| `SEG_MISSING` | an A-table system's R-module-code isn't found in the B-table number-range registry | major |
| `DANGLING_DEP` | an explicit SystemID (`S\d+`) in the A-table「Deps (upstream)」doesn't exist in the A-table | major |
| `BAD_STATUS` | an A/D/E-table status value isn't in the status enum (`Final*` normalized to `Final`) | major |
| `NO_CBLOCK` | an A-table system has no `### <ID>` cross-layer index block in the C table | major |
| `CYCLE` | a mutually-dependent cluster in the dependency graph (Tarjan SCC, edges by system name/ID, self-loops excluded, longer name first), reported once per cluster, hinting that a common type must be globally registered first to break the cycle | advisory (human judgment) |
| `DEFINED_NO_CONTRACT` | a `Final`/`Final*` system block in the C table is missing the proto or acceptance row | advisory |
| `SEG_UNUSED` / `CBLOCK_ORPHAN` | a B-table number range hangs empty / a C-table block lingers (the system was deleted) | advisory |
| `DEP_BY_NAME` | a dependency edge parsed by system name from the prose dependency column (the real manifest dependency column isn't a pure ID) — a transparent declaration | info |

> The real manifest's「Deps (upstream)」column is **prose + reference by name** (`item[broadcast](disassembly material)`), not a clean ID column. So `DANGLING_DEP` only reports major for **explicit `S\d+`** (zero false positives), and the cycle check edges by **system-name substring** and excludes self-loops. **Doesn't catch**: D-table recheck trigger ↔ F-table reconciliation (the trigger items mix point-to-point conventions, machine-checking would heavily false-report, left to humans).

### `ref_graph.py` — tool 7 · design-file **bidirectional reference graph** + dangling-reference gate (pure stdlib)
```
python ref_graph.py <projectRoot> [--out refs.md] [--who-refs <symbol>] [--check] [--json]
```
Scans all design files (`.md`/`.proto`/`.xlsx`), extracts **structured** references (`R-code` / `table[primaryKey]` / proto `import`), giving "each file → who it references / ← who references it (= **its change-impact set**)." Discipline: **the forward reference is the canonical source, the reverse index is computed in real time, never written to disk** — so it doesn't drift the way a hand-written "referenced-by" would. Non-zero exit code (under `--check`) = has major.

| Category | What it catches | Severity |
|------|--------|--------|
| `DANGLING_RULE` | an `R-code` is referenced but defined by no file (a subsystem named in a heading `## … R-X` / a leaf rule at a line start `- **R-X-01**` both count as a definition) | major |
| `DANGLING_PROTO` | `import "x.proto"` finds no corresponding `.proto` file | major |
| `DANGLING_TABLE` | `table[primaryKey]` has no corresponding xlsx table (may also be a false hit on array notation, `[inferred]` needs human verification) | advisory |
| `DUP_DEF` | the same `R-code` appears as a definition point in multiple places (should be uniquely defined) | advisory |

- `--who-refs R-X`: query the change-impact set of "where a symbol (R-code/table name/`x.proto`) is defined + who references it."
- `--out refs.md`: generate the bidirectional graph (**a pure artifact, marked `DO NOT EDIT` at the top, never hand-written into the rules/config-spec/manifest or other canonical docs**; change the docs and re-run to overwrite).
- Recognizes only structured tokens, **does no fuzzy prose matching** (so structured-reference precision is high); the R-code "definition point vs reference point" uses a heading/line-start heuristic, distinguishing the wildcard `R-X-*` from the bold `**R-X**`.

### `ref_lib.py` — shared layer (library, not CLI)
`ref_graph`'s **reference-syntax canonical source**: `RULE_RE` (R-codes), `TABLEREF_RE` (`table[primaryKey]`, the table + primary-key part consistent with `config_index.REF_RE`, the field optional here), proto `import`, plus the "definition point vs reference point" decision, wildcard/array notation filtering, and file discovery. Reuses `xlsx_dump` to fetch xlsx table names. **The reference syntax is concentrated in one place, to avoid multiple tools each writing their own and drifting against each other.**

### `config_index.py` — shared layer (library, not CLI)
Shared by `value_check` and `gherkin_to_checklist`. Provides: `build_index` (scan all xlsx in the config directory → table index, including array columns `arraycols`), `lookup` (`table[primaryKey].field` → real value/`MULTI`/`None`, composite keys matched by component via the keymap, enum names resolved via enums), `row_exists` (distinguishes "missing row" from "empty field"), `column_values` / `array_column_values` (foreign-key value domain), `load_enums` / `load_keymap`.

### `gherkin_to_checklist.py` — acceptance cases → planner-version checklist xlsx (openpyxl write)
```
python gherkin_to_checklist.py <acceptance.md> [out.xlsx] \
  [--config <configDir>] [--enums <enums.md>] [--keymap <composite-key-map.json>] [--loc <LocalizationText.xlsx>]
```
Translates Gherkin acceptance cases into a planner/QA item-by-item checklist (info page + test-checklist page + progress stats). With `--config`, **substitutes the config real values** for the `table[primaryKey].field` in the assertions (reverse-validating config↔rule consistency); guardrails: multi-key/can't-find marked `[fill-in needed]`/`[can't find]`, **never fabricated**.

### `xlsx_dump.py` — portable xlsx → text (pure stdlib, foundation)
```
python xlsx_dump.py <file.xlsx> [out.txt] [max_rows]
```
`zipfile`+`ElementTree` parses xlsx directly (bypassing openpyxl's style error), the **common foundation** for all the xlsx-reading scripts above. For Chinese, be sure to write a file and then view it (printing to the console directly may garble).

### `resolve_loc.py` — LocalizationText text id → Chinese (pure stdlib)
```
python resolve_loc.py <LocalizationText.xlsx> [out.txt] [start-end ...]
```
Builds a text id → Chinese map, for `gherkin_to_checklist --loc` to attach Chinese to NameId/DescId.

---

## Project metadata (placed in the config directory, alongside the xlsx; auto-loaded by value_check/gherkin)

| File | Role |
|------|------|
| `composite-key-map.json` (composite-key map) | composite-primary-key table → component column order (e.g. `starTable: [rarity,element,star]`), for `lookup` to match by column |
| `ref-table-map.json` (reference-table map) | a human/doc name in a reference column → English `table.field` (e.g. `itemList→item.id`), for cross-file foreign-key resolution; **external/not-yet-built systems are intentionally not registered** (registering would produce unfixable false majors) |
| `enums.md` (enum dictionary) | enum name/Chinese → id (in the global spec, not the config directory), for `lookup` to resolve enum names in composite keys |

## Tests

`tests/test_*.py`, **a stdlib-bundled runner, no pytest dependency**:
```
python tests/test_value_check.py      # a single one
```
Each test file's `if __name__=="__main__"` runs all `test_*`, prints PASS/FAIL, sets the exit code by failure count; cases needing Pillow skip gracefully. The logic layer uses in-memory fixtures (no xlsx written, table/field names all illustrative), pure stdlib, no project dependency.

Run the whole set:
```
for t in tests/test_*.py; do python "$t" | tail -1; done   # automatically includes manifest_check / ref_graph etc.
```

## Where it wires into the gate

- **After writing the spine (each skill's "write back" step)**: run `manifest_check`; if there's a major → fix spine self-consistency first (module-code registration / dependency pointing / status / C block) before continuing. The template self-check section is in the「Self-check commands」at the end of `templates/manifest.tpl.md`.
- **`aigd-handoff` finalization admission**: before finalizing always run `config_check` + `value_check`; if there's a major → send it back.
- **Quality gate (methodology Step 4, eight items)**: the two items「every config field has type/range/reference」and「cross-table/cross-file references have no broken links」hang on these two machine-check commands — **don't just tick a box self-assessed** ("doc defined first, xlsx changed later out of sync" is the number-one root cause of forked downstream-implementation reads of the handoff package).
- **(Optional) reference integrity**: run `ref_graph <root> --check`; a dangling `R-code`/proto = failure (reinforcing the "references have no broken links" item); routinely use `ref_graph <root> --who-refs R-X` to query "which docs/acceptance/proto changing this rule will affect."

## Typical flows

**Screenshot into the library**: `aigd-ui-capture` (tool 1) → `<screenID>.md` → `ui_render` (restore for verification) + `ui_palette --merge` (sample colors) [+ `ui_slice` (split assets)] → into `patterns/ui-patterns/`.

**Config finalization validation**: `config_check` (schema) + `value_check` (data integrity) → **both 0 major** to pass → `gherkin_to_checklist --config` (output the planner-version checklist + reverse-check the config).
