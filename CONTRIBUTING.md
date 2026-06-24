# 贡献指南（AIGD）

## 跑测试

校验器/工具脚本有纯 stdlib 测试(**非 pytest**:每个 test 文件自带 runner)。

```bash
cd aigd/references/scripts
for t in tests/test_*.py; do python "$t"; done     # 逐个跑,末行打 N/N passed
pip install -r requirements.txt                     # 仅 ui_palette/slice(Pillow)、gherkin(openpyxl)需要
```

CI(`.github/workflows/tests.yml`)在 push/PR 上跑全套。改脚本必须保持全绿。

## 核心原则（改之前先懂）

1. **单一真源,不复制**:方法论只在 `aigd/references/`,6 个子 skill 是**薄路由壳**,正文用 `../aigd/references/` 取方法论。**别把方法论内容抄进子 skill**——会 5 处漂移。
2. **脚本:argv 驱动、零项目硬编码、确定性**(无 `Date.now`/随机)。读 xlsx 一律走 `xlsx_dump`(绕开 openpyxl 对国产导表的样式报错),只有"写 xlsx"才用 openpyxl。
3. **不含任何具体项目**:示例/测试夹具用中性示意名(`unit`/`evolveLine`/`potion`…),不写死真实游戏的表名/数值/路径。
4. **校验器宁可漏报不误报**:解不出/查不到 → 显式标记(`*_SKIP` info),不静默漏、不臆造。

## 怎么加东西

- **加一条领域规则**:在某 `<系统>.checks.json` 按 `value_check.py` 顶部的规则 schema 写(`cardinality`/`coverage`/`monotonic`),样例见 `aigd/references/scripts/checks/example.checks.json`。
- **加一个 patterns 弹药**:放 `aigd/references/patterns/<玩法范式|数值坑集|界面范式>/`,中性化、可移植,并在 `references/README.md` 现有清单登记。
- **加一个校验器**:纯 stdlib + argv + 配 `tests/test_*.py`(内存夹具,跑通"埋错能抓 + 干净不误报"),在 `scripts/README.md` 登记类别/严重度。
- **改 SKILL.md**:保持薄,只路由 + 准入/准出,方法论指向 references。

## 约定

- 文件 **UTF-8 无 BOM**;跨平台用 `/` 路径。各 harness 写法见 `aigd/references/harness-adapt.md`。
- markdown 表格内容列**别用裸 `|`**(撑乱表格)——用 `/` 或 `\|`。
- 工具调用用你 harness 要求的 function-call 格式,**发后复核产物真落盘**(读文件/`ls`),别假设已生效。
- 跨 harness:包结构在 Claude Code / ZCode / Gemini / Codex 通用(均已实测;Copilot 1.0.63 无 skills 机制,见 `harness-adapt.md`)。提 PR 前若能在更多 harness 上实测安装跑通,欢迎在 PR 里说一声。
