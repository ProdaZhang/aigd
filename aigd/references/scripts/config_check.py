# -*- coding: utf-8 -*-
"""工具4 · config_check —— config-spec.md ↔ xlsx schema 漂移校验器(纯 stdlib)。

为什么存在:方法论把「值」放 xlsx、「schema/规则」放文档(config-spec.md 按字段名引用 xlsx)。
改值不用动文档 —— 但改**结构**(加列 / 改字段域 / 改 sheet 名)是改了文档拥有的 schema,
却改在了 xlsx 里,两边静默失同步。config-spec.md 末尾的「校验清单」写了对的检查,但它是
未勾的框、被自评 ✅。本脚本把那张清单的 schema 部分变成确定性机检。

抓什么(高置信):
  UNDOC_COL    xlsx 有列、配置说明没记 —— 后改 xlsx 未回写文档的典型痕迹
  MISSING_COL  配置说明声明字段、xlsx 无此列
  TYPE         同名字段 文档类型 ≠ xlsx 类型
  RENAME       文档表名找不到同名 sheet,最接近的疑似改名
  MISSING_TABLE 文档声明表、xlsx 无 sheet
抓什么(advisory,需人判):
  DOMAIN       字段声明域(0/1、1~5 这类可解析的)与实际数据不符;给越界样例,human 判真伪

不抓(留给 value-integrity 工具,另做):跨表外键解析 / 验收用例字面值对账 / *Percentage 单调。

xlsx 读取复用 xlsx_dump(zipfile+ElementTree,绕开 openpyxl 对国产导表 xlsx 的样式报错)。
无项目硬编码,路径全走 argv。

用法:
  python config_check.py <config-spec.md> <config.xlsx>
  退出码: 有 major/MISSING_TABLE → 1,否则 0(advisory/info 不致失败)。
"""
import sys, os, re, zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import xlsx_dump as X


# ---------------------------------------------------------------- 域解析
def parse_domain(s):
    """把声明域解析成 ('enum', {..}) / ('range', lo, hi) / None。
    严格锚定:只认纯整数斜杠枚举与 a~b 范围;带文字/省略/口径一律 None(避免误报)。"""
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


# ---------------------------------------------------------------- xlsx 解析
def _cell(row, i):
    return row[i] if i < len(row) else ""


def parse_xlsx_sheet(rows):
    """rows: 行列表(字符串)。自描述表头:行1=表名 行2=类型 行3=字段key(数组 field[…]) 行4=中文 行5+=数据。
    返回 {table, fields:{name:{type,is_array,vals}}}。数组列归一为单逻辑字段;空(合并)列跳过;
    标量字段采集去重 int 数据域(string 列 → vals=[])。"""
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
            if "]" in nm:          # 闭合:简单数组 `]` 或对象数组 `max}]`
                in_array, cur = False, None
            continue
        if not nm:
            continue                       # 合并/空列
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
                break                       # 非 int(string 列)→ 不做域检
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


# ---------------------------------------------------------------- config-spec.md 解析
def parse_config_md(text):
    """带 backtick 表名的 `## 段` + 其后字段表 → {code:{fields:{name:{type,value,range,ref,is_array}}}}。
    字段表列按表头名(字段/类型/取值/范围/引用)定位,容忍列序与缺列;数组字段名归一。"""
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
        if code and st.startswith("|") and "字段" in st:
            header = [c.strip() for c in st.strip("|").split("|")]
            idx = {}
            for key in ("字段", "类型", "取值", "范围", "引用"):
                idx[key] = next((j for j, h in enumerate(header) if key in h), None)
            i += 1
            if i < n and set(lines[i].strip()) <= set("|-: "):   # 分隔行
                i += 1
            fields = {}
            while i < n and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]

                def cg(key, _cells=cells):
                    j = idx[key]
                    return _cells[j] if (j is not None and j < len(_cells)) else "—"

                raw = cg("字段")
                base = raw.split("[")[0].strip()
                if base and base != "字段":
                    typ = cg("类型")
                    fields[base] = {"type": typ.replace("[]", "").strip(),
                                    "value": cg("取值"), "range": cg("范围"),
                                    "ref": cg("引用"),
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
                                 "msg": "文档表名 '%s' 无同名 sheet;最接近 '%s'(疑改名,需同步)" % (code, xname)})
        if xname is None:
            findings.append({"sev": "major", "kind": "MISSING_TABLE", "table": code, "field": None,
                             "msg": "文档声明表 '%s',xlsx 无对应 sheet" % code})
            continue
        used.add(xname)
        xfields = xlsx[xname]["fields"]

        for fn in sorted(dfields):
            if fn not in xfields:
                findings.append({"sev": "major", "kind": "MISSING_COL", "table": code, "field": fn,
                                 "msg": "文档声明字段 '%s.%s',xlsx 无此列" % (code, fn)})
        for fn in sorted(xfields):
            if fn not in dfields:
                findings.append({"sev": "major", "kind": "UNDOC_COL", "table": code, "field": fn,
                                 "msg": "xlsx '%s' 有列 '%s',配置说明未记录(疑后改 xlsx 未回写文档)" % (xname, fn)})
        for fn in sorted(dfields):
            if fn not in xfields:
                continue
            dt, xt = dfields[fn]["type"], xfields[fn]["type"]
            # 数组/对象数组(混合子类型)无单一标量类型可比,跳过 TYPE 检查
            if not (dfields[fn].get("is_array") or xfields[fn].get("is_array")) and dt and xt and dt != xt:
                findings.append({"sev": "major", "kind": "TYPE", "table": code, "field": fn,
                                 "msg": "字段 '%s.%s' 类型不一致: 文档=%s xlsx=%s" % (code, fn, dt, xt)})
            if not xfields[fn]["is_array"]:
                dv, dr = dfields[fn].get("value", ""), dfields[fn].get("range", "")
                dom = parse_domain(dv) or parse_domain(dr)
                vals = xfields[fn].get("vals") or []
                if dom and vals:
                    bad = _domain_violations(dom, vals)
                    if bad:
                        decl = dv if parse_domain(dv) else dr
                        more = " …共%d个" % len(bad) if len(bad) > 5 else ""
                        findings.append({"sev": "advisory", "kind": "DOMAIN", "table": code, "field": fn,
                                         "msg": "字段 '%s.%s' 声明域 '%s',实际越界样例: %s%s" % (
                                             code, fn, decl, ",".join(str(b) for b in bad[:5]), more)})

    for t in sorted(xlsx):
        if t not in used:
            findings.append({"sev": "info", "kind": "UNDOC_TABLE", "table": t, "field": None,
                             "msg": "xlsx sheet '%s' 在配置说明中无对应表段" % t})
    return findings


def check(md_path, xlsx_path):
    with open(md_path, encoding="utf-8") as f:
        doc = parse_config_md(f.read())
    return diff(doc, read_xlsx(xlsx_path))


# ---------------------------------------------------------------- report / main
_SEV_ORDER = {"major": 0, "advisory": 1, "info": 2}


def format_report(findings, md_path, xlsx_path):
    out = ["配置说明 ↔ xlsx schema 漂移校验",
           "  配置说明: %s" % md_path,
           "  xlsx    : %s" % xlsx_path, ""]
    if not findings:
        out.append("✓ 无漂移:列 / 类型 / 表名一致,可解析域无越界。")
        return "\n".join(out)
    by_tbl = {}
    for f in findings:
        by_tbl.setdefault(f["table"] or "(其他)", []).append(f)
    n_major = sum(1 for f in findings if f["sev"] == "major")
    n_adv = sum(1 for f in findings if f["sev"] == "advisory")
    n_info = sum(1 for f in findings if f["sev"] == "info")
    out.append("发现 %d 条(major=%d advisory=%d info=%d):" % (len(findings), n_major, n_adv, n_info))
    out.append("")
    tag = {"major": "[major]", "advisory": "[advisory]", "info": "[info]"}
    for tbl in sorted(by_tbl):
        out.append("● %s" % tbl)
        for f in sorted(by_tbl[tbl], key=lambda x: (_SEV_ORDER[x["sev"]], x["kind"], x["field"] or "")):
            out.append("    %-10s %-13s %s" % (tag[f["sev"]], f["kind"], f["msg"]))
        out.append("")
    out.append("major 须回写文档/改 xlsx 后重跑;advisory 请人工判定声明域是否只是简写。")
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
