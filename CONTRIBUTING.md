# Contributing guide (AIGD)

## Running tests

The checker / tool scripts have pure-stdlib tests (**not pytest**: each test file ships its own runner).

```bash
cd aigd/references/scripts
for t in tests/test_*.py; do python "$t"; done     # run one by one, last line prints N/N passed
pip install -r requirements.txt                     # only ui_palette/slice (Pillow) and gherkin (openpyxl) need it
```

CI (`.github/workflows/tests.yml`) runs the whole suite on push/PR. Changing a script must keep everything green.

## Core principles (understand before changing)

1. **Single source of truth, no copying**: the methodology lives only in `aigd/references/`, the 6 sub-skills are **thin routing shells** whose bodies use `../aigd/references/` to fetch the methodology. **Don't copy the methodology content into the sub-skills** — that's 5 places to drift.
2. **Scripts: argv-driven, zero project hardcoding, deterministic** (no `Date.now`/randomness). Reading xlsx always goes through `xlsx_dump` (sidesteps openpyxl's style errors on domestically-exported tables), only "writing xlsx" uses openpyxl.
3. **Contains no specific project**: examples / test fixtures use neutral illustrative names (`unit`/`evolveLine`/`potion`…), don't hardcode a real game's table names / numbers / paths.
4. **Checkers would rather under-report than false-positive**: can't parse / can't find → flag explicitly (`*_SKIP` info), don't silently drop, don't fabricate.

## How to add things

- **Add a domain rule**: in some `<system>.checks.json`, write it per the rule schema at the top of `value_check.py` (`cardinality`/`coverage`/`monotonic`), sample in `aigd/references/scripts/checks/example.checks.json`.
- **Add a patterns round**: put it in `aigd/references/patterns/<loops|numeric-traps|ui-patterns>/`, neutralized and portable, and register it in the existing list in `references/README.md`.
- **Add a checker**: pure stdlib + argv + a matching `tests/test_*.py` (in-memory fixtures, running through "planted error gets caught + clean doesn't false-positive"), register the category / severity in `scripts/README.md`.
- **Change a SKILL.md**: keep it thin, just routing + admission/exit, point the methodology to references.

## Conventions

- Files are **UTF-8 without BOM**; use `/` paths cross-platform. Per-harness writing methods are in `aigd/references/harness-adapt.md`.
- In markdown table content columns, **don't use a bare `|`** (it breaks the table apart) — use `/` or `\|`.
- Make tool calls in the function-call format your harness requires, and **after sending, re-verify the artifact actually landed** (read the file / `ls`), don't assume it took effect.
- Cross-harness: the package structure is common across Claude Code / ZCode / Gemini / Codex (all tested; Copilot 1.0.63 has no skills mechanism, see `harness-adapt.md`). Before opening a PR, if you can test-install and run it on more harnesses, please say so in the PR.
