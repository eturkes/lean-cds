# Scratch Pad

Per-session ephemeral notes. Wipe at session start unless explicitly continuing prior work. **Anything that should survive -- move to DECISIONS, LESSONS, or ARCHITECTURE before ending the session.**

---

## Session: 2026-06-01 — Relocate `compaction.sh` to global; 90% → 80% threshold

**Trigger**: User edited CLAUDE.md — gauge now referenced as `$HOME/.claude/compaction.sh`, wrap-up threshold 90% → 80%.

**Finding**: `$HOME/.claude/compaction.sh` is a symlink → `pro/agents/claude/compaction.sh` (outside lean-cds) — a newer dual-mode + color-coded version (red ≥80%, yellow ≥60%). The tracked repo-root `compaction.sh` was the older single-mode fork with a stale `>=90%` comment → redundant, drifted duplicate.

**Actions**:
1. `git rm compaction.sh` (repo-root duplicate; superseded by global canonical).
2. [DEC-010] appended; [DEC-008] marked superseded.
3. Verified global gauge runs this session (`15% 30K/200K`).
4. Committed.

**Scope note**: Global script lives outside project root — left untouched (already encodes 80%, no stale refs).

**Status**: complete.
