# Numeric-trap collection · common numeric traps (design-review checklist)

> **Purpose**: go through item by item during a `aigd-system`/`aigd-iterate` numeric/rule review; also a reminder for `aigd-concept` to propose conventions.
> **How to use**: for the system being designed, self-check each item "did I dodge this trap"; items that can be machine-checked are tagged with the corresponding tool (`value_check`/`config_check`/`manifest_check`), don't rely only on the naked eye.
> Items tagged ⚠️ are traps actually exposed in real projects (given in neutralized illustrative form), not textbook examples.

---

## 1. Exponential-growth runaway
**Symptom**: late-game numbers overflow (power/resources break int, the UI display is crushed, balance becomes meaningless).
**Root cause**: growth uses multiplicative compounding (`×1.1^n`) with no cap.
**How to prevent**: prefer **piecewise-linear / logarithmic convergence** for growth curves; always set a hard cap (level/star cap); use `value_check`'s `coverage` rule to confirm tiers have a definite endpoint, no open-ended infinite tiers.

## 2. Divide-by-0 / empty table / negative-damage-heal (defensive boundaries)
**Symptom**: `#DIV/0`, empty config crashes the tier, subtraction underflow turns into "negative damage = healing."
**Root cause**: the formula has no guardrail — the denominator may be 0, the config may be missing a row, `atk−def` may be negative.
**How to prevent**: check the denominator before dividing; a lower bound like `max(1, atk−def)` for damage; read config rows with a "row exists" check (`config_index.row_exists` distinguishes **missing row** from **empty field** — avoiding the false report of an empty optional cell as a missing row). An empty table / missing row must have a definite fallback, can't silently take a default.

## 3. Multiplicative-stacking explosion (additive domain vs multiplicative domain)
**Symptom**: a few buffs look mild individually but explode when stacked (or multiply into astronomical numbers).
**Root cause**: same-class bonuses that should add are written as a multiplicative product (or vice versa), with no distinction of "bonus domain."
**How to prevent**: be clear whether each class of bonus goes into the **additive pool** or the **multiplicative pool** (e.g. `finalDamage = base × (1 + Σadditive%) × Π(1 + multiplicative%)`); within a pool only Σ; write it into the rule formula, don't leave it for the implementation to guess.

## 4. Cumulative value vs incremental value confusion ⚠️
**Symptom**: growth is double-counted (summed tier by tier and also taking the cumulative column) or under-added.
**Root cause**: whether the config table stores "cumulative total up to this tier" or "this tier's increment" is neither uniform across the whole table nor written down.
**How to prevent**: **pick one, uniform across the whole table, write it into the config-spec**. E.g. a progression system's stats `*Percentage`/skill points store the **cumulative total**, settlement directly takes the current-tier row (not tier-by-tier summing), a single grant = this tier − previous tier diff. The cumulative column must be **monotonically non-decreasing** → machine-checked by `value_check`'s `monotonic` rule.

## 5. Sentinel value collides with default value / legal value ⚠️
**Symptom**: `0`/empty means both "no reference" and happens to be a legal datum or encoding result → misjudgment.
**Root cause**: using `0` as the "none" sentinel, but some field's legal domain contains 0, or some encoding computes 0.
**Real case (neutralized)**:
- **Grid-inventory position encoding**: a 3×N grid encodes cell positions with `(columnX<<16)|rowY`; the top-left cell `(0,0)→0` collides with the "in inventory / not worn" sentinel `0`, making the top-left cell unwearable. Fix: `+1` each in the encoding (`((X+1)<<16)|(Y+1)`), reserving `0` for the inventory.
- **Evolution/reference field = 0**: some "next form id" field `0` = final stage, no reference, but the foreign-key check treats 0 as an id to query → false `FK_BREAK`. Fix: `value_check` lists `{0, 0.0}` as foreign-key empty sentinels to skip (precondition: **the id domain is always positive, doesn't contain 0**).
**How to prevent**: before using `0`/empty as a sentinel, **confirm that field's legal domain doesn't contain 0 and no encoding path computes 0**; for encoding types use a `+1` offset to make room for the sentinel; write "`0` = no reference" into the field spec so the validator knows to skip.

## 6. Inconsistent unit/scaling (per-myriad trap)
**Symptom**: numbers off by 10000×, or a percentage used as an absolute value.
**Root cause**: the same concept mixes per-myriad (`/10000`), percentage, and absolute value.
**How to prevent**: a unified project scaling convention (e.g. **per-myriad uniformly `/10000`**), field type/spec clearly marking the unit; `config_check`'s `DOMAIN` can catch a declared domain (e.g. `0~10000`) mismatching the actual data.

## 7. The psychology and imbalance of first-pay / paywall thresholds
**Symptom**: first-pay/tier design makes the player feel "just a tiny bit short of the next tier" to induce over-spending, or pricing misalignment crashes ARPU.
**Root cause**: the pay point isn't aligned with the growth curve, the threshold is pulled out of thin air.
**How to prevent**: align the pay tier with the progression gradient (don't let the free wall land right before a pay tier in a way that looks like extortion); mark the pricing convention `[to-confirm]` for the planner/monetization to decide, **the AI does not decide numbers on their behalf**.

## 8. Pity / variance experience (pseudo-random)
**Symptom**: under true randomness, an unlucky player gets a long dry streak, the experience collapses; or the pity is too loose and loses the sense of scarcity.
**Root cause**: using pure uniform randomness, with no pity / soft pity.
**How to prevent**: gacha sets a **hard pity** (guaranteed within N pulls) + optional **soft pity** (increasing probability); drops use a pseudo-random distribution (PRD) to suppress variance; the pity-counter's save slot must go into the contract.

## 9. Ceiling and capping (fill-out data)
**Symptom**: the config is fully laid out but some rows shouldn't be used at runtime, yet the implementation uses them → out-of-bounds growth.
**Root cause**: the numeric table laid out template rows beyond the cap for tidiness, with no mechanism to truncate.
**How to prevent**: concentrate the capping logic **in one place** (e.g. "cap by quality": truncate by the quality table's "evolvable count," the excess evolution template rows are fill-out data, unused); "chain length > cap" is **expected**, the validation rule uses `severity: advisory`, don't report major (see `checks/example.checks.json` cardinality).

## 10. Cross-system numeric coupling (change one place, drift globally)
**Symptom**: changing one shared value (quality coefficient / attribute id / text structure) silently misaligns several systems.
**Root cause**: a broadcast-type shared canonical source (item-id namespace, enum, some global quality/coefficient table, etc.) is referenced by multiple systems, and the change didn't follow a compatibility strategy.
**How to prevent**: a broadcast-type source is **append-only, never break** (enums only add values, tables only add fields, ids aren't reused); only a breaking change reverse-looks-up the referencers for recheck — registered in the `manifest` F table, with `manifest_check` guarding spine self-consistency. config↔doc desync is machine-checked with `config_check`+`value_check` (don't just tick a box self-assessed — this is the number-one root cause of forked downstream reads of the handoff package).

---

## Quick reference: trap ↔ machine-check tool

| Trap | Machine-checkable? | Tool/rule |
|----|---------|----------|
| §4 cumulative monotonic | ✅ | `value_check` `monotonic` |
| §1/§9 tier coverage/endpoint | ✅ | `value_check` `coverage` |
| §6 declared-domain mismatch | ✅ | `config_check` `DOMAIN` |
| §5/§10 broken foreign key | ✅ | `value_check` `FK_BREAK` (incl. empty-sentinel skip) |
| §9 chain length vs cap | ✅ (advisory) | `value_check` `cardinality` |
| §10 spine/shared-source self-consistency | ✅ | `manifest_check` + F table |
| §2 missing row vs empty field | ✅ | `config_index.row_exists` |
| §3/§7/§8 design conventions | ❌ human judgment | rule review + `[to-confirm]` to the planner |
