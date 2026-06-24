# 药水合成系统 — 配置说明（potion.xlsx 字段 schema）

> 玩具样例。`potion.xlsx` 4 张表的字段注解。自描述表头:行1=表英文名 行2=类型 行3=字段key(数组 `field[…]`) 行4=中文,行5+数据。
> 引用列写 `表.字段`(反引号)= 外键,`config_check`/`value_check` 据此机检;外部表标"(外部)"不机检。万分比统一 `/10000`。

---

## 配置表总览

| 表名 | 主键 | 用途 |
|------|------|------|
| `potion` | id | 药水静态配置 |
| `potionRarity` | id | 品质 → 叠加上限 |
| `potionLv` | id | 等级 → 回血加成(累计) |
| `recipe` | id | 配方:产出 + 材料 |

---

## 1. `potion` 药水列表（主键 id）

| 字段 | 类型 | 取值/枚举 | 范围/默认 | 引用 | 说明 |
|------|------|----------|----------|------|------|
| id | int | — | 1xx | — | 药水 id |
| name | int | — | — | 文本表(外部) | 名称文本 id |
| rarity | int | — | 1~3 | `potionRarity.id` | 品质 |
| heal | int | — | — | — | 基础回血量 |
| craftCost | int | — | — | 道具表(外部) | 合成消耗道具 id |

## 2. `potionRarity` 药水品质（主键 id）

| 字段 | 类型 | 取值/枚举 | 范围/默认 | 引用 | 说明 |
|------|------|----------|----------|------|------|
| id | int | — | 1~3 | — | 品质 id |
| name | int | — | — | 文本表(外部) | 品质名文本 id |
| maxStack | int | — | — | — | 叠加上限 |

## 3. `potionLv` 药水等级（主键 id）

| 字段 | 类型 | 取值/枚举 | 范围/默认 | 引用 | 说明 |
|------|------|----------|----------|------|------|
| id | int | — | 1~5 | — | 等级 |
| heal | int | 累计值 | — | — | 回血加成总值(随等级单调不减) |

## 4. `recipe` 配方（主键 id）

| 字段 | 类型 | 取值/枚举 | 范围/默认 | 引用 | 说明 |
|------|------|----------|----------|------|------|
| id | int | — | — | — | 配方 id |
| output | int | — | — | `potion.id` | 产出药水 id |
| material[ … ] | int[] | — | 最多 3 | `potion.id` | 材料药水 id 列表(逐成员校验) |

---

## 校验清单（机检,见样例 README）

- [ ] schema 对齐:`config_check.py config-spec.md potion.xlsx` → 0 major。
- [ ] 外键:`potion.rarity→potionRarity.id`、`recipe.output→potion.id`、`recipe.material[]→potion.id` 无断链。
- [ ] 等级:`potionLv.id` 连续覆盖 1~5;`potionLv.heal` 随等级单调不减(见 `potion.checks.json`)。
- [ ] `craftCost`/`name` 引外部表 → 机检跳过(info),投放时由道具/文本系统保证。
