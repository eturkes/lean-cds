"""Verifiable Clinical Decision Support — Litestar application.

Serves the bilingual Guideline Collision Gallery UI (Japanese default,
English toggle) and exposes a verification endpoint that invokes the
Lean 4 compiler against a *static*, pre-written ``ScenarioX.lean`` file.
No user input is ever interpolated into Lean source: each scenario id is
mapped through an in-process whitelist (``scenarios.get_scenarios``) to
a fixed filename in the ``lean/`` directory.

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

from litestar import Litestar, Request, get, post
from litestar.contrib.jinja import JinjaTemplateEngine
from litestar.datastructures import Cookie
from litestar.exceptions import NotFoundException
from litestar.response import Template
from litestar.static_files import create_static_files_router
from litestar.template.config import TemplateConfig
from pygments.formatters import HtmlFormatter
from pygments.lexers import Lean4Lexer

from i18n import (
    LANGUAGE_COOKIE,
    SUPPORTED_LOCALES,
    get_ui_strings,
    normalize_locale,
    other_locale,
)
from lean_decorate import render_lean_with_tooltips
from scenarios import (
    KNOWLEDGE_BASE_MODULE,
    LEAN_DIR,
    Scenario,
    get_scenarios,
    knowledge_base_file,
)

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

LEAN_BINARY = shutil.which("lean") or "lean"
LEAN_TIMEOUT_SECONDS = 60

_LEXER = Lean4Lexer()
_FORMATTER = HtmlFormatter(nowrap=False, cssclass="lean-code", noclasses=False)

def _highlight_lean(code: str, locale: str) -> str:
    """Render Lean 4 source as syntax-highlighted HTML with per-line tips.

    The real work lives in `lean_decorate.render_lean_with_tooltips`: it
    parses the scenario file into a line → declaration map, runs Pygments
    normally, and then rewrites every recognised token span so its
    `data-lean-tip` attribute holds a plain-English (or plain-Japanese)
    sentence composed from *that specific line's* declaration (name,
    type, proof body, or tactic argument). The browser tooltip popover
    in `static/tooltips.js` reads the attribute value directly.

    ``locale`` selects which medical-knowledge vocabulary table to read
    for guideline-axiom and patient-name glosses, so the JA build of a
    scenario file gets Japanese tooltips referencing JSH/JDS/JRS axioms.
    """
    return render_lean_with_tooltips(code, _LEXER, _FORMATTER, locale=locale)


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


def _ensure_knowledge_base_compiled(locale: str) -> str | None:
    """Compile a locale's ``MedicalKnowledge.lean`` to ``.olean`` if stale.

    Returns ``None`` on success or a human-readable error string on
    failure. The compiled artefact is what every scenario file in the
    locale's ``lean/<locale>/`` directory imports.
    """
    src = knowledge_base_file(locale)
    locale_dir = src.parent
    olean_path = locale_dir / f"{KNOWLEDGE_BASE_MODULE}.olean"
    ilean_path = locale_dir / f"{KNOWLEDGE_BASE_MODULE}.ilean"
    src_mtime = src.stat().st_mtime
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
                src.name,
            ],
            capture_output=True,
            text=True,
            timeout=LEAN_TIMEOUT_SECONDS,
            cwd=locale_dir,
        )
    except FileNotFoundError:
        return (
            "The Lean 4 compiler executable was not found on this system. "
            "Install Lean via elan and ensure it is on PATH."
        )
    except subprocess.TimeoutExpired:
        return (
            f"Compiling {locale}/MedicalKnowledge.lean exceeded the "
            f"{LEAN_TIMEOUT_SECONDS}s time limit."
        )
    if completed.returncode != 0:
        return (
            f"Lean failed to compile {locale}/MedicalKnowledge.lean:\n"
            f"{completed.stdout}\n{completed.stderr}".strip()
        )
    return None


def _precompile_all_knowledge_bases() -> dict[str, str | None]:
    """Compile every supported locale's knowledge base; return errors keyed by locale."""
    return {loc: _ensure_knowledge_base_compiled(loc) for loc in SUPPORTED_LOCALES}


_KNOWLEDGE_BASE_ERRORS: dict[str, str | None] = _precompile_all_knowledge_bases()


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
    """Invoke ``lean`` against the scenario's static ``.lean`` file.

    Each scenario lives under ``lean/<locale>/`` and imports the
    sibling ``MedicalKnowledge.olean`` from that same directory, so the
    subprocess is run with ``cwd`` and ``LEAN_PATH`` both set to the
    locale-specific subdirectory.
    """
    locale_error = _KNOWLEDGE_BASE_ERRORS.get(scenario.lean_subdir)
    if locale_error is not None:
        return VerificationResult(
            exit_code=-1,
            stdout="",
            stderr="",
            verdict=None,
            trusted_axioms=(),
            error_message=locale_error,
        )
    locale_dir = scenario.lean_dir
    env = os.environ.copy()
    existing = env.get("LEAN_PATH")
    env["LEAN_PATH"] = (
        f"{locale_dir}{os.pathsep}{existing}" if existing else str(locale_dir)
    )
    try:
        completed = subprocess.run(
            [LEAN_BINARY, scenario.lean_filename],
            capture_output=True,
            text=True,
            timeout=LEAN_TIMEOUT_SECONDS,
            cwd=locale_dir,
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


def _resolve_locale(request: Request) -> str:
    """Pick the active locale from query string, then cookie, then default.

    Query parameter ``?lang=ja|en`` always wins so a deep link or the
    header toggle can override a previously stored cookie. Anything else
    falls back to the JA default.
    """
    query_lang = request.query_params.get("lang") if request.query_params else None
    if query_lang is not None:
        return normalize_locale(query_lang)
    cookie_lang = request.cookies.get(LANGUAGE_COOKIE) if request.cookies else None
    return normalize_locale(cookie_lang)


def _get_scenario(scenario_id: str, locale: str) -> Scenario:
    scenarios = get_scenarios(locale)
    scenario = scenarios.get(scenario_id)
    if scenario is None:
        raise NotFoundException(detail=f"Unknown scenario id: {scenario_id}")
    return scenario


def _scenario_context(scenario: Scenario, locale: str) -> dict[str, object]:
    lean_source = scenario.read_lean_source()
    return {
        "scenario": scenario,
        "lean_source": lean_source,
        "highlighted_lean": _highlight_lean(lean_source, locale),
        "lang": locale,
        "other_lang": other_locale(locale),
        "t": get_ui_strings(locale),
    }


def _persist_locale(template: Template, locale: str) -> Template:
    """Attach a long-lived ``cds_lang`` cookie to ``template``."""
    template.cookies = [
        Cookie(
            key=LANGUAGE_COOKIE,
            value=locale,
            path="/",
            max_age=60 * 60 * 24 * 365,
            httponly=False,
            samesite="lax",
        )
    ]
    return template


@get("/", name="index")
async def index(request: Request) -> Template:
    locale = _resolve_locale(request)
    scenarios = list(get_scenarios(locale).values())
    template = Template(
        template_name="index.html",
        context={
            "scenarios": scenarios,
            **_scenario_context(scenarios[0], locale),
        },
    )
    return _persist_locale(template, locale)


@get("/scenarios/{scenario_id:str}", name="scenario_panel")
async def scenario_panel(scenario_id: str, request: Request) -> Template:
    locale = _resolve_locale(request)
    scenario = _get_scenario(scenario_id, locale)
    template = Template(
        template_name="_scenario_panel.html",
        context=_scenario_context(scenario, locale),
    )
    return _persist_locale(template, locale)


@post("/scenarios/{scenario_id:str}/verify", name="verify_scenario")
async def verify_scenario(scenario_id: str, request: Request) -> Template:
    locale = _resolve_locale(request)
    scenario = _get_scenario(scenario_id, locale)
    result = _run_lean(scenario)
    template = Template(
        template_name="_verification_result.html",
        context={
            "scenario": scenario,
            "result": result,
            "lang": locale,
            "t": get_ui_strings(locale),
        },
    )
    return _persist_locale(template, locale)


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
