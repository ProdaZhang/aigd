# Implementation Overview (Spine Template) — Handoff-package Entry Point (the "start here" for the downstream development AI)

> After the downstream AI / engineering team clones this repo, **read this first**. This package produces **platform-agnostic** "rules + contracts + config + acceptance"; picking a tech stack to implement them is the downstream's job.

## What Game Is This
`<one line>` — see `project-charter.md` for details.

## Build Order (dependency-driven)
> Gives the recommended implementation order per the manifest dependency graph; common types / shared tables first.
1. `<S0x …>`
2. `…`

## Where Each System Lives (points to the manifest cross-layer index)
- System inventory + status + cross-layer index: **`manifest.md`** (read it first)
- Rules (behavior, carrying R-codes): `docs/systems/<…>/rules.md`
- Contracts: `proto/` (common + each system; unified ranges)
- Config: `config/source/` (tables + config spec; includes LocalizationText)
- Acceptance (definition of done): `<…>-05acceptance.md` (Gherkin) + planner-facing checklist

## How to Tell "It's Implemented Correctly"
- Use the **acceptance cases** as the definition of done (assertions use proto fields + `table[primary-key].field`).
- Cross-system: `specs/global-integration-acceptance.md` (adventure / minimal playable loop).

## Global Sources of Truth
- Enum dictionary / code registry / unit conventions / visual spec: `specs/`
- Config shared sources of truth: `config/source/` (item / base / property / LocalizationText…)

## Edge-case Handling Principles (default fallbacks when the design doesn't cover something)
1. Two systems' rules conflict → defer to the rules of the **upstream system on the dependency graph** (upstream constrains downstream).
2. Numeric boundaries (0 / negative / extreme values) → default to **clamp**, and add a warn log in the code.
3. A player action the design doesn't cover → **reject + log**, do not silently allow.
4. Discover a **reasonable** action the design doesn't cover → feed it back to the design side, mark it `[TBD]` (don't kill it off on the spot).

## Status and Boundaries
- System statuses are in the manifest (Draft / Playtesting / Final / Recheck); **only implement finalized systems**, draft systems may still change, and `Recheck` systems need confirmation first.
- Boundary: this package stops at the "handoff artifacts"; client / server code is implemented by the downstream per the chosen tech stack.
