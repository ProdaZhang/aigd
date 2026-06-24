---
name: aigd-sync
description: AIGD cross-cutting action · sync-back integration (a non-linear "last step", triggered after every system's handoff). Use this when, once a system is settled, you need to update the global spec, the overall html prototype (integration demo), the implementation master guide (handoff-package entry point), or mark downstream systems for recheck after a shared item changes. Maintains consistency between the spine and the handoff-package entry point. Part of the aigd package; methodology in ../aigd/references/.
---

# AIGD · sync (sync-back integration)　[minimal skeleton]

> **Package contract**: install the whole `aigd` package (the orchestrator `aigd/`+`references/` and the 6 sub-skills (including aigd-ui-capture) placed at the same level in this environment's skills directory, following the host agent, e.g. Claude Code's `.claude/skills/`), **don't copy this skill alone** — this package's sub-skills rely on `aigd/` at the same level to fetch the methodology, copying it alone breaks the link.

## Positioning
**Cross-cutting action (not a linear "step 5")**: triggered after every system's handoff, a continuous / milestone-style sync-back. Writes each single system's results back to the project layer, keeping the spine consistent with the whole; manages "downstream impact".

## Read / produce / write back
- **Read**: the `manifest` (full), each system's status, the `project charter`.
- **Produce / change**:
  - Global-spec consolidation (enums / number ranges / units deduplicated and aligned).
  - `spec/integration-acceptance.md` (**land** the results of the "integration check" below into cross-system acceptance; the `implementation master guide` points to it).
  - Overall prototype (integration demo) — a single html file, placed where the project charter"directory layout"specifies (engineering layout → `docs/prototypes/`).
  - `impl-overview.md` (handoff-package entry point: the start-here for downstream AI).
- **Write back**: ① shared item changed → per "recipe 4" reverse-look-up in two categories (point-to-point → table A "depended-on-by (downstream)" / broadcast-type → table C "referenced shared source of truth") → mark affected already-finalized systems `Recheck` (record in table D); ② **recheck passed** → that system `Recheck → Final`, refresh table D's finalization time (= this recheck's confirmation time) — this is the only exit from the `Recheck` state; not handling it leaves that state hanging forever.

## Recipe
1. After a system is finalized: absorb its enums / number ranges into the global spec.
2. Merge that system into the overall prototype (integration demo).
3. Refresh the implementation master guide (system list / build order / contract locations / acceptance entry).
4. Run downstream impact, **in two categories** (each reverse-looks-up a different column):
   - **Point-to-point system edge** (one system's output consumed by several others) changed → reverse-look-up **table A "depended-on-by (downstream)"**, mark those few downstream `Recheck` (record in table D).
   - **Broadcast-type shared source of truth** (enums / text structure / id namespace, see manifest table F) changed → **backward-compatible (pure append) needs no recheck**; **breaking change** → reverse-look-up **table C "referenced shared source of truth"** to find the systems that listed it (broadcast-type sources aren't in table A "depended-on-by") → mark those systems `Recheck` in table D, **don't blow up the whole table**.
5. **Recheck the `Recheck` systems**: verify whether their references to the "changed shared item" still hold → if they hold, status back to `Final`, refresh table D; if not, bounce (back to iterate/concept, and per the bounce rules cascade to its downstream again).

## Integration check (must run every time — meso-layer (inter-system combination) post-hoc gate; the up-front design of combination points is in concept)
- [ ] The enums system A produces — do the fields align when B consumes them?
- [ ] Do A's config primary keys exist in B's reference table?
- [ ] Is there a deadlock in the A↔B state machines (A waits for B, B waits for A)?
- [ ] Does the core loop (minimal playable closed loop) cover all systems?
Any one failing → flag the problem, go back to the relevant system (back to concept if needed), and write the result into `spec/integration-acceptance.md`.

## Admission / exit
- **Admission**: a system has changed to `Final`, or some shared item has changed, or there are `Recheck` systems pending verification.
- **Exit**: global spec consolidated + overall prototype updated + implementation master guide refreshed + affected systems marked `Recheck` + the `Recheck` systems selected for recheck settled (pass → `Final` / fail → bounce).

## Boundary
Only does project-layer sync-back and consistency maintenance, doesn't design new systems (that's concept/system).
