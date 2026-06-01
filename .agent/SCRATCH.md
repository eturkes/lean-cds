# Scratch Pad

Per-session ephemeral notes. Wipe at session start unless explicitly continuing prior work. **Anything that should survive -- move to DECISIONS, LESSONS, or ARCHITECTURE before ending the session.**

---

## Session: 2026-06-01 — `compaction.sh`: 90% → 80%, relocate-to-global, then re-vendor in-repo

**Trigger**: Series of CLAUDE.md edits. Net result: threshold 90% → **80%**; gauge referenced path-lessly as "the supplied `compaction.sh`" (in-repo).

**Final state**:
- Repo-root `compaction.sh` is a regular file, byte-identical to canonical global `$HOME/.claude/compaction.sh` (real path `~/agents/claude/compaction.sh`) — dual-mode + color-coded, red ≥80%. Tracked, executable.
- The old stale single-mode `>=90%` fork is gone; current copy is the newer canonical content.

**Arc** (newest decision wins): [DEC-008] adopt repo-root → [DEC-010] remove, point to global → **[DEC-011] re-vendor in-repo** (user reversed). DEC-010 partially superseded; its "canonical originates globally" finding stands (in-repo file is a vendored snapshot, can drift; re-sync via `cp "$HOME/.claude/compaction.sh" ./compaction.sh`).

**Scope note**: Global script lives outside project root — untouched; already encodes 80%.

**Status**: complete.
