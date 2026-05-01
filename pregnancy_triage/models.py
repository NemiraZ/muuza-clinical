"""
Data models for the Muuza Pregnancy Triage tool.
All types are plain dataclasses — no external dependencies.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class RiskLevel(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

    def __gt__(self, other: "RiskLevel") -> bool:
        return _RISK_ORDER.index(self) > _RISK_ORDER.index(other)

    def __ge__(self, other: "RiskLevel") -> bool:
        return self == other or self > other

    def __lt__(self, other: "RiskLevel") -> bool:
        return _RISK_ORDER.index(self) < _RISK_ORDER.index(other)

    def __le__(self, other: "RiskLevel") -> bool:
        return self == other or self < other


_RISK_ORDER = [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH]


class RecommendedAction(Enum):
    MONITOR_HOME    = "Monitor at home — note symptoms and report at next midwife contact"
    CONTACT_MIDWIFE = "Contact your midwife (non-urgent, within 24 hours)"
    SEE_GP_TODAY    = "Arrange a same-day appointment with your GP or midwife today"
    MATERNITY_TRIAGE = "Attend maternity triage or assessment unit today"
    AE_999          = "Call 999 or go to A&E immediately"


@dataclass
class ClinicalFinding:
    """One assessed clinical finding with its risk contribution and rationale."""
    rule_name: str          # internal rule identifier (for audit trail)
    symptom: str            # short display label
    detail: str             # specific detail from the patient context
    risk: RiskLevel
    reasoning: str          # clinician-readable rationale
    nice_ref: str           # NICE guideline reference
    patient_summary: str    # one sentence in plain language for the patient


@dataclass
class PatientContext:
    """All inputs gathered from the questionnaire or UI form."""
    weeks: int
    days: int = 0

    # --- Bleeding ---
    has_bleeding: bool = False
    bleeding_amount: str = "none"   # "spots" | "light" | "heavy" | "soaking"
    bleeding_with_clots: bool = False

    # --- Pain ---
    has_pain: bool = False
    pain_severity: int = 0          # 1–10
    pain_location: str = ""         # "lower_abdomen" | "upper_abdomen" | "one_sided" | "shoulder_tip" | "generalised"
    pain_character: str = ""        # "cramping" | "constant" | "sharp" | "pressure"
    shoulder_tip_pain: bool = False

    # --- Nausea / vomiting ---
    has_nausea: bool = False
    vomiting_frequency: int = 0     # times in past 24 h
    unable_to_keep_fluids: bool = False

    # --- Discharge ---
    has_discharge_change: bool = False
    discharge_colour: str = ""      # "clear_white" | "yellow_green" | "grey" | "pink_brown" | "watery"
    discharge_odour: bool = False
    has_itching: bool = False       # generalised itching (obstetric cholestasis screen)

    # --- Fetal movements (≥24 weeks) ---
    reduced_movements: Optional[bool] = None

    # --- Systemic / red-flag ---
    headache_severe: bool = False
    visual_disturbance: bool = False
    facial_hand_swelling: bool = False
    fever: bool = False
    fever_temp: float = 0.0
    chest_pain: bool = False
    breathlessness: bool = False
    dizziness: bool = False
    seizure: bool = False
    trauma: bool = False

    # --- Fluid / membranes ---
    fluid_gush: bool = False

    @property
    def trimester(self) -> int:
        if self.weeks <= 12:
            return 1
        if self.weeks <= 27:
            return 2
        return 3

    @property
    def gestation_label(self) -> str:
        return f"{self.weeks}+{self.days} weeks"


@dataclass
class AssessmentResult:
    """Final output of the risk assessment."""
    risk_level: RiskLevel
    action: RecommendedAction
    findings: list[ClinicalFinding] = field(default_factory=list)
    patient_explanation: str = ""
    safety_net_advice: list[str] = field(default_factory=list)

    @property
    def triggered_rules(self) -> list[str]:
        return [f.rule_name for f in self.findings]

    @property
    def highest_risk_finding(self) -> Optional[ClinicalFinding]:
        if not self.findings:
            return None
        return max(self.findings, key=lambda f: _RISK_ORDER.index(f.risk))
