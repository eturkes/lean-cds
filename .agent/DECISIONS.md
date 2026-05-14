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
