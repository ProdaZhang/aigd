# Gameplay paradigm · multi-axis battle-unit progression (collect-progress genre)

> **Purpose**: domain ammunition for when `aigd-concept`/`aigd-system` interviews a "battle-unit progression"-type system (pet/spirit/hero/general/upgradable equipment) — a battle-tested structural skeleton + design points + common mistakes.
> This page is an **abstract paradigm**; field/table names are **illustrative**; when it lands on a concrete project, go by that project's naming.
> Related: numeric-design risks in [`../numeric-traps/numeric-traps.md`](../numeric-traps/numeric-traps.md); loop position in [`core-loops.md`](core-loops.md)「collect → progress → validate」.

---

## I. Paradigm skeleton: one "battle unit progressable along multiple axes"

Battle-unit progression = **one static unit definition** + **N mutually orthogonal growth axes** + **one ability-ceiling master switch**.

```text
quality/rarity (rarity) ── master switch: determines level cap / evolution count / star cap ──┐
                                                                                              ▼
unit static table (unit) ─┬─ level axis    (lv:   materials×qty → stats%)
                          ├─ evolution axis (swap form id: stage → stats% + unlocks)
                          ├─ star axis      (star: materials×qty → stats% + skill points)
                          ├─ skill axis     (skill slot: conditional unlock + level cap)
                          ├─ formation axis (formation slot: conditional unlock)
                          └─ bond axis      (member group + tier conditions → attributes)
```

Each axis is **independently tabled, independently consumed, independently bonused**; at runtime each takes its current-tier row and sums into the total attributes. The axes couple only through the "quality ceiling" and "unlock conditions," not inlined into each other — this is the key to being able to iterate in parallel and balance individually.

---

## II. Five design decisions worth reusing

### 1. Collection unit ≠ form unit (evolution swaps id)
After evolving, the unit **swaps to a different id** (`unit.evolveTo` = the next form's id). So you need a **stable collection unit** spanning the whole journey: use a "line id" that never changes through the entire evolution (e.g. `unit.line`) to normalize the codex/bond.
- **Single canonical source**: the evolution chain takes `unit.evolveTo` as the sole canonical source; the "evolution-line member table" (ordered members `evolveLine.unit[]`) is only for **collection/codex normalization**, not the canonical source of the evolution logic. The same relationship stored in two places → you must designate which is authoritative, or dual-writing drifts.
- **Terminal sentinel**: `evolveTo = 0` means the final stage, can no longer evolve. **id is always positive**, so `0` can safely be the "no reference" sentinel (see trap page §5, but confirm the id domain doesn't contain 0).

### 2. Quality = the ability-ceiling master switch (hard cap)
`rarityCap[quality]` defines in one row that quality's `level cap / evolvable count / star cap`. **No matter what the other configs say, at runtime the quality always caps it** (quality cap takes priority).
- Paired with a **fill-out data strategy**: the evolution/star tables contain **template rows beyond that quality's cap** (for tidy table export), and at runtime are **always truncated by `rarityCap[r].evolution`**, with the excess rows unused.
- Benefit: numeric tables can be laid out neatly without cropping per quality; the capping logic is concentrated in one place.
- Risk: in validation, "chain length > quality count" is **expected**, not an error → the validation rule must use `severity: advisory` (see the cardinality rule in `checks/example.checks.json`).

### 3. Cumulative value vs incremental value (store the total, diff for the single step)
Stats bonuses `*Percentage` and things like skill points store the **cumulative total up to that tier**, not the per-tier increment.
- Settlement: directly take the current-tier row (e.g. `levelStep[currentLevel].HpPercentage`), **don't sum tier by tier** — to avoid the precision/performance issues of summing N tiers.
- A single grant = `this tier's total − the previous tier's total` (e.g. the skill points gained from one star-up = `starStep[star].skillPoint − starStep[star-1].skillPoint`).
- Invariant: the cumulative column is **monotonically non-decreasing with tier** (`value_check`'s `monotonic` rule guards this).

### 4. Multiple unit classes reuse one table
Use a flag bit (e.g. `unit.isEnemy`) to switch semantics: enemy units use **absolute** `hp/atk/def`; friendly units grow stats by percentage, with the absolute columns left empty. One schema carries both classes of battle unit, saving a table + sharing the battle loader.

### 5. Parameterized unlock conditions (condition + para)
Skill slots / formation slots express the unlock threshold with a `(condition, para)` pair: `condition` is an enum (0 no limit / 1 unit star / 2 team level / …), `para` is the threshold. Adding a new unlock dimension = adding an enum value, without touching the table structure.

---

## III. Key reference chains (foreign-key skeleton, portable)

```text
unit.rarity     → enum Rarity           (ability-ceiling key)
unit.element    → enum Element          (composite-key component, if templated by element)
unit.line       → evolveLine.id         (collection unit)
unit.evolveTo   → unit.id (or 0=final)  (evolution id-swap canonical source)
unit.skill[]    → skill-system table    (cross-system [external])
evolveStep/starStep (rarity, element) → composite key, matched by component via「composite-key-map.json」(composite-key map)
bond.member[]   → unit.line             (normalized by evolution line, not by form id)
*.cost          → item/material table.id (per-axis consumption)
*.property      → attribute table       (bond / battle attributes)
```

Composite primary keys (e.g. `starStep:[rarity,element,star]`) must register `composite-key-map.json` (composite-key map) in the config directory, so `value_check` can parse `table[primaryKey].field` references.

---

## IV. Design-interview checklist (ask item by item when applying this kind of system)

- [ ] What is the **collection unit**? Does evolution/class-change swap the id? If so, what threads through (codex/bond)?
- [ ] **Ceiling master switch**: who caps the ability (quality/rarity/class)? Is the cap concentrated in one place or scattered?
- [ ] **How many progression axes**? For each: what it consumes, what it produces, whether it's orthogonal to the others?
- [ ] Is the bonus a **cumulative value or an incremental value**? (Pick one, uniform across the whole table, write it into the config-spec.)
- [ ] **Fill-out data**: should the numeric tables lay out template rows beyond the cap? What truncates them at runtime?
- [ ] How many dimensions of **unlock conditions**? Can they be parameterized with `(condition,para)` to avoid changing the structure?
- [ ] Is the same table reused for **multiple unit classes** (enemy/friendly/summonable)? Switched by what field?
- [ ] Which cross-system dependencies (skill/tech/item/text) are `[external]`? Mark the dependency first, don't inline.

---

## V. This paradigm's position in the loop

Battle-unit progression is the "progress" middle segment of the「**collect → progress → validate**」core loop: collection (gacha/drops) feeds in new units and materials, progression (this paradigm) pushes the numeric axes up, validation (stages/PVP) consumes power and yields materials back. When designing, confirm that **the power gain produced by progression has a matching consumption gradient on the validation end**, or progression stalls (see [`core-loops.md`](core-loops.md)).
