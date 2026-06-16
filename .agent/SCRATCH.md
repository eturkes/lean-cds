# Scratch Pad

Per-session ephemeral notes. Wipe at session start unless explicitly continuing prior work. **Anything that should survive — move to DECISIONS, LESSONS, or ARCHITECTURE before ending the session.**

---

## Pending — 2026-06-16

- **`./.elan` toolchain repair is user-handled.** Project-local `./.elan` lacks the floated-to v4.31.0 (only a stale `…v4.31.lock`); this hangs `lean` under the pinned `ELAN_HOME` and is why `check_scenarios.py` is red and the live `/verify` is broken. Full diagnosis: [LSN-007]. After the user restores v4.31.0, run `uv run python scripts/check_scenarios.py` to confirm 6/6 — it should pass with no further code change (ARC-009 auto-heals the oleans on `import app`).
- Optional code follow-up: harden `_lean_version`/ARC-009 to fail safe on an undeterminable version ([LSN-007] prevention).
- Dash-rule work ([DEC-020]) is committed; its gate was verified independently (`import app` OK, dash-scan clean, no Lean source touched).
