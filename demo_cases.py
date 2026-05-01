#!/usr/bin/env python3
"""
Demo cases for the Muuza Pregnancy Triage tool.

Runs 10 clinical scenarios through the engine and prints results.
Includes expected risk level for each case as a sanity check.

Usage:
    python3 demo_cases.py
"""

from __future__ import annotations
import sys
import textwrap
from pregnancy_triage import PatientContext, ClinicalEngine, RiskLevel, RecommendedAction
from pregnancy_triage.renderers import _RISK_COLOUR, _RESET, _BOLD

engine = ClinicalEngine()

_RISK_LABEL_COLOUR = {
    RiskLevel.LOW:    "\033[92m",
    RiskLevel.MEDIUM: "\033[93m",
    RiskLevel.HIGH:   "\033[91m",
}


def _banner(n: int, title: str) -> None:
    print()
    print("  " + "═" * 64)
    print(f"  {_BOLD}CASE {n}: {title}{_RESET}")
    print("  " + "═" * 64)


def _show(result, expected: RiskLevel) -> None:
    colour = _RISK_LABEL_COLOUR.get(result.risk_level, "")
    match = "PASS" if result.risk_level == expected else "FAIL"
    match_colour = "\033[92m" if match == "PASS" else "\033[91m"
    print(
        f"  Risk level : {colour}{_BOLD}{result.risk_level.value}{_RESET}  "
        f"(expected: {expected.value})  "
        f"{match_colour}{_BOLD}{match}{_RESET}"
    )
    print(f"  Action     : {result.action.value}")
    print()
    print(f"  {_BOLD}Patient guidance:{_RESET}")
    for line in textwrap.wrap(result.patient_explanation, 64):
        print(f"    {line}")
    print()
    print(f"  {_BOLD}Triggered rules:{_RESET}")
    for rule_name in result.triggered_rules:
        print(f"    • {rule_name}")
    print()
    print(f"  {_BOLD}Findings:{_RESET}")
    for f in result.findings:
        fc = _RISK_LABEL_COLOUR.get(f.risk, "")
        print(f"    [{fc}{f.risk.value}{_RESET}] {f.symptom}")
    print()
    if result.safety_net_advice:
        print(f"  {_BOLD}Safety-net advice:{_RESET}")
        for item in result.safety_net_advice:
            wrapped = textwrap.fill(item, 62, initial_indent="    • ", subsequent_indent="      ")
            print(wrapped)


def run_demo_cases() -> int:
    """Run all cases. Returns number of failures."""
    failures = 0

    # -----------------------------------------------------------------
    # Case 1: Mild nausea only at 8 weeks
    # Expected: LOW
    # -----------------------------------------------------------------
    _banner(1, "Mild nausea only — 8 weeks")
    ctx = PatientContext(
        weeks=8,
        has_nausea=True,
        vomiting_frequency=1,
    )
    result = engine.assess(ctx)
    expected = RiskLevel.LOW
    _show(result, expected)
    if result.risk_level != expected:
        failures += 1

    # -----------------------------------------------------------------
    # Case 2: Increased clear/white discharge, no odour, no red flags
    # Expected: LOW
    # -----------------------------------------------------------------
    _banner(2, "Increased clear/white discharge, no red flags — 16 weeks")
    ctx = PatientContext(
        weeks=16,
        has_discharge_change=True,
        discharge_colour="clear_white",
        discharge_odour=False,
    )
    result = engine.assess(ctx)
    expected = RiskLevel.LOW
    _show(result, expected)
    if result.risk_level != expected:
        failures += 1

    # -----------------------------------------------------------------
    # Case 3: Smelly discharge + itching at 20 weeks
    # Expected: MEDIUM
    # -----------------------------------------------------------------
    _banner(3, "Smelly yellow discharge + itching — 20 weeks")
    ctx = PatientContext(
        weeks=20,
        has_discharge_change=True,
        discharge_colour="yellow_green",
        discharge_odour=True,
        has_itching=True,
    )
    result = engine.assess(ctx)
    expected = RiskLevel.MEDIUM
    _show(result, expected)
    if result.risk_level != expected:
        failures += 1

    # -----------------------------------------------------------------
    # Case 4: Spotting only at 7 weeks, no pain, no other symptoms
    # Expected: LOW
    # -----------------------------------------------------------------
    _banner(4, "Spotting only — 7 weeks")
    ctx = PatientContext(
        weeks=7,
        has_bleeding=True,
        bleeding_amount="spots",
    )
    result = engine.assess(ctx)
    expected = RiskLevel.LOW
    _show(result, expected)
    if result.risk_level != expected:
        failures += 1

    # -----------------------------------------------------------------
    # Case 5: Spotting + one-sided pain at 8 weeks (ectopic concern)
    # Expected: HIGH
    # -----------------------------------------------------------------
    _banner(5, "Spotting + one-sided pain — 8 weeks (possible ectopic)")
    ctx = PatientContext(
        weeks=8,
        has_bleeding=True,
        bleeding_amount="spots",
        has_pain=True,
        pain_severity=5,
        pain_location="one_sided",
        pain_character="sharp",
    )
    result = engine.assess(ctx)
    expected = RiskLevel.HIGH
    _show(result, expected)
    if result.risk_level != expected:
        failures += 1

    # -----------------------------------------------------------------
    # Case 6: Heavy bleeding at 22 weeks
    # Expected: HIGH
    # -----------------------------------------------------------------
    _banner(6, "Heavy vaginal bleeding — 22 weeks")
    ctx = PatientContext(
        weeks=22,
        has_bleeding=True,
        bleeding_amount="heavy",
    )
    result = engine.assess(ctx)
    expected = RiskLevel.HIGH
    _show(result, expected)
    if result.risk_level != expected:
        failures += 1

    # -----------------------------------------------------------------
    # Case 7: Severe abdominal pain (9/10) at 18 weeks
    # Expected: HIGH
    # -----------------------------------------------------------------
    _banner(7, "Severe abdominal pain 9/10 — 18 weeks")
    ctx = PatientContext(
        weeks=18,
        has_pain=True,
        pain_severity=9,
        pain_location="lower_abdomen",
        pain_character="constant",
    )
    result = engine.assess(ctx)
    expected = RiskLevel.HIGH
    _show(result, expected)
    if result.risk_level != expected:
        failures += 1

    # -----------------------------------------------------------------
    # Case 8: Shoulder-tip pain + dizziness at 9 weeks
    # Expected: HIGH
    # -----------------------------------------------------------------
    _banner(8, "Shoulder-tip pain + dizziness — 9 weeks")
    ctx = PatientContext(
        weeks=9,
        has_pain=True,
        pain_severity=6,
        pain_location="one_sided",
        pain_character="sharp",
        shoulder_tip_pain=True,
        dizziness=True,
    )
    result = engine.assess(ctx)
    expected = RiskLevel.HIGH
    _show(result, expected)
    if result.risk_level != expected:
        failures += 1

    # -----------------------------------------------------------------
    # Case 9: Fluid leakage at 28 weeks (PPROM)
    # Expected: HIGH
    # -----------------------------------------------------------------
    _banner(9, "Sudden fluid leakage — 28 weeks (possible PPROM)")
    ctx = PatientContext(
        weeks=28,
        fluid_gush=True,
    )
    result = engine.assess(ctx)
    expected = RiskLevel.HIGH
    _show(result, expected)
    if result.risk_level != expected:
        failures += 1

    # -----------------------------------------------------------------
    # Case 10: Reduced fetal movements at 32 weeks
    # Expected: HIGH / maternity triage
    # -----------------------------------------------------------------
    _banner(10, "Reduced fetal movements — 32 weeks")
    ctx = PatientContext(
        weeks=32,
        reduced_movements=True,
    )
    result = engine.assess(ctx)
    expected = RiskLevel.HIGH
    _show(result, expected)
    if result.risk_level != expected:
        failures += 1
    if result.action != RecommendedAction.MATERNITY_TRIAGE:
        print(f"  ACTION FAIL — expected MATERNITY_TRIAGE, got {result.action}")
        failures += 1

    # -----------------------------------------------------------------
    # Summary
    # -----------------------------------------------------------------
    print()
    print("  " + "═" * 64)
    total = 10
    passed = total - failures
    if failures == 0:
        print(f"  \033[92m\033[1mAll {total} demo cases passed.\033[0m")
    else:
        print(f"  \033[91m\033[1m{failures} of {total} demo cases FAILED.\033[0m")
    print("  " + "═" * 64)
    print()

    return failures


if __name__ == "__main__":
    failures = run_demo_cases()
    sys.exit(failures)
