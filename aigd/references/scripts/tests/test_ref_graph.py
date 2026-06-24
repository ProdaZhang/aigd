# -*- coding: utf-8 -*-
"""ref_graph / ref_lib tests (pure stdlib runner, not pytest).

Temporary fixtures: lay a few .md/.proto files in a tempdir, run build/dangling/who_refs/file_view, verify:
definition-point vs reference-point heuristic, reverse index, dangling (R/proto major, table advisory), definition-point collision, --check exit code.
No xlsx is created (to avoid openpyxl): table references always take the "no xlsx table -> DANGLING_TABLE advisory" path.
"""
import os, sys, shutil, tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import ref_lib, ref_graph


def _proj(files):
    d = tempfile.mkdtemp(prefix="refg_")
    for rel, content in files.items():
        fp = os.path.join(d, rel)
        os.makedirs(os.path.dirname(fp), exist_ok=True)
        with open(fp, "w", encoding="utf-8") as f:
            f.write(content)
    return d


# ---------- ref_lib unit ----------

def test_rule_defs_in_line():
    assert ref_lib.rule_defs_in_line("### R-A-01 equipment gain") == {"R-A-01"}
    assert ref_lib.rule_defs_in_line("| R-A-02 | bag position |") == {"R-A-02"}
    assert ref_lib.rule_defs_in_line("- **R-A-03**: omitted") == {"R-A-03"}
    assert ref_lib.rule_defs_in_line("value see R-B-99 TBD") == set()    # mid-prose reference, not a definition
    assert ref_lib.rule_defs_in_line("Scenario: conforms to R-A-01") == set()
    # a heading line names its R subsystem: a mid-line R-code also counts as a definition
    assert ref_lib.rule_defs_in_line("## I. Crafting -- R-POT-CRAFT") == {"R-POT-CRAFT"}
    # wildcard/generic notations count as neither a definition nor a reference
    assert ref_lib.rule_defs_in_line("> each one tagged R-POT-* code") == set()
    assert list(ref_lib._codes_in("tagged R-POT-* and R-A-01")) == ["R-A-01"]


def test_scan_text_roles():
    d = _proj({"rules.md":
               "### R-A-01 equipment gain main attribute\n"
               "main attribute see Foo[3].hp and Foo[5]\n"
               "value spec see R-B-99 (TBD)\n"})
    try:
        sc = ref_lib.scan_text(os.path.join(d, "rules.md"))
        assert sc["rule_defs"] == {"R-A-01"}
        assert sc["rule_refs"] == {"R-B-99"}            # the defined R-A-01 is not a self-reference
        assert sc["table_refs"] == {"Foo"}
        assert sc["proto_imports"] == set()
    finally:
        shutil.rmtree(d, ignore_errors=True)


# ---------- ref_graph integration ----------

def _sample():
    return _proj({
        "rules.md": "### R-A-01 gain\nmain attribute Foo[3].hp\n### R-A-02 bag\nvalue see R-B-99 TBD\n",
        "accept.md": "Scenario A\n  Then conforms to R-A-01\nScenario B\n  Then and satisfies R-A-02\n",
        "team.proto": 'syntax="proto3";\nimport "monster.proto";\n',
        "monster.proto": 'syntax="proto3";\nmessage Monster { int32 id = 1; }\n',
    })


def test_reverse_index():
    d = _sample()
    try:
        g = ref_graph.build(d)
        assert set(g["rule_def"]) == {"R-A-01", "R-A-02"}
        # reverse index: who references R-A-01 -> accept.md (rules.md is the definer, not a reference)
        wr = ref_graph.who_refs(g, "R-A-01")
        assert [os.path.basename(p) for p in wr["defined_in"]] == ["rules.md"]
        assert [os.path.basename(p) for p in wr["referenced_in"]] == ["accept.md"]
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_file_impact_set():
    d = _sample()
    try:
        g = ref_graph.build(d)
        _fwd, defined, back = ref_graph.file_view(g, os.path.join(d, "rules.md"))
        assert defined == {"R-A-01", "R-A-02"}
        backnames = {os.path.basename(f) for f in back}
        assert backnames == {"accept.md"}              # editing rules.md -> accept.md is affected
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_dangling_rule_and_table():
    d = _sample()
    try:
        g = ref_graph.build(d)
        dang = ref_graph.dangling(g)
        kinds = {(x["kind"], x["sym"], x["sev"]) for x in dang}
        assert ("DANGLING_RULE", "R-B-99", "major") in kinds        # referenced an R-code no one defines
        assert ("DANGLING_TABLE", "Foo", "advisory") in kinds       # no xlsx table -> only advisory
        # monster.proto exists -> should not be dangling
        assert not any(x["kind"] == "DANGLING_PROTO" for x in dang)
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_heading_subsystem_def_not_dangling():
    # subsystem code written in a heading, leaf code at line start; referencing the subsystem code should not be judged dangling
    d = _proj({
        "rules.md": "## I. Crafting -- R-M-CRAFT\n- **R-M-CRAFT-01** omitted\n",
        "manifest.md": "C-table block references the R-M-CRAFT subsystem\n",
        "accept.md": "scenario (R-M-CRAFT-01)\n",
    })
    try:
        g = ref_graph.build(d)
        assert {"R-M-CRAFT", "R-M-CRAFT-01"} <= set(g["rule_def"])
        dang = ref_graph.dangling(g)
        assert not any(x["kind"] == "DANGLING_RULE" for x in dang)   # both levels are defined
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_dangling_proto():
    d = _proj({"team.proto": 'import "ghost.proto";\n'})       # no ghost.proto
    try:
        g = ref_graph.build(d)
        dang = ref_graph.dangling(g)
        assert any(x["kind"] == "DANGLING_PROTO" and x["sym"] == "ghost.proto"
                   and x["sev"] == "major" for x in dang)
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_dup_def():
    d = _proj({"a.md": "### R-X-01 first\n", "b.md": "### R-X-01 second (duplicate definition)\n"})
    try:
        g = ref_graph.build(d)
        dang = ref_graph.dangling(g)
        assert any(x["kind"] == "DUP_DEF" and x["sym"] == "R-X-01" for x in dang)
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_check_exit_code():
    # dangling R-code -> --check exit code 1
    d = _sample()
    try:
        assert ref_graph.main([d, "--check"]) == 1
    finally:
        shutil.rmtree(d, ignore_errors=True)
    # clean project -> --check exit code 0
    d2 = _proj({"rules.md": "### R-A-01 gain\n", "accept.md": "Then conforms to R-A-01\n"})
    try:
        assert ref_graph.main([d2, "--check"]) == 0
    finally:
        shutil.rmtree(d2, ignore_errors=True)


def test_out_artifact_marked_generated():
    d = _sample()
    out = os.path.join(d, "refs.md")
    try:
        ref_graph.main([d, "--out", out])
        text = open(out, encoding="utf-8").read()
        assert "DO NOT EDIT" in text and "<- referenced by" in text
        assert "accept.md" in text                     # should appear in rules.md's impact set
    finally:
        shutil.rmtree(d, ignore_errors=True)


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for fn in fns:
        try:
            fn()
            print("PASS", fn.__name__)
        except Exception as e:
            failed += 1
            print("FAIL", fn.__name__, "->", repr(e))
    print("%d/%d passed" % (len(fns) - failed, len(fns)))
    sys.exit(1 if failed else 0)
