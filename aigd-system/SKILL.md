---
name: aigd-system
description: AIGD 阶段2 · 单系统设计(讨论驱动)。当要把某个系统做出来——规则(-01,挂R编号)、配置表(带测试数据)、系统 html 原型时使用。源 xlsx 可选(给了就读、没给靠访谈)。是 aigd 包的一员;完整方法论见 ../aigd/references/methodology.md。
---

# AIGD · system(单系统设计)　[最小骨架]

> **包契约**:`aigd` 整包安装(编排器 `aigd/`+`references/` 与 6 子 skill(含 aigd-ui-capture)同级放于本环境的 skills 目录,随宿主 agent,如 Claude Code 的 `.claude/skills/`),**勿单拷本 skill**——正文 `../aigd/references/` 依赖同级 `aigd/`,单独拷会断链。

## 定位
阶段 2。每系统一遍。**只产"便宜、迭代期会改"的三样**:规则 / 配置(测试数据) / 系统原型。
**接口契约 / 验收用例 / 后端算法不在本阶段**——推迟到 `aigd-handoff`(定稿后)生,避免设计还在变就锁死、白 churn。

## 读 / 产 / 写回
- **读**:`manifest` 该系统条目(依赖、引用的共享真源)、`项目档案`;`../aigd/references/methodology.md`(以它为准)。
- **产** —— 下方路径为工程化布局示例,**实际目录/文件名以 `项目档案『目录布局・命名规范』` 为准**(与 manifest 跨层索引同源):
  - `docs/系统/<系统>/rules.md`(-01,挂 R-编号,散文无裸数值)。
  - `config/source/<表>.xlsx`(**带测试数据**)+ 配置说明。
  - `docs/prototypes/<系统>.html`(单文件零依赖可点;示意数据与配置对量)。
- **写回**:`manifest` 该系统跨层索引 + 状态=草稿;新枚举 / R-编号就地登记到全局规范。

## 方法论
**以 `../aigd/references/methodology.md` 为准**(本骨架不复制)。务必记住:契约/验收/后端归 handoff,本阶段不产。

## 准入 / 准出
- **准入**:manifest 该系统状态=`草稿`,且其**所有依赖系统至少 `草稿`**(否则缺底图,先回 concept 补)。
- **准出**:rules.md + 配置表(测试数据) + 系统原型.html 齐、manifest 跨层索引已写 → 转 `aigd-iterate`。

## 边界
不锁契约、不写验收、不做平衡(数值填测试值即可,深度平衡是包外工种)。
