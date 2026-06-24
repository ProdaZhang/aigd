# -*- coding: utf-8 -*-
"""Tool 6 - manifest_check -- internal-consistency validator for the spine manifest.md (pure stdlib).

Why it exists: the manifest is the spine (A system list + dependency graph / B range registry / C cross-layer index /
D freeze ledger + recheck / E rollback record / F shared sources of truth), 6 strongly-typed tables all hand-written in markdown,
and cross-table references (A table R-ModuleCode <-> B table Range, A table Deps <-> A table systems, A table systems <-> C table blocks,
A<->A dependency cycles) are unchecked by machine. config_check/value_check cover "config <-> doc"; this script covers "is the spine self-consistent".

What it catches (major, gates):
  SEG_MISSING   an A-table system's R-ModuleCode is not found in the B-table Range registry -- code claimed but not registered / registry row missing
  DANGLING_DEP  an explicit system ID (S\\d+) in the A-table "Deps (upstream)" does not exist in the A table -- points to a non-existent system
  BAD_STATUS    a status value in tables A/D/E is not in the status enum (Final* is normalized to Final)
  NO_CBLOCK     an A-table system has no `### <ID>` cross-layer index block in the C table -- artifacts scattered and unregistered
What it catches (advisory, needs human judgment):
  CYCLE         the dependency graph (edges by system name/ID, self-loops excluded) has a cycle -- prompts that common types must first be registered in the global spec to break the cycle
  DEFINED_NO_CONTRACT  a Final/Final* system's C-table block lacks a proto or acceptance line (a finalized system should have handoff artifacts)
  SEG_UNUSED    the B table registers a ModuleCode but no A-table system uses it -- a range left hanging / system deleted
  CBLOCK_ORPHAN the C table has a block but the A table has no such system -- system deleted without deleting the index
info:
  DEP_BY_NAME   dependency edges resolved by system name (the real manifest Deps column is prose) -- transparent declaration that edges are wired by name this run

What it does not catch (left to humans / too free-form, would false-positive): D-table "Recheck trigger" <-> F-table registry reconciliation (trigger items
include point-to-point spec, not all broadcast sources, so machine checks would false-positive en masse); pairwise non-collision of Range numeric intervals (the B table already ships a `sample` placeholder).

Consistent with config_check/value_check by design: argv-driven, zero project hard-coding, deterministic, prefers under-reporting to false-positives.

Usage:
  python manifest_check.py <manifest.md>
  Exit code: any major -> 1, otherwise 0 (advisory/info do not cause failure).
"""
import sys, os, re

STATUS_ENUM = {"Draft", "Playtesting", "Final", "Recheck"}
_SYS_ID_RE = re.compile(r"\bS\d{1,3}\b")
_RCODE_RE = re.compile(r"R-[A-Z][A-Z0-9]*")   # ModuleCode token (all-uppercase ASCII); one system may have multiple codes (e.g. R-FOO / R-BAR)
_SPLIT_RE = re.compile(r"(?<!\\)\|")


# ---------------------------------------------------------------- markdown table parsing
def _split_row(line):
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c.replace("\\|", "|").strip() for c in _SPLIT_RE.split(s)]


def _is_sep(line):
    body = line.strip().strip("|")
    return bool(body) and set(body) <= set("-:| ") and "-" in body


def parse_md_tables(text):
    """Consecutive | lines form one table: first row is the header, the next row (if it is ---|---) is the separator and skipped, the rest are data rows."""
    tables = []
    lines = text.splitlines()
    i, n = 0, len(lines)
    while i < n:
        if lines[i].lstrip().startswith("|"):
            block = []
            while i < n and lines[i].lstrip().startswith("|"):
                block.append(lines[i])
                i += 1
            header = _split_row(block[0])
            start = 2 if len(block) > 1 and _is_sep(block[1]) else 1
            rows = [_split_row(b) for b in block[start:]]
            tables.append({"header": header, "rows": rows})
        else:
            i += 1
    return tables


def _col(header, *keys):
    for k in keys:
        for j, h in enumerate(header):
            if k in h:
                return j
    return None


def _pick(tables, *keys):
    """Take the first table whose header contains all keys."""
    for t in tables:
        if all(_col(t["header"], k) is not None for k in keys):
            return t
    return None


def _cell(row, i):
    return row[i] if (i is not None and i < len(row)) else ""


def _norm_status(s):
    """Strip markdown emphasis/backticks/ledger asterisks -> a plain status word."""
    return (s or "").replace("**", "").replace("`", "").replace("*", "").strip()


def _names_in_text(text, names):
    """Which system names (set) appear in the text. Longer names are masked first, so a short name is not falsely matched by a long one
    (e.g. the system name "main" is a substring of "main quest" -> mentioning main quest should not falsely wire a main edge)."""
    found, tmp = set(), text
    for nm in sorted(names, key=len, reverse=True):
        if nm and nm in tmp:
            found.add(nm)
            tmp = tmp.replace(nm, "\x00" * len(nm))   # mask the already-matched long name, so short substrings do not match again
    return found


def _is_placeholder(s):
    s = (s or "").strip()
    return (not s) or s in {"—", "-"} or (s.startswith("<") and s.endswith(">"))


# ---------------------------------------------------------------- C-table block parsing
def parse_c_blocks(text):
    """`### <ID> <name>` starts a block, the body runs to the next ###/##/#. Returns {id:{name,body}}."""
    blocks = {}
    lines = text.splitlines()
    cur_id = cur_name = None
    buf = []

    def flush():
        if cur_id:
            blocks[cur_id] = {"name": cur_name, "body": "\n".join(buf)}

    for ln in lines:
        st = ln.strip()
        if st.startswith("### "):
            flush()
            buf = []
            head = st[4:].strip()
            m = _SYS_ID_RE.search(head)
            cur_id = m.group(0) if m else None
            cur_name = head
        elif re.match(r"^#{1,3} ", st):   # back to ###/##/# at the same level or higher -> end the current block
            flush()
            cur_id = cur_name = None
            buf = []
        else:
            if cur_id:
                buf.append(ln)
    flush()
    return blocks


# ---------------------------------------------------------------- main check
def check_text(text):
    findings = []
    tables = parse_md_tables(text)

    A = _pick(tables, "SystemID")
    B = _pick(tables, "ModuleCode", "Range")
    D = _pick(tables, "Recheck")
    E = _pick(tables, "FromStatus")

    if not A:
        return [{"sev": "major", "kind": "NO_A_TABLE", "where": "manifest",
                 "msg": "A table not found (system list, header must contain 'SystemID') -- this is not a valid manifest or the header was broken"}]

    # ---- A-table extraction ----
    aid = _col(A["header"], "SystemID")
    aname = _col(A["header"], "Name")
    astat = _col(A["header"], "Status")
    acode = _col(A["header"], "ModuleCode")
    adep = _col(A["header"], "Deps")

    sys_ids, sys_names, sys_status, sys_code, sys_dep = [], {}, {}, {}, {}
    for r in A["rows"]:
        sid = _cell(r, aid).replace("`", "").strip()
        if _is_placeholder(sid) or not _SYS_ID_RE.match(sid):
            continue
        sys_ids.append(sid)
        nm = _cell(r, aname).replace("`", "").replace("*", "").strip()
        sys_names[sid] = nm
        sys_status[sid] = _norm_status(_cell(r, astat))
        sys_code[sid] = _RCODE_RE.findall(_cell(r, acode))   # one system may have multiple codes (e.g. R-FOO / R-BAR)
        sys_dep[sid] = _cell(r, adep)
    id_set = set(sys_ids)
    name_to_id = {n: i for i, n in sys_names.items() if n}

    # ---- B-table Range registry ----
    b_codes = set()
    if B:
        bcode = _col(B["header"], "ModuleCode")
        for r in B["rows"]:
            c = _cell(r, bcode).replace("`", "").strip()
            if not _is_placeholder(c):
                b_codes.add(c)

    # (1) SEG_MISSING / SEG_UNUSED: A-table ModuleCode <-> B-table registry (one system may have multiple codes)
    used_codes = set()
    for sid in sys_ids:
        for code in sys_code.get(sid, []):
            used_codes.add(code)
            if B and code not in b_codes:
                findings.append({"sev": "major", "kind": "SEG_MISSING", "where": "A->B table",
                                 "msg": "system %s (%s) ModuleCode '%s' not found in the B-table Range registry" % (sid, sys_names.get(sid, ""), code)})
    for c in sorted(b_codes - used_codes):
        findings.append({"sev": "advisory", "kind": "SEG_UNUSED", "where": "B table",
                         "msg": "B table registers ModuleCode '%s', no A-table system uses it (range left hanging or system deleted)" % c})

    # (2) status enum: tables A / D / E
    for sid in sys_ids:
        s = sys_status.get(sid, "")
        if s and s not in STATUS_ENUM:
            findings.append({"sev": "major", "kind": "BAD_STATUS", "where": "A table",
                             "msg": "system %s status '%s' not in the status enum %s" % (sid, s, "/".join(sorted(STATUS_ENUM)))})
    if D:
        dstat = _col(D["header"], "Status")
        dsysc = _col(D["header"], "System")
        for r in D["rows"]:
            s = _norm_status(_cell(r, dstat))
            who = _cell(r, dsysc).replace("`", "").strip()
            if _is_placeholder(s):
                continue                              # placeholder rows (— / empty) are not checked
            if s and s not in STATUS_ENUM:
                findings.append({"sev": "major", "kind": "BAD_STATUS", "where": "D table",
                                 "msg": "D table '%s' status '%s' not in the status enum" % (who, s)})
    if E:
        etrans = _col(E["header"], "FromStatus")
        for r in E["rows"]:
            cell = _cell(r, etrans)
            if _is_placeholder(cell):
                continue                              # placeholder rows (— / empty, "no rollback") are not checked
            for part in re.split(r"→|->", cell):
                s = _norm_status(part)
                if _is_placeholder(s):
                    continue
                if s and s not in STATUS_ENUM:
                    findings.append({"sev": "major", "kind": "BAD_STATUS", "where": "E table",
                                     "msg": "E table status transition '%s' contains '%s' not in the status enum" % (cell.strip(), s)})

    # (3) dependency resolution: DANGLING_DEP (explicit ID) + wire edges by name (for cycle detection)
    edges = {}   # sid -> set(upstream sid)
    dep_by_name = False
    for sid in sys_ids:
        cell = sys_dep.get(sid, "")
        ups = set()
        for tok in _SYS_ID_RE.findall(cell):       # explicit ID reference
            if tok == sid:
                continue
            if tok in id_set:
                ups.add(tok)
            else:
                findings.append({"sev": "major", "kind": "DANGLING_DEP", "where": "A table",
                                 "msg": "system %s depends on '%s', but the A table has no such system" % (sid, tok)})
        for nm in _names_in_text(cell, name_to_id):   # wire edges by system name (the real manifest Deps column is prose; longer names masked first)
            nid = name_to_id[nm]
            if nid == sid:
                continue
            ups.add(nid)
            dep_by_name = True
        edges[sid] = ups
    if dep_by_name:
        findings.append({"sev": "info", "kind": "DEP_BY_NAME", "where": "A table",
                         "msg": "some dependency edges resolved from the prose Deps column by system name (not explicit IDs); cycle detection wires edges accordingly"})

    # (4) CYCLE: mutually-dependent clusters in the dependency graph (SCC, advisory -- common types must first be registered in the global spec to break the cycle)
    #    Uses strongly connected components rather than cycle enumeration: each mutually-dependent cluster is reported once (complete, non-redundant, no combinatorial blowup)
    for comp in _find_cyclic_clusters(edges):
        nodes = sorted(comp)
        label = " . ".join("%s(%s)" % (i, sys_names.get(i, "")) for i in nodes)
        cyc = _sample_cycle(edges, set(comp))
        sample = (" -> ".join(cyc)) if cyc else "(self-loop/multiple cycles)"
        findings.append({"sev": "advisory", "kind": "CYCLE", "where": "A-table dependency graph",
                         "msg": "mutually-dependent cluster {%s} forms a cycle (sample %s) -- common types must first be registered in the global spec (project layer) to break the cycle, sinking proto/common at handoff" % (label, sample)})

    # (5) C-table blocks: NO_CBLOCK / CBLOCK_ORPHAN / DEFINED_NO_CONTRACT
    cblocks = parse_c_blocks(text)
    for sid in sys_ids:
        if sid not in cblocks:
            findings.append({"sev": "major", "kind": "NO_CBLOCK", "where": "A->C table",
                             "msg": "system %s (%s) has no `### %s` cross-layer index block in the C table" % (sid, sys_names.get(sid, ""), sid)})
            continue
        if sys_status.get(sid) == "Final":          # includes Final* (already normalized)
            body = cblocks[sid]["body"]
            miss = []
            if "proto" not in body and "contract" not in body:
                miss.append("proto/contract")
            if "acceptance" not in body:
                miss.append("acceptance")
            if miss:
                findings.append({"sev": "advisory", "kind": "DEFINED_NO_CONTRACT", "where": "C table %s" % sid,
                                 "msg": "Final system %s (%s) C block lacks %s line(s) (a finalized system should have handoff artifacts)" % (
                                     sid, sys_names.get(sid, ""), ", ".join(miss))})
    for cid in sorted(cblocks):
        if cid not in id_set:
            findings.append({"sev": "advisory", "kind": "CBLOCK_ORPHAN", "where": "C table %s" % cid,
                             "msg": "C table has block '%s' (%s), A table has no such system (deleted system without deleting the index?)" % (cid, cblocks[cid]["name"])})
    return findings


def _find_cyclic_clusters(edges):
    """Tarjan strongly connected components, returns each SCC of size>1 (list of nodes).
    More suitable here than "cycle enumeration": each mutually-dependent cluster is reported exactly once, neither missing
    (colored DFS misses cycles formed by cross edges) nor redundant (enumeration would report multiple overlapping cycles for the same cluster), with no combinatorial blowup."""
    index, low, onstack, stk, sccs = {}, {}, {}, [], []
    counter = [0]

    def strong(v):
        index[v] = low[v] = counter[0]
        counter[0] += 1
        stk.append(v)
        onstack[v] = True
        for w in edges.get(v, ()):
            if w not in edges:
                continue
            if w not in index:
                strong(w)
                low[v] = min(low[v], low[w])
            elif onstack.get(w):
                low[v] = min(low[v], index[w])
        if low[v] == index[v]:
            comp = []
            while True:
                w = stk.pop()
                onstack[w] = False
                comp.append(w)
                if w == v:
                    break
            if len(comp) > 1:
                sccs.append(sorted(comp))
    for v in edges:
        if v not in index:
            strong(v)
    return sccs


def _sample_cycle(edges, comp):
    """Find one representative cycle within an SCC (from the smallest node back to itself), for readable reporting. best-effort."""
    start = sorted(comp)[0]
    stack = [(start, [start])]
    seen = set()
    while stack:
        node, path = stack.pop()
        for w in sorted(edges.get(node, ())):
            if w not in comp:
                continue
            if w == start and len(path) >= 2:
                return path + [start]
            if w not in seen:
                seen.add(w)
                stack.append((w, path + [w]))
    return None


def check(path):
    with open(path, encoding="utf-8") as f:
        return check_text(f.read())


# ---------------------------------------------------------------- report / main
_SEV_ORDER = {"major": 0, "advisory": 1, "info": 2}


def format_report(findings, path):
    out = ["spine manifest internal-consistency validation", "  manifest: %s" % path, ""]
    if not findings:
        out.append("OK self-consistent: ModuleCodes all registered / no dangling deps / statuses valid / every system has a C block / no dependency cycles.")
        return "\n".join(out)
    n_major = sum(1 for f in findings if f["sev"] == "major")
    n_adv = sum(1 for f in findings if f["sev"] == "advisory")
    n_info = sum(1 for f in findings if f["sev"] == "info")
    out.append("found %d (major=%d advisory=%d info=%d):" % (len(findings), n_major, n_adv, n_info))
    out.append("")
    by_where = {}
    for f in findings:
        by_where.setdefault(f["where"], []).append(f)
    tag = {"major": "[major]", "advisory": "[advisory]", "info": "[info]"}
    for w in sorted(by_where):
        out.append("* %s" % w)
        for f in sorted(by_where[w], key=lambda x: (_SEV_ORDER[x["sev"]], x["kind"])):
            out.append("    %-10s %-18s %s" % (tag[f["sev"]], f["kind"], f["msg"]))
        out.append("")
    out.append("major must be fixed in the spine and re-run; advisory/info need human judgment (cycle = whether already globally registered to break it; DEP_BY_NAME = transparent declaration).")
    return "\n".join(out)


def main(argv):
    if len(argv) < 2:
        sys.stderr.write("usage: python manifest_check.py <manifest.md>\n")
        return 2
    path = argv[1]
    findings = check(path)
    sys.stdout.buffer.write((format_report(findings, path) + "\n").encode("utf-8"))
    return 1 if any(f["sev"] == "major" for f in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
