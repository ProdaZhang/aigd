import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import ui_render as R

SAMPLE = '''# EXAMPLE-01 · 示例 · 测试屏

> 用途: 测试用(blockquote 元数据不该被解析)

## 配色板 (可选提示)
主强调 品红 #e848a0

## Layout (层级树: 元素 :id [类型] @{x y w h})

```
返回            :back     [按钮]   @{1.8 4.9 4.8 5.3} z=6      "◁"
难度·VIII       :nodeVIII [按钮]   @{4 36 6 10.3} z=6 [选中] "VIII"
中央背景art     :heroArt  [背景槽] @{0 0 100 100} z=1  "底图·换素材"
词缀×3                   [文本]   @{70 51 28 12} z=4        "debuff"
进入            :enter[按钮·主] @{80 90 18 9} z=6            "进入"
每周进展        :weekly   [数值条] @{43 86 24 7} z=6         "每周进展 8000/8000"
```

## Events

```
点击 返回 -> 上级
```

## 设计点评 (检索面)
- 这是点评,不该被解析成元素或事件
'''


def test_parse_basic():
    d = R.parse_dsl(SAMPLE)
    assert d["screen"].startswith("EXAMPLE-01")
    assert d["palette"] and "品红" in d["palette"]
    ids = [e["id"] for e in d["elements"]]
    assert ids == ["back", "nodeVIII", "heroArt", None, "enter", "weekly"], ids
    back = d["elements"][0]
    assert back["type"] == "按钮" and back["x"] == 1.8 and back["h"] == 5.3
    assert back["z"] == 6 and back["text"] == "◁" and back["state"] is None
    assert d["elements"][1]["state"] == "选中"
    assert d["elements"][3]["repeat"] == 3 and d["elements"][3]["type"] == "文本"
    enter = d["elements"][4]
    assert enter["id"] == "enter" and enter["type"] == "按钮·主" and enter["text"] == "进入"
    assert d["events"] == ["点击 返回 -> 上级"]


def test_parse_kind_and_size():
    d = R.parse_dsl("# M · 模块\n> 类型: 模块\n> 尺寸: 400×600\n\n## Layout\n\n```\nA :a [按钮] @{0 0 100 100} z=1\n```\n")
    assert d["kind"] == "模块"
    assert d["size"] == (400, 600)
    d2 = R.parse_dsl("# S · 屏\n\n## Layout\n\n```\nA :a [按钮] @{0 0 10 10} z=1\n```\n")
    assert d2["kind"] == "屏" and d2["size"] == (2400, 1080)   # 默认=横版手游基准


def test_recommend_size():
    assert R.recommend_size(1602, 932) == (1856, 1080)   # 横版:高锁1080,宽=round(1080*1602/932)
    assert R.recommend_size(1080, 2400) == (1080, 2400)   # 竖版:宽锁1080
    assert R.recommend_size(1000, 1000) == (1080, 1080)   # 方:按横版规则,高锁1080


def test_parse_imports():
    d = R.parse_dsl("# S\n\n## 引用\n\n资源栏 = ../modules/资源栏.module.md\n卡片 = ./card.md\n\n## Layout\n\n```\nA :a [按钮] @{0 0 10 10} z=1\n```\n")
    assert d["imports"] == {"资源栏": "../modules/资源栏.module.md", "卡片": "./card.md"}


def test_parse_two_value_geo():
    d = R.parse_dsl("# S\n\n## Layout\n\n```\n顶栏 :top [实例·资源栏] @{10 5} z=9\n```\n")
    e = d["elements"][0]
    assert e["x"] == 10.0 and e["y"] == 5.0 and e["w"] is None and e["h"] is None
    assert e["type"] == "实例·资源栏" and e["z"] == 9


def test_type_variant_abbr():
    import json as _j
    els = _j.loads(R._els_json(R.parse_dsl(SAMPLE)["elements"]))
    enter = [e for e in els if e["id"] == "enter"][0]
    assert enter["abbr"] == "anniu", enter["abbr"]


def test_render_html_l0():
    html = R.render_html(R.parse_dsl(SAMPLE))
    assert html.startswith("<!doctype html>")
    assert '"id": "nodeVIII"' in html or '"id":"nodeVIII"' in html
    assert "position:absolute" in html and "z-index:2" in html
    assert "EXAMPLE-01" in html
    assert "http://" not in html and "https://" not in html


def test_render_uses_declared_size():
    d = R.parse_dsl("# M · 模块\n> 类型: 模块\n> 尺寸: 400×600\n\n## Layout\n\n```\nA :a [按钮] @{0 0 100 100} z=1\n```\n")
    html = R.render_html(d)
    assert "width:400px;height:600px" in html and "{x:400,y:600}" in html
    svg = R.render_svg(d)
    assert 'viewBox="0 0 400 664"' in svg            # H+64
    assert 'width="400" height="600"' in svg          # 舞台矩形


def test_default_size_renders_2400x1080():
    d = R.parse_dsl("# S\n\n## Layout\n\n```\nA :a [按钮] @{0 0 10 10} z=1\n```\n")
    assert "width:2400px;height:1080px" in R.render_html(d)


def test_render_html_deterministic():
    p = R.parse_dsl(SAMPLE)
    assert R.render_html(p) == R.render_html(p)


def test_render_html_has_three_modes():
    html = R.render_html(R.parse_dsl(SAMPLE))
    for token in ["render('wire')", "render('skin')", "render('atmo')", "线稿", "皮肤", "氛围"]:
        assert token in html, token


def test_svg_chinese_label_and_container_no_center():
    dsl = "## Layout\n\n```\n顶栏          [容器] @{0 4 100 8}\n返回 :back [按钮] @{1 5 5 5} \"◁\"\n```\n"
    svg = R.render_svg(R.parse_dsl(dsl))
    assert "anniu" not in svg          # 标签用中文类型,不用拼音 abbr
    assert "·按钮" in svg and "·容器" in svg
    assert svg.count("顶栏") == 1      # 容器无文本→只左上角标签,不再居中重复


def test_shape_circle_only_when_declared():
    # 同样近方形:声明 形=圆 → 圆;未声明 → 仍方角(渲染器不靠纵横比猜)
    dsl = "## Layout\n\n```\n圆节点 :c [按钮] @{4 36 6 10} 形=圆 \"O\"\n方节点 :q [按钮] @{20 36 6 10} \"X\"\n```\n"
    svg = R.render_svg(R.parse_dsl(dsl))
    import re as _re
    rxc = float(_re.search(r'data-id="c"><rect[^>]*rx="([0-9.]+)"', svg).group(1))
    rxq = float(_re.search(r'data-id="q"><rect[^>]*rx="([0-9.]+)"', svg).group(1))
    assert rxc > 10, rxc       # 声明圆 → 大 rx(圆)
    assert rxq == 4.0, rxq     # 近方形但未声明 → 方角不变


def test_svg_legend_and_selected_state():
    svg = R.render_svg(R.parse_dsl(SAMPLE))   # nodeVIII 带 [选中] 态
    assert "选中态" in svg             # 图例
    assert "#e848a0" in svg            # 选中态品红描边/图例色


def test_svg_background_behind_foreground():
    svg = R.render_svg(R.parse_dsl(SAMPLE))
    assert svg.index('data-id="heroArt"') < svg.index('data-id="back"'), "全屏底图应先画(底层),前景后画"


def test_shuzhitiao_renders_bar():
    p = R.parse_dsl(SAMPLE)
    html = R.render_html(p)
    assert ".bar" in html and 'abbr==="shuzhitiao"' in html
    svg = R.render_svg(p)
    assert "data-bar" in svg and "每周进展" in svg


def test_calibration_export_present():
    html = R.render_html(R.parse_dsl(SAMPLE))
    for token in ["校准", "导出 DSL", "calib", "@{"]:
        assert token in html, token


def test_render_svg_and_determinism():
    p = R.parse_dsl(SAMPLE)
    svg = R.render_svg(p)
    assert svg.startswith("<svg") and "viewBox" in svg and "nodeVIII" in svg
    assert R.render_svg(p) == R.render_svg(p)


def test_sample_dsl_consistency():
    # 随包合规样例,自包含、不依赖项目实例路径
    here = os.path.dirname(__file__)
    path = os.path.join(here, "..", "..", "ui-dsl-example.md")
    assert os.path.exists(path), path
    d = R.parse_dsl(open(path, encoding="utf-8").read())
    ids = [e["id"] for e in d["elements"] if e["id"]]
    for must in ["back", "nodeVIII", "heroArt", "card", "enter", "reobserve", "weekly"]:
        assert must in ids, must
    he = [e for e in d["elements"] if e["id"] == "heroArt"][0]
    assert (he["x"], he["y"], he["w"], he["h"]) == (0.0, 0.0, 100.0, 100.0)


def test_cli_writes_files(tmp_path):
    src = tmp_path / "d.md"; src.write_text(SAMPLE, encoding="utf-8")
    out = tmp_path / "o.html"; svg = tmp_path / "o.svg"
    rc = R.main([str(src), str(out), "--svg", str(svg)])
    assert rc == 0 and out.exists() and svg.exists()
    assert out.read_bytes()[:3] != b"\xef\xbb\xbf"
    assert "<svg" in svg.read_text(encoding="utf-8")


def test_parse_skin_section():
    d = R.parse_dsl(
        "## Layout\n\n```\nA :a [按钮·主] @{0 0 10 10} z=1 \"A\"\n```\n\n"
        "## 皮肤\n\n# 注释行(# 起头)应跳过\n"
        "a       #112233 / #aabbcc\n"
        "按钮     #2b2f3a / #ffffff\n")
    sk = d["skin"]
    assert sk["a"] == {"fill": "#112233", "ink": "#aabbcc"}     # 按 id
    assert sk["按钮"] == {"fill": "#2b2f3a", "ink": "#ffffff"}  # 按类型
    assert "# 注释行" not in str(sk)                             # 注释跳过


def test_skin_section_applied_without_skin_flag():
    d = R.parse_dsl("## Layout\n\n```\nA :a [按钮] @{0 0 10 10} z=1 \"A\"\n```\n\n## 皮肤\n\na  #abcdef / #102030\n")
    assert "#abcdef" in R.render_svg(d)        # 皮肤段生效,无需 --skin
    assert "#abcdef" in R.render_html(d)


def test_type_keyed_theme_generalizes():
    # 主题按类型上色:两个按钮都吃 "按钮" 的色(design.md 风格泛化),变体 按钮·主 走基础类型回退
    d = R.parse_dsl("## Layout\n\n```\nA :a [按钮] @{0 0 10 10} z=1\nB :b [按钮·主] @{20 0 10 10} z=1\n```\n")
    theme = {"按钮": {"fill": "#123456", "ink": "#ffffff"}}
    els = __import__("json").loads(R._els_json(d["elements"], R._eff_skin(d, theme)))
    assert els[0]["fill"] == "#123456"         # 按钮 直接命中
    assert els[1]["fill"] == "#123456"         # 按钮·主 → 基础类型 按钮 回退命中


def test_canvas_key_themes_backdrop():
    # @canvas 保留键:套画布底色到 stage(html)/根矩形(svg),且不当作元素渲染
    d = R.parse_dsl("## Layout\n\n```\nA :a [文本] @{0 0 10 10} z=1 \"A\"\n```\n")
    theme = {"@canvas": {"fill": "#faf9f5", "ink": "#141413"}, "文本": {"fill": "", "ink": "#3d3d3a"}}
    html = R.render_html(d, theme)
    assert '"#faf9f5"' in html                       # CANVAS 常量注入
    svg = R.render_svg(d, theme)
    assert svg.count("#faf9f5") >= 1                 # 根矩形用画布色
    import json as _j
    ids = [e["id"] for e in _j.loads(R._els_json(d["elements"], R._eff_skin(d, theme)))]
    assert ids == ["a"]                              # @canvas 不混进元素


def test_external_skin_overrides_section():
    d = R.parse_dsl("## Layout\n\n```\nA :a [按钮] @{0 0 10 10} z=1\n```\n\n## 皮肤\n\na  #aaaaaa\n")
    svg = R.render_svg(d, {"a": {"fill": "#bbbbbb", "ink": ""}})
    assert "#bbbbbb" in svg and "#aaaaaa" not in svg            # --skin 覆盖皮肤段


def test_render_with_skin():
    p = R.parse_dsl(SAMPLE)
    skin = {"back": {"fill": "#112233", "ink": "#aabbcc"}}
    html = R.render_html(p, skin)
    assert "#112233" in html and "#aabbcc" in html      # 注入 ELS
    svg = R.render_svg(p, skin)
    assert "#112233" in svg                              # back 的 rect 用采样 fill
    assert R.render_svg(p, skin) == R.render_svg(p, skin)


def test_z_optional_layer_falls_back_to_indent():
    # 无 z:子元素缩进更深 → layer 更大 → svg 后画(叠在父容器上),validate 仅提醒不阻断
    dsl = "## Layout\n\n```\n容器 :box [容器] @{0 0 100 100}\n  子 :kid [按钮] @{10 10 20 20} \"K\"\n```\n"
    d = R.parse_dsl(dsl)
    assert R.validate(d) == ["容器", "子"]              # 缺 z → 提醒列表(非阻断)
    import json as _j
    els = {e["id"]: e for e in _j.loads(R._els_json(d["elements"]))}
    assert els["box"]["layer"] == 0 and els["kid"]["layer"] == 2   # 缩进 0 vs 2(两空格)
    svg = R.render_svg(d)
    assert svg.index('data-id="box"') < svg.index('data-id="kid"')  # 父先画、子后画(在上)


def test_z_wins_over_indent():
    # 显式 z 压过缩进:深缩进但 z 低 → 仍在浅缩进高 z 之下
    dsl = "## Layout\n\n```\n背景 :bg [背景槽] @{0 0 100 100} z=1\n  浮层 :ov [面板] @{10 10 20 20} z=8\n```\n"
    d = R.parse_dsl(dsl)
    svg = R.render_svg(d)
    assert svg.index('data-id="bg"') < svg.index('data-id="ov"')


def test_validate_advisory_only():
    ok = R.parse_dsl("## Layout\n\n```\nA :a [按钮] @{0 0 10 10} z=2 \"A\"\n```\n")
    assert R.validate(ok) == []
    bad = R.parse_dsl("## Layout\n\n```\nB :b [按钮] @{0 0 10 10} \"B\"\n```\n")
    assert R.validate(bad) == ["B"]                     # 仍列出,但 main 不再因此报错


def test_layout_mode_present_with_instances():
    insts = [{"id": "top", "label": "顶栏", "alias": "资源栏", "x": 0, "y": 0,
              "w": None, "h": None, "box": [0, 0, 66.7, 11.1], "native": True, "z": 9}]
    html = R.render_html(R.parse_dsl("# S\n\n## Layout\n\n```\n占 :p [文本] @{0 0 1 1} z=1\n```\n"),
                         instances=insts)
    assert "render('layout')" in html and "布局" in html
    assert '"alias": "资源栏"' in html or '"alias":"资源栏"' in html
    assert "[实例·" in html        # 导出器能拼实例行


import tempfile


def _w(p, t):
    open(p, "w", encoding="utf-8").write(t)


def test_resolve_native_placement_no_scale():
    d = tempfile.mkdtemp()
    _w(os.path.join(d, "bar.md"),
       "# 资源栏 · 模块\n> 类型: 模块\n> 尺寸: 200×100\n\n## Layout\n\n```\n背板 :bg [面板] @{0 0 100 100} z=3\n金币 :gold [数值条] @{0 0 50 100} z=5\n```\n")
    screen = R.parse_dsl("# S\n> 尺寸: 1000×1000\n\n## 引用\n\n资源栏 = bar.md\n\n## Layout\n\n```\n顶栏 :top [实例·资源栏] @{10 5} z=9\n开始 :start [按钮] @{40 80 20 8} z=6\n```\n")
    out = R.resolve(screen, d)
    ids = [e["id"] for e in out["elements"]]
    assert "top.bg" in ids and "top.gold" in ids and "start" in ids
    assert all(not e["type"].startswith("实例") for e in out["elements"])
    bg = [e for e in out["elements"] if e["id"] == "top.bg"][0]
    assert (round(bg["x"], 3), round(bg["y"], 3), round(bg["w"], 3), round(bg["h"], 3)) == (10.0, 5.0, 20.0, 10.0)
    gold = [e for e in out["elements"] if e["id"] == "top.gold"][0]
    assert round(gold["w"], 3) == 10.0 and round(gold["h"], 3) == 10.0
    assert bg["z"] == 9 and gold["z"] == 9


def test_resolve_contain_box_letterbox():
    d = tempfile.mkdtemp()
    _w(os.path.join(d, "sq.md"), "# 方 · 模块\n> 类型: 模块\n> 尺寸: 100×100\n\n## Layout\n\n```\n满 :f [面板] @{0 0 100 100} z=1\n```\n")
    screen = R.parse_dsl("# S\n> 尺寸: 1000×1000\n\n## 引用\n\n方 = sq.md\n\n## Layout\n\n```\n条 :c [实例·方] @{0 0 100 10} z=2\n```\n")
    f = [e for e in R.resolve(screen, d)["elements"] if e["id"] == "c.f"][0]
    assert round(f["x"], 1) == 45.0 and round(f["w"], 1) == 10.0 and round(f["y"], 1) == 0.0 and round(f["h"], 1) == 10.0


def test_resolve_module_skin_baked():
    d = tempfile.mkdtemp()
    _w(os.path.join(d, "bar.md"),
       "# 资源栏 · 模块\n> 类型: 模块\n> 尺寸: 100×100\n\n## Layout\n\n```\n金币 :gold [数值条] @{0 0 100 100} z=5\n```\n\n## 皮肤\n\ngold  #ffcc00 / #000000\n")
    screen = R.parse_dsl("# S\n> 尺寸: 1000×1000\n\n## 引用\n\n资源栏 = bar.md\n\n## Layout\n\n```\n顶栏 :top [实例·资源栏] @{0 0} z=9\n```\n")
    out = R.resolve(screen, d)
    assert out["skin"].get("top.gold", {}).get("fill") == "#ffcc00"
    assert "#ffcc00" in R.render_svg(out)


def test_resolve_cycle_detected():
    d = tempfile.mkdtemp()
    _w(os.path.join(d, "a.md"), "# A · 模块\n> 类型: 模块\n> 尺寸: 100×100\n\n## 引用\n\nB = b.md\n\n## Layout\n\n```\nx :x [实例·B] @{0 0} z=1\n```\n")
    _w(os.path.join(d, "b.md"), "# B · 模块\n> 类型: 模块\n> 尺寸: 100×100\n\n## 引用\n\nA = a.md\n\n## Layout\n\n```\ny :y [实例·A] @{0 0} z=1\n```\n")
    screen = R.parse_dsl("# S\n> 尺寸: 1000×1000\n\n## 引用\n\nA = a.md\n\n## Layout\n\n```\nz :z [实例·A] @{0 0} z=1\n```\n")
    try:
        R.resolve(screen, d); assert False, "应检测到环"
    except ValueError as e:
        assert "循环" in str(e)


def test_resolve_deterministic():
    d = tempfile.mkdtemp()
    _w(os.path.join(d, "bar.md"), "# B · 模块\n> 类型: 模块\n> 尺寸: 100×100\n\n## Layout\n\n```\na :a [按钮] @{0 0 100 100} z=1\n```\n")
    txt = "# S\n> 尺寸: 1000×1000\n\n## 引用\n\nB = bar.md\n\n## Layout\n\n```\ni :i [实例·B] @{10 10} z=4\n```\n"
    assert R.render_svg(R.resolve(R.parse_dsl(txt), d)) == R.render_svg(R.resolve(R.parse_dsl(txt), d))


if __name__ == "__main__":
    import traceback, inspect, tempfile, pathlib
    fns = [(n, f) for n, f in sorted(globals().items())
           if n.startswith("test_") and callable(f)]
    fails = 0
    for n, f in fns:
        try:
            if "tmp_path" in inspect.signature(f).parameters:
                f(pathlib.Path(tempfile.mkdtemp()))
            else:
                f()
            print("PASS", n)
        except Exception:
            fails += 1
            print("FAIL", n)
            traceback.print_exc()
    print(f"\n{len(fns)-fails}/{len(fns)} passed")
    raise SystemExit(1 if fails else 0)
