# Scratch Pad

Per-session ephemeral notes. Wipe at session start unless explicitly continuing prior work. **Anything that should survive -- move to DECISIONS, LESSONS, or ARCHITECTURE before ending the session.**

---

## Session: 2026-06-01 -- CLAUDE.md v4 update review

**Goal**: User edited CLAUDE.md (uncommitted); review diff, execute implied work.

**Diff summary** (working tree vs committed v3):

| Change | Disposition |
|---|---|
| Env fact: Debian Distrobox on openSUSE host; "use LSP servers + REPLs (bgcmd)" | Forward-looking capability hint. Deferred to user (see Open). |
| "skills, plugins, etc." | Wording. |
| NEW: keep home dir clean; pkg-mgr cleanup; fix dangling symlinks / unused dirs | Acted: removed stale `__pycache__`. Home dir: no dangling symlinks; toolchain/tool dirs (`.cargo`/`.opam`/`tweakcc-*`/...) are out of project scope, untouched. |
| Prose: "dry, direct, concise, precise; assume technical proficiency" | Go-forward writing style. |
| NEW: memory entries must add value beyond docs/codebase/git; no superfluous pkg versions | Acted: trimmed version pins in ARCHITECTURE.md -> [DEC-006]. |
| Modularity rephrased to positive constraint ("tight scope in every change") | Go-forward (pink-elephant compliance). |
| NEW: TDD/red-green-refactor; multi-agent councils/teams; subagents always use most-advanced model | Go-forward. Already in CLAUDE.md; not restated in `.agent/` (restating = bloat). This task done directly (KISS) -- too small to warrant subagents. |
| NEW: consider agent-oriented prog languages (agentlanguages.dev) + AI-targeted tooling | Exploratory. Deferred to user (see Open). |

**Actions taken**:
1. ARCHITECTURE.md version trims: `driver.js 1.3` -> `driver.js`; `uv ≥ 0.11` -> `uv`; `Python 3.13` -> `Python 3` / point to `pyproject.toml`. Source of truth = `pyproject.toml` + `templates/index.html`. -> [DEC-006].
2. Removed orphaned `./__pycache__` + `./scripts/__pycache__` (held stale `smt_runtime.cpython-313.pyc` for a module deleted in the SMT->Lean migration, cf [LSN-003]). Verified `import app` -> `IMPORT_OK`; regenerated cache orphan-free.
3. SCRATCH refreshed; [DEC-006] appended.

**Resolved (user)**: Both forward-looking capability hints (AOP / AI-tooling; LSP + `bgcmd` REPL setup) -> **defer both**, task-driven not speculative. Recorded as [DEC-007] so future sessions don't re-litigate.

**Status**: complete. Committed `a9cbc72` (hygiene sync) + DEC-007 follow-up.
