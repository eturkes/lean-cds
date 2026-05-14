# Reusable Session Prompt — lean-cds

Paste into a fresh Claude Code session. Append user steering after `---`.

---

You are continuing work on **lean-cds**: a Lean 4 / Python / Litestar PoC for verifiable clinical decision support (bilingual JA/EN, JA default).

**Read on session start, in order:** `CLAUDE.md` (universal operating philosophy — authoritative; this prompt does not restate it), then `.agent/INDEX.md` (memory-system map) which directs you to `ARCHITECTURE.md`, `DECISIONS.md`, `LESSONS.md`, and `SCRATCH.md` (if continuing).

**Project-specific operational notes:**

- Python deps via `uv`. Lean toolchain at `./.elan/bin/lean` (preferred) or `$HOME/.elan/bin/lean`.
- Verify cheaply via execution: `uv run python -c "import app"`, `uv run pytest`, `uv run python scripts/check_scenarios.py` (kernel-typechecks all 6 scenarios).
- Always grep `[LSN-` in `.agent/LESSONS.md` before non-obvious choices.

If you find a better bootstrap pattern, propose `[DEC-NNN]` and update this file.

---

User steering for this session: <append your instructions here>
