# memory

Carried-forward lessons and decisions. Only what the code/Git history can't tell you; the code is the source of truth (no architecture doc by design — a prior one drifted from `app.py`). Append durable facts; prune the obsolete.

## Verify (the gate)
- `uv run python scripts/check_scenarios.py` → every scenario must report CollisionVerified, exit 0. This is the known-good gate to run before and after work.
- `uv run python -c "import app"` triggers the import-time olean precompile (fast sanity).
- Serve: `uv run litestar run` → <http://127.0.0.1:8000>.

## Safety invariant (load-bearing — preserve)
- No user input ever reaches Lean. `/verify` kernel-checks a STATIC, whitelisted scenario file: `scenario_id` only indexes a predefined `Scenario`; unknown id → 404. The knowledge base (axioms) is precompiled per locale to `.olean` at import, so each request is one `lean` subprocess (cwd = locale dir, `LEAN_PATH` = locale dir, 60 s timeout). Verdict is parsed from `#print axioms` (`sorryAx` → unsound; `error:`/nonzero exit → compiler error; else collision verified).

## Lean toolchain / olean (highest-value gotchas)
- The toolchain floats on elan's `stable` channel; there is no tracked `lean-toolchain` pin, and `.elan/` is gitignored. A fresh clone or a relocated dir has no toolchain → elan re-downloads on the first `lean` call.
- Oleans are locked to the exact lean build (version + commit). A build change makes lean fail with "incompatible header". `app.py` auto-heals: `MedicalKnowledge.olean.stamp` holds the build string; a stale stamp (or source newer by mtime) forces recompile. So after any toolchain change, just re-run the gate and it rebuilds.
- A toolchain mismatch makes each verify burn the full 60 s timeout instead of failing fast. If the gate seems to hang, suspect a missing/mismatched toolchain, not a logic bug.
- Relocating the project breaks the absolute paths baked into `.venv/bin/*` shebangs and `.venv/bin/activate`: recreate the venv with `uv sync`. For oleans stranded after a move, `rm lean/{en,ja}/*.{olean,ilean}` and let auto-heal recompile.

## Deontic model + trust boundary (conceptual, not in code)
- Collisions are proved via `incompatible_modalities` in `lean/{en,ja}/MedicalKnowledge.lean`: guideline directives are deontic modalities on a treatment (e.g. Indicated vs Contraindicated); a patient triggering both yields `theorem absurd : False`, kernel-checked.
- The algebra is monotonic — no defeasibility or precedence. Real guideline priority is not modeled yet (see roadmap).
- No fidelity metatheorem: Lean proves the ENCODING is contradictory, not that the axioms faithfully transcribe the published guideline. Faithfulness rests entirely on encoder discipline (axioms hand-authored from cited guideline sections). This is the core trust boundary.

## Pointers
- `.agent/NAVMAP.md` — generated symbol/route index (gitignored). Regenerate after structural changes: `scripts/gen_navmap.sh`.
- `.agent/context.sh` — context-usage gauge (`pct used/window`); check as you approach 80%.
- Add a scenario: create `lean/{en,ja}/ScenarioX.lean` (import MedicalKnowledge; axioms; `theorem absurd : False`) and register it in `scenarios.py` (`SCENARIOS_BY_LOCALE`), mirroring the A/B/C pattern.
