# lean-cds

A local proof-of-concept that encodes published clinical guidelines as
Lean 4 `axiom`s on a `Patient → Prop` deontic predicate algebra and asks
the Lean kernel to *prove* that two guidelines, applied to a single
patient, derive `False`. The audit is not a runtime evaluator: each
scenario lives in a static `.lean` file containing a `theorem absurd :
False` whose proof is built from the encoded clinical-guideline axioms,
the patient's chart-derived observation axioms, and a global
`incompatible_modalities` axiom forbidding any treatment from being both
indicated and contraindicated for the same patient. A successful kernel
typecheck of `absurd` is the verification that the two guidelines collide.

The UI is an HTMX gallery with a sidebar of scenarios, a two-column main
panel (natural-language guidelines on the left, the static Lean 4 source
on the right), and a verification button that runs the `lean` compiler
against the scenario's pre-written file and surfaces the trusted-axiom
list extracted from `#print axioms absurd`.

The interface is bilingual end-to-end. **Japanese (日本語) is the
default** and the header carries a JA/EN toggle. The Japanese build
cites Japanese medical society guidelines (JSH 2019, JSN AKI 2016,
JDS 2024, JSAD/JSNP 2025 パニック症診療ガイドライン, JRS SAS 2020) and
ships its own `lean/ja/` source tree with Japanese placeholder patient
names (`TaroYamada`, `HanakoSuzuki`, `IchiroTanaka`) and Japanese
guideline axiom identifiers (`JSH2019_Ch5_FirstLine`,
`JSN_AKI2016_Diuretics`, `JDS2024_Sec20_1_DKA`, …). The English build
ships `lean/en/` with the original American guidelines (ACC/AHA, KDIGO,
ADA, AACE/ACE, APA, AASM) and `JohnDoe / JaneRoe / RichardRoe`. Hover
tooltips on the highlighted Lean source are likewise localized: the
JA build's `data-lean-tip` attributes hold Japanese explanations, the
EN build's hold English. The two trees prove the same theorem
structure with renamed identifiers.

## Stack

| Layer            | Tool                              |
|------------------|-----------------------------------|
| Verifier         | **Lean 4** (`lean` on PATH)       |
| Package manager  | **uv** (Astral)                   |
| Language         | **Python 3.13**                   |
| Web framework    | **Litestar 2** (`litestar[jinja,standard]`) |
| ASGI server      | **uvicorn**                       |
| Templates        | **Jinja2**                        |
| Frontend         | **HTMX 2** (CDN, no build step)   |
| Syntax highlight | **Pygments** `Lean4Lexer` (server-side, dual light/dark) |
| Theming          | CSS `prefers-color-scheme`        |
| Localization     | In-process JA/EN catalogs (`i18n.py`), JA default, query+cookie toggle |

## Prerequisites

- **Lean 4** installed via [`elan`](https://github.com/leanprover/elan).
  Verify with `lean --version`.
- **uv** ≥ 0.11. Verify with `uv --version`.
- Python 3.13 (uv will fetch it on demand if missing).

## Quick start

```bash
git clone git@github.com:eturkes/lean-cds.git
cd lean-cds
uv sync                                         # creates .venv from uv.lock
uv run uvicorn app:app --host 127.0.0.1 --port 8000
```

Open <http://127.0.0.1:8000>. Pick a scenario and click **Run Lean Formal
Verification**.

## Project layout

```
.
├── app.py                          # Litestar app + Lean subprocess wrapper
├── i18n.py                         # JA/EN UI string catalogs + locale resolver
├── scenarios.py                    # Per-locale scenario metadata, ID → .lean filename map
├── lean_decorate.py                # Pygments → per-line tooltip HTML renderer (locale-aware)
├── lean_vocab.py                   # Per-locale glosses for every MedicalKnowledge symbol
├── lean/
│   ├── en/                         # American guideline axioms + romanized patient names
│   │   ├── MedicalKnowledge.lean   #   AHA/KDIGO/ADA/AACE/APA/AASM
│   │   ├── ScenarioA.lean          #   JohnDoe — hypertension vs. severe dehydration
│   │   ├── ScenarioB.lean          #   JaneRoe — DKA vs. severe hypokalaemia
│   │   └── ScenarioC.lean          #   RichardRoe — acute panic vs. untreated severe OSA
│   └── ja/                         # Japanese guideline axioms + Japanese patient names
│       ├── MedicalKnowledge.lean   #   JSH/JSN/JDS/JSAD-JSNP/JRS
│       ├── ScenarioA.lean          #   TaroYamada (山田太郎)
│       ├── ScenarioB.lean          #   HanakoSuzuki (鈴木花子)
│       └── ScenarioC.lean          #   IchiroTanaka (田中一郎)
├── scripts/
│   └── check_scenarios.py          # Regression harness asserting expected axiom sets
├── templates/
│   ├── index.html                  # Full page shell + sidebar
│   ├── _scenario_panel.html        # Scenario two-column body (HTMX target)
│   └── _verification_result.html   # Compiler-result alert + terminal
├── static/
│   ├── styles.css                  # Hand-written enterprise theme (light/dark)
│   ├── syntax.css                  # Pygments CSS, regenerated at app import
│   └── tooltips.js                 # Vanilla-JS tooltip popovers for Lean keywords
├── pyproject.toml                  # uv-managed metadata + deps
├── uv.lock                         # cross-platform lockfile
└── LICENSE                         # Apache 2.0
```

## How it works

### Routes (`app.py`)

| Method | Path                              | Returns                                    |
|--------|-----------------------------------|--------------------------------------------|
| GET    | `/`                               | Full page (`index.html` + first scenario)  |
| GET    | `/scenarios/{scenario_id}`        | `_scenario_panel.html` HTMX swap fragment  |
| POST   | `/scenarios/{scenario_id}/verify` | `_verification_result.html` HTMX fragment  |
| GET    | `/static/*`                       | `static/` files                            |

Every route accepts an optional `?lang=ja|en` query parameter. The
resolver in `app.py` (`_resolve_locale`) prefers the query string, then
falls back to the `cds_lang` cookie, then to the JA default. Each
response sets the `cds_lang` cookie so a one-time toggle is sticky.

### Verification pipeline (`app.py` `_run_lean`)

1. At import time, `_precompile_all_knowledge_bases()` walks every
   supported locale and runs `_ensure_knowledge_base_compiled(locale)`,
   which checks the mtimes of `lean/<locale>/MedicalKnowledge.lean`
   against its `.olean` / `.ilean` companions and runs
   `lean -o MedicalKnowledge.olean -i MedicalKnowledge.ilean
   MedicalKnowledge.lean` (with `cwd=lean/<locale>`) if either is missing
   or stale. The compiled module is what each locale's scenario files
   import.
2. A request to `POST /scenarios/{id}/verify` looks the scenario up in
   the per-locale `scenarios.get_scenarios(locale)` whitelist. Unknown
   ids 404. **No request data is ever interpolated into Lean source** —
   the only thing the handler does is map an id to a fixed filename,
   which is identical across locales.
3. `subprocess.run([LEAN_BINARY, scenario.lean_filename],
   cwd=lean/<locale>/, env={"LEAN_PATH": "lean/<locale>/", ...},
   timeout=60)`. Setting `LEAN_PATH` to the locale subdirectory lets the
   static `import MedicalKnowledge` line in each scenario resolve against
   the locale-specific precompiled `.olean` (so the JA build sees the
   JSH / JDS / JRS axioms and the EN build sees the AHA / ADA / AASM
   axioms).
4. `_parse_trusted_axioms()` scans stdout for the
   `'…absurd' depends on axioms: [ … ]` block emitted by the
   `#print axioms absurd` line at the end of every scenario file and
   returns the list of axiom names.
5. `_classify()` maps the compiler outcome onto a three-state `Verdict`:
   `CollisionVerified` (exit 0, axiom list present, no `sorryAx`,
   no `error:` lines), `ProofUnsound` (axiom list contains `sorryAx`),
   or `CompilerError` (any other failure). The Jinja template renders
   `alert-danger` for a verified collision, `alert-warning` for the two
   failure modes, and a fallback when the compiler is missing or timed
   out.

`LEAN_BINARY` is resolved once at import time via `shutil.which("lean")`.
Override by exporting a different `lean` on PATH or editing the constant.

### Syntax highlighting

`_write_syntax_css()` runs at module import and writes `static/syntax.css`
containing two Pygments stylesheets wrapped in
`@media (prefers-color-scheme: ...)` blocks (Tango for light, Monokai for
dark). Per-scenario highlighted HTML is computed on demand in
`_scenario_context()` from the static `.lean` file's contents and passed
to templates as `highlighted_lean | safe`.

### Scenario data model (`scenarios.py`)

```python
@dataclass(frozen=True)
class Guideline:
    source: str        # journal/society + section
    body: str          # natural-language guideline excerpt

@dataclass(frozen=True)
class Scenario:
    id: str            # URL slug, e.g. "scenario-a"
    title: str
    subtitle: str
    patient_summary: str
    guideline_a: Guideline
    guideline_b: Guideline
    lean_filename: str         # filename, e.g. "ScenarioA.lean"
    lean_subdir: str           # locale dir, e.g. "ja" or "en"
    audit_summary: str         # short technical caption under the code frame
    plain_english: str         # narrative shown in the verification result alert

SCENARIOS_BY_LOCALE: dict[str, dict[str, Scenario]] = {
    "ja": { ... },   # JSH / JSN / JDS / JSAD-JSNP / JRS citations
    "en": { ... },   # ACC/AHA / KDIGO / ADA / AACE-ACE / APA / AASM
}

def get_scenarios(locale: str) -> dict[str, Scenario]: ...
```

Each `Scenario` resolves its file via `lean/<lean_subdir>/<lean_filename>`,
so the JA and EN copies of `scenario-a` share an `id` and a `lean_filename`
("ScenarioA.lean") but live in `lean/ja/` and `lean/en/` respectively
with locale-appropriate identifiers (`TaroYamada` vs. `JohnDoe`,
`JSH2019_Ch5_FirstLine` vs. `AHA_ACC_HTN_8_1_5`). UI chrome strings
(button labels, alert titles, decoder legend, etc.) live separately in
`i18n.UI_STRINGS` and reach templates as `t`. Tooltip prose lives in
`lean_vocab.py` (per-locale `VocabEntry` tables) and `lean_decorate.py`
(per-locale composer branches), so hovering on `JSH2019_Ch5_FirstLine`
in the JA build shows a Japanese explanation while hovering on
`AHA_ACC_HTN_8_1_5` in the EN build shows an English one.

`scenarios.py` carries no Lean source. The actual proof for each
scenario lives in `lean/<lean_subdir>/<lean_filename>` and follows the
same shape:

* `import MedicalKnowledge`
* a fresh `namespace ClinicalAudit.ScenarioX`
* `axiom Patient` introducing the patient inhabitant
* one `axiom obs_*` per chart-derived finding
* `theorem absurd : False := by …` deriving the contradiction with
  explicit tactics (`apply And.intro`, `exact`, `unfold`, etc.) from the
  guideline axioms in `MedicalKnowledge.lean`
* `#print axioms absurd` emitting the trusted-axiom witness the host
  parser uses to confirm the kernel really used the expected guidelines.

### Adding a new scenario

1. Add the new guideline (or two) and any new condition predicates to
   **both** `lean/en/MedicalKnowledge.lean` and
   `lean/ja/MedicalKnowledge.lean`. Each guideline is a single `axiom`
   of shape `∀ p, HasFooCondition p → Indicated p Treatment.bar` (or
   `Contraindicated`); the EN file names it after the American society
   (e.g. `AHA_…`) and the JA file after the Japanese society (e.g.
   `JSH…`). Delete the cached `MedicalKnowledge.olean` in each locale
   directory so the host recompiles it on next request.
2. Create `lean/en/ScenarioD.lean` and `lean/ja/ScenarioD.lean`
   following the structure above and prove `theorem absurd : False`
   with explicit tactics. Run
   `(cd lean/en && LEAN_PATH=. lean ScenarioD.lean)` and the
   corresponding `lean/ja/` invocation by hand to confirm the kernel
   accepts each proof.
3. Append a new `Scenario` constant to `scenarios.py` for **both**
   locales (`_JA_SCENARIO_D` citing the Japanese guideline and
   `_EN_SCENARIO_D` citing the American one) with `lean_filename=
   "ScenarioD.lean"` and `lean_subdir="ja"` / `lean_subdir="en"`. Add
   each to the matching entry in `SCENARIOS_BY_LOCALE` at the bottom of
   the module.
4. Add `VocabEntry` records for any new symbols to **both**
   `_EN_VOCAB` and `_JA_VOCAB` in `lean_vocab.py` so the tooltip
   composer has English and Japanese glosses for them.
5. Append the expected axiom set to **both** locale dicts in
   `scripts/check_scenarios.py` so the regression harness pins the new
   proof in each language.
6. The sidebar, fragment endpoint, and verify endpoint all pick the new
   scenario up automatically — no template edits required.

## Common dev tasks

```bash
# Install / sync deps after a pull
uv sync

# Add a runtime dep
uv add <package>

# Add a dev-only dep
uv add --dev <package>

# Run an arbitrary command in the project venv
uv run <command>

# Re-verify all 6 Lean scenarios (3 × 2 locales) from the CLI (no server)
uv run python -c "
from app import _run_lean
from scenarios import get_scenarios
for locale in ('ja', 'en'):
    for sid, sc in get_scenarios(locale).items():
        r = _run_lean(sc)
        print(locale, sid, r.verdict, list(r.trusted_axioms), r.exit_code)
"

# Run the regression harness (pins both locales)
uv run python scripts/check_scenarios.py

# Compile a single scenario by hand against its locale's knowledge base
(cd lean/ja && LEAN_PATH=. lean ScenarioA.lean)
(cd lean/en && LEAN_PATH=. lean ScenarioA.lean)
```

`static/syntax.css` is overwritten on every app import — don't hand-edit it;
edit the Pygments style names in `_write_syntax_css()` instead.

## Limitations

- The knowledge base is hand-curated. There is no automatic translation
  from natural-language guidelines to `axiom` declarations; encoder
  discipline is the dominant correctness constraint, and a misencoded
  precondition or modality will silently produce the wrong proof
  obligation.
- The deontic semantics is monotonic. `incompatible_modalities` flatly
  forbids `Indicated p t ∧ Contraindicated p t` for any `p`, `t`, so
  there is no built-in mechanism for guideline defeasibility,
  prioritisation, or context-conditioned exceptions. Conditional
  guidelines must be encoded as guideline axioms with the precondition
  in the antecedent.
- There is no separate metatheorem proving that the encoded axioms
  faithfully represent the published guidelines. The verification claim
  is "the Lean kernel typechecks `theorem absurd : False` from exactly
  this list of trusted axioms," not "this list of axioms is a sound
  formalisation of the underlying clinical literature."

## License

Apache License 2.0. See [`LICENSE`](LICENSE).
