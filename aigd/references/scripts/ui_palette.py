"""Tool 3 family · deterministic color sampler: source image + interface DSL -> per-element main color (fill) + text color (ink) skin module.

Samples real colors from the source image by each DSL bbox (main color = the region's dominant color, text color = the color in the
region with the greatest contrast to the main color); background/portrait slots (art, to be swapped) and elements without id are not sampled.
Requires Pillow; same input + same Pillow version -> consistent output.

Usage: python ui_palette.py <dsl.md> <image> [out.skin.json]
Output: {element id: {"fill":"#rrggbb", "ink":"#rrggbb"}} -- feeds ui_render.py --skin to color each element.
        Or --merge to write the colors into the md's `## Skin` section (rendering that md then uses the real colors, no --skin needed).
"""
import sys, json, os

try:
    import ui_render as R
except ImportError:
    R = None

ART = ("bgSlot", "artSlot")


def _hex(c):
    return "#%02x%02x%02x" % (int(c[0]), int(c[1]), int(c[2]))


def _lum(c):
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def _dominant(region, k=6):
    rgb = region.convert("RGB")
    q = rgb.quantize(colors=k).convert("RGB")
    cols = q.getcolors(q.width * q.height) or []
    cols.sort(key=lambda c: c[0], reverse=True)   # descending by frequency
    return [c[1] for c in cols]


def sample(image_path, parsed):
    from PIL import Image
    img = Image.open(image_path).convert("RGB")
    W, H = img.size
    skin = {}
    for e in parsed["elements"]:
        if not e["id"] or e["type"] in ART:
            continue
        x1, y1 = e["x"] / 100 * W, e["y"] / 100 * H
        x2, y2 = (e["x"] + e["w"]) / 100 * W, (e["y"] + e["h"]) / 100 * H
        box = (max(0, int(x1)), max(0, int(y1)), min(W, int(round(x2))), min(H, int(round(y2))))
        if box[2] <= box[0] or box[3] <= box[1]:
            continue
        # circular element: sample the central inner ring (otherwise the background inside the box but outside the circle dominates and samples the wrong color)
        if (e.get("shape") or "") in ("circle",):
            cx, cy = (box[0] + box[2]) / 2.0, (box[1] + box[3]) / 2.0
            hw, hh = (box[2] - box[0]) * 0.28, (box[3] - box[1]) * 0.28
            inner = (int(cx - hw), int(cy - hh), int(cx + hw), int(cy + hh))
            if inner[2] > inner[0] and inner[3] > inner[1]:
                box = inner
        doms = _dominant(img.crop(box))
        if not doms:
            continue
        fill = doms[0]
        ink = max(doms, key=lambda c: abs(_lum(c) - _lum(fill))) if len(doms) > 1 else (240, 240, 240)
        skin[e["id"]] = {"fill": _hex(fill), "ink": _hex(ink)}
    return skin


def merge(md_text, skin):
    """Write the sampled colors into the md's `## Skin` section (id -> color): replace an existing Skin section, or append at the end.

    Skin and structure (Layout) are separated -- the whole section can be re-skinned/deleted (delete = fall back to L1), without polluting element lines.
    skin is an ordered dict (sample produces it in element order) -> deterministic output.
    """
    lines = md_text.splitlines()
    out, i, n = [], 0, len(lines)
    while i < n:
        ln = lines[i]
        if ln.strip().startswith("## ") and ln.strip()[3:].strip().startswith("Skin"):
            i += 1                                   # skip the old Skin section (until the next ## or end of file)
            while i < n and not lines[i].strip().startswith("## "):
                i += 1
            continue
        out.append(ln); i += 1
    while out and not out[-1].strip():               # strip trailing blank lines before appending
        out.pop()
    block = ["", "## Skin", ""]
    for key in skin:
        c = skin[key]
        row = "%s  %s" % (key, c["fill"])
        if c.get("ink"):
            row += " / %s" % c["ink"]
        block.append(row)
    return "\n".join(out + block) + "\n"


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    merge_mode, merge_out = False, None
    if "--merge" in argv:
        merge_mode = True
        i = argv.index("--merge")
        if i + 1 < len(argv) and not argv[i + 1].startswith("-"):
            merge_out = argv[i + 1]; del argv[i:i + 2]
        else:
            del argv[i]
    if len(argv) < 2:
        print("usage: python ui_palette.py <dsl.md> <image> [out.skin.json]")
        print("       python ui_palette.py <dsl.md> <image> --merge [out.md]   # write the colors into the md's ## Skin section")
        return 2
    if R is None:
        print("X requires same-directory ui_render.py (reuses parse_dsl)")
        return 2
    dsl, image = argv[0], argv[1]
    with open(dsl, encoding="utf-8") as f:
        md = f.read()
    parsed = R.parse_dsl(md)
    # do not resolve: sampling/--merge writes back by the authored md's ids; after expansion, namespaced ids would be written wrong.
    # competitor capture (this tool's only scenario) contains no instances anyway, so resolve is the identity; hence skipped.
    from PIL import Image as _I
    iw, ih = _I.open(image).size
    print("recommended > size:", "%dx%d" % R.recommend_size(iw, ih))
    skin = sample(image, parsed)
    if merge_mode:
        out = merge_out or (dsl.rsplit(".", 1)[0] + ".colored.md")
        with open(out, "w", encoding="utf-8") as f:
            f.write(merge(md, skin))
        print("merged md ->", out, "(%d elements colored)" % len(skin))
    else:
        out = argv[2] if len(argv) > 2 else (dsl.rsplit(".", 1)[0] + ".skin.json")
        with open(out, "w", encoding="utf-8") as f:
            json.dump(skin, f, ensure_ascii=False, indent=1)
        print("skin ->", out, "(%d elements)" % len(skin))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
