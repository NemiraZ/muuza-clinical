"""
Output renderers for the Muuza Pregnancy Triage tool.

Provides:
  - patient_friendly_explanation()  — plain-language summary string
  - build_safety_net()              — list of safety-net advice strings
  - render_terminal()               — coloured terminal output
"""

from __future__ import annotations
import textwrap
from .models import (
    AssessmentResult, PatientContext, RiskLevel, RecommendedAction,
)


# ---------------------------------------------------------------------------
# Patient-friendly explanation
# ---------------------------------------------------------------------------

_PATIENT_EXPLANATIONS: dict[RiskLevel, str] = {
    RiskLevel.LOW: (
        "Your symptoms appear to be within the range of changes that can "
        "occur in normal pregnancy. We recommend monitoring at home and "
        "mentioning these symptoms at your next midwife appointment. "
        "If anything changes or becomes more severe, contact your midwife "
        "or GP promptly."
    ),
    RiskLevel.MEDIUM: (
        "Some of your symptoms need further assessment by a healthcare "
        "professional. Please contact your GP or midwife today to arrange "
        "a same-day review. Do not wait for your next scheduled appointment. "
        "If your symptoms worsen while waiting, seek more urgent help."
    ),
    RiskLevel.HIGH: (
        "Your symptoms require urgent medical attention. Please seek care "
        "immediately — call 999, attend A&E, or go to your nearest maternity "
        "triage unit as directed below. Do not drive yourself if you feel unwell. "
        "Do not wait to see if symptoms improve."
    ),
}


def patient_friendly_explanation(
    risk: RiskLevel,
    action: RecommendedAction,
) -> str:
    return _PATIENT_EXPLANATIONS[risk]


# ---------------------------------------------------------------------------
# Safety-net advice
# ---------------------------------------------------------------------------

def build_safety_net(ctx: PatientContext, risk: RiskLevel) -> list[str]:
    advice: list[str] = []

    if risk == RiskLevel.LOW:
        advice.append(
            "If any new symptoms develop, or if your existing symptoms worsen, "
            "contact your midwife or GP promptly rather than waiting."
        )
        advice.append(
            "If you experience heavy bleeding, severe pain, dizziness, or "
            "collapse at any time, call 999 immediately."
        )

    if risk == RiskLevel.MEDIUM:
        advice.append(
            "If you cannot be seen today, or if your symptoms worsen significantly "
            "while waiting for an appointment, go to A&E or call 999."
        )

    if ctx.weeks >= 24:
        advice.append(
            "Count your baby's movements every day. If you notice a reduction "
            "in movement at any point, contact your maternity unit immediately "
            "— do not wait until your next appointment."
        )

    if ctx.weeks < 14:
        advice.append(
            "If you develop sudden severe one-sided abdominal pain — with or "
            "without bleeding — seek emergency care immediately to exclude "
            "ectopic pregnancy."
        )

    if ctx.weeks >= 20:
        advice.append(
            "If you develop a severe headache, visual disturbances, or sudden "
            "swelling of the face or hands, seek urgent assessment as these "
            "may be signs of pre-eclampsia."
        )

    advice.append(
        "This tool provides decision support only and does not replace "
        "assessment by a midwife, GP, or obstetrician. Always follow the "
        "advice of your healthcare team."
    )

    return advice


# ---------------------------------------------------------------------------
# Terminal renderer (coloured)
# ---------------------------------------------------------------------------

_RISK_COLOUR = {
    RiskLevel.LOW:    "\033[92m",   # green
    RiskLevel.MEDIUM: "\033[93m",   # yellow
    RiskLevel.HIGH:   "\033[91m",   # red
}
_RESET = "\033[0m"
_BOLD  = "\033[1m"


def _divider() -> None:
    print("  " + "═" * 62)


def render_terminal(result: AssessmentResult) -> None:
    _divider()
    colour = _RISK_COLOUR.get(result.risk_level, "")

    print()
    print(f"  {_BOLD}ASSESSMENT RESULT{_RESET}")
    print()
    print(f"  Risk level : {colour}{_BOLD}{result.risk_level.value}{_RESET}")
    print(f"  Action     : {_BOLD}{result.action.value}{_RESET}")
    print()

    _divider()
    print(f"  {_BOLD}FOR THE PATIENT{_RESET}")
    print()
    for line in textwrap.wrap(result.patient_explanation, width=62):
        print(f"  {line}")
    print()

    if result.findings:
        _divider()
        print(f"  {_BOLD}CLINICAL FINDINGS & REASONING  ({len(result.findings)} rule(s) triggered){_RESET}")
        print()
        for i, f in enumerate(result.findings, start=1):
            fc = _RISK_COLOUR.get(f.risk, "")
            print(f"  {i}. [{fc}{f.risk.value}{_RESET}]  {_BOLD}{f.symptom}{_RESET}")
            print(f"     Rule      : {f.rule_name}")
            if f.detail:
                print(f"     Detail    : {f.detail}")
            reasoning_wrapped = textwrap.fill(
                f.reasoning, width=60,
                initial_indent="     Reasoning : ",
                subsequent_indent="               ",
            )
            print(reasoning_wrapped)
            print(f"     NICE ref  : {f.nice_ref}")
            print()

    if result.safety_net_advice:
        _divider()
        print(f"  {_BOLD}SAFETY-NET ADVICE{_RESET}")
        print()
        for item in result.safety_net_advice:
            wrapped = textwrap.fill(
                item, width=62,
                initial_indent="  • ",
                subsequent_indent="    ",
            )
            print(wrapped)
        print()

    _divider()
    print(
        textwrap.fill(
            "  DISCLAIMER: This output is for clinical decision support only. "
            "It does not replace professional assessment or examination. "
            "Always follow current NICE guidelines and local clinical protocols.",
            width=68,
        )
    )
    _divider()
