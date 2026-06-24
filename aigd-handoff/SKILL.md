---
name: aigd-handoff
description: AIGD Phase 4 · finalize and generate the handoff package. Use this when, after a system is finalized in playtesting, you want to generate the interface contract, acceptance cases, (as needed) art/client/server docs, and the designer-facing acceptance checklist. Produces platform-agnostic handoff artifacts that "another AI can develop directly from". Part of the aigd package; methodology in ../aigd/references/.
---

# AIGD · handoff (finalize → handoff package)　[minimal skeleton]

> **Package contract**: install the whole `aigd` package (the orchestrator `aigd/`+`references/` and the 6 sub-skills (including aigd-ui-capture) placed at the same level in this environment's skills directory, following the host agent, e.g. Claude Code's `.claude/skills/`), **don't copy this skill alone** — the body's `../aigd/references/` depends on `aigd/` at the same level, copying it alone breaks the link.

## Positioning
Phase 4. **Finalization gate**: only entered once the user signs off on playtesting; if generation exposes a design hole, **bouncing back to `aigd-iterate` is allowed**. This is where the "expensive, downstream" artifacts are generated (not produced during iteration).

## Read / produce / write back
- **Read**: this system in the `manifest` (rules/config/referenced shared items), the `project charter`, `../aigd/references/methodology.md`.
- **Produce (mandatory, platform-agnostic)** — the paths are an engineering-layout example, **the actual ones defer to the `project charter"directory layout · naming conventions"`**:
  - `proto/<system>.proto`: import `proto/common.proto` (the common types that concept/manifest registered in the global spec, **made concrete / added into `common.proto` here** — the landing point for breaking cycles; the first handoff to use it is responsible for creating it, later ones add to it), draw the number range (protocol numbers / error codes) from the manifest.
  - **proto formula comments**: for every message that has a computation formula, give in the comment the **formula with field references substituted in**, so the implementing AI can transcribe it directly without reverse-engineering it from prose rules. Example:

    ```proto
    // damage: damage = atk * coefficient - def
    // field refs: atk=Actor.atk, coefficient=Skill.damage_coef, def=Target.def
    message DamageResult { int32 damage = 1; int32 atk = 2; int32 coefficient = 3; int32 def = 4; }
    ```

  - Engineering-grade `acceptance cases` (Gherkin, tagged with R-numbers, assertions using proto fields + `table[primary key].field`).
- **Produce (as needed)**: art needs / client dev docs / server dev docs (-06); **designer-facing acceptance checklist (md + xlsx)** — see `../aigd/references/handoff-checklist.md`.
- **Write back**: this system in the `manifest` — Status = Final, occupied number ranges, references / referenced-by, recheck triggers.

## Solidified sub-capabilities
- **Designer-facing acceptance checklist generator**: `../aigd/references/handoff-checklist.md` (config → md+xlsx, already test-run and passing; side effect: automatically catches config contradictions and produces `[to confirm]`).
- **Config-consistency checker (must run at the finalization gate)**: `../aigd/references/scripts/`
  - `config_check.py <config-spec.md> <table.xlsx>` — schema drift (undocumented columns / type mismatch / table-name drift / declared-domain out of range).
  - `value_check.py <config-spec.md> <config dir> [--acc <acceptance.md>] [--rules <system.checks.json>] [--enums <enum-dictionary.md>]` — data integrity (foreign-key breakage / dangling acceptance references / domain rules such as evolution-chain length ≤ evolvable times).
  - **Non-zero exit code (has major) = config↔doc out of sync, bounce**. Turns "that self-assessed ✅ checklist at the end of the config spec that nobody runs" into a machine check — experience: doc fixed first, xlsx changed later without re-sync is the #1 root cause of the handoff package being read into forked implementations downstream.

## Admission / exit / bounce
- **Admission**: the user explicitly says "finalize" (satisfied with playtesting); the dependency systems' common types / shared tables are ready.
- **Exit**: proto + acceptance cases (+ as needed client-server docs / designer-facing checklist) complete, this system's status in the manifest = `Final`, number ranges registered → triggers `aigd-sync`; **and `config_check` + `value_check` have no major** (if they do, treat it as a design hole and bounce).
- **Bounce**: generation exposes a design hole → status back to `Playtesting`, back to `aigd-iterate`; and per the manifest "bounce rules" reverse-look-up `depended-on-by`, marking already-finalized systems that depend on this one as `Recheck`.

## Boundary
Goes only as far as "an AI can develop directly from" handoff artifacts; doesn't write client/server code in a specific tech stack (that's the downstream landing skill).
