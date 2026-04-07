# Implementation Plan: From "Collision Demo" to Defensible Verdict Engine

## Background

`lean-cds` is a Litestar + Lean 4 demo that currently encodes three clinical
scenarios as monotonic first-order axioms and asks Lean to derive `False`. An
audit established that the "contradictions" the system proves are artifacts of
the encoder dropping context, deontic modality, and in-document exceptions —
not properties of the underlying medical knowledge. Every "polypharmacy
collision" the demo reports is a false positive that a human clinician
resolves trivially.

This plan rebuilds the verification core so that:

1. Guidelines carry **temporal/contextual preconditions**.
2. Recommendations are encoded with **deontic modality** (`Indicated` is not
   the same as `Obligated`).
3. **In-document exceptions** are faithfully imported as guard conditions
   (the original Scenario B silently dropped the ADA's own `K ≥ 3.3`
   precondition — that is the audit's most damning finding).
4. Missing chart data yields **`InsufficientData`**, not a contradiction.
5. The verifier returns a **four-state `Verdict`**, not a binary
   contradiction flag.
6. The current three scenarios stop reporting contradictions and start
   reporting clinically-correct verdicts.

The Lean kernel still does the verification work — it typechecks the
deeply-embedded evaluation engine on each scenario. We are **not** moving to a
two-tier external-solver architecture; that is deferred until after the demo
stage.

## Architectural decisions (settled — do not relitigate)

These decisions have been made deliberately. If you hit a concrete blocker
that requires revisiting one of them, stop and ask the user; do not change
direction unilaterally.

1. **Pure Lean 4, deep embedding.** We define `Rule`, `Chart`, `Verdict`, and
   an `evaluate` function as ordinary Lean 4 terms. The meta-logic (Lean's
   own type theory) stays monotonic; the embedded object logic is defeasible
   via priorities. No external solver, no Datalog, no ASP, no Carneades.

2. **File organization: shared core + per-scenario fragment.** A single
   `CORE_LEAN_SOURCE` constant in `scenarios.py` holds the type definitions
   and `evaluate` function. Each `Scenario.lean_code` field holds only the
   rules, chart, and `#eval` lines for that scenario. The Python wrapper
   concatenates `CORE_LEAN_SOURCE + "\n\n" + scenario.lean_code` at write
   time and writes the result to `audit.lean`. No Lake project, no separate
   files on disk, no `import` statements.

3. **Three-valued observations.** The `Chart` maps observations to a
   `ThreeValued` enum (`tTrue`, `tFalse`, `tUnknown`). Rules whose
   preconditions evaluate to `tUnknown` are *suspended* and contribute to
   `InsufficientData`.

4. **Verdict shape.** Exactly four cases: `Recommended action |
   Underdetermined actions | InsufficientData missingObs | GenuineConflict
   ruleIds`. There is no explicit `Forbidden` case — an action that no
   surviving rule recommends is implicitly not in the verdict.

5. **Defeasibility mechanism: numeric priority.** Each `Rule` carries a `Nat`
   priority. When two rules conclude opposite modalities on the same action,
   the strictly higher-priority rule wins. Equal priorities with opposite
   modalities → `GenuineConflict`. This is naive but adequate for the demo;
   richer argumentation frameworks are out of scope.

6. **No soundness theorem.** We do not prove a separate `evaluate_sound`
   lemma. The verification claim is "the Lean kernel typechecks the
   `evaluate` function definition and reduces it to a concrete `Verdict` for
   each scenario." That is what the user sees when `lean audit.lean` exits 0
   and stdout contains the expected `VERDICT:` line. Full mathematical
   soundness of a defeasible reasoning engine is research-grade work and
   explicitly out of scope.

7. **Verdict communication: stdout marker strings.** Each scenario ends with
   `#eval IO.println s!"VERDICT: {evaluate rules chart}"`, which prints a
   single line beginning with `VERDICT: ` to Lean's stdout. The Python
   wrapper parses that line. No JSON, no structured IPC, no Lean → Python
   serialisation library.

## Glossary

| Term              | Meaning in this codebase                                       |
|-------------------|----------------------------------------------------------------|
| `ThreeValued`     | `tTrue \| tFalse \| tUnknown`                                  |
| `Observation`     | A discrete chart fact, identified by a `String` key            |
| `Action`          | A possible intervention, identified by a `String` key          |
| `DeonticModality` | `indicated \| obligated \| contraindicated`                    |
| `Chart`           | `{ lookup : Observation → ThreeValued }`                       |
| `Rule`            | `{ id, source, appliesWhen, conclusion, priority }`            |
| `Verdict`         | `recommended \| underdetermined \| insufficientData \| genuineConflict` |
| Core source       | The shared Lean source held in `scenarios.CORE_LEAN_SOURCE`    |
| Scenario fragment | The per-scenario Lean source held in `Scenario.lean_code`      |

## How to run Lean against a scenario manually

Most sections need a way to compile the concatenated source by hand. Use:

```bash
uv run python -c "
from scenarios import CORE_LEAN_SOURCE, SCENARIOS
import sys
sid = sys.argv[1] if len(sys.argv) > 1 else 'scenario-a'
src = CORE_LEAN_SOURCE + '\n\n' + SCENARIOS[sid].lean_code
open('/tmp/audit.lean', 'w').write(src)
" scenario-a && lean /tmp/audit.lean
```

Replace `scenario-a` with `scenario-b` or `scenario-c` as needed. Inspect
stdout for the `VERDICT:` line.

---

## Section 1 — Lean core: types and DSL skeleton

- [x] **Status** — Added `CORE_LEAN_SOURCE` with stub `evaluate`; `ToString Verdict` format is `<Name> <comma-joined-detail>` (e.g. `Recommended HoldThiazideAndRehydrate`, `InsufficientData ` for empty list).

**Goal.** Add the foundational types of the deep-embedded DSL to a new
module-level constant `CORE_LEAN_SOURCE` in `scenarios.py`. No evaluation
logic in this section — just the data model and a stub `evaluate` that
returns `Verdict.insufficientData []`. Section 2 will replace the stub.

**Files affected.** `scenarios.py`

**Tasks.**
1. Read `scenarios.py` end to end before editing.
2. Add `CORE_LEAN_SOURCE: str` near the top of the file (above
   `SCENARIO_A`). It must be a raw triple-quoted string containing Lean 4
   source that defines, in order, inside `namespace ClinicalAudit.Core`:
   - `inductive ThreeValued | tTrue | tFalse | tUnknown` with
     `deriving Repr, DecidableEq` if Lean accepts it.
   - `abbrev Observation := String`
   - `abbrev Action := String`
   - `inductive DeonticModality | indicated | obligated | contraindicated`
     with `deriving Repr, DecidableEq`.
   - `structure Chart where lookup : Observation → ThreeValued`
   - `structure Rule where`
       - `id : String`
       - `source : String`
       - `appliesWhen : Chart → ThreeValued`
       - `conclusion : DeonticModality × Action`
       - `priority : Nat`
   - `inductive Verdict`
       - `| recommended (action : Action)`
       - `| underdetermined (actions : List Action)`
       - `| insufficientData (missing : List Observation)`
       - `| genuineConflict (rules : List String)`
   - `instance : ToString Verdict` whose output begins with one of
     `Recommended `, `Underdetermined `, `InsufficientData `,
     `GenuineConflict `. The detail format is up to you, but it must be
     parseable by a simple `^(\w+)(?: (.*))?$` regex on the line that
     follows the `VERDICT: ` marker.
   - Stub: `def evaluate (_rules : List Rule) (_chart : Chart) : Verdict :=
     Verdict.insufficientData []`
   - Close the namespace with `end ClinicalAudit.Core`.
3. Run the manual compile command from the top of this file against any
   scenario id; the existing `SCENARIO_A.lean_code` will fail to compile
   (it still contains the old axiom-based code) — that is expected for now.
   To verify the core alone, write only `CORE_LEAN_SOURCE` to `/tmp/audit.lean`
   and run `lean /tmp/audit.lean`:

   ```bash
   uv run python -c "from scenarios import CORE_LEAN_SOURCE; open('/tmp/audit.lean','w').write(CORE_LEAN_SOURCE)" && lean /tmp/audit.lean
   ```

**Acceptance criteria.**
- `uv run python -c "import scenarios"` succeeds without exception.
- The core-only compile command above exits 0 with no errors.
- The placeholder `evaluate` definition typechecks.

**Notes.**
- `Observation` and `Action` are deliberately `String` aliases. Type-safe
  enums would force every scenario to declare a constructor for every fact,
  which is gratuitous ceremony for a demo. The trade-off is intentional.
- Do **not** add example rules, scenarios, or `#eval` lines in this section.
  Section 1 is pure type definitions plus a stub.
- Do **not** touch `SCENARIO_A`, `SCENARIO_B`, or `SCENARIO_C` in this
  section. They will fail to compile against the new core; that is fine and
  is fixed in Sections 3, 4, 5.

---

## Section 2 — Lean core: evaluation engine

- [x] **Status** — Implemented `evaluate` with `isPositiveModality`/`isNegativeModality`/`maxPriority`/`dedupActions` helpers; per step 4 simplification, `InsufficientData` always returns an empty `missing` list (no observation-key extraction from opaque `appliesWhen`); smoke `#eval` uses a `smokeUnknownChart` helper to avoid nested-brace ambiguity inside `s!`.

**Goal.** Replace the Section 1 stub `evaluate` with a real implementation
that produces each of the four `Verdict` cases according to the semantics
documented below. After this section, the core source compiles standalone
and a smoke `#eval` returns a sensible verdict on a tiny synthetic input.

**Files affected.** `scenarios.py` (the `CORE_LEAN_SOURCE` constant)

**Semantics of `evaluate rules chart`.**

1. **Classify each rule by precondition.** Evaluate `rule.appliesWhen chart`:
   - `tTrue`  → the rule *fires*.
   - `tFalse` → the rule is *inert* (drop it).
   - `tUnknown` → the rule is *suspended* (could fire if the missing
     observation were known).

2. **Collect fired conclusions.** From the fired rules, build a list of
   `(modality, action, ruleId, priority)` tuples.

3. **Per-action analysis.** For each distinct `action` mentioned in the
   fired conclusions:
   - Let `pos` = fired rules concluding `indicated action` or
     `obligated action`.
   - Let `neg` = fired rules concluding `contraindicated action`.
   - Resolve:
     - If `pos` is non-empty and `neg` is empty → action is **recommended**.
     - If `neg` is non-empty and `pos` is empty → action is **forbidden**
       (drop it from the verdict).
     - If both are non-empty:
       - Let `maxPos` = max priority in `pos`; `maxNeg` = max priority in
         `neg`.
       - `maxPos > maxNeg` → recommended.
       - `maxNeg > maxPos` → forbidden.
       - `maxPos = maxNeg` → action contributes to `genuineConflict`; record
         the ids of the conflicting rules (one from each side at the tied
         priority is sufficient).

4. **Suspended-rule check.** If the fired-rule analysis yields no conflicts
   and the recommended-actions list is empty, but at least one rule was
   *suspended*, return `Verdict.insufficientData missing` where `missing` is
   the deduplicated list of observation keys whose `tUnknown` value caused
   the suspension. For the demo, the simplest implementation is acceptable:
   if you cannot easily extract the relevant observation key from
   `appliesWhen` (since it is an opaque function), return
   `Verdict.insufficientData []` and document the limitation in the section's
   status line. Do not block on this — empty `missing` is acceptable.

5. **Compose final verdict** in this priority order:
   - If the conflict list is non-empty → `Verdict.genuineConflict ids`.
   - Else if exactly one action is recommended → `Verdict.recommended action`.
   - Else if two or more actions are recommended →
     `Verdict.underdetermined actions`.
   - Else if any rule was suspended → `Verdict.insufficientData missing`
     (per step 4).
   - Else → `Verdict.insufficientData []` (degenerate "no applicable
     guidance" case).

**Tasks.**
1. Implement `def evaluate` in `CORE_LEAN_SOURCE` matching the semantics
   above. Use only `List` combinators from Lean's `Init` (no Mathlib
   dependency).
2. Helpful primitives you can write inline:
   - A `partition3` function that splits `rules` into fired/inert/suspended.
   - A `dedupActions : List Action → List Action` (use `String` equality).
   - A `maxPriority : List Rule → Nat` that returns 0 on the empty list.
3. Add a smoke `#eval` *inside* `CORE_LEAN_SOURCE`, after `evaluate`, that
   runs `evaluate [] { lookup := fun _ => ThreeValued.tUnknown }` and
   `IO.println`s the result. This must compile and produce a `Verdict`-shaped
   output line during the manual compile.
4. Re-run the manual core-only compile command from Section 1 and confirm
   exit 0 plus the smoke output.

**Acceptance criteria.**
- The core-only `lean /tmp/audit.lean` exits 0.
- Stdout from that compile contains a recognisable `Verdict` print from the
  smoke `#eval`.
- `evaluate` contains zero `sorry`, zero `axiom`, zero `unsafe`.

**Notes.**
- Lean 4's structural recursion may complain on hand-rolled `partition`s.
  If so, use `List.foldr` with explicit accumulators — that always
  terminates and Lean accepts it without contortions.
- `String` equality: use `String.decEq` or just `==`. Do not import any
  decidability typeclass machinery beyond what `Init` provides.
- If you find yourself reaching for Mathlib, stop. The demo must run with
  vanilla Lean 4 from `elan`. Add nothing to `lakefile.lean` (there isn't
  one) and add no Lake config.
- Resist the urge to prove a soundness lemma. Decision 6 above explicitly
  defers it.

---

## Section 3 — Encode Scenario A in the new framework

- [x] **Status** — Rewrote `SCENARIO_A.lean_code` with three rules (AHA-ACC priority 1, two KDIGO rules priority 2) under `namespace ClinicalAudit.ScenarioA`; chart sets `HemodynamicallyStable := tFalse` so the AHA rule is inert and the verdict resolves to `Recommended HoldThiazideAndRehydrate`.

**Goal.** Rewrite `SCENARIO_A.lean_code` so it (a) consumes the
`CORE_LEAN_SOURCE` types and `evaluate`, (b) faithfully encodes the AHA/ACC
and KDIGO guidelines including their preconditions, and (c) produces a
clinically correct verdict — recommending that the thiazide be held and the
patient rehydrated, **not** a contradiction.

**Files affected.** `scenarios.py` (`SCENARIO_A.lean_code` only — leave the
natural-language fields alone)

**Required encoding.**

Observations (string keys, exact spelling matters because rules will
reference them):
- `"EssentialHypertension"`
- `"HemodynamicallyStable"`
- `"SevereDehydration"`

Actions:
- `"ThiazideDiuretic"`
- `"HoldThiazideAndRehydrate"`

Rules:

| id                          | source              | precondition                                          | conclusion                                  | priority |
|-----------------------------|---------------------|-------------------------------------------------------|---------------------------------------------|----------|
| `"AHA-ACC-HTN-8.1.5"`       | AHA/ACC HTN §8.1.5  | `EssentialHypertension = tTrue` AND `HemodynamicallyStable = tTrue` | `(indicated, "ThiazideDiuretic")`           | `1`      |
| `"KDIGO-AKI-3.1.2-neg"`     | KDIGO AKI §3.1.2    | `SevereDehydration = tTrue`                           | `(contraindicated, "ThiazideDiuretic")`     | `2`      |
| `"KDIGO-AKI-3.1.2-pos"`     | KDIGO AKI §3.1.2    | `SevereDehydration = tTrue`                           | `(indicated, "HoldThiazideAndRehydrate")`   | `2`      |

Chart for `thePatient`:
- `EssentialHypertension → tTrue`
- `HemodynamicallyStable → tFalse` (BP 84/52 disqualifies stability)
- `SevereDehydration → tTrue`
- everything else → `tUnknown`

Expected verdict line in stdout:
```
VERDICT: Recommended HoldThiazideAndRehydrate
```

(Exact formatting depends on your `ToString Verdict` instance from Section 1
— whatever you chose, the parser in Section 6 will match it. If you have not
yet committed to a format, document it in this section's status line.)

**Tasks.**
1. Read the current `SCENARIO_A.lean_code` so you know what you are
   replacing. Do **not** try to translate the old axioms line by line —
   start fresh from the table above.
2. Replace `SCENARIO_A.lean_code` with a Lean source string that:
   - Opens `namespace ClinicalAudit.ScenarioA`
   - Opens `ClinicalAudit.Core` via `open ClinicalAudit.Core`
   - Defines `def rules : List Rule := [ ... ]` matching the table.
     Use Lean lambda syntax for `appliesWhen`, e.g.
     `fun chart => match chart.lookup "EssentialHypertension", chart.lookup "HemodynamicallyStable" with | .tTrue, .tTrue => .tTrue | _, _ => .tFalse`
   - Defines `def chart : Chart := { lookup := fun obs => match obs with | "EssentialHypertension" => .tTrue | "HemodynamicallyStable" => .tFalse | "SevereDehydration" => .tTrue | _ => .tUnknown }`
   - Ends with `#eval IO.println s!"VERDICT: {evaluate rules chart}"`
   - Closes the namespace with `end ClinicalAudit.ScenarioA`
3. Compile manually (use the command at the top of this file with
   `scenario-a`). Confirm:
   - Exit code 0.
   - Stdout contains a `VERDICT: Recommended HoldThiazideAndRehydrate` line
     (or whatever exact spelling your `ToString Verdict` produces).
4. Do not edit `SCENARIO_A.guideline_a.body`,
   `SCENARIO_A.guideline_b.body`, `SCENARIO_A.patient_summary`,
   `SCENARIO_A.title`, `SCENARIO_A.subtitle`, or
   `SCENARIO_A.collision_summary`. Sections 8 and 9 handle the prose
   reframing.

**Acceptance criteria.**
- Manual compile of `scenario-a` exits 0.
- Stdout contains the expected `VERDICT:` line for a recommended
  `HoldThiazideAndRehydrate`.
- The new `SCENARIO_A.lean_code` contains zero `axiom`, zero `theorem`,
  zero `sorry`, and no reference to `polypharmacy_collision`.

**Notes.**
- Priority `2 > 1` is the mechanism by which the acute KDIGO rule defeats
  the chronic AHA/ACC rule. If you adopt a different mechanism, document it
  in your status-line summary so Sections 4 and 5 can mirror it.
- The "two-rule" encoding of KDIGO (one negating the thiazide, one
  recommending the alternative action) is intentional. A single rule cannot
  carry two conclusions in this DSL.

---

## Section 4 — Encode Scenario B in the new framework

- [x] **Status** — Rewrote `SCENARIO_B.lean_code` with three rules under `namespace ClinicalAudit.ScenarioB`; ADA precondition restored (`appliesWhen` references both `DiabeticKetoacidosis` and `SerumKAtLeast33`); chart sets `SerumKAtLeast33 := tFalse` so the ADA rule is inert and the verdict resolves to `Recommended RepleteKThenStartInsulin`.

**Goal.** Rewrite `SCENARIO_B.lean_code` to faithfully encode the ADA and
AACE/ACE guidelines, **including the in-document `serumK ≥ 3.3`
precondition that the original Scenario B silently dropped**. This is the
single most important encoding fix in the project — restoring the
precondition makes the manufactured contradiction vanish and reveals the
actual clinical answer.

**Files affected.** `scenarios.py` (`SCENARIO_B.lean_code` only)

**Required encoding.**

Observations:
- `"DiabeticKetoacidosis"`
- `"SerumKAtLeast33"`
- `"SevereHypokalemia"`

Actions:
- `"IVRegularInsulin"`
- `"RepleteKThenStartInsulin"`

Rules:

| id                          | source                   | precondition                                                | conclusion                                       | priority |
|-----------------------------|--------------------------|-------------------------------------------------------------|--------------------------------------------------|----------|
| `"ADA-DKA-Sec16"`           | ADA Standards §16        | `DiabeticKetoacidosis = tTrue` AND `SerumKAtLeast33 = tTrue` | `(obligated, "IVRegularInsulin")`                | `1`      |
| `"AACE-ACE-Hypo-neg"`       | AACE/ACE CSR-4           | `SevereHypokalemia = tTrue`                                 | `(contraindicated, "IVRegularInsulin")`          | `2`      |
| `"AACE-ACE-Hypo-pos"`       | AACE/ACE CSR-4           | `SevereHypokalemia = tTrue`                                 | `(indicated, "RepleteKThenStartInsulin")`        | `2`      |

Chart:
- `DiabeticKetoacidosis → tTrue`
- `SerumKAtLeast33 → tFalse` (measured K is 2.9)
- `SevereHypokalemia → tTrue`
- everything else → `tUnknown`

Expected verdict:
```
VERDICT: Recommended RepleteKThenStartInsulin
```

**Tasks.**
1. Read `SCENARIO_B.lean_code` so you know what you are replacing. Read
   Section 3 above so you know the pattern.
2. Replace `SCENARIO_B.lean_code` with a fresh Lean source string following
   the same shape as Section 3:
   - `namespace ClinicalAudit.ScenarioB`
   - `open ClinicalAudit.Core`
   - `def rules : List Rule := [...]` matching the table. The ADA rule's
     `appliesWhen` **must** reference both `DiabeticKetoacidosis` and
     `SerumKAtLeast33`. Do not omit the precondition.
   - `def chart : Chart := { lookup := fun obs => match obs with ... }`
   - `#eval IO.println s!"VERDICT: {evaluate rules chart}"`
   - `end ClinicalAudit.ScenarioB`
3. Compile manually with `scenario-b`. Confirm exit 0 and the expected
   `VERDICT:` line.
4. Inspect the Lean source one more time and verify by eye that the
   `appliesWhen` of the ADA rule references `SerumKAtLeast33`. This is the
   audit fix this section exists for.
5. Do not edit any of the natural-language fields.

**Acceptance criteria.**
- Manual compile of `scenario-b` exits 0.
- Stdout contains `VERDICT: Recommended RepleteKThenStartInsulin` (or
  equivalent spelling).
- The ADA rule's `appliesWhen` references `SerumKAtLeast33`. Document this
  in your status line ("ADA precondition restored").
- Zero `axiom`/`theorem`/`sorry`/`polypharmacy_collision` in the new source.

**Notes.**
- The clinical correctness of this scenario depends entirely on the
  precondition being present. If you find a way to make the contradiction
  reappear, you have made an error — the contradiction is the bug, not the
  feature.
- Use `obligated` for the ADA insulin recommendation (the actual published
  guideline phrases insulin in DKA as a "should not be delayed" mandate);
  use `indicated` for the K-replete-first alternative.

---

## Section 5 — Encode Scenario C in the new framework

- [x] **Status** — Rewrote `SCENARIO_C.lean_code` with three rules under `namespace ClinicalAudit.ScenarioC` (two APA rules priority 1: `indicated Benzodiazepine` and `indicated NonBenzoAnxiolytic`; one AASM rule priority 2: `contraindicated Benzodiazepine`); chart sets both `AcutePanicEpisode` and `UntreatedSevereOSA` to `tTrue` so all three rules fire and priority 2 > 1 forbids `Benzodiazepine`, leaving the verdict `Recommended NonBenzoAnxiolytic`.

**Goal.** Rewrite `SCENARIO_C.lean_code` so the APA recommendation for
benzodiazepines is encoded as `indicated` (a first-line option), an
alternative non-benzo action is also encoded as `indicated`, and the AASM
contraindication on benzos in untreated severe OSA defeats the benzo
option, leaving the non-benzo as the uniquely-recommended action.

**Files affected.** `scenarios.py` (`SCENARIO_C.lean_code` only)

**Required encoding.**

Observations:
- `"AcutePanicEpisode"`
- `"UntreatedSevereOSA"`

Actions:
- `"Benzodiazepine"`
- `"NonBenzoAnxiolytic"`

Rules:

| id                          | source                | precondition                          | conclusion                                | priority |
|-----------------------------|-----------------------|---------------------------------------|-------------------------------------------|----------|
| `"APA-Panic-Benzo"`         | APA Panic Disorder    | `AcutePanicEpisode = tTrue`           | `(indicated, "Benzodiazepine")`           | `1`      |
| `"APA-Panic-NonBenzo"`      | APA Panic Disorder    | `AcutePanicEpisode = tTrue`           | `(indicated, "NonBenzoAnxiolytic")`       | `1`      |
| `"AASM-OSA-Benzo-neg"`      | AASM OSA Pharm Safety | `UntreatedSevereOSA = tTrue`          | `(contraindicated, "Benzodiazepine")`     | `2`      |

Chart:
- `AcutePanicEpisode → tTrue`
- `UntreatedSevereOSA → tTrue`
- everything else → `tUnknown`

Expected verdict:
```
VERDICT: Recommended NonBenzoAnxiolytic
```

The reasoning the engine should follow: both APA rules fire, contributing
`indicated Benzodiazepine` and `indicated NonBenzoAnxiolytic`. The AASM rule
fires, contributing `contraindicated Benzodiazepine` at priority 2 > 1, so
`Benzodiazepine` is forbidden. `NonBenzoAnxiolytic` has only positive rules,
so it remains recommended. Exactly one action survives → `Recommended`.

**Tasks.**
1. Read `SCENARIO_C.lean_code` and Section 3.
2. Replace `SCENARIO_C.lean_code` with a fresh source string following the
   Section 3 pattern (namespace `ClinicalAudit.ScenarioC`, open core,
   define rules + chart, `#eval` the verdict, end namespace).
3. Compile manually with `scenario-c`. Confirm exit 0 and the expected
   `VERDICT:` line.
4. Do not edit natural-language fields.

**Acceptance criteria.**
- Manual compile of `scenario-c` exits 0.
- Stdout contains `VERDICT: Recommended NonBenzoAnxiolytic`.
- Zero `axiom`/`theorem`/`sorry`/`polypharmacy_collision`.

**Notes.**
- If your verdict comes out as `Underdetermined [Benzodiazepine,
  NonBenzoAnxiolytic]`, the priority resolution in Section 2 step 3 is
  not eliminating the benzo. Re-read that step and confirm your `evaluate`
  drops actions whose `maxNeg > maxPos`.
- If your verdict comes out as `GenuineConflict`, the AASM rule and the
  APA-benzo rule have equal priority in your encoding. Ensure AASM is `2`
  and APA-benzo is `1`.

---

## Section 6 — Python wrapper: parse the new verdict output

- [x] **Status** — Added `Verdict` enum (`enum.Enum` with string values) and `_VERDICT_LINE_RE` regex; replaced `contradiction_proven` with `verdict`/`verdict_detail` fields on `VerificationResult` (early-return error paths now set `verdict=None, verdict_detail=""`); `_run_lean` now concatenates `CORE_LEAN_SOURCE + "\n\n" + scenario.lean_code`; `_parse_verdict` returns the **last** matching `VERDICT:` line (the core's smoke `#eval` always emits one before the scenario fragment runs, so the scenario verdict is always the final match).

**Goal.** Update `app.py` to (a) concatenate `CORE_LEAN_SOURCE` with the
scenario fragment before invoking Lean, (b) parse the four-state `VERDICT:`
marker emitted by Lean, and (c) replace the `contradiction_proven` boolean
on `VerificationResult` with a `verdict` field.

**Files affected.** `app.py`

**Tasks.**
1. Read `app.py` end to end. Pay particular attention to `_run_lean`,
   `VerificationResult`, and any references to `contradiction_proven` or
   `polypharmacy_collision`.
2. Add an enum (or `typing.Literal`) named `Verdict` with exactly four
   members: `Recommended`, `Underdetermined`, `InsufficientData`,
   `GenuineConflict`. Place it near the top of the file.
3. Update `VerificationResult` to:
   - Remove `contradiction_proven: bool`.
   - Add `verdict: Verdict | None` (None when Lean produced no marker).
   - Add `verdict_detail: str` (the rest of the marker line, e.g.
     `"HoldThiazideAndRehydrate"`).
4. Update `_run_lean` to:
   - Import `CORE_LEAN_SOURCE` from `scenarios`.
   - Concatenate `CORE_LEAN_SOURCE + "\n\n" + scenario.lean_code` and write
     the result to `audit.lean` in the tempdir.
   - After the subprocess runs, scan stdout line by line for a line
     matching `^VERDICT: (\w+)(?:\s+(.*))?$`. The first capture group is
     the verdict tag; the second (optional) is the detail.
   - Map the tag to a `Verdict` enum member (case-sensitive). If no line
     matches, set `verdict=None` and `verdict_detail=""`.
5. Remove every reference to `contradiction_proven` and
   `polypharmacy_collision` from the file. Grep to confirm.
6. The 60-second subprocess timeout, the `tempfile.TemporaryDirectory`
   handling, the exit-code-and-stderr error path, and the
   compiler-missing warning all stay as they are.

**Acceptance criteria.**
- `uv run python -c "import app"` succeeds.
- `grep -n contradiction_proven app.py` returns nothing.
- `grep -n polypharmacy_collision app.py` returns nothing.
- A manual call against Scenario A returns `verdict = Verdict.Recommended`
  and `verdict_detail = "HoldThiazideAndRehydrate"`. Verify with:

  ```bash
  uv run python -c "
  from app import _run_lean
  from scenarios import SCENARIOS
  r = _run_lean(SCENARIOS['scenario-a'])
  print(r.verdict, repr(r.verdict_detail))
  print('exit:', r.exit_code)
  "
  ```

**Notes.**
- The template layer still depends on the old field name in this section.
  That breakage is fixed in Section 7. Do not try to fix templates here.
- Do not invent additional verdict states or detail formats. The four
  states are settled.

---

## Section 7 — Templates: render the four verdict states

- [x] **Status** — Replaced `contradiction_proven` block in `_verification_result.html` with five-branch `result.verdict.name`-switched block (`Recommended` → new `alert-success`/check-circle, `Underdetermined` → existing `alert-info`, `InsufficientData` → `alert-warning`, `GenuineConflict` → `alert-danger`, `None` fallback → `alert-warning` "No Verdict Produced"); detail strings rendered inline as `<code>`; terminal stdout/stderr block preserved verbatim; added `--success`/`--success-soft`/`--success-border` CSS variables (light and dark) plus an `.alert-success` rule in `static/styles.css`; `_scenario_panel.html` had no `contradiction_proven`/`collision_summary` references so was left untouched (static prose deferred to Sections 8/9); verified all three scenarios via running `uv run uvicorn app:app` and posting to `/scenarios/{a,b,c}/verify` — each returns the green Recommended banner with the correct action and the live `lean` terminal output.

**Goal.** Update the HTMX result fragment so it renders all four verdict
states with appropriate visual styling, replacing the old three-banner
(`alert-danger` / `alert-info` / `alert-warning`) layout. Also update any
other template that references the old `contradiction_proven` field.

**Files affected.**
- `templates/_verification_result.html`
- `templates/_scenario_panel.html` (only if it still references the old
  field)
- `static/styles.css` (only if you introduce new banner classes)

**Tasks.**
1. Read `templates/_verification_result.html`, `templates/_scenario_panel.html`,
   and `static/styles.css` end to end before editing.
2. Replace the `contradiction_proven`-conditional block in
   `_verification_result.html` with a `verdict`-switched block that renders
   one of:
   - `Recommended` → positive/green banner. Body: "Verifier returned a
     single recommended action: `<verdict_detail>`."
   - `Underdetermined` → neutral/blue banner. Body: "Verifier returned
     multiple acceptable actions: `<verdict_detail>`."
   - `InsufficientData` → amber/warning banner. Body: "Chart lacks
     observations needed to decide. Missing: `<verdict_detail>`."
   - `GenuineConflict` → red/danger banner. Body: "Guidelines genuinely
     conflict on this patient. Conflicting rules: `<verdict_detail>`."
   - No verdict (None) → keep the existing warning banner used when the
     compiler is missing or times out.
3. Preserve the live `lean` stdout/stderr terminal block — that stays
   regardless of verdict.
4. If `_scenario_panel.html` references `contradiction_proven` or contains
   the words "collision" / "contradiction proven" in template logic
   (not in static prose — that gets handled in Sections 8 and 9), update
   it.
5. Add CSS classes to `static/styles.css` for any new banner colours you
   introduce. Keep the existing `alert-*` naming convention. Verify the
   classes work in both light and dark mode (`prefers-color-scheme`).
6. Start the app and click through all three scenarios manually:

   ```bash
   uv run uvicorn app:app --host 127.0.0.1 --port 8000
   ```

   Confirm each renders with a visually distinct, correctly-styled banner
   in both colour schemes.

**Acceptance criteria.**
- `grep -rn contradiction_proven templates static` returns nothing.
- All three scenarios render their expected verdict banner in the running
  app.
- No JavaScript was added (the project is HTMX-only).
- Light and dark modes both render correctly.

**Notes.**
- The terminal stdout/stderr block must remain. Users want to see the raw
  `lean` output even when the verdict is clean — it is part of the
  "verifiable" framing.
- Do not attempt to render the verdict detail as a clickable link or with
  JavaScript-driven interactivity. Plain text is correct.

---

## Section 8 — `scenarios.py`: rename the collision framing

- [x] **Status** — Renamed `Scenario.collision_summary` → `Scenario.verdict_summary` in the dataclass and updated all three scenario constants with the suggested prose templates verbatim (using Unicode escapes for the curly quotes and `≥`/`—`); `_scenario_panel.html` does not reference the field so was left untouched (Section 7 status note already records this); per the explicit grep acceptance criterion I also renamed the single occurrence in `README.md`'s data model snippet (line 117, field name + comment only — broader README rewrite is Section 9), so README.md was edited despite not being in this section's "Files affected" list; verified all three panels and the index render HTTP 200 via `uv run uvicorn app:app` on port 8765; only remaining `collision_summary` references project-wide are in `PLAN.md` itself, which describes the rename work.

**Goal.** The `Scenario` dataclass currently has a `collision_summary` field
that no longer matches the new system. Rename it to `verdict_summary` and
update each scenario's text to describe the *verdict* the verifier produces
rather than the no-longer-existent collision.

**Files affected.**
- `scenarios.py`
- Any template that references `collision_summary` (probably
  `_scenario_panel.html`)

**Tasks.**
1. Read the current `Scenario` dataclass and the three scenario constants.
2. Rename `Scenario.collision_summary` → `Scenario.verdict_summary` in the
   dataclass definition.
3. For each of `SCENARIO_A`, `SCENARIO_B`, `SCENARIO_C`, replace the field's
   text with a 1–2 sentence description of the actual verdict. Suggested
   templates:

   - **A:** "The KDIGO acute-volume rule has higher priority than the
     AHA/ACC chronic-management rule in this hemodynamic context, so the
     verifier recommends holding the thiazide and rehydrating. The earlier
     'collision' was an artifact of the previous encoding, which omitted
     hemodynamic context."

   - **B:** "The ADA insulin recommendation is conditioned on serum
     potassium ≥ 3.3 mEq/L — a precondition that exists in the published
     ADA guideline itself. With measured K of 2.9 mEq/L the ADA rule does
     not fire, the AACE/ACE rule does, and the verifier recommends
     potassium repletion before insulin. There is no real conflict in the
     literature; the previous encoding manufactured one by dropping the
     ADA precondition."

   - **C:** "The AASM contraindication on benzodiazepines in untreated
     severe OSA defeats the APA's benzodiazepine option (priority 2 > 1).
     A non-benzo anxiolytic remains a valid first-line APA option, so the
     verifier recommends that alternative. The earlier 'collision' assumed
     benzos were the only acceptable APA recommendation, which the actual
     APA guideline does not assert."

4. Update `templates/_scenario_panel.html` (or any other template
   referencing `collision_summary`) to use the new field name. Update any
   surrounding labels that say "collision" or "contradiction" to say
   "verdict" or "expected verdict".
5. Do not edit `guideline_a.body`, `guideline_b.body`, `patient_summary`,
   `title`, or `subtitle`. The natural-language guideline excerpts stay
   accurate; only the framing changes.

**Acceptance criteria.**
- `grep -rn collision_summary .` returns nothing under the project root
  (excluding `.venv` and `__pycache__`).
- The scenario panel renders the new summary text for all three scenarios.
- The Python module imports cleanly.

**Notes.**
- The `subtitle` fields ("Thiazide diuretic — recommended and
  contraindicated", etc.) describe the *clinical tension* the system now
  resolves. They are still accurate and stay.
- Do not delete the field — the panel UI uses it. Renaming only.

---

## Section 9 — README rewrite

- [ ] **Status**

**Goal.** The README markets the system as proving guideline collisions.
Reframe it to describe the new verdict engine without overclaiming what
the formalism delivers.

**Files affected.** `README.md`

**Tasks.**
1. Read the current `README.md` end to end.
2. Update the opening paragraph. Suggested replacement (refine if you can,
   but stay within the actual capabilities):

   > A local proof-of-concept that translates clinical guidelines into a
   > deeply-embedded Lean 4 DSL with deontic modality, contextual
   > preconditions, and priority-based defeasible reasoning, then asks the
   > Lean kernel to typecheck and reduce a `Verdict` computation for each
   > patient scenario. The verifier returns one of four states —
   > `Recommended`, `Underdetermined`, `InsufficientData`, or
   > `GenuineConflict` — surfacing whether the encoded rules unambiguously
   > recommend an action, leave room for clinician choice, lack the chart
   > data needed to decide, or genuinely disagree.

3. Replace the verification-pipeline section ("How it works") to describe
   the new flow:
   `CORE_LEAN_SOURCE` + scenario fragment → `audit.lean` → `lean` → parse
   `VERDICT:` marker → four-state `VerificationResult`.
4. Replace the "Adding a new scenario" section to describe the new shape:
   define `rules` and `chart` in the scenario's `lean_code`, set the
   expected verdict in `verdict_summary`, optionally add a regression check
   in `scripts/check_scenarios.py` (Section 10).
5. Remove all references to `polypharmacy_collision`, `contradiction_proven`,
   "guideline collision gallery," and "proves that the encoded guidelines
   are mutually inconsistent." These claims no longer match the system.
6. Add a short **Limitations** section that acknowledges:
   - The DSL is hand-curated; there is no automatic translation from
     natural-language guidelines to `Rule` definitions. Encoder discipline
     is the dominant correctness constraint.
   - Defeasibility is implemented as naive numeric priority, not a
     real argumentation framework (ASPIC+, defeasible logic programming,
     etc.).
   - There is no separate soundness theorem for `evaluate`. The
     verification claim is "the Lean kernel typechecks the function
     definition and reduces it to a concrete verdict per scenario."
   - Two-tier external-solver architecture (e.g., ASP solver emitting a
     Lean-checkable certificate) is deferred until after demo stage.
7. Leave the Stack table, Prerequisites, Quick start, Project layout,
   License, and "Common dev tasks" sections largely intact. Update only
   the parts that referenced the old contradiction-based pipeline.

**Acceptance criteria.**
- README contains no references to "collision," "contradiction proven,"
  "polypharmacy_collision," or "mutually inconsistent."
- The new Limitations section is present.
- A reader who has not seen the audit conversation can understand what
  the system does and what it does not claim.

**Notes.**
- Do not mention the audit conversation, the previous version, or "the
  flaw we fixed." The README is for new readers, not a changelog.
- Do not add screenshots, badges, or other documentation cruft.

---

## Section 10 — Lean regression harness

- [ ] **Status**

**Goal.** A small Python harness that runs all scenarios through `_run_lean`
and asserts each produces its expected verdict. Replaces the implicit
"contradiction_proven for all three" sanity check from the old README.

**Files affected.**
- New file: `scripts/check_scenarios.py` (create the `scripts/` directory
  if it does not exist)
- `README.md` (add one line under "Common dev tasks")

**Tasks.**
1. Create `scripts/` if it does not exist.
2. Create `scripts/check_scenarios.py` with the following structure:
   - Imports: `from app import _run_lean, Verdict` and
     `from scenarios import SCENARIOS`.
   - A module-level `EXPECTED: dict[str, tuple[Verdict, str]]` mapping
     each scenario id to its expected `(verdict, detail)`. Populate with:

     ```python
     EXPECTED = {
         "scenario-a": (Verdict.Recommended, "HoldThiazideAndRehydrate"),
         "scenario-b": (Verdict.Recommended, "RepleteKThenStartInsulin"),
         "scenario-c": (Verdict.Recommended, "NonBenzoAnxiolytic"),
     }
     ```

   - A `main()` that iterates over `EXPECTED`, runs `_run_lean` on each
     scenario, compares the result to the expected tuple, prints
     `PASS scenario-x` or `FAIL scenario-x: got=... expected=...` per
     scenario, and exits 0 if all pass, 1 otherwise.
   - A `if __name__ == "__main__": main()` guard.
3. Run the script and confirm three `PASS` lines and exit 0:

   ```bash
   uv run python scripts/check_scenarios.py
   ```

4. Add a one-liner to the README's "Common dev tasks" section:

   ```bash
   # Run the regression harness
   uv run python scripts/check_scenarios.py
   ```

5. Sanity-check the failure path by temporarily mutating one expected
   verdict (e.g., change `"HoldThiazideAndRehydrate"` to `"WrongAction"`),
   re-running, observing exit 1 and a clear FAIL line, then **reverting**
   the change.

**Acceptance criteria.**
- `uv run python scripts/check_scenarios.py` exits 0 with three PASS lines
  on a clean checkout.
- The deliberate-mutation sanity check produced a FAIL and exit 1, and was
  reverted.
- README's "Common dev tasks" section includes the new invocation.

**Notes.**
- Do not add a test framework dependency. Plain `assert` or hand-written
  comparison plus `sys.exit` is correct for this scale.
- This is the final section. Once it passes on a clean checkout, the three
  legacy "collision" scenarios have been fully replaced by clinically
  correct verdicts and the project's verification claim has been brought
  in line with what the formalism actually delivers.
