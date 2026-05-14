# lean-cds Architecture Snapshot

**As-of**: 2026-05-14. Rewrite affected sections on structural change; do not leave stale text inline.

## Mission

Local PoC. Encode published clinical guidelines as Lean 4 `axiom`s over a `Patient → Prop` deontic predicate algebra. Ask the Lean kernel to prove `theorem absurd : False` from (a) two guideline axioms, (b) patient chart-derived observation axioms, (c) a global `incompatible_modalities` axiom forbidding any treatment from being both indicated and contraindicated. **A successful kernel typecheck of `absurd` is the verification that two guidelines collide on this patient.**

This is **not** a runtime evaluator. Every scenario is a static `.lean` file under `lean/<locale>/`.

## Stack

| Layer | Tool |
|-------|------|
| Verifier | Lean 4 (`lean` on PATH; `./.elan/bin/lean` preferred) |
| Package mgr | uv (Astral) |
| Language | Python 3.13 |
| Web | Litestar 2 with `litestar[jinja,standard]` |
| ASGI | uvicorn |
| Templates | Jinja2 |
| Frontend | HTMX 2 (CDN, no build step) |
| Tour | driver.js 1.3 (CDN) |
| Syntax HL | Pygments `Lean4Lexer` (server-side, dual light/dark) |
| Theme | CSS `prefers-color-scheme` |
| i18n | In-process JA/EN catalogs (`i18n.py`); JA default; query+cookie toggle |

## File layout

```
app.py                       — Litestar app, /verify endpoint, lean subprocess shim
i18n.py                      — locale registry, UI_STRINGS, per-request resolver
scenarios.py                 — bilingual per-scenario metadata (SCENARIOS_BY_LOCALE)
lean_decorate.py             — Pygments syntax highlight + data-lean-tip tooltips
lean_vocab.py                — kanji/english identifier vocabulary for tooltips
scripts/check_scenarios.py   — Batch-verify all scenarios kernel-typecheck
lean/en/                     — EN Lean tree (AHA/ACC, KDIGO, ADA, APA, AASM)
lean/ja/                     — JA Lean tree (JSH, JSN, JDS, JSAD/JSNP, JRS); kanji ids via «…»
lean/MedicalKnowledge.lean   — Shared DSL; precompiled at app boot to .olean
artifacts/proofs/            — Generated proof artifacts (build output)
templates/index.html         — Main shell
templates/_scenario_panel.html, _verification_result.html — HTMX fragments
static/styles.css, syntax.css, tooltips.js
tests/                       — Pytest (verify presence before relying)
.elan/                       — Project-local Lean toolchain (preferred over $HOME/.elan)
```

## Data flow

1. Request → Litestar route.
2. Locale resolved: `?lang=` overrides cookie `cds_lang`; default `ja`.
3. Template renders sidebar (scenarios) + main panel (guidelines + Lean source, server-side highlighted).
4. User clicks Verify → POST `/verify` with `scenario_id` (whitelisted via `scenarios.get_scenarios`).
5. App invokes `lean lean/<locale>/ScenarioX.lean` as subprocess.
6. Stdout parsed: `#print axioms absurd` lines → trusted-axiom list → `_verification_result.html` via HTMX swap (with header pill OOB update).

## Invariants

- **[ARC-001]** No user input is interpolated into Lean source. Scenario id is whitelisted via `scenarios.get_scenarios`; the file is static. Any change here is a security review.
- **[ARC-002]** `lean/MedicalKnowledge.lean` is precompiled at app import time to `MedicalKnowledge.olean`. Per-request verification is a single `lean` invocation, not a cold compile of the DSL.
- **[ARC-003]** Lean source trees `lean/en/` and `lean/ja/` are structurally parallel but identifier-disjoint. EN uses ASCII names; JA uses kanji via Lean 4's `«…»` French-quote syntax. Do **not** assume a name-mapping table — locales are independent vocabularies proving the same theorem shape.
- **[ARC-004]** Japanese is the default locale, English is the toggle. Don't flip without explicit user direction.
- **[ARC-005]** Pygments highlights are computed **server-side**. No client-side compile.
- **[ARC-006]** `./.elan/bin/lean` is preferred over `$HOME/.elan/bin/lean`. `app.py` checks project-local first.
- **[ARC-007]** HTMX swaps include OOB updates for the header status pill (pattern set by commit `7818641`).
- **[ARC-008]** Light/dark theme via `prefers-color-scheme`. Two Pygments stylesheets are emitted, gated by `@media`.

## Public surfaces

| Surface | Form | Purpose |
|---------|------|---------|
| `GET /` | HTTP | Index / gallery shell. |
| `POST /verify` | HTTP (HTMX) | Run lean on a whitelisted scenario, return result fragment. |
| `GET /?lang=ja\|en` | HTTP | Locale toggle (sets `cds_lang` cookie). |
| `/static/*` | HTTP | CSS, JS, fonts. |
| `scripts/check_scenarios.py` | CLI | Batch-verify all scenarios. |

## Known sensitivities

- `lean` binary must be discoverable; failures surface as 500s. Check `LEAN_BIN` resolution in `app.py` first.
- Pygments highlights may be implicitly cached by template engine. If stale highlights appear after editing Lean source, investigate cache invalidation.
- `__pycache__/` directories exist in the working tree (committed history shows them in `ls`); confirm `.gitignore` covers them before commit.
