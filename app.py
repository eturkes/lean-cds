"""Verifiable Clinical Decision Support — Litestar application.

Serves the Guideline Collision Gallery UI and exposes a verification endpoint
that writes the selected scenario's Lean 4 source to a temporary file, invokes
the ``lean`` compiler, and returns the captured output as an HTML fragment for
HTMX-driven swap into the page.
"""

from __future__ import annotations

import enum
import re
import shutil
import subprocess
import tempfile
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

from scenarios import CORE_LEAN_SOURCE, SCENARIOS, Scenario

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


class Verdict(enum.Enum):
    Recommended = "Recommended"
    Underdetermined = "Underdetermined"
    InsufficientData = "InsufficientData"
    GenuineConflict = "GenuineConflict"


_VERDICT_LINE_RE = re.compile(r"^VERDICT: (\w+)(?:\s+(.*))?$")


@dataclass(frozen=True)
class VerificationResult:
    exit_code: int
    stdout: str
    stderr: str
    verdict: Verdict | None
    verdict_detail: str
    error_message: str | None


def _parse_verdict(stdout: str) -> tuple[Verdict | None, str]:
    """Scan Lean stdout for the last ``VERDICT:`` marker and decode it.

    The core source emits a smoke ``VERDICT:`` line before the scenario
    fragment runs, so the scenario's own verdict is always the final match.
    """
    last: tuple[Verdict | None, str] | None = None
    for line in stdout.splitlines():
        match = _VERDICT_LINE_RE.match(line)
        if match is None:
            continue
        tag, detail = match.group(1), match.group(2) or ""
        try:
            last = (Verdict[tag], detail)
        except KeyError:
            last = (None, "")
    return last if last is not None else (None, "")


def _run_lean(scenario: Scenario) -> VerificationResult:
    """Write the scenario's Lean source to a temp file and run the compiler."""
    source = CORE_LEAN_SOURCE + "\n\n" + scenario.lean_code
    with tempfile.TemporaryDirectory(prefix="lean-cds-") as tmpdir:
        audit_path = Path(tmpdir) / "audit.lean"
        audit_path.write_text(source, encoding="utf-8")
        try:
            completed = subprocess.run(
                [LEAN_BINARY, str(audit_path)],
                capture_output=True,
                text=True,
                timeout=LEAN_TIMEOUT_SECONDS,
                cwd=tmpdir,
            )
        except FileNotFoundError:
            return VerificationResult(
                exit_code=-1,
                stdout="",
                stderr="",
                verdict=None,
                verdict_detail="",
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
                verdict_detail="",
                error_message=(
                    f"Lean verification exceeded the {LEAN_TIMEOUT_SECONDS}s "
                    "time limit."
                ),
            )

    verdict, verdict_detail = _parse_verdict(completed.stdout)
    return VerificationResult(
        exit_code=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
        verdict=verdict,
        verdict_detail=verdict_detail,
        error_message=None,
    )


def _get_scenario(scenario_id: str) -> Scenario:
    scenario = SCENARIOS.get(scenario_id)
    if scenario is None:
        raise NotFoundException(detail=f"Unknown scenario id: {scenario_id}")
    return scenario


def _scenario_context(scenario: Scenario) -> dict[str, object]:
    return {
        "scenario": scenario,
        "highlighted_lean": _highlight_lean(scenario.lean_code),
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
