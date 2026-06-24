---
name: aigd-handoff
description: AIGD 阶段4 · 定稿生成交接包。当某系统试玩定稿后,要生成接口契约、验收用例、(按需)美术/客户端/服务端文档、策划版验收清单时使用。产出"另一个 AI 能直接开发"的平台无关交接物。是 aigd 包的一员,方法论见 ../aigd/references/。
---

# AIGD · handoff(定稿 → 交接包)　[最小骨架]

> **包契约**:`aigd` 整包安装(编排器 `aigd/`+`references/` 与 6 子 skill(含 aigd-ui-capture)同级放于本环境的 skills 目录,随宿主 agent,如 Claude Code 的 `.claude/skills/`),**勿单拷本 skill**——正文 `../aigd/references/` 依赖同级 `aigd/`,单独拷会断链。

## 定位
阶段 4。**定稿门**:用户试玩签字才进;若生成时暴露设计漏洞,**允许打回 `aigd-iterate`**。这里才生成"贵的、下游的"产物(迭代期不产)。

## 读 / 产 / 写回
- **读**:`manifest` 该系统(规则/配置/引用共享)、`项目档案`、`../aigd/references/methodology.md`。
- **产(必出,平台无关)** —— 路径为工程化布局示例,**实际以 `项目档案『目录布局・命名规范』` 为准**:
  - `proto/<系统>.proto`:import `proto/common.proto`(concept/manifest 在全局规范登记的公共类型,**在此具象/补进 `common.proto`**——破环的落地点,首个用到它的 handoff 负责建、后续补),从 manifest 领号段(协议号/错误码)。
  - **proto 公式注释**:凡有计算公式的 message,在注释里给出**代入了字段引用的公式**,让实现 AI 直接照译、不必从散文规则反推。例:

    ```proto
    // 伤害: damage = atk * coefficient - def
    // 字段引用: atk=Actor.atk, coefficient=Skill.damage_coef, def=Target.def
    message DamageResult { int32 damage = 1; int32 atk = 2; int32 coefficient = 3; int32 def = 4; }
    ```

  - 工程版 `验收用例`(Gherkin,挂 R-编号,断言用 proto 字段 + `表[主键].字段`)。
- **产(按需)**:美术需求 / 客户端开发文档 / 服务端开发文档(-06);**策划版验收清单(md + xlsx)**——见 `../aigd/references/handoff-checklist.md`。
- **写回**:`manifest` 该系统 状态=定稿、占用号段、引用/被引用、待重验触发。

## 已固化子能力
- **策划版验收清单生成器**:`../aigd/references/handoff-checklist.md`(配置→md+xlsx,已试跑通过;副作用:自动抓配置矛盾产 `[待确认]`)。
- **配置一致性校验器(定稿门必跑)**:`../aigd/references/scripts/`
  - `config_check.py <config-spec.md> <表.xlsx>` —— schema 漂移(未文档化列/类型不符/表名漂移/声明域越界)。
  - `value_check.py <config-spec.md> <配置目录> [--acc <acceptance.md>] [--rules <系统.checks.json>] [--enums <枚举字典.md>]` —— 数据完整性(外键断链/验收悬空引用/领域规则如进化链长≤可进化次数)。
  - **退出码非 0(有 major)= 配置↔文档失同步,打回**。把"配置说明末尾那张自评 ✅ 却没人跑的校验清单"变成机检——经验:文档先定、xlsx 后改不同步,是交接包被下游读出分叉实现的头号根因。

## 准入 / 准出 / 打回
- **准入**:用户明确"定稿"(试玩满意);依赖系统的公共类型/共享表已就绪。
- **准出**:proto + 验收用例(+ 按需 端文档/策划版清单)齐,manifest 该系统状态=`定稿`、号段已登记 → 触发 `aigd-sync`;**且 `config_check` + `value_check` 无 major**(有则视为设计漏洞、打回)。
- **打回**:生成时暴露设计漏洞 → 状态回 `试玩中`、回 `aigd-iterate`;并按 manifest「打回规则」反查 `被依赖`,把依赖本系统的已定稿系统标 `待重验`。

## 边界
只到"AI 可直接开发"的交接物为止;不写具体技术栈的客户端/服务端代码(那是下游落地 skill)。
