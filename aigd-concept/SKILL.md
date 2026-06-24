---
name: aigd-concept
description: AIGD Phase 1 · brainstorming & top-level design. Use this when you want to set the concept for a new game, fix the core loop / platform / target users, or split the game into a system list + dependency graph and start the project spine. Produces / revises the project charter + manifest (system list). Part of the aigd package; methodology in ../aigd/references/.
---

# AIGD · concept (brainstorming + top-level design)　[minimal skeleton]

> **Package contract**: install the whole `aigd` package (the orchestrator `aigd/`+`references/` and the 6 sub-skills (including aigd-ui-capture) placed at the same level in this environment's skills directory, following the host agent, e.g. Claude Code's `.claude/skills/`), **don't copy this skill alone** — the body's `../aigd/references/` depends on `aigd/` at the same level, copying it alone breaks the link.

## Positioning
Phase 1. Diverge in discussion → converge into "what to make + which systems it's made of". **Low-frequency but repeatedly revisable** (deeper discussion will circle back to change the concept / platform / system list) — it writes the live spine, not a one-shot artifact.

## Read / produce / write back
- **Read**: existing spine (if any); `../aigd/references/methodology.md` (the naming / numbering / spec parts).
- **Produce / write back** (fill per template, see `../aigd/references/templates/`):
  - `project-charter.md` (per `project-charter.tpl.md`): concept / core loop / pillars / platform / target users / **project-specific conventions** (naming / units / quality system…).
  - `manifest.md` (per `manifest.tpl.md`): system list + dependency graph + number-range pre-allocation + cross-layer index placeholders (Status = Draft).

## Recipe
1. Interview: core experience / core loop / design pillars / monetization / art direction; **cut the weak directions**.
2. Split into systems: per the "system-splitting rules" below, fix boundaries → list the systems, draw the dependency graph (edge set), fix the build order; cycle detection → common types are **registered first in the project layer (global spec)** to break cycles (made concrete as `proto/common.proto` later at handoff). **Also flag "emergent combinations"** (those that only make sense when several systems are combined, e.g. combat = movement + skills + damage + AI) — register them as "combination points", leaving them for sync to do **up-front integration design** rather than patching them in afterward.
3. Per template, write `project-charter.md` + `manifest.md` (one row per system, Status = Draft) + stand up the global-spec skeleton (enum / naming / unit placeholders).

## System-splitting rules (the ruler for "one system" in the manifest)
Must meet **≥2 of the following** to stand alone as a system, otherwise merge into the parent:
- **Has its own config table** (not just consuming someone else's table);
- **Has an independent rule boundary** (can be explained apart from other systems);
- **Can be playtested independently** (if the game still runs with it turned off, it's an optional module, not a system);
- **Has an independent state machine / lifecycle**.
Meets all of them → consider splitting further into subsystems (`system/subsystem` two levels).
Counter-examples: "damage formula" is a rule of combat, not a system; "red-dot notification" is a cross-system mechanic, belongs in the global spec.

## Admission / exit
- **Admission**: none (starting from scratch), or an existing old spine (then it's a revision).
- **Exit**: `project-charter.md` + `manifest.md` (system list + dependency graph + number-range pre-allocation) complete → only then proceed to `aigd-system`.

## Boundary
Produces only the spine and top-level design, doesn't get into single-system detail (that's aigd-system).
