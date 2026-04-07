"""Verifiable Clinical Decision Support — Litestar application.

Serves the Guideline Collision Gallery UI and exposes a verification
endpoint that invokes the Lean 4 compiler against a *static*, pre-written
``ScenarioX.lean`` file. No user input is ever interpolated into Lean
source: each scenario id is mapped through an in-process whitelist
(``scenarios.SCENARIOS``) to a fixed filename in the ``lean/`` directory.

At import time the shared knowledge base (``lean/MedicalKnowledge.lean``)
is compiled once to ``lean/MedicalKnowledge.olean`` so that subsequent
scenario verifications can `import` it as a precompiled module — this
keeps each verification a single, fast ``lean`` invocation rather than a
cold compile of the whole DSL on every request.
"""

from __future__ import annotations

import enum
import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from litestar import Litestar, get, post
from litestar.contrib.jinja import JinjaTemplateEngine
from litestar.exceptions import NotFoundException
from litestar.response import Template
from litestar.static_files import create_static_files_router
from litestar.template.config import TemplateConfig
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import Lean4Lexer

from scenarios import (
    KNOWLEDGE_BASE_FILE,
    KNOWLEDGE_BASE_MODULE,
    LEAN_DIR,
    SCENARIOS,
    Scenario,
)

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

LEAN_BINARY = shutil.which("lean") or "lean"
LEAN_TIMEOUT_SECONDS = 60

_LEXER = Lean4Lexer()
_FORMATTER = HtmlFormatter(nowrap=False, cssclass="lean-code", noclasses=False)


def _highlight_lean(code: str) -> str:
    """Render Lean 4 source as syntax-highlighted HTML."""
    return highlight(code, _LEXER, _FORMATTER)


def _write_syntax_css() -> None:
    """Emit a dual light/dark Pygments stylesheet wrapped in media queries."""
    light = HtmlFormatter(style="tango").get_style_defs(".lean-code")
    dark = HtmlFormatter(style="monokai").get_style_defs(".lean-code")
    css = (
        "/* Auto-generated from Pygments at app startup. */\n"
        "@media (prefers-color-scheme: light) {\n"
        f"{light}\n"
        "}\n"
        "@media (prefers-color-scheme: dark) {\n"
        f"{dark}\n"
        "}\n"
    )
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    (STATIC_DIR / "syntax.css").write_text(css, encoding="utf-8")


_write_syntax_css()


def _ensure_knowledge_base_compiled() -> str | None:
    """Compile ``MedicalKnowledge.lean`` to ``.olean`` if it is stale.

    Returns ``None`` on success or a human-readable error string on failure.
    The compiled artefact is what every scenario file imports, so the
    application refuses to start serving verifications until it exists.
    """
    olean_path = LEAN_DIR / f"{KNOWLEDGE_BASE_MODULE}.olean"
    ilean_path = LEAN_DIR / f"{KNOWLEDGE_BASE_MODULE}.ilean"
    src_mtime = KNOWLEDGE_BASE_FILE.stat().st_mtime
    if (
        olean_path.exists()
        and olean_path.stat().st_mtime >= src_mtime
        and ilean_path.exists()
        and ilean_path.stat().st_mtime >= src_mtime
    ):
        return None
    try:
        completed = subprocess.run(
            [
                LEAN_BINARY,
                "-o",
                olean_path.name,
                "-i",
                ilean_path.name,
                KNOWLEDGE_BASE_FILE.name,
            ],
            capture_output=True,
            text=True,
            timeout=LEAN_TIMEOUT_SECONDS,
            cwd=LEAN_DIR,
        )
    except FileNotFoundError:
        return (
            "The Lean 4 compiler executable was not found on this system. "
            "Install Lean via elan and ensure it is on PATH."
        )
    except subprocess.TimeoutExpired:
        return (
            f"Compiling MedicalKnowledge.lean exceeded the "
            f"{LEAN_TIMEOUT_SECONDS}s time limit."
        )
    if completed.returncode != 0:
        return (
            "Lean failed to compile MedicalKnowledge.lean:\n"
            f"{completed.stdout}\n{completed.stderr}".strip()
        )
    return None


_KNOWLEDGE_BASE_ERROR: str | None = _ensure_knowledge_base_compiled()


class Verdict(enum.Enum):
    """Outcomes the host parser can derive from a Lean verification run."""

    CollisionVerified = "CollisionVerified"
    ProofUnsound = "ProofUnsound"
    CompilerError = "CompilerError"


@dataclass(frozen=True)
class VerificationResult:
    exit_code: int
    stdout: str
    stderr: str
    verdict: Verdict | None
    trusted_axioms: tuple[str, ...]
    error_message: str | None


_AXIOMS_RE = re.compile(
    r"depends on axioms:\s*\[([^\]]*)\]",
    re.DOTALL,
)


def _parse_trusted_axioms(stdout: str) -> tuple[str, ...]:
    """Extract the axiom dependency list emitted by ``#print axioms``.

    Lean's pretty printer wraps the bracketed list across multiple lines
    and indents continuation lines, so the regex spans newlines and we
    normalise whitespace before splitting on commas.
    """
    match = _AXIOMS_RE.search(stdout)
    if match is None:
        return ()
    raw = match.group(1)
    parts = [chunk.strip() for chunk in raw.split(",")]
    return tuple(p for p in parts if p)


def _classify(
    exit_code: int, stdout: str, stderr: str, axioms: tuple[str, ...]
) -> Verdict:
    """Map the Lean compiler outcome onto a `Verdict`."""
    if exit_code != 0:
        return Verdict.CompilerError
    if not axioms:
        return Verdict.CompilerError
    if "sorryAx" in axioms:
        return Verdict.ProofUnsound
    lowered = (stdout + "\n" + stderr).lower()
    if "error:" in lowered:
        return Verdict.CompilerError
    return Verdict.CollisionVerified


def _run_lean(scenario: Scenario) -> VerificationResult:
    """Invoke ``lean`` against the scenario's static ``.lean`` file."""
    if _KNOWLEDGE_BASE_ERROR is not None:
        return VerificationResult(
            exit_code=-1,
            stdout="",
            stderr="",
            verdict=None,
            trusted_axioms=(),
            error_message=_KNOWLEDGE_BASE_ERROR,
        )
    env = os.environ.copy()
    existing = env.get("LEAN_PATH")
    env["LEAN_PATH"] = (
        f"{LEAN_DIR}{os.pathsep}{existing}" if existing else str(LEAN_DIR)
    )
    try:
        completed = subprocess.run(
            [LEAN_BINARY, scenario.lean_filename],
            capture_output=True,
            text=True,
            timeout=LEAN_TIMEOUT_SECONDS,
            cwd=LEAN_DIR,
            env=env,
        )
    except FileNotFoundError:
        return VerificationResult(
            exit_code=-1,
            stdout="",
            stderr="",
            verdict=None,
            trusted_axioms=(),
            error_message=(
                "The Lean 4 compiler executable was not found on this "
                "system. Install Lean via elan and ensure it is on PATH."
            ),
        )
    except subprocess.TimeoutExpired:
        return VerificationResult(
            exit_code=-1,
            stdout="",
            stderr="",
            verdict=None,
            trusted_axioms=(),
            error_message=(
                f"Lean verification exceeded the {LEAN_TIMEOUT_SECONDS}s "
                "time limit."
            ),
        )

    axioms = _parse_trusted_axioms(completed.stdout)
    verdict = _classify(completed.returncode, completed.stdout, completed.stderr, axioms)
    return VerificationResult(
        exit_code=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
        verdict=verdict,
        trusted_axioms=axioms,
        error_message=None,
    )


def _get_scenario(scenario_id: str) -> Scenario:
    scenario = SCENARIOS.get(scenario_id)
    if scenario is None:
        raise NotFoundException(detail=f"Unknown scenario id: {scenario_id}")
    return scenario


def _scenario_context(scenario: Scenario) -> dict[str, object]:
    lean_source = scenario.read_lean_source()
    return {
        "scenario": scenario,
        "lean_source": lean_source,
        "highlighted_lean": _highlight_lean(lean_source),
    }


@get("/", name="index")
async def index() -> Template:
    scenarios = list(SCENARIOS.values())
    return Template(
        template_name="index.html",
        context={
            "scenarios": scenarios,
            **_scenario_context(scenarios[0]),
        },
    )


@get("/scenarios/{scenario_id:str}", name="scenario_panel")
async def scenario_panel(scenario_id: str) -> Template:
    scenario = _get_scenario(scenario_id)
    return Template(
        template_name="_scenario_panel.html",
        context=_scenario_context(scenario),
    )


@post("/scenarios/{scenario_id:str}/verify", name="verify_scenario")
async def verify_scenario(scenario_id: str) -> Template:
    scenario = _get_scenario(scenario_id)
    result = _run_lean(scenario)
    return Template(
        template_name="_verification_result.html",
        context={"scenario": scenario, "result": result},
    )


app = Litestar(
    route_handlers=[
        index,
        scenario_panel,
        verify_scenario,
        create_static_files_router(path="/static", directories=[STATIC_DIR]),
    ],
    template_config=TemplateConfig(
        directory=TEMPLATES_DIR,
        engine=JinjaTemplateEngine,
    ),
)
