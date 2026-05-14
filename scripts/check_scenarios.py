"""Regression harness. For every entry in ``EXPECTED``, runs ``app._run_lean`` and asserts: verdict == ``CollisionVerified``; the ``#print axioms absurd`` list matches expected exactly (no ``sorryAx``, no extras); exit code 0. Both locales pinned — EN against AHA/KDIGO/ADA/APA/AASM identifiers, JA against ``«…»``-quoted kanji identifiers."""

from __future__ import annotations

import sys

from app import Verdict, _run_lean
from i18n import SUPPORTED_LOCALES
from scenarios import get_scenarios

EXPECTED: dict[str, dict[str, frozenset[str]]] = {
    "en": {
        "scenario-a": frozenset({
            "AHA_ACC_HTN_8_1_6",
            "KDIGO_AKI_3_4",
            "incompatible_modalities",
            "JohnDoe",
            "obs_essential_hypertension",
            "obs_severe_dehydration",
        }),
        "scenario-b": frozenset({
            "ADA_DKA_Sec16",
            "ADA_DKA_Sec16_KSafety",
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
            "«高血圧2019_第5章_第一選択»",
            "«腎臓AKI2016_利尿薬»",
            "«治療法の両立不能性»",
            "«山田太郎»",
            "«所見_本態性高血圧»",
            "«所見_重症脱水»",
        }),
        "scenario-b": frozenset({
            "«糖尿病2024_第20_1項_DKA»",
            "«糖尿病2024_第20_1項_K管理»",
            "«治療法の両立不能性»",
            "«鈴木花子»",
            "«所見_糖尿病性ケトアシドーシス»",
            "«所見_重症低カリウム血症»",
        }),
        "scenario-c": frozenset({
            "«不安症神経精神薬理パニック症2025_急性期»",
            "«呼吸器SAS2020_BZD»",
            "«治療法の両立不能性»",
            "«田中一郎»",
            "«所見_急性パニック発作»",
            "«所見_未治療重症OSA»",
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
