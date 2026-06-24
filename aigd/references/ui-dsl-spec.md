# UI DSL Spec (screenshot knowledge base · toolchain contract)

> A plain-text DSL describing "UI screen structure": **tool 1** (the capture skill, fill it in by looking at an image) writes it, **tool 2** (`ui_render.py`) renders it, **tool 3** (`ui_slice.py`, slices an image by boxes) consumes it.
> **One DSL, two uses**: own design (has a real config table) and competitor capture (no real data) — distinguished by "source semantics."
> This document is **authoritative**; the grammar must stay in sync with `parse_dsl` in `references/scripts/ui_render.py` (to change the grammar, change the parser first and run the tests).

## 1. File skeleton

```
# screenID · source · screenName

> Purpose: …
> Layout pattern: …      # retrieval facet: similar references are matched by it
> Tags: #tagA #tagB
> Source: <game/own> / <date> / original image discarded

## Palette               # optional hint (prose, semantic reference only)
<a palette description, containing several #RRGGBB>

## Layout                # element tree (can be wrapped in a ``` fence)
<one element per line, see §2>

## Events                # interactions (can be wrapped in a ``` fence)
<trigger element [guard] -> result/target>

## Skin                  # optional, structured coloring (id or type → color), separated from structure, see §9
<id-or-type  #fill[/#text]>

## Notes                 # optional, retrieval facet: layout pattern / insights
- …
```

- Section headings are recognized by **keyword prefix** (`## Layout (……)` also matches); the heading may carry a parenthetical note.
- `## Layout` / `## Events` content may be wrapped in a ```` ``` ```` fence (fence lines are skipped by the parser).
- `> …` quote lines and the `Notes` section **do not participate in rendering** (pure retrieval facet).

## 2. Layout-line grammar (authoritative)

```
name [:id] [type] @{x y w h} [z=N] [shape=shapeName] [[state]] [×N] ["text"]
```

| Part | Description | Required |
|------|------|------|
| name | short Chinese name (display label / slot name) | yes |
| `:id` | for cross-reference/events; may directly follow the type with no space (`:back[button]`) | no |
| `[type]` | the bracket **before** `@{` = type; see the §3 type table; variants use `·` (e.g. `button·primary`) | yes |
| `@{x y w h}` | **percentage** bbox (0–100, relative to screen, origin top-left) | yes |
| `z=N` | layering. **Optional**: if tagged, stack by it; if not, fall back to (indent, document order) (see §4) | no |
| `shape=circle` | shape, default rectangular corners; circle/rectangle are **structural attributes** (see §5) | no |
| `[state]` | the bracket **after** `@{` = state (selected/locked/disabled…) | no |
| `×N` | repeat count | no |
| `"text"` | the element's text content | no |

> **Coloring is not written on the element line** — skin and structure are separated, gathered into the `## Skin` section (see §9); the whole section can be swapped or deleted.
> **Leading indent of a line = nesting level** (child elements are more deeply indented); without z it participates in the layering fallback (see §4).
> Parsing rule: `@{}` splits the line into pre/post; in pre, take the `:id` and the first `[type]`; in post, take `z=` / `shape=` / the first `[state]` / `"text"`. Lines with no `@{}` (headings/comments) are skipped.

## 3. Type table (= slot types, swap in your own assets)

`container` / `panel` / `button` / `text` / `iconSlot` / `bgSlot` / `artSlot` / `valueBar` / `decoration` / `chrome` (window frames and other non-game UI).

- The renderer gives each type a **generic skin** (L1) and a wireframe color; `iconSlot/bgSlot/artSlot` = art placeholders, left empty to swap in assets; `valueBar` draws a progress bar (if the text contains `X/Y`, it's proportional).
- Type not in the table → fall back to the base type before `·`, and failing that, to "unknown."

## 4. Layering (z) — z first, otherwise by indent + document order

The sort key = **`z first; without z, by (indent depth, document order)`**, stacked low to high (low at the bottom).

- **If `z=N` is tagged**: stack by it. An explicit z **always overrides** the indent fallback.
- **If z is not tagged**: stack by **leading-indent depth** (child elements are more deeply indented → stacked on top of the parent container); same indent stacks by **document order** (later-written on top). Indent is **structural information, not geometry** — uphold the hard principle below.
- **Hard principle**: the renderer **draws only by the declared z / indent, and never guesses layering from aspect ratio, who's fullscreen, who nests whom, or other geometry**.
- **When to add z**: add z when there's a **fullscreen background** or when elements **overlap** (background `@{0 0 100 100} z=1`), otherwise a base image declared mid-stream will cover what precedes it; a flat-layered draft can skip it.
- **Mixing caution**: when a screen has both z-tagged and non-z elements, a non-z element's layer = its indent depth, which may not align with the z ladder — if you mix, tag z fully on that screen.
- **Recommended ladder**: background = 1 · panel/container = 3–4 · ordinary elements inside a container = 4–5 · interactive (button/valueBar/node) = 6 · overlay/popup = 7–8 · chrome = 9.
- **Strong/weak convention**: the **capture skill (tool 1) still requires z on every element** (when copying a real image, layering must be fully recorded); **discussion-mode DSL may omit z** (early structure sketching). The renderer never errors on missing z; `validate()` only reminds.

## 5. Shape (shape=) — a structural attribute, takes effect only when declared

- `shape=circle` (or `circle`) → rendered as a circle/capsule; **default rectangular corners**.
- Circle/rectangle affects the form of "the asset you drop into the slot," which is structural information, **declared by tool 1 when reading the image**; the renderer **does not guess from aspect ratio**.

## 6. Source semantics (competitor-library credibility, key)

- `:canonical table[primaryKey].field` — **own design**, backed by a real config table;
- `:observed …` — what is **visually readable** in a **competitor** image (text/coloring/layout), a fact;
- `:inferred …` — a guess at a **competitor**'s **data structure / source table**, a hypothesis.

**Never treat a competitor's `:inferred` as `:canonical`** — otherwise guesses in the knowledge base will contaminate later designs.

> Structure capture **need not tag each observed text element with `:observed`** (writing the text down is itself an observation); **tag `:inferred` only when you write out an "inferred data structure / source table."** A competitor DSL just needs one note in the screen header's `> Source` saying "all data is observed, no canonical source."

## 7. Image-reading recipe (tool 1's fixed order, to reduce granularity drift)

1. **Screen header**: screenID / source / purpose / layout pattern / tags.
2. **Palette** (optional): main color + a few `#RRGGBB`.
3. **Layout, outside-in, top-to-bottom**:
   a. First the **container/panel** (give it a lower z), then its **children/leaves** (give them a higher z);
   b. For each element **always give** name + `[type]` + `@{x y w h}` + `z=N`; add `shape=` / `[state]` / `×N` / `"text"` as needed;
   c. **Fullscreen base image** = `@{0 0 100 100} z=1`;
   d. Tag circular elements (avatars/nodes/badges) with `shape=circle`; tag selected/locked etc. with `[state]`.
4. **Geometry**: eyeball the percentage bbox, **no need to be pixel-accurate** — leave it to the "calibrate" drag fine-tuning of `ui_render.py`, which exports back to md.
5. **Events**: `trigger element [guard] -> result/target`.
6. **Source**: competitor data is uniformly `:observed`/`:inferred`, never written as `:canonical`.
7. **Notes** (optional): insights such as layout pattern, positive/negative zoning, visual focus.

**Granularity rule**: one visual block that "can be clicked independently / can have its asset swapped / carries one independent piece of information" = one element; pure grouping is wrapped with a container. When in doubt, **prefer splitting finer** (container + children), don't cram a whole region into one element.

## 8. Getting it running (with the toolchain)

This DSL has **two entry points**, sharing the same renderer:

```
entry 1 find screenshot ─[tool 1 capture skill]─► <screenID>.md ─► ui_render ─► html/svg ─► into patterns/
entry 2 aigd discussion ─► rules ─► <screenID>.md ───────────────► ui_render ─► html (with theme skin) playtest
```

```
python ui_render.py <screenID>.md <out>.html --svg <out>.svg [--skin theme.skin.json]
   │  no z → no error (indent/document-order fallback); missing z only reminds — better to fill in before capture into the library
   ▼  outputs html (L0 line art / L1 skin / L2 atmosphere + calibrate) + svg snapshot; eyeball vs the original → calibrate-tune, export back to md
```

Sample: the bundled `references/ui-dsl-example.md` (compliant, directly renderable); after capture into the library, see also `patterns/ui-patterns/<game>/<screenID>.md`. This package's tests (`scripts/tests/`) use an inline `SAMPLE` + that bundled sample, **depending on no project-instance path**.

**Part slicing (tool 3 · optional)**: `ui_slice.py <screenID>.md <originalImage> [outdir]` slices the original image by bbox into per-element png (`shape=circle` adds a circular alpha mask, declaration-driven) + an `index.md` contact sheet (thumbnails + bbox table), splitting a competitor UI into reference-able / replaceable assets; `--only bgSlot,artSlot,iconSlot` slices only the art slots. Same family as `ui_palette.py` (color sampling, §9): both reuse `parse_dsl`, need Pillow, deterministic.

## 9. Skin (coloring) — separated from structure, re-skinnable / themeable

**Coloring is not written on the element line**, it's gathered into the md's `## Skin` section (the whole section can be deleted or swapped; delete it and it falls back to the type-default L1). Keys are of two kinds:

```
## Skin
nodeVIII  #ffc2ec / #be69aa     # by id — precise to a specific element (common for competitor sampling)
button    #2b2f3a / #ffffff     # by type — generalized to a class (project theme / brand color)
```

- Format: `key  #fill[/#text]` (key first, color after). A line starting with `#` is treated as a comment.
- **Color-lookup priority**: `id` → `type` → base type before `·` (`button·primary` → `button`) → built-in L1 gray.
- **Reserved key `@canvas`**: corresponds to no element, sets the **canvas background color** (html stage / svg root rectangle) + the default fill/text for elements with no theme. It must be set to produce a light-color brand (e.g. cream), otherwise the stage is still a dark base.
- **Three sources, one unified interface**:
  - **Entry 1 competitor sampling**: `ui_palette.py <screenID>.md <originalImage> --merge` samples each element's main color / text color by bbox, **written as a `## Skin` section (by id)** (`shape=circle` takes the center to avoid background dominance); afterward `ui_render.py` rendering that md uses the real colors, **without needing `--skin`**.
  - **Entry 2 project theme style**: list a theme of brand colors **by type** (see the sample `example.skin.json`: `{"button":{...},"panel":{...},"bgSlot":{...}}`), pass `ui_render.py <screenID>.md … --skin <theme.skin.json>` once, and **any structural DSL renders into the project's unified style**; the brand colors are maintained in this one place.
  - **Hand-written**: just write a few lines in the md's `## Skin` section.
- **Override**: `--skin` overrides same-keyed entries in the md's `## Skin` section; the more specific `id` takes priority over `type`.
- You can also do `ui_palette.py … out.skin.json` to output a standalone json module (not written back into md).

## 10. Screen/module and resolution (non-fullscreen · own dimensions)

The screen-header blockquote may declare `> Type:` and `> Size:`, by which the renderer sets the stage pixels (no longer hard-coded):

```
> Type: module          # screen (default) / module
> Size: 1600×120        # stage pixels; separator × / x / *
```

- **An element's `@{}` is a percentage relative to this canvas (Size)**; a module can be **rendered independently** (stage = module Size).
- **Two resolution entry points** (UI design spec §I, 20:9):
  - **Slicing screenshots**: landscape locks height = 1080, portrait locks width = 1080, the other axis follows the original image's ratio — at capture, use `ui_render.recommend_size(origW, origH)` to compute and write into `> Size`.
  - **Discussion/self-test**: `> Size` default = **`2400×1080`** (landscape mobile baseline; for portrait rewrite to `1080×2400`).

## 11. Instances and references (module reuse)

A screen can reference a module and reuse its structure. First declare alias → path in `## Refs`, then place it in Layout with `[instance·alias]`:

```
## Refs
resourceBar = ui-dsl-example-resourcebar.module.md   # alias = relative path (relative to this screen file; --modules <dir> as a fallback search)

## Layout
topResourceBar :top [instance·resourceBar] @{0 0}        z=9   # default: placed at original pixels (no scaling)
popup          :pop [instance·confirmBox] @{30 30 40 40} z=7   # optional: contain-scaled into the box (centered, aspect preserved)
```

- **Two placement modes**: `@{x y}` = the module is placed at **its own original pixel size** at (x,y) (screen share = moduleW/screenW, moduleH/screenH, **no scaling**); `@{x y w h}` = scaled into the box by `object-fit: contain`, aspect-preserved and centered.
- **Flatten**: before render/slice, `resolve()` replaces instances with the module's flattened absolute elements; downstream `ui_render/slice` is unchanged (`ui_palette` is a capture tool and does not flatten).
- **id namespace**: after flattening, an element id = `instanceId.moduleId` (e.g. `top.gold`); multiple instantiations of the same module don't collide and are traceable.
- **Single z layer**: an instance as a whole lands on the instance's z (the module's internal z only sets the within-group stacking).
- **Skin**: the module's own `## Skin` is baked onto each namespaced id at flatten time; the screen's `--skin`/theme covers, by type, whatever wasn't colored.
- **Nesting**: a module can reference a module, recursive flattening + cycle detection (a loop errors out).
- **Instance calibration**: the html top's "Layout" tier draws the instance as a draggable placeholder box (native: drag only, no scale; contain: drag and scale) → "Export DSL" outputs the instance line to paste back into the screen md; to change the module internals, edit the module file.
- CLI: `ui_render.py screen.md out.html --modules <moduleDir>` (when the module is not beside the screen).
