---
description: Boot a fresh lean-cds work session. Bare `/session` runs the roadmap; `/session <TASK>` overrides it with a one-off objective.
argument-hint: [TASK]
disable-model-invocation: true
---

# Session boot — lean-cds

You are (re)starting work on **lean-cds**: a Lean 4 / Python / Litestar PoC for verifiable clinical decision support (bilingual JA/EN, JA default).

## 1. Bootstrap (always)

Read, in order:

1. `CLAUDE.md` (repo root) — universal operating philosophy; authoritative. This prompt does not restate it.
2. `.agent/INDEX.md` — memory-system map; it directs you to `ARCHITECTURE.md`, `DECISIONS.md`, `LESSONS.md`, and `SCRATCH.md` (read `SCRATCH.md` only if continuing a prior session).

Project operational notes:

- Python deps via `uv`. Lean toolchain at `./.elan/bin/lean` (preferred) or `$HOME/.elan/bin/lean`.
- Verify cheaply via execution: `uv run python -c "import app"`, `uv run python scripts/check_scenarios.py` (kernel-typechecks all 6 scenarios).
- Always grep `[LSN-` in `.agent/LESSONS.md` before non-obvious choices.

## 2. This session's objective

$ARGUMENTS

**If the objective above is blank**, no override was given — proceed through the roadmap as usual. `SPEC.md` is the authoritative build plan. Follow its §0 *Agent operating contract*: from repository state and the §11.3 build-unit table (dependency order), select the next uncompleted unit, load **only** its §11.4 reading slice plus earlier accepted artifacts (full-spec loading is reserved for spec-maintenance work — `SPEC.md` is ~3.5k lines), implement that one deliverable, run its acceptance gate, commit the artifacts, and end.

**Otherwise**, the text above is a one-session override (typically a meta/tooling task): make it the sole focus of this session and defer the roadmap. Still honor `CLAUDE.md`, and log any non-trivial decision or observed mistake to `.agent/` (`DECISIONS.md` / `LESSONS.md`) per `INDEX.md`.

If you find a better bootstrap pattern, propose `[DEC-NNN]` and update this command file (`.claude/commands/session.md`).
