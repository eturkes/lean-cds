# Lessons Log

Append-only postmortems. Newest on top. **Grep here before making non-obvious choices** to avoid repeating past mistakes.

Format per entry:
```
## [LSN-NNN] YYYY-MM-DD — One-line summary

**What happened**: Concrete description. Include `file:line` where relevant.
**Root cause**: Why it occurred. Wrong assumption? Missing test? Tooling gap? Doc gap?
**Fix**: What resolved it.
**Prevention**: The rule, check, or note that would have prevented this. If a CLAUDE.md or `.agent/ARCHITECTURE.md` update is warranted, do it and link here.
```

---

## [LSN-004] 2026-05-14 — ARCHITECTURE.md had wrong route path; uncaught for ~1 day

**What happened**: ARCHITECTURE.md "Public surfaces" table listed `POST /verify` and data-flow step 4 said the same. Actual `app.py:324` defines `@post("/scenarios/{scenario_id:str}/verify", name="verify_scenario")`. Discrepancy surfaced only during the README → ARCHITECTURE consolidation pass when both docs were diffed side-by-side. README had the correct path; ARCHITECTURE was wrong. Any agent who'd used ARCHITECTURE.md as ground truth for routing would have generated invalid links / curl commands.

**Root cause**: ARCHITECTURE.md was hand-written without a verification step against `app.py`. The route name "POST `/verify`" is a *plausible* shortening that survived undetected.

**Fix**: ARCHITECTURE.md "Public surfaces" + "Request lifecycle" sections updated to `POST /scenarios/{scenario_id}/verify` to match `app.py:324`. README absorbed into ARCHITECTURE in same pass; single source of truth eliminates this drift class for routes.

**Prevention**: When documenting routes/CLI commands/file paths/env vars in any `.agent/` file, **grep the source for the literal string** before committing. For routes specifically: `grep -n '@get\|@post' app.py` and copy verbatim. The Public-surfaces table should be regenerable from a `grep` of `app.py`; if it can't be, the doc has drifted.

---

## [LSN-003] 2026-05-14 — Don't infer purpose from filenames; confirm by reference

**What happened**: When writing ARCHITECTURE.md I labeled `artifacts/proofs/*.alethe` as "Generated proof artifacts (build output)" based on the directory name alone. User asked what to do with the folder; investigation showed `.alethe` is the cvc5/veriT SMT proof-trace format, **not** Lean output, and *nothing* in the current codebase reads, writes, or imports those files. They are remnants of an earlier SMT-based verification approach that was abandoned for the current Lean-kernel approach. ARCHITECTURE.md was actively misleading future agents.

**Root cause**: Inferred role from path + extension without grepping the codebase to confirm any code path actually produces or consumes them. Path "artifacts/proofs/" sounds plausible as build output, and `.alethe` sounds like a proof format, so the wrong story stuck.

**Fix**: Deleted `artifacts/`; removed the line from ARCHITECTURE.md.

**Prevention**: When documenting a directory's role in ARCHITECTURE.md, **grep the codebase for the directory name and a sample filename first**. If zero references, the directory is either orphaned or external-facing — say so explicitly (e.g. "orphaned, candidate for removal") rather than inventing a plausible-sounding role. The phrases "build output", "generated", "cache" should each be backed by an actual writer in the code.

---

## [LSN-002] 2026-05-14 — Stale `.olean` caches silently fail with "incompatible header" or 60s timeouts

**What happened**: First `uv run python scripts/check_scenarios.py` run hit 5/6 scenario timeouts at 60s. Initial reading suggested my docstring trims had broken the verification pipeline. Investigation showed: (a) `lean` shim reported "no default toolchain configured"; (b) when invoked with `ELAN_HOME` set, it downloaded the project's required Lean version (`v4.29.1`); (c) running scenarios then failed with `error: failed to read file './MedicalKnowledge.olean', incompatible header` because the cached `.olean`/`.ilean` files were built against an older Lean. The 60s "timeouts" were really `elan` blocking on a toolchain download for the first scenario, then a fast-failing subsequent scenarios that I had already exceeded the budget for.

**Root cause**: `.olean`/`.ilean` artifacts are version-bound. They were checked into the working tree dated May 1 (built against an older toolchain) and never refreshed when the project pinned `v4.29.1`. `_ensure_knowledge_base_compiled` only recompiles on mtime-stale source, not on toolchain mismatch.

**Fix**: `rm -f lean/{en,ja}/*.olean lean/{en,ja}/*.ilean` and re-run. Subsequent run passes all 6 in ~30s.

**Prevention**: When verification surfaces a "Lean verification exceeded the 60s time limit" on multiple scenarios, **always rule out toolchain/cache mismatch first** before suspecting Python-side regressions. A quick check: `ls -la lean/<locale>/*.olean` + `lean --version` + try one scenario by hand with `(cd lean/<locale> && LEAN_PATH=. lean ScenarioA.lean)`. If the first lean invocation triggers a download or prints "incompatible header", clear the caches.

**Possible enhancement** (for a future session): teach `_ensure_knowledge_base_compiled` to also probe a sentinel olean against the current Lean version and refresh if incompatible. Out of scope for this session.

---

## [LSN-001] 2026-05-14 — Survey agent overcounted docstring-trim potential

**What happened**: An `Explore` subagent surveyed `lean_decorate.py` and reported "22 multi-paragraph docstrings to compress" with line-range estimates implying ~400 lines could be removed. When the trim was attempted, most of the listed targets (`_tip_import`, `_tip_namespace`, …, `_compose_*`) turned out to have **no docstrings at all** — the survey was counting **function body length** (long localized return strings) as docstring length. Actual trimmable docstrings in the file totaled ~80 lines, not 400.

**Root cause**: Survey prompt asked for "multi-paragraph candidates" by line range without requiring the agent to confirm the lines were inside a `"""..."""` block. The agent inferred from function size.

**Fix**: Skipped the false targets and trimmed only the genuine docstrings (`parse_lean_contexts`, `_tactic_arg`, `_gloss_local_identifier`, `compose_group_tip`, `_find_matching_span_close`, `_parse_html_chunks`, `_wrap_groups_in_line`, `render_lean_with_tooltips`, plus all dataclass docstrings). File shed 146 lines (~8%), not 400.

**Prevention**: When delegating a survey, require the agent to **quote the first and last line of each claimed docstring** so you can verify it's actually a `"""..."""` block before acting on the list. Better: ask for a unified diff of proposed changes, not just file:line refs.

---


