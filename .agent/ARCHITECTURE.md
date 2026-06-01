# lean-cds Architecture Snapshot

**As-of**: 2026-05-14. Rewrite affected sections on structural change; do not leave stale text inline.

## Mission

Local PoC. Encode published clinical guidelines as Lean 4 `axiom`s over a `Patient → Prop` deontic predicate algebra. Ask the Lean kernel to prove `theorem absurd : False` from (a) two guideline axioms, (b) patient chart-derived observation axioms, (c) a global `incompatible_modalities` axiom forbidding any treatment from being both `Indicated` and `Contraindicated`. **A successful kernel typecheck of `absurd` is the verification that two guidelines collide on this patient.** Not a runtime evaluator; every scenario is a static `.lean` file under `lean/<locale>/`. No user input is ever interpolated into Lean source.

UI: HTMX gallery (sidebar of scenarios + two-column body: NL guidelines | Lean source). Verify button runs `lean` against the scenario file and surfaces the axiom witness from `#print axioms absurd`.

Bilingual end-to-end. **Japanese (日本語) is the default**; header carries JA/EN toggle.

- `lean/ja/`: JSH 2019, JSN AKI 2016, JDS 2024, JSAD/JSNP 2025, JRS SAS 2020. Lean identifiers are kanji via `«…»` (`«山田太郎»`, `«患者»`, `«適応»`, `«禁忌»`, `«衝突»`, `«高血圧2019_第5章_第一選択»`, …).
- `lean/en/`: ACC/AHA, KDIGO, ADA, APA, AASM. ASCII identifiers (`JohnDoe`, `AHA_ACC_HTN_8_1_6`, …).

The two trees prove the same theorem shape with disjoint identifier vocabularies. Tooltips (`data-lean-tip` attrs) are locale-matched.

## Stack

| Layer | Tool |
|-------|------|
| Verifier | Lean 4 (`./.elan/bin/lean` preferred, else `lean` on PATH) |
| Package mgr | uv (Astral) |
| Language | Python 3 |
| Web | Litestar 2 with `litestar[jinja,standard]` |
| ASGI | uvicorn |
| Templates | Jinja2 |
| Frontend | HTMX 2 (CDN, no build step) |
| Tour | driver.js (CDN) |
| Syntax HL | Pygments `Lean4Lexer` (server-side, dual light/dark) |
| Theme | CSS `prefers-color-scheme` |
| i18n | In-process JA/EN catalogs (`i18n.py`); JA default; query+cookie toggle |

## Prerequisites

- Lean 4 via [`elan`](https://github.com/leanprover/elan). Project-local install (preferred):

  ```bash
  ELAN_HOME="$PWD/.elan" curl -fsSL https://elan.lean-lang.org/elan-init.sh \
      | sh -s -- -y --no-modify-path --default-toolchain stable
  ```

- uv. Python per `requires-python` in `pyproject.toml` (uv fetches on demand).

## Quick start

```bash
uv sync
uv run uvicorn app:app --host 127.0.0.1 --port 8000
```

Open <http://127.0.0.1:8000>, pick a scenario, click **Run Lean Formal Verification**.

## File layout

```
app.py                       — Litestar app, /scenarios/{id}/verify endpoint, lean subprocess shim
i18n.py                      — locale registry, UI_STRINGS, per-request resolver
scenarios.py                 — bilingual per-scenario metadata (SCENARIOS_BY_LOCALE)
lean_decorate.py             — Pygments syntax highlight + data-lean-tip tooltips
lean_vocab.py                — kanji/english identifier vocabulary for tooltips
scripts/check_scenarios.py   — Batch-verify all scenarios kernel-typecheck (pins expected axiom sets)
lean/MedicalKnowledge.lean   — (per locale) Shared DSL; precompiled at app boot to .olean
lean/en/                     — ScenarioA (JohnDoe: HTN vs. severe dehydration), B (JaneRoe: DKA vs. hypokalaemia), C (RichardRoe: panic vs. severe OSA)
lean/ja/                     — ScenarioA (山田太郎: 高血圧 vs. 重症脱水), B (鈴木花子: DKA vs. 重症低カリウム血症), C (田中一郎: 急性パニック vs. 重症OSA)
templates/index.html         — Main shell
templates/_scenario_panel.html, _verification_result.html — HTMX fragments
static/styles.css, syntax.css, tooltips.js
.elan/                       — Project-local Lean toolchain (preferred over $HOME/.elan)
```

## Public surfaces

| Surface | Form | Purpose |
|---------|------|---------|
| `GET /` | HTTP | Index / gallery shell. Returns full page (`index.html` + first scenario). |
| `GET /scenarios/{scenario_id}` | HTTP (HTMX) | Returns `_scenario_panel.html` fragment. |
| `POST /scenarios/{scenario_id}/verify` | HTTP (HTMX) | Runs `lean` on whitelisted scenario, returns `_verification_result.html`. |
| `GET /static/*` | HTTP | CSS, JS, fonts. |
| `scripts/check_scenarios.py` | CLI | Batch-verify all scenarios. |

Every route accepts `?lang=ja|en`. Resolution (in `_resolve_locale`): query → `cds_lang` cookie → JA default. Each response sets `cds_lang` for stickiness.

## Request lifecycle

1. **At import** — `_precompile_all_knowledge_bases()` calls `_ensure_knowledge_base_compiled(locale)` per supported locale. If `lean/<locale>/MedicalKnowledge.{olean,ilean}` are missing or stale relative to the `.lean`, runs `lean -o MedicalKnowledge.olean -i MedicalKnowledge.ilean MedicalKnowledge.lean` (cwd `lean/<locale>`). `LEAN_BINARY` resolves once via `_resolve_lean_binary` (project-local `./.elan/bin/lean` first, then `shutil.which("lean")`).
2. **Request** → Litestar route. Locale resolved (`?lang=` → cookie → JA default).
3. **Render** — template renders sidebar (scenarios) + main panel (guidelines + Lean source, server-side highlighted via Pygments).
4. **User clicks Verify** → `POST /scenarios/{scenario_id}/verify`. Handler looks `id` up in `scenarios.get_scenarios(locale)`. Unknown → 404. Maps id → fixed filename.
5. **Subprocess** — `subprocess.run([LEAN_BIN, scenario.lean_filename], cwd=lean/<locale>/, env={"LEAN_PATH": "lean/<locale>/", ...}, timeout=60)`. `LEAN_PATH` lets `import MedicalKnowledge` resolve to the locale's precompiled `.olean`.
6. **Parse** — `_parse_trusted_axioms` scans stdout for `'…absurd' depends on axioms: [ … ]`.
7. **Classify** (`_classify`) — three-state `Verdict`:
   - `CollisionVerified` — exit 0, axiom list present, no `sorryAx`, no `error:`.
   - `ProofUnsound` — axiom list contains `sorryAx`.
   - `CompilerError` — any other failure.
8. **Response** — `_verification_result.html` via HTMX swap (with header pill OOB update). Verified collision → `alert-danger`; failures → `alert-warning`; compiler missing/timeout → fallback.

## Invariants

- **[ARC-001]** No user input is interpolated into Lean source. Scenario id is whitelisted via `scenarios.get_scenarios`; the file is static. Any change here is a security review.
- **[ARC-002]** `lean/MedicalKnowledge.lean` is precompiled at app import time to `MedicalKnowledge.olean`. Per-request verification is a single `lean` invocation, not a cold compile of the DSL.
- **[ARC-003]** Lean source trees `lean/en/` and `lean/ja/` are structurally parallel but identifier-disjoint. EN uses ASCII names; JA uses kanji via Lean 4's `«…»` French-quote syntax. Do **not** assume a name-mapping table — locales are independent vocabularies proving the same theorem shape.
- **[ARC-004]** Japanese is the default locale, English is the toggle. Don't flip without explicit user direction.
- **[ARC-005]** Pygments highlights are computed **server-side**. No client-side compile.
- **[ARC-006]** `./.elan/bin/lean` is preferred over `$HOME/.elan/bin/lean`. `app.py` checks project-local first.
- **[ARC-007]** HTMX swaps include OOB updates for the header status pill (pattern set by commit `7818641`).
- **[ARC-008]** Light/dark theme via `prefers-color-scheme`. Two Pygments stylesheets are emitted, gated by `@media`.

## Adding a scenario

1. **Update both `MedicalKnowledge.lean`** (`lean/en/`, `lean/ja/`) with new guideline(s) and any new condition predicates. Each guideline is one `axiom` of shape `∀ p, HasFoo p → Indicated p Treatment.bar` (or `Contraindicated`). EN: ASCII + American society prefix (`AHA_…`). JA: kanji in `«…»` + Japanese society prefix (`«高血圧2019_…»`). **Delete cached `MedicalKnowledge.olean` in both dirs.**
2. **Create both scenario files** `lean/{en,ja}/ScenarioD.lean`. Sanity-check:
   ```bash
   (cd lean/en && LEAN_PATH=. lean ScenarioD.lean)
   (cd lean/ja && LEAN_PATH=. lean ScenarioD.lean)
   ```
3. **Append `Scenario` constants** to `scenarios.py` for both locales (`_JA_SCENARIO_D`, `_EN_SCENARIO_D`) with `lean_filename="ScenarioD.lean"` and matching `lean_subdir`. Add to `SCENARIOS_BY_LOCALE`.
4. **Add `VocabEntry` records** for new symbols to both `_EN_VOCAB` and `_JA_VOCAB` in `lean_vocab.py`.
5. **Append expected axiom set** to both locale dicts in `scripts/check_scenarios.py`.
6. Sidebar, fragment endpoint, verify endpoint auto-discover the new scenario. No template edits needed.

## Common dev tasks

```bash
uv sync                                         # install / sync deps
uv add <package>                                # add runtime dep
uv add --dev <package>                          # add dev-only dep
uv run <command>                                # run in project venv

# Regression harness (pins both locales)
uv run python scripts/check_scenarios.py

# Compile one scenario by hand
(cd lean/ja && LEAN_PATH=. lean ScenarioA.lean)
(cd lean/en && LEAN_PATH=. lean ScenarioA.lean)
```

`static/syntax.css` is overwritten on every app import — don't hand-edit. Edit Pygments style names in `_write_syntax_css()` instead.

## Known sensitivities

- `lean` binary must be discoverable; failures surface as 500s. Check `LEAN_BIN` resolution in `app.py` first.
- Pygments highlights may be implicitly cached by template engine. If stale highlights appear after editing Lean source, investigate cache invalidation.
- Stale `.olean` artifacts silently fail with "incompatible header" — see [LSN-002].

## Limitations

- **Encoder discipline is the dominant correctness constraint.** Knowledge base is hand-curated. No automatic translation from NL guidelines to `axiom` declarations; misencoded preconditions or modalities silently produce the wrong proof obligation.
- **Deontic semantics is monotonic.** `incompatible_modalities` flatly forbids `Indicated p t ∧ Contraindicated p t` for any `p`, `t`. No defeasibility, prioritisation, or context-conditioned exceptions. Conditional guidelines must encode the precondition in the antecedent.
- **No metatheorem of fidelity.** The verification claim is "Lean kernel typechecks `theorem absurd : False` from exactly this list of trusted axioms" — not "this list of axioms soundly formalises the underlying clinical literature."
