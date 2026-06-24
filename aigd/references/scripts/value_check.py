# -*- coding: utf-8 -*-
"""工具5 · value_check —— 配置数据完整性校验(纯 stdlib,复用 config_index + config_check)。

schema 校验器(config_check)管「结构对不对」;本工具管「数据本身/数据之间对不对」:
  FK_BREAK      配置说明 引用列 `表.字段` 外键:源列有值在目标列找不到(断链)
  ACC_DANGLING  验收用例里的 `表[主键].字段` 引用解析不到配置行(悬空引用)
  RULE_*        选填规则文件(<系统>.checks.json)的领域约束:
                  cardinality 数组成员数 vs 另一表的值(如 进化链长−1 ≤ 品质可进化次数)
                  monotonic   字段随档位单调不减(如 *Percentage,可按 group_fields 分组)
                  coverage    整数主键连续覆盖 [min,max] 无断档
跨文档引用(枚举字典.X / 属性列表.md / 道具表 这类非机器句柄)→ 记 FK_SKIP(info),不静默漏。

用法:
  python value_check.py <config-spec.md> <配置目录> [--acc <acceptance.md>]
        [--rules <系统.checks.json>] [--enums <枚举字典.md>] [--keymap <复合键映射.json>]
  退出码: 有 major(FK_BREAK / RULE_CARDINALITY) → 1。
"""
import sys, os, re, json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config_index as CI
import config_check as CC

_TF_RE = re.compile(r"^([^\s.]+)\.([^\s.]+)$")   # `表.字段`(含中文表名,如 枚举字典.Rarity → 记 FK_SKIP)
_NULL_FK = {"0", "0.0"}    # 外键空哨兵:本项目 id 恒为正,0=无引用(末阶/无前置等),不参与断链判定


def _int(v):
    try:
        return int(float(str(v).strip()))
    except (ValueError, TypeError):
        return None


def _col(row, c):
    return row[c] if (c is not None and c < len(row)) else None


# ---------------------------------------------------------------- 外键
def check_fk(doc, idx, refmap=None):
    """外键断链。引用列 `表.字段`(英文)直接解析;中文名/文档名经 refmap 映射(跨文件)。
    数组源(is_array)逐成员校验(v3);0/空哨兵不参与。"""
    refmap = refmap or {}
    findings = []
    for table in sorted(doc):
        for fn in sorted(doc[table]["fields"]):
            fld = doc[table]["fields"][fn]
            ref = (fld.get("ref") or "").strip().strip("`").strip()
            tgt = refmap.get(ref)                  # 中文名/文档名 → 英文 表.字段
            m = _TF_RE.match(tgt if tgt else ref)
            if not m:
                continue                           # 非外键引用(—/纯中文未登记/外部标记)
            tgt_t, tgt_f = m.group(1), m.group(2)
            if fld.get("is_array"):
                srcvals = CI.array_column_values(idx, table, fn)
                if srcvals is None:
                    findings.append({"sev": "info", "kind": "FK_SKIP", "table": table, "field": fn,
                                     "msg": "数组源 '%s.%s'→'%s.%s' 表头未识别为数组列,跳过" % (table, fn, tgt_t, tgt_f)})
                    continue
                lbl = "数组成员"
            else:
                srcvals = CI.column_values(idx, table, fn)
                if srcvals is None:
                    continue                       # 源表/列不在 idx(如改名表)→ 交 schema 校验器
                lbl = ""
            tgtvals = CI.column_values(idx, tgt_t, tgt_f)
            if tgtvals is None:
                findings.append({"sev": "info", "kind": "FK_SKIP", "table": table, "field": fn,
                                 "msg": "引用 '%s.%s' 目标不在配置表中(未登记/跨文档),跳过" % (tgt_t, tgt_f)})
                continue
            bad = sorted((srcvals - _NULL_FK) - tgtvals, key=lambda x: (len(x), x))
            if bad:
                more = " …共%d个" % len(bad) if len(bad) > 5 else ""
                findings.append({"sev": "major", "kind": "FK_BREAK", "table": table, "field": fn,
                                 "msg": "'%s.%s'%s→'%s.%s' 外键断链,源有值目标缺: %s%s" % (
                                     table, fn, ("(%s)" % lbl if lbl else ""), tgt_t, tgt_f,
                                     ",".join(bad[:5]), more)})
    return findings


# ---------------------------------------------------------------- 验收引用解析
def check_acceptance(acc_text, idx):
    findings, seen = [], set()
    for m in CI.REF_RE.finditer(acc_text):
        ref, table, keystr, field = m.group(0), m.group(1), m.group(2).strip(), m.group(3)
        k = (table, keystr, field)
        if k in seen:
            continue
        seen.add(k)
        # 只报『行不存在』的悬空引用;字段空值(可选字段)不算断链,避免误报
        if table in idx and CI.row_exists(idx, table, keystr) is False:
            findings.append({"sev": "advisory", "kind": "ACC_DANGLING", "table": table, "field": field,
                             "msg": "验收引用 '%s' 配置中无此行(主键命不中=悬空引用)" % ref})
    return sorted(findings, key=lambda f: f["msg"])


# ---------------------------------------------------------------- rules
def _rule_cardinality(rule, idx):
    at, af = rule["array_table"], rule["array_field"]
    t = idx.get(at)
    if not t:
        return [{"sev": "info", "kind": "RULE_SKIP", "table": at, "field": af,
                 "msg": "cardinality: 数组表 '%s' 不在配置表" % at}]
    start = t["fieldcol"].get(af)
    if start is None:
        return [{"sev": "info", "kind": "RULE_SKIP", "table": at, "field": af,
                 "msg": "cardinality: 数组字段 '%s' 未找到" % af}]
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
                        "msg": "%s[%s] 链长 %d(=%d 段进化) > %s[%s].%s=%s(超出成员在该上限下不可达)" % (
                            at, gid, len(members), evo, rule["limit_table"], rarity, rule["limit_field"], limit)})
    return out


def _rule_coverage(rule, idx):
    t = idx.get(rule["table"])
    if not t:
        return [{"sev": "info", "kind": "RULE_SKIP", "table": rule["table"], "field": rule["field"],
                 "msg": "coverage: 表不在配置"}]
    fc = t["fieldcol"].get(rule["field"])
    if fc is None:
        return [{"sev": "info", "kind": "RULE_SKIP", "table": rule["table"], "field": rule["field"],
                 "msg": "coverage: 字段未找到"}]
    vals = set(v for v in (_int(_col(row, fc)) for row in t["data"]) if v is not None)
    missing = [i for i in range(rule["min"], rule["max"] + 1) if i not in vals]
    if missing:
        more = " …共%d个" % len(missing) if len(missing) > 8 else ""
        return [{"sev": "advisory", "kind": "RULE_COVERAGE", "table": rule["table"], "field": rule["field"],
                 "msg": "%s.%s 未连续覆盖 [%d,%d],缺: %s%s" % (
                     rule["table"], rule["field"], rule["min"], rule["max"],
                     ",".join(str(x) for x in missing[:8]), more)}]
    return []


def _rule_monotonic(rule, idx):
    t = idx.get(rule["table"])
    if not t:
        return [{"sev": "info", "kind": "RULE_SKIP", "table": rule["table"], "field": rule["field"],
                 "msg": "monotonic: 表不在配置"}]
    ff = t["fieldcol"].get(rule["field"])
    of = t["fieldcol"].get(rule["order_field"])
    groups = rule.get("group_fields", [])
    gcols = [t["fieldcol"].get(g) for g in groups]
    if ff is None or of is None or any(c is None for c in gcols):
        return [{"sev": "info", "kind": "RULE_SKIP", "table": rule["table"], "field": rule["field"],
                 "msg": "monotonic: 字段/分组列未找到"}]
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
                            "msg": "%s.%s 非单调:按 %s 第 %d 档 %d→%d 下降%s" % (
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
                             "msg": "未知规则类型 '%s',跳过" % rule.get("type")})
    return findings


# ---------------------------------------------------------------- 顶层
def check(config_md_path, config_dir, acc_path=None, rules_path=None,
          enums_path=None, keymap_path=None, refmap_path=None):
    with open(config_md_path, encoding="utf-8") as f:
        doc = CC.parse_config_md(f.read())
    idx = CI.build_index(config_dir)
    if not keymap_path:
        auto = os.path.join(config_dir, "复合键映射.json")
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
        auto = os.path.join(config_dir, "引用表映射.json")
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
    out = ["配置数据完整性校验(value_check)", "  " + "  ".join(args), ""]
    if not findings:
        out.append("✓ 无问题:外键无断链、验收引用可解析、规则约束通过。")
        return "\n".join(out)
    nm = sum(1 for f in findings if f["sev"] == "major")
    na = sum(1 for f in findings if f["sev"] == "advisory")
    ni = sum(1 for f in findings if f["sev"] == "info")
    out.append("发现 %d 条(major=%d advisory=%d info=%d):" % (len(findings), nm, na, ni))
    out.append("")
    tag = {"major": "[major]", "advisory": "[advisory]", "info": "[info]"}
    for f in sorted(findings, key=lambda x: (_SEV[x["sev"]], x["kind"], x.get("table") or "")):
        out.append("  %-10s %-16s %s" % (tag[f["sev"]], f["kind"], f["msg"]))
    out.append("")
    out.append("major(FK_BREAK / RULE_CARDINALITY)须修数据/规则后重跑;advisory 请人工判定。")
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
        sys.stderr.write("usage: python value_check.py <config-spec.md> <配置目录> "
                         "[--acc <acceptance.md>] [--rules <系统.checks.json>] "
                         "[--enums <枚举字典.md>] [--keymap <复合键映射.json>] "
                         "[--refmap <引用表映射.json>]\n")
        return 2
    findings = check(pos[0], pos[1], acc_path=opt.get("acc"), rules_path=opt.get("rules"),
                     enums_path=opt.get("enums"), keymap_path=opt.get("keymap"),
                     refmap_path=opt.get("refmap"))
    sys.stdout.buffer.write((format_report(findings, pos) + "\n").encode("utf-8"))
    return 1 if any(f["sev"] == "major" for f in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
