# AIGD — AI-assisted game design methodology (portable skill package)

Turns **game system design** into a **platform-agnostic handoff package** that another AI (or person) can develop directly from; and ships **deterministic checkers** that gate the handoff package to "consumable" before letting it through.

> In one line: `aigd` doesn't decide your numbers for you, doesn't bind to an engine — it's a **discussion-driven** design flow + a set of **machine-check scripts**, producing system docs where "rules / config / contract / acceptance" are four-way aligned and downstream guesses nothing.

---

## What it solves

The most common failure in game-design handoff isn't too little documentation, it's **docs and config quietly drifting out of sync** ("doc fixed first, table changed later without writing it back"), with downstream AI/programmers each reading their own → forked implementations. AIGD blocks it three ways:

1. **Structured output (the 6-piece set)** — every rule tagged with a number, every value living in a config table, prose only referencing `table[primary key].field`, eliminating room for interpretation.
2. **Explicit ledgering of the undecided** — any uncertain convention is uniformly tagged `[to confirm]` and handed to a person to decide, the AI doesn't decide; these marks happen to predict exactly where downstream will fork.
3. **Deterministic machine checks** — `config_check`/`value_check`/`manifest_check` turn the "config↔doc↔spine" consistency into an exit code, 0 major counts as handoffable.

---

## Output: a system's "6-piece set"

| # | Artifact | Audience |
|---|------|------|
| 1 | Functional rules (tagged with `R-` numbers + UI DSL) | everyone |
| 2 | Config table (self-describing header xlsx, with test data) | numbers |
| 3 | Config spec (per-field type/range/reference) | numbers + table export |
| 4 | Interface contract (proto, client = server, one copy) | front + back end |
| 5 | UI spec + single-file clickable prototype | art + client |
| 6 | Acceptance cases (Gherkin, tagged with `R-` numbers) | testing |

During iteration only the "cheap, will-change" ones are produced (rules/config/prototype), the "expensive, downstream" ones are produced only after finalization (contract/acceptance/backend) — don't lock the contract while the design is still fluid.

---

## Package structure

```text
aigd/                  ← this package · orchestrator + methodology source of truth
├── SKILL.md           orchestrator: read spine → judge progress → dispatch to sub-skill
├── README.md          ← the one you're reading
├── references/        the single source of truth for the methodology (no copying, no drift)
│   ├── methodology.md       design interview / naming / numbering / the eight gates
│   ├── ui-dsl-spec.md        the grammar contract for screenshot→DSL
│   ├── gotchas.md       execution/handoff/check pitfalls actually stepped on
│   ├── templates/           the three spine templates (project charter / manifest / implementation master guide)
│   ├── patterns/            domain rounds (core loops / progression paradigms / number traps)
│   └── scripts/             deterministic check/tool scripts (mostly pure stdlib) + tests
└── examples/
    └── potion-crafting/     ← self-contained toy sample, runs the 3 checkers through
aigd-concept/   Phase 1 concept → system list + spine
aigd-system/    Phase 2 single-system design (rules/config/prototype)
aigd-iterate/   Phase 3 playtest iteration
aigd-handoff/   Phase 4 finalize → contract/acceptance/handoff package
aigd-sync/      cross-cutting: sync-back integration + mark recheck
aigd-ui-capture/ tool: UI screenshot → UI DSL
```

**Install the whole package, can't be split**: the 6 sub-skills go **at the same level** as `aigd/` in the host's skills directory (e.g. Claude Code's `.claude/skills/`). Sub-skill bodies use `../aigd/references/` to fetch the methodology, so `aigd/` must exist at the same level.

---

## Getting started

1. **Install**: copy the following **7 folders (no more no less)** as a whole into the host's skills directory (Claude Code = `.claude/skills/`), keeping them **at the same level**:

   ```text
   aigd/            ← orchestrator + references/ (contains the methodology, scripts, templates, patterns, examples)
   aigd-concept/    Phase 1 concept
   aigd-system/     Phase 2 single-system design
   aigd-iterate/    Phase 3 iteration
   aigd-handoff/    Phase 4 finalize & handoff
   aigd-sync/       sync-back integration
   aigd-ui-capture/ UI screenshot→DSL
   ```

   - **All 7 must be copied and at the same level**: sub-skill bodies use `../aigd/references/` to fetch the methodology, missing `aigd/` or a wrong level breaks the link.
   - **Don't copy** other skills in the skills directory unrelated to aigd (they belong to their own projects); `.gitignore` can be copied or not, either way.
   - After installing, that directory should contain **exactly** these 7 `aigd`/`aigd-*` folders.
   - **Switching harness**: ZCode installs to `~/.zcode/skills/`; Gemini `~/.gemini/skills/` (or `gemini skills install <repo>` to install in one step); Codex `~/.codex/skills/` (or its built-in skill-installer). The `SKILL.md` format is common across these and already tested; **Copilot 1.0.63 has no skills mechanism, needs adapting**. Where to install, how to invoke, tool-name mapping: see [`references/harness-adapt.md`](references/harness-adapt.md).
2. **Running the checkers needs Python** (most scripts are pure standard library; `ui_palette`/`ui_slice` need Pillow, `gherkin_to_checklist` writing xlsx needs openpyxl, see `references/scripts/requirements.txt`).
3. **New project**: call `aigd` (let it route if you don't know which step you're at) or directly `aigd-concept` to set the concept and build the spine → `aigd-system` system-by-system design → finalize with `aigd-handoff`.
4. **Get a feel first**: go into [`examples/potion-crafting/`](examples/potion-crafting/), follow its README to run the 3 checkers once, and see what "6-piece set + machine-check gating" actually looks like.

---

## Checkers (references/scripts)

| Script | What it manages | Dependency |
|------|--------|------|
| `config_check.py` | config spec ↔ xlsx **schema drift** (column/type/table-name/domain) | stdlib |
| `value_check.py` | config **data integrity** (foreign-key breakage/dangling acceptance/coverage·monotonic·cardinality) | stdlib |
| `manifest_check.py` | spine **manifest self-consistency** (module-code registration/dependency targets/status/chunking/dependency-cycle SCC) | stdlib |
| `ui_render.py` | UI DSL → clickable html/svg wireframe | stdlib |
| `gherkin_to_checklist.py` | acceptance cases → designer-facing checklist xlsx | openpyxl |
| `xlsx_dump.py` | any xlsx → text (sidesteps openpyxl's errors on domestically-exported tables) | stdlib |

All **argv-driven, zero project hardcoding, deterministic** (CI-ready). See [`references/scripts/README.md`](references/scripts/README.md). Non-zero exit code = has major, wired into the finalization gate.

---

## Portability & status

- **Cross-harness**: the package structure (`SKILL.md` + `name`/`description` frontmatter) is common across **Claude Code / ZCode / Gemini CLI / Codex**; the only differences are which directory to install to, how to invoke, and the read/write tool names — see [`references/harness-adapt.md`](references/harness-adapt.md). The methodology itself depends on no harness, nor on its instruction files (`CLAUDE.md`/`AGENTS.md`/`GEMINI.md`). The checker scripts are argv-driven command lines, used the same everywhere as long as there's Python.
  > **Tested status (2026-06-23)**: tested working in practice across four harnesses — **Claude Code (native · real project), ZCode 3.1.3 (Claude family), Gemini CLI 0.47 (Google), Codex 0.140 (OpenAI)** — discovery + routing + execution all passing, **including the two cross-vendor ones Gemini and Codex**; Gemini/Codex can also install from this repo in one step with their respective native installers. **Copilot CLI 1.0.63 was tested and has no SKILL.md skills mechanism** (goes through AGENTS.md/MCP/plugin), aigd needs adapting. See [`references/harness-adapt.md`](references/harness-adapt.md).
- **Scope of applicability**: manages the structure and consistency of design handoff, **not number balance**; the html prototype verifies information architecture/flow, **can't verify feel/timing/networking** (real-time combat types only verify information architecture); best suited for UI-dense systems. See the repo root `README.md` "Scope of applicability".
- **Project-specific** (concept/conventions/system list/number ranges) all lives in the **spine** (`project charter`/`manifest`), not in this package — switch projects, switch AI, just read the spine to pick it up.
- `patterns/` is a starter pack that will grow (currently: 5 core loops / a combat-unit progression paradigm / 10 number traps).
