# Toy Example · Potion-Crafting System (potion-crafting)

A **self-contained, runnable** minimal AIGD output, used to demonstrate: what the **six-piece set** of a system design looks like, and how the **3 deterministic validators** gate it to "ready for handoff". Entirely fictional, containing no specific project.

## Files (the six-piece set + spine)

| File | What it is |
|------|--------|
| [rules.md](rules.md) | Functional rules, each carrying `R-POT-*`, prose with no bare numbers (only references `<table>[<key>].<field>`) |
| [potion.xlsx](potion.xlsx) | Config tables (4: `potion`/`potionRarity`/`potionLv`/`recipe`), self-describing 4-row header |
| [config-spec.md](config-spec.md) | potion.xlsx's field schema + foreign-key declarations |
| [potion.proto](potion.proto) | Interface contract (client = server, one and the same) |
| [acceptance.md](acceptance.md) | Gherkin, assertions reference config truth |
| [potion.checks.json](potion.checks.json) | Domain rules (level-table coverage + monotonic) |
| [manifest.md](manifest.md) | Spine (2 systems: potion + shop stub) |

## Run the Validators (in this directory)

```bash
S=../../references/scripts

# 1) schema drift: are the config spec ↔ xlsx columns/types/table names consistent
python $S/config_check.py config-spec.md potion.xlsx

# 2) data integrity: broken foreign-key links / dangling acceptance refs / coverage·monotonic rules
python $S/value_check.py config-spec.md . --acc acceptance.md --rules potion.checks.json

# 3) spine self-consistency: module-code registration / dependency targets / status / C blocks / dependency cycle
python $S/manifest_check.py manifest.md
```

**Expected (all three clean)**:

```text
1) ✓ No drift: columns / types / table names consistent, parseable domains in bounds.   (exit 0)
2) ✓ No issues: foreign keys with no broken links, acceptance refs resolvable, rule constraints pass.   (exit 0)
3) Found 1 (major=0 advisory=0 info=1):
   [info] DEP_BY_NAME …                                          (exit 0)
```

The foreign-key chains checked: `potion.rarity→potionRarity.id`, `recipe.output→potion.id`, `recipe.material[]→potion.id` (array, per member). External tables `craftCost→item table`, `name→text table` are marked "(external)" → machine-check skipped (info).

## Want to See the Validators Report an Error? Deliberately Break One Spot:

- Change a `material` in some `recipe` of `potion.xlsx` to a nonexistent potion id (e.g. `999`) → `value_check` reports **FK_BREAK(major)**.
- Change some row's `heal` in `potionLv` to be smaller than the previous row → `value_check` reports **RULE_MONOTONIC**.
- Delete `R-POT` from table B in `manifest.md` → `manifest_check` reports **SEG_MISSING(major)**.
- Delete the `potion.heal` row from the config spec → `config_check` reports **MISSING_COL**; conversely, if the xlsx has an extra column not recorded → **UNDOC_COL**.

This is AIGD's core loop: **design → machine-check gating → only 0 major counts as ready for handoff**, keeping drift like "doc settled first, config changed later without syncing" out before handoff.
