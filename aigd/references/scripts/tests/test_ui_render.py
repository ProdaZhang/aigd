import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import ui_render as R

SAMPLE = '''# EXAMPLE-01 · sample · test screen

> Purpose: for testing (blockquote metadata should not be parsed)

## Palette (optional hint)
main accent magenta #e848a0

## Layout (layer tree: element :id [type] @{x y w h})

```
back            :back     [button]   @{1.8 4.9 4.8 5.3} z=6      "◁"
difficulty·VIII :nodeVIII [button]   @{4 36 6 10.3} z=6 [selected] "VIII"
centralBgArt    :heroArt  [bgSlot]   @{0 0 100 100} z=1  "base image·swap asset"
affix×3                   [text]     @{70 51 28 12} z=4        "debuff"
enter           :enter[button·primary] @{80 90 18 9} z=6        "Enter"
weeklyProgress  :weekly   [valueBar] @{43 86 24 7} z=6          "Weekly Progress 8000/8000"
```

## Events

```
click back -> parent
```

## Notes (retrieval surface)
- this is a note, should not be parsed as an element or event
'''


def test_parse_basic():
    d = R.parse_dsl(SAMPLE)
    assert d["screen"].startswith("EXAMPLE-01")
    assert d["palette"] and "magenta" in d["palette"]
    ids = [e["id"] for e in d["elements"]]
    assert ids == ["back", "nodeVIII", "heroArt", None, "enter", "weekly"], ids
    back = d["elements"][0]
    assert back["type"] == "button" and back["x"] == 1.8 and back["h"] == 5.3
    assert back["z"] == 6 and back["text"] == "◁" and back["state"] is None
    assert d["elements"][1]["state"] == "selected"
    assert d["elements"][3]["repeat"] == 3 and d["elements"][3]["type"] == "text"
    enter = d["elements"][4]
    assert enter["id"] == "enter" and enter["type"] == "button·primary" and enter["text"] == "Enter"
    assert d["events"] == ["click back -> parent"]


def test_parse_kind_and_size():
    d = R.parse_dsl("# M · module\n> Type: module\n> Size: 400×600\n\n## Layout\n\n```\nA :a [button] @{0 0 100 100} z=1\n```\n")
    assert d["kind"] == "module"
    assert d["size"] == (400, 600)
    d2 = R.parse_dsl("# S · screen\n\n## Layout\n\n```\nA :a [button] @{0 0 10 10} z=1\n```\n")
    assert d2["kind"] == "screen" and d2["size"] == (2400, 1080)   # default = landscape mobile baseline


def test_recommend_size():
    assert R.recommend_size(1602, 932) == (1856, 1080)   # landscape: lock height 1080, width = round(1080*1602/932)
    assert R.recommend_size(1080, 2400) == (1080, 2400)   # portrait: lock width 1080
    assert R.recommend_size(1000, 1000) == (1080, 1080)   # square: per landscape rule, lock height 1080


def test_parse_imports():
    d = R.parse_dsl("# S\n\n## Refs\n\nresourceBar = ../modules/resourceBar.module.md\ncard = ./card.md\n\n## Layout\n\n```\nA :a [button] @{0 0 10 10} z=1\n```\n")
    assert d["imports"] == {"resourceBar": "../modules/resourceBar.module.md", "card": "./card.md"}


def test_parse_two_value_geo():
    d = R.parse_dsl("# S\n\n## Layout\n\n```\ntop :top [instance·resourceBar] @{10 5} z=9\n```\n")
    e = d["elements"][0]
    assert e["x"] == 10.0 and e["y"] == 5.0 and e["w"] is None and e["h"] is None
    assert e["type"] == "instance·resourceBar" and e["z"] == 9


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
    d = R.parse_dsl("# M · module\n> Type: module\n> Size: 400×600\n\n## Layout\n\n```\nA :a [button] @{0 0 100 100} z=1\n```\n")
    html = R.render_html(d)
    assert "width:400px;height:600px" in html and "{x:400,y:600}" in html
    svg = R.render_svg(d)
    assert 'viewBox="0 0 400 664"' in svg            # H+64
    assert 'width="400" height="600"' in svg          # stage rect


def test_default_size_renders_2400x1080():
    d = R.parse_dsl("# S\n\n## Layout\n\n```\nA :a [button] @{0 0 10 10} z=1\n```\n")
    assert "width:2400px;height:1080px" in R.render_html(d)


def test_render_html_deterministic():
    p = R.parse_dsl(SAMPLE)
    assert R.render_html(p) == R.render_html(p)


def test_render_html_has_three_modes():
    html = R.render_html(R.parse_dsl(SAMPLE))
    for token in ["render('wire')", "render('skin')", "render('atmo')", "Wireframe", "Skin", "Atmosphere"]:
        assert token in html, token


def test_svg_label_and_container_no_center():
    dsl = "## Layout\n\n```\ntopbar          [container] @{0 4 100 8}\nback :back [button] @{1 5 5 5} \"◁\"\n```\n"
    svg = R.render_svg(R.parse_dsl(dsl))
    assert "anniu" not in svg          # labels use the type name, not pinyin abbr
    assert "·button" in svg and "·container" in svg
    assert svg.count("topbar") == 1    # container with no text -> only the top-left label, not repeated in the center


def test_shape_circle_only_when_declared():
    # both nearly square: declaring shape=circle -> circle; not declared -> still square corners (renderer does not guess from aspect ratio)
    dsl = "## Layout\n\n```\ncircleNode :c [button] @{4 36 6 10} shape=circle \"O\"\nsquareNode :q [button] @{20 36 6 10} \"X\"\n```\n"
    svg = R.render_svg(R.parse_dsl(dsl))
    import re as _re
    rxc = float(_re.search(r'data-id="c"><rect[^>]*rx="([0-9.]+)"', svg).group(1))
    rxq = float(_re.search(r'data-id="q"><rect[^>]*rx="([0-9.]+)"', svg).group(1))
    assert rxc > 10, rxc       # declared circle -> large rx (circle)
    assert rxq == 4.0, rxq     # nearly square but not declared -> square corners unchanged


def test_svg_legend_and_selected_state():
    svg = R.render_svg(R.parse_dsl(SAMPLE))   # nodeVIII has a [selected] state
    assert "selected state" in svg     # legend
    assert "#e848a0" in svg            # selected-state magenta stroke / legend color


def test_svg_background_behind_foreground():
    svg = R.render_svg(R.parse_dsl(SAMPLE))
    assert svg.index('data-id="heroArt"') < svg.index('data-id="back"'), "the full-screen backdrop should be drawn first (bottom), foreground after"


def test_shuzhitiao_renders_bar():
    p = R.parse_dsl(SAMPLE)
    html = R.render_html(p)
    assert ".bar" in html and 'abbr==="shuzhitiao"' in html
    svg = R.render_svg(p)
    assert "data-bar" in svg and "Weekly Progress" in svg


def test_calibration_export_present():
    html = R.render_html(R.parse_dsl(SAMPLE))
    for token in ["Calibrate", "Export DSL", "calib", "@{"]:
        assert token in html, token


def test_render_svg_and_determinism():
    p = R.parse_dsl(SAMPLE)
    svg = R.render_svg(p)
    assert svg.startswith("<svg") and "viewBox" in svg and "nodeVIII" in svg
    assert R.render_svg(p) == R.render_svg(p)


def test_sample_dsl_consistency():
    # bundled compliant sample, self-contained, does not depend on project instance paths
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
        "## Layout\n\n```\nA :a [button·primary] @{0 0 10 10} z=1 \"A\"\n```\n\n"
        "## Skin\n\n# comment line (starts with #) should be skipped\n"
        "a        #112233 / #aabbcc\n"
        "button   #2b2f3a / #ffffff\n")
    sk = d["skin"]
    assert sk["a"] == {"fill": "#112233", "ink": "#aabbcc"}        # by id
    assert sk["button"] == {"fill": "#2b2f3a", "ink": "#ffffff"}   # by type
    assert "# comment line" not in str(sk)                          # comment skipped


def test_skin_section_applied_without_skin_flag():
    d = R.parse_dsl("## Layout\n\n```\nA :a [button] @{0 0 10 10} z=1 \"A\"\n```\n\n## Skin\n\na  #abcdef / #102030\n")
    assert "#abcdef" in R.render_svg(d)        # Skin section takes effect, no --skin needed
    assert "#abcdef" in R.render_html(d)


def test_type_keyed_theme_generalizes():
    # theme colors by type: both buttons take the "button" color (design.md style generalization), the variant button·primary falls back to the base type
    d = R.parse_dsl("## Layout\n\n```\nA :a [button] @{0 0 10 10} z=1\nB :b [button·primary] @{20 0 10 10} z=1\n```\n")
    theme = {"button": {"fill": "#123456", "ink": "#ffffff"}}
    els = __import__("json").loads(R._els_json(d["elements"], R._eff_skin(d, theme)))
    assert els[0]["fill"] == "#123456"         # button hits directly
    assert els[1]["fill"] == "#123456"         # button·primary -> base type button fallback hit


def test_canvas_key_themes_backdrop():
    # @canvas reserved key: apply the canvas background to the stage (html) / root rect (svg), and not render it as an element
    d = R.parse_dsl("## Layout\n\n```\nA :a [text] @{0 0 10 10} z=1 \"A\"\n```\n")
    theme = {"@canvas": {"fill": "#faf9f5", "ink": "#141413"}, "text": {"fill": "", "ink": "#3d3d3a"}}
    html = R.render_html(d, theme)
    assert '"#faf9f5"' in html                       # CANVAS constant injected
    svg = R.render_svg(d, theme)
    assert svg.count("#faf9f5") >= 1                 # root rect uses the canvas color
    import json as _j
    ids = [e["id"] for e in _j.loads(R._els_json(d["elements"], R._eff_skin(d, theme)))]
    assert ids == ["a"]                              # @canvas does not mix into elements


def test_external_skin_overrides_section():
    d = R.parse_dsl("## Layout\n\n```\nA :a [button] @{0 0 10 10} z=1\n```\n\n## Skin\n\na  #aaaaaa\n")
    svg = R.render_svg(d, {"a": {"fill": "#bbbbbb", "ink": ""}})
    assert "#bbbbbb" in svg and "#aaaaaa" not in svg            # --skin overrides the Skin section


def test_render_with_skin():
    p = R.parse_dsl(SAMPLE)
    skin = {"back": {"fill": "#112233", "ink": "#aabbcc"}}
    html = R.render_html(p, skin)
    assert "#112233" in html and "#aabbcc" in html      # injected into ELS
    svg = R.render_svg(p, skin)
    assert "#112233" in svg                              # back's rect uses the sampled fill
    assert R.render_svg(p, skin) == R.render_svg(p, skin)


def test_z_optional_layer_falls_back_to_indent():
    # without z: children indent deeper -> larger layer -> drawn later in svg (stacked above the parent), validate only reminds, does not block
    dsl = "## Layout\n\n```\nbox :box [container] @{0 0 100 100}\n  kid :kid [button] @{10 10 20 20} \"K\"\n```\n"
    d = R.parse_dsl(dsl)
    assert R.validate(d) == ["box", "kid"]             # missing z -> reminder list (non-blocking)
    import json as _j
    els = {e["id"]: e for e in _j.loads(R._els_json(d["elements"]))}
    assert els["box"]["layer"] == 0 and els["kid"]["layer"] == 2   # indent 0 vs 2 (two spaces)
    svg = R.render_svg(d)
    assert svg.index('data-id="box"') < svg.index('data-id="kid"')  # parent drawn first, child after (on top)


def test_z_wins_over_indent():
    # explicit z overrides indent: deep indent but low z -> still below the shallow-indent high z
    dsl = "## Layout\n\n```\nbg :bg [bgSlot] @{0 0 100 100} z=1\n  overlay :ov [panel] @{10 10 20 20} z=8\n```\n"
    d = R.parse_dsl(dsl)
    svg = R.render_svg(d)
    assert svg.index('data-id="bg"') < svg.index('data-id="ov"')


def test_validate_advisory_only():
    ok = R.parse_dsl("## Layout\n\n```\nA :a [button] @{0 0 10 10} z=2 \"A\"\n```\n")
    assert R.validate(ok) == []
    bad = R.parse_dsl("## Layout\n\n```\nB :b [button] @{0 0 10 10} \"B\"\n```\n")
    assert R.validate(bad) == ["B"]                     # still listed, but main no longer errors because of it


def test_layout_mode_present_with_instances():
    insts = [{"id": "top", "label": "topbar", "alias": "resourceBar", "x": 0, "y": 0,
              "w": None, "h": None, "box": [0, 0, 66.7, 11.1], "native": True, "z": 9}]
    html = R.render_html(R.parse_dsl("# S\n\n## Layout\n\n```\np :p [text] @{0 0 1 1} z=1\n```\n"),
                         instances=insts)
    assert "render('layout')" in html and "Layout" in html
    assert '"alias": "resourceBar"' in html or '"alias":"resourceBar"' in html
    assert "[instance·" in html        # the exporter can assemble instance lines


import tempfile


def _w(p, t):
    open(p, "w", encoding="utf-8").write(t)


def test_resolve_native_placement_no_scale():
    d = tempfile.mkdtemp()
    _w(os.path.join(d, "bar.md"),
       "# resourceBar · module\n> Type: module\n> Size: 200×100\n\n## Layout\n\n```\nbackplate :bg [panel] @{0 0 100 100} z=3\ngold :gold [valueBar] @{0 0 50 100} z=5\n```\n")
    screen = R.parse_dsl("# S\n> Size: 1000×1000\n\n## Refs\n\nresourceBar = bar.md\n\n## Layout\n\n```\ntop :top [instance·resourceBar] @{10 5} z=9\nstart :start [button] @{40 80 20 8} z=6\n```\n")
    out = R.resolve(screen, d)
    ids = [e["id"] for e in out["elements"]]
    assert "top.bg" in ids and "top.gold" in ids and "start" in ids
    assert all(not e["type"].startswith("instance") for e in out["elements"])
    bg = [e for e in out["elements"] if e["id"] == "top.bg"][0]
    assert (round(bg["x"], 3), round(bg["y"], 3), round(bg["w"], 3), round(bg["h"], 3)) == (10.0, 5.0, 20.0, 10.0)
    gold = [e for e in out["elements"] if e["id"] == "top.gold"][0]
    assert round(gold["w"], 3) == 10.0 and round(gold["h"], 3) == 10.0
    assert bg["z"] == 9 and gold["z"] == 9


def test_resolve_contain_box_letterbox():
    d = tempfile.mkdtemp()
    _w(os.path.join(d, "sq.md"), "# square · module\n> Type: module\n> Size: 100×100\n\n## Layout\n\n```\nfull :f [panel] @{0 0 100 100} z=1\n```\n")
    screen = R.parse_dsl("# S\n> Size: 1000×1000\n\n## Refs\n\nsquare = sq.md\n\n## Layout\n\n```\nbar :c [instance·square] @{0 0 100 10} z=2\n```\n")
    f = [e for e in R.resolve(screen, d)["elements"] if e["id"] == "c.f"][0]
    assert round(f["x"], 1) == 45.0 and round(f["w"], 1) == 10.0 and round(f["y"], 1) == 0.0 and round(f["h"], 1) == 10.0


def test_resolve_module_skin_baked():
    d = tempfile.mkdtemp()
    _w(os.path.join(d, "bar.md"),
       "# resourceBar · module\n> Type: module\n> Size: 100×100\n\n## Layout\n\n```\ngold :gold [valueBar] @{0 0 100 100} z=5\n```\n\n## Skin\n\ngold  #ffcc00 / #000000\n")
    screen = R.parse_dsl("# S\n> Size: 1000×1000\n\n## Refs\n\nresourceBar = bar.md\n\n## Layout\n\n```\ntop :top [instance·resourceBar] @{0 0} z=9\n```\n")
    out = R.resolve(screen, d)
    assert out["skin"].get("top.gold", {}).get("fill") == "#ffcc00"
    assert "#ffcc00" in R.render_svg(out)


def test_resolve_cycle_detected():
    d = tempfile.mkdtemp()
    _w(os.path.join(d, "a.md"), "# A · module\n> Type: module\n> Size: 100×100\n\n## Refs\n\nB = b.md\n\n## Layout\n\n```\nx :x [instance·B] @{0 0} z=1\n```\n")
    _w(os.path.join(d, "b.md"), "# B · module\n> Type: module\n> Size: 100×100\n\n## Refs\n\nA = a.md\n\n## Layout\n\n```\ny :y [instance·A] @{0 0} z=1\n```\n")
    screen = R.parse_dsl("# S\n> Size: 1000×1000\n\n## Refs\n\nA = a.md\n\n## Layout\n\n```\nz :z [instance·A] @{0 0} z=1\n```\n")
    try:
        R.resolve(screen, d); assert False, "should detect a cycle"
    except ValueError as e:
        assert "circular" in str(e)


def test_resolve_deterministic():
    d = tempfile.mkdtemp()
    _w(os.path.join(d, "bar.md"), "# B · module\n> Type: module\n> Size: 100×100\n\n## Layout\n\n```\na :a [button] @{0 0 100 100} z=1\n```\n")
    txt = "# S\n> Size: 1000×1000\n\n## Refs\n\nB = bar.md\n\n## Layout\n\n```\ni :i [instance·B] @{10 10} z=4\n```\n"
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
