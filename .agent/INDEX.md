# .agent/ — Agent Memory System

Cross-session continuity for AI agents working on **lean-cds**.

## Read order on session start

1. `CLAUDE.md` (repo root) — operating philosophy.
2. This file (`INDEX.md`) — map of the system.
3. `ARCHITECTURE.md` — current codebase snapshot.
4. `DECISIONS.md` — top entries (newest on top).
5. `LESSONS.md` — top entries (grep before non-obvious choices).
6. `SCRATCH.md` — if continuing a prior session.

## Files

| File | Type | Purpose | Update trigger |
|------|------|---------|----------------|
| `INDEX.md` | Static | This map. | File set changes. |
| `ARCHITECTURE.md` | Snapshot | Stack, layout, data flow, invariants. | Structural change. |
| `DECISIONS.md` | Append-only | ADRs: context → decision → alternatives → rationale. | Non-trivial decision. |
| `LESSONS.md` | Append-only | Mistakes + root cause + fix + prevention. | After every observed mistake. |
| `SCRATCH.md` | Ephemeral | Per-session working state. | Continuously. Wipe at session start unless continuing. |
| `SESSION_PROMPT.md` | Static | Reusable boot prompt for fresh sessions. | Major project shift. |

## Where to write

- Made a non-trivial choice with rejected alternatives → **DECISIONS.md** (append).
- Discovered a mistake (yours or a prior agent's) → **LESSONS.md** (append).
- Structure shifted (new module, removed dep, renamed concept) → **ARCHITECTURE.md** (rewrite affected section).
- Mid-session todos, working state, open questions → **SCRATCH.md**.
- When in doubt, write it down. Future sessions inherit only what's on disk.

## Conventions

- **ID prefixes**: `[DEC-NNN]` decisions, `[LSN-NNN]` lessons, `[ARC-NNN]` architecture invariants. IDs are ascending and permanent — never renumber.
- **Newest-on-top** for append-only logs (DECISIONS, LESSONS). Front-loads relevance for partial reads.
- **ISO-8601 dates** (`YYYY-MM-DD`).
- **Markdown tables** for structured data; bullet lists for unstructured; prose only for rationale paragraphs in ADRs/lessons.
- **Anchors are grep targets**. Stable IDs let agents reference each other across files.

## Pruning policy

- `DECISIONS.md`, `LESSONS.md`: append-only during a session. If file exceeds ~500 lines, summarize entries older than 90 days into an `## Archive` section.
- `SCRATCH.md`: wipe at session start unless explicitly continuing.
- `ARCHITECTURE.md`: rewrite affected sections in place; do not leave "old version" cruft inline. If history matters, link the relevant DEC-NNN.

## Anti-patterns

- Writing prose paragraphs when a table or bullet list works.
- Restating what a name already says ("The function `verify` verifies …").
- Storing transient logs in DECISIONS/LESSONS — those go in SCRATCH.
- Renumbering IDs.
- Deleting LESSONS entries because they feel embarrassing — they're the highest-value content here.
