# lean-cds

Local PoC encoding clinical guidelines as Lean 4 `axiom`s; per-patient guideline collisions are verified by `theorem absurd : False` kernel typecheck. Bilingual JA/EN; AI-developed.

Run it: `uv run litestar run`, then open <http://127.0.0.1:8000>. Verify the proofs: `uv run python scripts/check_scenarios.py`.

- Agent operating contract: [`CLAUDE.md`](CLAUDE.md)
- Plan and status: [`.agent/roadmap.md`](.agent/roadmap.md)
- Carried-forward lessons and decisions: [`.agent/memory.md`](.agent/memory.md)
- License: Apache 2.0 ([`LICENSE`](LICENSE))
