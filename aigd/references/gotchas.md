# AIGD common-mistakes quick reference (pitfalls actually hit)

> **Purpose**: skim before working with `aigd-system`/`aigd-handoff`. The pitfalls here are **all ones exposed during actual development/validation with AIGD** (project details neutralized), not textbook examples — each gives symptom / root cause / correct practice.
> Numeric/economy design traps are separately covered in [`patterns/numeric-traps/numeric-traps.md`](patterns/numeric-traps/numeric-traps.md); this page is for the **execution + handoff + validation** kind.

---

## A. Tool execution / writing files (the easiest "thought I did it but didn't")

| Mistake | Symptom | Root cause | Correct practice |
|------|------|------|---------|
| **Malformed tool call silently doesn't execute** | "blew up again / is it written yet?"; file not written, command not run, yet you think it's done | the function-call block format doesn't meet the harness's requirement (e.g. Claude Code missing the `antml:` prefix) → silently discarded | **Check the format before sending + double-check the artifact after** (confirm it actually landed with read-file / `ls`); if the user says "blew up" → first admit it didn't execute, check the actual state, resend verbatim. Per-harness formats in `harness-adapt.md` |
| **Chinese file gets a BOM added / turns into UTF-16** | downstream reads garbled or fails to parse | used a writing method that adds a BOM (e.g. bare PowerShell `Out-File`/`Set-Content`) | confirm UTF-8 without BOM before writing to disk (Claude Code's Write defaults to no BOM; PowerShell uses `UTF8Encoding $false`), see `harness-adapt.md` |
| **Delete/edit is irreversible** | accidentally deleted the user's source file, overwrote filled config | the repo is **not git**, delete/rename has no rollback | **Read the content first** before touching an existing file; **never touch / never overwrite** the user's source xlsx and filled config; before deleting an artifact, confirm it's an artifact, not a canonical source |
| **Bare `|` in a table breaks columns** | markdown table column count misaligned (MD056) | wrote a literal `|` in the content (e.g. the position-encoding formula `(X+1)<<16)|(Y+1)`) | use `/` or escape `\|` in the content column |

## B. Design / coding conventions (the source of forked reads downstream of the handoff package)

| Mistake | Symptom | Root cause | Correct practice |
|------|------|------|---------|
| **Sentinel value collides with a legal value** ⚠️ | the top-left cell is unusable; `0` is both "none" and a legal encoding | using `0`/empty as the "none" sentinel, but the legal domain contains 0 or the encoding can compute 0 (e.g. grid position encoding of the top-left corner (0,0)→0 collides with the "in inventory" sentinel) | before using `0` as a sentinel, confirm the **legal domain doesn't contain 0 and no encoding path produces 0**; for encoding types, `+1` each to make room for the sentinel |
| **Operator precedence written wrong (even in pseudocode)** | downstream implements per the pseudocode and gets a wrong value | e.g. `pos>>16 - 1` is actually `pos>>15` (shift has lower precedence than subtraction) | add explicit parentheses even in formulas/pseudocode: `(pos>>16)-1`; give the proto comment the full formula |
| **Bare numbers stuffed into prose** | a number changed but the doc forgot to update, dual-canonical drift | the rule doc hard-codes numbers directly instead of referencing config | prose has **no bare numbers**: write only formulas + `table[primaryKey].field` references; numbers live in the xlsx |
| **Decided a pending convention for the user** | a number/rule locked into the spine actually wasn't decided | took it on yourself to decide a `[to-confirm]` to avoid hassle | always list pending items as `[to-confirm]` for the user to decide; **the AI does not decide numbers/conventions on their behalf** |

## C. Validation / handoff (machine-check > self-assessed checkboxes)

| Mistake | Symptom | Root cause | Correct practice |
|------|------|------|---------|
| **config↔doc desync** ⚠️ | the doc layer all passes, downstream still implements a fork | **doc defined first, xlsx changed later without backfill** (the number-one root cause of forked reads of the handoff package) | before finalization **always run** `config_check` (schema) + `value_check` (data integrity), only 0 major counts as passing; don't just tick the "validation checklist" box self-assessed |
| **Validator false positive (empty sentinel / empty cell)** | false `FK_BREAK`/false `ACC_DANGLING`, credibility collapses | `0`=no-reference treated as an id and queried as a foreign key (some "next form id" field = 0); an empty optional cell treated as a missing row (some optional field left blank) | skip foreign-key empty sentinels `{0,0.0}` (precondition: id is always positive); use `row_exists` to distinguish **missing row vs empty field**; **prefer under-reporting over false-reporting**, and if you can't resolve it, mark rather than fabricate |
| **Object-array header missed in parsing** | config columns swallowed, a pile of false majors reported | array closure only recognizes `]`, missing the object-array `max}]` | use `"]" in nm` for closure detection; array columns **don't compare scalar types** (mixed sub-types have no single type) |
| **Spine cross-table inconsistency** | module-code unregistered, dependency points at a nonexistent system, finalized but missing proto | the manifest's 6 tables hand-written, not machine-checked | after writing the spine, run `manifest_check`, fix majors first before continuing (see the self-check section in `templates/manifest.tpl.md`) |

## D. Delegating to sub-agents (consumer-side validation / parallel production)

| Mistake | Symptom | Root cause | Correct practice |
|------|------|------|---------|
| **Blindly trusting a sub-agent's assertion** | changed something based on a "gap" the sub-agent reported, when there was no gap | the sub-agent claims the config is missing some data (e.g. falsely reports an array has only 1 member, actually 3) | personally verify the gap/bug the sub-agent reports against the xlsx first-hand, then decide whether to change |
| **Sub-agent writes garbage into the ledger** | CHANGELOG mixed with records of scaffolding/artifacts | the recording boundary wasn't spelled out when delegating | agree that **`.uploads/` scaffolding and intermediate artifacts are not written to CHANGELOG**; state this clearly when delegating; for parallel writes to the same file, re-read the tail before appending |
| **Sub-agent's injected project snapshot is stale** | the sub-agent reports "some file is still the old value" but the disk is already the new value | the sub-agent holds a snapshot of the project context from the start of the session, lagging mid-session edits | take the **actual disk content as authoritative**, don't judge by the sub-agent's snapshot; if in doubt, Read the current file first |
