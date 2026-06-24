# -*- coding: utf-8 -*-
"""Portable xlsx dumper -- zipfile + ElementTree.

Why not openpyxl: many domestic table-export tools produce xlsx files that make
openpyxl raise `Colors must be aRGB hex values`. This script bypasses the style
sheet and parses the XML directly.

Usage:
  python xlsx_dump.py <file.xlsx> [out.txt] [max_rows]
    - with out.txt -> write a UTF-8 file (always write Chinese to a file before
      viewing; printing directly to the console may show garbled text)
    - without out  -> output to stdout (UTF-8 bytes)
    - max_rows     -> take the first N rows per sheet (default 60), enough to see
      the self-describing header + samples

Self-describing header convention (row1=English table name / row2=type /
row3=field key (array field[...]) / row4=Chinese name / row5+=data).
No project hard-coding: all paths come from argv.
"""
import zipfile, re, os, sys
import xml.etree.ElementTree as ET

NS  = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
RNS = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"

def col_letters(ref):
    m = re.match(r"([A-Z]+)\d+", ref); return m.group(1) if m else "A"

def col_to_idx(letters):
    n = 0
    for ch in letters: n = n*26 + (ord(ch)-ord('A')+1)
    return n-1  # 0-based

def load_shared_strings(z):
    out = []
    try: data = z.read("xl/sharedStrings.xml")
    except KeyError: return out
    for si in ET.fromstring(data).findall(f"{NS}si"):
        out.append("".join(t.text or "" for t in si.iter(f"{NS}t")))
    return out

def sheet_map(z):
    """[(display name, sheet xml path)], in workbook order."""
    wb   = ET.fromstring(z.read("xl/workbook.xml"))
    rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    rid  = {r.get("Id"): r.get("Target") for r in rels}
    out = []
    for sh in wb.find(f"{NS}sheets").findall(f"{NS}sheet"):
        tgt = rid.get(sh.get(f"{RNS}id"), "")
        tgt = tgt.lstrip("/") if tgt.startswith("/") else "xl/" + tgt
        out.append((sh.get("name"), tgt))
    return out

def read_rows(z, path, shared, max_rows=None):
    sd = ET.fromstring(z.read(path)).find(f"{NS}sheetData"); rows = []
    if sd is None: return rows
    for r in sd.findall(f"{NS}row"):
        if max_rows is not None and len(rows) >= max_rows: break
        cells = {}; mx = -1
        for c in r.findall(f"{NS}c"):
            ci = col_to_idx(col_letters(c.get("r", "A1"))); t = c.get("t"); val = ""
            if t == "s":
                v = c.find(f"{NS}v"); val = shared[int(v.text)] if v is not None and v.text else ""
            elif t == "inlineStr":
                ie = c.find(f"{NS}is"); val = "".join((x.text or "") for x in ie.iter(f"{NS}t")) if ie is not None else ""
            else:
                v = c.find(f"{NS}v"); val = v.text if v is not None and v.text else ""
            cells[ci] = val; mx = max(mx, ci)
        rows.append([cells.get(i, "") for i in range(mx+1)])
    return rows

def dump(path, max_rows=60):
    z = zipfile.ZipFile(path); shared = load_shared_strings(z)
    lines = [f"===== FILE: {os.path.basename(path)} ====="]
    sheets = sheet_map(z)
    lines.append(f"sheets ({len(sheets)}): " + ", ".join(n for n, _ in sheets)); lines.append("")
    for name, sp in sheets:
        rows = read_rows(z, sp, shared, max_rows)
        lines.append(f"----- SHEET: {name} ({sp}) rows={len(rows)} -----")
        for i, row in enumerate(rows): lines.append(f"[r{i+1}] " + "\t".join(row))
        lines.append("")
    z.close(); return "\n".join(lines)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: python xlsx_dump.py <file.xlsx> [out.txt] [max_rows]"); sys.exit(1)
    src = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else None
    mr  = int(sys.argv[3]) if len(sys.argv) > 3 else 60
    txt = dump(src, mr)
    if out:
        with open(out, "w", encoding="utf-8") as f: f.write(txt)
        print("written:", out)
    else:
        sys.stdout.buffer.write(txt.encode("utf-8"))
