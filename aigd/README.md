# AIGD — AI 辅助游戏设计方法论（可移植 skill 包）

把**游戏系统设计**变成一份**平台无关的交接包**,让另一个 AI(或人)能照着直接开发;并自带**确定性校验器**,把交接包门控到"可消费"才放行。

> 一句话:`aigd` 不替你拍数值、不绑定引擎——它是一套**讨论驱动**的设计流程 + 一组**机检脚本**,产出"规则/配置/契约/验收"四对齐、下游零猜的系统文档。

---

## 它解决什么

游戏设计交接最常见的失败不是文档写得少,而是**文档与配置悄悄失同步**("文档先定、表格后改没回写"),下游 AI/程序各读各的 → 实现分叉。AIGD 用三招挡住它:

1. **结构化产出(6 件套)**——每条规则挂编号、每个数值住配置表、散文只引 `表[主键].字段`,消除可解释空间。
2. **未定的显式挂账**——拿不准的口径一律标 `[待确认]` 交人拍板,AI 不替拍;这些标记恰好预言了下游会分叉的地方。
3. **确定性机检**——`config_check`/`value_check`/`manifest_check` 把"配置↔文档↔脊柱"的一致性变成退出码,0 major 才算可交接。

---

## 产出:一个系统的「6 件套」

| # | 产物 | 受众 |
|---|------|------|
| 1 | 功能规则(挂 `R-` 编号 + 界面 DSL) | 全员 |
| 2 | 配置表(自描述表头 xlsx,带测试数据) | 数值 |
| 3 | 配置说明(逐字段 类型/范围/引用) | 数值 + 导表 |
| 4 | 接口契约(proto,客户端=服务端同一份) | 前后端 |
| 5 | 界面规格 + 单文件可点原型 | 美术 + 客户端 |
| 6 | 验收用例(Gherkin,挂 `R-` 编号) | 测试 |

迭代期只产"便宜会改"的(规则/配置/原型),定稿后才生"贵的下游的"(契约/验收/后端)——别在设计还流动时锁契约。

---

## 包结构

```text
aigd/                  ← 本包 · 编排器 + 方法论真源
├── SKILL.md           编排器:读脊柱→判断进度→分派到子 skill
├── README.md          ← 你在看的这份
├── references/        方法论唯一真源(不复制、不漂移)
│   ├── methodology.md       设计访谈 / 命名 / 编号 / 八条门禁
│   ├── ui-dsl-spec.md        截图→DSL 的文法契约
│   ├── gotchas.md       真踩过的执行/交接/校验坑
│   ├── templates/           脊柱三模板(项目档案 / manifest / 实现总纲)
│   ├── patterns/            领域弹药(核心循环 / 养成范式 / 数值陷阱)
│   └── scripts/             确定性校验/工具脚本(纯 stdlib 为主)+ 测试
└── examples/
    └── potion-crafting/     ← 自包含玩具样例,跑通 3 个校验器
aigd-concept/   阶段1 立意 → 系统清单 + 脊柱
aigd-system/    阶段2 单系统设计(规则/配置/原型)
aigd-iterate/   阶段3 试玩迭代
aigd-handoff/   阶段4 定稿 → 契约/验收/交接包
aigd-sync/      贯穿:回写整合 + 标重验
aigd-ui-capture/ 工具:界面截图 → 界面 DSL
```

**整包安装、不可拆**:6 个子 skill 与 `aigd/` **同级**放入宿主的 skills 目录(如 Claude Code 的 `.claude/skills/`)。子 skill 正文用 `../aigd/references/` 取方法论,故 `aigd/` 必须同级存在。

---

## 上手

1. **装**:把下面**这 7 个文件夹(不多不少)**整体拷进宿主的 skills 目录(Claude Code = `.claude/skills/`),保持**平级**:

   ```text
   aigd/            ← 编排器 + references/(含方法论、脚本、模板、patterns、examples)
   aigd-concept/    阶段1 立意
   aigd-system/     阶段2 单系统设计
   aigd-iterate/    阶段3 迭代
   aigd-handoff/    阶段4 定稿交接
   aigd-sync/       回写整合
   aigd-ui-capture/ 界面截图→DSL
   ```

   - **必须 7 个都拷且平级**:子 skill 正文用 `../aigd/references/` 取方法论,缺 `aigd/` 或层级错就断链。
   - **不要拷** skills 目录下与 aigd 无关的其它 skill(它们是各自项目的东西);`.gitignore` 拷不拷都行。
   - 装好后该目录下应**正好**是这 7 个 `aigd`/`aigd-*` 文件夹。
   - **换 harness**:ZCode 装 `~/.zcode/skills/`;Gemini `~/.gemini/skills/`(或 `gemini skills install <repo>` 一键装);Codex `~/.codex/skills/`(或自带 skill-installer)。`SKILL.md` 格式在这几家通用且已实测;**Copilot 1.0.63 无 skills 机制、需适配**。装哪、怎么唤起、工具名对应见 [`references/harness-adapt.md`](references/harness-adapt.md)。
2. **跑校验器要 Python**(多数脚本纯标准库;`ui_palette`/`ui_slice` 需 Pillow,`gherkin_to_checklist` 写 xlsx 需 openpyxl,见 `references/scripts/requirements.txt`)。
3. **新项目**:调 `aigd`(不知道在哪一步就让它路由)或直接 `aigd-concept` 立意建脊柱 → `aigd-system` 逐系统设计 → 定稿 `aigd-handoff`。
4. **先感受**:进 [`examples/potion-crafting/`](examples/potion-crafting/),照其 README 把 3 个校验器跑一遍,看"6 件套 + 机检门控"实际长什么样。

---

## 校验器(references/scripts)

| 脚本 | 管什么 | 依赖 |
|------|--------|------|
| `config_check.py` | 配置说明 ↔ xlsx **schema 漂移**(列/类型/表名/域) | stdlib |
| `value_check.py` | 配置**数据完整性**(外键断链/验收悬空/覆盖·单调·基数) | stdlib |
| `manifest_check.py` | 脊柱 **manifest 自洽**(模块码登记/依赖指向/状态/分块/依赖环 SCC) | stdlib |
| `ui_render.py` | 界面 DSL → 可点 html/svg 线框 | stdlib |
| `gherkin_to_checklist.py` | 验收用例 → 策划版清单 xlsx | openpyxl |
| `xlsx_dump.py` | 任意 xlsx → 文本(绕开 openpyxl 对国产导表的报错) | stdlib |

全部 **argv 驱动、零项目硬编码、确定性**(可进 CI)。详见 [`references/scripts/README.md`](references/scripts/README.md)。退出码非 0 = 有 major,接进定稿门禁。

---

## 可移植 & 状态

- **跨 harness**:包结构(`SKILL.md` + `name`/`description` frontmatter)在 **Claude Code / ZCode / Gemini CLI / Codex** 通用;不同的只是装哪个目录、怎么唤起、读写工具名——见 [`references/harness-adapt.md`](references/harness-adapt.md)。方法论本身不依赖任何 harness、不依赖其指令文件(`CLAUDE.md`/`AGENTS.md`/`GEMINI.md`)。校验器脚本是 argv 驱动命令行,只要有 Python 哪家都一样用。
  > **实测状态(2026-06-23)**:已在 **Claude Code(原生·真项目)、ZCode 3.1.3(Claude 系)、Gemini CLI 0.47(Google)、Codex 0.140(OpenAI)** 四个 harness 实测跑通——发现 + 路由 + 执行全过,**含 Gemini、Codex 两个跨厂**;Gemini/Codex 还能用各自原生 installer 从本仓库一键装。**Copilot CLI 1.0.63 经实测无 SKILL.md skills 机制**(走 AGENTS.md/MCP/plugin),aigd 需适配。详见 [`references/harness-adapt.md`](references/harness-adapt.md)。
- **适用边界**:管设计交接的结构与一致性,**不管数值平衡**;html 原型验信息架构/流程,**验不了手感/时序/网络**(实时战斗类只验信息架构);UI 密集系统适配最好。详见仓库根 `README.md`「适用边界」。
- **项目专属**(立意/约定/系统清单/号段)全部住**脊柱**(`项目档案`/`manifest`),不进本包——换项目换 AI,读脊柱即可接手。
- `patterns/` 是会长大的**启动包**(目前:5 种核心循环 / 战斗单位养成范式 / 10 条数值陷阱)。
