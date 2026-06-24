# AIGD 工具链（references/scripts）

AIGD 方法论自带的**确定性脚本**。两条主线:

- **界面知识库**:截图 → 界面 DSL → 还原 html/svg、采色、切素材（攒可检索的界面范式库）。
- **配置/交接校验**:把"配置说明 ↔ xlsx ↔ 验收用例"的一致性变成机检，接进定稿门禁；并从验收用例生成策划版清单。

## 设计原则（所有脚本共守）

- **argv 驱动、零项目硬编码**——路径全走参数，可移植；项目专属映射放配置目录（见下）。
- **确定性**——同输入同输出（无 `Date.now`/随机），可进 CI、可 diff。
- **能纯 stdlib 就纯 stdlib**——读 xlsx 一律走 `xlsx_dump`（`zipfile`+`ElementTree`），**绕开 openpyxl 读国产导表 xlsx 的 `Colors must be aRGB hex values` 报错**；只有"写 xlsx"才用 openpyxl。
- **不静默漏**——校验器对"看起来该查却没查"的项显式记 `FK_SKIP`/`RULE_SKIP`（info），不当作通过。
- **不臆造、宁可漏报不误报**——查不到/解不出 → 标记，不猜值（误报最伤校验器可信度）。
- **自描述表头约定**(xlsx)：第 1 行=表英文名(codegen 类名)、第 2 行=字段类型、第 3 行=字段英文 key(数组用 `field[ … ]`)、第 4 行=中文名(批注写枚举/口径)、第 5 行起=数据。

## 依赖

| 依赖 | 谁用 | 装法 |
|------|------|------|
| 纯标准库 | `ui_render` `xlsx_dump` `resolve_loc` `config_index` `config_check` `value_check` `manifest_check` `ref_lib` `ref_graph` | 无需安装 |
| Pillow≥9 | `ui_palette` `ui_slice`（图像采色/切片） | `pip install Pillow` |
| openpyxl≥3 | `gherkin_to_checklist`（**写** xlsx） | `pip install openpyxl` |

> 见 `requirements.txt`。缺依赖时相关测试**优雅跳过**（不算失败）。

---

## A. 界面知识库工具链

> 工具1 = **`aigd-ui-capture` skill**（不是脚本）：把截图读成一份界面 DSL（`.md`）。文法契约见 `../界面DSL规范.md`。以下脚本消费这份 DSL。

### `ui_render.py` — 工具2 · DSL → html/svg（纯 stdlib，确定性）
```
python ui_render.py <DSL.md> <out.html> [--svg <out.svg>] [--skin <skin.json>] [--modules <模块目录>]
```
- **入**：界面 DSL（`# 屏头` + `## Layout` 缩进树 + `## Events` + 可选 `## 皮肤`/`## 引用`）。
- **出**：可点矢量 html（带「校准」拖拽 + 「导出 DSL」回贴校正坐标）+ 可选 svg。
- 支持 屏/模块/实例引用（`resolve` 预渲染展平）、皮肤段/主题（`@canvas`）、缺 `z` 按缩进+文档序兜底。
- 改图比对结构/层级/比例/文本/交互——**不追像素复刻**（美术换自己素材）。

### `ui_palette.py` — 工具3 · 原图采色 → 皮肤段（Pillow）
```
python ui_palette.py <DSL.md> <原图> --merge
```
- 按元素 id 从原图采主色，写成 `## 皮肤` 段回贴 DSL（**不写进元素行**，整段可换可删）。背景槽/立绘槽等美术槽不采。

### `ui_slice.py` — 工具3 · 图+DSL → 逐元素切片（Pillow）
```
python ui_slice.py <DSL.md> <原图> [outdir] [--only 背景槽,立绘槽,图标槽]
```
- 把原图按元素 bbox 切成逐元素 png + `index.md` 接触表，便于参考/替换竞品部件。`--only` 只切指定类型槽。

---

## B. 配置 / 交接校验工具链

### `config_check.py` — 工具4 · 配置说明 ↔ xlsx **schema 漂移**（纯 stdlib）
```
python config_check.py <配置说明.md> <表.xlsx>
```
管"**结构**对不对"：列/类型/表名/声明域。退出码非 0 = 有 major。

| 类别 | 抓什么 | 严重度 |
|------|--------|--------|
| `UNDOC_COL` | xlsx 有列、配置说明没记（改 xlsx 没回写的典型痕迹） | major |
| `MISSING_COL` | 配置说明声明字段、xlsx 无此列 | major |
| `TYPE` | 同名字段 文档类型 ≠ xlsx 类型 | major |
| `RENAME` | 文档表名找不到同名 sheet，给最接近的（疑改名） | major |
| `MISSING_TABLE` | 文档声明表、xlsx 无 sheet | major |
| `DOMAIN` | 声明域（`0/1`、`1~5` 等可解析的）对不上实际数据，给越界样例 | advisory（人判） |

### `value_check.py` — 工具5 · 配置**数据完整性**（纯 stdlib）
```
python value_check.py <配置说明.md> <配置目录> \
  [--acc <验收用例.md>] [--rules <系统.checks.json>] \
  [--enums <枚举字典.md>] [--keymap <复合键映射.json>] [--refmap <引用表映射.json>]
```
管"**数据本身/数据之间**对不对"。`复合键映射.json` 与 `引用表映射.json` 在配置目录时**自动加载**（无需显式传）。退出码非 0 = 有 major。

| 类别 | 抓什么 | 严重度 |
|------|--------|--------|
| `FK_BREAK` | 引用列 `表.字段` 外键断链：源有值在目标列找不到（数组源逐成员校验；跨文件经 refmap） | major |
| `RULE_CARDINALITY` | 数组成员数 vs 另一表的值（如 进化链长−1 ≤ 品质可进化次数） | 规则可配 `severity` |
| `ACC_DANGLING` | 验收用例 `表[主键].字段` 引用解析不到配置行（行缺=悬空；字段空不算） | advisory |
| `RULE_MONOTONIC` / `RULE_COVERAGE` | 字段随档位单调不减 / 整数主键连续覆盖无断档 | advisory |
| `FK_SKIP` / `RULE_SKIP` / `UNDOC_TABLE` | 跨文档/未登记引用、未识别数组列、未对应 sheet——**显式记、不静默漏** | info |
| `0` / 空 | 外键空哨兵（当 id 域恒正、`0`=无引用时）→ 不参与断链判定 | — |

**规则文件** `checks/<系统>.checks.json`（样例 `checks/example.checks.json`，表/字段名均为示意）：
```json
{ "rules": [
  {"type":"cardinality","severity":"advisory","array_table":"evolveLine","array_field":"unit",
   "member_table":"unit","member_rarity_field":"rarity","limit_table":"rarityCap","limit_field":"evolution"},
  {"type":"coverage","table":"levelTable","field":"id","min":1,"max":200},
  {"type":"monotonic","table":"starTable","field":"HpPercentage","order_field":"star","group_fields":["rarity","element"]}
] }
```

### `manifest_check.py` — 工具6 · 脊柱 **manifest 内部一致性**（纯 stdlib）
```
python manifest_check.py <manifest.md>
```
管"**脊柱自己对不对**"：6 张强类型表(A–F)的跨表引用是否自洽。`config_check`/`value_check` 管"配置 ↔ 文档"，这个管"脊柱内部"。退出码非 0 = 有 major。

| 类别 | 抓什么 | 严重度 |
|------|--------|--------|
| `SEG_MISSING` | A 表系统的 R-模块码，B 表号段登记里查不到 | major |
| `DANGLING_DEP` | A 表「依赖(上游)」里的显式系统ID（`S\d+`）在 A 表不存在 | major |
| `BAD_STATUS` | A/D/E 表状态值不在状态枚举内（`定稿*` 归一为 `定稿`） | major |
| `NO_CBLOCK` | A 表系统在 C 表无 `### <ID>` 跨层索引分块 | major |
| `CYCLE` | 依赖图互依集群（Tarjan SCC，按系统名/ID 连边、排自环、长名优先），每个集群报一次，提示公共类型须先全局登记破环 | advisory（人判） |
| `DEFINED_NO_CONTRACT` | C 表里 `定稿`/`定稿*` 系统分块缺 proto 或 验收行 | advisory |
| `SEG_UNUSED` / `CBLOCK_ORPHAN` | B 表号段空挂 / C 表残留分块（系统已删） | advisory |
| `DEP_BY_NAME` | 依赖边按系统名从散文依赖列解析（真 manifest 依赖列非纯 ID）——透明声明 | info |

> 真 manifest 的「依赖(上游)」列是**散文 + 按名引用**（`物品[广播](分解道具)`），不是干净 ID 列。故 `DANGLING_DEP` 只对**显式 `S\d+`** 报 major（零误报），环检测则按**系统名子串**连边并排除自环。**不抓**：D 表待重验触发 ↔ F 表对账（触发项混点对点口径，机检会大量误报，留人工）。

### `ref_graph.py` — 工具7 · 设计文件**双向引用图** + 悬空引用门禁（纯 stdlib）
```
python ref_graph.py <项目根> [--out refs.md] [--who-refs <符号>] [--check] [--json]
```
扫全部设计文件（`.md`/`.proto`/`.xlsx`），抽**结构化**引用（`R-编号` / `表[主键]` / proto `import`），给"每文件→引用了谁 / ←被谁引用（=**改它的影响集**）"。纪律:**正向引用是真源,反向索引实时算、绝不落盘**——所以不会像手写"被引用"那样漂移。退出码非 0（`--check` 下）= 有 major。

| 类别 | 抓什么 | 严重度 |
|------|--------|--------|
| `DANGLING_RULE` | `R-编号` 被引用但无任何文件定义（标题命名子系统 `## … R-X` / 行首叶子规则 `- **R-X-01**` 都算定义） | major |
| `DANGLING_PROTO` | `import "x.proto"` 找不到对应 `.proto` 文件 | major |
| `DANGLING_TABLE` | `表[主键]` 无对应 xlsx 表（也可能 array 记法误命中，`[推断]` 需人核） | advisory |
| `DUP_DEF` | 同一 `R-编号` 在多处呈定义点（应唯一定义） | advisory |

- `--who-refs R-X`：查某符号（R 编号/表名/`x.proto`）"定义在哪 + 被谁引用"的影响集。
- `--out refs.md`：生成双向图（**纯产物，顶部标 `DO NOT EDIT`，绝不手写进规则/配置说明/manifest 等真源文档**；改文档重跑覆盖）。
- 只认结构化令牌、**不做散文模糊匹配**（故结构引用精度高）；R 编号"定义点 vs 引用点"用标题/行首启发式，通配 `R-X-*` 与粗体 `**R-X**` 已区分。

### `ref_lib.py` — 共享层（库，非 CLI）
`ref_graph` 的**引用语法真源**:`RULE_RE`(R 编号)、`TABLEREF_RE`(`表[主键]`,表+主键部分与 `config_index.REF_RE` 一致、字段在此可选)、proto `import`,以及"定义点 vs 引用点"判定、通配/数组记法过滤、文件发现。复用 `xlsx_dump` 取 xlsx 表名。**引用语法集中一处,避免多工具各写一套而互相漂移。**

### `config_index.py` — 共享层（库，非 CLI）
`value_check` 与 `gherkin_to_checklist` 共用。提供：`build_index`（扫配置目录所有 xlsx → 表索引，含数组列 `arraycols`）、`lookup`（`表[主键].字段`→真值/`MULTI`/`None`，复合键经 keymap 分量匹配、枚举名经 enums 解）、`row_exists`（区分"行缺"与"字段空"）、`column_values` / `array_column_values`（外键取值域）、`load_enums` / `load_keymap`。

### `gherkin_to_checklist.py` — 验收用例 → 策划版清单 xlsx（openpyxl 写）
```
python gherkin_to_checklist.py <验收用例.md> [out.xlsx] \
  [--config <配置目录>] [--enums <枚举字典.md>] [--keymap <复合键映射.json>] [--loc <LocalizationText.xlsx>]
```
把 Gherkin 验收用例翻成策划/QA 逐条勾的清单（说明页 + 测试清单页 + 进度统计）。`--config` 时把断言里的 `表[主键].字段` **代入配置真值**（反向校验配置↔规则一致性）；护栏：多键/查不到标 `[需手填]`/`[查不到]`，**绝不臆造**。

### `xlsx_dump.py` — 可移植 xlsx → 文本（纯 stdlib，底座）
```
python xlsx_dump.py <file.xlsx> [out.txt] [max_rows]
```
`zipfile`+`ElementTree` 直解 xlsx（绕开 openpyxl 样式报错），是上面所有读 xlsx 的脚本的**共同底座**。中文务必写文件再看（控制台直接 print 可能乱码）。

### `resolve_loc.py` — LocalizationText 文本 id → 中文（纯 stdlib）
```
python resolve_loc.py <LocalizationText.xlsx> [out.txt] [start-end ...]
```
建 文本 id→中文 映射，供 `gherkin_to_checklist --loc` 给 NameId/DescId 附中文。

---

## 项目元数据（放配置目录，与 xlsx 同处；value_check/gherkin 自动加载）

| 文件 | 作用 |
|------|------|
| `复合键映射.json` | 复合主键表 → 分量列顺序（如 `starTable: [rarity,element,star]`），供 `lookup` 按列匹配 |
| `引用表映射.json` | 引用列里中文名/文档名 → 英文 `表.字段`（如 `道具表→item.id`），供跨文件外键解析；**外部/未建系统有意不登记**（登记会产生不可修假 major） |
| `枚举字典.md` | 枚举名/中文 → id（在全局规范，非配置目录），`lookup` 解复合键里的枚举名 |

## 测试

`tests/test_*.py`，**stdlib 自带 runner，不依赖 pytest**：
```
python tests/test_value_check.py      # 单个
```
每个 test 文件 `if __name__=="__main__"` 跑全部 `test_*`、打 PASS/FAIL、按失败数设退出码；缺 Pillow 的用例优雅跳过。逻辑层用内存夹具（不落 xlsx、表/字段名均为示意），纯 stdlib、无项目依赖。

跑全套：
```
for t in tests/test_*.py; do python "$t" | tail -1; done   # 自动含 manifest_check / ref_graph 等
```

## 接进门禁的地方

- **写脊柱后(各 skill「写回」步)**：跑 `manifest_check`，有 major → 先修脊柱自洽（模块码登记 / 依赖指向 / 状态 / C 分块）再继续。模板自检段见 `templates/manifest.模板.md` 末「自检命令」。
- **`aigd-handoff` 定稿准入**：定稿前必跑 `config_check` + `value_check`，有 major → 打回。
- **质量门禁（方法论第 4 步八条）**：「配置每字段有类型/范围/引用」「跨表/跨文件引用无断链」两条挂这俩机检命令——**别只勾框自评**（"文档先定、xlsx 后改不同步"是交接包被下游读出分叉实现的头号根因）。
- **（可选）引用完整性**：跑 `ref_graph <根> --check`，`R-编号`/proto 悬空 = 失败（补强"引用无断链"那条）；平时用 `ref_graph <根> --who-refs R-X` 查"改这条会牵动哪些文档/验收/proto"。

## 典型流程

**截图入库**：`aigd-ui-capture`(工具1) → `<屏ID>.md` → `ui_render`(还原验证) + `ui_palette --merge`(采色) [+ `ui_slice`(拆素材)] → 入 `patterns/界面范式/`。

**配置定稿校验**：`config_check`(schema) + `value_check`(数据完整性) → **均 0 major** 才算过 → `gherkin_to_checklist --config`(出策划版清单 + 反向核配置)。
