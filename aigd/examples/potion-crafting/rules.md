# 药水合成系统 — 功能规则（玩具样例）

> 散文无裸数值:只写公式 + `表[主键].字段` 引用,数值住 `potion.xlsx`。每条程序判断挂 `R-POT-*`。
> 范围:药水的合成、使用回血、叠加上限。消耗道具/文本走外部系统。

---

## 一、合成 — R-POT-CRAFT

- **R-POT-CRAFT-01**(按配方合成):选定配方 `recipe[rid]` → 校验背包含其 `recipe[rid].material[]` 全部材料药水各 1 个 → 扣除材料、产出 `recipe[rid].output` 药水 ×1。材料不足则拒绝(`ERR_MATERIAL_LACK`)。
- **R-POT-CRAFT-02**(消耗道具):合成额外消耗 `potion[output].craftCost` 指定的道具(数量由道具系统[外部]结算);不足则拒绝。

## 二、使用 — R-POT-USE

- **R-POT-USE-01**(回血):使用药水 `potion[pid]` → 回血量 = `potion[pid].heal + potionLv[当前等级].heal`(基础值 + 等级加成累计值);超过最大生命按最大生命封顶。
- **R-POT-USE-02**(等级加成口径):`potionLv[lv].heal` 为**截至该等级的累计总值**,直接取当前等级行,不逐级累加。

## 三、叠加 — R-POT-STACK

- **R-POT-STACK-01**(叠加上限):同一 `potion[pid]` 在背包按 `potionRarity[potion[pid].rarity].maxStack` 封顶叠加;超出溢出处理由背包系统[外部]决定。

---

## 错误码

| 码 | 含义 |
|----|------|
| `ERR_MATERIAL_LACK` | 合成材料不足 |
| `ERR_ITEM_LACK` | 合成消耗道具不足 |

## 外部依赖

- **道具系统**[外部]:`potion.craftCost` 指向的消耗道具、合成产出入包。
- **文本系统**[外部]:`potion.name` / `potionRarity.name` 文本 id。
- **背包系统**[外部]:叠加溢出、容量。
