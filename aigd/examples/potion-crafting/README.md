# 玩具样例 · 药水合成系统（potion-crafting）

一个**自包含、可跑通**的最小 AIGD 产出,用来演示:一份系统设计的 **6 件套**长什么样,以及 **3 个确定性校验器**怎么把它门控到"可交接"。完全虚构、不含任何具体项目。

## 文件（6 件套 + 脊柱）

| 文件 | 是什么 |
|------|--------|
| [rules.md](rules.md) | 功能规则,每条挂 `R-POT-*`,散文无裸数值(只引 `表[主键].字段`) |
| [potion.xlsx](potion.xlsx) | 配置表(4 张:`potion`/`potionRarity`/`potionLv`/`recipe`),自描述 4 行表头 |
| [config-spec.md](config-spec.md) | potion.xlsx 的字段 schema + 外键声明 |
| [potion.proto](potion.proto) | 接口契约(客户端=服务端同一份) |
| [acceptance.md](acceptance.md) | Gherkin,断言引配置真值 |
| [potion.checks.json](potion.checks.json) | 领域规则(等级表 coverage + monotonic) |
| [manifest.md](manifest.md) | 脊柱(2 系统:药水 + 商店 stub) |

## 跑校验器（在本目录下）

```bash
S=../../references/scripts

# 1) schema 漂移:配置说明 ↔ xlsx 列/类型/表名是否一致
python $S/config_check.py config-spec.md potion.xlsx

# 2) 数据完整性:外键断链 / 验收悬空 / 覆盖·单调规则
python $S/value_check.py config-spec.md . --acc acceptance.md --rules potion.checks.json

# 3) 脊柱自洽:模块码登记 / 依赖指向 / 状态 / C 分块 / 依赖环
python $S/manifest_check.py manifest.md
```

**预期(三个都干净)**:

```text
1) ✓ 无漂移:列 / 类型 / 表名一致,可解析域无越界。              (exit 0)
2) ✓ 无问题:外键无断链、验收引用可解析、规则约束通过。          (exit 0)
3) 发现 1 条(major=0 advisory=0 info=1):
   [info] DEP_BY_NAME …                                          (exit 0)
```

校验的外键链:`potion.rarity→potionRarity.id`、`recipe.output→potion.id`、`recipe.material[]→potion.id`(数组逐成员)。外部表 `craftCost→道具表`、`name→文本表` 标"(外部)"→ 机检跳过(info)。

## 想看校验器报错?故意改坏一处:

- 把 `potion.xlsx` 的 `recipe` 某 `material` 改成一个不存在的药水 id(如 `999`)→ `value_check` 报 **FK_BREAK(major)**。
- 把 `potionLv` 某行 `heal` 改成比上一行小 → `value_check` 报 **RULE_MONOTONIC**。
- 把 `manifest.md` 里 `R-POT` 从 B 表删掉 → `manifest_check` 报 **SEG_MISSING(major)**。
- 配置说明删掉 `potion.heal` 那行 → `config_check` 报 **MISSING_COL**;反之 xlsx 多一列没记 → **UNDOC_COL**。

这就是 AIGD 的核心循环:**设计 → 机检门控 → 0 major 才算可交接**,把"文档先定、配置后改没同步"这类漂移挡在交接前。
