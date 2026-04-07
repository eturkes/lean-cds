"""Regression harness: assert each scenario produces its expected verdict."""

from __future__ import annotations

import sys

from app import Verdict, _run_lean
from scenarios import SCENARIOS

EXPECTED: dict[str, tuple[Verdict, str]] = {
    "scenario-a": (Verdict.Recommended, "HoldThiazideAndRehydrate"),
    "scenario-b": (Verdict.Recommended, "RepleteKThenStartInsulin"),
    "scenario-c": (Verdict.Recommended, "NonBenzoAnxiolytic"),
}


def main() -> int:
    failures = 0
    for sid, (expected_verdict, expected_detail) in EXPECTED.items():
        scenario = SCENARIOS[sid]
        result = _run_lean(scenario)
        actual = (result.verdict, result.verdict_detail)
        expected = (expected_verdict, expected_detail)
        if actual == expected:
            print(f"PASS {sid}")
        else:
            failures += 1
            print(f"FAIL {sid}: got={actual} expected={expected}")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
