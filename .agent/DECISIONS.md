# Decisions Log

Append-only ADRs. Newest on top. IDs ascending and permanent.

Format per entry:
```
## [DEC-NNN] YYYY-MM-DD — One-line summary

**Context**: …
**Decision**: …
**Alternatives rejected**: …
**Rationale**: …
```

---

## [DEC-010] 2026-06-01 — Canonical gauge relocated to global `$HOME/.claude/compaction.sh`; repo-root copy removed (supersedes [DEC-008])

**Context**: The user moved `compaction.sh` out of lean-cds. `$HOME/.claude/compaction.sh` is now a symlink → `pro/agents/claude/compaction.sh` (a sibling tree *outside* this repo), and the 2026-06-01 CLAUDE.md edit references it path-fully as `$HOME/.claude/compaction.sh` while lowering the wrap-up threshold 90% → 80%. The global script is a newer, evolved version: dual-mode (manual transcript read when `CLAUDE_CODE_SESSION_ID` is set; statusline stdin-JSON otherwise — realizing the [DEC-009] statusline finding) and color-coded (red ≥80%, yellow ≥60%, encoding the new threshold). The tracked repo-root `compaction.sh` was the older single-mode fork still carrying the stale `>=90%` comment — a drifted duplicate. Verified this session: the global gauge runs clean (`15% 30K/200K`) via `$CLAUDE_CODE_SESSION_ID`.

**Decision**: `git rm` the repo-root `compaction.sh`. The canonical gauge is the global `$HOME/.claude/compaction.sh`, owned outside this repo and shared across the user's projects; lean-cds no longer vendors a copy. CLAUDE.md (read #1) is the sole pointer — no `.agent/` doc restates the path or threshold. Supersedes [DEC-008]'s repo-root placement; the adopt-as-canonical intent carries forward.

**Alternatives rejected**:
- Keep the repo-root copy as a fresh-clone fallback — reintroduces the exact drift it already showed (90% vs 80%; single- vs dual-mode), the anti-pattern [DEC-006] targets. The agent always runs in this sandbox where the global symlink resolves, so a vendored copy serves no reader.
- Sync the repo-root copy to match global — perpetuates two truths for a tool the user has made global agent-meta, not lean-cds code.
- Edit the global script from here — it lives outside the project root (CLAUDE.md scope rule) and already encodes 80%; nothing to fix.

**Rationale**: Completes the trajectory [DEC-008] ("portable, universal agent tool") and [DEC-009] (cross-project agent UX belongs at user/global level) only gestured at — the gauge is now physically global, so the repo-local duplicate is vestigial. Single source of truth, zero drift; the repo carries only lean-cds-specific content.

---

## [DEC-009] 2026-06-01 — No project-local statusline in lean-cds; context gauge stays CLI-only here

**Context**: This session explored wiring `compaction.sh` into a Claude Code `statusLine` (`.claude/settings.json`) so context usage shows every turn. Three implementations were verified against mock stdin: reuse `compaction.sh` via its `CLAUDE_CODE_SESSION_ID`/`CLAUDE_CONTEXT_WINDOW` override knobs; a native `jq` one-liner over the stdin JSON; or plain `compaction.sh`. Before choosing, the user decided to build a **single global statusline used across all their projects** instead.

**Decision**: Do **not** add a project-local `statusLine` to this repo. `compaction.sh` remains the committed CLI gauge ([DEC-008]); in-UI context display is handled by the user's global statusline (`~/.claude/settings.json`), outside this repo's scope. The probe `.claude/settings.json` created during exploration was reverted; no `.claude/` is tracked.

**Alternatives rejected**:
- Project-local `statusLine` (any of the three implementations above) — redundant with the user's global statusline, adds per-repo UI config to maintain, and a project setting can conflict with the global one.

**Rationale**: A statusline is cross-project agent UX, not lean-cds infrastructure — it belongs at the user/global level, matching the "portable, universal tool" framing in [DEC-008]. Recorded here rather than only in the ephemeral SCRATCH so future sessions do not resurface the offer.

**Reusable finding** (for any statusline, including the global one): the `statusLine` stdin JSON carries live context — `context_window.used_percentage`, `context_window.context_window_size` (200000, or 1000000 on the 1M beta), and `context_window.total_input_tokens` (= `input + cache_creation + cache_read`, the same input-only formula `compaction.sh` derives from the transcript jsonl). A newly-added shell-executing `statusLine` needs a Claude Code restart + workspace-trust accept to activate (no mid-session hot-reload).

---

## [DEC-008] 2026-06-01 — Adopt `compaction.sh` as canonical context gauge; lives at repo root

**Superseded by [DEC-010]** (2026-06-01): the gauge moved to global `$HOME/.claude/compaction.sh` and the repo-root copy was removed. The repo-root placement decided below no longer holds; the adopt-as-canonical intent carries forward.

**Context**: The 2026-06-01 CLAUDE.md edit adds a compaction workflow — "As you cross 90% usage of your context window, prepare yourself for compaction … Monitor your context usage often using the supplied `compaction.sh`" — and ships `compaction.sh` (untracked, executable, read-only `sh`+`jq`). It prints the latest main-thread turn's context usage as `NN% used/window` (e.g. `15% 30K/200K`), resolving the window from launcher env (`CLAUDE_CODE_DISABLE_1M_CONTEXT` ⇒ 200K, else 1M; `CLAUDE_CONTEXT_WINDOW` overrides). Verified this session: runs clean, `jq-1.7` present, `git check-ignore` confirms trackable, and it resolves *this* session's jsonl via `$CLAUDE_CODE_SESSION_ID` even with newer sibling-project sessions present (SID-first, not merely newest).

**Decision**: Adopt as the canonical context gauge. Keep it at **repo root**, tracked, unmodified. Documentation surface is this entry plus the script's own header. The *workflow rule* (monitor often; wrap up cleanly ≥90% for a user-issued `/compact`) stays solely in CLAUDE.md; it is not restated in SESSION_PROMPT.md or INDEX.md.

**Alternatives rejected**:
- Move to `scripts/` — that dir is app-scoped (`check_scenarios.py` verifies the Lean app); `compaction.sh` is agent-meta, reads Claude Code session files, orthogonal to lean-cds.
- Move to `.agent/` — that tree is markdown memory; an executable changes its character, and the tool is portable across projects, not lean-cds-specific memory.
- Restate the workflow in SESSION_PROMPT.md / INDEX.md — violates [DEC-004] (prompt defers to CLAUDE.md) and [DEC-006] (carry only info not recoverable elsewhere); CLAUDE.md is read #1 and the script self-documents.
- Rewrite/wrap the script — it is correct and fit-for-purpose; gratuitous churn.

**Rationale**: CLAUDE.md references it path-lessly as "the supplied `compaction.sh`," signalling a portable, universal agent tool (works in any Claude Code project) — root placement matches that framing and keeps it visible. One durable record (this DEC) + the self-documenting script + the CLAUDE.md directive covers future sessions with zero redundancy.

**Note**: The same CLAUDE.md edit adds subagent rate-limiting guidance ("sequential chunking; verify all agents ran to completion") — go-forward operational behaviour already captured in CLAUDE.md, no separate action needed.

---

## [DEC-007] 2026-06-01 — Capability investments (AOP tooling, LSP/REPL setup) are task-driven, not standing

**Context**: The 2026-06-01 CLAUDE.md edit adds two forward-looking capability hints: "consider … agent-oriented programming languages … as well as any other tooling … that targets AI" and "Make full use of … LSP servers and REPLs." Asked whether to act now, the user chose **defer both**.

**Decision**: Treat both as standing encouragements, not speculative this-session work. Stand up LSP servers / `bgcmd` REPLs, or trial an agent-oriented language, when a *concrete coding task* would materially benefit — evaluate per task. The current docs/maintenance phase triggers neither.

**Alternatives rejected**:
- Set the tooling up speculatively now — investment with no active consumer; risks the home-dir/project cruft the same CLAUDE.md edit's clean-up directive warns against.
- Read the hints as a one-time prompt and drop them — they are standing guidance; this entry records *timing*, not rejection.

**Rationale**: Avoids speculative setup and prevents future sessions re-asking, while preserving the CLAUDE.md encouragement. Re-evaluation trigger is explicit: a coding task the tooling demonstrably accelerates.

---

## [DEC-006] 2026-06-01 — Docs carry only version info a grep can't cheaply recover

**Context**: CLAUDE.md (2026-06-01 edit) added: entries "must provide value beyond what the project documentation, codebase, and Git history already provide; superfluous information like package versions only add bloat and the potential for drift." ARCHITECTURE.md carried precise pins (`driver.js 1.3`, `uv ≥ 0.11`, `Python 3.13`) that duplicate `pyproject.toml` (`requires-python >=3.13`, `litestar>=2.13`, `uvicorn>=0.34`) and `templates/index.html` (`driver.js@1.3.1`, `htmx.org@2.0.4`). `driver.js 1.3` was already mildly stale vs the actual `1.3.1`.

**Decision**: `pyproject.toml` + `templates/index.html` own exact versions. ARCHITECTURE.md keeps a version token only when the *major* is load-bearing architecture — i.e. the major changes the API an agent codes against (`Lean 4`, `Litestar 2`, `HTMX 2`). Precise minor/patch pins are dropped; where the exact value matters, the doc points to the file the toolchain actually reads. Historical version mentions inside postmortems (e.g. `v4.29.1` in [LSN-002]) stay — they narrate a past incident, not current config.

**Alternatives rejected**:
- Strip every version token — loses the major-version API signal (`Litestar 2` vs `1` is a real code difference) for no drift reduction (majors rarely churn).
- Keep all pins — the exact duplicated drift surface the new rule targets; `driver.js 1.3` had already drifted.

**Rationale**: Single source of truth is the file the toolchain reads, not a prose mirror of it. The doc carries only what an agent cannot recover with one `grep pyproject.toml`. Generalises the DEC-005 single-source principle from prose sections to version tokens.

---

## [DEC-005] 2026-05-14 — README.md collapsed to a 6-line stub; ARCHITECTURE.md is canonical

**Context**: README.md (220 lines) duplicated ~104 lines of ARCHITECTURE.md content (Stack table, File/Project layout, Routes / Public surfaces, Verification pipeline / Data flow) and additionally contained a `## Scenario data model` section that pasted Python dataclass defs from `scenarios.py` verbatim. ~47% of the README was duplication. Same drift class as DEC-004 (SESSION_PROMPT ↔ CLAUDE.md). The discrepancy in route paths (README correct, ARCHITECTURE.md wrong — `POST /verify` vs actual `POST /scenarios/{id}/verify`) surfaced only during the diff pass and is logged as [LSN-004].

**Decision**: ARCHITECTURE.md is now the canonical technical reference for the project. README.md is a 6-line stub: title, one-sentence what-is, and four links (ARCHITECTURE.md, INDEX.md, CLAUDE.md, LICENSE). Unique README content (Prerequisites, Quick start, Adding-a-scenario procedure, Common dev tasks, Limitations, bilingual orientation paragraph, patient names per scenario) was absorbed into ARCHITECTURE.md. Route paths corrected against `app.py` grep.

**Alternatives rejected**:
- Aggressive (~50 lines, keep Prerequisites/Quickstart/License in README) — still maintains two truths; trim the rest.
- Moderate (cut verbatim duplicates only) — leaves README as parallel doc; drift surface remains.
- User picked the strongest option (full elimination); the .agent/-as-canonical model is the natural endpoint for an AI-developed project where humans are not the primary readers.

**Rationale**: Single source of truth eliminates the entire drift class. ARCHITECTURE.md grew from 80 → ~165 lines (absorbed content) but the duplicate surface is gone. GitHub viewers still get the four pointers from the stub.

---

## [DEC-004] 2026-05-14 — SESSION_PROMPT.md defers to CLAUDE.md instead of restating it

**Context**: Original `SESSION_PROMPT.md` (~42 lines) restated ~12 rules already present verbatim or near-verbatim in `CLAUDE.md`: sudo, env-modification, git-locally-only, ask-when-ambiguous, accuracy-over-completion, failure-acceptable, LLM-optimized files, immutable CLAUDE.md, web-search-for-SOTA, pink-elephant negative-constraint framing, conversational-chat-reserved-for-blockers, ambitious-work-welcomed. Two harms: (a) any drift between the two files silently contradicts; (b) bootstrap tokens spent restating known facts instead of project-specific orientation.

**Decision**: SESSION_PROMPT.md keeps only project-unique content — identity (lean-cds, Lean 4 / Python / Litestar, JA default), `.agent/` read order, project tooling (`uv`, `./.elan/bin/lean`, `check_scenarios.py`), grep-LSN-first reminder, and the self-update meta-instruction. CLAUDE.md is the single source of truth for universal philosophy; the prompt explicitly defers to it.

**Alternatives rejected**:
- Keep restating for emphasis — drift risk + token cost outweighs emphasis benefit; CLAUDE.md is read first anyway.
- Merge SESSION_PROMPT.md into INDEX.md — different audience (user-paste vs. agent-internal); keeping them separate preserves clean entry points.
- Auto-generate the prompt from CLAUDE.md + INDEX.md — over-engineered for a file the user pastes once.

**Rationale**: Reduces SESSION_PROMPT.md from 42 → 19 lines (~55% reduction). Eliminates duplication-induced drift surface. Future agents still get full context because CLAUDE.md is item #1 in the read order.

---

## [DEC-003] 2026-05-14 — Newest-on-top ordering for append-only logs

**Context**: DECISIONS.md and LESSONS.md will be partial-read by future agents. Two ordering options: chronological (oldest top) vs. reverse-chronological (newest top).

**Decision**: Newest on top. Numeric IDs ascend (DEC-001, DEC-002, …) but appear in reverse position order.

**Alternatives rejected**:
- Chronological with an "Active" summary at the top — doubles maintenance.
- Strictly chronological — buries recent context behind history.

**Rationale**: LLMs partial-reading these files benefit most from front-loaded recent relevance. The cost (ID order differs from position order) is minor; IDs are still discoverable by grep.

---

## [DEC-002] 2026-05-14 — Memory system lives at `.agent/`

**Context**: New CLAUDE.md mandates a memory/scratchpad system. Candidates: `.agent/` (new top-level), `artifacts/agent/` (under existing artifacts), `.claude/` (per-machine harness state).

**Decision**: Top-level `.agent/`, version-controlled.

**Alternatives rejected**:
- `artifacts/agent/` — mixes ephemeral build output with durable agent state.
- `.claude/` — conventionally gitignored; would not sync to fresh clones / new machines.

**Rationale**: Top-level visibility, git-tracked, easy to discover (`ls` shows it), separable from `.claude/` (harness state) and `artifacts/` (build output).

---

## [DEC-001] 2026-05-14 — Drop the old CLAUDE.md operational rules entirely

**Context**: CLAUDE.md was rewritten from a structured rule set (modern tooling, theme awareness, no backend info in UI, isolated venvs, two-phase research/implementation workflow, enterprise UI) into a meta-instructional philosophy. The user was asked whether to migrate the old rules into the new memory system as "inherited norms" or drop them; they chose drop.

**Decision**: Treat the new CLAUDE.md as the sole source of truth. Old rules are **not** migrated into `.agent/`.

**Alternatives rejected**:
- Migrate as inherited norms — would silently re-introduce constraints the user removed.
- Rule-by-rule decision — overhead without proportional value.

**Rationale**: User intent is explicit. The codebase already follows most former rules de facto; dropping the *documented* rule loosens future agents' latitude but doesn't change current behavior. If a former rule turns out to matter, it can re-surface via a new DEC-NNN entry.
