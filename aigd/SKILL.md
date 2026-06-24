---
name: aigd
description: AIGD(AI Game Design)总入口 / 编排器。当用户要**从零开张一个游戏项目**、**不确定该用哪个阶段**、想**总览或推进整条研发流程**,或要**维护项目脊柱(项目档案/manifest)**时使用。本 skill 只做"读脊柱→判断进度→分派到对应子 skill";**已经明确某一步(立意/做系统/迭代/定稿/回写/截图入库)就直接用对应子 skill**(aigd-concept / aigd-system / aigd-iterate / aigd-handoff / aigd-sync / aigd-ui-capture)。方法论自带于 references/,不依赖具体项目。
---

# AIGD · 编排器(orchestrator)

AIGD = **AI Game Design**。一套**可移植**的 AI 游戏研发方法论包:覆盖 **头脑风暴 → 系统设计 → 试玩迭代 → 定稿交接**,产出"另一个 AI 能直接照着开发"的**交接包**(平台无关);**落地实现(选技术栈写客户端/服务端)不在本包**,留给未来单独的落地 skill。

> 状态:**骨架**。各子 skill 与部分 references 待充实(见各文件 TODO / `references/README.md`)。

## 核心模型(细节以 references/ 为准)
- **两层**:① 活的**项目层(脊柱)**——`项目档案`(立意/平台/目标用户/品类/风格/命名约定)+ `manifest`(系统清单 + 依赖图 + 跨层索引 + 冻结账本 + 号段登记),持续修订;② **每系统生产循环**。
- **集中真源**:枚举 / 编号 / 接口契约 / 配置表 归项目层;**双份**(系统 + 全局):验收 / 资源需求 / 原型;**纯系统层**:规则 / 后端算法。
- **每个操作都**:读脊柱 → 干活 → 写回脊柱。下层发现(新系统/新依赖/新枚举/改立意)反向回写上层。
- 方法论真源:`references/methodology.md`、`references/README.md`。

## 路由:按"这次想干啥"派子 skill
| 你要做的 | 子 skill |
|---|---|
| 立意 / 核心循环 / 平台 / 目标用户 / 拆系统 | **aigd-concept** |
| 设计某系统(规则 + 配置测试数据 + html 原型) | **aigd-system** |
| 试玩后优化某系统(规则/配置/原型,可反复) | **aigd-iterate** |
| 某系统定稿 → 契约 / 验收 / 端文档 / 策划版验收清单 | **aigd-handoff** |
| 回写全局规范 / 整体原型 / 实现总纲;共享项变更标重验 | **aigd-sync** |
| 界面截图 → 界面 DSL(攒 patterns 界面范式知识库,供设计时检索参考) | **aigd-ui-capture** |

## 用法
1. **先读脊柱**(项目档案 + manifest)判断:项目到了哪一步、这次的系统处于什么状态、缺什么。
2. 没有脊柱 → 先 `aigd-concept` 起项目(建脊柱)。
3. 选对应子 skill,**用 Skill 工具 invoke 它**执行;各子 skill 都读写同一脊柱,保持一致与可重入(跨会话/换 AI 可接手)。
4. 典型路径:concept(一次)→ 每系统 {system → iterate…(反复)→ handoff 定稿} → sync(持续)。**iterate 完不直接进 sync**——sync 准入要「系统已 `定稿`」,而只有 handoff 能定稿;顺序非强制,按需路由。

> **无脊柱时**(首次在某项目用、`项目档案`/`manifest` 还不存在):"读脊柱"会扑空 → 直接 route `aigd-concept` 起脊柱,属正常、不是错误。

## 开局自检（每次进 /aigd 先跑 —— 主动推进,别等用户猜)
1. **脊柱在不在?** 在 → 读 `项目档案.md` + `manifest.md`;不在 → route `aigd-concept` 起项目。
2. **哪些系统状态 ≠ `定稿`?** 列出,问用户这次推哪个。
3. **有 `待重验` 系统?** 提醒先重验(某共享项变过)→ route `aigd-sync` 结清(重验通过回 `定稿` / 不过打回)。
4. **号段冲突 / 依赖图有环?** 检查并报告。

## 状态流转（非线性 · 带回退)
```
概念 ──→ 系统设计 ⇄ 试玩迭代 ──→ 定稿 ──→ 整合
 ▲           │            │         │(打回)
 │           │            │         ▼
 │           └─边界画错────┴─────→ 回试玩/回概念
 └────────── 整合发现不兼容 / 需重拆 ──────────┘
```
- 任何**打回 / 重拆**都在 manifest「回退记录」记一笔,并按「打回规则」反查 `被依赖`,把下游已定稿系统标 `待重验`(见 `aigd-handoff` / `aigd-sync`)。
- 模板:`references/templates/`(项目档案 / manifest / 实现总纲,强类型)。

## 包结构(整包安装,勿拆)
`aigd`(本编排器,含 `references/` 方法论与模板)+ 6 子 skill `aigd-concept / system / iterate / handoff / sync / ui-capture`,**同级安装于本环境的 skills 目录**(随宿主 agent,如 Claude Code 的 `.claude/skills/`)。子 skill 正文用 `../aigd/references/` 取方法论 → `aigd/` 必须同级存在(`aigd-ui-capture` 走 `../aigd/references/ui-dsl-spec.md` 与 `scripts/`,同理)。**单一真源、勿单拷**;将来要独立分发再升级为 plugin(详见 `references/README.md`「打包与可移植」)。

## 项目环境建议
- 脊柱文件(`项目档案` / `manifest`)与设计产物建议纳入 **Git/SVN** 管理;编排器每次操作前宜瞄一眼版本状态。
- **CHANGELOG(改动账本)与版本控制互补**:VCS 记「改了什么」,CHANGELOG 记「为什么 + 哪个模型」(本方法论是 AI 辅助流程,记模型便于回溯某次改动出处)。

## 边界
- 做到"**AI 可直接开发的交接包**"为止(平台无关:规则 / 契约 / 配置 / 验收 / 原型 / 资源需求)。
- 技术栈选择与客户端/服务端实现 = **下游**,不在本包。
