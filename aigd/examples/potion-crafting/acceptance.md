# Potion-Crafting System — Acceptance Cases (Gherkin, toy example)

> Each carries an `R-POT-*`; assertions reference config truth via `<table>[<key>].<field>`, which `value_check` parses one by one (missing row = dangling, empty field ≠ dangling).

## Crafting

```gherkin
Scenario: Materials complete → crafting succeeds (R-POT-CRAFT-01)
  Given the inventory contains 1 each of all materials in recipe[1].material[]
  When crafting by recipe recipe[1]
  Then consume the materials and produce recipe[1].output potion ×1

Scenario: Insufficient materials → reject (R-POT-CRAFT-01)
  Given the inventory is missing at least one of recipe[2].material[]
  When crafting by recipe recipe[2]
  Then return ERR_MATERIAL_LACK and the inventory is unchanged
```

## Use

```gherkin
Scenario: Heal = base + cumulative level bonus (R-POT-USE-01)
  Given the player's level corresponds to potionLv[3]
  When using potion potion[103]
  Then heal amount = potion[103].heal + potionLv[3].heal

Scenario: Level bonus takes the cumulative value, not level-by-level accumulation (R-POT-USE-02)
  When the player is at level 5
  Then the level heal bonus = potionLv[5].heal (read that row directly, not the sum of 1..5)
```

## Stacking

```gherkin
Scenario: Stacking is capped by rarity (R-POT-STACK-01)
  When stacking potion potion[104] in the inventory
  Then the stack cap = potionRarity[potion[104].rarity i.e. 3].maxStack
```
