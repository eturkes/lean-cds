Continue this project (fresh session). Non-empty task below ⇒ your sole task: do exactly it, editing `.agent/roadmap.md` only if it directs you to. Empty ⇒ advance the next `## Forward` item in `.agent/roadmap.md`.

Load `.agent/roadmap.md` (status / forward / backlog), then `.agent/memory.md` (lessons + decisions); CLAUDE.md (imports `AGENTS.md`) is auto-injected. Read only what the step implicates. Navigate via LSP where available, else grep.

Do: (1) restate the task + its acceptance in one line; (2) implement from real verified inputs (deny-listed inputs off-limits; an unmet precondition stops you — report it), reusing modules, matching surrounding style; (3) VERIFY the gate `.agent/memory.md` names — `uv run python scripts/check_scenarios.py` → every scenario CollisionVerified, exit 0 — and that touched scripts exit clean; (4) record durable lessons/decisions in `.agent/memory.md` and prune the obsolete; reconcile `.agent/roadmap.md`.

Close: one scoped commit (scopedcommits.com), LLM-optimized. After a closing commit I may compact and run `/codex-review`; fix accepted findings in a follow-up commit that keeps the scope and adds a `Codex-Review: <accepted findings>` trailer.

Task (may be empty): $ARGUMENTS
