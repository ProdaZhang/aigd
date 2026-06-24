# -*- coding: utf-8 -*-
"""ref_graph / ref_lib 测试(纯 stdlib runner,非 pytest)。

临时夹具:在 tempdir 里铺几份 .md/.proto,跑 build/dangling/who_refs/file_view,验:
定义点 vs 引用点启发式、反向索引、悬空(R/proto major、表 advisory)、定义点撞车、--check 退出码。
不造 xlsx(免 openpyxl):表引用一律走"无 xlsx 表 → DANGLING_TABLE advisory"路径。
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


# ---------- ref_lib 单元 ----------

def test_rule_defs_in_line():
    assert ref_lib.rule_defs_in_line("### R-A-01 装备增益") == {"R-A-01"}
    assert ref_lib.rule_defs_in_line("| R-A-02 | 背包位置 |") == {"R-A-02"}
    assert ref_lib.rule_defs_in_line("- **R-A-03**: 略") == {"R-A-03"}
    assert ref_lib.rule_defs_in_line("数值见 R-B-99 待定") == set()    # 散文中段引用,非定义
    assert ref_lib.rule_defs_in_line("Scenario: 符合 R-A-01") == set()
    # 标题行命名其 R 子系统:中段的 R 编号也算定义
    assert ref_lib.rule_defs_in_line("## 一、合成 — R-POT-CRAFT") == {"R-POT-CRAFT"}
    # 通配/泛指写法既不算定义也不算引用
    assert ref_lib.rule_defs_in_line("> 每条挂 R-POT-* 编号") == set()
    assert list(ref_lib._codes_in("挂 R-POT-* 与 R-A-01")) == ["R-A-01"]


def test_scan_text_roles():
    d = _proj({"rules.md":
               "### R-A-01 装备增益主属性\n"
               "主属性见 Foo[3].hp 与 Foo[5]\n"
               "数值口径见 R-B-99(待定)\n"})
    try:
        sc = ref_lib.scan_text(os.path.join(d, "rules.md"))
        assert sc["rule_defs"] == {"R-A-01"}
        assert sc["rule_refs"] == {"R-B-99"}            # 定义的 R-A-01 不算自引
        assert sc["table_refs"] == {"Foo"}
        assert sc["proto_imports"] == set()
    finally:
        shutil.rmtree(d, ignore_errors=True)


# ---------- ref_graph 集成 ----------

def _sample():
    return _proj({
        "rules.md": "### R-A-01 增益\n主属性 Foo[3].hp\n### R-A-02 背包\n数值见 R-B-99 待定\n",
        "accept.md": "Scenario A\n  Then 符合 R-A-01\nScenario B\n  Then 并满足 R-A-02\n",
        "team.proto": 'syntax="proto3";\nimport "monster.proto";\n',
        "monster.proto": 'syntax="proto3";\nmessage Monster { int32 id = 1; }\n',
    })


def test_reverse_index():
    d = _sample()
    try:
        g = ref_graph.build(d)
        assert set(g["rule_def"]) == {"R-A-01", "R-A-02"}
        # 反向索引:谁引用 R-A-01 → accept.md(rules.md 是定义方,不算引用)
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
        assert backnames == {"accept.md"}              # 改 rules.md → accept.md 受影响
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_dangling_rule_and_table():
    d = _sample()
    try:
        g = ref_graph.build(d)
        dang = ref_graph.dangling(g)
        kinds = {(x["kind"], x["sym"], x["sev"]) for x in dang}
        assert ("DANGLING_RULE", "R-B-99", "major") in kinds        # 引用了无人定义的 R 编号
        assert ("DANGLING_TABLE", "Foo", "advisory") in kinds       # 无 xlsx 表 → 只 advisory
        # monster.proto 存在 → 不应悬空
        assert not any(x["kind"] == "DANGLING_PROTO" for x in dang)
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_heading_subsystem_def_not_dangling():
    # 子系统码写在标题、叶子码写在行首;引用子系统码不应判悬空
    d = _proj({
        "rules.md": "## 一、合成 — R-M-CRAFT\n- **R-M-CRAFT-01** 略\n",
        "manifest.md": "C 表分块引用 R-M-CRAFT 子系统\n",
        "accept.md": "场景 (R-M-CRAFT-01)\n",
    })
    try:
        g = ref_graph.build(d)
        assert {"R-M-CRAFT", "R-M-CRAFT-01"} <= set(g["rule_def"])
        dang = ref_graph.dangling(g)
        assert not any(x["kind"] == "DANGLING_RULE" for x in dang)   # 两级都已定义
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_dangling_proto():
    d = _proj({"team.proto": 'import "ghost.proto";\n'})       # 无 ghost.proto
    try:
        g = ref_graph.build(d)
        dang = ref_graph.dangling(g)
        assert any(x["kind"] == "DANGLING_PROTO" and x["sym"] == "ghost.proto"
                   and x["sev"] == "major" for x in dang)
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_dup_def():
    d = _proj({"a.md": "### R-X-01 甲\n", "b.md": "### R-X-01 乙(重复定义)\n"})
    try:
        g = ref_graph.build(d)
        dang = ref_graph.dangling(g)
        assert any(x["kind"] == "DUP_DEF" and x["sym"] == "R-X-01" for x in dang)
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_check_exit_code():
    # 有悬空 R 编号 → --check 退出码 1
    d = _sample()
    try:
        assert ref_graph.main([d, "--check"]) == 1
    finally:
        shutil.rmtree(d, ignore_errors=True)
    # 干净项目 → --check 退出码 0
    d2 = _proj({"rules.md": "### R-A-01 增益\n", "accept.md": "Then 符合 R-A-01\n"})
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
        assert "DO NOT EDIT" in text and "← 被引" in text
        assert "accept.md" in text                     # rules.md 的影响集里应出现
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
