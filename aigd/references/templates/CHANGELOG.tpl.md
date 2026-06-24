# CHANGELOG — Change Ledger (default: project root)

> **AIGD project-environment prerequisite** (the only one): the spine's re-entrancy relies on this — every time you change a file, append a line at the end; switching AIs / across sessions you can trace back "what was done, and why".
> Columns: `Time | File | Content | Reason | Model`. **Don't use a bare `|` in the Content column** (it breaks the table) — use `/` or `\|`.
> **Location**: defaults to `CHANGELOG.md` at the project root; can be pointed elsewhere in `project-charter "Directory layout"`.
> **The project already has a ledger** (any name) → **reuse it, don't start a new one**; this template is only for initializing when "the project root doesn't have one yet".
> The backfill rule is enforced by methodology step 5 + quality-gate item 8, and **does not depend on any host-AI instruction file** (CLAUDE.md / AGENTS.md / GEMINI.md etc. are the runtime environment's business, not AIGD's).

| Time | File | Content | Reason | Model |
|------|------|------|------|------|
| YYYY-MM-DD HH:mm | `<file>` | `<what changed>` | `<why>` | `<model name>` |
