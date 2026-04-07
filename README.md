# lean-cds

A local proof-of-concept web application that demonstrates a **Verifiable
Clinical Decision Support (CDS)** system. Each scenario translates two
real-world clinical guideline excerpts into Lean 4 axioms and asks the Lean
compiler to prove that the encoded guidelines are mutually inconsistent on a
single patient context (`theorem polypharmacy_collision : False`).

The UI is a "Guideline Collision Gallery" with a sidebar of scenarios, a
two-column main panel (natural-language guidelines on the left, generated
Lean 4 source on the right), and a verification button that streams the live
`lean` compiler output back to the browser via HTMX.

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

### Verification pipeline (`app.py:74` `_run_lean`)

1. Look up the `Scenario` by id (`scenarios.SCENARIOS`).
2. Write its `lean_code` field to `audit.lean` inside a fresh
   `tempfile.TemporaryDirectory(prefix="lean-cds-")`.
3. `subprocess.run([LEAN_BINARY, "audit.lean"], ..., timeout=60)`.
4. Set `contradiction_proven = (returncode == 0 and
   "polypharmacy_collision : False" in stdout)`.
5. Return a `VerificationResult` (exit code, stdout, stderr, flag,
   error_message). The Jinja template chooses one of three banners:
   `alert-danger` (contradiction proven), `alert-info` (no contradiction),
   `alert-warning` (compiler missing or timed out).

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
    collision_summary: str     # plain-English collision explanation

SCENARIOS: dict[str, Scenario] = {...}   # what the app iterates over
```

Each `lean_code` defines an abstract `Patient` type, predicates for the two
clinical conditions, an `intervention` predicate, observation axioms for the
specific patient, and two guideline axioms — one mandating the intervention,
one negating it. The theorem then derives `False` by `exact h_neg h_pos`.

### Adding a new scenario

1. Append a new `Scenario` constant to `scenarios.py` with realistic
   guideline text and a Lean source string that defines a
   `theorem polypharmacy_collision : False` inside its own
   `namespace ClinicalAudit_<id>`.
2. Add the constant to the `SCENARIOS` dict at the bottom of the module.
3. Sanity-check the Lean compiles to `False`:
   ```bash
   uv run python -c "
   from app import _run_lean
   from scenarios import SCENARIOS
   r = _run_lean(SCENARIOS['<your-id>'])
   assert r.contradiction_proven, (r.exit_code, r.stdout, r.stderr)
   "
   ```
4. The sidebar, fragment endpoint, and verify endpoint all pick it up
   automatically — no template edits required.

The `contradiction_proven` flag depends on the literal substring
`polypharmacy_collision : False` appearing in the compiler stdout. Keep the
theorem name stable, or update the check in `app.py:110`.

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
    print(sid, r.contradiction_proven, r.exit_code)
"
```

`static/syntax.css` is overwritten on every app import — don't hand-edit it;
edit the Pygments style names in `_write_syntax_css()` instead.

## License

Apache License 2.0. See [`LICENSE`](LICENSE).
