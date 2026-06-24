---
name: aigd-iterate
description: AIGD Phase 3 · playtest iteration. Use this when, after the user playtests the prototype, they want to optimize the rules or change the config table (can be run repeatedly). Only touches the "cheap" artifacts — rules / config / prototype — not the contract / acceptance (those are produced after finalization). Part of the aigd package; methodology in ../aigd/references/.
---

# AIGD · iterate (playtest iteration)　[minimal skeleton]

> **Package contract**: install the whole `aigd` package (the orchestrator `aigd/`+`references/` and the 6 sub-skills (including aigd-ui-capture) placed at the same level in this environment's skills directory, following the host agent, e.g. Claude Code's `.claude/skills/`), **don't copy this skill alone** — this package's sub-skills rely on `aigd/` at the same level to fetch the methodology, copying it alone breaks the link.

## Positioning
Phase 3. Loops between system (2) ↔ iterate (3), **repeatable**. The design is still fluid, so **only change rules / config (test data) / prototype** — the proto/acceptance haven't even been produced yet, and **zero churn** is exactly the essence of how this step saves cost.

## Read / produce / write back
- **Read**: this system in the `manifest`, the user's **playtest feedback**.
- **Produce / change**: rules.md / config table (test data) / system prototype.html.
- **Write back**: this system's status in the `manifest` → `Playtesting` (currently playtesting; a system bounced back from handoff also **stays `Playtesting`**, don't overwrite it back to Draft); record this round's iteration points (what changed, why).

## Recipe
1. Collect playtest feedback → locate whether it's a **rule problem** or a **value problem**.
2. Change the corresponding artifact (rules → change -01, numbers → change config test data, presentation → change prototype).
3. Re-emit the prototype → playtest again → loop, until the user is satisfied → move to `aigd-handoff` to finalize.

## Playtest-feedback format (filled by the user or the AI after playtesting, fed to this skill — the locating decides which artifact to change)

| Dimension | Problem description | Locating (rule/value/presentation/other) | Repro steps |
|------|---------|---------------------------|---------|
| `<e.g. combat pacing>` | `<too long a wait after casting a skill>` | `<value>` | `<enter combat → tap skill → watch cooldown>` |

- Locating = **rule** → change `-01 rules.md` (changing logic / judgment)
- Locating = **value** → change config table test data (changing feel parameters)
- Locating = **presentation** → change `-03 prototype.html` (changing feedback / animation / layout)
> A bare "not fun" can't be acted on — first break it down by this table into dimension + locating, then start changing.

## Admission / exit
- **Admission**: the prototype is clickable, the user already has playtest feedback.
- **Exit**: the changed rules/config/prototype + manifest iteration record; **user satisfied** → move to `aigd-handoff` to finalize; **found the system boundary was drawn wrong** → back to `aigd-concept` to re-split.

## Boundary
Doesn't produce contract / acceptance / client-server docs; doesn't touch already-finalized systems (those must be bounced first).
