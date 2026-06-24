# AIGD references — the bundled canonical methodology source (portable core)

The methodology lives here, **depending on no project**; project-specific things are carried by the **spine** (project charter / manifest / implementation overview). Switch projects, switch AI — read the spine and you can take over.

## What exists
- **methodology.md** — the 6-piece skeleton / design interview / naming / numbering / self-describing header / UI DSL / the eight quality gates / hard constraints (migrated in from the former single `aigd` skill).
- **templates/** — the three spine templates (strongly typed): `project-charter.tpl.md` / `manifest.tpl.md` / `impl-overview.tpl.md`; + the change-ledger template `CHANGELOG.tpl.md` (the only project-environment prerequisite). `aigd-concept` builds the spine from them, and the later skills read/write the spine by its columns.
- **ui-dsl-spec.md** — the **authoritative** UI DSL grammar contract (file skeleton / Layout-line grammar / type table / z layering / shape / source semantics / image-reading recipe / skin and theme); `aigd-ui-capture`'s Step 0 and the renderer go by it.
- **scripts/** — reusable deterministic tool scripts (argv-driven, no project hard-coding). **See `scripts/README.md`** (tool list/usage/dependencies/gate integration/flow). Two main lines:
  - **UI knowledge base**: `ui_render.py` (tool 2 · DSL→html/svg, pure stdlib) / `ui_palette.py` (tool 3 · color sampling→skin section) / `ui_slice.py` (tool 3 · slicing→contact sheet).
  - **Config / handoff validation**: `config_check.py` (tool 4 · config-spec ↔ xlsx schema drift) / `value_check.py` (tool 5 · data integrity: broken foreign keys / dangling acceptance / cardinality·monotonic·coverage) / `config_index.py` (shared layer) / `gherkin_to_checklist.py` (acceptance cases → planner-version checklist). Wired into `aigd-handoff`'s finalization admission gate + template §7 quality gate.
  - **Foundation**: `xlsx_dump.py` (zipfile+xml parses any domestic xlsx, bypassing openpyxl's `Colors must be aRGB` error) / `resolve_loc.py` (LocalizationText text id → Chinese). `checks/<system>.checks.json` domain rules + `tests/` (stdlib runner).
- **example.skin.json** — a **sample** theme skin by type, applied as a demo by `ui_render.py --skin`; users replace the coloring per their own visual spec (designated by project-charter"Art Style / Brand").
- **handoff-checklist.md** — an `aigd-handoff` sub-capability: the recipe and read/write contract for config → planner-version acceptance checklist (md + xlsx) (already test-run, passing).
- **patterns/** — **domain-knowledge ammunition** (the methodology gives "process", this gives "domain knowledge", for concept/system to use as an interview guide — cutting weak directions and proposing conventions):
  - `loops/core-loops.md` — 5 core-loop templates (collect-progress-validate / explore-build / PVP / gacha-push-stages / economy), each with driving variable · feedback · stall point · what to ask in the interview.
  - `loops/battle-unit-progression.md` — the multi-axis battle-unit progression paradigm (collect-progress genre: collection-unit ≠ form-unit, quality cap, cumulative vs incremental, fill-out data, parameterized unlocking).
  - `numeric-traps/numeric-traps.md` — 10 numeric/economy traps + ⚠️ actually-hit ones (sentinel collision / cumulative confusion) + a trap ↔ machine-check tool quick reference.
  - `ui-patterns/` — the UI DSL library where `aigd-ui-capture` archives competitor/own screenshots (accumulated as you go).
- **gotchas.md** — a quick reference of pitfalls actually hit during this package's iteration + consumer-side validation (pointed to by `methodology.md`, skim before system/handoff).
- **harness-adapt.md** — cross-harness install/invocation/tool-name mapping + tested status: the package structure is common to Claude Code / ZCode / Gemini / Codex (all tested, including the two cross-vendor ones Gemini/Codex); **Copilot 1.0.63 has no skills mechanism and needs adaptation**.

## To be filled in (TODO, to flesh out after building the package)
- **numbering-and-units-rules.md / quality-gate.md / naming-convention.md** — currently inlined in「methodology.md」; the concrete content is in each project's global spec (the path goes by the spec directory designated by the spine's「project charter」, not a fixed in-package path). To be later extracted into a **portable copy**.
- **patterns/ domain-knowledge ammunition** — the minimal starter pack has landed (core loops / battle progression / numeric traps, see「What exists」above); **keep accumulating with the project** (more gameplay paradigms, genre-specific pitfalls, and UI paradigms archived by ui-capture).

## Project layer vs package layer (don't mix)
- **Package layer (here)** = methodology, templates, recipes, common across projects.
- **Project layer (spine)** = concept/platform/conventions/system list/number ranges/cross-layer index, one instance per project.
- A sub-skill = an operation on the spine: **read the spine → do the work → write back the spine**, fetching the methodology from here.

## Packaging and portability (decided: the whole package as a unit)
**Decision**: `aigd` is distributed/installed as **one inseparable package**; copying a single sub-skill on its own is not supported.
- **Package contract** (written at the top of every sub-skill): a whole-package install = the orchestrator `aigd/` (including `references/`) + the 6 sub-skills (`aigd-concept/system/iterate/handoff/sync/ui-capture`) **placed as siblings in this environment's skills directory** (following the host agent, e.g. Claude Code's `.claude/skills/`); the sub-skill body fetches the methodology via `../aigd/references/`, so `aigd/` must exist as a sibling.
- **Single canonical source**: there's only one copy of references (`aigd/references/`), **not copied** — to forestall drift.
- **Why not the other two options**:
  - (B) sub-skills carry their own references copy → the methodology is still evolving, and 5 copies (one per sub-skill) will inevitably drift, with each change needing 5 syncs, not worth it;
  - (A) make it a plugin → would introduce the `aigd:concept` namespace, changing the established flat name `aigd-concept`, unnecessary during the evolution phase.
- **Upgrade path**: when someday we want "install one and it just works" (standalone install / marketplace distribution) and the methodology has stabilized → upgrade to a **plugin** (option A), accepting the `aigd:concept` namespace at that point, with references traveling with the package. For now, don't solidify too early.
