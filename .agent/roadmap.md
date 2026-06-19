# roadmap

## Status
PoC functional — `scripts/check_scenarios.py` exits 0 with all six scenarios CollisionVerified (three guideline collisions × JA/EN). Bilingual UI, Pygments highlighting, and olean toolchain auto-heal are in place.
- A — antihypertensive (thiazide) vs acute kidney injury volume status
- B — DKA insulin therapy vs severe hypokalemia (serum potassium safety floor)
- C — panic-disorder benzodiazepines vs severe obstructive sleep apnea

## Forward
1. ScenarioD (en + ja) — a fourth guideline collision; mirror A/B/C (memory.md → Add a scenario).
2. Precedence for `incompatible_modalities` — model guideline priority/defeasibility. The algebra is monotonic today, so it can express mutual exclusion only, not "X overrides Y".
3. Fidelity assurance — a metatheorem or auditable process tying axioms to their cited guideline sections. Faithfulness is encoder-discipline only right now (the core trust gap). Open/hard.

## Backlog
- Pin the Lean toolchain (a `lean-toolchain` file or an elan override) for reproducible builds. It floats on `stable` now, so a fresh clone re-downloads whatever stable currently resolves to.
