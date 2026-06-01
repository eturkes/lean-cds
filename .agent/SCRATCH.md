# Scratch Pad

Per-session ephemeral notes. Wipe at session start unless explicitly continuing prior work. **Anything that should survive -- move to DECISIONS, LESSONS, or ARCHITECTURE before ending the session.**

---

## Session: 2026-06-01 — Incorporate `compaction.sh` workflow

**Goal**: User added `compaction.sh` + a compaction-at-90% workflow to CLAUDE.md (both uncommitted). Make the tool a tracked, verified, documented part of the repo.

**CLAUDE.md uncommitted diff** (vs committed `6121d90`):

| Change | Disposition |
|---|---|
| Wording: "I have limited" → "I usually limit" you to 200K | Trivial. |
| NEW: ≥90% ctx → wrap up cleanly for user-issued `/compact`; monitor with `compaction.sh` | Core task. Workflow lives in CLAUDE.md (read #1); not restated elsewhere per [DEC-004]/[DEC-006]. |
| NEW: subagent rate-limiting → sequential chunking; verify all agents completed | Go-forward operational; already in CLAUDE.md, no code action. |

**Verification** (`./compaction.sh`): prints `15% 30K/200K`; `jq-1.7`; `git check-ignore` → not ignored (trackable); resolves this session's jsonl via `$CLAUDE_CODE_SESSION_ID` even with newer sibling-project sessions present. Script correct + fit-for-purpose; left unmodified.

**Actions**:
1. Verified script + environment (above).
2. Appended [DEC-008] (adopt as canonical gauge; root placement; no restatement).
3. Committed CLAUDE.md (user edit) + compaction.sh + .agent updates.

**Open (optional, surfaced to user)**: wire `compaction.sh` as a Claude Code statusline (`.claude/settings.json`, machine-local — out of "codebase" scope, hence not done unprompted).

**Status**: complete.
