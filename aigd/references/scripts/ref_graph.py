# -*- coding: utf-8 -*-
"""ref_graph —— 设计文件**双向引用图** + **悬空引用门禁**(纯 stdlib,复用 ref_lib/config_index/xlsx_dump)。

扫项目所有设计文件,抽**结构化**引用(R 编号 / 表[主键] / proto import),给出:
  - 每文件「→ 引用」:它引用了谁(及该符号定义在哪)
  - 每文件「← 被引」:谁引用了"本文件定义的符号" = **改本文件的影响集**

纪律:**正向引用是真源,反向索引实时算、绝不落盘**(派生不存 → 永不漂移)。"被引用"可**展示**在生成文件
`refs.md` 里(顶部标 DO-NOT-EDIT、每次全量覆盖),但**绝不手写进**规则/配置说明/manifest 等真源文档。

    python ref_graph.py <项目根> [--out refs.md] [--who-refs <符号>] [--check] [--json]

  --out      生成双向图到文件(纯产物,勿手改;不传则只在终端给摘要)
  --who-refs 查单个符号(R 编号 / 表名 / x.proto)的影响集:定义在哪 + 被谁引用
  --check    悬空引用门禁:R 编号/proto 悬空 = major → 退出码 1(进 CI);表悬空只 advisory(语法可能误命中 array 记法)
  --json     机读输出

只认结构化令牌、不做散文模糊匹配——所以**不报"图变了"**(那会变成提交生成物的跑步机),只报真错(悬空/定义点撞车)。
"""
import os, sys, json, argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ref_lib


def build(root):
    """扫描 → 符号定义表 + 反向索引(who-refs)。"""
    texts, xlsxs = ref_lib.discover_files(root)
    rule_def, table_def, proto_files, file_scan = {}, {}, {}, {}
    for p in texts:
        sc = ref_lib.scan_text(p)
        file_scan[p] = sc
        for d in sc["rule_defs"]:
            rule_def.setdefault(d, []).append(p)
        if p.lower().endswith(".proto"):
            proto_files.setdefault(os.path.basename(p), p)
    for x in xlsxs:
        for t in ref_lib.xlsx_tables(x):
            table_def.setdefault(t, []).append(x)

    who_rule, who_table, who_proto = {}, {}, {}        # 反向索引(实时算,不落盘)
    for p, sc in file_scan.items():
        for r in sc["rule_refs"]:
            who_rule.setdefault(r, []).append(p)
        for t in sc["table_refs"]:
            who_table.setdefault(t, []).append(p)
        for im in sc["proto_imports"]:
            who_proto.setdefault(im, []).append(p)

    return {"root": root, "texts": texts, "xlsxs": xlsxs,
            "rule_def": rule_def, "table_def": table_def, "proto_files": proto_files,
            "file_scan": file_scan,
            "who_rule": who_rule, "who_table": who_table, "who_proto": who_proto}


def _rel(g, p):
    return os.path.relpath(p, g["root"]).replace("\\", "/")


def dangling(g):
    """悬空 / 定义点撞车 findings。R 编号·proto = major;表 = advisory(语法可能误命中 array 记法)。"""
    out = []
    for r, files in sorted(g["who_rule"].items()):
        if r not in g["rule_def"]:
            out.append({"sev": "major", "kind": "DANGLING_RULE", "sym": r,
                        "msg": "R 编号 %s 被引用但无任何文件定义它(定义点缺失)" % r,
                        "refs": sorted(set(files))})
    for im, files in sorted(g["who_proto"].items()):
        if im not in g["proto_files"]:
            out.append({"sev": "major", "kind": "DANGLING_PROTO", "sym": im,
                        "msg": 'import "%s" 找不到对应 .proto 文件' % im,
                        "refs": sorted(set(files))})
    for t, files in sorted(g["who_table"].items()):
        if t not in g["table_def"]:
            out.append({"sev": "advisory", "kind": "DANGLING_TABLE", "sym": t,
                        "msg": "表引用 %s[…] 无对应 xlsx 表([推断];也可能是 array 记法误命中,需人核)" % t,
                        "refs": sorted(set(files))})
    for r, defs in sorted(g["rule_def"].items()):
        if len(set(defs)) > 1:
            out.append({"sev": "advisory", "kind": "DUP_DEF", "sym": r,
                        "msg": "R 编号 %s 在多处呈定义点(应唯一定义),需人核" % r,
                        "refs": sorted(set(defs))})
    return out


def who_refs(g, sym):
    """某符号(R 编号 / 表名 / x.proto)的影响集:定义在哪 + 被哪些文件引用。"""
    defined = []
    if sym in g["rule_def"]:
        defined = sorted(set(g["rule_def"][sym]))
    elif sym in g["table_def"]:
        defined = sorted(set(g["table_def"][sym]))
    elif sym in g["proto_files"]:
        defined = [g["proto_files"][sym]]
    referenced = sorted(set(g["who_rule"].get(sym, []) +
                            g["who_table"].get(sym, []) +
                            g["who_proto"].get(sym, [])))
    return {"symbol": sym, "defined_in": defined, "referenced_in": referenced}


def file_view(g, path):
    """一个文件的 (正向引用列表, 本文件定义的符号集, 被引{文件: [经哪些符号]})。"""
    sc = g["file_scan"].get(path, {})
    forward = []
    for r in sorted(sc.get("rule_refs", set())):
        forward.append(("R", r, g["rule_def"].get(r, [])))
    for t in sorted(sc.get("table_refs", set())):
        forward.append(("表", t, g["table_def"].get(t, [])))
    for im in sorted(sc.get("proto_imports", set())):
        forward.append(("proto", im, [g["proto_files"][im]] if im in g["proto_files"] else []))

    defined = set(sc.get("rule_defs", set()))
    low = path.lower()
    if low.endswith(".xlsx"):
        defined |= {t for t, xs in g["table_def"].items() if path in xs}
    if low.endswith(".proto"):
        defined.add(os.path.basename(path))

    back = {}
    for sym in defined:
        for f in set(g["who_rule"].get(sym, []) +
                     g["who_table"].get(sym, []) +
                     g["who_proto"].get(sym, [])):
            if f != path:
                back.setdefault(f, set()).add(sym)
    return forward, defined, back


def render_md(g):
    """双向图 → 生成式 markdown(纯产物,勿手改)。"""
    L = ["<!-- GENERATED by ref_graph.py — DO NOT EDIT. 重跑生成,勿手改;反向索引是派生物,改文档后重跑即可。 -->",
         "# 引用图(双向)", "",
         "> 正向引用是真源;本表「← 被引」为实时计算的派生物。改了文档跑 `ref_graph.py <根> --out <本文件>` 重生成。", ""]
    for p in sorted(set(g["texts"]) | set(g["xlsxs"])):
        fwd, _defined, back = file_view(g, p)
        L.append("## " + _rel(g, p))
        if fwd:
            L.append("  → 引用:")
            for kind, sym, dfn in fwd:
                tgt = ("  → " + ", ".join(_rel(g, d) for d in dfn)) if dfn else "  ⚠悬空"
                L.append("      [%s] %s%s" % (kind, sym, tgt))
        if back:
            L.append("  ← 被引(改本文件的影响集):")
            for f, syms in sorted(back.items()):
                L.append("      %s  (经 %s)" % (_rel(g, f), ", ".join(sorted(syms))))
        if not fwd and not back:
            L.append("  (无结构化引用)")
        L.append("")
    return "\n".join(L)


def main(argv):
    ap = argparse.ArgumentParser(description="设计文件双向引用图 + 悬空引用门禁")
    ap.add_argument("root", help="项目根目录")
    ap.add_argument("--out", help="生成双向图到此文件(纯产物,勿手改)")
    ap.add_argument("--who-refs", dest="who", help="查单个符号(R 编号/表名/x.proto)的影响集")
    ap.add_argument("--check", action="store_true", help="悬空门禁:R 编号/proto 悬空→退出码 1")
    ap.add_argument("--json", action="store_true", help="机读输出")
    a = ap.parse_args(argv)
    g = build(a.root)

    if a.who:
        res = who_refs(g, a.who)
        if a.json:
            print(json.dumps(res, ensure_ascii=False, indent=2))
            return 0
        print("符号: " + a.who)
        print("  定义于: " + (", ".join(_rel(g, d) for d in res["defined_in"]) or "(无 → 悬空)"))
        print("  被引用于(改它的影响集):")
        for f in res["referenced_in"]:
            print("      " + _rel(g, f))
        if not res["referenced_in"]:
            print("      (无)")
        return 0

    dang = dangling(g)
    nfiles = len(g["texts"]) + len(g["xlsxs"])
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(render_md(g))
        print("已生成 %s(%d 文件)" % (a.out, nfiles))

    majors = [d for d in dang if d["sev"] == "major"]
    if a.json:
        print(json.dumps({"files": nfiles, "dangling": dang}, ensure_ascii=False, indent=2))
    elif dang:
        print("引用问题(%d;major %d):" % (len(dang), len(majors)))
        for d in dang:
            print("  [%s] %s  %s" % (d["sev"], d["kind"], d["msg"]))
            for r in d["refs"][:6]:
                print("        ← " + _rel(g, r))
    else:
        print("扫描 %d 文件,无悬空/撞车引用(通过)" % nfiles)

    return 1 if (a.check and majors) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
