# Decisions Log

Append-only ADRs. Newest on top. IDs ascending and permanent.

Format per entry:
```
## [DEC-NNN] YYYY-MM-DD — One-line summary

**Context**: …
**Decision**: …
**Alternatives rejected**: …
**Rationale**: …
```

---

## [DEC-018] 2026-06-16 — Sync Serena `ignored_paths` with the non-gitignored do-not-read set; keep `.serena/.gitignore` tracked

**Context**: CLAUDE.md's Headroom/200K bullets were re-edited (same-day successor to [DEC-016]/[DEC-017]). Two deltas bear on repo state: (1) a generalised **do-not-read** doctrine — a set *distinct from* `.gitignore`, enforced via `permissions.deny Read()`, with the new clause "add any non-gitignored do-not-read entry to Serena's `ignored_paths` and keep those surfaces in sync"; `ignored_paths` was empty. (2) The `.serena/` track list narrowed in prose from "`project.yml` and `.gitignore`" to "`project.yml`", which read literally suggests untracking `.serena/.gitignore`.

**Decision**: (1) Set `.serena/project.yml` `ignored_paths` to `/uv.lock`, `/LICENSE` — the only `permissions.deny Read()` entries that are tracked (not gitignored) **and** would otherwise be surfaced by Serena. Root-anchored `/` mirrors the deny-rule style ([DEC-014]). (2) Keep `.serena/.gitignore` tracked (user-confirmed: the nested file serves a legitimate purpose; CLAUDE.md-designated Serena ignores live in the repo-root `.gitignore`) — [DEC-017]'s tracking state stands; the prose drop is simplification, not an untrack directive.

**Alternatives rejected**: Add `.git` to `ignored_paths` — non-gitignored + Read-denied, but Serena already auto-excludes VCS dirs, so listing it changes nothing Serena surfaces; sync here is *semantic* (no do-not-read path reaches Serena), not literal 1:1. Untrack `.serena/.gitignore` to match the literal wording — rejected by user; would also need a redundant repo-root ignore to hide it.

**Rationale**: Gitignored do-not-read paths are already honoured by Serena (`ignore_all_files_in_gitignore: true`); `ignored_paths` need only carry the non-gitignored remainder, keeping the three surfaces (`permissions.deny`, repo-root `.gitignore`, Serena `ignored_paths`) semantically in sync without duplication. Config-only; reversible.

---

## [DEC-017] 2026-06-16 — Move `.serena/` ignore rules to repo-root `.gitignore` (supersedes [DEC-016] mechanism)

**Context**: CLAUDE.md's Headroom paragraph was rewritten to require that `.serena/`'s `cache/`, `project.local.yml`, and `memories/` live in **the repo-root `.gitignore`** (plus Read-denies), while `project.yml` and `.gitignore` stay Git-tracked. [DEC-016] had centralised those ignores in the co-located, Serena-owned `.serena/.gitignore` and explicitly rejected the repo-root option — the updated wording reverses that choice.

**Decision**: (1) Added `.serena/cache/`, `.serena/project.local.yml`, `.serena/memories/` to repo-root `.gitignore` — now the authoritative ignore. (2) Reverted [DEC-016]'s `/memories` addition to `.serena/.gitignore`, returning that tracked file to Serena's auto-generated content (`/cache`, `/project.local.yml`). Tracking of `.serena/.gitignore` + `.serena/project.yml` and the three `Read()` denies ([DEC-016]) are already correct — unchanged.

**Alternatives rejected**: Keep [DEC-016]'s co-located mechanism — contradicts the updated CLAUDE.md. Add repo-root rules yet leave `/memories` in the co-located file — a redundant line that drifts every time Serena regenerates `.serena/.gitignore` (Serena writes only `/cache` + `/project.local.yml`).

**Rationale**: Repo-root rules are immune to Serena rewriting its own `.gitignore`, fixing the latent drift [DEC-016] accepted; the tracked `.serena/.gitignore` now equals Serena-native output, so regeneration yields no spurious diff. Paths stay ignored throughout — no tracking regression. Reversible.

---

## [DEC-016] 2026-06-15 — Track `.serena/project.yml`; gitignore + Read-deny the rest of Headroom's `.serena/`

**Context**: CLAUDE.md gained a directive: Headroom (the read-compression wrapper) introduces `.serena/`, where `project.yml` is the tracked LSP config and `cache/`, `project.local.yml`, `memories/` "should be ignored both by you and Git." The dir was entirely untracked (`?? .serena/`); Serena's auto-generated `.serena/.gitignore` covered `/cache` + `/project.local.yml` but **not** `/memories`. Nothing was Read-denied.

**Decision**: (1) Added `/memories` to the co-located `.serena/.gitignore`, keeping Serena's own file as the ignore mechanism. (2) Tracked `.serena/.gitignore` + `.serena/project.yml` so the LSP config and its ignore rules survive a fresh clone. (3) Added `Read()` denies for `/.serena/cache/**`, `/.serena/memories/**`, `/.serena/project.local.yml` ([DEC-014] root-anchored pattern) — the "ignored by you" half. `project.yml` stays readable (small, occasionally-useful config).

**Alternatives rejected**: Centralise `.serena/` ignores in the root `.gitignore` — duplicates Serena's co-located `.gitignore` and a fresh Serena/Headroom run regenerates its own anyway. Read-deny `project.yml` too — it is the one file meant to be versioned.

**Rationale**: Matches upstream Serena layout (versioned `project.yml` + co-located ignore). `memories/` is empty and unused — this project's memory system is `.agent/`, not Serena's — so ignoring it forecloses future drift if Serena ever writes there. Read-denies stop LSP-pickle/cache and memory-file context burn, consistent with [DEC-014].

---

## [DEC-015] 2026-06-08 — Reusable boot prompt becomes the `/session-prompt` slash command with roadmap override

**Context**: The reusable session prompt lived at `.agent/SESSION_PROMPT.md`, pasted by hand into each fresh session with user steering appended after a `---`. Pasting is friction; the override convention was prose, not mechanism. CLAUDE.md's "write a reusable prompt to a file" directive ([DEC-004]) is satisfied equally by a slash command, which Claude Code invokes natively.

**Decision**: Relocate the prompt to the `/session-prompt` slash command at `.claude/commands/session-prompt.md`. Bare `/session-prompt` (empty `$ARGUMENTS`) runs the roadmap per usual — `SPEC.md` §0 contract: pick the next §11.3 build unit, load only its §11.4 slice, implement, gate, commit, end. `/session-prompt <TASK>` (non-empty `$ARGUMENTS`) makes `<TASK>` the sole focus for that session and defers the roadmap (this relocation task was itself such an override). Bootstrap reads (CLAUDE.md → INDEX.md → …) are unchanged and run in both branches. `SESSION_PROMPT.md` deleted; the `INDEX.md` Files-table row became an external-pointer note; CLAUDE.md's meta-instruction repointed to the command. The [DEC-004] defer-to-CLAUDE.md content principle carries over verbatim.

**Alternatives rejected**:
- `.claude/skills/session-prompt/SKILL.md` — same `/session-prompt` invocation but adds a directory + SKILL.md indirection and supporting-file scaffolding this prompt does not need. Commands are skills under the hood, so the single-file command is the KISS endpoint.
- Keep `SESSION_PROMPT.md` and make the command a thin wrapper — two sources for one prompt; reintroduces the [DEC-004] drift class.
- Two commands (`/session-prompt` + `/session-task`) for the two branches — `$ARGUMENTS` substitution handles both in one file; splitting duplicates the bootstrap.

**Rationale**: One native invocation replaces copy-paste; the override is now a first-class argument, not a prose convention. `disable-model-invocation: true` keeps the boot prompt user-triggered only. Single source of truth preserved — no SESSION_PROMPT ↔ CLAUDE.md mirror left to drift.

---

## [DEC-014] 2026-06-08 — `Read()` deny rules in `.claude/settings.json` (token guardrail)

**Context**: New CLAUDE.md directive: maintain `permissions.deny` `Read()` rules against low-benefit paths. Measured: `.elan` 13G, `.venv` 53M, `uv.lock` 112K (~30K tok of version pins), `LICENSE` 12K, plus binaries (`*.olean`, `__pycache__`, `.lake`) and `.git` internals.

**Decision**: Committed `.claude/settings.json` denying Read on `/.elan/**`, `/.venv/**`, `/.git/**`, `/**/__pycache__/**`, `/**/.lake/**`, `/**/*.olean`, `/**/*.ilean`, `/uv.lock`, `/LICENSE`. Leading `/` = **project-root** anchor (docs semantics: `//`=absolute, `~/`=home, `/`=project root, bare or `./`=cwd). Deliberately readable: `*.olean.stamp` (1-line cache-debug text, [ARC-009]), `.agent/NAVMAP.md`, `.env*` (credential use granted by CLAUDE.md).

**Alternatives rejected**: `./`-prefixed patterns — anchor to *cwd*, silently mis-scope if a session/subagent runs from a subdir. Denying `.env*` — would obstruct granted credential use. Trusting in-session probes — settings edits are **not** hot-applied to the running session; verified instead via fresh `claude -p` probes (all four pattern classes DENIED, control file ALLOWED).

**Rationale**: Guardrail, not a security boundary — Bash (`git`, `uv tree`, grep) still reaches these paths when genuinely needed, though deny also covers recognized file commands (`cat`/`head`/`tail`/`sed`). Stops Read/Glob/`@`-mention context burn on toolchain internals, site-packages, lockfile pins, and binaries. Edit the file if a rule proves obstructive.

---

## [DEC-013] 2026-06-04 — Olean cache keyed to toolchain via `.olean.stamp` sidecar (not import-probe)

**Context**: `_ensure_knowledge_base_compiled` recompiled only on source-mtime staleness, so a floated `stable` channel (v4.29.1 → v4.30.0) left mtime-fresh oleans that fail the kernel with "incompatible header" at verify time — the recurring [LSN-002]/[LSN-005] class. Needed an import-time auto-heal.

**Decision**: Capture the active toolchain once at import (`LEAN_VERSION` = full `lean --version` line incl. commit). After each compile, write it to `MedicalKnowledge.olean.stamp` (gitignored sidecar). Cache is reusable iff mtime-fresh **AND** stamp == `LEAN_VERSION`. If the live version is undeterminable (lean missing), fall back to mtime-only — no regression to prior behaviour.

**Alternatives rejected**: Probe-by-import (run a throwaway `import MedicalKnowledge`, recompile on "incompatible header") — tests the real condition but adds a `lean` subprocess per locale on *every* boot, including steady-state. Oleans are strictly toolchain-locked, so version-string equality is an *exact* proxy, not a heuristic — the cheaper check is equally correct. Pinning a `lean-toolchain` file — would stop the float but overrides the project's deliberate stable-channel design and still wouldn't heal an already-stale cache.

**Rationale**: One `lean --version` at import (~0.3s, once) beats a per-locale subprocess every boot; steady-state boots do zero extra Lean work (verified: olean mtime stable across imports). Auto-heals the toolchain-drift half of [LSN-002]/[LSN-005] with no manual `rm`.

---

## [DEC-012] 2026-06-04 — Token-efficiency pass: compress settled DECISIONS in place; value-based pruning; add NAVMAP

**Context**: Measured the per-session bootstrap read (CLAUDE.md + `.agent/`) at ~49K chars ≈ 12.3K tokens. DECISIONS.md was the largest single file (~4.6K tok) and the `compaction.sh` location saga ([DEC-008]..[DEC-011]) was **50%** of it (9,167 chars) — four self-superseding entries that net to one durable fact, re-read in full every session. User directive: make working in this codebase more token-efficient.

**Decision**: (1) Compress settled/superseded entries **in place** to their durable takeaways, **preserving every ID** (greppable; [DEC-008]/[DEC-010] become one-line superseded pointers to [DEC-011]). (2) Generalise the INDEX pruning policy from age-based (90-day) to **value-based**: a *settled or superseded* entry may be compressed to its durable takeaway at any age, IDs retained. (3) Add a regenerable `.agent/NAVMAP.md` (symbol index) + `scripts/gen_navmap.sh` so in-task work targets reads instead of loading whole files; it is **on-demand**, not part of the bootstrap read order. Also: wiped stale SCRATCH; tightened ARCHITECTURE prose. CLAUDE.md left untouched (user-owned).

**Alternatives rejected**: Hot/cold split to a separate archive file — user chose in-place over a second file. Leave logs append-only/age-gated — the 90-day rule would force 90 days of re-reading 7.7K chars of settled churn, itself token-inefficient. Hand-annotated symbol map — drift risk ([LSN-004]); a grep-based generator stays fresh by construction.

**Rationale**: The compaction saga proved that verbose rejected-alternatives prose on a *peripheral, settled* question becomes pure recurring tax. Value-based compression keeps the re-exploration-preventing facts (why a vendored regular file; the no-statusline finding) while shedding the narrative. Net bootstrap saving ≈ 1.9K tok/session from the saga alone, before ARCHITECTURE trims.

---

## [DEC-011] 2026-06-01 — `compaction.sh` settled: in-repo vendored copy of the global gauge

Canonical state; supersedes the [DEC-008]→[DEC-010] back-and-forth below (kept as terse pointers per the compress-in-place pass [DEC-012]). Repo-root `compaction.sh` is a tracked, executable **regular file** — a byte-identical vendored snapshot of the upstream global `$HOME/.claude/compaction.sh` (real path `~/agents/claude/compaction.sh`). It prints plain `N% used/window`: finds the session transcript by `CLAUDE_CODE_SESSION_ID` glob (newest-mtime `*.jsonl` fallback), sums the last assistant turn's `input + cache_creation + cache_read`, window = 200K when `CLAUDE_CODE_DISABLE_1M_CONTEXT` is truthy else 1M. **Single-mode by design**: the old statusline stdin-JSON branch and ANSI color (red/yellow thresholds) were stripped 2026-06-08 (global+repo in lockstep, `diff` clean) as dead code — the repo's statusline is a *separate* `~/.claude/statusline.sh` ([DEC-009]) that never called this, and agents always invoke it via Bash with `CLAUDE_CODE_SESSION_ID` set, hitting the transcript path. The in-repo copy may drift; re-sync with `cp "$HOME/.claude/compaction.sh" ./compaction.sh` and confirm `diff` clean.

**Why a vendored regular file** (not a symlink, not global-only): an absolute-`$HOME` symlink breaks on clone and on the host/container path split (`/run/host/...` vs `/var/home/...`); a vendored file is self-contained and runs without `$HOME/.claude`. Reversed [DEC-010]'s global-only removal on explicit user instruction (final say). The monitor-often / wrap-up-≥80% *workflow rule* lives in CLAUDE.md only — deliberately not restated here ([DEC-006]).

---

## [DEC-010] 2026-06-01 — (superseded by [DEC-011]) Briefly removed the repo copy, pointing to global `$HOME/.claude/compaction.sh`; reverted by the user re-vendoring in-repo. See [DEC-011].

---

## [DEC-009] 2026-06-01 — No project-local statusline in lean-cds; context gauge stays CLI-only here

**Decision**: No project-local `statusLine` in this repo — in-UI context display is the user's *global* statusline (`~/.claude/settings.json`), outside repo scope; `compaction.sh` is the committed CLI gauge. A statusline is cross-project agent UX, not lean-cds infrastructure. Logged so future sessions don't re-offer it.

**Reusable finding** (any statusline): the stdin JSON carries live context — `context_window.used_percentage`, `context_window.context_window_size` (200000, or 1000000 on the 1M beta), and `context_window.total_input_tokens` (= `input + cache_creation + cache_read`). A newly-added shell-executing `statusLine` needs a Claude Code restart + workspace-trust accept to activate (no mid-session hot-reload).

---

## [DEC-008] 2026-06-01 — (superseded by [DEC-011]) Adopted `compaction.sh` as the canonical context gauge at repo root; placement/path since settled in [DEC-011]. Adopt-as-canonical intent carries forward.

---

## [DEC-007] 2026-06-01 — Capability investments (AOP tooling, LSP/REPL setup) are task-driven, not standing

**Context**: The 2026-06-01 CLAUDE.md edit adds two forward-looking capability hints: "consider … agent-oriented programming languages … as well as any other tooling … that targets AI" and "Make full use of … LSP servers and REPLs." Asked whether to act now, the user chose **defer both**.

**Decision**: Treat both as standing encouragements, not speculative this-session work. Stand up LSP servers / `bgcmd` REPLs, or trial an agent-oriented language, when a *concrete coding task* would materially benefit — evaluate per task. The current docs/maintenance phase triggers neither.

**Alternatives rejected**:
- Set the tooling up speculatively now — investment with no active consumer; risks the home-dir/project cruft the same CLAUDE.md edit's clean-up directive warns against.
- Read the hints as a one-time prompt and drop them — they are standing guidance; this entry records *timing*, not rejection.

**Rationale**: Avoids speculative setup and prevents future sessions re-asking, while preserving the CLAUDE.md encouragement. Re-evaluation trigger is explicit: a coding task the tooling demonstrably accelerates.

---

## [DEC-006] 2026-06-01 — Docs carry only version info a grep can't cheaply recover

**Context**: CLAUDE.md (2026-06-01 edit) added: entries "must provide value beyond what the project documentation, codebase, and Git history already provide; superfluous information like package versions only add bloat and the potential for drift." ARCHITECTURE.md carried precise pins (`driver.js 1.3`, `uv ≥ 0.11`, `Python 3.13`) that duplicate `pyproject.toml` (`requires-python >=3.13`, `litestar>=2.13`, `uvicorn>=0.34`) and `templates/index.html` (`driver.js@1.3.1`, `htmx.org@2.0.4`). `driver.js 1.3` was already mildly stale vs the actual `1.3.1`.

**Decision**: `pyproject.toml` + `templates/index.html` own exact versions. ARCHITECTURE.md keeps a version token only when the *major* is load-bearing architecture — i.e. the major changes the API an agent codes against (`Lean 4`, `Litestar 2`, `HTMX 2`). Precise minor/patch pins are dropped; where the exact value matters, the doc points to the file the toolchain actually reads. Historical version mentions inside postmortems (e.g. `v4.29.1` in [LSN-002]) stay — they narrate a past incident, not current config.

**Alternatives rejected**:
- Strip every version token — loses the major-version API signal (`Litestar 2` vs `1` is a real code difference) for no drift reduction (majors rarely churn).
- Keep all pins — the exact duplicated drift surface the new rule targets; `driver.js 1.3` had already drifted.

**Rationale**: Single source of truth is the file the toolchain reads, not a prose mirror of it. The doc carries only what an agent cannot recover with one `grep pyproject.toml`. Generalises the DEC-005 single-source principle from prose sections to version tokens.

---

## [DEC-005] 2026-05-14 — README.md collapsed to a 6-line stub; ARCHITECTURE.md is canonical

**Context**: README.md (220 lines) duplicated ~104 lines of ARCHITECTURE.md content (Stack table, File/Project layout, Routes / Public surfaces, Verification pipeline / Data flow) and additionally contained a `## Scenario data model` section that pasted Python dataclass defs from `scenarios.py` verbatim. ~47% of the README was duplication. Same drift class as DEC-004 (SESSION_PROMPT ↔ CLAUDE.md). The discrepancy in route paths (README correct, ARCHITECTURE.md wrong — `POST /verify` vs actual `POST /scenarios/{id}/verify`) surfaced only during the diff pass and is logged as [LSN-004].

**Decision**: ARCHITECTURE.md is now the canonical technical reference for the project. README.md is a 6-line stub: title, one-sentence what-is, and four links (ARCHITECTURE.md, INDEX.md, CLAUDE.md, LICENSE). Unique README content (Prerequisites, Quick start, Adding-a-scenario procedure, Common dev tasks, Limitations, bilingual orientation paragraph, patient names per scenario) was absorbed into ARCHITECTURE.md. Route paths corrected against `app.py` grep.

**Alternatives rejected**:
- Aggressive (~50 lines, keep Prerequisites/Quickstart/License in README) — still maintains two truths; trim the rest.
- Moderate (cut verbatim duplicates only) — leaves README as parallel doc; drift surface remains.
- User picked the strongest option (full elimination); the .agent/-as-canonical model is the natural endpoint for an AI-developed project where humans are not the primary readers.

**Rationale**: Single source of truth eliminates the entire drift class. ARCHITECTURE.md grew from 80 → ~165 lines (absorbed content) but the duplicate surface is gone. GitHub viewers still get the four pointers from the stub.

---

## [DEC-004] 2026-05-14 — SESSION_PROMPT.md defers to CLAUDE.md instead of restating it

*Partly superseded by [DEC-015]* — the prompt file moved to the `/session-prompt` slash command (`.claude/commands/session-prompt.md`); the defer-to-CLAUDE.md content principle below still holds.

**Context**: Original `SESSION_PROMPT.md` (~42 lines) restated ~12 rules already present verbatim or near-verbatim in `CLAUDE.md`: sudo, env-modification, git-locally-only, ask-when-ambiguous, accuracy-over-completion, failure-acceptable, LLM-optimized files, immutable CLAUDE.md, web-search-for-SOTA, pink-elephant negative-constraint framing, conversational-chat-reserved-for-blockers, ambitious-work-welcomed. Two harms: (a) any drift between the two files silently contradicts; (b) bootstrap tokens spent restating known facts instead of project-specific orientation.

**Decision**: SESSION_PROMPT.md keeps only project-unique content — identity (lean-cds, Lean 4 / Python / Litestar, JA default), `.agent/` read order, project tooling (`uv`, `./.elan/bin/lean`, `check_scenarios.py`), grep-LSN-first reminder, and the self-update meta-instruction. CLAUDE.md is the single source of truth for universal philosophy; the prompt explicitly defers to it.

**Alternatives rejected**:
- Keep restating for emphasis — drift risk + token cost outweighs emphasis benefit; CLAUDE.md is read first anyway.
- Merge SESSION_PROMPT.md into INDEX.md — different audience (user-paste vs. agent-internal); keeping them separate preserves clean entry points.
- Auto-generate the prompt from CLAUDE.md + INDEX.md — over-engineered for a file the user pastes once.

**Rationale**: Reduces SESSION_PROMPT.md from 42 → 19 lines (~55% reduction). Eliminates duplication-induced drift surface. Future agents still get full context because CLAUDE.md is item #1 in the read order.

---

## [DEC-003] 2026-05-14 — Newest-on-top ordering for append-only logs

**Context**: DECISIONS.md and LESSONS.md will be partial-read by future agents. Two ordering options: chronological (oldest top) vs. reverse-chronological (newest top).

**Decision**: Newest on top. Numeric IDs ascend (DEC-001, DEC-002, …) but appear in reverse position order.

**Alternatives rejected**:
- Chronological with an "Active" summary at the top — doubles maintenance.
- Strictly chronological — buries recent context behind history.

**Rationale**: LLMs partial-reading these files benefit most from front-loaded recent relevance. The cost (ID order differs from position order) is minor; IDs are still discoverable by grep.

---

## [DEC-002] 2026-05-14 — Memory system lives at `.agent/`

**Context**: New CLAUDE.md mandates a memory/scratchpad system. Candidates: `.agent/` (new top-level), `artifacts/agent/` (under existing artifacts), `.claude/` (per-machine harness state).

**Decision**: Top-level `.agent/`, version-controlled.

**Alternatives rejected**:
- `artifacts/agent/` — mixes ephemeral build output with durable agent state.
- `.claude/` — conventionally gitignored; would not sync to fresh clones / new machines.

**Rationale**: Top-level visibility, git-tracked, easy to discover (`ls` shows it), separable from `.claude/` (harness state) and `artifacts/` (build output).

---

## [DEC-001] 2026-05-14 — Drop the old CLAUDE.md operational rules entirely

**Context**: CLAUDE.md was rewritten from a structured rule set (modern tooling, theme awareness, no backend info in UI, isolated venvs, two-phase research/implementation workflow, enterprise UI) into a meta-instructional philosophy. The user was asked whether to migrate the old rules into the new memory system as "inherited norms" or drop them; they chose drop.

**Decision**: Treat the new CLAUDE.md as the sole source of truth. Old rules are **not** migrated into `.agent/`.

**Alternatives rejected**:
- Migrate as inherited norms — would silently re-introduce constraints the user removed.
- Rule-by-rule decision — overhead without proportional value.

**Rationale**: User intent is explicit. The codebase already follows most former rules de facto; dropping the *documented* rule loosens future agents' latitude but doesn't change current behavior. If a former rule turns out to matter, it can re-surface via a new DEC-NNN entry.
