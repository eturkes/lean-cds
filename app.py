"""Litestar app + Lean subprocess wrapper. Bilingual UI (JA default). ``/verify`` invokes ``lean`` on a static whitelisted scenario file; no user input is ever interpolated into Lean source. At import, each locale's ``MedicalKnowledge.lean`` is precompiled to ``.olean`` so per-request verification is a single fast ``lean`` invocation."""

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
    Scenario,
    get_scenarios,
    knowledge_base_file,
)

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"


def _resolve_lean_binary() -> str:
    """Project-local ``./.elan/bin/lean`` if present, else ``shutil.which("lean")``."""
    # Project-local elan is off PATH by default; pin ELAN_HOME so spawned
    # subprocesses resolve toolchains against the same isolated tree.
    project_local_root = BASE_DIR / ".elan"
    project_local = project_local_root / "bin" / "lean"
    if project_local.is_file() and os.access(project_local, os.X_OK):
        os.environ.setdefault("ELAN_HOME", str(project_local_root))
        return str(project_local)
    return shutil.which("lean") or "lean"


LEAN_BINARY = _resolve_lean_binary()
LEAN_TIMEOUT_SECONDS = 60


def _lean_version() -> str:
    """Full ``lean --version`` line (incl. build commit) identifying the active toolchain.

    Oleans are locked to this exact build; a change invalidates cached ``.olean``
    artifacts. Empty string if lean is unavailable — the
    missing-compiler error then surfaces downstream at compile time."""
    try:
        completed = subprocess.run(
            [LEAN_BINARY, "--version"],
            capture_output=True,
            text=True,
            timeout=LEAN_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return completed.stdout.strip() if completed.returncode == 0 else ""


LEAN_VERSION = _lean_version()

_LEXER = Lean4Lexer()
_FORMATTER = HtmlFormatter(nowrap=False, cssclass="lean-code", noclasses=False)

def _highlight_lean(code: str, locale: str) -> str:
    """Pygments-highlight Lean source with per-line ``data-lean-tip`` attrs (locale-aware vocab)."""
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
    """Compile locale's ``MedicalKnowledge.lean`` to ``.olean`` if stale; return ``None`` on success or an error string.

    Stale := source newer than the artifacts (mtime) **or** the artifacts were
    built against a different Lean toolchain than the active one (``.olean.stamp``
    mismatch). The toolchain check auto-heals the "incompatible header" class:
    oleans are toolchain-locked, so a floated ``stable``
    channel silently invalidates mtime-fresh caches. When the live version is
    undeterminable (lean missing), fall back to mtime-only so a transient outage
    does not force a doomed recompile."""
    src = knowledge_base_file(locale)
    locale_dir = src.parent
    olean_path = locale_dir / f"{KNOWLEDGE_BASE_MODULE}.olean"
    ilean_path = locale_dir / f"{KNOWLEDGE_BASE_MODULE}.ilean"
    stamp_path = locale_dir / f"{KNOWLEDGE_BASE_MODULE}.olean.stamp"
    src_mtime = src.stat().st_mtime
    artifacts_fresh = (
        olean_path.exists()
        and olean_path.stat().st_mtime >= src_mtime
        and ilean_path.exists()
        and ilean_path.stat().st_mtime >= src_mtime
    )
    toolchain_ok = LEAN_VERSION == "" or (
        stamp_path.exists()
        and stamp_path.read_text(encoding="utf-8").strip() == LEAN_VERSION
    )
    if artifacts_fresh and toolchain_ok:
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
    if LEAN_VERSION:
        stamp_path.write_text(LEAN_VERSION, encoding="utf-8")
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
    """Parse axiom list from ``#print axioms`` output. Regex spans newlines (Lean wraps the bracketed list)."""
    match = _AXIOMS_RE.search(stdout)
    if match is None:
        return ()
    raw = match.group(1)
    parts = [chunk.strip() for chunk in raw.split(",")]
    return tuple(p for p in parts if p)


def _classify(
    exit_code: int, stdout: str, stderr: str, axioms: tuple[str, ...]
) -> Verdict:
    """Map Lean compiler outcome → ``Verdict`` (CollisionVerified|ProofUnsound|CompilerError)."""
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
    """Invoke ``lean`` on the scenario's static file. ``cwd`` and ``LEAN_PATH`` set to ``lean/<locale>/`` so ``import MedicalKnowledge`` resolves to the locale's precompiled ``.olean``."""
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
    """Locale order: ``?lang=`` query → ``cds_lang`` cookie → JA default. Query wins so deep links override prior cookie."""
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
