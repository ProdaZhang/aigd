# -*- coding: utf-8 -*-
"""manifest_check.py 测试 —— 纯 stdlib(逻辑层用内存 markdown 串夹具)。
跑法: python test_manifest_check.py
真·pilot manifest 集成测试在文件缺失时优雅跳过。
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import manifest_check as M


def _kinds(findings):
    return [f["kind"] for f in findings]


# ---------- markdown 表解析 ----------

def test_parse_md_tables_basic():
    txt = "前言\n\n| a | b |\n|---|---|\n| 1 | 2 |\n| 3 | 4 |\n\n尾巴\n"
    ts = M.parse_md_tables(txt)
    assert len(ts) == 1
    assert ts[0]["header"] == ["a", "b"]
    assert ts[0]["rows"] == [["1", "2"], ["3", "4"]]

def test_split_row_unescapes_pipe():
    # 内容里转义的 \| 不该切列
    assert M._split_row(r"| x = a\|b | y |") == ["x = a|b", "y"]

def test_norm_status_strips_star_and_emphasis():
    assert M._norm_status("定稿*") == "定稿"
    assert M._norm_status("**试玩中**") == "试玩中"
    assert M._norm_status("`草稿`") == "草稿"


# ---------- C 表分块 ----------

def test_parse_c_blocks():
    txt = "## C. 跨层索引\n\n### S01 物品\n- proto: x\n- 验收: y\n\n### S02 主角\n- 规则\n\n## D. 别的\n"
    b = M.parse_c_blocks(txt)
    assert set(b) == {"S01", "S02"}
    assert "proto" in b["S01"]["body"]
    assert "验收" not in b["S02"]["body"]


# ---------- 完整 manifest:干净样例 0 major ----------

_CLEAN = """# manifest
## 状态枚举
`草稿` → `试玩中` → `定稿` → `待重验`。

## A. 系统清单 + 依赖图
| 系统ID | 系统名 | 区-子-系统目录 | 状态 | R-模块码 | 依赖(上游) | 被依赖(下游) |
|--------|--------|----------------|------|----------|-----------|-------------|
| S01 | 物品 | 05-01-02 | 定稿* | R-ITEM | (无上游;邮件 [外部]) | 广播(见 F) |
| S02 | 装备 | 02-02-01 | 草稿 | R-EQUIP | 物品[广播](分解道具) | 战斗[外部] |

## B. 号段
| 模块码 | 系统 | 协议号段 | 错误码段 | 备注 |
|--------|------|----------|----------|------|
| R-ITEM | 物品 | 1400–1499 | 14000– | x |
| R-EQUIP | 装备 | 1200–1299 | 12000– | x |

## C. 跨层索引
### S01 物品
- **契约(proto)**: proto/item.proto
- **验收**: item-验收.md
### S02 装备
- **规则(-01)**: docs/equip/rules.md

## D. 冻结账本
| 系统 | 状态 | 定稿时间 | 占用号段 | 待重验触发 |
|------|------|----------|----------|------------|
| S01 物品 | 定稿* | 2026-06-17 | 1400– | 挂账 |

## E. 回退记录
| 时间 | 系统 | 从状态 → 到状态 | 原因 | 受影响下游 |
|------|------|-----------------|------|------------|
| 2026-06-17 | S01 | 定稿* → 试玩中 | x | S02 |
"""

def test_clean_manifest_no_major():
    fs = M.check_text(_CLEAN)
    majors = [f for f in fs if f["sev"] == "major"]
    assert not majors, "干净 manifest 不应有 major: %r" % majors

def test_clean_dep_by_name_info():
    # 装备依赖列写「物品」(按名),应出 DEP_BY_NAME info
    assert "DEP_BY_NAME" in _kinds(M.check_text(_CLEAN))


# ---------- 各 major 都能抓 ----------

def test_seg_missing():
    # A 表 S02 模块码 R-GHOST,B 表没登记
    txt = _CLEAN.replace("| S02 | 装备 | 02-02-01 | 草稿 | R-EQUIP |", "| S02 | 装备 | 02-02-01 | 草稿 | R-GHOST |")
    fs = M.check_text(txt)
    assert any(f["kind"] == "SEG_MISSING" and f["sev"] == "major" for f in fs)

def test_dangling_dep_explicit_id():
    # 显式依赖 S99 不存在
    txt = _CLEAN.replace("| 物品[广播](分解道具) |", "| S99(不存在),物品 |")
    fs = M.check_text(txt)
    assert any(f["kind"] == "DANGLING_DEP" and "S99" in f["msg"] for f in fs)

def test_multi_code_both_registered_ok():
    # 一系统两段码 R-EQUIP / R-AUTO,B 表都登记 → 无 SEG_MISSING
    txt = _CLEAN.replace("| S02 | 装备 | 02-02-01 | 草稿 | R-EQUIP |",
                         "| S02 | 装备 | 02-02-01 | 草稿 | R-EQUIP / R-AUTO |")
    txt = txt.replace("| R-EQUIP | 装备 | 1200–1299 | 12000– | x |",
                      "| R-EQUIP | 装备 | 1200–1299 | 12000– | x |\n| R-AUTO | 装备 | 1300– | 13000– | x |")
    assert not any(f["kind"] == "SEG_MISSING" for f in M.check_text(txt))

def test_multi_code_one_missing_flagged():
    # 两段码但 R-AUTO 没在 B 表登记 → 只 R-AUTO 报 SEG_MISSING
    txt = _CLEAN.replace("| S02 | 装备 | 02-02-01 | 草稿 | R-EQUIP |",
                         "| S02 | 装备 | 02-02-01 | 草稿 | R-EQUIP / R-AUTO |")
    seg = [f for f in M.check_text(txt) if f["kind"] == "SEG_MISSING"]
    assert len(seg) == 1 and "R-AUTO" in seg[0]["msg"]

def test_placeholder_status_rows_ok():
    # D/E 表占位行(— / 空,"暂无")不应误报 BAD_STATUS
    txt = _CLEAN + ("\n## E. 回退记录\n| 时间 | 系统 | 从状态 → 到状态 | 原因 | 受影响下游 |\n"
                    "|--|--|--|--|--|\n| — | — | — | — | — |\n")
    assert not any(f["kind"] == "BAD_STATUS" for f in M.check_text(txt))

def test_bad_status():
    txt = _CLEAN.replace("| S02 | 装备 | 02-02-01 | 草稿 |", "| S02 | 装备 | 02-02-01 | 已上线 |")
    fs = M.check_text(txt)
    assert any(f["kind"] == "BAD_STATUS" and f["sev"] == "major" for f in fs)

def test_no_cblock():
    # 删掉 S02 的 C 分块
    txt = _CLEAN.replace("### S02 装备\n- **规则(-01)**: docs/equip/rules.md\n", "")
    fs = M.check_text(txt)
    assert any(f["kind"] == "NO_CBLOCK" and "S02" in f["msg"] for f in fs)

def test_cycle_detected():
    # 让 S01 也依赖装备 → 物品↔装备 成环
    txt = _CLEAN.replace("| (无上游;邮件 [外部]) |", "| 装备(反向依赖) |")
    fs = M.check_text(txt)
    assert any(f["kind"] == "CYCLE" and f["sev"] == "advisory" for f in fs)

def test_names_in_text_substring_guard():
    # 「主线」是「主线任务」的子串:文本只提主线任务,不该命中主线
    assert M._names_in_text("自动完成主线任务", {"主线", "主线任务"}) == {"主线任务"}
    # 两者都独立出现则都命中
    assert M._names_in_text("主线关卡 + 主线任务链", {"主线", "主线任务"}) == {"主线", "主线任务"}

def test_no_self_cycle_from_own_name():
    # S01 依赖列含自己的名字「物品」不该成自环 major/CYCLE
    txt = _CLEAN.replace("| (无上游;邮件 [外部]) |", "| 物品仓库内部流转 |")
    fs = M.check_text(txt)
    assert not any(f["kind"] == "CYCLE" for f in fs)

def test_defined_no_contract():
    # S01 定稿* 但 C 分块抽掉 proto + 验收
    txt = _CLEAN.replace("- **契约(proto)**: proto/item.proto\n- **验收**: item-验收.md", "- **规则**: x")
    fs = M.check_text(txt)
    assert any(f["kind"] == "DEFINED_NO_CONTRACT" for f in fs)

def test_seg_unused():
    # B 表多登记一个没人用的码
    txt = _CLEAN.replace("| R-EQUIP | 装备 | 1200–1299 | 12000– | x |",
                         "| R-EQUIP | 装备 | 1200–1299 | 12000– | x |\n| R-ORPHAN | 幽灵 | 9000– | 90000– | x |")
    fs = M.check_text(txt)
    assert any(f["kind"] == "SEG_UNUSED" and "R-ORPHAN" in f["msg"] for f in fs)

def test_cblock_orphan():
    txt = _CLEAN + "\n### S77 幽灵系统\n- 残留索引\n"
    fs = M.check_text(txt)
    assert any(f["kind"] == "CBLOCK_ORPHAN" and "S77" in f["msg"] for f in fs)

def test_no_a_table():
    fs = M.check_text("# 不是 manifest\n\n| x | y |\n|---|---|\n| 1 | 2 |\n")
    assert any(f["kind"] == "NO_A_TABLE" for f in fs)

def test_deterministic():
    assert M.check_text(_CLEAN) == M.check_text(_CLEAN)


# ---------- 集成: 真·pilot manifest(缺文件则跳过) ----------

def test_integration_pilot_no_major():
    here = os.path.dirname(__file__)
    root = os.path.abspath(os.path.join(here, "..", "..", "..", "..", "..", ".."))
    path = os.path.join(root, ".uploads", "aigd-pilot", "manifest.md")
    if not os.path.exists(path):
        print("  (skip integration: 缺 pilot manifest)"); return
    majors = [f for f in M.check(path) if f["sev"] == "major"]
    assert not majors, "pilot manifest 不应有 major: %r" % majors


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
