# lean-cds

Local PoC encoding published clinical guidelines as Lean 4 `axiom`s over a `Patient → Prop` deontic predicate algebra. Each scenario is a static `.lean` file whose `theorem absurd : False` is proved from (a) two guideline axioms, (b) chart-derived observation axioms, (c) a global `incompatible_modalities` axiom forbidding any treatment from being both `Indicated` and `Contraindicated` for the same patient. **Successful kernel typecheck of `absurd` = the two guidelines collide on this patient.** Not a runtime evaluator; no user input is interpolated into Lean source.

UI: HTMX gallery (sidebar of scenarios + two-column body: NL guidelines | Lean source). The verify button runs `lean` against the scenario file and surfaces the axiom witness from `#print axioms absurd`.

**Bilingual end-to-end. Japanese (日本語) is the default**; header carries a JA/EN toggle.

- `lean/ja/`: JSH 2019, JSN AKI 2016, JDS 2024, JSAD/JSNP 2025, JRS SAS 2020. Every Lean identifier is kanji via Lean 4's `«…»` syntax (`«山田太郎»`, `«患者»`, `«治療»`, `«適応»`, `«禁忌»`, `«衝突»`, `«本態性高血圧を有する»`, `«高血圧2019_第5章_第一選択»`, …).
- `lean/en/`: ACC/AHA, KDIGO, ADA, APA, AASM. ASCII identifiers (`JohnDoe`, `AHA_ACC_HTN_8_1_6`, …).

The two trees prove the same theorem shape with disjoint identifier vocabularies. Tooltips (`data-lean-tip` attrs) are locale-matched.

## Stack

| Layer | Tool |
|-------|------|
| Verifier | Lean 4 (`lean` on PATH; `./.elan/bin/lean` preferred) |
| Package manager | uv (Astral) |
| Language | Python 3.13 |
| Web framework | Litestar 2 (`litestar[jinja,standard]`) |
| ASGI server | uvicorn |
| Templates | Jinja2 |
| Frontend | HTMX 2 (CDN, no build) |
| Product tour | driver.js 1.3 (CDN, no build) |
| Syntax highlight | Pygments `Lean4Lexer` (server-side, dual light/dark) |
| Theming | CSS `prefers-color-scheme` |
| Localization | In-process JA/EN catalogs (`i18n.py`), JA default, query+cookie toggle |

## Prerequisites

- Lean 4 via [`elan`](https://github.com/leanprover/elan). Project-local install (preferred — `app.py` checks `./.elan/bin/lean` first):

  ```bash
  ELAN_HOME="$PWD/.elan" curl -fsSL https://elan.lean-lang.org/elan-init.sh \
      | sh -s -- -y --no-modify-path --default-toolchain stable
  ```

- uv ≥ 0.11.
- Python 3.13 (uv fetches on demand).

## Quick start

```bash
git clone git@github.com:eturkes/lean-cds.git
cd lean-cds
uv sync
uv run uvicorn app:app --host 127.0.0.1 --port 8000
```

Open <http://127.0.0.1:8000>, pick a scenario, click **Run Lean Formal Verification**.

## Project layout

```
.
├── app.py                          # Litestar app + Lean subprocess wrapper
├── i18n.py                         # JA/EN UI string catalogs + locale resolver
├── scenarios.py                    # Per-locale scenario metadata, ID → .lean filename
├── lean_decorate.py                # Pygments → per-line tooltip HTML renderer
├── lean_vocab.py                   # Per-locale glosses for MedicalKnowledge symbols
├── lean/
│   ├── en/                         # AHA/KDIGO/ADA/APA/AASM; ASCII names
│   │   ├── MedicalKnowledge.lean
│   │   ├── ScenarioA.lean          # JohnDoe — HTN vs. severe dehydration
│   │   ├── ScenarioB.lean          # JaneRoe — DKA vs. severe hypokalaemia
│   │   └── ScenarioC.lean          # RichardRoe — acute panic vs. untreated severe OSA
│   └── ja/                         # JSH/JSN/JDS/JSAD-JSNP/JRS; kanji names in «…»
│       ├── MedicalKnowledge.lean
│       ├── ScenarioA.lean          # «山田太郎» — 高血圧症 vs. 重症脱水
│       ├── ScenarioB.lean          # «鈴木花子» — DKA vs. 重症低カリウム血症
│       └── ScenarioC.lean          # «田中一郎» — 急性パニック症 vs. 重症 OSA
├── scripts/
│   └── check_scenarios.py          # Regression harness pinning expected axiom sets
├── templates/
│   ├── index.html                  # Full page shell + sidebar
│   ├── _scenario_panel.html        # Scenario two-column body (HTMX target)
│   └── _verification_result.html   # Compiler-result alert + terminal
├── static/
│   ├── styles.css                  # Hand-written theme (light/dark)
│   ├── syntax.css                  # Pygments CSS, regenerated at app import
│   └── tooltips.js                 # Tooltip popovers for Lean keywords
├── .agent/                         # Agent memory system (see .agent/INDEX.md)
├── pyproject.toml                  # uv-managed metadata + deps
├── uv.lock                         # cross-platform lockfile
└── LICENSE                         # Apache 2.0
```

## Routes (`app.py`)

| Method | Path | Returns |
|--------|------|---------|
| GET | `/` | Full page (`index.html` + first scenario) |
| GET | `/scenarios/{scenario_id}` | `_scenario_panel.html` HTMX fragment |
| POST | `/scenarios/{scenario_id}/verify` | `_verification_result.html` HTMX fragment |
| GET | `/static/*` | `static/` files |

Every route accepts `?lang=ja|en`. Resolution order (in `_resolve_locale`): query → `cds_lang` cookie → JA default. Each response sets `cds_lang` for stickiness.

## Verification pipeline (`app.py` `_run_lean`)

1. **At import.** `_precompile_all_knowledge_bases()` calls `_ensure_knowledge_base_compiled(locale)` per supported locale. If `lean/<locale>/MedicalKnowledge.{olean,ilean}` are missing or stale relative to the `.lean`, it runs `lean -o MedicalKnowledge.olean -i MedicalKnowledge.ilean MedicalKnowledge.lean` (cwd `lean/<locale>`). Scenarios import the precompiled module.

2. **Per request.** `POST /scenarios/{id}/verify` looks `id` up in `scenarios.get_scenarios(locale)`. Unknown → 404. **No request data is ever interpolated into Lean source.** Handler maps id → fixed filename.

3. **Subprocess.** `subprocess.run([LEAN_BIN, scenario.lean_filename], cwd=lean/<locale>/, env={"LEAN_PATH": "lean/<locale>/", ...}, timeout=60)`. `LEAN_PATH` lets `import MedicalKnowledge` resolve to the locale's precompiled `.olean`.

4. **Parse.** `_parse_trusted_axioms()` scans stdout for `'…absurd' depends on axioms: [ … ]` and returns the list.

5. **Classify** (`_classify`). Three-state `Verdict`:
   - `CollisionVerified` — exit 0, axiom list present, no `sorryAx`, no `error:`.
   - `ProofUnsound` — axiom list contains `sorryAx`.
   - `CompilerError` — any other failure.

Template renders `alert-danger` for verified collision, `alert-warning` for failures, fallback when compiler is missing or timed out.

`LEAN_BIN` resolves once at import (`_resolve_lean_binary`): project-local `./.elan/bin/lean` first, then `shutil.which("lean")`.

## Syntax highlighting

`_write_syntax_css()` runs at module import; writes `static/syntax.css` with two Pygments stylesheets wrapped in `@media (prefers-color-scheme: …)` blocks (Tango light, Monokai dark). Per-scenario highlighted HTML is computed on demand in `_scenario_context()` from the static `.lean` and passed to templates as `highlighted_lean | safe`.

## Scenario data model (`scenarios.py`)

```python
@dataclass(frozen=True)
class Guideline:
    source: str        # journal/society + section
    body: str          # natural-language excerpt

@dataclass(frozen=True)
class Scenario:
    id: str            # URL slug, e.g. "scenario-a"
    title: str
    subtitle: str
    patient_summary: str
    guideline_a: Guideline
    guideline_b: Guideline
    lean_filename: str         # e.g. "ScenarioA.lean"
    lean_subdir: str           # "ja" or "en"
    audit_summary: str
    plain_english: str

SCENARIOS_BY_LOCALE: dict[str, dict[str, Scenario]] = {
    "ja": { ... },   # JSH / JSN / JDS / JSAD-JSNP / JRS
    "en": { ... },   # ACC/AHA / KDIGO / ADA / APA / AASM
}
```

JA and EN copies of `scenario-a` share `id` and `lean_filename` but differ in `lean_subdir`. UI chrome strings live in `i18n.UI_STRINGS` (rendered as `t` in templates). Tooltip prose lives in `lean_vocab.py` (per-locale `VocabEntry` tables) and `lean_decorate.py` (per-locale composer branches).

Each Lean scenario follows the same shape (EN names shown; JA uses `«臨床監査».«シナリオX»`, `«患者»`, `«所見_…»`, `«背理»`, etc.):

- `import MedicalKnowledge`
- `namespace ClinicalAudit.ScenarioX`
- `axiom` for the patient inhabitant
- one `axiom obs_*` per chart finding
- `theorem absurd : False := by …` deriving the contradiction
- `#print axioms absurd` emitting the trusted-axiom witness

## Adding a new scenario

1. **Update both `MedicalKnowledge.lean`** (`lean/en/`, `lean/ja/`) with the new guideline(s) and any new condition predicates. Each guideline is one `axiom` of shape `∀ p, HasFoo p → Indicated p Treatment.bar` (or `Contraindicated`). EN: ASCII + American society prefix (`AHA_…`). JA: kanji in `«…»` + Japanese society prefix (`«高血圧2019_…»`). **Delete cached `MedicalKnowledge.olean` in both dirs.**

2. **Create both scenario files** `lean/{en,ja}/ScenarioD.lean`. Sanity-check by hand:

   ```bash
   (cd lean/en && LEAN_PATH=. lean ScenarioD.lean)
   (cd lean/ja && LEAN_PATH=. lean ScenarioD.lean)
   ```

3. **Append `Scenario` constants** to `scenarios.py` for both locales (`_JA_SCENARIO_D`, `_EN_SCENARIO_D`) with `lean_filename="ScenarioD.lean"` and matching `lean_subdir`. Add to `SCENARIOS_BY_LOCALE`.

4. **Add `VocabEntry` records** for any new symbols to both `_EN_VOCAB` and `_JA_VOCAB` in `lean_vocab.py`.

5. **Append expected axiom set** to both locale dicts in `scripts/check_scenarios.py`.

6. Sidebar, fragment endpoint, verify endpoint auto-discover the new scenario. No template edits needed.

## Common dev tasks

```bash
uv sync                                         # install / sync deps
uv add <package>                                # add runtime dep
uv add --dev <package>                          # add dev-only dep
uv run <command>                                # run in project venv

# Verify all 6 scenarios (3 × 2 locales) headless
uv run python -c "
from app import _run_lean
from scenarios import get_scenarios
for locale in ('ja', 'en'):
    for sid, sc in get_scenarios(locale).items():
        r = _run_lean(sc)
        print(locale, sid, r.verdict, list(r.trusted_axioms), r.exit_code)
"

# Regression harness (pins both locales)
uv run python scripts/check_scenarios.py

# Compile one scenario by hand
(cd lean/ja && LEAN_PATH=. lean ScenarioA.lean)
(cd lean/en && LEAN_PATH=. lean ScenarioA.lean)
```

`static/syntax.css` is overwritten on every app import — don't hand-edit. Edit Pygments style names in `_write_syntax_css()` instead.

## Agent workflow

This project is developed by AI agents under instructions in [`CLAUDE.md`](CLAUDE.md). Cross-session memory and conventions live in [`.agent/`](.agent/) — start with [`.agent/SESSION_PROMPT.md`](.agent/SESSION_PROMPT.md) to bootstrap a fresh session, then [`.agent/INDEX.md`](.agent/INDEX.md) for the memory-system map.

## Limitations

- **Encoder discipline is the dominant correctness constraint.** The knowledge base is hand-curated. There is no automatic translation from natural-language guidelines to `axiom` declarations; misencoded preconditions or modalities silently produce the wrong proof obligation.
- **Deontic semantics is monotonic.** `incompatible_modalities` flatly forbids `Indicated p t ∧ Contraindicated p t` for any `p`, `t`. No defeasibility, prioritisation, or context-conditioned exceptions. Conditional guidelines must be encoded as axioms with the precondition in the antecedent.
- **No metatheorem of fidelity.** The verification claim is "Lean kernel typechecks `theorem absurd : False` from exactly this list of trusted axioms" — not "this list of axioms soundly formalises the underlying clinical literature."

## License

Apache License 2.0. See [`LICENSE`](LICENSE).
