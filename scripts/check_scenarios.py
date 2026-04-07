"""Regression harness: assert each scenario's Lean theorem typechecks.

For every entry in :data:`EXPECTED` we invoke the Lean compiler on the
scenario's static ``.lean`` file (via :func:`app._run_lean`) and check
that:

  * the verdict is :class:`app.Verdict.CollisionVerified`,
  * the dependency list extracted from ``#print axioms absurd`` is exactly
    the expected set of guideline + observation axioms (no ``sorryAx``,
    no extras), and
  * the compiler exit code is zero.
"""

from __future__ import annotations

import sys

from app import Verdict, _run_lean
from scenarios import SCENARIOS

EXPECTED: dict[str, frozenset[str]] = {
    "scenario-a": frozenset({
        "AHA_ACC_HTN_8_1_5",
        "KDIGO_AKI_3_1_2",
        "incompatible_modalities",
        "JohnDoe",
        "obs_essential_hypertension",
        "obs_severe_dehydration",
    }),
    "scenario-b": frozenset({
        "ADA_DKA_Sec16",
        "AACE_ACE_CSR4",
        "incompatible_modalities",
        "JaneRoe",
        "obs_diabetic_ketoacidosis",
        "obs_severe_hypokalemia",
    }),
    "scenario-c": frozenset({
        "APA_Panic_Acute",
        "AASM_OSA_PharmSafety",
        "incompatible_modalities",
        "RichardRoe",
        "obs_acute_panic_episode",
        "obs_untreated_severe_osa",
    }),
}


def main() -> int:
    failures = 0
    for sid, expected_axioms in EXPECTED.items():
        scenario = SCENARIOS[sid]
        result = _run_lean(scenario)
        actual_axioms = frozenset(result.trusted_axioms)
        if (
            result.verdict == Verdict.CollisionVerified
            and actual_axioms == expected_axioms
            and result.exit_code == 0
        ):
            print(f"PASS {sid}  (axioms={sorted(actual_axioms)})")
            continue
        failures += 1
        print(f"FAIL {sid}")
        print(f"  verdict   = {result.verdict}")
        print(f"  exit_code = {result.exit_code}")
        print(f"  axioms    = {sorted(actual_axioms)}")
        print(f"  expected  = {sorted(expected_axioms)}")
        if result.error_message:
            print(f"  error     = {result.error_message}")
        if result.stdout:
            print("  --- stdout ---")
            print(result.stdout)
        if result.stderr:
            print("  --- stderr ---")
            print(result.stderr)
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
