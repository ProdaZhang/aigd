# AIGD references —— 自带方法论真源(可移植核心)

方法论存这里,**不依赖任何项目**;项目专属的东西由**脊柱**(项目档案 / manifest / 实现总纲)承载。换项目换 AI,读脊柱即可接手。

## 现有
- **methodology.md** —— 6 件套骨架 / 设计访谈 / 命名 / 编号 / 自描述表头 / 界面 DSL / 八条质量门禁 / 硬约束(由原单一 `aigd` skill 迁入)。
- **templates/** —— 脊柱三模板(强类型):`project-charter.tpl.md` / `manifest.tpl.md` / `impl-overview.tpl.md`;+ 改动账本模板 `CHANGELOG.tpl.md`(唯一项目环境前置)。`aigd-concept` 照它建脊柱,后续各 skill 读写脊柱按它的列。
- **ui-dsl-spec.md** —— **权威**界面 DSL 文法契约(文件骨架 / Layout 行文法 / 类型表 / z 分层 / 形状 / 来源语义 / 看图配方 / 皮肤与主题);`aigd-ui-capture` 第 0 步与渲染器以它为准。
- **scripts/** —— 可复用确定性工具脚本(argv 驱动、无项目硬编码)。**详见 `scripts/README.md`**(工具清单/用法/依赖/门禁接入/流程)。两条主线:
  - **界面知识库**:`ui_render.py`(工具2 · DSL→html/svg,纯 stdlib)/ `ui_palette.py`(工具3 · 采色→皮肤段)/ `ui_slice.py`(工具3 · 切片→接触表)。
  - **配置/交接校验**:`config_check.py`(工具4 · 配置说明↔xlsx schema 漂移)/ `value_check.py`(工具5 · 数据完整性:外键断链/验收悬空/cardinality·monotonic·coverage)/ `config_index.py`(共享层)/ `gherkin_to_checklist.py`(验收用例→策划版清单)。接进 `aigd-handoff` 定稿准入 + 模板 §7 质量门禁。
  - **底座**:`xlsx_dump.py`(zipfile+xml 解任意国产 xlsx,绕开 openpyxl `Colors must be aRGB` 报错)/ `resolve_loc.py`(LocalizationText 文本 id→中文)。`checks/<系统>.checks.json` 领域规则 + `tests/`(stdlib runner)。
- **example.skin.json** —— 按类型的**示例**主题皮肤,`ui_render.py --skin` 套用演示;用户按自己视觉规范(项目档案『美术风格/品牌』指定)替换配色。
- **handoff-checklist.md** —— `aigd-handoff` 子能力:配置 → 策划版验收清单(md + xlsx)的配方与读写契约(已试跑通过)。
- **patterns/** —— **领域知识弹药**(方法论给"流程",这里给"领域知识",供 concept/system 访谈当引导者时砍弱方向/提口径):
  - `loops/core-loops.md` —— 5 种核心循环模板(收集养成验证 / 探索建造 / PVP / 抽卡推图 / 经济),每种含驱动变量·反馈·失速点·访谈要问什么。
  - `loops/battle-unit-progression.md` —— 战斗单位多维养成范式(收集养成类:收集单位≠形态单位、品质封顶、累计vs增量、补全数据、解锁参数化)。
  - `numeric-traps/numeric-traps.md` —— 10 条数值/经济陷阱 + ⚠️真踩过的(哨兵撞车 / 累计混淆)+ 坑↔机检工具速查。
  - `界面范式/` —— `aigd-ui-capture` 把竞品/自家截图入库的界面 DSL 库(随用随攒)。
- **gotchas.md** —— 本包迭代 + 消费端验证中真踩过的坑速查(被 `methodology.md` 指向,system/handoff 前过一遍)。
- **harness-adapt.md** —— 跨 harness 的装法/唤起/工具名对应 + 实测状态:包结构在 Claude Code / ZCode / Gemini / Codex 通用(均已实测,含 Gemini/Codex 两个跨厂);**Copilot 1.0.63 无 skills 机制、需适配**。

## 待补(TODO,建包后续充实)
- **编号与量纲rules.md / 质量门禁.md / 命名规范.md** —— 目前内联在「methodology.md」;具体内容在各项目的全局规范(路径走脊柱「项目档案」指定的规范目录,非包内固定路径)。后续抽离为**可移植副本**。
- **patterns/ 领域知识弹药** —— 已落地最小启动包(核心循环 / 战斗养成范式 / 数值陷阱,见上「现有」);**随项目继续攒**(更多玩法范式、品类专项坑、界面范式由 ui-capture 入库)。

## 项目层 vs 包层(别混)
- **包层(这里)** = 方法论、模板、配方,跨项目通用。
- **项目层(脊柱)** = 立意/平台/约定/系统清单/号段/跨层索引,每项目一份实例。
- 子 skill = 在脊柱上的操作:**读脊柱 → 干活 → 写回脊柱**,方法论来这里取。

## 打包与可移植(已定:整包为单元)
**决策**:`aigd` 作为**一个不可拆的包**分发/安装,不支持单拷子 skill。
- **包契约**(已写进每个子 skill 顶部):整包安装 = 编排器 `aigd/`(含 `references/`)+ 6 子 skill(`aigd-concept/system/iterate/handoff/sync/ui-capture`)**同级放于本环境的 skills 目录**(随宿主 agent,如 Claude Code 的 `.claude/skills/`);子 skill 正文用 `../aigd/references/` 取方法论,故 `aigd/` 必须同级存在。
- **单一真源**:references 只此一份(`aigd/references/`),**不复制**——杜绝漂移。
- **为什么不选另两案**:
  - (B) 子 skill 自带 references 副本 → 方法论仍在演进,5 份副本(每子 skill 各一)必然漂移、每次改要 5 处同步,得不偿失;
  - (A) 做成 plugin → 会引入 `aigd:concept` 命名空间,改掉既定扁平名 `aigd-concept`,演进期不必要。
- **升级路径**:将来要"装一个就能用"(独立安装 / 市场分发)且方法论已稳 → 再升级为 **plugin**(方案 A),届时接受 `aigd:concept` 命名空间、references 随包走。现在不过早固化。
