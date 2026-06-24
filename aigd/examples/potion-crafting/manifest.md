# manifest (spine) — Potion-Crafting Toy Example

> Minimal spine: trimmed so `manifest_check` passes. 2 systems (potion/shop), real data pointing at this example's files.

## Status Enum (unified across all tables)
`Draft` → `Playtesting` → `Final` → `Recheck`. `Final*` = Final with a `[TBD]` backlog.

## A. System Inventory + Dependency Graph
| SystemID | Name | area-sub-system dir | Status | R-ModuleCode | Deps (upstream) | Depended-on-by (downstream) |
|--------|--------|----------------|------|----------|-----------|-------------|
| S01 | Potion | examples/potion-crafting | Final* | R-POT | Item`[external]`·Text`[external]` | Shop |
| S02 | Shop | examples/shop | Draft | R-SHOP | Potion (sells potions) | (none) |

> Edges: Shop → Potion (sells). Potion only references external tables (item/text), forming no system dependency edge. No build cycle.

## B. Range Allocation Registry
| ModuleCode | System | Protocol Range | Error-code Range | Notes |
|--------|------|----------|----------|------|
| R-POT | Potion | 1700–1799 `example` | 17000– `example` | `PotionError` |
| R-SHOP | Shop | 1800–1899 `example` | 18000– `example` | stub |

## C. Cross-layer Index (one block per system)

### S01 Potion
- **Rules (-01)**: `rules.md` (R-POT-CRAFT/USE/STACK)
- **Config tables**: `potion.xlsx` (4 tables) + `config-spec.md`
- **Contract (proto)**: `potion.proto`
- **Acceptance**: `acceptance.md`
- **Domain rules**: `potion.checks.json` (coverage/monotonic)
- **Reverse-provides**: no exclusive shared source of truth

### S02 Shop  `(draft stub)`
- **Rules (-01)**: `(to be written)`
- **Referenced shared sources of truth**: potion `potion.id` (listing for sale)
- **The rest**: pending (stub)

## D. Freeze Ledger + Recheck
| System | Status | Final time | Occupied ranges | Recheck trigger |
|------|------|----------|----------|------------|
| S01 Potion | Final* | 2026-06-23 | 1700– / 17000– | backlog: none |
| S02 Shop | Draft | — | — | potion interface |

## E. Rollback Records
| Time | System | From status → To status | Reason | Affected downstream |
|------|------|-----------------|------|--------------|
| — | — | — | — | — |
