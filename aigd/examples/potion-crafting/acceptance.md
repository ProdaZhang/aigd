# 药水合成系统 — 验收用例（Gherkin，玩具样例）

> 每条挂 `R-POT-*`;断言用 `表[主键].字段` 引配置真值,`value_check` 会逐条解析(行缺=悬空,字段空≠悬空)。

## 合成

```gherkin
场景: 材料齐则合成成功 (R-POT-CRAFT-01)
  假设 背包含药水 recipe[1].material[] 的全部材料各 1 个
  当 按配方 recipe[1] 合成
  那么 扣除材料、产出 recipe[1].output 药水 ×1

场景: 材料不足则拒绝 (R-POT-CRAFT-01)
  假设 背包缺 recipe[2].material[] 中至少一种
  当 按配方 recipe[2] 合成
  那么 返回 ERR_MATERIAL_LACK 且背包不变
```

## 使用

```gherkin
场景: 回血 = 基础 + 等级累计 (R-POT-USE-01)
  假设 玩家等级对应 potionLv[3]
  当 使用药水 potion[103]
  那么 回血量 = potion[103].heal + potionLv[3].heal

场景: 等级加成取累计值不逐级累加 (R-POT-USE-02)
  当 玩家处于等级 5
  那么 等级回血加成 = potionLv[5].heal（直接取该行,非 1..5 求和）
```

## 叠加

```gherkin
场景: 叠加按品质封顶 (R-POT-STACK-01)
  当 背包叠放药水 potion[104]
  那么 叠加上限 = potionRarity[potion[104].rarity 即 3].maxStack
```
