# Scratch Pad

Per-session ephemeral notes. Wipe at session start unless explicitly continuing prior work. **Anything that should survive -- move to DECISIONS, LESSONS, or ARCHITECTURE before ending the session.**

---

## Session: 2026-05-25 -- CLAUDE.md v3 update review

**Goal**: User updated CLAUDE.md; review changes, propagate to .agent/ where needed.

**Status**: complete.

**Changes reviewed** (diff against prior version):

| Change | Impact |
|---|---|
| CLAUDE.md edit permission now unrestricted | Agents can rewrite CLAUDE.md freely. No .agent/ file referenced the old restriction. |
| Directory constraint added ("constrain to launch dir and children") | New constraint; already followed de facto. |
| Commit cadence: per-cohesive-work (was per-session), LLM-optimized messages, defer when mid-iteration | Future agents pick this up from CLAUDE.md directly. |
| Memory system: "must diligently keep up-to-date to avoid drift" | Strengthens existing practice. |
| Session prompt: expanded with overwrite/inform details | SESSION_PROMPT.md already exists; no structural change needed. |
| Security: periodic audits, software updates | New operational directive; no immediate action. |
| Testing: permissible but warns against overtesting | New guidance. |
| KISS/UNIX philosophy, periodic refactoring | New guidance. |
| Objectivity: collaborative framing, specific methodologies | Expanded. |
| "Google Gemini" -> "ChatGPT/Gemini" | Wording only. |

**Actions taken**:

1. Wiped stale SCRATCH.md (2026-05-14 session).
2. Fixed SESSION_PROMPT.md: removed `uv run pytest` (no test suite exists since prior session deleted empty `tests/`).
