---
name: aigd-system
description: AIGD Phase 2 · single-system design (discussion-driven). Use this when you want to build out a system — rules (-01, tagged with R-numbers), config table (with test data), system html prototype. The source xlsx is optional (read it if given, otherwise rely on interview). Part of the aigd package; full methodology in ../aigd/references/methodology.md.
---

# AIGD · system (single-system design)　[minimal skeleton]

> **Package contract**: install the whole `aigd` package (the orchestrator `aigd/`+`references/` and the 6 sub-skills (including aigd-ui-capture) placed at the same level in this environment's skills directory, following the host agent, e.g. Claude Code's `.claude/skills/`), **don't copy this skill alone** — the body's `../aigd/references/` depends on `aigd/` at the same level, copying it alone breaks the link.

## Positioning
Phase 2. One pass per system. **Produces only the three "cheap, will-change-during-iteration" things**: rules / config (test data) / system prototype.
**Interface contract / acceptance cases / backend algorithms are not in this phase** — deferred to `aigd-handoff` (after finalization), to avoid locking things down while the design is still changing and wasting churn.

## Read / produce / write back
- **Read**: this system's entry in the `manifest` (dependencies, referenced shared sources of truth), the `project charter`; `../aigd/references/methodology.md` (it is authoritative).
- **Produce** — the paths below are an engineering-layout example, **the actual directories/filenames defer to the `project charter"directory layout · naming conventions"`** (same source as the manifest cross-layer index):
  - `docs/systems/<system>/rules.md` (-01, tagged with R-numbers, prose with no bare numerals).
  - `config/source/<table>.xlsx` (**with test data**) + config spec.
  - `docs/prototypes/<system>.html` (single file, zero-dependency, clickable; illustrative data on the same scale as the config).
- **Write back**: this system's cross-layer index in the `manifest` + Status = Draft; new enums / R-numbers registered in place into the global spec.

## Methodology
**Defers to `../aigd/references/methodology.md`** (this skeleton does not copy it). Be sure to remember: contract / acceptance / backend belong to handoff, not produced in this phase.

## Admission / exit
- **Admission**: this system's status in the manifest = `Draft`, and **all its dependency systems are at least `Draft`** (otherwise the base map is missing, go back to concept to fill it in first).
- **Exit**: rules.md + config table (test data) + system prototype.html complete, manifest cross-layer index written → move to `aigd-iterate`.

## Boundary
Doesn't lock the contract, doesn't write acceptance, doesn't do balancing (filling in test values for numbers is enough; deep balancing is an out-of-package discipline).
