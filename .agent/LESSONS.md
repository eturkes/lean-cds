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

## [LSN-007] 2026-06-16 — Lean verify *hangs* (not "incompatible header") when ELAN_HOME points to an elan home missing the active toolchain; an empty version silently disables the [ARC-009] auto-heal

**What happened**: Running the dash work's acceptance gate, `check_scenarios.py` timed out (60s) on all 6 scenarios, and the live `/verify` feature was equally broken — yet the edits touched no Lean source. Diagnosis: `stable` floated v4.30.0 → v4.31.0; `~/.elan` has v4.31.0 but the project-local `./.elan/toolchains/` does not (only a stale `…v4.31.lock` from an interrupted install). `app.py:50` pins `ELAN_HOME=./.elan`, so every `lean` call resolves `stable`→v4.31.0, finds it absent, and **blocks trying to install it** → hang. `_lean_version()` (no `env=`, inherits the pinned ELAN_HOME) times out → `LEAN_VERSION=""`. Then `_ensure_knowledge_base_compiled`'s `toolchain_ok = LEAN_VERSION == "" or stamp == LEAN_VERSION` short-circuits **True**, so the [ARC-009]/[DEC-013] stamp auto-heal is silently skipped and the stale 4.30.0 oleans persist.

**Root cause**: Two compounding faults. (1) `./.elan` never finished installing the toolchain its `stable` default now points to, so `ELAN_HOME=./.elan lean` blocks on an install attempt instead of running. (2) `_lean_version` returning `""` is treated by the cache logic as "toolchain fine" (**fail-open**): a version-probe failure disables the very check meant to catch toolchain drift, and masks the hang behind a generic 60s verify timeout.

**Fix**: User is restoring v4.31.0 into `./.elan` (copy from `~/.elan` or `elan toolchain install stable`, clear the stale `.lock`); ARC-009 then auto-rebuilds the oleans. `MedicalKnowledge.lean` compiles clean+fast under 4.31 (no source incompatibility). The dash edits ([DEC-020]) were committed independently (import-verified, scan-clean).

**Prevention**: Extends [LSN-002]/[LSN-005] with a new failure mode — a 60s verify *timeout* (vs a fast "incompatible header") points at `ELAN_HOME` resolving to an elan home **missing** the active/`stable` toolchain (it blocks on install), not merely a stale olean. Quick probe: compare `ELAN_HOME=$PWD/.elan ./.elan/bin/elan toolchain list` against the active `lean --version`. Worthwhile code follow-up: make `_lean_version`/`_ensure_knowledge_base_compiled` **fail safe** — an undeterminable version should surface the probe failure (or force a bounded recompile), never silently mark the cache toolchain-ok.

---

## [LSN-006] 2026-06-16 — Auditing a character class: literal-glyph grep undercounts (escapes + look-alike codepoints)

**What happened**: Tasked with removing em/en dashes from human-facing UI text, my first grep searched only the literal `—`/`–`/`―` glyphs. It reported ~27 sites and characterized the JA dashes as "wave dash + horizontal bar" — and I asked the user a scoping question on that basis. A fuller scan found **62** human-facing dash-sites: EN guideline bodies in `scenarios.py` encode dashes as Python `—`/`–` **escape sequences** (six ASCII chars in the file, invisible to a glyph grep), and the dominant JA "dash" was `U+2500` **BOX DRAWINGS LIGHT HORIZONTAL** doubled (`──`) — a table-drawing glyph, not a typographic dash.

**Root cause**: Searched for the rendered glyph, not all of its source representations. `\uXXXX` escapes and look-alike glyphs (box-drawing vs em-dash) render identically but are different bytes; `grep '[—–]'` sees neither.

**Fix**: Re-scanned with a Python scanner covering (a) the full dash-family codepoint set incl. `U+2500/2501/301C/FF5E`, (b) `\\u(2013|2014|2015|…)` escape sequences, (c) per-occurrence codepoint + context. Re-confirmed the corrected inventory with the user before editing JA.

**Prevention**: When auditing/replacing a character class across source, enumerate **representations**, not just the target glyph: literal char, `\uXXXX`/`\xXX` escapes, HTML entities, and visually-identical look-alikes (confirm with `ord()`). Generalises [LSN-001] (survey accuracy) and [LSN-004] (grep the literal string). Make bulk string edits assertion-guarded: assert each occurrence count before replacing and abort-all on mismatch (two-pass), so a mis-specified pattern fails loudly instead of silently corrupting or missing.

---

## [LSN-005] 2026-06-04 — Relocating the project dir silently breaks gitignored local tooling (`.venv`, `.elan/env`); `git status` stays clean

**What happened**: Project moved `…/Documents/pro/lean-cds` → `…/Projects/lean-cds` (same `/run/host/home/eturkes` root — a plain rename, not a container/host split). `git status` was clean, so nothing flagged breakage. Three local artifacts still carried the **old absolute path**: (1) every `.venv/bin/*` console-script shebang + all `activate*` scripts (`#!/…/Documents/pro/…/.venv/bin/python`) — direct `.venv/bin/uvicorn`/`litestar` and `source .venv/bin/activate` broken; (2) `.elan/env`'s `export PATH="…/Documents/pro/…/.elan/bin:$PATH"`; (3) `lean/{en,ja}/*.olean` were *additionally* stale — built v4.29.1, but `stable` had floated to v4.30.0, a re-occurrence of [LSN-002]. **`uv run …` masks (1)**: it re-resolves the venv and ignores the dead shebang, so `uv run python -c "import app"` "works" while the activate script / direct entry-points fail — a partial green that hides the rot.

**Root cause**: venv console scripts and elan's `env` bake the absolute project path at creation time; relocation invalidates them. All three artifacts are gitignored (correctly — non-portable, reproducible), so `git status` structurally **cannot** surface the drift. `app.py` resolves its own paths from `__file__` and pins `ELAN_HOME=BASE_DIR/.elan`, so the *app* relocates cleanly — only the prebuilt local tooling is path-bound.

**Fix**: `rm -rf .venv && uv sync` (regenerates shebangs/activate from `uv.lock`); repoint `.elan/env` PATH to the new root; `rm -f lean/{en,ja}/*.{olean,ilean}` then let app import recompile against the current toolchain ([LSN-002]). Verified: `import app` → KB errors `{ja: None, en: None}`; `check_scenarios.py` 6/6 PASS against v4.30.0.

**Prevention**: After any **clone or directory move**, treat a clean `git status` as meaningless for runtime health — the artifacts that break on move are all gitignored. Run the post-move repair: rebuild venv + repoint `.elan/env` + clear oleans, then `uv run python scripts/check_scenarios.py`. Fast staleness probe: `grep -rIl <old-or-any-foreign-abs-path> .venv .elan` (zero hits = clean); or assert `head -1 .venv/bin/uvicorn` and the `.elan/env` PATH both contain `$PWD`. **Enhancement implemented** ([DEC-013], 2026-06-04): the olean half now auto-heals via a toolchain version stamp in `_ensure_knowledge_base_compiled` — relocation/float no longer needs a manual olean clear. The `.venv` + `.elan/env` halves still require the manual repair above; a `scripts/repair_after_move.sh` one-shot remains an option if it recurs.

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

**Enhancement implemented** ([DEC-013], 2026-06-04): `_ensure_knowledge_base_compiled` now recompiles on toolchain change via a `MedicalKnowledge.olean.stamp` version stamp, so this incompatible-header class auto-heals at import — a manual cache-clear is the fallback, no longer the primary remedy.

---

## [LSN-001] 2026-05-14 — Survey agent overcounted docstring-trim potential

**What happened**: An `Explore` subagent surveyed `lean_decorate.py` and reported "22 multi-paragraph docstrings to compress" with line-range estimates implying ~400 lines could be removed. When the trim was attempted, most of the listed targets (`_tip_import`, `_tip_namespace`, …, `_compose_*`) turned out to have **no docstrings at all** — the survey was counting **function body length** (long localized return strings) as docstring length. Actual trimmable docstrings in the file totaled ~80 lines, not 400.

**Root cause**: Survey prompt asked for "multi-paragraph candidates" by line range without requiring the agent to confirm the lines were inside a `"""..."""` block. The agent inferred from function size.

**Fix**: Skipped the false targets and trimmed only the genuine docstrings (`parse_lean_contexts`, `_tactic_arg`, `_gloss_local_identifier`, `compose_group_tip`, `_find_matching_span_close`, `_parse_html_chunks`, `_wrap_groups_in_line`, `render_lean_with_tooltips`, plus all dataclass docstrings). File shed 146 lines (~8%), not 400.

**Prevention**: When delegating a survey, require the agent to **quote the first and last line of each claimed docstring** so you can verify it's actually a `"""..."""` block before acting on the list. Better: ask for a unified diff of proposed changes, not just file:line refs.

---


