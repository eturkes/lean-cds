"""Lean 4 source → syntax-highlighted HTML with per-line tooltips.

The scenario files in ``lean/`` are small and structurally predictable:
each top-level construct is an ``import``, ``namespace``, ``open``,
``end``, ``axiom``, ``theorem`` (term- or tactic-mode), or
``#print axioms``. For the Verifiable Clinical Decision Support UI to
be readable by clinicians, regulators, and engineering managers with
zero Lean / functional programming / formal verification background,
every non-obvious token on every line needs to explain what it means
*in that specific spot* — not with a generic example.

Concretely: the ``:`` inside ``axiom JohnDoe : Patient`` should read
"``JohnDoe`` is a ``Patient``", while the ``:`` inside
``theorem thiazide_indicated : Indicated JohnDoe …`` should read
"``thiazide_indicated`` is a proof of ``Indicated JohnDoe …``". The
two tooltips share a symbol but nothing else.

This module solves that by:

1. Parsing the scenario file with a tiny, purpose-built line-based
   recogniser (``parse_lean_contexts``) that maps every source line
   to the declaration that owns it.
2. Running Pygments normally to get syntax-highlighted HTML.
3. Walking that HTML one source line at a time (Pygments' Lean4Lexer
   preserves one output line per source line), and for each
   recognised token span substituting in a ``data-lean-tip``
   attribute whose value is a plain-English sentence composed from
   *this* line's declaration. The browser tooltip popover
   (``static/tooltips.js``) reads the attribute directly, so there is
   no shared JavaScript dictionary to keep in sync.
"""
from __future__ import annotations

import html as _html
import re
from dataclasses import dataclass, field
from typing import Callable, Optional

from pygments import highlight
from pygments.formatter import Formatter
from pygments.lexer import Lexer

import lean_vocab


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------


@dataclass
class LeanDecl:
    """One recognised declaration from a scenario file.

    The parser is deliberately shallow: it matches the exact line
    shapes used by ``ScenarioA/B/C.lean`` and falls back silently on
    anything it doesn't understand, leaving ``line_to_decl`` empty for
    unrecognised lines. The tip generators all accept ``None`` and
    degrade to generic text when that happens.
    """

    kind: str  # 'import' | 'namespace' | 'open' | 'end' | 'axiom' |
    # 'theorem_term' | 'theorem_tactic' | 'print_axioms'
    name: str = ""
    type_raw: str = ""  # the claim written to the right of `:`
    body_raw: str = ""  # everything written to the right of `:=`
    first_line: int = 0  # 1-indexed
    last_line: int = 0


# Group roles used by the HTML wrapper + tooltip composer.
GROUP_AXIOM_TYPE = "axiom_type"
GROUP_THEOREM_TYPE = "theorem_type"
GROUP_THEOREM_BODY = "theorem_body_term"
GROUP_TACTIC_ARG = "tactic_arg"


@dataclass
class LeanGroup:
    """One hover-as-a-phrase slice of a scenario file.

    A group is a contiguous range of source columns on a single line
    that should behave as one tooltip target: hovering any identifier
    inside the range shows the same composed plain-English reading.
    ``start_col``/``end_col`` are 0-indexed offsets into the raw source
    line (as emitted by ``source.split("\\n")``) and align with
    Pygments span boundaries for the scenario files we parse.
    """

    line_no: int
    start_col: int
    end_col: int
    role: str  # one of the GROUP_* constants above
    text: str  # the exact raw slice between start_col and end_col
    decl_name: str  # the owning declaration's name (for context)
    tactic: str = ""  # for GROUP_TACTIC_ARG, the tactic keyword


@dataclass
class FileContext:
    """What the scenario file itself tells us about its local names.

    Populated by the parser as it walks declarations top to bottom, so
    by the time the tooltip composer runs for a phrase like
    ``AHA_ACC_HTN_8_1_5 JohnDoe obs_essential_hypertension`` it knows
    which identifier is the scenario's patient, which is a chart
    observation (and what condition that observation is of), and which
    earlier theorem names have already been proved.
    """

    patient_name: Optional[str] = None
    # obs_name (e.g. 'obs_essential_hypertension')
    #   → condition predicate name (e.g. 'HasEssentialHypertension')
    observations: dict[str, str] = field(default_factory=dict)
    # theorem_name → normalised type_raw (the claim being proved)
    theorems: dict[str, str] = field(default_factory=dict)


@dataclass
class ParseResult:
    """What ``parse_lean_contexts`` returns.

    The line-indexed dictionaries are for the decorator to look up
    per-line information as it walks the Pygments HTML; the shared
    ``FileContext`` lets the tooltip composer produce sentences that
    talk about the scenario's own patient, observations, and
    previously-proved theorems rather than a universal example.
    """

    line_to_decl: dict[int, LeanDecl]
    line_to_groups: dict[int, list[LeanGroup]]
    file_context: FileContext


_RE_IMPORT = re.compile(r"^import\s+(\S+)\s*$")
_RE_NAMESPACE = re.compile(r"^namespace\s+(\S+)\s*$")
_RE_OPEN = re.compile(r"^open\s+(\S+)\s*$")
_RE_END = re.compile(r"^end\s+(\S+)\s*$")
_RE_PRINT = re.compile(r"^#print\s+axioms\s+(\S+)\s*$")
_RE_AXIOM_SINGLE = re.compile(r"^axiom\s+(\S+)\s+:\s+(.+?)\s*$")
_RE_THEOREM_SINGLE = re.compile(
    r"^theorem\s+(\S+)\s+:\s+(.+?)\s+:=\s+(.+?)\s*$"
)
_RE_THEOREM_HEADER = re.compile(r"^theorem\s+(\S+)\s+:\s*$")
_RE_STARTER = re.compile(
    r"^(import|namespace|open|end|axiom|theorem|#print)\b"
)

# Tactic line, applied to the raw line (not stripped) so m.start(4) /
# m.end(4) give the absolute column range of the tactic argument.
# Allows an optional leading `·` bullet and matches only the three
# tactic names that ever take arguments in the scenarios.
_RE_TACTIC_LINE = re.compile(
    r"^(\s*)(?:(·)\s+)?(apply|exact|unfold)\s+(.+?)\s*$"
)


def _norm(s: str) -> str:
    """Collapse runs of whitespace so aligned axiom columns read cleanly."""
    return " ".join(s.split())


def parse_lean_contexts(source: str) -> ParseResult:
    """Parse a scenario file into per-line decls, groups, and file context.

    Walks the source top to bottom with a small line-based recogniser,
    producing three things the decorator needs:

    * ``line_to_decl`` maps every recognised line to its owning
      declaration, so the single-token tooltip generators can refer
      to the surrounding name/type/body.
    * ``line_to_groups`` maps each line to the ``LeanGroup`` phrases
      that should be wrapped as unified tooltip targets — axiom type
      slices, theorem type slices, term-mode body slices, and tactic
      arguments.
    * ``file_context`` collects the scenario's own patient axiom,
      observation axioms (and the condition predicate each observes),
      and previously-proved theorem names, so the group tooltip
      composer can refer to them by meaning rather than by label.
    """
    lines = source.split("\n")
    line_to_decl: dict[int, LeanDecl] = {}
    line_to_groups: dict[int, list[LeanGroup]] = {}
    file_ctx = FileContext()

    in_block_comment = False
    i = 0

    def ln(idx: int) -> int:
        return idx + 1

    def attach(d: LeanDecl, start_idx: int, end_idx: int) -> None:
        d.first_line = ln(start_idx)
        d.last_line = ln(end_idx)
        for k in range(d.first_line, d.last_line + 1):
            line_to_decl[k] = d

    def add_group(
        line_no: int,
        start_col: int,
        end_col: int,
        role: str,
        text: str,
        decl_name: str,
        tactic: str = "",
    ) -> None:
        if start_col >= end_col or not text:
            return
        g = LeanGroup(
            line_no=line_no,
            start_col=start_col,
            end_col=end_col,
            role=role,
            text=text,
            decl_name=decl_name,
            tactic=tactic,
        )
        line_to_groups.setdefault(line_no, []).append(g)

    def maybe_record_observation(axiom_name: str, type_text: str) -> None:
        """If the axiom's type is ``HasX p`` for a known condition, remember it."""
        parts = type_text.split()
        if len(parts) >= 1:
            head = parts[0]
            entry = lean_vocab.lookup(head)
            if entry is not None and entry.role == lean_vocab.ROLE_CONDITION_PRED:
                file_ctx.observations[axiom_name] = head

    def sweep_tactic_lines(start_j: int, decl_name: str) -> int:
        """Collect tactic lines after a ``:= by`` header, emitting groups.

        Returns the index of the first line past the last tactic line.
        Each tactic line (``apply X`` / ``exact X`` / ``unfold X``,
        optionally prefixed by a ``·`` bullet) gets a
        ``GROUP_TACTIC_ARG`` over the argument's column range.
        """
        j = start_j
        while j < len(lines):
            jraw = lines[j]
            jstr = jraw.strip()
            if not jstr or not jraw.startswith((" ", "\t")):
                break
            if _RE_STARTER.match(jstr):
                break
            tm = _RE_TACTIC_LINE.match(jraw)
            if tm:
                tactic_name = tm.group(3)
                arg_text = tm.group(4).rstrip()
                add_group(
                    ln(j),
                    tm.start(4),
                    tm.start(4) + len(arg_text),
                    GROUP_TACTIC_ARG,
                    arg_text,
                    decl_name,
                    tactic=tactic_name,
                )
            j += 1
        return j

    while i < len(lines):
        raw = lines[i]
        stripped = raw.strip()
        leading_ws = len(raw) - len(raw.lstrip())

        # Skip block comments `/- … -/` and their doc variants
        # `/-- … -/` and `/-! … -/`. These never contribute to a
        # declaration, but they often span many source lines.
        if in_block_comment:
            if "-/" in raw:
                in_block_comment = False
            i += 1
            continue
        if stripped.startswith("/-"):
            if "-/" not in stripped[2:]:
                in_block_comment = True
            i += 1
            continue
        if stripped.startswith("--") or not stripped:
            i += 1
            continue

        m = _RE_IMPORT.match(stripped)
        if m:
            attach(LeanDecl(kind="import", name=m.group(1)), i, i)
            i += 1
            continue

        m = _RE_NAMESPACE.match(stripped)
        if m:
            attach(LeanDecl(kind="namespace", name=m.group(1)), i, i)
            i += 1
            continue

        m = _RE_OPEN.match(stripped)
        if m:
            attach(LeanDecl(kind="open", name=m.group(1)), i, i)
            i += 1
            continue

        m = _RE_END.match(stripped)
        if m:
            attach(LeanDecl(kind="end", name=m.group(1)), i, i)
            i += 1
            continue

        m = _RE_PRINT.match(stripped)
        if m:
            attach(LeanDecl(kind="print_axioms", name=m.group(1)), i, i)
            i += 1
            continue

        m = _RE_AXIOM_SINGLE.match(stripped)
        if m:
            name = m.group(1)
            type_text = m.group(2).rstrip()
            d = LeanDecl(
                kind="axiom",
                name=name,
                type_raw=_norm(type_text),
            )
            attach(d, i, i)
            add_group(
                ln(i),
                leading_ws + m.start(2),
                leading_ws + m.start(2) + len(type_text),
                GROUP_AXIOM_TYPE,
                type_text,
                name,
            )
            # File context: remember the scenario's patient axiom and
            # any observation axiom whose type is `HasX p`.
            if type_text == "Patient":
                file_ctx.patient_name = name
            else:
                maybe_record_observation(name, type_text)
            i += 1
            continue

        # Single-line theorem: `theorem NAME : TYPE := BODY`
        m = _RE_THEOREM_SINGLE.match(stripped)
        if m:
            name = m.group(1)
            type_text = m.group(2).rstrip()
            body_text = m.group(3).rstrip()
            is_tactic = body_text == "by" or body_text.startswith(
                ("by ", "by\t")
            )
            d = LeanDecl(
                kind="theorem_tactic" if is_tactic else "theorem_term",
                name=name,
                type_raw=_norm(type_text),
                body_raw=body_text,
            )
            # TYPE group on the header line
            add_group(
                ln(i),
                leading_ws + m.start(2),
                leading_ws + m.start(2) + len(type_text),
                GROUP_THEOREM_TYPE,
                type_text,
                name,
            )
            if is_tactic:
                j = sweep_tactic_lines(i + 1, name)
                attach(d, i, j - 1)
                file_ctx.theorems[name] = _norm(type_text)
                i = j
            else:
                # BODY group on the header line (same-line term)
                add_group(
                    ln(i),
                    leading_ws + m.start(3),
                    leading_ws + m.start(3) + len(body_text),
                    GROUP_THEOREM_BODY,
                    body_text,
                    name,
                )
                attach(d, i, i)
                file_ctx.theorems[name] = _norm(type_text)
                i += 1
            continue

        # Multi-line theorem header: `theorem NAME :` with the type
        # (and then `:=` and body) on subsequent indented lines.
        m = _RE_THEOREM_HEADER.match(stripped)
        if m:
            name = m.group(1)
            start_idx = i
            j = i + 1
            type_parts: list[str] = []
            body_raw = ""
            is_tactic = False
            # Collect the type across continuation lines, emitting a
            # GROUP_THEOREM_TYPE for the portion of each line that
            # carries type text (before any `:=`).
            while j < len(lines):
                jraw = lines[j]
                jstr = jraw.strip()
                j_lead = len(jraw) - len(jraw.lstrip())
                if not jstr or _RE_STARTER.match(jstr):
                    break
                if ":=" in jraw:
                    assign_col = jraw.index(":=")
                    type_on_line = jraw[j_lead:assign_col].rstrip()
                    if type_on_line:
                        type_parts.append(type_on_line)
                        add_group(
                            ln(j),
                            j_lead,
                            j_lead + len(type_on_line),
                            GROUP_THEOREM_TYPE,
                            type_on_line,
                            name,
                        )
                    rest = jraw[assign_col + 2:].strip()
                    if rest == "by" or rest.startswith(("by ", "by\t")):
                        is_tactic = True
                    body_raw = rest
                    j += 1
                    break
                # No `:=` on this line — the whole non-whitespace
                # suffix is type text and gets its own group.
                type_on_line = jraw[j_lead:].rstrip()
                if type_on_line:
                    type_parts.append(type_on_line)
                    add_group(
                        ln(j),
                        j_lead,
                        j_lead + len(type_on_line),
                        GROUP_THEOREM_TYPE,
                        type_on_line,
                        name,
                    )
                j += 1

            d = LeanDecl(
                kind="theorem_tactic" if is_tactic else "theorem_term",
                name=name,
                type_raw=_norm(" ".join(type_parts)),
                body_raw=body_raw,
            )

            if is_tactic:
                j = sweep_tactic_lines(j, name)
            else:
                # Term-mode: the body lives on one or more indented
                # continuation lines. Each line becomes a
                # GROUP_THEOREM_BODY so hovering any of its identifiers
                # fires the unified proof-term tooltip.
                while j < len(lines):
                    jraw = lines[j]
                    jstr = jraw.strip()
                    j_lead = len(jraw) - len(jraw.lstrip())
                    if not jstr or not jraw.startswith((" ", "\t")):
                        break
                    if _RE_STARTER.match(jstr):
                        break
                    body_on_line = jraw[j_lead:].rstrip()
                    add_group(
                        ln(j),
                        j_lead,
                        j_lead + len(body_on_line),
                        GROUP_THEOREM_BODY,
                        body_on_line,
                        name,
                    )
                    d.body_raw = (
                        _norm(d.body_raw + " " + body_on_line)
                        if d.body_raw
                        else body_on_line
                    )
                    j += 1

            attach(d, start_idx, j - 1)
            file_ctx.theorems[name] = d.type_raw
            i = j
            continue

        # Unrecognised line: advance without attaching.
        i += 1

    return ParseResult(line_to_decl, line_to_groups, file_ctx)


# ---------------------------------------------------------------------------
# Tooltip text generators
# ---------------------------------------------------------------------------
#
# Each generator takes the declaration owning the current line (or
# ``None`` if the parser didn't recognise it) and the raw source line,
# and returns a plain-text sentence describing what the token means in
# that specific spot. The caller HTML-escapes the return value before
# embedding it in the ``data-lean-tip`` attribute.


def _is_simple_type(t: str) -> bool:
    """True for single-identifier types like ``Patient``, ``Prop``, ``Type``."""
    t = t.strip()
    return bool(t) and not any(c.isspace() for c in t)


def _code(s: str) -> str:
    return f"`{s}`"


def _preview(s: str, limit: int = 72) -> str:
    s = " ".join(s.split())
    if len(s) > limit:
        s = s[: limit - 1].rstrip() + "…"
    return _code(s)


def _tactic_arg(tactic: str, source_line: str) -> str:
    """Extract the rest-of-line argument to a tactic call.

    ``· exact thiazide_indicated`` → ``thiazide_indicated``
    ``apply incompatible_modalities JohnDoe Treatment.thiazideDiuretic``
        → ``incompatible_modalities JohnDoe Treatment.thiazideDiuretic``
    """
    stripped = re.sub(r"^\s*(·\s*)?", "", source_line)
    m = re.match(rf"^{re.escape(tactic)}\b\s*(.*?)\s*$", stripped)
    return m.group(1).strip() if m else ""


def _tip_import(decl: Optional[LeanDecl], src: str) -> str:
    name = decl.name if decl else "another module"
    return (
        f"import {name} — loads {_code(name + '.lean')} so its "
        f"declarations are available here without being retyped. In this "
        f"audit {_code('MedicalKnowledge.lean')} holds the shared "
        f"vocabulary: what a {_code('Patient')} is, which treatments "
        f"exist, and every clinical-guideline axiom the scenarios rely on."
    )


def _tip_namespace(decl: Optional[LeanDecl], src: str) -> str:
    if not decl:
        return (
            "namespace — opens a named section; must be closed by a "
            "matching `end`."
        )
    return (
        f"namespace {decl.name} — opens a named section. Every "
        f"declaration in this file gets the prefix "
        f"{_code(decl.name + '.')} from the outside, so each scenario "
        f"can have its own {_code('collision_detected')} without "
        f"clashing. Must be closed by {_code('end ' + decl.name)} at the "
        f"bottom of the file."
    )


def _tip_open(decl: Optional[LeanDecl], src: str) -> str:
    if not decl:
        return (
            "open — lets you refer to names inside a namespace without "
            "the prefix."
        )
    return (
        f"open {decl.name} — lets this file refer to names inside "
        f"{_code(decl.name)} without writing the prefix every time. "
        f"With {_code('open ' + decl.name)} in effect we can write "
        f"{_code('Patient')} instead of {_code(decl.name + '.Patient')}."
    )


def _tip_end(decl: Optional[LeanDecl], src: str) -> str:
    if not decl:
        return "end — closes the surrounding namespace or section."
    return (
        f"end {decl.name} — closes the {_code('namespace ' + decl.name)} "
        f"opened earlier in this file. Everything between that "
        f"`namespace` and this `end` belonged to {_code(decl.name)}."
    )


def _tip_axiom(decl: Optional[LeanDecl], src: str) -> str:
    if decl and decl.kind == "axiom":
        if _is_simple_type(decl.type_raw):
            return (
                f"axiom {decl.name} — declares {_code(decl.name)} as a "
                f"starting fact Lean accepts without proof: a fresh "
                f"{_code(decl.type_raw)} this scenario's proofs may "
                f"refer to. Lean never tries to verify it."
            )
        return (
            f"axiom {decl.name} — declares {_code(decl.name)} as a "
            f"starting fact Lean accepts without proof: a proof of "
            f"{_code(decl.type_raw)}. In this audit every `axiom` "
            f"encodes either a published clinical guideline or a "
            f"finding from the patient's chart."
        )
    return (
        "axiom — a starting fact Lean accepts without proof. In this "
        "audit every axiom is either a published clinical guideline or "
        "a finding from the patient's chart."
    )


def _tip_theorem(decl: Optional[LeanDecl], src: str) -> str:
    if decl and decl.kind in ("theorem_term", "theorem_tactic"):
        return (
            f"theorem {decl.name} — declares {_code(decl.name)} as a "
            f"claim Lean will only accept after mechanically checking "
            f"its proof. The claim is {_code(decl.type_raw)}, and the "
            f"right-hand side of `:=` must actually prove it. Unlike an "
            f"`axiom` (taken on trust), every `theorem` is derived step "
            f"by step from the axioms and earlier checked theorems."
        )
    return (
        "theorem — a claim Lean only accepts after mechanically "
        "checking its proof."
    )


def _tip_colon(decl: Optional[LeanDecl], src: str) -> str:
    if decl and decl.kind == "axiom":
        if _is_simple_type(decl.type_raw):
            return (
                f"`:` reads as “is a”. This line declares that "
                f"{_code(decl.name)} is a {_code(decl.type_raw)}."
            )
        return (
            f"`:` reads as “is a proof of”. This line declares that "
            f"{_code(decl.name)} is a proof of {_code(decl.type_raw)} — "
            f"the claim written to the right of the colon."
        )
    if decl and decl.kind in ("theorem_term", "theorem_tactic"):
        return (
            f"`:` reads as “is a proof of”. This theorem claims that "
            f"{_code(decl.name)} is a proof of {_code(decl.type_raw)}. "
            f"The right-hand side of `:=` must actually supply that "
            f"proof before Lean will accept the theorem."
        )
    return (
        "`:` — read as “is a” or “has type”. In Lean a finished proof "
        "is itself a value, and the claim it proves is that value's type."
    )


def _tip_coloneq(decl: Optional[LeanDecl], src: str) -> str:
    if decl and decl.kind == "theorem_term":
        return (
            f"`:=` reads as “is defined as”. {_code(decl.name)} is "
            f"defined to be the proof term {_preview(decl.body_raw)}. "
            f"Lean will kernel-check that that term really does prove "
            f"{_code(decl.type_raw)}."
        )
    if decl and decl.kind == "theorem_tactic":
        return (
            f"`:=` reads as “is defined as”. {_code(decl.name)} is "
            f"defined by the `by …` tactic block that follows; the "
            f"tactics are a recipe Lean runs to construct a proof of "
            f"{_code(decl.type_raw)}."
        )
    return (
        "`:=` — “is defined as”. The name on the left becomes another "
        "way of writing the content on the right."
    )


def _tip_by(decl: Optional[LeanDecl], src: str) -> str:
    if decl and decl.kind == "theorem_tactic":
        return (
            f"by — switches into tactic mode for the proof of "
            f"{_code(decl.name)}. The indented lines below are a "
            f"step-by-step recipe Lean runs to construct a proof of "
            f"{_code(decl.type_raw)}. The block runs until the goal is "
            f"closed."
        )
    return (
        "by — switches from writing a proof directly to writing "
        "step-by-step tactics. Everything indented after `by` is a "
        "recipe for building the proof."
    )


def _tip_unfold(decl: Optional[LeanDecl], src: str) -> str:
    arg = _tactic_arg("unfold", src)
    if decl and arg:
        return (
            f"unfold {arg} — inside the proof of {_code(decl.name)}, "
            f"replace the name {_code(arg)} with its definition in the "
            f"current goal. That reveals the internal structure of "
            f"{_code(arg)} so the next tactics can act on it directly."
        )
    return (
        "unfold X — tactic: replace the name `X` with its definition "
        "here, so the structure it names becomes visible in the goal."
    )


def _tip_apply(decl: Optional[LeanDecl], src: str) -> str:
    arg = _tactic_arg("apply", src)
    if decl and arg:
        return (
            f"apply {arg} — inside the proof of {_code(decl.name)}, the "
            f"conclusion of {_code(arg)} matches the current goal, so "
            f"Lean uses {_code(arg)} and asks you to prove its "
            f"remaining premises as fresh sub-goals."
        )
    return (
        "apply L — tactic: “the conclusion of `L` matches the current "
        "goal; use `L` and let me prove its premises next.”"
    )


def _tip_exact(decl: Optional[LeanDecl], src: str) -> str:
    arg = _tactic_arg("exact", src)
    if decl and arg:
        return (
            f"exact {arg} — inside the proof of {_code(decl.name)}, the "
            f"term {_code(arg)} is exactly a proof of the current "
            f"sub-goal; Lean accepts it and closes this step."
        )
    return (
        "exact E — tactic: “the term `E` is exactly a proof of the "
        "current goal — accept it and close the step.”"
    )


def _tip_bullet(decl: Optional[LeanDecl], src: str) -> str:
    if decl and decl.kind == "theorem_tactic":
        return (
            f"`·` — focuses the next sub-goal of {_code(decl.name)}. A "
            f"previous tactic (typically `apply And.intro`) left more "
            f"than one goal open; each `·` begins a mini-proof of one "
            f"of them, keeping the branches visually separated."
        )
    return (
        "`·` — focuses the next sub-goal left open by a previous "
        "tactic; each bullet starts a mini-proof of one of the branches."
    )


def _tip_and_intro(decl: Optional[LeanDecl], src: str) -> str:
    if decl and decl.kind in ("theorem_term", "theorem_tactic"):
        return (
            f"And.intro — to prove a claim of the form “P ∧ Q” (here "
            f"that's {_code(decl.type_raw)}), you must supply a proof "
            f"of each half separately. `And.intro` is Lean's “here are "
            f"both halves” constructor; the two sub-goals it leaves "
            f"open are picked up by the two `·` bullets below."
        )
    return (
        "And.intro — to prove “P ∧ Q”, supply a proof of P and a proof "
        "of Q separately."
    )


def _tip_false(decl: Optional[LeanDecl], src: str) -> str:
    if decl and decl.kind in ("theorem_term", "theorem_tactic"):
        return (
            f"False — the proposition that is never true. The theorem "
            f"{_code(decl.name)} claims `False`, so a successful proof "
            f"of it means the axioms it depends on are mutually "
            f"impossible — exactly the contradiction this audit exists "
            f"to surface."
        )
    return (
        "False — the proposition that is never true. Proving it from a "
        "set of axioms means those axioms are mutually impossible."
    )


def _tip_absurd(decl: Optional[LeanDecl], src: str) -> str:
    if decl and decl.kind == "print_axioms" and decl.name == "absurd":
        return (
            "absurd — here, the name whose trusted-axiom list "
            "`#print axioms` is about to emit. `absurd` is the audit's "
            "final theorem, and its claim is `False`."
        )
    if (
        decl
        and decl.kind in ("theorem_term", "theorem_tactic")
        and decl.name == "absurd"
    ):
        return (
            "absurd — the audit's final theorem. Its claim is `False`, "
            "so a successful proof of it means the two encoded clinical "
            "guidelines are logically contradictory for this specific "
            "patient."
        )
    return (
        "absurd — the audit's final theorem; its claim is `False`, so "
        "its proof is the contradiction the audit exists to surface."
    )


def _tip_print_axioms(decl: Optional[LeanDecl], src: str) -> str:
    if decl and decl.kind == "print_axioms":
        return (
            f"#print axioms {decl.name} — meta-command, not part of the "
            f"proof. Asks Lean to print the exact list of axioms the "
            f"proof of {_code(decl.name)} actually depended on. The "
            f"host process reads that list to confirm no `sorry` "
            f"placeholder (which would silently invalidate the proof) "
            f"slipped in."
        )
    return (
        "#print axioms NAME — meta-command that lists every axiom the "
        "proof of NAME actually relied on."
    )


# ---------------------------------------------------------------------------
# Phrase-group tooltip composer
# ---------------------------------------------------------------------------
#
# A group tooltip has to answer "what does this multi-word phrase
# mean?" for a reader with no Lean background. The composer walks the
# phrase head-first, looks the head symbol up in the MedicalKnowledge
# vocab, and pastes its arguments into the right role-specific
# template (deontic predicate applied to a patient and a treatment,
# guideline axiom applied to a patient and an observation, etc.). For
# heads that aren't in the vocab (locally-declared theorems, chart
# observations, or the patient axiom itself) it falls back to looking
# the name up in the per-file context so the tooltip can still say
# "the earlier theorem `thiazide_indicated` (which claims …)".


def _gloss_treatment(symbol: str) -> str:
    """Plain-English noun phrase for a ``Treatment.X`` constructor."""
    entry = lean_vocab.lookup(symbol)
    if entry is not None and entry.noun:
        return entry.noun
    return f"the treatment `{symbol}`"


def _gloss_local_identifier(symbol: str, fc: FileContext) -> str:
    """Explain a name that is declared locally in the scenario file.

    Covers the scenario's patient axiom, its observation axioms, and
    any previously-proved theorem. Falls back to a code-quoted name
    when we have no idea what it refers to.
    """
    if fc.patient_name and symbol == fc.patient_name:
        return f"`{symbol}`, this scenario's patient"
    if symbol in fc.observations:
        cond_name = fc.observations[symbol]
        cond_entry = lean_vocab.lookup(cond_name)
        reads = cond_entry.reads if cond_entry else "has that condition"
        return (
            f"`{symbol}`, the axiom recording that "
            f"`{fc.patient_name or 'the patient'}` {reads}"
        )
    if symbol in fc.theorems:
        claim = fc.theorems[symbol]
        return f"the earlier theorem `{symbol}`, whose claim is `{claim}`"
    return f"`{symbol}`"


def _role_frame(role: str, decl_name: str) -> str:
    """Role-specific closing sentence for the composed group tooltip."""
    if role == GROUP_AXIOM_TYPE:
        return (
            f" Since this is the type of `axiom {decl_name}`, Lean "
            f"accepts the claim as a ground-truth finding without "
            f"asking for a proof."
        )
    if role == GROUP_THEOREM_TYPE:
        return (
            f" This is the claim that theorem `{decl_name}` is "
            f"proving; the right-hand side of `:=` has to actually "
            f"supply a proof of it."
        )
    if role == GROUP_THEOREM_BODY:
        return (
            f" This is the proof term supplied for theorem "
            f"`{decl_name}`."
        )
    if role == GROUP_TACTIC_ARG:
        return (
            f" Supplied as an argument to a tactic inside the proof "
            f"of `{decl_name}`."
        )
    return ""


def _compose_condition_pred(
    head: str,
    entry: lean_vocab.VocabEntry,
    args: list[str],
    fc: FileContext,
) -> str:
    """``HasX p`` → "``p`` has X"."""
    if len(args) == 1:
        patient = args[0]
        patient_phrase = (
            f"`{patient}`"
            if patient == fc.patient_name
            else f"`{patient}`"
        )
        return (
            f"`{head} {patient}` — the Lean proposition {patient_phrase} "
            f"{entry.reads}. `{head}` is {entry.plain} ({entry.shape})."
        )
    return f"{entry.plain}: {entry.reads}."


def _compose_deontic_pred(
    head: str,
    entry: lean_vocab.VocabEntry,
    args: list[str],
    fc: FileContext,
) -> str:
    """``Indicated p t`` → "``t`` is indicated for ``p``"."""
    if len(args) == 2:
        patient, treatment = args
        treatment_noun = _gloss_treatment(treatment)
        return (
            f"`{head} {patient} {treatment}` — the Lean proposition "
            f"that {treatment_noun} {entry.reads} `{patient}`. `{head}` "
            f"is {entry.plain} ({entry.shape})."
        )
    return f"{entry.plain}: `{head}` applied to {' and '.join(args)}."


def _compose_collision_def(
    head: str,
    entry: lean_vocab.VocabEntry,
    args: list[str],
    fc: FileContext,
) -> str:
    """``Collision p t`` → unfolds to both halves of the deontic conflict."""
    if len(args) == 2:
        patient, treatment = args
        treatment_noun = _gloss_treatment(treatment)
        return (
            f"`{head} {patient} {treatment}` — unfolds to "
            f"`Indicated {patient} {treatment} ∧ "
            f"Contraindicated {patient} {treatment}`. Reads as: "
            f"{treatment_noun} is simultaneously indicated AND "
            f"contraindicated for `{patient}` — the deontic collision "
            f"this audit exists to surface."
        )
    return f"{entry.plain}."


def _compose_guideline_axiom(
    head: str,
    entry: lean_vocab.VocabEntry,
    args: list[str],
    fc: FileContext,
) -> str:
    """``AHA_ACC_HTN_8_1_5 p obs`` → full in-context reading."""
    base = (
        f"`{head}` — {entry.plain} ({entry.source}). Its shape is "
        f"`{entry.shape}`, which reads as: {entry.reads}."
    )
    if len(args) == 2:
        patient, obs = args
        obs_gloss = _gloss_local_identifier(obs, fc)
        return (
            base
            + f" Applied here to `{patient}` and {obs_gloss}, it yields "
            f"a proof of the axiom's conclusion for `{patient}`."
        )
    return base


def _compose_global_axiom(
    head: str,
    entry: lean_vocab.VocabEntry,
    args: list[str],
    fc: FileContext,
) -> str:
    """``incompatible_modalities p t`` → plain reading with args."""
    base = (
        f"`{head}` — {entry.plain}. Its shape is `{entry.shape}`, "
        f"which reads as: {entry.reads}."
    )
    if len(args) == 2:
        patient, treatment = args
        treatment_noun = _gloss_treatment(treatment)
        return (
            base
            + f" Applied here to `{patient}` and `{treatment}` "
            f"({treatment_noun}), it yields a proof that "
            f"{treatment_noun} cannot be both indicated and "
            f"contraindicated for `{patient}`."
        )
    return base


def _compose_head_vocab(
    head: str,
    entry: lean_vocab.VocabEntry,
    args: list[str],
    fc: FileContext,
) -> str:
    """Dispatch on an in-vocab head symbol."""
    role = entry.role
    if role == lean_vocab.ROLE_PATIENT_TYPE:
        return (
            f"`{head}` — {entry.plain}. It has no constructors; each "
            f"scenario introduces a fresh patient via an `axiom`."
        )
    if role == lean_vocab.ROLE_TREATMENT_CTOR:
        return f"`{head}` — {entry.plain}, representing {entry.noun}."
    if role == lean_vocab.ROLE_PROPOSITION:
        return entry.plain + "."
    if role == lean_vocab.ROLE_CONDITION_PRED:
        return _compose_condition_pred(head, entry, args, fc)
    if role == lean_vocab.ROLE_DEONTIC_PRED:
        return _compose_deontic_pred(head, entry, args, fc)
    if role == lean_vocab.ROLE_COLLISION_DEF:
        return _compose_collision_def(head, entry, args, fc)
    if role == lean_vocab.ROLE_GUIDELINE_AXIOM:
        return _compose_guideline_axiom(head, entry, args, fc)
    if role == lean_vocab.ROLE_GLOBAL_AXIOM:
        return _compose_global_axiom(head, entry, args, fc)
    if role == lean_vocab.ROLE_AND_INTRO:
        return f"`{head}` — {entry.reads}."
    return f"`{head}` — {entry.plain}."


def _compose_head_local(
    head: str,
    args: list[str],
    fc: FileContext,
) -> str:
    """Dispatch on a head symbol declared locally in the scenario file."""
    gloss = _gloss_local_identifier(head, fc)
    if not args:
        return f"{gloss[0].upper() + gloss[1:]}."
    arg_phrases = ", ".join(f"`{a}`" for a in args)
    return f"{gloss[0].upper() + gloss[1:]}. Applied here to {arg_phrases}."


def _split_phrase(text: str) -> list[str]:
    """Split a phrase into whitespace-separated tokens (dots kept in place)."""
    return [tok for tok in text.split() if tok]


def compose_group_tip(
    group: LeanGroup, fc: FileContext, decl: Optional[LeanDecl]
) -> str:
    """Plain-English explanation for a multi-word phrase group.

    The phrase is split on whitespace, the head token drives
    role-specific composition (via the vocab table when it is a
    MedicalKnowledge symbol, or via the per-file context for
    locally-declared names), and the closing sentence frames the
    phrase's role in its owning declaration.
    """
    tokens = _split_phrase(group.text)
    if not tokens:
        return f"`{group.text}`"

    head = tokens[0]
    args = tokens[1:]
    entry = lean_vocab.lookup(head)

    if entry is not None:
        body = _compose_head_vocab(head, entry, args, fc)
    else:
        body = _compose_head_local(head, args, fc)

    # For single-symbol tactic arguments we've already explained the
    # symbol; the role frame would add nothing. For multi-word phrases
    # the role frame is the tooltip's anchor to the surrounding code.
    frame = _role_frame(group.role, group.decl_name)
    return (body + frame).strip()


_TipFn = Callable[[Optional[LeanDecl], str], str]

_TIP_DISPATCH: dict[str, _TipFn] = {
    "import": _tip_import,
    "namespace": _tip_namespace,
    "open": _tip_open,
    "end": _tip_end,
    "axiom": _tip_axiom,
    "theorem": _tip_theorem,
    "colon": _tip_colon,
    "coloneq": _tip_coloneq,
    "by": _tip_by,
    "unfold": _tip_unfold,
    "apply": _tip_apply,
    "exact": _tip_exact,
    "bullet": _tip_bullet,
    "and-intro": _tip_and_intro,
    "false": _tip_false,
    "absurd": _tip_absurd,
    "print-axioms": _tip_print_axioms,
}


# ---------------------------------------------------------------------------
# HTML decoration
# ---------------------------------------------------------------------------
#
# Each target rewrites a specific Pygments span (or span sequence) on a
# single source line into a tooltip-bearing span whose `data-lean-tip`
# attribute holds the fully-rendered, context-specific explanation for
# *this* occurrence. Ordering `:=` before `:` keeps the intent obvious
# even though Python's literal substring match wouldn't confuse them.

_TARGETS: tuple[tuple[re.Pattern[str], str, str], ...] = (
    (
        re.compile(r'<span class="kn">import</span>'),
        "import",
        '<span class="kn lean-tip" data-lean-tip="{tip}" tabindex="0">import</span>',
    ),
    (
        re.compile(r'<span class="kn">namespace</span>'),
        "namespace",
        '<span class="kn lean-tip" data-lean-tip="{tip}" tabindex="0">namespace</span>',
    ),
    (
        re.compile(r'<span class="kn">open</span>'),
        "open",
        '<span class="kn lean-tip" data-lean-tip="{tip}" tabindex="0">open</span>',
    ),
    (
        re.compile(r'<span class="kn">end</span>'),
        "end",
        '<span class="kn lean-tip" data-lean-tip="{tip}" tabindex="0">end</span>',
    ),
    (
        re.compile(r'<span class="kn">axiom</span>'),
        "axiom",
        '<span class="kn lean-tip" data-lean-tip="{tip}" tabindex="0">axiom</span>',
    ),
    (
        re.compile(r'<span class="kn">theorem</span>'),
        "theorem",
        '<span class="kn lean-tip" data-lean-tip="{tip}" tabindex="0">theorem</span>',
    ),
    (
        re.compile(r'<span class="o">:=</span>'),
        "coloneq",
        '<span class="o lean-tip" data-lean-tip="{tip}" tabindex="0">:=</span>',
    ),
    (
        re.compile(r'<span class="o">:</span>'),
        "colon",
        '<span class="o lean-tip" data-lean-tip="{tip}" tabindex="0">:</span>',
    ),
    (
        re.compile(r'<span class="k">by</span>'),
        "by",
        '<span class="k lean-tip" data-lean-tip="{tip}" tabindex="0">by</span>',
    ),
    (
        re.compile(r'<span class="n">unfold</span>'),
        "unfold",
        '<span class="n lean-tip" data-lean-tip="{tip}" tabindex="0">unfold</span>',
    ),
    (
        re.compile(r'<span class="n">apply</span>'),
        "apply",
        '<span class="n lean-tip" data-lean-tip="{tip}" tabindex="0">apply</span>',
    ),
    (
        re.compile(r'<span class="n">exact</span>'),
        "exact",
        '<span class="n lean-tip" data-lean-tip="{tip}" tabindex="0">exact</span>',
    ),
    (
        re.compile(r'<span class="bp">·</span>'),
        "bullet",
        '<span class="bp lean-tip" data-lean-tip="{tip}" tabindex="0">·</span>',
    ),
    (
        re.compile(
            r'<span class="n">And</span><span class="bp">\.</span><span class="n">intro</span>'
        ),
        "and-intro",
        '<span class="lean-tip lean-tip-compound" data-lean-tip="{tip}" '
        'tabindex="0"><span class="n">And</span><span class="bp">.</span>'
        '<span class="n">intro</span></span>',
    ),
    (
        re.compile(r'<span class="n">False</span>'),
        "false",
        '<span class="n lean-tip" data-lean-tip="{tip}" tabindex="0">False</span>',
    ),
    (
        re.compile(r'<span class="n">absurd</span>'),
        "absurd",
        '<span class="n lean-tip" data-lean-tip="{tip}" tabindex="0">absurd</span>',
    ),
    (
        re.compile(r'<span class="bp">#</span><span class="n">print</span>'),
        "print-axioms",
        '<span class="lean-tip lean-tip-compound" data-lean-tip="{tip}" '
        'tabindex="0"><span class="bp">#</span><span class="n">print</span></span>',
    ),
)


def _decorate_line(
    html_line: str, source_line: str, decl: Optional[LeanDecl]
) -> str:
    """Wrap every recognised token on a line with a context-specific tip."""
    for regex, kind, template in _TARGETS:
        tip_fn = _TIP_DISPATCH[kind]
        text = tip_fn(decl, source_line)
        escaped = _html.escape(text, quote=True)
        replacement = template.replace("{tip}", escaped)
        # Use a lambda so `re.sub` doesn't interpret backslashes in the
        # replacement string.
        html_line = regex.sub(lambda _m, r=replacement: r, html_line)
    return html_line


# ---------------------------------------------------------------------------
# Phrase-group HTML wrapping
# ---------------------------------------------------------------------------
#
# After individual-token decoration, we walk each HTML line one top-level
# ``<span>…</span>`` chunk at a time, track each chunk's visible column
# range, and wrap the chunks that cover a ``LeanGroup``'s source range
# in an outer ``<span class="lean-tip-group" …>``. Compound wrappers
# (already emitted by `_decorate_line` around `And.intro` and `#print`)
# count as a single chunk thanks to the depth-counting span walker.

_STRIP_TAGS_RE = re.compile(r"<[^>]+>")


def _find_matching_span_close(html: str, open_tag_end: int) -> int:
    """Return the index *after* the ``</span>`` matching the span opened at ``open_tag_end - 1``.

    ``open_tag_end`` is the index just past the ``>`` of the opening
    ``<span …>``. Walks forward with a depth counter so nested
    ``<span>`` elements (as in the already-wrapped compound tooltips for
    ``And.intro`` and ``#print``) are handled correctly.
    """
    depth = 1
    j = open_tag_end
    n = len(html)
    while j < n and depth > 0:
        ch = html[j]
        if ch == "<":
            if html.startswith("<span", j):
                depth += 1
                # jump past the opening tag
                gt = html.index(">", j)
                j = gt + 1
            elif html.startswith("</span>", j):
                depth -= 1
                j += len("</span>")
            else:
                # Some other tag; jump past it
                gt = html.index(">", j)
                j = gt + 1
        else:
            j += 1
    return j


def _parse_html_chunks(html_line: str) -> list[tuple[int, int, str]]:
    """Split an HTML line into ``(visible_start, visible_end, html_chunk)`` tuples.

    Each chunk is one top-level ``<span>…</span>`` element (nested
    spans for compound wrappers collapse into a single chunk). Visible
    length is computed by stripping all HTML tags — safe for Pygments
    Lean output, which never introduces ``&``, ``<``, or ``>`` entities
    because the scenarios don't contain those characters.
    """
    chunks: list[tuple[int, int, str]] = []
    visible = 0
    i = 0
    n = len(html_line)
    while i < n:
        if html_line.startswith("<span", i):
            open_end = html_line.index(">", i) + 1
            close_end = _find_matching_span_close(html_line, open_end)
            chunk_html = html_line[i:close_end]
            vis_text = _STRIP_TAGS_RE.sub("", chunk_html)
            vis_len = len(vis_text)
            chunks.append((visible, visible + vis_len, chunk_html))
            visible += vis_len
            i = close_end
        elif html_line[i] == "<":
            # Stray tag (shouldn't occur inside a Pygments body); skip.
            gt = html_line.index(">", i)
            chunks.append((visible, visible, html_line[i : gt + 1]))
            i = gt + 1
        else:
            # Bare character outside any span — treat as one visible glyph.
            chunks.append((visible, visible + 1, html_line[i]))
            visible += 1
            i += 1
    return chunks


def _wrap_groups_in_line(
    html_line: str,
    groups: list[LeanGroup],
    fc: FileContext,
    decl: Optional[LeanDecl],
) -> str:
    """Wrap the chunks covering each group's column range in a group span.

    If a group's start/end columns don't land exactly on chunk
    boundaries (which would only happen if Pygments changed how it
    tokenises an identifier the parser recognises), the line is left
    unchanged rather than producing malformed HTML.
    """
    if not groups:
        return html_line

    chunks = _parse_html_chunks(html_line)
    # Groups come out of the parser left-to-right, but be defensive.
    sorted_groups = sorted(groups, key=lambda g: (g.start_col, g.end_col))

    out: list[str] = []
    chunk_idx = 0
    g_idx = 0

    while chunk_idx < len(chunks):
        if g_idx >= len(sorted_groups):
            out.append(chunks[chunk_idx][2])
            chunk_idx += 1
            continue

        g = sorted_groups[g_idx]
        vs, ve, html = chunks[chunk_idx]

        if ve <= g.start_col or (vs == ve and vs < g.start_col):
            # Entirely before this group's range — pass through.
            out.append(html)
            chunk_idx += 1
            continue

        if vs == g.start_col:
            # Found the first chunk of a group. Locate the matching
            # end chunk whose visible-end column equals g.end_col, then
            # wrap the slice as one lean-tip-group span.
            end_idx = None
            for k in range(chunk_idx, len(chunks)):
                if chunks[k][1] == g.end_col:
                    end_idx = k
                    break
                if chunks[k][1] > g.end_col:
                    break
            if end_idx is None:
                # Couldn't align — skip this group and move on.
                out.append(html)
                chunk_idx += 1
                g_idx += 1
                continue

            tip_text = compose_group_tip(g, fc, decl)
            escaped = _html.escape(tip_text, quote=True)
            inner = "".join(c[2] for c in chunks[chunk_idx : end_idx + 1])
            out.append(
                f'<span class="lean-tip-group" data-lean-tip="{escaped}" '
                f'tabindex="0">{inner}</span>'
            )
            chunk_idx = end_idx + 1
            g_idx += 1
            continue

        # Chunk straddles or starts after the group's start column
        # without matching it — the parser's bookkeeping disagrees with
        # Pygments. Drop the group to stay safe.
        out.append(html)
        chunk_idx += 1
        if vs >= g.end_col:
            g_idx += 1

    return "".join(out)


_PRE_OPEN = '<div class="lean-code"><pre>'
_PRE_CLOSE = "</pre></div>"


def render_lean_with_tooltips(
    code: str, lexer: Lexer, formatter: Formatter
) -> str:
    """Syntax-highlight ``code`` and inject per-line tooltip attributes.

    Pygments' ``Lean4Lexer`` output preserves one HTML line per source
    line inside the ``<pre>`` block, so we split the body on ``\\n`` and
    can align HTML lines with source lines 1:1. For each line we
    first wrap recognised single tokens (``:``, ``:=``, keywords,
    tactic names, ``·``, and compound identifiers) with their
    context-aware individual tooltip, then wrap any multi-word phrase
    groups (axiom type, theorem type, theorem body term, tactic
    argument) so hovering anywhere inside the phrase shows a unified
    plain-English reading composed from the per-file vocab and the
    declaration context.
    """
    result = parse_lean_contexts(code)
    raw = highlight(code, lexer, formatter)

    if not raw.startswith(_PRE_OPEN) or _PRE_CLOSE not in raw:
        # Pygments output shape changed — fall back to the raw highlight
        # so the UI still shows something readable.
        return raw

    body_start = len(_PRE_OPEN)
    body_end = raw.rindex(_PRE_CLOSE)
    body = raw[body_start:body_end]

    src_lines = code.split("\n")
    html_lines = body.split("\n")

    decorated: list[str] = []
    for idx, line_html in enumerate(html_lines):
        line_no = idx + 1
        source_line = src_lines[idx] if idx < len(src_lines) else ""
        decl = result.line_to_decl.get(line_no)
        step1 = _decorate_line(line_html, source_line, decl)
        groups = result.line_to_groups.get(line_no, [])
        step2 = _wrap_groups_in_line(step1, groups, result.file_context, decl)
        decorated.append(step2)

    return _PRE_OPEN + "\n".join(decorated) + _PRE_CLOSE
