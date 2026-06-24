# -*- coding: utf-8 -*-
"""Tool 5 - value_check -- config-data integrity validation (pure stdlib, reuses config_index + config_check).

The schema validator (config_check) handles "is the structure right"; this tool handles "is the data itself / between data right":
  FK_BREAK      foreign key from a config-spec Ref column `Table.field`: a source column has a value not found in the target column (broken link)
  ACC_DANGLING  a `Table[primary key].field` reference in an acceptance case does not resolve to a config row (dangling reference)
  RULE_*        domain constraints from an optional rules file (<system>.checks.json):
                  cardinality  array member count vs another table's value (e.g. evolution chain length - 1 <= rarity max evolutions)
                  monotonic    a field is non-decreasing along a tier (e.g. *Percentage, can be grouped by group_fields)
                  coverage     integer primary key covers [min,max] contiguously with no gaps
Cross-document references (enum-dict.X / attribute-list.md / item-table and similar non-machine handles) -> recorded as FK_SKIP (info), not silently dropped.

Usage:
  python value_check.py <config-spec.md> <config dir> [--acc <acceptance.md>]
        [--rules <system.checks.json>] [--enums <enum-dict.md>] [--keymap <composite-key-map.json>]
  Exit code: any major (FK_BREAK / RULE_CARDINALITY) -> 1.
"""
import sys, os, re, json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config_index as CI
import config_check as CC

_TF_RE = re.compile(r"^([^\s.]+)\.([^\s.]+)$")   # `Table.field` (incl. Chinese table names, e.g. enum-dict.Rarity -> recorded as FK_SKIP)
_NULL_FK = {"0", "0.0"}    # foreign-key null sentinel: in this project ids are always positive, 0 = no reference (last stage / no predecessor etc.), not part of broken-link checks


def _int(v):
    try:
        return int(float(str(v).strip()))
    except (ValueError, TypeError):
        return None


def _col(row, c):
    return row[c] if (c is not None and c < len(row)) else None


# ---------------------------------------------------------------- foreign keys
def check_fk(doc, idx, refmap=None):
    """Foreign-key broken links. A Ref column `Table.field` (English) resolves directly; Chinese names / doc names are mapped via refmap (cross-file).
    Array sources (is_array) are checked per member (v3); 0/empty sentinels are excluded."""
    refmap = refmap or {}
    findings = []
    for table in sorted(doc):
        for fn in sorted(doc[table]["fields"]):
            fld = doc[table]["fields"][fn]
            ref = (fld.get("ref") or "").strip().strip("`").strip()
            tgt = refmap.get(ref)                  # Chinese name / doc name -> English Table.field
            m = _TF_RE.match(tgt if tgt else ref)
            if not m:
                continue                           # not a foreign-key reference (—/pure Chinese not registered/external marker)
            tgt_t, tgt_f = m.group(1), m.group(2)
            if fld.get("is_array"):
                srcvals = CI.array_column_values(idx, table, fn)
                if srcvals is None:
                    findings.append({"sev": "info", "kind": "FK_SKIP", "table": table, "field": fn,
                                     "msg": "array source '%s.%s'->'%s.%s' header not recognized as an array column, skipped" % (table, fn, tgt_t, tgt_f)})
                    continue
                lbl = "array member"
            else:
                srcvals = CI.column_values(idx, table, fn)
                if srcvals is None:
                    continue                       # source table/column not in idx (e.g. renamed table) -> leave to schema validator
                lbl = ""
            tgtvals = CI.column_values(idx, tgt_t, tgt_f)
            if tgtvals is None:
                findings.append({"sev": "info", "kind": "FK_SKIP", "table": table, "field": fn,
                                 "msg": "reference '%s.%s' target not in config tables (not registered/cross-document), skipped" % (tgt_t, tgt_f)})
                continue
            bad = sorted((srcvals - _NULL_FK) - tgtvals, key=lambda x: (len(x), x))
            if bad:
                more = " ...%d in total" % len(bad) if len(bad) > 5 else ""
                findings.append({"sev": "major", "kind": "FK_BREAK", "table": table, "field": fn,
                                 "msg": "'%s.%s'%s->'%s.%s' foreign-key broken link, source has values the target lacks: %s%s" % (
                                     table, fn, ("(%s)" % lbl if lbl else ""), tgt_t, tgt_f,
                                     ",".join(bad[:5]), more)})
    return findings


# ---------------------------------------------------------------- acceptance reference resolution
def check_acceptance(acc_text, idx):
    findings, seen = [], set()
    for m in CI.REF_RE.finditer(acc_text):
        ref, table, keystr, field = m.group(0), m.group(1), m.group(2).strip(), m.group(3)
        k = (table, keystr, field)
        if k in seen:
            continue
        seen.add(k)
        # Only report 'row does not exist' dangling references; an empty field value (optional field) is not a broken link, to avoid false positives
        if table in idx and CI.row_exists(idx, table, keystr) is False:
            findings.append({"sev": "advisory", "kind": "ACC_DANGLING", "table": table, "field": field,
                             "msg": "acceptance reference '%s' has no such row in config (primary key miss = dangling reference)" % ref})
    return sorted(findings, key=lambda f: f["msg"])


# ---------------------------------------------------------------- rules
def _rule_cardinality(rule, idx):
    at, af = rule["array_table"], rule["array_field"]
    t = idx.get(at)
    if not t:
        return [{"sev": "info", "kind": "RULE_SKIP", "table": at, "field": af,
                 "msg": "cardinality: array table '%s' not in config tables" % at}]
    start = t["fieldcol"].get(af)
    if start is None:
        return [{"sev": "info", "kind": "RULE_SKIP", "table": at, "field": af,
                 "msg": "cardinality: array field '%s' not found" % af}]
    idc = t["fieldcol"].get("id", 0)
    out = []
    for row in t["data"]:
        members = [v for v in (row[start:] if start < len(row) else []) if str(v).strip() and _int(v) is not None]
        if not members:
            continue
        rarity = CI.lookup(idx, rule["member_table"], members[0], rule["member_rarity_field"])
        if rarity is None or rarity == "MULTI":
            continue
        limit = CI.lookup(idx, rule["limit_table"], rarity, rule["limit_field"])
        if limit is None or _int(limit) is None:
            continue
        evo = len(members) - 1
        if evo > _int(limit):
            gid = _col(row, idc) or "?"
            out.append({"sev": rule.get("severity", "major"), "kind": "RULE_CARDINALITY", "table": at, "field": af,
                        "msg": "%s[%s] chain length %d (=%d evolution steps) > %s[%s].%s=%s (members beyond this limit are unreachable)" % (
                            at, gid, len(members), evo, rule["limit_table"], rarity, rule["limit_field"], limit)})
    return out


def _rule_coverage(rule, idx):
    t = idx.get(rule["table"])
    if not t:
        return [{"sev": "info", "kind": "RULE_SKIP", "table": rule["table"], "field": rule["field"],
                 "msg": "coverage: table not in config"}]
    fc = t["fieldcol"].get(rule["field"])
    if fc is None:
        return [{"sev": "info", "kind": "RULE_SKIP", "table": rule["table"], "field": rule["field"],
                 "msg": "coverage: field not found"}]
    vals = set(v for v in (_int(_col(row, fc)) for row in t["data"]) if v is not None)
    missing = [i for i in range(rule["min"], rule["max"] + 1) if i not in vals]
    if missing:
        more = " ...%d in total" % len(missing) if len(missing) > 8 else ""
        return [{"sev": "advisory", "kind": "RULE_COVERAGE", "table": rule["table"], "field": rule["field"],
                 "msg": "%s.%s does not contiguously cover [%d,%d], missing: %s%s" % (
                     rule["table"], rule["field"], rule["min"], rule["max"],
                     ",".join(str(x) for x in missing[:8]), more)}]
    return []


def _rule_monotonic(rule, idx):
    t = idx.get(rule["table"])
    if not t:
        return [{"sev": "info", "kind": "RULE_SKIP", "table": rule["table"], "field": rule["field"],
                 "msg": "monotonic: table not in config"}]
    ff = t["fieldcol"].get(rule["field"])
    of = t["fieldcol"].get(rule["order_field"])
    groups = rule.get("group_fields", [])
    gcols = [t["fieldcol"].get(g) for g in groups]
    if ff is None or of is None or any(c is None for c in gcols):
        return [{"sev": "info", "kind": "RULE_SKIP", "table": rule["table"], "field": rule["field"],
                 "msg": "monotonic: field/group column not found"}]
    buckets = {}
    for row in t["data"]:
        gkey = tuple(str(_col(row, c) or "") for c in gcols)
        o, fv = _int(_col(row, of)), _int(_col(row, ff))
        if o is None or fv is None:
            continue
        buckets.setdefault(gkey, []).append((o, fv))
    out = []
    for gkey in sorted(buckets):
        pairs = sorted(buckets[gkey])
        for i in range(1, len(pairs)):
            if pairs[i][1] < pairs[i - 1][1]:
                gtxt = (" group=%s" % ",".join(gkey)) if groups else ""
                out.append({"sev": "advisory", "kind": "RULE_MONOTONIC", "table": rule["table"], "field": rule["field"],
                            "msg": "%s.%s non-monotonic: by %s at tier %d it drops %d->%d%s" % (
                                rule["table"], rule["field"], rule["order_field"],
                                pairs[i][0], pairs[i - 1][1], pairs[i][1], gtxt)})
                break
    return out


_RULE_FN = {"cardinality": _rule_cardinality, "coverage": _rule_coverage, "monotonic": _rule_monotonic}


def run_rules(rules, idx):
    findings = []
    for rule in rules:
        fn = _RULE_FN.get(rule.get("type"))
        if fn:
            findings += fn(rule, idx)
        else:
            findings.append({"sev": "info", "kind": "RULE_UNKNOWN", "table": rule.get("table"), "field": None,
                             "msg": "unknown rule type '%s', skipped" % rule.get("type")})
    return findings


# ---------------------------------------------------------------- top level
def check(config_md_path, config_dir, acc_path=None, rules_path=None,
          enums_path=None, keymap_path=None, refmap_path=None):
    with open(config_md_path, encoding="utf-8") as f:
        doc = CC.parse_config_md(f.read())
    idx = CI.build_index(config_dir)
    if not keymap_path:
        auto = os.path.join(config_dir, "composite-key-map.json")
        if os.path.exists(auto):
            keymap_path = auto
    if keymap_path and os.path.exists(keymap_path):
        try:
            idx["__keymap__"] = CI.load_keymap(keymap_path)
        except Exception:
            pass
    if enums_path and os.path.exists(enums_path):
        try:
            idx["__enums__"] = CI.load_enums(enums_path)
        except Exception:
            pass
    if not refmap_path:
        auto = os.path.join(config_dir, "ref-table-map.json")
        if os.path.exists(auto):
            refmap_path = auto
    refmap = {}
    if refmap_path and os.path.exists(refmap_path):
        try:
            refmap = {k: v for k, v in json.load(open(refmap_path, encoding="utf-8")).items()
                      if not k.startswith("_")}
        except Exception:
            pass
    findings = check_fk(doc, idx, refmap)
    if acc_path and os.path.exists(acc_path):
        with open(acc_path, encoding="utf-8") as f:
            findings += check_acceptance(f.read(), idx)
    if rules_path and os.path.exists(rules_path):
        with open(rules_path, encoding="utf-8") as f:
            rj = json.load(f)
        findings += run_rules(rj.get("rules", []) if isinstance(rj, dict) else rj, idx)
    return findings


_SEV = {"major": 0, "advisory": 1, "info": 2}


def format_report(findings, args):
    out = ["config-data integrity validation (value_check)", "  " + "  ".join(args), ""]
    if not findings:
        out.append("OK no problems: foreign keys unbroken, acceptance references resolve, rule constraints pass.")
        return "\n".join(out)
    nm = sum(1 for f in findings if f["sev"] == "major")
    na = sum(1 for f in findings if f["sev"] == "advisory")
    ni = sum(1 for f in findings if f["sev"] == "info")
    out.append("found %d (major=%d advisory=%d info=%d):" % (len(findings), nm, na, ni))
    out.append("")
    tag = {"major": "[major]", "advisory": "[advisory]", "info": "[info]"}
    for f in sorted(findings, key=lambda x: (_SEV[x["sev"]], x["kind"], x.get("table") or "")):
        out.append("  %-10s %-16s %s" % (tag[f["sev"]], f["kind"], f["msg"]))
    out.append("")
    out.append("major (FK_BREAK / RULE_CARDINALITY) must be fixed in data/rules, then re-run; advisory needs human judgment.")
    return "\n".join(out)


def main(argv):
    pos, opt, i = [], {}, 1
    while i < len(argv):
        a = argv[i]
        if a in ("--acc", "--rules", "--enums", "--keymap", "--refmap") and i + 1 < len(argv):
            opt[a[2:]] = argv[i + 1]; i += 2
        else:
            pos.append(a); i += 1
    if len(pos) < 2:
        sys.stderr.write("usage: python value_check.py <config-spec.md> <config dir> "
                         "[--acc <acceptance.md>] [--rules <system.checks.json>] "
                         "[--enums <enum-dict.md>] [--keymap <composite-key-map.json>] "
                         "[--refmap <ref-table-map.json>]\n")
        return 2
    findings = check(pos[0], pos[1], acc_path=opt.get("acc"), rules_path=opt.get("rules"),
                     enums_path=opt.get("enums"), keymap_path=opt.get("keymap"),
                     refmap_path=opt.get("refmap"))
    sys.stdout.buffer.write((format_report(findings, pos) + "\n").encode("utf-8"))
    return 1 if any(f["sev"] == "major" for f in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
