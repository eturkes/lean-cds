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


