# Reusable Session Prompt — lean-cds

Paste this into a fresh Claude Code session to bootstrap an agent on this project. Append your own steering after the `---` at the bottom.

---

You are continuing work on **lean-cds**, a Lean 4 / Python / Litestar PoC for verifiable clinical decision support (bilingual JA/EN, JA default).

**Before doing anything else, read in this exact order:**

1. `CLAUDE.md` (repo root) — agent operating philosophy. Key points: ambitious work is welcomed, ask clarifying questions when ambiguous, prioritize factual accuracy over completion, failure is acceptable, all files (code and docs) are optimized for LLM machine readability and token efficiency rather than human readability, CLAUDE.md itself may not be modified without explicit user approval.

2. `.agent/INDEX.md` — map of the agent memory system. Then in order:
   - `.agent/ARCHITECTURE.md` — current codebase snapshot (stack, file layout, data flow, `[ARC-NNN]` invariants).
   - `.agent/DECISIONS.md` — append-only ADRs, newest on top. Grep `[DEC-` for IDs.
   - `.agent/LESSONS.md` — append-only mistakes/fixes. **Grep here before making non-obvious choices.**
   - `.agent/SCRATCH.md` — last session's working state, if continuing.

**During the session:**

- **Updates write to disk.** Anything that should survive the session belongs in `.agent/`. SCRATCH.md is ephemeral; DECISIONS, LESSONS, ARCHITECTURE are durable.
- **Non-trivial decisions** → append `[DEC-NNN]` to DECISIONS.md (newest on top, ID ascending).
- **Observed mistakes** (yours or prior) → append `[LSN-NNN]` to LESSONS.md with prevention note.
- **Structural changes** to the codebase → rewrite the affected section of ARCHITECTURE.md in place.
- **Ask the user** when anything is ambiguous, when planning would benefit from input, or when a tooling decision could go multiple ways — the user wants questions over hallucinated assumptions. Conversational chat is reserved for blockers; routine audits/summaries go through `gemini` later.

**Operational notes:**

- Passwordless sudo is available. You own this sandbox. Modify environment, install tools, hit the network freely.
- Use `uv` for Python deps. Lean toolchain is at `./.elan/bin/lean` (preferred) or `$HOME/.elan/bin/lean`.
- Git commits OK locally. The user handles all remote-affecting commands.
- Verify work via execution where the cost is reasonable: `python -c "import app"`, `pytest`, kernel-typecheck a scenario.
- When choosing a library/tool/pattern, web-search for SOTA-as-of-today before committing. Training data biases toward popular-with-humans, not best-for-this-task.
- LLMs struggle with negative constraints — prefer "always X" / "you must X" framings over "don't" / "never" when writing instructions for yourself or future agents.

**Reusable prompt usage:**

This prompt is canonical. If you discover a better way to bootstrap a session, propose it as a `[DEC-NNN]` and update this file accordingly.

---

User steering for this session: <append your instructions here>
