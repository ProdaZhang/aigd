# -*- coding: utf-8 -*-
"""ref_graph -- design-file **bidirectional reference graph** + **dangling-reference gate** (pure stdlib, reuses ref_lib/config_index/xlsx_dump).

Scans all design files in a project, extracts **structured** references (R-codes / Table[primary key] / proto import), and gives:
  - per file "-> references": who it references (and where that symbol is defined)
  - per file "<- referenced by": who references "the symbols this file defines" = **the impact set of changing this file**

Discipline: **forward references are the source of truth; the reverse index is computed live and never persisted** (nothing derived is stored -> never drifts). "Referenced by" may be **displayed** in the generated file
`refs.md` (marked DO-NOT-EDIT at the top, fully overwritten each run), but is **never hand-written into** source-of-truth docs like rules/config-spec/manifest.

    python ref_graph.py <project root> [--out refs.md] [--who-refs <symbol>] [--check] [--json]

  --out      generate the bidirectional graph to a file (pure artifact, do not hand-edit; if omitted, only a terminal summary is shown)
  --who-refs query a single symbol (R-code / table name / x.proto) impact set: where it is defined + who references it
  --check    dangling-reference gate: dangling R-code/proto = major -> exit code 1 (for CI); a dangling table is only advisory (the grammar may falsely match array notation)
  --json     machine-readable output

Only structured tokens are recognized, no fuzzy prose matching -- so it **never reports "the graph changed"** (that would turn it into a treadmill of committing generated artifacts), only real errors (dangling / definition-point collision).
"""
import os, sys, json, argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ref_lib


def build(root):
    """Scan -> symbol definition table + reverse index (who-refs)."""
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

    who_rule, who_table, who_proto = {}, {}, {}        # reverse index (computed live, not persisted)
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
    """Dangling / definition-point-collision findings. R-code and proto = major; table = advisory (grammar may falsely match array notation)."""
    out = []
    for r, files in sorted(g["who_rule"].items()):
        if r not in g["rule_def"]:
            out.append({"sev": "major", "kind": "DANGLING_RULE", "sym": r,
                        "msg": "R-code %s is referenced but no file defines it (definition point missing)" % r,
                        "refs": sorted(set(files))})
    for im, files in sorted(g["who_proto"].items()):
        if im not in g["proto_files"]:
            out.append({"sev": "major", "kind": "DANGLING_PROTO", "sym": im,
                        "msg": 'import "%s" cannot find a matching .proto file' % im,
                        "refs": sorted(set(files))})
    for t, files in sorted(g["who_table"].items()):
        if t not in g["table_def"]:
            out.append({"sev": "advisory", "kind": "DANGLING_TABLE", "sym": t,
                        "msg": "table reference %s[...] has no matching xlsx table ([inferred]; may also be a false match against array notation, needs human review)" % t,
                        "refs": sorted(set(files))})
    for r, defs in sorted(g["rule_def"].items()):
        if len(set(defs)) > 1:
            out.append({"sev": "advisory", "kind": "DUP_DEF", "sym": r,
                        "msg": "R-code %s appears as a definition point in multiple places (should be uniquely defined), needs human review" % r,
                        "refs": sorted(set(defs))})
    return out


def who_refs(g, sym):
    """A symbol's (R-code / table name / x.proto) impact set: where it is defined + which files reference it."""
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
    """A file's (forward reference list, set of symbols this file defines, referenced-by {file: [via which symbols]})."""
    sc = g["file_scan"].get(path, {})
    forward = []
    for r in sorted(sc.get("rule_refs", set())):
        forward.append(("R", r, g["rule_def"].get(r, [])))
    for t in sorted(sc.get("table_refs", set())):
        forward.append(("table", t, g["table_def"].get(t, [])))
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
    """Bidirectional graph -> generated markdown (pure artifact, do not hand-edit)."""
    L = ["<!-- GENERATED by ref_graph.py -- DO NOT EDIT. Regenerate by re-running, do not hand-edit; the reverse index is derived, just re-run after editing docs. -->",
         "# Reference graph (bidirectional)", "",
         "> Forward references are the source of truth; the \"<- referenced by\" column below is a live-computed derivative. After editing docs, run `ref_graph.py <root> --out <this file>` to regenerate.", ""]
    for p in sorted(set(g["texts"]) | set(g["xlsxs"])):
        fwd, _defined, back = file_view(g, p)
        L.append("## " + _rel(g, p))
        if fwd:
            L.append("  -> references:")
            for kind, sym, dfn in fwd:
                tgt = ("  -> " + ", ".join(_rel(g, d) for d in dfn)) if dfn else "  !dangling"
                L.append("      [%s] %s%s" % (kind, sym, tgt))
        if back:
            L.append("  <- referenced by (impact set of changing this file):")
            for f, syms in sorted(back.items()):
                L.append("      %s  (via %s)" % (_rel(g, f), ", ".join(sorted(syms))))
        if not fwd and not back:
            L.append("  (no structured references)")
        L.append("")
    return "\n".join(L)


def main(argv):
    ap = argparse.ArgumentParser(description="Design-file bidirectional reference graph + dangling-reference gate")
    ap.add_argument("root", help="project root directory")
    ap.add_argument("--out", help="generate the bidirectional graph to this file (pure artifact, do not hand-edit)")
    ap.add_argument("--who-refs", dest="who", help="query a single symbol (R-code/table name/x.proto) impact set")
    ap.add_argument("--check", action="store_true", help="dangling gate: dangling R-code/proto -> exit code 1")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    a = ap.parse_args(argv)
    g = build(a.root)

    if a.who:
        res = who_refs(g, a.who)
        if a.json:
            print(json.dumps(res, ensure_ascii=False, indent=2))
            return 0
        print("symbol: " + a.who)
        print("  defined in: " + (", ".join(_rel(g, d) for d in res["defined_in"]) or "(none -> dangling)"))
        print("  referenced in (impact set of changing it):")
        for f in res["referenced_in"]:
            print("      " + _rel(g, f))
        if not res["referenced_in"]:
            print("      (none)")
        return 0

    dang = dangling(g)
    nfiles = len(g["texts"]) + len(g["xlsxs"])
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(render_md(g))
        print("generated %s (%d files)" % (a.out, nfiles))

    majors = [d for d in dang if d["sev"] == "major"]
    if a.json:
        print(json.dumps({"files": nfiles, "dangling": dang}, ensure_ascii=False, indent=2))
    elif dang:
        print("reference issues (%d; major %d):" % (len(dang), len(majors)))
        for d in dang:
            print("  [%s] %s  %s" % (d["sev"], d["kind"], d["msg"]))
            for r in d["refs"][:6]:
                print("        <- " + _rel(g, r))
    else:
        print("scanned %d files, no dangling/collision references (passed)" % nfiles)

    return 1 if (a.check and majors) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
