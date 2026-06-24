# -*- coding: utf-8 -*-
"""Tool 4 - config_check -- config-spec.md <-> xlsx schema drift validator (pure stdlib).

Why it exists: the methodology puts "values" in xlsx and "schema/rules" in docs (config-spec.md references xlsx by field name).
Changing values needs no doc edit -- but changing the **structure** (adding a column / changing a field domain / renaming a sheet) changes the schema the doc owns,
yet does it in the xlsx, so the two silently go out of sync. The "validation checklist" at the end of config-spec.md writes the right checks, but it is an
unchecked box, rubber-stamped with a self-assessed checkmark. This script turns the schema part of that checklist into a deterministic machine check.

What it catches (high confidence):
  UNDOC_COL     xlsx has a column the config-spec does not record -- the typical trace of editing xlsx later without writing back to the doc
  MISSING_COL   config-spec declares a field, xlsx has no such column
  TYPE          same-named field, doc type != xlsx type
  RENAME        the doc table name has no same-named sheet; the closest one is a suspected rename
  MISSING_TABLE the doc declares a table, xlsx has no sheet
What it catches (advisory, needs human judgment):
  DOMAIN        the field's declared domain (parseable ones like 0/1, 1~5) does not match actual data; gives an out-of-range sample, human judges true/false

What it does not catch (left to the value-integrity tool, done separately): cross-table foreign-key resolution / acceptance-case literal-value reconciliation / *Percentage monotonicity.

xlsx reading reuses xlsx_dump (zipfile+ElementTree, bypassing openpyxl's style errors on domestic table-export xlsx).
No project hard-coding, all paths come from argv.

Usage:
  python config_check.py <config-spec.md> <config.xlsx>
  Exit code: any major/MISSING_TABLE -> 1, otherwise 0 (advisory/info do not cause failure).
"""
import sys, os, re, zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import xlsx_dump as X


# ---------------------------------------------------------------- domain parsing
def parse_domain(s):
    """Parse a declared domain into ('enum', {..}) / ('range', lo, hi) / None.
    Strictly anchored: only recognizes pure-integer slash enums and a~b ranges; anything with text/ellipsis/spec is None (to avoid false positives)."""
    s = (s or "").strip()
    if not s:
        return None
    m = re.match(r"^(\d+)\s*~\s*(\d+)$", s)
    if m:
        return ("range", int(m.group(1)), int(m.group(2)))
    if re.match(r"^\d+(/\d+)+$", s):
        return ("enum", set(int(x) for x in s.split("/")))
    return None


def _domain_violations(dom, vals):
    if dom[0] == "enum":
        return [v for v in vals if v not in dom[1]]
    if dom[0] == "range":
        lo, hi = dom[1], dom[2]
        return [v for v in vals if not (lo <= v <= hi)]
    return []


# ---------------------------------------------------------------- xlsx parsing
def _cell(row, i):
    return row[i] if i < len(row) else ""


def parse_xlsx_sheet(rows):
    """rows: list of rows (strings). Self-describing header: row1=table name, row2=type, row3=field key (array field[...]), row4=Chinese, row5+=data.
    Returns {table, fields:{name:{type,is_array,vals}}}. Array columns collapse into one logical field; empty (merged) columns are skipped;
    scalar fields collect a deduplicated int data domain (string columns -> vals=[])."""
    type_row = rows[1] if len(rows) > 1 else []
    field_row = rows[2] if len(rows) > 2 else []
    data_rows = rows[4:] if len(rows) > 4 else []

    table = ""
    for v in (rows[0] if rows else []):
        if v is not None and str(v).strip():
            table = str(v).strip()
            break

    fields = {}   # name -> {type, is_array, col, vals}
    ncol = max(len(type_row), len(field_row))
    in_array = False
    cur = None
    for i in range(ncol):
        raw = _cell(field_row, i)
        nm = str(raw).strip() if raw is not None else ""
        if in_array:
            if "]" in nm:          # close: simple array `]` or object array `max}]`
                in_array, cur = False, None
            continue
        if not nm:
            continue                       # merged/empty column
        t = str(_cell(type_row, i) or "").strip().replace("[]", "")
        if "[" in nm:
            base = nm.split("[")[0].strip()
            if base:
                fields[base] = {"type": t, "is_array": True, "col": i, "vals": []}
            if "]" not in nm:
                in_array, cur = True, base
        else:
            fields[nm] = {"type": t, "is_array": False, "col": i, "vals": []}

    CAP = 500
    for f in fields.values():
        if f["is_array"]:
            continue
        ci, seen = f["col"], set()
        ok = True
        for dr in data_rows:
            v = _cell(dr, ci)
            if v is None or str(v).strip() == "":
                continue
            try:
                seen.add(int(float(str(v).strip())))
            except ValueError:
                ok = False
                break                       # non-int (string column) -> no domain check
            if len(seen) > CAP:
                break
        f["vals"] = sorted(seen) if ok else []

    return {"table": table,
            "fields": {n: {"type": f["type"], "is_array": f["is_array"], "vals": f["vals"]}
                       for n, f in fields.items()}}


def read_xlsx(path):
    z = zipfile.ZipFile(path)
    shared = X.load_shared_strings(z)
    out = {}
    for name, sp in X.sheet_map(z):
        sh = parse_xlsx_sheet(X.read_rows(z, sp, shared, None))
        if sh["table"]:
            out[sh["table"]] = sh
    z.close()
    return out


# ---------------------------------------------------------------- config-spec.md parsing
def parse_config_md(text):
    """A backtick table name `## section` + its following field table -> {code:{fields:{name:{type,value,range,ref,is_array}}}}.
    Field-table columns are located by header name (Field/Type/Values/Range/Ref), tolerant of column order and missing columns; array field names are collapsed."""
    tables = {}
    lines = text.splitlines()
    code = None
    i, n = 0, len(lines)
    while i < n:
        st = lines[i].strip()
        if st.startswith("#"):
            m = re.search(r"`([^`]+)`", st)
            code = m.group(1).strip() if m else None
            i += 1
            continue
        if code and st.startswith("|") and "Field" in st:
            header = [c.strip() for c in st.strip("|").split("|")]
            idx = {}
            for key in ("Field", "Type", "Values", "Range", "Ref"):
                idx[key] = next((j for j, h in enumerate(header) if key in h), None)
            i += 1
            if i < n and set(lines[i].strip()) <= set("|-: "):   # separator row
                i += 1
            fields = {}
            while i < n and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]

                def cg(key, _cells=cells):
                    j = idx[key]
                    return _cells[j] if (j is not None and j < len(_cells)) else "—"

                raw = cg("Field")
                base = raw.split("[")[0].strip()
                if base and base != "Field":
                    typ = cg("Type")
                    fields[base] = {"type": typ.replace("[]", "").strip(),
                                    "value": cg("Values"), "range": cg("Range"),
                                    "ref": cg("Ref"),
                                    "is_array": ("[" in raw or typ.strip().endswith("[]"))}
                i += 1
            if fields:
                tables.setdefault(code, {"fields": {}})["fields"].update(fields)
            continue
        i += 1
    return tables


# ---------------------------------------------------------------- diff
def diff(doc, xlsx):
    findings = []
    used = set()
    for code in sorted(doc):
        dfields = doc[code]["fields"]
        xname = None
        if code in xlsx:
            xname = code
        else:
            cands = [t for t in xlsx if (code.lower() in t.lower() or t.lower() in code.lower())]
            if len(cands) == 1:
                xname = cands[0]
                findings.append({"sev": "major", "kind": "RENAME", "table": code, "field": None,
                                 "msg": "doc table name '%s' has no same-named sheet; closest is '%s' (suspected rename, needs sync)" % (code, xname)})
        if xname is None:
            findings.append({"sev": "major", "kind": "MISSING_TABLE", "table": code, "field": None,
                             "msg": "doc declares table '%s', xlsx has no matching sheet" % code})
            continue
        used.add(xname)
        xfields = xlsx[xname]["fields"]

        for fn in sorted(dfields):
            if fn not in xfields:
                findings.append({"sev": "major", "kind": "MISSING_COL", "table": code, "field": fn,
                                 "msg": "doc declares field '%s.%s', xlsx has no such column" % (code, fn)})
        for fn in sorted(xfields):
            if fn not in dfields:
                findings.append({"sev": "major", "kind": "UNDOC_COL", "table": code, "field": fn,
                                 "msg": "xlsx '%s' has column '%s', not recorded in config-spec (suspected xlsx edited later without writing back to doc)" % (xname, fn)})
        for fn in sorted(dfields):
            if fn not in xfields:
                continue
            dt, xt = dfields[fn]["type"], xfields[fn]["type"]
            # array/object array (mixed subtypes) has no single scalar type to compare, skip the TYPE check
            if not (dfields[fn].get("is_array") or xfields[fn].get("is_array")) and dt and xt and dt != xt:
                findings.append({"sev": "major", "kind": "TYPE", "table": code, "field": fn,
                                 "msg": "field '%s.%s' type mismatch: doc=%s xlsx=%s" % (code, fn, dt, xt)})
            if not xfields[fn]["is_array"]:
                dv, dr = dfields[fn].get("value", ""), dfields[fn].get("range", "")
                dom = parse_domain(dv) or parse_domain(dr)
                vals = xfields[fn].get("vals") or []
                if dom and vals:
                    bad = _domain_violations(dom, vals)
                    if bad:
                        decl = dv if parse_domain(dv) else dr
                        more = " ...%d in total" % len(bad) if len(bad) > 5 else ""
                        findings.append({"sev": "advisory", "kind": "DOMAIN", "table": code, "field": fn,
                                         "msg": "field '%s.%s' declared domain '%s', actual out-of-range samples: %s%s" % (
                                             code, fn, decl, ",".join(str(b) for b in bad[:5]), more)})

    for t in sorted(xlsx):
        if t not in used:
            findings.append({"sev": "info", "kind": "UNDOC_TABLE", "table": t, "field": None,
                             "msg": "xlsx sheet '%s' has no matching table section in config-spec" % t})
    return findings


def check(md_path, xlsx_path):
    with open(md_path, encoding="utf-8") as f:
        doc = parse_config_md(f.read())
    return diff(doc, read_xlsx(xlsx_path))


# ---------------------------------------------------------------- report / main
_SEV_ORDER = {"major": 0, "advisory": 1, "info": 2}


def format_report(findings, md_path, xlsx_path):
    out = ["config-spec <-> xlsx schema drift validation",
           "  config-spec: %s" % md_path,
           "  xlsx       : %s" % xlsx_path, ""]
    if not findings:
        out.append("OK no drift: columns / types / table names consistent, parseable domains have no out-of-range values.")
        return "\n".join(out)
    by_tbl = {}
    for f in findings:
        by_tbl.setdefault(f["table"] or "(other)", []).append(f)
    n_major = sum(1 for f in findings if f["sev"] == "major")
    n_adv = sum(1 for f in findings if f["sev"] == "advisory")
    n_info = sum(1 for f in findings if f["sev"] == "info")
    out.append("found %d (major=%d advisory=%d info=%d):" % (len(findings), n_major, n_adv, n_info))
    out.append("")
    tag = {"major": "[major]", "advisory": "[advisory]", "info": "[info]"}
    for tbl in sorted(by_tbl):
        out.append("* %s" % tbl)
        for f in sorted(by_tbl[tbl], key=lambda x: (_SEV_ORDER[x["sev"]], x["kind"], x["field"] or "")):
            out.append("    %-10s %-13s %s" % (tag[f["sev"]], f["kind"], f["msg"]))
        out.append("")
    out.append("major must be fixed by writing back to doc / editing xlsx, then re-run; advisory needs human judgment on whether the declared domain is just shorthand.")
    return "\n".join(out)


def main(argv):
    if len(argv) < 3:
        sys.stderr.write("usage: python config_check.py <config-spec.md> <config.xlsx>\n")
        return 2
    md, xl = argv[1], argv[2]
    findings = check(md, xl)
    sys.stdout.buffer.write((format_report(findings, md, xl) + "\n").encode("utf-8"))
    return 1 if any(f["sev"] == "major" for f in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
