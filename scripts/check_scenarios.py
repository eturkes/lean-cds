"""Regression harness: assert each scenario's Lean theorem typechecks.

For every entry in :data:`EXPECTED` we invoke the Lean compiler on the
scenario's static ``.lean`` file (via :func:`app._run_lean`) and check
that:

  * the verdict is :class:`app.Verdict.CollisionVerified`,
  * the dependency list extracted from ``#print axioms absurd`` is exactly
    the expected set of guideline + observation axioms (no ``sorryAx``,
    no extras), and
  * the compiler exit code is zero.

Both locales are exercised — the EN build pins the AHA / KDIGO / ADA /
AACE / APA / AASM axiom names against ``JohnDoe / JaneRoe / RichardRoe``,
and the JA build pins the JSH / JSN / JDS / JSAD-JSNP / JRS axiom names
against ``TaroYamada / HanakoSuzuki / IchiroTanaka``.
"""

from __future__ import annotations

import sys

from app import Verdict, _run_lean
from i18n import SUPPORTED_LOCALES
from scenarios import get_scenarios

EXPECTED: dict[str, dict[str, frozenset[str]]] = {
    "en": {
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
    },
    "ja": {
        "scenario-a": frozenset({
            "JSH2019_Ch5_FirstLine",
            "JSN_AKI2016_Diuretics",
            "incompatible_modalities",
            "TaroYamada",
            "obs_essential_hypertension",
            "obs_severe_dehydration",
        }),
        "scenario-b": frozenset({
            "JDS2024_Sec20_1_DKA",
            "JDS2024_Sec20_1_KMgmt",
            "incompatible_modalities",
            "HanakoSuzuki",
            "obs_diabetic_ketoacidosis",
            "obs_severe_hypokalemia",
        }),
        "scenario-c": frozenset({
            "JSAD_JSNP_Panic2025_Acute",
            "JRS_SAS2020_BZD",
            "incompatible_modalities",
            "IchiroTanaka",
            "obs_acute_panic_episode",
            "obs_untreated_severe_osa",
        }),
    },
}


def main() -> int:
    failures = 0
    for locale in SUPPORTED_LOCALES:
        scenarios = get_scenarios(locale)
        for sid, expected_axioms in EXPECTED[locale].items():
            scenario = scenarios[sid]
            result = _run_lean(scenario)
            actual_axioms = frozenset(result.trusted_axioms)
            label = f"[{locale}] {sid}"
            if (
                result.verdict == Verdict.CollisionVerified
                and actual_axioms == expected_axioms
                and result.exit_code == 0
            ):
                print(f"PASS {label}  (axioms={sorted(actual_axioms)})")
                continue
            failures += 1
            print(f"FAIL {label}")
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
