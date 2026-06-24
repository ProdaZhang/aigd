# -*- coding: utf-8 -*-
"""Config-table index + `Table[primary key].field` resolution (pure stdlib, reuses xlsx_dump).

A shared layer extracted from gherkin_to_checklist.py, shared by gherkin_to_checklist
(planner-version checklist value substitution) and config_check / value_check
(validation), to avoid duplication and to keep openpyxl out of the validators.

- build_index(dir): scan all sheets of all xlsx in a directory -> {English table name: {file, fieldcol, data}}.
- load_enums(enum-dictionary.md): {enum name/Chinese: id}; conflicting names dropped (to prevent wrong substitution).
- load_keymap(composite-key-map.json): {composite-key table: [component column names...]}.
- lookup(idx, table, keystr, field): real value / 'MULTI' (multi-key enum needs manual fill) / None (not found = broken link).
  Guardrails: single numeric primary key looked up directly against id/col0; composite key matched by keymap component columns; enum names resolved via enums; never fabricated.
"""
import os, re, json, zipfile

import xlsx_dump

REF_RE = re.compile(r"([A-Za-z]\w*)\[([^\]\[]+)\]\.([A-Za-z]\w*)")   # Table[primary key].field


def _array_spans(field_row):
    """Simple list array (`field[ ... ]`) -> {base: [data column indices]}. Object arrays (`[{...}]`) are skipped."""
    spans = {}
    base, cols = None, []
    for ci in range(len(field_row)):
        k = (field_row[ci] or "").strip() if field_row[ci] is not None else ""
        if base is not None:
            if "]" in k and "{" not in k:          # closing-marker column (no data)
                spans[base] = cols; base, cols = None, []
                continue
            if k == "":
                cols.append(ci); continue
            spans[base] = cols; base, cols = None, []   # hit a new field early -> wrap up (trailing array)
        if "[" in k and "{" not in k:
            b = re.split(r"[\[.]", k)[0].strip()
            if b:
                base, cols = b, [ci]
                if "]" in k:                        # self-closing
                    spans[b] = cols; base, cols = None, []
    if base is not None:
        spans[base] = cols
    return spans


def build_index(config_dir):
    """Scan all sheets of all xlsx in the config directory, build English table name -> {file, fieldcol, arraycols, data}.
    Self-describing header: row1=table name, row3=field key (array field[ also registered under its bare name), row5+=data."""
    idx = {}
    for fn in sorted(os.listdir(config_dir)):
        if not fn.lower().endswith(".xlsx") or fn.startswith("~$"):
            continue
        path = os.path.join(config_dir, fn)
        try:
            z = zipfile.ZipFile(path)
            shared = xlsx_dump.load_shared_strings(z)
            for name, sp in xlsx_dump.sheet_map(z):
                rows = xlsx_dump.read_rows(z, sp, shared, None)
                if len(rows) < 5:
                    continue
                table = (rows[0][0] or "").strip()
                if not table or not re.match(r"^[A-Za-z]\w*$", table):
                    continue
                fieldcol = {}
                for ci, k in enumerate(rows[2]):
                    k = (k or "").strip()
                    if not k:
                        continue
                    if k not in fieldcol:
                        fieldcol[k] = ci
                    base = re.split(r"[\[.]", k)[0]    # array/object field member[ / jump.x -> register the bare name too
                    if base and base not in fieldcol:
                        fieldcol[base] = ci
                idx[table] = {"file": fn, "fieldcol": fieldcol,
                              "arraycols": _array_spans(rows[2]), "data": rows[4:]}
            z.close()
        except Exception:
            continue
    return idx


def load_enums(path):
    """Parse the markdown table of enum-dictionary.md -> {enum name/Chinese: id}. Conflicting names dropped (to prevent wrong substitution)."""
    enums, ambig = {}, set()
    with open(path, encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if not s.startswith("|"):
                continue
            cells = [c.strip() for c in s.strip("|").split("|")]
            if len(cells) < 2 or not re.fullmatch(r"\d+", cells[0]):
                continue
            idv = cells[0]
            for nm in cells[1:3]:
                if nm and not re.fullmatch(r"[-:\s]+", nm) and not re.fullmatch(r"\d+", nm):
                    if nm in enums and enums[nm] != idv:
                        ambig.add(nm)
                    else:
                        enums.setdefault(nm, idv)
    for a in ambig:
        enums.pop(a, None)
    return enums


def load_keymap(path):
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    return {k: v for k, v in d.items() if not k.startswith("_")}   # drop comment keys


def _cell(row, fc):
    if fc < len(row):
        v = str(row[fc]).strip()
        return v if v != "" else None
    return None


def _resolve_key(k, enums):
    """key -> id string used to match the column (numbers as-is; enum name->id; None if unresolvable)."""
    if re.fullmatch(r"-?\d+", k):
        return k
    return enums.get(k)


def _find_row(idx, table, keystr):
    """Match a row by primary key -> row / 'MULTI' (multi-key enum needs manual fill) / None (no such row). Composite key matched by component columns."""
    t = idx.get(table)
    if not t:
        return None
    enums = idx.get("__enums__", {}) or {}
    keymap = idx.get("__keymap__", {}) or {}
    keys = [k.strip() for k in keystr.split(",")]
    if len(keys) == 1 and re.fullmatch(r"-?\d+", keys[0]):
        k = keys[0]
        keycols = ([t["fieldcol"]["id"]] if "id" in t["fieldcol"] else []) + [0]
        for row in t["data"]:
            if any(kc < len(row) and str(row[kc]).strip() == k for kc in keycols):
                return row
        return None
    cols = keymap.get(table)
    if not cols or len(cols) != len(keys):
        return "MULTI"
    colidx = []
    for ck in cols:
        ci = t["fieldcol"].get(ck)
        if ci is None:
            return None
        colidx.append(ci)
    resolved = []
    for k in keys:
        rk = _resolve_key(k, enums)
        if rk is None:
            return "MULTI"
        resolved.append(rk)
    for row in t["data"]:
        if all(ci < len(row) and str(row[ci]).strip() == resolved[j] for j, ci in enumerate(colidx)):
            return row
    return None


def lookup(idx, table, keystr, field):
    """Real value string / 'MULTI' (needs manual fill) / None (not found = broken link, or field empty). Composite key matched across multiple component columns."""
    row = _find_row(idx, table, keystr)
    if row == "MULTI":
        return "MULTI"
    if row is None:
        return None
    fc = idx[table]["fieldcol"].get(field)
    return _cell(row, fc) if fc is not None else None


def row_exists(idx, table, keystr):
    """Whether the primary key matches a row (ignores the field value). True / False / None (MULTI undecidable, or table not present).
    Used to distinguish 'dangling reference (row does not exist)' from 'field value empty (optional field)', so empty values are not misreported as broken links."""
    row = _find_row(idx, table, keystr)
    if row == "MULTI" or (row is None and table not in idx):
        return None
    return row is not None


def column_values(idx, table, field):
    """All non-empty values of a table column (set of strings). Used for foreign-key validation (target column value domain)."""
    t = idx.get(table)
    if not t:
        return None
    fc = t["fieldcol"].get(field)
    if fc is None:
        return None
    out = set()
    for row in t["data"]:
        v = _cell(row, fc)
        if v is not None:
            out.add(v)
    return out


def array_column_values(idx, table, base):
    """All member values (non-empty) of an array field (`base[ ... ]`) across all rows. None = table/array column does not exist.
    Used for per-member foreign-key validation (e.g. each id in evolveLine.member[] in unit.id)."""
    t = idx.get(table)
    if not t:
        return None
    cols = t.get("arraycols", {}).get(base)
    if not cols:
        return None
    out = set()
    for row in t["data"]:
        for c in cols:
            v = _cell(row, c)
            if v is not None:
                out.add(v)
    return out
