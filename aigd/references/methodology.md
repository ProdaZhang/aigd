# AIGD Methodology · The 6-Piece Set (portable core)

> Migrated in from the former single `aigd` skill. This is the canonical source for how AIGD produces a **single-system design**, referenced by `aigd-system` / `aigd-handoff`.
> Note: every concrete directory path, quality/rarity enum name, module-code prefix, etc. that appears in this text is **illustrative**; the real values are parameterized item by item by the **project charter** — the methodology itself is **not bound to any project**. Switching projects only swaps the project charter; the method stays the same.
> Also note: deliverables are split into **two phases** (see Step 3 A/B): the iteration phase (system/iterate) only produces rules/config/prototype; contract/acceptance/backend are generated **after finalization** by `aigd-handoff` — don't lock a contract while the design is still fluid.
> **Project-environment prerequisite**: this package requires only one thing — a **change ledger** (default: project-root `CHANGELOG.md`). Spine re-entrancy relies on it for backfill. **If the project has none → on the first run, create it from `references/templates/CHANGELOG.tpl.md`**; **if a ledger already exists (under any name), reuse it, don't start a new one**; its location can be set in `project-charter"Directory Layout"`. Backfill is enforced by Step 5 + gate item 8, and **does not depend on any host-AI instruction file** — CLAUDE.md / AGENTS.md / GEMINI.md etc. are concerns of the runtime environment; AIGD neither creates nor depends on them (stuffing "create CLAUDE.md" into the methodology would bind it to a particular harness, contradicting portability).

---

> **Skim before working**: [`gotchas.md`](gotchas.md) (execution/handoff/validation pitfalls this package has actually hit: malformed tool calls silently not executing, sentinel collisions, config↔doc desync, validator false positives, blindly trusting sub-agent assertions…); domain numeric pitfalls in [`patterns/numeric-traps/numeric-traps.md`](patterns/numeric-traps/numeric-traps.md); interview-domain ammunition in [`patterns/loops/`](patterns/loops/).

## Core stance
The entry point is a **design discussion**, not "hand over a design doc first." Talk through the rule points, numeric conventions, and UI intent with the user, mark 【to-confirm】 on the spot, and only produce output once you've agreed. The source xlsx (design doc/config) is **optional fuel** — read it if given and align to it as the canonical source; if not given, fill the gaps by interview, and **never hard-code numbers on the user's behalf**.

## Step 0: Read the canonical source (do this every time, with Read, never from memory)

> **Read the spine first, don't read hard-coded project filenames.** Below, "what to fetch" is generic; "where to fetch it" is always decided by `project-charter"Project-Specific Conventions"` + the global-spec paths it points to — switch projects and it follows automatically, never coming up empty.
> **If the new project's spine isn't built yet** → run `aigd-concept` first to build the spine (come back once the sources in this table are in place); this package depends on no project-specific filename.

| What to fetch | Where to fetch it (decided by the project charter, not hard-coded) |
|--------|----------------------------------|
| Directory layout / naming / units / quality system / module-code style | `project-charter"Project-Specific Conventions"` |
| Reference syntax, `R-` numbering rules + already-used module-code ranges (pick a code, avoid collisions) | Global spec · numbering registry (the spec directory designated by `project-charter"Directory Layout"`) |
| Existing enums — reuse first, don't redefine | Global spec · enum dictionary (same spec directory as above) |
| Term CN↔EN glossary | Global spec · glossary (same) |
| UI-prototype visual canonical source (brand + dimensions) | The visual spec designated by `project-charter"Art Style / Brand"` |
| Samples to imitate in form / granularity / README | Any already-finalized system in the project (if any) |

## Step 0.5: Read the source xlsx only if there is one (optional) — parsing has pitfalls

- **openpyxl reading xlsx exported by domestic (Chinese) tools throws `Colors must be aRGB hex values`** → switch to `zipfile` + `xml.etree.ElementTree` and parse directly: `xl/sharedStrings.xml`, `xl/workbook.xml` + `xl/_rels/workbook.xml.rels` (sheet name ↔ file), and the `sheetData` of `xl/worksheets/*.xml` (`t="s"` → take from sharedStrings, `inlineStr` → take from `<is>`, otherwise take `<v>`).
- **Write Chinese to a UTF-8 file then view it with Read** (printing directly garbles). The dump exports the first 4 header rows along with the data, so the schema is self-evident.
- **Reusable parsing scripts are in `references/scripts/`**: `xlsx_dump.py` (parses any domestic xlsx — the zipfile+xml implementation above) / `resolve_loc.py` (LocalizationText text id → Chinese). They're argv-driven with no project hard-coding: just `python …/xlsx_dump.py <table> <out.txt>`.
- **Dump artifacts** (intermediate files like `dump_*.txt`) go in the working directory and are **cleaned up after confirmation** — what gets cleaned is the **artifact**; the reusable **script** is already in the package, don't clean it.
- **Self-describing header**: row 1 = the table's English name (kv tables carry `kv:`), row 2 = type, row 3 = field key (arrays `field[…]`, object-arrays `field.sub[{a|b|c}…]`), row 4 = Chinese name; rows 5+ = data. Three kinds of **side-note columns** are ignored on import and exist only for humans: **plaintext columns** (Chinese to the right of a text id), **derived columns** (code-generated statistics), and **legend blocks** (enum explanations pasted at the table's tail).

## Step 1: Design interview (talk the system out)

Proactively ask item by item and decide on the spot: **intent/boundary**, **core rule points** (each tagged with an R-code), **numeric conventions** (don't decide for them, list 【to-confirm】), **UI intent** (image preferred if available), **config expectations** (which tables/primary keys are needed), **which enums/module-codes to reuse**.
- Ask back item by item for whatever's missing, don't fill in from imagination; list pending items as 【to-confirm】 for the user to decide.
- If a source xlsx was given and it conflicts with the verbal/design-doc account → **first determine the config's origin, then decide which is authoritative** (to avoid locking stale/junk/test data into the spine): planner hand-filled → config wins, mark verbal discrepancies `[to-confirm]`; tool-exported → interview wins, mark config discrepancies `[to-confirm]`; origin uncertain → list both ends, mark all `[to-confirm]`, **don't decide for them**. In every case, faithfully write "design doc says X, config currently Y"; don't fill in fields on their behalf.
- No source xlsx at all → the interview conclusion is the canonical source; anything involving numbers is uniformly `[to-confirm]`.

## Step 2: Set the directory and naming

> **Directory layout/naming is governed by `project-charter"Directory Layout · Naming Convention"` — it is the single switch.** What follows is one common layout (the system's 6-piece set `-0X` in the same directory, flat); if the project charter chose the engineered layout (`docs/` + `proto/` + `config/` split apart, see the `manifest` cross-layer index / `Implementation Overview`), go by that. The two are just different values of `Directory Layout`, **not two different methods** — don't copy the paths below over the project charter.
> **Migrating an existing flat project = MOVE the canonical source, not COPY**: copying makes flat and `docs/` drift into dual canonical sources. Migrate in one shot and abandon the flat path afterward; if a coexistence transition period is unavoidable, **clearly mark which side is canonical**. The per-piece naming map is in `project-charter.tpl`「Layout-Switch Naming Map」.

- One system = one directory, placed under the corresponding zone as `<zone>-<sub-seq><sub-name>-<system-seq><system-name>/`. Before touching an existing file, look first and confirm first (not git).
- File naming = `<full-folder-name>-<two-digit-seq><file-type>`: `-01systemrules.md` / `-02config-spec.md` / `-03ui-prototype.html` / `-04interface-contract.proto` / `-05acceptance.md` / `-06backend-dev.md` (as needed).
- **Pick a unique module-code** `R-<module>` — check the numbering-range table first to avoid collisions, register after creating.
- Cross-system references are **position-independent** (`tableName[primaryKey].field` / `screenID.elementID` / `R-code`).

## Step 3: Produce output (the two-phase split — the key to deferred shaping)

> The iteration phase produces only the "cheap, will-change" things; the "expensive, downstream" things wait **until finalization** to be generated by `aigd-handoff`. Don't lock the contract while the design is still fluid.

### A. system-phase output (iteration phase · aigd-system / aigd-iterate)

1. **-01systemrules.md** — feature rules, each program-judgeable rule tagged `R-<module>-<subsystem>-<seq>`; prose has **no bare numbers** (write only formulas + field references); the second part writes the **UI DSL** (`# screenIdUI` + `## Layout` indented tree [`:source` `[state]` `×N`] + `## Events` `<trigger> <element> [guard] -> result`, tagged with R-codes).
2. **Lightweight registration of enums/units/module-codes** — the rules need to reference them, so register them in place: write new enums / R-module ranges into the **global-spec file** designated by `project-charter"Directory Layout"` (**for example**: in this project = `enum-dictionary.md` / `id-and-units-convention.md`) (pure runtime enums / error codes can wait for the contract phase).
3. **-02 config-spec + config tables (test data)** — for each table, field by field: type/range/reference/enum annotations + a validation checklist; if config is already filled → only describe + validate broken links, never overwrite; if it doesn't exist → provide an empty xlsx with a self-describing header **and fill in test data** (for prototyping and playtesting); if there's no standalone table → clearly write the external-table dependencies it consumes.
4. **-03ui-prototype.html** — generated from the DSL of -01 as a vector clickable wireframe, **single file, zero dependencies, works offline**. May be delegated to a sub-agent; must be acceptance-checked after production: no BOM, zero external links, all screens present, interactions in place; **the sample data is in the same units as the canonical config source**.
   - **Applicability boundary**: it's sufficient for UI-dense systems (inventory/shop/progression); for **real-time combat/physics/multiplayer interaction**, a clickable wireframe only validates information architecture and flow, and **cannot validate feel/timing/networking** — leave that "feel" to a later engineering prototype or dedicated validation; don't treat the html prototype as having already validated feel/numbers.
5. **README.md (draft)** — placeholder first: the 6-piece set cross-reference + entry points; fill in fully at finalization.

### B. handoff-phase output (after finalization · aigd-handoff)

6. **-04interface-contract.proto** — protocol + archive + runtime + error codes, client = server, the same single file; draw the number range from the manifest.
7. **-05acceptance.md** — Gherkin, each tagged with an R-code, normal + boundary, assertions using proto fields + `table[primaryKey].field`.
8. **-06backend-dev.md (as needed)** — write only when there's a server-side fetch+compute decision that exists beyond the rules/contract.
9. **Planner-version acceptance checklist (md+xlsx)** — see `handoff-checklist.md`.
10. **README.md (final)** — the 6-piece set cross-reference table + entry points for 5 role types + the ID-threading closed-loop diagram + the gate self-check table + external dependencies / to-confirm.

## Step 4: Quality gate (eight items, mark the result of each in the README)
① every program judgment / test assertion has an R-code ② every R-code has ≥1 scenario in acceptance ③ every config field has type/range/reference, enums entered into the dictionary ④ prose has no bare numbers ⑤ protocol/archive are typed, the same single file on both ends ⑥ every clickable UI element has interaction + state, the prototype is zero-dependency and works offline ⑦ no duplicate definitions of enums/units/IDs ⑧ changes written to CHANGELOG (the change ledger). Any item failing → fix until it passes.

## Step 5: Backfill CHANGELOG (the change ledger, hard requirement — see "Project-environment prerequisite")
After each file change, append `| YYYY-MM-DD HH:mm | file | content | reason | model |` to the end of the project ledger (default root `CHANGELOG.md`; reuse the project's existing ledger name) (format / initialization in `references/templates/CHANGELOG.tpl.md`; if the project has no such ledger → create it from the template first, then backfill).
- **Don't use a bare `|` in the content column** (it breaks the table) — use `/` or `\|`.
- When delegating to a sub-agent, have it append the same way; for parallel writes to the same file, re-read the tail before appending — don't overwrite.

---

## Hard constraints (don't violate)
- Files are **UTF-8 without BOM** (adding a BOM / turning into UTF-16 garbles things downstream for Chinese); per-harness specifics in `harness-adapt.md` (Claude Code's Write defaults to no BOM; PowerShell writing Chinese needs `UTF8Encoding $false`).
- The repo is **not git**; delete/rename is irreversible — before touching an existing file / deleting a temp artifact, look first, confirm first; **don't touch / don't overwrite** the user's source xlsx and already-filled config.
- Per-myriad (basis points) uniformly `/10000`; reference by name (position-independent).
- **Config tables are uniformly pooled in the project-level global pool** (`config/source/` etc.), with **no per-system private tables**: any system references by name, position-independently, without monopolizing; don't treat a table as private to one system (`base` / `property` = attribute source etc. are pure global sources with no single maintaining system; for maintainers see manifest「reverse-provides」). A cross-system reference to one table = an ordinary reference, and does not constitute a system dependency edge.
- **Broadcast-type shared canonical sources** (an id namespace / text structure / enum referenced by most systems) are **append-only, never break** (enums only add values, don't drop meanings; tables add fields, don't drop fields; ids aren't reused); only a breaking change notifies referencers — **don't manage it with "mark systems for recheck one by one"** (fan-out = the whole project blows up; register it in the `manifest` F table).
- **Don't mix multiple quality/rarity enums**: a project often has several mutually unrelated quality dimensions (e.g. item rarity, equipment quality, character quality — each a separate set, with different numeric domains / tier counts); each is managed separately, don't share one enum; which sets exist is registered in `project-charter"Quality System"`.
- **Tool calls must use the function-call block format your harness requires**, or they may silently fail to execute (the file isn't written but you think it was) — after sending, double-check the artifact actually landed on disk with read-file / `ls`. Per-harness specifics in `harness-adapt.md` (e.g. Claude Code requires the `antml:` namespace prefix).
