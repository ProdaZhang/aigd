---
name: aigd
description: AIGD (AI Game Design) main entry / orchestrator. Use this when the user wants to **start a game project from scratch**, is **unsure which phase to use**, wants to **survey or advance the entire development pipeline**, or needs to **maintain the project spine (project charter / manifest)**. This skill only does "read the spine → judge progress → dispatch to the matching sub-skill"; **if a specific step is already clear (concept / build a system / iterate / finalize / sync-back / screenshot capture), use the corresponding sub-skill directly** (aigd-concept / aigd-system / aigd-iterate / aigd-handoff / aigd-sync / aigd-ui-capture). The methodology ships with references/ and does not depend on any specific project.
---

# AIGD · orchestrator

AIGD = **AI Game Design**. A **portable** AI game-development methodology package: covering **brainstorming → system design → playtest iteration → finalization & handoff**, producing a **handoff package** (platform-agnostic) that "another AI can develop directly from"; **landing the implementation (picking a tech stack to write the client/server) is not in this package** and is left to a future dedicated landing skill.

> Status: **skeleton**. The sub-skills and parts of the references still need fleshing out (see the TODO in each file / `references/README.md`).

## Core model (details defer to references/)
- **Two layers**: ① the live **project layer (spine)** — `project charter` (concept / platform / target users / genre / style / naming conventions) + `manifest` (system list + dependency graph + cross-layer index + freeze ledger + number-range registry), continuously revised; ② the **per-system production loop**.
- **Centralized source of truth**: enums / numbering / interface contracts / config tables belong to the project layer; **dual copies** (system + global): acceptance / resource needs / prototype; **system-layer only**: rules / backend algorithms.
- **Every operation**: read the spine → do the work → write back to the spine. Lower-layer discoveries (new system / new dependency / new enum / changed concept) write back up to the upper layer.
- Methodology source of truth: `references/methodology.md`, `references/README.md`.

## Routing: dispatch a sub-skill by "what you want to do this time"
| What you want to do | Sub-skill |
|---|---|
| Concept / core loop / platform / target users / split into systems | **aigd-concept** |
| Design a system (rules + config test data + html prototype) | **aigd-system** |
| Optimize a system after playtest (rules/config/prototype, repeatable) | **aigd-iterate** |
| Finalize a system → contract / acceptance / client-server docs / designer-facing acceptance checklist | **aigd-handoff** |
| Sync back the global spec / overall prototype / implementation master guide; mark recheck on shared-item changes | **aigd-sync** |
| UI screenshot → UI DSL (build up the patterns UI-paradigm knowledge base, for design-time retrieval & reference) | **aigd-ui-capture** |

## Usage
1. **Read the spine first** (project charter + manifest) to judge: which step the project has reached, what state this time's system is in, what's missing.
2. No spine → start the project with `aigd-concept` first (build the spine).
3. Pick the matching sub-skill and **invoke it with the Skill tool** to run; every sub-skill reads and writes the same spine, keeping it consistent and re-entrant (can be picked up across sessions / by another AI).
4. Typical path: concept (once) → per system {system → iterate… (repeated) → handoff finalize} → sync (continuous). **iterate does not go straight into sync** — sync admission requires the system to be already `Final`, and only handoff can finalize; ordering is not enforced, route as needed.

> **When there's no spine** (first time using it on a project, `project charter` / `manifest` don't exist yet): "read the spine" comes up empty → route directly to `aigd-concept` to start the spine; this is normal, not an error.

## Opening self-check (run on every entry into /aigd — proactively drive forward, don't wait for the user to guess)
1. **Does the spine exist?** Yes → read `project-charter.md` + `manifest.md`; No → route to `aigd-concept` to start the project.
2. **Which systems have status ≠ `Final`?** List them, ask the user which to push this time.
3. **Any `Recheck` systems?** Remind to recheck first (some shared item changed) → route to `aigd-sync` to settle (recheck pass → back to `Final` / fail → bounce back).
4. **Number-range conflicts / cycles in the dependency graph?** Check and report.

## State transitions (non-linear · with rollback)
```
concept ──→ system design ⇄ playtest iteration ──→ finalize ──→ integration
 ▲             │              │            │(bounce)
 │             │              │            ▼
 │             └─boundary mis-drawn──┴────→ back to playtest / back to concept
 └────────── integration finds incompatibility / needs re-split ──────────┘
```
- Any **bounce / re-split** records an entry in the manifest "rollback log", and per the "bounce rules" reverse-looks-up `depended-on-by`, marking already-finalized downstream systems as `Recheck` (see `aigd-handoff` / `aigd-sync`).
- Templates: `references/templates/` (project charter / manifest / implementation master guide, strongly typed).

## Package structure (install the whole package, don't split it)
`aigd` (this orchestrator, containing the `references/` methodology and templates) + 6 sub-skills `aigd-concept / system / iterate / handoff / sync / ui-capture`, **installed at the same level in this environment's skills directory** (following the host agent, e.g. Claude Code's `.claude/skills/`). Sub-skill bodies use `../aigd/references/` to fetch the methodology → `aigd/` must exist at the same level (`aigd-ui-capture` goes through `../aigd/references/ui-dsl-spec.md` and `scripts/`, likewise). **Single source of truth, don't copy individually**; if you later want to distribute it independently, upgrade it to a plugin (see `references/README.md` "Packaging & portability").

## Project environment recommendations
- Spine files (`project charter` / `manifest`) and design artifacts are recommended to be put under **Git/SVN** management; the orchestrator should glance at the version status before each operation.
- **CHANGELOG (change ledger) complements version control**: VCS records "what changed", CHANGELOG records "why + which model" (this methodology is an AI-assisted flow, recording the model helps trace where a given change came from).

## Boundary
- Goes as far as "**a handoff package an AI can develop directly from**" (platform-agnostic: rules / contract / config / acceptance / prototype / resource needs).
- Tech-stack choice and client/server implementation = **downstream**, not in this package.
