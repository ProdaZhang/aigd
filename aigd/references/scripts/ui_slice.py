"""Tool 3 family · deterministic slicer: source image + interface DSL -> one png slice per element + an index.md contact sheet.

Cuts each element's region out of the source image by the DSL bbox (`shape=circle` adds a circular alpha mask), splitting a
competitor interface into reference/replaceable part assets. Same family as ui_palette: reuses parse_dsl, requires Pillow, declaration-driven
(only `shape=` decides circle/square, not guessing from aspect ratio). Same input + same Pillow/zlib version -> byte-identical output.

Usage: python ui_slice.py <dsl.md> <image> [outdir]
       python ui_slice.py <dsl.md> <image> [outdir] --only bgSlot,artSlot,iconSlot   # only cut these types
Output: outdir/NN_<id or name>.png (per-element slice, NN=document order) + outdir/index.md (thumbnail contact sheet + bbox table).
"""
import sys, os, re

try:
    import ui_render as R
except ImportError:
    R = None

_UNSAFE = re.compile(r'[\\/:*?"<>|\s]+')
_CIRCLE = ("circle",)


def _slug(e):
    s = _UNSAFE.sub("-", (e["id"] or e["name"] or e["type"] or "el")).strip("-")
    return s or "el"


def _box(e, W, H):
    x1, y1 = e["x"] / 100 * W, e["y"] / 100 * H
    x2, y2 = (e["x"] + e["w"]) / 100 * W, (e["y"] + e["h"]) / 100 * H
    return (max(0, int(x1)), max(0, int(y1)), min(W, int(round(x2))), min(H, int(round(y2))))


def cut(image_path, parsed, outdir, only=None):
    """Cut each (optionally type-filtered) element -> outdir/NN_slug.png; returns the manifest list (order preserved).

    The number NN is taken from the **full element list's document order** -- even when filtered with only, the kept slices keep stable numbers.
    """
    from PIL import Image, ImageDraw
    img = Image.open(image_path).convert("RGB")
    W, H = img.size
    all_els = parsed["elements"]
    keep = set(only) if only else None
    width = max(2, len(str(len(all_els))))
    os.makedirs(outdir, exist_ok=True)
    manifest = []
    for i, e in enumerate(all_els):
        if keep is not None and e["type"] not in keep and e["type"].split("·")[0] not in keep:
            continue
        box = _box(e, W, H)
        if box[2] <= box[0] or box[3] <= box[1]:
            continue
        crop = img.crop(box)
        if (e.get("shape") or "") in _CIRCLE:
            crop = crop.convert("RGBA")
            mask = Image.new("L", crop.size, 0)
            ImageDraw.Draw(mask).ellipse([0, 0, crop.width - 1, crop.height - 1], fill=255)
            crop.putalpha(mask)
        fn = "%0*d_%s.png" % (width, i, _slug(e))
        crop.save(os.path.join(outdir, fn))
        manifest.append({"file": fn, "id": e["id"], "name": e["name"], "type": e["type"],
                         "z": e["z"], "shape": e.get("shape") or "",
                         "bbox": [e["x"], e["y"], e["w"], e["h"]]})
    with open(os.path.join(outdir, "index.md"), "w", encoding="utf-8") as f:
        f.write(index_md(parsed, manifest))
    return manifest


def _cell(s):
    return str(s).replace("|", "/")          # table cells must not contain a bare pipe


def index_md(parsed, manifest):
    """Thumbnail contact sheet + bbox table (markdown, directly readable in the knowledge base)."""
    lines = ["# Slice contact sheet · %s" % (parsed["screen"] or ""), "",
             "> Tool 3 ui_slice output: per-element cut from the source image (`shape=circle` already has a circular mask).",
             "> When swapping assets, align by bbox/type; the source image can be discarded, this table + the slices are the archive.", ""]
    for m in manifest:
        cap = m["name"] or m["id"] or m["type"]
        lines.append("![%s](%s)" % (_cell(cap), m["file"]))
    lines += ["", "| slice | id | name | type | shape | z | bbox(x y w h %) |",
              "|---|---|---|---|---|---|---|"]
    for m in manifest:
        z = "" if m["z"] is None else m["z"]
        bb = " ".join("%g" % v for v in m["bbox"])
        lines.append("| %s | %s | %s | %s | %s | %s | %s |" % (
            _cell(m["file"]), _cell(m["id"] or ""), _cell(m["name"] or ""),
            _cell(m["type"]), _cell(m["shape"]), z, bb))
    return "\n".join(lines) + "\n"


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    only = None
    if "--only" in argv:
        i = argv.index("--only")
        only = [t for t in argv[i + 1].split(",") if t] if i + 1 < len(argv) else None
        del argv[i:i + 2]
    if len(argv) < 2:
        print("usage: python ui_slice.py <dsl.md> <image> [outdir] [--only type,type]")
        return 2
    if R is None:
        print("X requires same-directory ui_render.py (reuses parse_dsl)")
        return 2
    dsl, image = argv[0], argv[1]
    outdir = argv[2] if len(argv) > 2 and not argv[2].startswith("-") else (dsl.rsplit(".", 1)[0] + ".slices")
    with open(dsl, encoding="utf-8") as f:
        parsed = R.parse_dsl(f.read())
    from PIL import Image as _I
    iw, ih = _I.open(image).size
    print("recommended > size:", "%dx%d" % R.recommend_size(iw, ih))
    parsed = R.resolve(parsed, os.path.dirname(os.path.abspath(dsl)))   # expand instances (identity if none)
    manifest = cut(image, parsed, outdir, only)
    print("slices ->", outdir, "(%d slices + index.md)" % len(manifest))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
