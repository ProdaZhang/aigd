# Potion-Crafting System — Functional Rules (toy example)

> Prose has no bare numbers: only formulas + `<table>[<key>].<field>` references; the numbers live in `potion.xlsx`. Every procedural decision carries an `R-POT-*`.
> Scope: potion crafting, healing on use, and the stack cap. Consumed items / text go through external systems.

---

## I. Crafting — R-POT-CRAFT

- **R-POT-CRAFT-01** (craft by recipe): select a recipe `recipe[rid]` → verify the inventory contains 1 of each of its `recipe[rid].material[]` material potions → consume the materials and produce `recipe[rid].output` potion ×1. If materials are insufficient, reject (`ERR_MATERIAL_LACK`).
- **R-POT-CRAFT-02** (consume items): crafting additionally consumes the item specified by `potion[output].craftCost` (the quantity is settled by the item system [external]); if insufficient, reject.

## II. Use — R-POT-USE

- **R-POT-USE-01** (healing): use potion `potion[pid]` → heal amount = `potion[pid].heal + potionLv[current level].heal` (base value + cumulative level bonus); capped at max HP if it exceeds max HP.
- **R-POT-USE-02** (level-bonus convention): `potionLv[lv].heal` is the **cumulative total up to that level**; read the current level's row directly, do not accumulate level by level.

## III. Stacking — R-POT-STACK

- **R-POT-STACK-01** (stack cap): the same `potion[pid]` stacks in the inventory capped by `potionRarity[potion[pid].rarity].maxStack`; overflow handling is decided by the inventory system [external].

---

## Error Codes

| Code | Meaning |
|----|------|
| `ERR_MATERIAL_LACK` | Insufficient crafting materials |
| `ERR_ITEM_LACK` | Insufficient items consumed by crafting |

## External Dependencies

- **Item system** [external]: the consumed item that `potion.craftCost` points to, and putting the crafted output into the inventory.
- **Text system** [external]: the `potion.name` / `potionRarity.name` text ids.
- **Inventory system** [external]: stack overflow, capacity.
