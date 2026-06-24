# -*- coding: utf-8 -*-
"""config_check.py tests -- pure stdlib (logic layer uses in-memory fixtures, no xlsx files written; table/field names are illustrative).
Run: python test_config_check.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import config_check as C


# ---------- parse_domain ----------

def test_parse_domain_enum():
    assert C.parse_domain("0/1") == ("enum", {0, 1})
    assert C.parse_domain("50/100/150/200") == ("enum", {50, 100, 150, 200})

def test_parse_domain_range():
    assert C.parse_domain("1~5") == ("range", 1, 5)
    assert C.parse_domain("1~200") == ("range", 1, 200)

def test_parse_domain_unparseable_returns_none():
    # anything with text/ellipsis/spec is not parsed, to avoid false positives
    for s in ["per-ten-thousand", "—", "cumulative value", "0/1, default 0", "Grade 1A/2B/3C/4S",
              "0 random/int designated slot", "0/5/10/.../100", "0 and up", ""]:
        assert C.parse_domain(s) is None, s


# ---------- parse_xlsx_sheet (in-memory rows) ----------

def _rows(*rows):
    return [list(r) for r in rows]

def test_xlsx_table_name_from_row1():
    sh = C.parse_xlsx_sheet(_rows(
        ["unit", "", "", ""],
        ["int", "int", "int", "int"],
        ["id", "name", "rarity", "convert"],
        ["id", "name", "rarity", "convert"],
        ["1001", "1", "2", "5001"],
    ))
    assert sh["table"] == "unit"
    assert set(sh["fields"]) == {"id", "name", "rarity", "convert"}

def test_xlsx_array_field_collapsed():
    # skill[ ] spans 4 columns -> collapses into the logical field skill
    sh = C.parse_xlsx_sheet(_rows(
        ["unit", "", "", "", "", ""],
        ["int", "int", "int", "int", "int", "int"],
        ["id", "skill[", "", "", "]", "model"],
        ["id", "skill", "", "", "", "model"],
        ["1001", "1", "2", "3", "4", "9"],
    ))
    assert set(sh["fields"]) == {"id", "skill", "model"}
    assert sh["fields"]["skill"]["is_array"] is True

def test_xlsx_object_array_collapsed():
    # object array field.sub[{id,min,max}...max}] closes at the column containing ] -> collapses into one logical field, later columns not swallowed
    sh = C.parse_xlsx_sheet(_rows(
        ["gear", "", "", "", "", ""],
        ["int", "int", "int64", "int64", "int", "int64"],
        ["id", "stat.roll[{id", "min", "max}]", "groupId", "bonus"],
        ["id", "stat", "", "", "group", "bonus"],
        ["1", "11", "5", "9", "3", "100"],
    ))
    assert set(sh["fields"]) == {"id", "stat.roll", "groupId", "bonus"}
    assert sh["fields"]["stat.roll"]["is_array"] is True   # later groupId/bonus not swallowed

def test_diff_skips_type_for_array():
    doc = {"T": {"fields": {"m": {"type": "mixed", "is_array": True, "value": "—", "range": "—", "ref": "—"}}}}
    xl = {"T": _xf({"m": ("int", None)})}        # xlsx array column, single type int
    assert not any(f["kind"] == "TYPE" for f in C.diff(doc, xl))   # arrays do not compare type

def test_xlsx_merge_artifact_none_skipped():
    # name merged cell -> 2nd column field name empty, should not produce a phantom field
    sh = C.parse_xlsx_sheet(_rows(
        ["unit", "", ""],
        ["int", "", "int"],
        ["name", "", "rarity"],
        ["name", "name", "rarity"],
        ["1", "", "2"],
    ))
    assert set(sh["fields"]) == {"name", "rarity"}

def test_xlsx_scalar_domain_collected():
    sh = C.parse_xlsx_sheet(_rows(
        ["starTable", ""],
        ["int", "int"],
        ["id", "skillPoint"],
        ["row id", "skill point"],
        ["1", "2"], ["2", "3"], ["3", "40"], ["4", ""],  # empty skipped
    ))
    assert sh["fields"]["skillPoint"]["vals"] == [2, 3, 40]


# ---------- parse_config_md ----------

_MD = """# Example config-spec

## Config table overview

| Sheet | Table | Primary key | Purpose | Status |
|---|---|---|---|---|
| unit | `unit` | id | x | [defined] |

## 1. `unit` unit list (primary key id)

| Field | Type | Values/Enum | Range/Default | Ref | Notes |
|------|------|----------|----------|------|------|
| id | int | — | 1xxxxx | — | id |
| rarity | int | Rarity | 1~5 | `enum-dict.Rarity` | rarity |
| skill[1..4] | int[] | — | 4 columns | skill-table | skill |

## 2. `starTable` star-up (primary key star)  [defined]

| Field | Type | Values | Range | Ref | Notes |
|------|------|------|------|------|------|
| id | int | — | — | — | id |
| skillPoint | int | 0/1 | — | — | whether to grant points |
"""

def test_config_md_tables_and_fields():
    doc = C.parse_config_md(_MD)
    assert set(doc) == {"unit", "starTable"}          # overview is not a table; only backtick-titled sections are taken
    assert set(doc["unit"]["fields"]) == {"id", "rarity", "skill"}  # array collapsed
    assert doc["unit"]["fields"]["rarity"]["range"] == "1~5"
    assert doc["starTable"]["fields"]["skillPoint"]["value"] == "0/1"


# ---------- diff ----------

def _docf(**types):
    return {"fields": {n: {"type": t, "value": "—", "range": "—", "ref": "—", "is_array": False}
                       for n, t in types.items()}}

def _xf(fields):
    # fields: {name: (type, vals_or_None)}
    out = {}
    for n, (t, vals) in fields.items():
        out[n] = {"type": t, "is_array": vals is None, "vals": (vals or [])}
    return {"table": "T", "fields": out}

def test_diff_undocumented_column():
    doc = {"T": _docf(id="int", name="int")}
    xl = {"T": _xf({"id": ("int", []), "name": ("int", []), "evolveTarget": ("int", [])})}
    fs = C.diff(doc, xl)
    assert any(f["kind"] == "UNDOC_COL" and f["field"] == "evolveTarget" for f in fs)
    assert all(f["sev"] == "major" for f in fs if f["kind"] == "UNDOC_COL")

def test_diff_missing_column():
    doc = {"T": _docf(id="int", convert="int")}
    xl = {"T": _xf({"id": ("int", [])})}
    fs = C.diff(doc, xl)
    assert any(f["kind"] == "MISSING_COL" and f["field"] == "convert" for f in fs)

def test_diff_type_mismatch():
    doc = {"T": _docf(id="int")}
    xl = {"T": _xf({"id": ("string", [])})}
    fs = C.diff(doc, xl)
    assert any(f["kind"] == "TYPE" and f["field"] == "id" for f in fs)

def test_diff_table_rename_then_field_diff():
    # doc table name slot, xlsx table name unitSlot (contains slot) -> RENAME; and extra column max -> UNDOC_COL
    doc = {"slot": _docf(id="int", condition="int", para="int")}
    xl = {"unitSlot": _xf({"id": ("int", []), "condition": ("int", []),
                           "para": ("int", []), "max": ("int", [])})}
    fs = C.diff(doc, xl)
    assert any(f["kind"] == "RENAME" for f in fs)
    assert any(f["kind"] == "UNDOC_COL" and f["field"] == "max" for f in fs)

def test_diff_domain_enum_violation():
    doc = {"T": {"fields": {"skillPoint": {"type": "int", "value": "0/1", "range": "—",
                                           "ref": "—", "is_array": False}}}}
    xl = {"T": _xf({"skillPoint": ("int", [0, 1, 2, 40])})}
    fs = C.diff(doc, xl)
    d = [f for f in fs if f["kind"] == "DOMAIN" and f["field"] == "skillPoint"]
    assert d and d[0]["sev"] == "advisory"
    assert "2" in d[0]["msg"] or "40" in d[0]["msg"]   # gives an out-of-range sample

def test_diff_domain_range_ok_no_finding():
    doc = {"T": {"fields": {"rarity": {"type": "int", "value": "Rarity", "range": "1~5",
                                       "ref": "—", "is_array": False}}}}
    xl = {"T": _xf({"rarity": ("int", [1, 2, 3, 4, 5])})}
    fs = C.diff(doc, xl)
    assert not any(f["kind"] == "DOMAIN" for f in fs)

def test_diff_domain_unparseable_skipped():
    doc = {"T": {"fields": {"hp": {"type": "int", "value": "per-ten-thousand", "range": "cumulative value",
                                   "ref": "—", "is_array": False}}}}
    xl = {"T": _xf({"hp": ("int", [120, 880, 9999])})}
    fs = C.diff(doc, xl)
    assert not any(f["kind"] == "DOMAIN" for f in fs)

def test_diff_array_field_no_false_positive():
    doc = {"T": {"fields": {"skill": {"type": "int", "value": "—", "range": "—",
                                      "ref": "—", "is_array": True}}}}
    xl = {"T": _xf({"skill": ("int", None)})}   # None vals -> array
    fs = C.diff(doc, xl)
    assert not any(f["kind"] in ("UNDOC_COL", "MISSING_COL") for f in fs)

def test_diff_deterministic():
    doc = {"T": _docf(id="int", name="int")}
    xl = {"T": _xf({"id": ("int", []), "x": ("int", [])})}
    assert C.diff(doc, xl) == C.diff(doc, xl)


if __name__ == "__main__":
    import traceback, inspect, tempfile, pathlib
    fns = [(n, f) for n, f in sorted(globals().items())
           if n.startswith("test_") and callable(f)]
    fails = 0
    for n, f in fns:
        try:
            if "tmp_path" in inspect.signature(f).parameters:
                f(pathlib.Path(tempfile.mkdtemp()))
            else:
                f()
            print("PASS", n)
        except Exception:
            fails += 1
            print("FAIL", n)
            traceback.print_exc()
    print(f"\n{len(fns)-fails}/{len(fns)} passed")
    raise SystemExit(1 if fails else 0)
