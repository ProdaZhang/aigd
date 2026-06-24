# -*- coding: utf-8 -*-
"""manifest_check.py tests -- pure stdlib (logic layer uses in-memory markdown-string fixtures).
Run: python test_manifest_check.py
The real pilot-manifest integration test skips gracefully when the file is missing.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import manifest_check as M


def _kinds(findings):
    return [f["kind"] for f in findings]


# ---------- markdown table parsing ----------

def test_parse_md_tables_basic():
    txt = "preamble\n\n| a | b |\n|---|---|\n| 1 | 2 |\n| 3 | 4 |\n\ntail\n"
    ts = M.parse_md_tables(txt)
    assert len(ts) == 1
    assert ts[0]["header"] == ["a", "b"]
    assert ts[0]["rows"] == [["1", "2"], ["3", "4"]]

def test_split_row_unescapes_pipe():
    # an escaped \| inside content should not split columns
    assert M._split_row(r"| x = a\|b | y |") == ["x = a|b", "y"]

def test_norm_status_strips_star_and_emphasis():
    assert M._norm_status("Final*") == "Final"
    assert M._norm_status("**Playtesting**") == "Playtesting"
    assert M._norm_status("`Draft`") == "Draft"


# ---------- C-table blocks ----------

def test_parse_c_blocks():
    txt = "## C. Cross-layer index\n\n### S01 item\n- proto: x\n- acceptance: y\n\n### S02 hero\n- rule\n\n## D. Other\n"
    b = M.parse_c_blocks(txt)
    assert set(b) == {"S01", "S02"}
    assert "proto" in b["S01"]["body"]
    assert "acceptance" not in b["S02"]["body"]


# ---------- full manifest: clean sample, 0 major ----------

_CLEAN = """# manifest
## status enum
`Draft` -> `Playtesting` -> `Final` -> `Recheck`.

## A. System list + dependency graph
| SystemID | Name | area-sub-system dir | Status | R-ModuleCode | Deps (upstream) | Dependents (downstream) |
|--------|--------|----------------|------|----------|-----------|-------------|
| S01 | item | 05-01-02 | Final* | R-ITEM | (no upstream; mail [external]) | broadcast (see F) |
| S02 | equip | 02-02-01 | Draft | R-EQUIP | item[broadcast](decompose item) | combat [external] |

## B. Range
| ModuleCode | System | protocol Range | error code segment | notes |
|--------|------|----------|----------|------|
| R-ITEM | item | 1400-1499 | 14000- | x |
| R-EQUIP | equip | 1200-1299 | 12000- | x |

## C. Cross-layer index
### S01 item
- **contract (proto)**: proto/item.proto
- **acceptance**: item-acceptance.md
### S02 equip
- **rule (-01)**: docs/equip/rules.md

## D. Freeze ledger
| System | Status | Final time | occupied Range | Recheck trigger |
|------|------|----------|----------|------------|
| S01 item | Final* | 2026-06-17 | 1400- | ledgered |

## E. Rollback record
| time | System | FromStatus -> ToStatus | reason | affected downstream |
|------|------|-----------------|------|------------|
| 2026-06-17 | S01 | Final* -> Playtesting | x | S02 |
"""

def test_clean_manifest_no_major():
    fs = M.check_text(_CLEAN)
    majors = [f for f in fs if f["sev"] == "major"]
    assert not majors, "clean manifest should have no major: %r" % majors

def test_clean_dep_by_name_info():
    # equip's Deps column says "item" (by name), should produce a DEP_BY_NAME info
    assert "DEP_BY_NAME" in _kinds(M.check_text(_CLEAN))


# ---------- each major is catchable ----------

def test_seg_missing():
    # A-table S02 ModuleCode R-GHOST, B table does not register it
    txt = _CLEAN.replace("| S02 | equip | 02-02-01 | Draft | R-EQUIP |", "| S02 | equip | 02-02-01 | Draft | R-GHOST |")
    fs = M.check_text(txt)
    assert any(f["kind"] == "SEG_MISSING" and f["sev"] == "major" for f in fs)

def test_dangling_dep_explicit_id():
    # explicit dependency S99 does not exist
    txt = _CLEAN.replace("| item[broadcast](decompose item) |", "| S99(missing),item |")
    fs = M.check_text(txt)
    assert any(f["kind"] == "DANGLING_DEP" and "S99" in f["msg"] for f in fs)

def test_multi_code_both_registered_ok():
    # one system with two codes R-EQUIP / R-AUTO, both registered in B table -> no SEG_MISSING
    txt = _CLEAN.replace("| S02 | equip | 02-02-01 | Draft | R-EQUIP |",
                         "| S02 | equip | 02-02-01 | Draft | R-EQUIP / R-AUTO |")
    txt = txt.replace("| R-EQUIP | equip | 1200-1299 | 12000- | x |",
                      "| R-EQUIP | equip | 1200-1299 | 12000- | x |\n| R-AUTO | equip | 1300- | 13000- | x |")
    assert not any(f["kind"] == "SEG_MISSING" for f in M.check_text(txt))

def test_multi_code_one_missing_flagged():
    # two codes but R-AUTO not registered in B table -> only R-AUTO reports SEG_MISSING
    txt = _CLEAN.replace("| S02 | equip | 02-02-01 | Draft | R-EQUIP |",
                         "| S02 | equip | 02-02-01 | Draft | R-EQUIP / R-AUTO |")
    seg = [f for f in M.check_text(txt) if f["kind"] == "SEG_MISSING"]
    assert len(seg) == 1 and "R-AUTO" in seg[0]["msg"]

def test_placeholder_status_rows_ok():
    # D/E table placeholder rows (— / empty, "none") should not falsely report BAD_STATUS
    txt = _CLEAN + ("\n## E. Rollback record\n| time | System | FromStatus -> ToStatus | reason | affected downstream |\n"
                    "|--|--|--|--|--|\n| — | — | — | — | — |\n")
    assert not any(f["kind"] == "BAD_STATUS" for f in M.check_text(txt))

def test_bad_status():
    txt = _CLEAN.replace("| S02 | equip | 02-02-01 | Draft |", "| S02 | equip | 02-02-01 | LiveNow |")
    fs = M.check_text(txt)
    assert any(f["kind"] == "BAD_STATUS" and f["sev"] == "major" for f in fs)

def test_no_cblock():
    # remove S02's C block
    txt = _CLEAN.replace("### S02 equip\n- **rule (-01)**: docs/equip/rules.md\n", "")
    fs = M.check_text(txt)
    assert any(f["kind"] == "NO_CBLOCK" and "S02" in f["msg"] for f in fs)

def test_cycle_detected():
    # make S01 also depend on equip -> item<->equip forms a cycle
    txt = _CLEAN.replace("| (no upstream; mail [external]) |", "| equip(reverse dependency) |")
    fs = M.check_text(txt)
    assert any(f["kind"] == "CYCLE" and f["sev"] == "advisory" for f in fs)

def test_names_in_text_substring_guard():
    # "main" is a substring of "main quest": text mentions only main quest, should not match main
    assert M._names_in_text("auto-complete main quest", {"main", "main quest"}) == {"main quest"}
    # if both appear independently, both match
    assert M._names_in_text("main level + main quest chain", {"main", "main quest"}) == {"main", "main quest"}

def test_no_self_cycle_from_own_name():
    # S01's Deps column containing its own name "item" should not form a self-cycle major/CYCLE
    txt = _CLEAN.replace("| (no upstream; mail [external]) |", "| item internal warehouse flow |")
    fs = M.check_text(txt)
    assert not any(f["kind"] == "CYCLE" for f in fs)

def test_defined_no_contract():
    # S01 Final* but its C block has proto + acceptance stripped out
    txt = _CLEAN.replace("- **contract (proto)**: proto/item.proto\n- **acceptance**: item-acceptance.md", "- **rule**: x")
    fs = M.check_text(txt)
    assert any(f["kind"] == "DEFINED_NO_CONTRACT" for f in fs)

def test_seg_unused():
    # B table registers an extra code no one uses
    txt = _CLEAN.replace("| R-EQUIP | equip | 1200-1299 | 12000- | x |",
                         "| R-EQUIP | equip | 1200-1299 | 12000- | x |\n| R-ORPHAN | ghost | 9000- | 90000- | x |")
    fs = M.check_text(txt)
    assert any(f["kind"] == "SEG_UNUSED" and "R-ORPHAN" in f["msg"] for f in fs)

def test_cblock_orphan():
    txt = _CLEAN + "\n### S77 ghost system\n- leftover index\n"
    fs = M.check_text(txt)
    assert any(f["kind"] == "CBLOCK_ORPHAN" and "S77" in f["msg"] for f in fs)

def test_no_a_table():
    fs = M.check_text("# not a manifest\n\n| x | y |\n|---|---|\n| 1 | 2 |\n")
    assert any(f["kind"] == "NO_A_TABLE" for f in fs)

def test_deterministic():
    assert M.check_text(_CLEAN) == M.check_text(_CLEAN)


# ---------- integration: real pilot manifest (skip if file missing) ----------

def test_integration_pilot_no_major():
    here = os.path.dirname(__file__)
    root = os.path.abspath(os.path.join(here, "..", "..", "..", "..", "..", ".."))
    path = os.path.join(root, ".uploads", "aigd-pilot", "manifest.md")
    if not os.path.exists(path):
        print("  (skip integration: missing pilot manifest)"); return
    majors = [f for f in M.check(path) if f["sev"] == "major"]
    assert not majors, "pilot manifest should have no major: %r" % majors


if __name__ == "__main__":
    import traceback
    fns = [(n, f) for n, f in sorted(globals().items())
           if n.startswith("test_") and callable(f)]
    fails = 0
    for n, f in fns:
        try:
            f()
            print("PASS", n)
        except Exception:
            fails += 1
            print("FAIL", n)
            traceback.print_exc()
    print(f"\n{len(fns)-fails}/{len(fns)} passed")
    raise SystemExit(1 if fails else 0)
