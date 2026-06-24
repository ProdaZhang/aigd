# -*- coding: utf-8 -*-
"""Reference grammar + extraction (pure stdlib) -- the shared foundation of `ref_graph`, centralizing "what counts as a reference".

Only three kinds of **machine-checkable structured "edges"** are recognized in design files (no fuzzy prose matching, so structural references are high-precision):
  - R-code       `R-<module>-<subsystem>-<seq>` (e.g. `R-EQUIP-GAIN-01`; the module code `R-STG` also counts)
  - config ref   `Table[primary key]` / `Table[primary key].field` (the table+primary-key part is consistent with `config_index.REF_RE`; the field is optional here)
  - proto import `import "x.proto"`

**Definition point vs reference point (R-code)**: a line that, after stripping leading markdown markers (`# - * > | ` ` space), **starts with an R-code** =
a definition point (the rule doc's `### R-X ...` / table row `| R-X | ... |`); any other occurrence (prose `conforms to R-X`) = a reference point. Not aiming for 100%;
a definition point appearing in >1 file -> hand to a human (`DUP_DEF`), no guessing.

Tables are defined by xlsx (self-describing header row1=English table name, reusing `xlsx_dump`); protos are defined by the same-named `.proto` file.
Single-source-of-truth discipline: the table reference grammar **does not start a separate one** -- the table+primary-key part stays consistent with `config_index.REF_RE` (the field is optional here).
"""
import os, re, zipfile

import config_index, xlsx_dump  # noqa: F401  reuse its xlsx parsing / table-reference grammar convention

# --- reference grammar (single source of truth) ---
RULE_RE = re.compile(r"R-[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*(?![a-z])")  # (?![a-z]): don't carve "R-M" out of CamelCase like "R-ModuleCode"; real R-codes end at a word boundary
# The table+primary-key part is the same as config_index.REF_RE; the field is **optional** here (impact-set edges only need Table[primary key], not the field)
TABLEREF_RE = re.compile(r"([A-Za-z]\w*)\[([^\[\]]+)\](?:\.([A-Za-z]\w*))?")
PROTO_IMPORT_RE = re.compile(r'import\s+"([^"]+\.proto)"')

_LEAD = re.compile(r"^[\s#>*|`\-]+")          # leading markdown markers (heading/list/quote/table pipe/backtick)

DESIGN_TEXT_EXTS = (".md", ".proto")          # text design files
SKIP_DIRS = {".git", "__pycache__", "node_modules", ".uploads", ".idea", ".vscode", ".github"}


def discover_files(root):
    """Recursively collect design files: text (.md/.proto) and .xlsx. Skip noise dirs like .git/__pycache__ and ~$ temp files."""
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
    """yield the real R-codes on this line -- skipping `R-XXX-*` wildcard/generic notations (prose like "each one tagged R-POT-*").
    Only dash+asterisk `-*` counts as a wildcard; a following `**` (markdown bold close `**R-X**`) is not a wildcard and is counted as usual."""
    for m in RULE_RE.finditer(line):
        if line[m.end():m.end() + 2] == "-*":
            continue
        yield m.group(0)


def rule_defs_in_line(line):
    """The set of R-code **definition points** on this line:
      - markdown heading line (`## ...`) -> all R-codes in the line (the heading names its R subsystem, e.g. `## I. Crafting -- R-POT-CRAFT`);
      - non-heading line -> the one that, after stripping leading markers, **starts with an R-code** (leaf rule `- **R-POT-CRAFT-01** ...`).
    Both granularities count as definitions, so referencing a subsystem code (`R-POT-CRAFT` in proto/manifest) is not misjudged as dangling."""
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
    """Scan one text design file -> {rule_defs, rule_refs, table_refs, proto_imports} (all sets).

    rule_refs = R-codes that appear but are not "this line's definition point", minus the ones this file itself defines (self-reference does not count as a reference)."""
    defs, refs, tables, imports = set(), set(), set(), set()
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line_defs = rule_defs_in_line(line)
                defs |= line_defs
                for code in _codes_in(line):
                    if code not in line_defs:          # not this line's definition point = a reference
                        refs.add(code)
                for m in TABLEREF_RE.finditer(line):
                    key = (m.group(2) or "").strip()
                    if not key or re.fullmatch(r"[…\.\s]+", key):
                        continue                       # `material[ ... ]` array notation (key is an ellipsis) is not a line reference, skip
                    tables.add(m.group(1))             # record the English table name (primary-key/field pair is irrelevant to impact set)
                for m in PROTO_IMPORT_RE.finditer(line):
                    imports.add(os.path.basename(m.group(1)))
    except Exception:
        pass
    refs -= defs                                       # what this file defines does not count as its own reference
    return {"rule_defs": defs, "rule_refs": refs, "table_refs": tables, "proto_imports": imports}


def xlsx_tables(path):
    """English table names of each sheet of an xlsx (self-describing header row1[0]) -> set. Reuses xlsx_dump (pure stdlib, bypasses openpyxl)."""
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
