# Project Charter (Spine Template) — Concept Layer (changes infrequently)

> Strongly-typed fields. Filled in by `aigd-concept` when starting the project; if discussion goes deeper you can come back and revise, and log it in CHANGELOG (the change ledger) when you do.
> **This holds the "project instance"; the methodology (references) stays generic** — when a sub-skill needs project-specific information it reads it from here, instead of hardcoding it into the methodology.

## One-line Concept
`<What this game is, in one sentence>`

## Core Loop
`<The core action loop the player repeats, 3–5 steps>`

## Design Pillars (≤3, after cutting the weak directions)
> If the concept hasn't converged yet (early-stage / migration project), the pillars may not exist yet — **leave a `[TBD]` inference, don't hardcode it as settled**.
- `<Pillar 1>` / `<Pillar 2>` / `<Pillar 3>`

## Target Users / Platform
- Target users: `<persona>`
- Platform: `<Mobile / PC / Console…>`; **server-authoritative?** `<yes/no>` (determines the shape of contracts/saves)
- Art style / brand: `<…>` (the visual source of truth for UI prototypes)

## Monetization
`<Core monetization model, placeholder is fine>`

## Non-functional Constraints (the technical boundaries given to the implementing AI — they affect tech-stack choices, fill them early and reap the benefits early)
- Frame-rate target: `<30 / 60 / …>` (determines the per-frame budget in ms)
- Network model: `<client-authoritative / server-authoritative>` (consistent with "Target Users/Platform · server-authoritative")
- Expected concurrent online: `<…>`
- Save-file size cap: `<…>`
- Latency cap for key operations: `<…ms>`
> Mark anything uncertain as `[TBD]`, so the downstream AI at least knows this is a question to ask.

## Project-Specific Conventions (← sub-skills read from here, keeping the methodology portable)
- Naming convention: `<area-sub-system / file naming…>`
- Units: `<per-ten-thousand /10000, etc.>`
- **Quality system**: `<which quality/rarity dimensions this project has, and the domain of each, e.g. item rarity 1-N / equipment quality / character quality, one set each>`
- Module-code style: `<R-XXX>`
- **Directory layout** (single switch, pick one of two; once chosen, the manifest cross-layer index and the system/handoff path examples **all follow this value**):
  - **Engineered**: `docs/systems/<system>/` + `proto/` + `config/source/` kept separate (root = `<…>`).
  - **Flat**: `<area>/<system-dir>/<system-dir>-0X<type>` (the six-piece set in one directory) + `specs/`·`config/` centralized.
- **Layout-switch naming map** (what the same piece is called under each of the two layouts):

  | Piece | Flat | Engineered |
  |----|------|--------|
  | Rules | `<system>-01rules.md` | `docs/systems/<system>/rules.md` |
  | Config spec | `<system>-02config-spec.md` | `config/source/<system>-config-spec.md` |
  | Prototype | `<system>-03prototype.html` | `docs/prototypes/<system>.html` |
  | Contract | `<system>-04contract.proto` | `proto/<system>.proto` |
  | Acceptance | `<system>-05acceptance.md` | `docs/systems/<system>/<system>-05acceptance.md` (**keep -05**) |

- ⚠️ **Migrating an existing flat project = MOVE, not COPY**: copying causes flat↔docs dual-source-of-truth drift; move once, and retire the flat paths after migrating. See `methodology.md` step 2.

## To Confirm
- [ ] `<Pending items involving specific values / conventions, awaiting the user's call>`
