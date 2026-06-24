import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import ui_render as R
try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
import ui_palette as P


def _rgb(h):
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def test_sample_known_colors(tmp_path):
    if not HAS_PIL:
        print("  (skip test_sample_known_colors: no Pillow)"); return
    img = Image.new("RGB", (100, 100), (10, 10, 10))
    img.paste((220, 20, 20), (0, 0, 50, 50))     # top-left red
    img.paste((20, 20, 220), (50, 0, 100, 50))   # top-right blue
    p = tmp_path / "t.png"; img.save(str(p))
    dsl = "## Layout\n\n```\nred :a [button] @{0 0 50 50} z=1\nblue :b [button] @{50 0 50 50} z=1\n```\n"
    skin = P.sample(str(p), R.parse_dsl(dsl))
    ra, rb = _rgb(skin["a"]["fill"]), _rgb(skin["b"]["fill"])
    assert ra[0] > 180 and ra[2] < 80, skin["a"]   # a leans red
    assert rb[2] > 180 and rb[0] < 80, skin["b"]   # b leans blue


def test_sample_skips_art_and_no_id(tmp_path):
    if not HAS_PIL:
        print("  (skip test_sample_skips_art_and_no_id: no Pillow)"); return
    img = Image.new("RGB", (100, 100), (30, 30, 30))
    p = tmp_path / "t.png"; img.save(str(p))
    dsl = "## Layout\n\n```\nbase :bg [bgSlot] @{0 0 100 100} z=1\nnoname [button] @{0 0 10 10} z=2\ncard :c [panel] @{20 20 30 30} z=3\n```\n"
    skin = P.sample(str(p), R.parse_dsl(dsl))
    assert "bg" not in skin     # background slot (art) is not sampled
    assert "c" in skin          # panel with an id is sampled
    assert len(skin) == 1       # the one without an id is not sampled


def test_sample_circle_takes_center(tmp_path):
    if not HAS_PIL:
        print("  (skip test_sample_circle_takes_center: no Pillow)"); return
    img = Image.new("RGB", (100, 100), (20, 20, 20))   # dark background
    img.paste((230, 40, 160), (25, 25, 75, 75))        # centered magenta block (25% area)
    p = tmp_path / "t.png"; img.save(str(p))
    sq = P.sample(str(p), R.parse_dsl("## Layout\n\n```\nA :a [button] @{0 0 100 100} z=1\n```\n"))
    ci = P.sample(str(p), R.parse_dsl("## Layout\n\n```\nA :a [button] @{0 0 100 100} z=1 shape=circle\n```\n"))
    aq, ac = _rgb(sq["a"]["fill"]), _rgb(ci["a"]["fill"])
    assert aq[0] < 80, sq                       # square: dark background dominates
    assert ac[0] > 180 and ac[1] < 110, ci      # circle: takes the center -> magenta


def test_sample_deterministic(tmp_path):
    if not HAS_PIL:
        print("  (skip test_sample_deterministic: no Pillow)"); return
    img = Image.new("RGB", (60, 60), (40, 80, 120))
    img.paste((200, 200, 40), (0, 0, 30, 60))
    p = tmp_path / "t.png"; img.save(str(p))
    parsed = R.parse_dsl("## Layout\n\n```\nA :a [button] @{0 0 50 100} z=1\n```\n")
    assert P.sample(str(p), parsed) == P.sample(str(p), parsed)


def test_merge_writes_skin_section(tmp_path):
    if not HAS_PIL:
        print("  (skip test_merge_writes_skin_section: no Pillow)"); return
    img = Image.new("RGB", (100, 100), (10, 10, 10))
    img.paste((220, 20, 20), (0, 0, 50, 50))
    p = tmp_path / "t.png"; img.save(str(p))
    md = "## Layout\n\n```\nred :a [button] @{0 0 50 50} z=1 \"R\"\n```\n"
    skin = P.sample(str(p), R.parse_dsl(md))
    merged = P.merge(md, skin)
    assert "## Skin" in merged and "color=" not in merged     # written as a Skin section, no inline color= on element lines
    parsed = R.parse_dsl(merged)
    assert parsed["skin"].get("a", {}).get("fill", "").startswith("#")  # the Skin section can be parsed back
    assert P.merge(md, skin) == P.merge(md, skin)         # deterministic


def test_merge_replaces_existing_skin_section(tmp_path):
    if not HAS_PIL:
        print("  (skip test_merge_replaces_existing_skin_section: no Pillow)"); return
    img = Image.new("RGB", (100, 100), (10, 10, 10))
    img.paste((220, 20, 20), (0, 0, 50, 50))
    p = tmp_path / "t.png"; img.save(str(p))
    md = "## Layout\n\n```\nred :a [button] @{0 0 50 50} z=1 \"R\"\n```\n\n## Skin\n\na  #000000\n"
    skin = P.sample(str(p), R.parse_dsl(md))
    merged = P.merge(md, skin)
    assert merged.count("## Skin") == 1                    # the old Skin section is replaced, not duplicated
    assert "#000000" not in merged                         # the old color is replaced by the new sampled color


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
