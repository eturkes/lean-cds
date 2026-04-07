# lean-cds

A local proof-of-concept that translates clinical guidelines into a
deeply-embedded Lean 4 DSL with deontic modality, contextual preconditions,
and priority-based defeasible reasoning, then asks the Lean kernel to
typecheck and reduce a `Verdict` computation for each patient scenario. The
verifier returns one of four states — `Recommended`, `Underdetermined`,
`InsufficientData`, or `GenuineConflict` — surfacing whether the encoded
rules unambiguously recommend an action, leave room for clinician choice,
lack the chart data needed to decide, or genuinely disagree.

The UI is an HTMX gallery with a sidebar of scenarios, a two-column main
panel (natural-language guidelines on the left, generated Lean 4 source on
the right), and a verification button that streams the live `lean` compiler
output back to the browser.

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
├── scenarios.py                    # Scenario dataclass + the 3 mock scenarios
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

### Verification pipeline (`app.py:106` `_run_lean`)

1. Look up the `Scenario` by id (`scenarios.SCENARIOS`).
2. Concatenate `CORE_LEAN_SOURCE + "\n\n" + scenario.lean_code` and write
   the result to `audit.lean` inside a fresh
   `tempfile.TemporaryDirectory(prefix="lean-cds-")`. The shared core
   defines the `Rule` / `Chart` / `Verdict` types and the `evaluate`
   function once; each scenario fragment supplies only its own `rules`,
   `chart`, and final `#eval` line.
3. `subprocess.run([LEAN_BINARY, "audit.lean"], ..., timeout=60)`.
4. Scan stdout for the last line matching
   `^VERDICT: (\w+)(?:\s+(.*))?$` and decode the tag into a four-state
   `Verdict` enum (`Recommended | Underdetermined | InsufficientData |
   GenuineConflict`); the second capture group becomes `verdict_detail`.
5. Return a `VerificationResult` (exit code, stdout, stderr, `verdict`,
   `verdict_detail`, `error_message`). The Jinja template picks one of
   five banners: `alert-success` for `Recommended`, `alert-info` for
   `Underdetermined`, `alert-warning` for `InsufficientData`,
   `alert-danger` for `GenuineConflict`, and a fallback `alert-warning`
   when the compiler is missing, timed out, or did not emit a parseable
   `VERDICT:` marker.

`LEAN_BINARY` is resolved once at import time via `shutil.which("lean")`.
Override by exporting a different `lean` on PATH or editing the constant.

### Syntax highlighting

`app.py:45` `_write_syntax_css()` runs at module import and writes
`static/syntax.css` containing two Pygments stylesheets wrapped in
`@media (prefers-color-scheme: ...)` blocks (Tango for light, Monokai for
dark). Per-scenario highlighted HTML is precomputed in
`_scenario_context()` and passed to templates as `highlighted_lean | safe`.

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
    lean_code: str             # full audit.lean source
    verdict_summary: str       # plain-English verdict explanation

SCENARIOS: dict[str, Scenario] = {...}   # what the app iterates over
```

Each `lean_code` opens its own namespace, opens `ClinicalAudit.Core` (the
shared core defined in `CORE_LEAN_SOURCE`), defines `rules : List Rule` and
`chart : Chart` for the patient context, and ends with
`#eval IO.println s!"VERDICT: {evaluate rules chart}"` so the Lean kernel
prints the four-state verdict to stdout. Each `Rule` carries an id, a source
citation, an `appliesWhen : Chart → ThreeValued` precondition, a
`(DeonticModality × Action)` conclusion, and a `Nat` priority used by
`evaluate` to resolve disagreements between rules concluding opposite
modalities on the same action.

### Adding a new scenario

1. Append a new `Scenario` constant to `scenarios.py` with realistic
   guideline text and a `lean_code` string that:
   - opens a fresh namespace (e.g. `namespace ClinicalAudit.ScenarioD`),
   - opens the shared core with `open ClinicalAudit.Core`,
   - defines `def rules : List Rule := [ ... ]` listing the encoded
     guideline rules with their preconditions, deontic conclusions, and
     priorities,
   - defines `def chart : Chart := { lookup := fun obs => match obs with ... }`
     mapping each observation key the rules reference to a `ThreeValued`
     value, with `_ => .tUnknown` as the catch-all,
   - ends with `#eval IO.println s!"VERDICT: {evaluate rules chart}"`,
   - closes the namespace with `end ClinicalAudit.ScenarioD`.
2. Add the constant to the `SCENARIOS` dict at the bottom of the module
   and write a 1–2 sentence `verdict_summary` describing the verdict the
   verifier should produce.
3. Sanity-check from the CLI:
   ```bash
   uv run python -c "
   from app import _run_lean
   from scenarios import SCENARIOS
   r = _run_lean(SCENARIOS['<your-id>'])
   print(r.verdict, repr(r.verdict_detail), r.exit_code)
   "
   ```
4. Optionally add an entry to `scripts/check_scenarios.py` so the
   regression harness asserts the expected `(verdict, verdict_detail)`
   pair on every run.
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
    print(sid, r.verdict, repr(r.verdict_detail), r.exit_code)
"

# Run the regression harness
uv run python scripts/check_scenarios.py
```

`static/syntax.css` is overwritten on every app import — don't hand-edit it;
edit the Pygments style names in `_write_syntax_css()` instead.

## Limitations

- The DSL is hand-curated. There is no automatic translation from
  natural-language guidelines to `Rule` definitions; encoder discipline is
  the dominant correctness constraint, and a misencoded precondition or
  modality will silently produce a wrong verdict.
- Defeasibility is implemented as naive numeric priority on individual
  rules, not a real argumentation framework (ASPIC+, defeasible logic
  programming, Carneades, etc.). The mechanism is adequate for the
  scenarios in this repository and not much beyond them.
- There is no separate soundness theorem for `evaluate`. The verification
  claim is "the Lean kernel typechecks the function definition and reduces
  it to a concrete `Verdict` for each scenario" — not "the verdict is a
  sound consequence of the encoded rules under any particular non-monotonic
  semantics."
- A two-tier architecture — an external solver (e.g. an ASP engine)
  emitting a Lean-checkable certificate — is deferred until after the demo
  stage. Today the entire reasoning step lives inside Lean's reduction.

## License

Apache License 2.0. See [`LICENSE`](LICENSE).
