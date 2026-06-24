# -*- coding: utf-8 -*-
"""引用语法 + 抽取(纯 stdlib)——`ref_graph` 的共享底座,集中"什么算一个引用"。

设计文件里**可机检的结构化"边"**只认三类(不做散文模糊匹配,所以结构引用精度高):
  - R 编号     `R-<模块>-<子系统>-<序号>`(如 `R-EQUIP-GAIN-01`;模块码 `R-STG` 也算)
  - 配置引用   `表[主键]` / `表[主键].字段`(表+主键部分与 `config_index.REF_RE` 一致;字段在此可选)
  - proto 导入 `import "x.proto"`

**定义点 vs 引用点(R 编号)**:某行剥掉行首 markdown 标记(`# - * > | ` ` 空格)后**以 R 编号开头** =
定义点(规则文档的 `### R-X …` / 表格行 `| R-X | … |`);其余出现(散文 `符合 R-X`)= 引用点。不追求 100%,
定义点出现在 >1 文件 → 交人核(`DUP_DEF`),不臆断。

表由 xlsx 定义(自描述表头行1=表英文名,复用 `xlsx_dump`);proto 由同名 `.proto` 文件定义。
单一真源纪律:表引用语法**不另起一套**——表+主键部分与 `config_index.REF_RE` 保持一致(此处字段可选)。
"""
import os, re, zipfile

import config_index, xlsx_dump  # noqa: F401  复用其 xlsx 解析 / 表引用语法约定

# --- 引用语法(单一真源)---
RULE_RE = re.compile(r"R-[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*")
# 表+主键部分与 config_index.REF_RE 同;字段在此**可选**(影响面的边只需 表[主键],不必到字段)
TABLEREF_RE = re.compile(r"([A-Za-z]\w*)\[([^\[\]]+)\](?:\.([A-Za-z]\w*))?")
PROTO_IMPORT_RE = re.compile(r'import\s+"([^"]+\.proto)"')

_LEAD = re.compile(r"^[\s#>*|`\-]+")          # 行首 markdown 标记(标题/列表/引用/表格管线/反引号)

DESIGN_TEXT_EXTS = (".md", ".proto")          # 文本设计文件
SKIP_DIRS = {".git", "__pycache__", "node_modules", ".uploads", ".idea", ".vscode", ".github"}


def discover_files(root):
    """递归收集设计文件:文本(.md/.proto)与 .xlsx。跳过 .git/__pycache__ 等噪声目录与 ~$ 临时文件。"""
    texts, xlsxs = [], []
    for dp, dns, fns in os.walk(root):
        dns[:] = [d for d in dns if d not in SKIP_DIRS]
        for fn in fns:
            if fn.startswith("~$"):
                continue
            p = os.path.join(dp, fn)
            low = fn.lower()
            if low.endswith(DESIGN_TEXT_EXTS):
                texts.append(p)
            elif low.endswith(".xlsx"):
                xlsxs.append(p)
    return sorted(texts), sorted(xlsxs)


_HEADING = re.compile(r"^#{1,6}\s")


def _codes_in(line):
    """yield 该行真 R 编号——跳过 `R-XXX-*` 这类**通配/泛指**写法(散文"每条挂 R-POT-*")。
    只认破折号+星号 `-*` 为通配;紧跟的 `**`(markdown 粗体闭合 `**R-X**`)不是通配,照常计入。"""
    for m in RULE_RE.finditer(line):
        if line[m.end():m.end() + 2] == "-*":
            continue
        yield m.group(0)


def rule_defs_in_line(line):
    """该行的 R 编号**定义点集合**:
      - markdown 标题行(`## …`)→ 行内全部 R 编号(标题命名其 R 子系统,如 `## 一、合成 — R-POT-CRAFT`);
      - 非标题行 → 剥行首标记后**以 R 编号打头**的那个(叶子规则 `- **R-POT-CRAFT-01** …`)。
    两级粒度都算定义,故引用子系统码(proto/manifest 里的 `R-POT-CRAFT`)不会误判悬空。"""
    codes = list(_codes_in(line))
    if not codes:
        return set()
    if _HEADING.match(line):
        return set(codes)
    s = _LEAD.sub("", line)
    m = RULE_RE.match(s)
    if m and m.group(0) in codes:
        return {m.group(0)}
    return set()


def scan_text(path):
    """扫一个文本设计文件 → {rule_defs, rule_refs, table_refs, proto_imports}(均为 set)。

    rule_refs = 出现但非"本行定义点"的 R 编号,且去掉本文件自己定义的(自引不算引用)。"""
    defs, refs, tables, imports = set(), set(), set(), set()
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line_defs = rule_defs_in_line(line)
                defs |= line_defs
                for code in _codes_in(line):
                    if code not in line_defs:          # 非本行定义点 = 引用
                        refs.add(code)
                for m in TABLEREF_RE.finditer(line):
                    key = (m.group(2) or "").strip()
                    if not key or re.fullmatch(r"[…\.\s]+", key):
                        continue                       # `material[ … ]` 数组记法(键是省略号)非行引用,跳过
                    tables.add(m.group(1))             # 记到表英文名(主键/字段对影响面无关)
                for m in PROTO_IMPORT_RE.finditer(line):
                    imports.add(os.path.basename(m.group(1)))
    except Exception:
        pass
    refs -= defs                                       # 本文件定义的不算它自己引用
    return {"rule_defs": defs, "rule_refs": refs, "table_refs": tables, "proto_imports": imports}


def xlsx_tables(path):
    """xlsx 各 sheet 的表英文名(自描述表头行1[0])→ set。复用 xlsx_dump(纯 stdlib,绕开 openpyxl)。"""
    out = set()
    try:
        z = zipfile.ZipFile(path)
        shared = xlsx_dump.load_shared_strings(z)
        for _name, sp in xlsx_dump.sheet_map(z):
            rows = xlsx_dump.read_rows(z, sp, shared, 1)
            if rows and rows[0]:
                t = (rows[0][0] or "").strip()
                if t and re.match(r"^[A-Za-z]\w*$", t):
                    out.add(t)
        z.close()
    except Exception:
        pass
    return out
