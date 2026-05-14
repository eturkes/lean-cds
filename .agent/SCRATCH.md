# Scratch Pad

Per-session ephemeral notes. Wipe at session start unless explicitly continuing prior work. **Anything that should survive — move to DECISIONS, LESSONS, or ARCHITECTURE before ending the session.**

---

## Session: 2026-05-14 — Broad bloat audit + ARCHITECTURE.md consolidation

**Goal**: User pushed back on first-pass trim, asked for broader codebase audit.

**Status**: complete.

**Findings & actions**:

| Finding | Action |
|---|---|
| Prompt ↔ README overlap (1 identity sentence) | Defensible; left as-is. Prompt needs immediate self-grounding. |
| **README ↔ ARCHITECTURE.md** — ~104 of 220 lines duplicated (Stack, Layout, Routes, Pipeline) + `Scenario data model` duplicated `scenarios.py` source | README collapsed to 6-line stub. Unique content absorbed into ARCHITECTURE.md. Logged [DEC-005]. |
| ARCHITECTURE.md route path wrong (`POST /verify` vs actual `POST /scenarios/{id}/verify`) | Fixed in ARCHITECTURE.md; logged [LSN-004]. |
| `pyproject.toml` description = "Add your description here" | Replaced with real one-line description. |
| 22 ASCII rule-line comments (`# ---...---`) across 4 .py files | Stripped via `sed '/^# -\{50,\}$/d'`. Label comments preserved. -22 lines total. |
| Empty `tests/` directory (only stale `__pycache__`) | Deleted. |
| Code docstrings | Already tight from prior session; no further action. |
| Templates / static/ | Not deep-audited; no obvious bloat surfaced. |
| `.agent/INDEX.md` minor self-overlap | Tolerable; left alone. |

**File deltas**:
- README.md: 220 → 6 lines (-214).
- ARCHITECTURE.md: 80 → ~165 lines (+85, absorbed README content).
- i18n.py: 218 → 216 (-2).
- scenarios.py: 561 → 555 (-6).
- lean_decorate.py: 1678 → 1668 (-10).
- lean_vocab.py: 456 → 452 (-4).
- tests/: removed.
- Net repo-wide: −151 lines (excluding INDEX/DEC/LSN updates).

**Verification**:
- `uv run python -c "import app, i18n, scenarios, lean_decorate, lean_vocab"` → clean.
- `uv run python scripts/check_scenarios.py` → 6/6 PASS in ~30s.

**Notes for future sessions**:
- ARCHITECTURE.md is now the canonical project doc. If you find yourself updating README beyond a tiny stub, you're probably reintroducing the drift class [DEC-005] eliminated.
- When documenting routes/CLI/env vars in any `.agent/` file, grep source first ([LSN-004]).
- The remaining 1-line in-dict separators in `lean_vocab.py` (`# ---- Types / constants ---`) were left intact — they're 1 line each and serve sub-section navigation within long dicts. Different cost/benefit than the 3-line block separators.
