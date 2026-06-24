# manifest (Spine Template) — A System Inventory + Dependency Graph / B Range Registry / C Cross-layer Index / D Freeze Ledger + Recheck / E Rollback Records / F Shared-source-of-truth Compatibility Ledger

> **Strongly typed**: each table's columns are fixed, the AI reads/writes by column, **don't change the column structure**; `<>` is a blank to fill, `enum:` marks the legal values.
> One file acts as **6 tables (A–F) + the status enum**. Every sub-skill's "read the spine → do the work → write back" operates on it.

## Status Enum (unified across all tables)
`Draft` → `Playtesting` → `Final` → `Recheck` (marked by reverse lookup after a shared item changes) → back to `Final` after the recheck.
> `Final*` = an **annotated variant** of Final (the six-piece set is complete but there are `[TBD]` items on the books, see table D "Final-with-backlog"), **not a separate status**; treat it as `Final`, and drop the `*` once the backlog is cleared.

## A. System Inventory + Dependency Graph
| SystemID | Name | area-sub-system dir | Status | R-ModuleCode | Deps (upstream) | Depended-on-by (downstream) |
|--------|--------|----------------|------|----------|-----------|-------------|
| S01 | `<Combat>` | `<03gameplay-…>` | Draft | R-CMBT | S03,S04 | S07 |

> The dependency graph = the edge set of this table's "Deps / Depended-on-by" columns. **Cycle detection**: A↔B mutually depend → **register the common type at the project layer (global spec) first** to break the cycle, then make it concrete as `proto/common` at handoff time.
> **External / to-be-designed dependencies**: when the dependency target isn't a system yet (no SystemID), mark it `<name>[external]` or `[TBD-design]` in the "Deps (upstream)" column, **don't mix it with system edges**; connect the real edge once it's chartered.
> **Foundational referenced systems** (e.g. "item table" is referenced by almost every system): if "Depended-on-by" can't fit and you shouldn't force-enumerate it, mark it `broadcast (see table F)` — this kind of downstream propagation doesn't go through per-system recheck.

## B. Range Allocation Registry (collision-prevention · single source of truth at the project layer)
| ModuleCode | System | Protocol Range | Error-code Range | Notes |
|--------|------|----------|----------|------|
| R-CMBT | Combat | 1000–1099 | 5000–5099 | filled in when claiming a range; `example` = pending alignment with the lead programmer |

## C. Cross-layer Index (one block per system — all artifacts scattered across layers + shared relationships)

> One `### <SystemID> <Name>` sub-block per system, with fields as sub-headings, laid out **vertically**. The strongly-typed field names don't change; **a wide table is unreadable on real data, hence the block layout**.
> **Config tables belong to the project-layer global pool (no system-private tables)**: the "Config tables" column = the global tables this system primarily uses/maintains (referenced by name, location-independent), **not private**; other systems can reference them too.
> **Maintainer** = the system that declares this table in the "Reverse-provides" column (it gatekeeps schema changes to it); a pure global source with no single maintainer (e.g. `base`/`property`) is marked `global-maintained`, and changes go through global-spec review.

### S01 `<Name>`
- **Rules (-01)**: `docs/systems/<…>/rules.md` (carries R-codes)
- **Config tables**: `config/source/<…>.xlsx` + config spec
- **Referenced shared sources of truth**: enums[…] / LocalizationText / base.xlsx …
- **Contract (proto)**: `proto/<…>.proto` (imports `common`; occupies a range)
- **Acceptance**: `<…>-05acceptance.md` (+ planner-facing checklist)
- **Asset needs**: `<…> asset needs` (icons / VFX…)
- **Prototype**: `prototypes/<…>.html`
- **Reverse-provides**: the shared things this system gives to the project layer (e.g. "the item-table source of truth"); **if it's a broadcast-type shared source of truth → register the compatibility strategy in table F** (don't only write it here, see F2)

## D. Freeze Ledger + Recheck
| System | Status | Final time | Occupied ranges | Recheck trigger (which shared items it references) |
|------|------|----------|----------|------------------------------|
| S01 | Draft | — | — | LocalizationText structure / a certain enum / a certain shared-table field |

> **Final-with-backlog**: the six-piece set is complete but there's still a `[TBD]` tail (the normal state of a real system) → record the status as `Final*`, and note the backlog item next to the "Recheck trigger" column (e.g. "feature field pending alignment"). Don't create a separate status for TBDs; `Final*` is still treated as Final, can still be implemented downstream, and drops the `*` once the backlog is cleared.
> **`Recheck` exit**: recheck passes → status returns to `Final`, and `Final time` is refreshed to this recheck's confirmation time (this column = "most recent finalization/recheck"); fails → bounced back (recorded in table E). The executor = `aigd-sync` (it's the one that marks Recheck, and also the one that clears it).

## E. Rollback Records (both bounce-backs and re-splits get a line — supports the non-linear flow)
| Time | System | From status → To status | Reason | Affected downstream (already marked Recheck) |
|------|------|-----------------|------|--------------------------|
| `<…>` | S01 | Final → Playtesting | handoff exposed a design flaw | S07 (Final → Recheck) |

> **Bounce-back rule**: when any system's status rolls back, **reverse-look up table A's "Depended-on-by (downstream)"** ("Depended-on-by" lives only in table A), mark all the finalized systems that depend on it as `Recheck`, and record them in this table.
> ⚠️ The bounce-back rule only applies to **point-to-point system edges**; changes to a **broadcast-type shared source of truth** (an id namespace / text structure / enum referenced by most systems) **don't go through this rule** — they go through table F (otherwise it explodes into a full-table recheck).

## F. Shared-source-of-truth Compatibility Ledger (broadcast-type sources of truth — replaces "marking recheck per system")

> **Why a separate table**: broadcast-type shared sources of truth like the `item.id` namespace / `LocalizationText` structure / enums, which are referenced by "almost all systems", have a fan-out = the whole project;
> applying "change → reverse-look-up depended-on-by → mark downstream for recheck" to them explodes into a **full-table recheck**. Instead, use a **compatibility strategy**: backward-compatible changes need no recheck, only breaking changes trigger one, and the scope = that source's referrers (not the whole table).
>
> **Criteria for using table F** (meets ≥1 → broadcast strategy; meets none → go through table A's "Depended-on-by" per-system recheck):
> ① Referenced by **≥5 systems**;
> ② It's an **id namespace / enum dictionary / LocalizationText structure** (regardless of referrer count);
> ③ The referrers **don't form a table-A "Deps" edge** (they only consume its data, not its output logic).

| Shared source of truth | Type | Compatibility strategy (no recheck) | Breaking change (triggers recheck) |
|----------|------|------------------|---------------------|
| `<some id namespace>` | broadcast | add-only, never reuse old ids | delete / change semantics → global announcement + per-referrer confirmation |
| `<LocalizationText structure>` | broadcast | add fields without deleting, don't reuse ids | change the structure → all referrers recheck |
| `<some enum>` | broadcast | **append values only**, no deleting / no changing meaning | delete a value / change meaning → reverse-look-up that enum's referrers for recheck |

> **Decision**: backward-compatible (pure append) → **no recheck needed**; **breaking change** → reverse-look-up **table C's "Referenced shared sources of truth"** to find the systems that listed it → mark them `Recheck` in table D (scope limited to referrers, not the whole table). Point-to-point system edges instead go through table A's "Depended-on-by (downstream)" reverse lookup.

---

## Self-check Command (run after writing the spine, don't just eyeball it)

```
python references/scripts/manifest_check.py manifest.md
```

A non-zero exit code = there's a **major** (unregistered module code / a dependency pointing to a nonexistent system / illegal status / a system missing its C block) → **fix self-consistency first before operating**. Advisories (dependency cycle, finalized but missing proto/acceptance, a dangling range, a leftover C block) and infos (dependency edges connected by name) need human judgment. See `references/scripts/README.md` for the check items and their severities.
> This check only covers **the spine's internal self-consistency**; config ↔ doc drift goes through `config_check`, and data integrity goes through `value_check`.
