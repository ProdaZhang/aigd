# -*- coding: utf-8 -*-
"""config_index.py tests -- pure stdlib. lookup/enums/keymap/column_values use in-memory fixtures (table/field names are illustrative)."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import config_index as CI


def _idx():
    return {
        "levelTable": {"file": "unit.xlsx", "fieldcol": {"id": 0, "key": 1, "value": 2},
                       "data": [["88", "5001", "880"], ["89", "5001", "890"]]},
        "evolveLine": {"file": "unit.xlsx", "fieldcol": {"id": 0, "member": 1},
                       "data": [["1001", "1002"]]},
        "starTable": {"file": "unit.xlsx",
                      "fieldcol": {"id": 0, "rarity": 1, "element": 2, "star": 3, "skillPoint": 4},
                      "data": [["100", "3", "1", "1", "2"]]},
        "unit": {"file": "unit.xlsx", "fieldcol": {"id": 0, "line": 1},
                 "data": [["1101", "1101"], ["1001", "1001"], ["1900", ""]]},
        "__enums__": {"A": "3", "water": "1"},
        "__keymap__": {"starTable": ["rarity", "element", "star"]},
    }


def test_lookup_single_int_key():
    assert CI.lookup(_idx(), "levelTable", "88", "value") == "880"

def test_lookup_dangling_returns_none():
    # 1101 not in evolveLine -> broken link
    assert CI.lookup(_idx(), "evolveLine", "1101", "member") is None

def test_lookup_composite_via_keymap_enums():
    assert CI.lookup(_idx(), "starTable", "A,water,1", "skillPoint") == "2"

def test_lookup_multi_when_enum_unresolved():
    assert CI.lookup(_idx(), "starTable", "A,fire,1", "skillPoint") == "MULTI"   # fire not in enums

def test_lookup_multi_when_no_keymap():
    idx = _idx(); idx["__keymap__"] = {}
    assert CI.lookup(idx, "starTable", "3,1,1", "skillPoint") == "MULTI"

def test_lookup_unknown_table_none():
    assert CI.lookup(_idx(), "nope", "1", "x") is None

def test_row_exists_true_when_row_present():
    assert CI.row_exists(_idx(), "levelTable", "88") is True

def test_row_exists_false_when_row_missing():
    assert CI.row_exists(_idx(), "evolveLine", "1101") is False

def test_row_exists_none_when_multi():
    assert CI.row_exists(_idx(), "starTable", "A,fire,1") is None     # fire unresolved -> MULTI undecidable

def test_column_values_skips_empty():
    assert CI.column_values(_idx(), "unit", "line") == {"1101", "1001"}   # empty skipped

def test_column_values_unknown_none():
    assert CI.column_values(_idx(), "unit", "nope") is None


def test_load_enums_drops_ambiguous(tmp_path):
    md = tmp_path / "e.md"
    md.write_text("| id | name | cn |\n|--|--|--|\n| 1 | A | first |\n| 2 | A | second |\n| 3 | B | third |\n",
                  encoding="utf-8")
    enums = CI.load_enums(str(md))
    assert enums.get("B") == "3"
    assert "A" not in enums          # A maps to both 1/2 -> conflict, dropped
    assert enums.get("first") == "1"

def test_load_keymap_drops_comment(tmp_path):
    j = tmp_path / "k.json"
    j.write_text('{"_note":"x","starTable":["rarity","star"]}', encoding="utf-8")
    km = CI.load_keymap(str(j))
    assert km == {"starTable": ["rarity", "star"]}


def test_array_spans():
    assert CI._array_spans(["id", "member[", "", "", "]"]) == {"member": [1, 2, 3]}
    assert CI._array_spans(["id", "name", None, "lineGroup[", None, None, "]"]) == {"lineGroup": [3, 4, 5]}
    assert CI._array_spans(["id", "x"]) == {}                      # no array
    assert CI._array_spans(["a", "reward.drop[{id", "}", "]"]) == {}  # object array skipped

def test_array_column_values():
    idx = {"g": {"fieldcol": {"id": 0, "member": 1}, "arraycols": {"member": [1, 2, 3]},
                 "data": [["1001", "1001", "1002", "1003"], ["1101", "1101", "", ""]]}}
    assert CI.array_column_values(idx, "g", "member") == {"1001", "1002", "1003", "1101"}
    assert CI.array_column_values(idx, "g", "nope") is None
    assert CI.array_column_values(idx, "no", "member") is None


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
