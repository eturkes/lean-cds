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
├── scenarios.py                    # Scenario metadata and ID → .lean filename map
├── lean/
│   ├── MedicalKnowledge.lean       # Shared knowledge base: types, predicates, axioms
│   ├── ScenarioA.lean              # Hypertension vs. severe dehydration proof
│   ├── ScenarioB.lean              # DKA vs. severe hypokalaemia proof
│   └── ScenarioC.lean              # Acute panic vs. untreated severe OSA proof
├── scripts/
│   └── check_scenarios.py          # Regression harness asserting expected axiom sets
├── templates/
│   ├── index.html                  # Full page shell + sidebar
│   ├── _scenario_panel.html        # Scenario two-column body (HTMX target)
│   └── _verification_result.html   # Compiler-result alert + terminal
├── static/
│   ├── styles.css                  # Hand-written enterprise theme (light/dark)
│   └── syntax.css                  # Pygments CSS, regenerated at app import
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

### Verification pipeline (`app.py` `_run_lean`)

1. At import time, `_ensure_knowledge_base_compiled()` checks the mtimes
   of `lean/MedicalKnowledge.lean` against its `.olean` / `.ilean`
   companions and runs `lean -o MedicalKnowledge.olean -i
   MedicalKnowledge.ilean MedicalKnowledge.lean` if either is missing or
   stale. The compiled module is what every scenario file imports.
2. A request to `POST /scenarios/{id}/verify` looks the scenario up in
   the `scenarios.SCENARIOS` whitelist. Unknown ids 404. **No request
   data is ever interpolated into Lean source** — the only thing the
   handler does is map an id to a fixed filename.
3. `subprocess.run([LEAN_BINARY, scenario.lean_filename], cwd=lean/,
   env={"LEAN_PATH": "lean/", ...}, timeout=60)`. Setting `LEAN_PATH`
   lets the static `import MedicalKnowledge` line in each scenario
   resolve against the precompiled `.olean`.
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
    lean_filename: str         # filename inside lean/ (e.g. "ScenarioA.lean")
    audit_summary: str         # plain-English explanation of the proof

SCENARIOS: dict[str, Scenario] = {...}   # what the app iterates over
```

`scenarios.py` carries no Lean source. The actual proof for each
scenario lives in `lean/<lean_filename>` and follows the same shape:

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

1. Add a guideline (or two) and any new condition predicates to
   `lean/MedicalKnowledge.lean`. Each guideline is a single
   `axiom` of shape `∀ p, HasFooCondition p → Indicated p Treatment.bar`
   (or `Contraindicated`). Delete the cached `MedicalKnowledge.olean`
   so the host recompiles it on next request.
2. Create `lean/ScenarioD.lean` following the structure above and
   prove `theorem absurd : False` with explicit tactics. Run
   `LEAN_PATH=lean lean lean/ScenarioD.lean` once by hand to confirm
   the kernel accepts the proof.
3. Append a new `Scenario` constant to `scenarios.py` with realistic
   guideline text and `lean_filename="ScenarioD.lean"`, then add it to
   the `SCENARIOS` dict at the bottom of the module.
4. Append the expected axiom set to `scripts/check_scenarios.py` so the
   regression harness pins the new proof.
5. The sidebar, fragment endpoint, and verify endpoint all pick the new
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

# Re-verify all 3 Lean scenarios from the CLI (no server)
uv run python -c "
from app import _run_lean
from scenarios import SCENARIOS
for sid, sc in SCENARIOS.items():
    r = _run_lean(sc)
    print(sid, r.verdict, list(r.trusted_axioms), r.exit_code)
"

# Run the regression harness
uv run python scripts/check_scenarios.py

# Compile a single scenario by hand against the knowledge base
(cd lean && LEAN_PATH=. lean ScenarioA.lean)
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
