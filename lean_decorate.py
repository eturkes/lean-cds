"""Parse Lean scenario files into per-line decl/group context; render Pygments HTML with per-token ``data-lean-tip`` attrs composed from that specific line's declaration. Each ``:`` or ``:=`` gets a context-specific reading (e.g. ``: Patient`` reads as "is a Patient"; ``: Indicated …`` reads as "is a proof of Indicated …"). The browser tooltip popover in ``static/tooltips.js`` reads the attribute directly — no shared JS dictionary."""
from __future__ import annotations

import html as _html
import re
from dataclasses import dataclass, field
from typing import Callable, Optional

from pygments import highlight
from pygments.formatter import Formatter
from pygments.lexer import Lexer

import lean_vocab


# Parser


@dataclass
class LeanDecl:
    """Recognised declaration. ``kind`` ∈ {import, namespace, open, end, axiom, theorem_term, theorem_tactic, print_axioms}. Parser is shallow — unrecognised lines leave ``line_to_decl`` empty; tip generators degrade to generic text."""

    kind: str
    name: str = ""
    type_raw: str = ""  # claim right of `:`
    body_raw: str = ""  # everything right of `:=`
    first_line: int = 0  # 1-indexed
    last_line: int = 0


# Group roles used by the HTML wrapper + tooltip composer.
GROUP_AXIOM_TYPE = "axiom_type"
GROUP_THEOREM_TYPE = "theorem_type"
GROUP_THEOREM_BODY = "theorem_body_term"
GROUP_TACTIC_ARG = "tactic_arg"


@dataclass
class LeanGroup:
    """Contiguous column range on one line that acts as one tooltip target. ``start_col``/``end_col`` are 0-indexed offsets aligning with Pygments span boundaries."""

    line_no: int
    start_col: int
    end_col: int
    role: str  # GROUP_* constant
    text: str  # raw slice [start_col:end_col]
    decl_name: str
    tactic: str = ""  # set when role == GROUP_TACTIC_ARG


@dataclass
class FileContext:
    """Local names the scenario file declares. Populated top-to-bottom so tooltip composer can identify which token is the patient, which is a chart observation (and of what condition), and which earlier theorems are proved."""

    patient_name: Optional[str] = None
    # obs_name → condition predicate (e.g. 'obs_essential_hypertension' → 'HasEssentialHypertension')
    observations: dict[str, str] = field(default_factory=dict)
    # theorem_name → normalised type_raw (claim being proved)
    theorems: dict[str, str] = field(default_factory=dict)


@dataclass
class ParseResult:
    """Parser output: line→decl + line→groups dicts let the decorator look up per-line context; ``file_context`` is shared so tooltips reference the file's own names rather than generic examples."""

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


def parse_lean_contexts(source: str, locale: str = "en") -> ParseResult:
    """Walk the scenario top-to-bottom; return ``line_to_decl`` (per-line owning decl), ``line_to_groups`` (axiom/theorem type slices + tactic args as one tooltip target), and ``file_context`` (patient, obs→condition map, theorem→type map). ``locale`` selects the medical vocab table for observation classification."""
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

    patient_type_symbols = set(
        lean_vocab.symbols_by_role(lean_vocab.ROLE_PATIENT_TYPE, locale)
    )

    def maybe_record_observation(axiom_name: str, type_text: str) -> None:
        """If the axiom's type is ``HasX p`` for a known condition, remember it."""
        parts = type_text.split()
        if len(parts) >= 1:
            head = parts[0]
            entry = lean_vocab.lookup(head, locale)
            if entry is not None and entry.role == lean_vocab.ROLE_CONDITION_PRED:
                file_ctx.observations[axiom_name] = head

    def sweep_tactic_lines(start_j: int, decl_name: str) -> int:
        """Collect tactic lines after ``:= by``; emit ``GROUP_TACTIC_ARG`` per arg; return index of first non-tactic line."""
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

        # Skip `/- … -/` and doc variants (`/-- … -/`, `/-! … -/`).
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
            # any observation axiom whose type is `HasX p`. The patient
            # type is locale-specific (`Patient` in en, `«患者»` in ja),
            # so consult the vocab table rather than hard-coding it.
            if type_text in patient_type_symbols:
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


# Tooltip text generators
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
    """Extract rest-of-line argument from a tactic call. E.g. ``· exact thiazide_indicated`` → ``thiazide_indicated``."""
    stripped = re.sub(r"^\s*(·\s*)?", "", source_line)
    m = re.match(rf"^{re.escape(tactic)}\b\s*(.*?)\s*$", stripped)
    return m.group(1).strip() if m else ""


def _tip_import(decl: Optional[LeanDecl], src: str, locale: str) -> str:
    if locale == "ja":
        name = decl.name if decl else "別のモジュール"
        return (
            f"import {name} ── {_code(name + '.lean')} を読み込み、"
            f"その宣言を再記述することなく利用可能にする。本監査では "
            f"{_code('MedicalKnowledge.lean')} が共有医療語彙を保持し、"
            f"{_code('Patient')} の定義、利用可能な治療、ならびに各シナリオ"
            f"が依拠する臨床ガイドライン公理をすべて含んでいる。"
        )
    name = decl.name if decl else "another module"
    return (
        f"import {name} — loads {_code(name + '.lean')} so its "
        f"declarations are available here without being retyped. In this "
        f"audit {_code('MedicalKnowledge.lean')} holds the shared "
        f"vocabulary: what a {_code('Patient')} is, which treatments "
        f"exist, and every clinical-guideline axiom the scenarios rely on."
    )


def _tip_namespace(decl: Optional[LeanDecl], src: str, locale: str) -> str:
    if locale == "ja":
        if not decl:
            return (
                "namespace ── 名前付きセクションを開く。対応する `end` で"
                "閉じる必要がある。"
            )
        return (
            f"namespace {decl.name} ── 名前付きセクションを開く。本ファイル"
            f"の各宣言は外部から {_code(decl.name + '.')} を接頭辞として"
            f"参照され、各シナリオは衝突することなく独自の "
            f"{_code('collision_detected')} を保持できる。ファイル末尾の "
            f"{_code('end ' + decl.name)} で閉じる必要がある。"
        )
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


def _tip_open(decl: Optional[LeanDecl], src: str, locale: str) -> str:
    if locale == "ja":
        if not decl:
            return (
                "open ── 接頭辞を付けずに名前空間内の名前を参照できる"
                "ようにする。"
            )
        return (
            f"open {decl.name} ── このファイル内で {_code(decl.name)} 内の"
            f"名前を接頭辞なしで参照できるようにする。"
            f"{_code('open ' + decl.name)} が有効な間、"
            f"{_code(decl.name + '.Patient')} の代わりに "
            f"{_code('Patient')} と書ける。"
        )
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


def _tip_end(decl: Optional[LeanDecl], src: str, locale: str) -> str:
    if locale == "ja":
        if not decl:
            return "end ── 直前の名前空間またはセクションを閉じる。"
        return (
            f"end {decl.name} ── このファイルで前に開かれた "
            f"{_code('namespace ' + decl.name)} を閉じる。その `namespace` "
            f"とこの `end` の間にある宣言はすべて {_code(decl.name)} に"
            f"属する。"
        )
    if not decl:
        return "end — closes the surrounding namespace or section."
    return (
        f"end {decl.name} — closes the {_code('namespace ' + decl.name)} "
        f"opened earlier in this file. Everything between that "
        f"`namespace` and this `end` belonged to {_code(decl.name)}."
    )


def _tip_axiom(decl: Optional[LeanDecl], src: str, locale: str) -> str:
    if locale == "ja":
        if decl and decl.kind == "axiom":
            if _is_simple_type(decl.type_raw):
                return (
                    f"axiom {decl.name} ── {_code(decl.name)} を、Lean が"
                    f"証明なしに受け入れる前提として宣言する：本シナリオ"
                    f"の証明が参照しうる新しい {_code(decl.type_raw)}。"
                    f"Lean は決してこれを検証しようとしない。"
                )
            return (
                f"axiom {decl.name} ── {_code(decl.name)} を、Lean が"
                f"証明なしに受け入れる前提として宣言する：すなわち "
                f"{_code(decl.type_raw)} の証明。本監査ではすべての "
                f"`axiom` が公開された臨床ガイドラインまたは患者カルテの"
                f"所見を符号化する。"
            )
        return (
            "axiom ── Lean が証明なしに受け入れる前提。本監査ではすべての"
            "公理が公開された臨床ガイドラインまたは患者カルテの所見である。"
        )
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


def _tip_theorem(decl: Optional[LeanDecl], src: str, locale: str) -> str:
    if locale == "ja":
        if decl and decl.kind in ("theorem_term", "theorem_tactic"):
            return (
                f"theorem {decl.name} ── {_code(decl.name)} を、Lean が"
                f"その証明を機械的に検査して初めて受け入れる主張として"
                f"宣言する。主張は {_code(decl.type_raw)} であり、`:=` の"
                f"右辺は実際にこれを証明しなければならない。`axiom` "
                f"（無条件に信頼される）と異なり、`theorem` は公理および"
                f"既に検査された定理から段階的に導出される。"
            )
        return (
            "theorem ── Lean がその証明を機械的に検査して初めて受け入れる"
            "主張。"
        )
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


def _tip_colon(decl: Optional[LeanDecl], src: str, locale: str) -> str:
    if locale == "ja":
        if decl and decl.kind == "axiom":
            if _is_simple_type(decl.type_raw):
                return (
                    f"`:` は「は〜である」と読む。本行は {_code(decl.name)} "
                    f"が {_code(decl.type_raw)} であることを宣言する。"
                )
            return (
                f"`:` は「〜の証明である」と読む。本行は {_code(decl.name)} "
                f"がコロンの右側に書かれた主張 {_code(decl.type_raw)} の"
                f"証明であることを宣言する。"
            )
        if decl and decl.kind in ("theorem_term", "theorem_tactic"):
            return (
                f"`:` は「〜の証明である」と読む。この定理は "
                f"{_code(decl.name)} が {_code(decl.type_raw)} の証明で"
                f"あると主張する。`:=` の右辺は Lean が定理を受け入れる前に"
                f"実際にその証明を与えなければならない。"
            )
        return (
            "`:` ── 「は〜である」あるいは「〜という型を持つ」と読む。"
            "Lean では完成した証明はそれ自体が値であり、証明される主張は"
            "その値の型である。"
        )
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


def _tip_coloneq(decl: Optional[LeanDecl], src: str, locale: str) -> str:
    if locale == "ja":
        if decl and decl.kind == "theorem_term":
            return (
                f"`:=` は「と定義する」と読む。{_code(decl.name)} は証明項 "
                f"{_preview(decl.body_raw)} と定義される。Lean はその項が"
                f"実際に {_code(decl.type_raw)} を証明することをカーネルで"
                f"検査する。"
            )
        if decl and decl.kind == "theorem_tactic":
            return (
                f"`:=` は「と定義する」と読む。{_code(decl.name)} は続く "
                f"`by …` 戦術ブロックによって定義される；戦術は Lean が "
                f"{_code(decl.type_raw)} の証明を構築するために実行する"
                f"レシピである。"
            )
        return (
            "`:=` ── 「と定義する」。左辺の名前が右辺の内容を別の表記で"
            "表すものになる。"
        )
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


def _tip_by(decl: Optional[LeanDecl], src: str, locale: str) -> str:
    if locale == "ja":
        if decl and decl.kind == "theorem_tactic":
            return (
                f"by ── {_code(decl.name)} の証明のために戦術モードへ"
                f"切り替える。下のインデント行は Lean が "
                f"{_code(decl.type_raw)} の証明を構築するために実行する"
                f"段階的なレシピである。ゴールが閉じるまでブロックは"
                f"続く。"
            )
        return (
            "by ── 直接証明を書く代わりに段階的な戦術を書くモードへ"
            "切り替える。`by` の後にインデントされたものはすべて証明を"
            "構築するレシピである。"
        )
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


def _tip_unfold(decl: Optional[LeanDecl], src: str, locale: str) -> str:
    arg = _tactic_arg("unfold", src)
    if locale == "ja":
        if decl and arg:
            return (
                f"unfold {arg} ── {_code(decl.name)} の証明内で、現在の"
                f"ゴールにある名前 {_code(arg)} をその定義で置き換える。"
                f"これにより {_code(arg)} の内部構造が露わになり、後続の"
                f"戦術が直接その構造に作用できる。"
            )
        return (
            "unfold X ── 戦術：名前 `X` をその定義でここで置き換え、"
            "それが指す構造をゴール中で可視化する。"
        )
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


def _tip_apply(decl: Optional[LeanDecl], src: str, locale: str) -> str:
    arg = _tactic_arg("apply", src)
    if locale == "ja":
        if decl and arg:
            return (
                f"apply {arg} ── {_code(decl.name)} の証明内で、"
                f"{_code(arg)} の結論が現在のゴールに一致するため、Lean は "
                f"{_code(arg)} を使用し、その残りの前提を新しい部分目標"
                f"として証明するよう求める。"
            )
        return (
            "apply L ── 戦術：「`L` の結論は現在のゴールに一致する。"
            "`L` を使い、その前提を次に証明する。」"
        )
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


def _tip_exact(decl: Optional[LeanDecl], src: str, locale: str) -> str:
    arg = _tactic_arg("exact", src)
    if locale == "ja":
        if decl and arg:
            return (
                f"exact {arg} ── {_code(decl.name)} の証明内で、項 "
                f"{_code(arg)} は現在の部分目標の証明そのものである；"
                f"Lean はこれを受け入れ、本ステップを閉じる。"
            )
        return (
            "exact E ── 戦術：「項 `E` は現在のゴールの証明そのもの ── "
            "受け入れてステップを閉じる。」"
        )
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


def _tip_bullet(decl: Optional[LeanDecl], src: str, locale: str) -> str:
    if locale == "ja":
        if decl and decl.kind == "theorem_tactic":
            return (
                f"`·` ── {_code(decl.name)} の次の部分目標に焦点を移す。"
                f"直前の戦術（通常 `apply And.intro`）が複数のゴールを"
                f"残しており、各 `·` がそのうち一つのミニ証明を開始し、"
                f"分岐を視覚的に分離する。"
            )
        return (
            "`·` ── 直前の戦術が残した次の部分目標に焦点を移す；"
            "各箇条書きが分岐の一つのミニ証明を開始する。"
        )
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


def _tip_and_intro(decl: Optional[LeanDecl], src: str, locale: str) -> str:
    if locale == "ja":
        if decl and decl.kind in ("theorem_term", "theorem_tactic"):
            return (
                f"And.intro ── 「P ∧ Q」の形の主張（ここでは "
                f"{_code(decl.type_raw)}）を証明するには、両半分の"
                f"証明をそれぞれ与えなければならない。`And.intro` は "
                f"Lean の「両半分はこれだ」という構成子であり、開いた"
                f"まま残る二つの部分目標は下の二つの `·` 箇条書きで"
                f"処理される。"
            )
        return (
            "And.intro ── 「P ∧ Q」を証明するには、P の証明と Q の"
            "証明をそれぞれ与える。"
        )
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


def _tip_false(decl: Optional[LeanDecl], src: str, locale: str) -> str:
    if locale == "ja":
        if decl and decl.kind in ("theorem_term", "theorem_tactic"):
            return (
                f"False ── 決して真にならない命題。定理 {_code(decl.name)} "
                f"は `False` を主張するため、これが証明に成功するという"
                f"ことは、依拠する公理が互いに不可能であることを意味する "
                f"── 本監査が暴き出すために存在する矛盾そのものである。"
            )
        return (
            "False ── 決して真にならない命題。ある公理集合からこれが"
            "証明されるということは、それらの公理が互いに不可能で"
            "あることを意味する。"
        )
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


def _tip_absurd(decl: Optional[LeanDecl], src: str, locale: str) -> str:
    if locale == "ja":
        if decl and decl.kind == "print_axioms" and decl.name == "absurd":
            return (
                "absurd ── ここでは、`#print axioms` がこれから出力する"
                "信頼公理リストの対象となる名前。`absurd` は本監査の最終"
                "定理であり、その主張は `False` である。"
            )
        if (
            decl
            and decl.kind in ("theorem_term", "theorem_tactic")
            and decl.name == "absurd"
        ):
            return (
                "absurd ── 本監査の最終定理。その主張は `False` で"
                "あるため、これが証明に成功するということは、符号化"
                "された二つの臨床ガイドラインがこの特定の患者に対して"
                "論理的に矛盾していることを意味する。"
            )
        return (
            "absurd ── 本監査の最終定理；その主張は `False` であり、"
            "その証明こそが本監査が暴き出すために存在する矛盾である。"
        )
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


def _tip_print_axioms(decl: Optional[LeanDecl], src: str, locale: str) -> str:
    if locale == "ja":
        if decl and decl.kind == "print_axioms":
            return (
                f"#print axioms {decl.name} ── 証明の一部ではないメタ"
                f"コマンド。{_code(decl.name)} の証明が実際に依拠した"
                f"公理の正確なリストを Lean に出力させる。ホストプロセスは"
                f"このリストを読み取り、（証明を密かに無効化する）`sorry` "
                f"仮置きが紛れ込んでいないことを確認する。"
            )
        return (
            "#print axioms NAME ── NAME の証明が実際に依拠したすべての"
            "公理を列挙するメタコマンド。"
        )
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


# Phrase-group tooltip composer
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


def _gloss_treatment(symbol: str, locale: str) -> str:
    """Locale-aware noun phrase for a ``Treatment.X`` constructor."""
    entry = lean_vocab.lookup(symbol, locale)
    if entry is not None and entry.noun:
        return entry.noun
    if locale == "ja":
        return f"治療 `{symbol}`"
    return f"the treatment `{symbol}`"


def _gloss_local_identifier(
    symbol: str, fc: FileContext, locale: str
) -> str:
    """Explain a locally-declared name (patient, observation, or previously-proved theorem). Falls back to code-quoted name when unknown."""
    if locale == "ja":
        if fc.patient_name and symbol == fc.patient_name:
            return f"本シナリオの患者 `{symbol}`"
        if symbol in fc.observations:
            cond_name = fc.observations[symbol]
            cond_entry = lean_vocab.lookup(cond_name, locale)
            reads = cond_entry.reads if cond_entry else "その病態を有する"
            return (
                f"`{fc.patient_name or '患者'}` が{reads}ことを"
                f"記録した公理 `{symbol}`"
            )
        if symbol in fc.theorems:
            claim = fc.theorems[symbol]
            return f"主張が `{claim}` である既出の定理 `{symbol}`"
        return f"`{symbol}`"
    if fc.patient_name and symbol == fc.patient_name:
        return f"`{symbol}`, this scenario's patient"
    if symbol in fc.observations:
        cond_name = fc.observations[symbol]
        cond_entry = lean_vocab.lookup(cond_name, locale)
        reads = cond_entry.reads if cond_entry else "has that condition"
        return (
            f"`{symbol}`, the axiom recording that "
            f"`{fc.patient_name or 'the patient'}` {reads}"
        )
    if symbol in fc.theorems:
        claim = fc.theorems[symbol]
        return f"the earlier theorem `{symbol}`, whose claim is `{claim}`"
    return f"`{symbol}`"


def _role_frame(role: str, decl_name: str, locale: str) -> str:
    """Role-specific closing sentence for the composed group tooltip."""
    if locale == "ja":
        if role == GROUP_AXIOM_TYPE:
            return (
                f" これは `axiom {decl_name}` の型であるため、Lean は"
                f"証明を求めることなく本主張を真理として受け入れる。"
            )
        if role == GROUP_THEOREM_TYPE:
            return (
                f" これは定理 `{decl_name}` が証明している主張であり、"
                f"`:=` の右辺は実際にその証明を与えなければならない。"
            )
        if role == GROUP_THEOREM_BODY:
            return f" これは定理 `{decl_name}` に与えられた証明項である。"
        if role == GROUP_TACTIC_ARG:
            return f" `{decl_name}` の証明内で戦術の引数として与えられる。"
        return ""
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
    locale: str,
) -> str:
    """``HasX p`` → "``p`` has X"."""
    if locale == "ja":
        if len(args) == 1:
            patient = args[0]
            return (
                f"`{head} {patient}` ── `{patient}` が{entry.reads}という"
                f"Lean 命題。`{head}` は{entry.plain}（{entry.shape}）。"
            )
        return f"{entry.plain}：{entry.reads}。"
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
    locale: str,
) -> str:
    """``Indicated p t`` → "``t`` is indicated for ``p``"."""
    if locale == "ja":
        if len(args) == 2:
            patient, treatment = args
            treatment_noun = _gloss_treatment(treatment, locale)
            return (
                f"`{head} {patient} {treatment}` ── {treatment_noun}が "
                f"`{patient}`{entry.reads}という Lean 命題。`{head}` は"
                f"{entry.plain}（{entry.shape}）。"
            )
        return f"{entry.plain}：`{head}` を {' と '.join(args)} に適用。"
    if len(args) == 2:
        patient, treatment = args
        treatment_noun = _gloss_treatment(treatment, locale)
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
    locale: str,
) -> str:
    """``Collision p t`` → unfolds to both halves of the deontic conflict."""
    deontic = lean_vocab.symbols_by_role(
        lean_vocab.ROLE_DEONTIC_PRED, locale
    )
    indicated = deontic[0] if len(deontic) > 0 else "Indicated"
    contraindicated = deontic[1] if len(deontic) > 1 else "Contraindicated"
    if locale == "ja":
        if len(args) == 2:
            patient, treatment = args
            treatment_noun = _gloss_treatment(treatment, locale)
            return (
                f"`{head} {patient} {treatment}` ── "
                f"`{indicated} {patient} {treatment} ∧ "
                f"{contraindicated} {patient} {treatment}` に展開される。"
                f"読み方：{treatment_noun}が `{patient}` に対して同時に"
                f"適応かつ禁忌である ── 本監査が暴き出すために存在する"
                f"義務論的衝突。"
            )
        return f"{entry.plain}。"
    if len(args) == 2:
        patient, treatment = args
        treatment_noun = _gloss_treatment(treatment, locale)
        return (
            f"`{head} {patient} {treatment}` — unfolds to "
            f"`{indicated} {patient} {treatment} ∧ "
            f"{contraindicated} {patient} {treatment}`. Reads as: "
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
    locale: str,
) -> str:
    """``JSH2019_Ch5_FirstLine p obs`` → full in-context reading."""
    if locale == "ja":
        base = (
            f"`{head}` ── {entry.plain}（{entry.source}）。型は "
            f"`{entry.shape}` であり、読み方は：{entry.reads}。"
        )
        if len(args) == 2:
            patient, obs = args
            obs_gloss = _gloss_local_identifier(obs, fc, locale)
            return (
                base
                + f" ここでは `{patient}` と{obs_gloss}に適用され、"
                f"`{patient}` に対する公理の結論の証明を生成する。"
            )
        return base
    base = (
        f"`{head}` — {entry.plain} ({entry.source}). Its shape is "
        f"`{entry.shape}`, which reads as: {entry.reads}."
    )
    if len(args) == 2:
        patient, obs = args
        obs_gloss = _gloss_local_identifier(obs, fc, locale)
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
    locale: str,
) -> str:
    """``incompatible_modalities p t`` → plain reading with args."""
    if locale == "ja":
        base = (
            f"`{head}` ── {entry.plain}。型は `{entry.shape}` であり、"
            f"読み方は：{entry.reads}。"
        )
        if len(args) == 2:
            patient, treatment = args
            treatment_noun = _gloss_treatment(treatment, locale)
            return (
                base
                + f" ここでは `{patient}` と `{treatment}`"
                f"（{treatment_noun}）に適用され、{treatment_noun}が "
                f"`{patient}` に対して同時に適応かつ禁忌となることが"
                f"あり得ないことの証明を生成する。"
            )
        return base
    base = (
        f"`{head}` — {entry.plain}. Its shape is `{entry.shape}`, "
        f"which reads as: {entry.reads}."
    )
    if len(args) == 2:
        patient, treatment = args
        treatment_noun = _gloss_treatment(treatment, locale)
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
    locale: str,
) -> str:
    """Dispatch on an in-vocab head symbol."""
    role = entry.role
    if locale == "ja":
        if role == lean_vocab.ROLE_PATIENT_TYPE:
            return (
                f"`{head}` ── {entry.plain}。コンストラクタを持たず、"
                f"各シナリオは `axiom` を介して新たな患者を導入する。"
            )
        if role == lean_vocab.ROLE_TREATMENT_CTOR:
            return f"`{head}` ── {entry.plain}（{entry.noun}を表す）。"
        if role == lean_vocab.ROLE_PROPOSITION:
            return entry.plain + "。"
        if role == lean_vocab.ROLE_CONDITION_PRED:
            return _compose_condition_pred(head, entry, args, fc, locale)
        if role == lean_vocab.ROLE_DEONTIC_PRED:
            return _compose_deontic_pred(head, entry, args, fc, locale)
        if role == lean_vocab.ROLE_COLLISION_DEF:
            return _compose_collision_def(head, entry, args, fc, locale)
        if role == lean_vocab.ROLE_GUIDELINE_AXIOM:
            return _compose_guideline_axiom(head, entry, args, fc, locale)
        if role == lean_vocab.ROLE_GLOBAL_AXIOM:
            return _compose_global_axiom(head, entry, args, fc, locale)
        if role == lean_vocab.ROLE_AND_INTRO:
            return f"`{head}` ── {entry.reads}。"
        return f"`{head}` ── {entry.plain}。"
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
        return _compose_condition_pred(head, entry, args, fc, locale)
    if role == lean_vocab.ROLE_DEONTIC_PRED:
        return _compose_deontic_pred(head, entry, args, fc, locale)
    if role == lean_vocab.ROLE_COLLISION_DEF:
        return _compose_collision_def(head, entry, args, fc, locale)
    if role == lean_vocab.ROLE_GUIDELINE_AXIOM:
        return _compose_guideline_axiom(head, entry, args, fc, locale)
    if role == lean_vocab.ROLE_GLOBAL_AXIOM:
        return _compose_global_axiom(head, entry, args, fc, locale)
    if role == lean_vocab.ROLE_AND_INTRO:
        return f"`{head}` — {entry.reads}."
    return f"`{head}` — {entry.plain}."


def _compose_head_local(
    head: str,
    args: list[str],
    fc: FileContext,
    locale: str,
) -> str:
    """Dispatch on a head symbol declared locally in the scenario file."""
    gloss = _gloss_local_identifier(head, fc, locale)
    if locale == "ja":
        if not args:
            return f"{gloss}。"
        arg_phrases = "、".join(f"`{a}`" for a in args)
        return f"{gloss}。ここでは {arg_phrases} に適用される。"
    if not args:
        return f"{gloss[0].upper() + gloss[1:]}."
    arg_phrases = ", ".join(f"`{a}`" for a in args)
    return f"{gloss[0].upper() + gloss[1:]}. Applied here to {arg_phrases}."


def _split_phrase(text: str) -> list[str]:
    """Split a phrase into whitespace-separated tokens (dots kept in place)."""
    return [tok for tok in text.split() if tok]


def compose_group_tip(
    group: LeanGroup,
    fc: FileContext,
    decl: Optional[LeanDecl],
    locale: str,
) -> str:
    """Compose plain-language reading for a multi-word phrase. Head token dispatches: vocab table for in-vocab symbols, file context for local names. Closing sentence frames the phrase's role in its owning decl."""
    tokens = _split_phrase(group.text)
    if not tokens:
        return f"`{group.text}`"

    head = tokens[0]
    args = tokens[1:]
    entry = lean_vocab.lookup(head, locale)

    if entry is not None:
        body = _compose_head_vocab(head, entry, args, fc, locale)
    else:
        body = _compose_head_local(head, args, fc, locale)

    # For single-symbol tactic arguments we've already explained the
    # symbol; the role frame would add nothing. For multi-word phrases
    # the role frame is the tooltip's anchor to the surrounding code.
    frame = _role_frame(group.role, group.decl_name, locale)
    return (body + frame).strip()


_TipFn = Callable[[Optional[LeanDecl], str, str], str]

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


# HTML decoration
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
    html_line: str,
    source_line: str,
    decl: Optional[LeanDecl],
    locale: str,
) -> str:
    """Wrap every recognised token on a line with a context-specific tip."""
    for regex, kind, template in _TARGETS:
        tip_fn = _TIP_DISPATCH[kind]
        text = tip_fn(decl, source_line, locale)
        escaped = _html.escape(text, quote=True)
        replacement = template.replace("{tip}", escaped)
        # Use a lambda so `re.sub` doesn't interpret backslashes in the
        # replacement string.
        html_line = regex.sub(lambda _m, r=replacement: r, html_line)
    return html_line


# Phrase-group HTML wrapping
#
# After individual-token decoration, we walk each HTML line one top-level
# ``<span>…</span>`` chunk at a time, track each chunk's visible column
# range, and wrap the chunks that cover a ``LeanGroup``'s source range
# in an outer ``<span class="lean-tip-group" …>``. Compound wrappers
# (already emitted by `_decorate_line` around `And.intro` and `#print`)
# count as a single chunk thanks to the depth-counting span walker.

_STRIP_TAGS_RE = re.compile(r"<[^>]+>")


def _find_matching_span_close(html: str, open_tag_end: int) -> int:
    """Index after the ``</span>`` matching the span opened at ``open_tag_end - 1``. Depth-counted to handle nested spans (compound wrappers for ``And.intro``, ``#print``)."""
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
    """Tokenize an HTML line into ``(visible_start, visible_end, html_chunk)`` tuples. Each chunk is one top-level ``<span>…</span>`` (nested spans collapse). Visible length = chunk minus tags; safe because Pygments Lean output has no `&`/`<`/`>` entities."""
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
    locale: str,
) -> str:
    """Wrap chunks covering each group's column range in a group span. If a group's start/end don't align to chunk boundaries (would mean Pygments retokenised an identifier the parser recognises), leave the line unchanged rather than produce malformed HTML."""
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

            tip_text = compose_group_tip(g, fc, decl, locale)
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
    code: str,
    lexer: Lexer,
    formatter: Formatter,
    locale: str = "en",
) -> str:
    """Highlight ``code`` and inject per-line tooltip attributes. Pygments Lean4Lexer preserves one HTML line per source line, so we align 1:1. Pass 1 wraps single tokens (``:``, ``:=``, keywords, tactics, ``·``, compound idents) with context-aware tooltips; pass 2 wraps multi-word phrase groups (axiom type, theorem type, term body, tactic arg) with unified readings. ``locale`` selects vocab table + tooltip-prose templates."""
    result = parse_lean_contexts(code, locale)
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
        step1 = _decorate_line(line_html, source_line, decl, locale)
        groups = result.line_to_groups.get(line_no, [])
        step2 = _wrap_groups_in_line(
            step1, groups, result.file_context, decl, locale
        )
        decorated.append(step2)

    return _PRE_OPEN + "\n".join(decorated) + _PRE_CLOSE
