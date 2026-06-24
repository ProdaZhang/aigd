# Potion-Crafting System — Config Spec (field schema for potion.xlsx)

> Toy example. Field annotations for the 4 tables in `potion.xlsx`. Self-describing header: row1=table English name, row2=type, row3=field key (arrays as `field[…]`), row4=Chinese, row5+ data.
> The Ref column written as `table.field` (in backticks) = a foreign key; `config_check`/`value_check` machine-check against it; external tables are marked "(external)" and not machine-checked. Per-ten-thousand is uniformly `/10000`.

---

## Config-table Overview

| Table | Primary key | Purpose |
|------|------|------|
| `potion` | id | Potion static config |
| `potionRarity` | id | Rarity → stack cap |
| `potionLv` | id | Level → heal bonus (cumulative) |
| `recipe` | id | Recipe: output + materials |

---

## 1. `potion` Potion List (primary key id)

| Field | Type | Values/Enum | Range/Default | Ref | Description |
|------|------|----------|----------|------|------|
| id | int | — | 1xx | — | Potion id |
| name | int | — | — | Text table (external) | Name text id |
| rarity | int | — | 1~3 | `potionRarity.id` | Rarity |
| heal | int | — | — | — | Base heal amount |
| craftCost | int | — | — | Item table (external) | Item id consumed by crafting |

## 2. `potionRarity` Potion Rarity (primary key id)

| Field | Type | Values/Enum | Range/Default | Ref | Description |
|------|------|----------|----------|------|------|
| id | int | — | 1~3 | — | Rarity id |
| name | int | — | — | Text table (external) | Rarity-name text id |
| maxStack | int | — | — | — | Stack cap |

## 3. `potionLv` Potion Level (primary key id)

| Field | Type | Values/Enum | Range/Default | Ref | Description |
|------|------|----------|----------|------|------|
| id | int | — | 1~5 | — | Level |
| heal | int | cumulative | — | — | Total heal bonus (monotonically non-decreasing with level) |

## 4. `recipe` Recipe (primary key id)

| Field | Type | Values/Enum | Range/Default | Ref | Description |
|------|------|----------|----------|------|------|
| id | int | — | — | — | Recipe id |
| output | int | — | — | `potion.id` | Output potion id |
| material[ … ] | int[] | — | up to 3 | `potion.id` | Material potion id list (checked per member) |

---

## Check Checklist (machine-checked, see the example README)

- [ ] schema alignment: `config_check.py config-spec.md potion.xlsx` → 0 major.
- [ ] foreign keys: `potion.rarity→potionRarity.id`, `recipe.output→potion.id`, `recipe.material[]→potion.id` with no broken links.
- [ ] levels: `potionLv.id` covers 1~5 contiguously; `potionLv.heal` is monotonically non-decreasing with level (see `potion.checks.json`).
- [ ] `craftCost`/`name` reference external tables → machine-check skipped (info); guaranteed at deploy time by the item/text systems.
