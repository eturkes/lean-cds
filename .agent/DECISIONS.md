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
