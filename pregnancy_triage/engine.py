"""
Clinical engine — applies all rules to a PatientContext and produces an AssessmentResult.
Deterministic: given the same inputs, always produces the same output.
"""

from __future__ import annotations
from .models import (
    PatientContext, AssessmentResult, ClinicalFinding,
    RiskLevel, RecommendedAction, _RISK_ORDER,
)
from .rules import ALL_RULES
from .renderers import patient_friendly_explanation, build_safety_net


class ClinicalEngine:
    """
    Applies ALL_RULES to a PatientContext in a fixed sequence.

    The engine:
      1. Collects all ClinicalFindings from every rule.
      2. Derives the overall risk level as the maximum of all finding risks.
      3. Maps risk level to a RecommendedAction, with specific exceptions
         for obstetric presentations best handled by maternity triage.
      4. Attaches a patient-friendly explanation and safety-net advice.
    """

    def assess(self, ctx: PatientContext) -> AssessmentResult:
        findings: list[ClinicalFinding] = []
        for rule_fn in ALL_RULES:
            findings.extend(rule_fn(ctx))

        overall_risk = self._aggregate_risk(findings)
        action = self._determine_action(ctx, findings, overall_risk)
        explanation = patient_friendly_explanation(overall_risk, action)
        safety_nets = build_safety_net(ctx, overall_risk)

        return AssessmentResult(
            risk_level=overall_risk,
            action=action,
            findings=findings,
            patient_explanation=explanation,
            safety_net_advice=safety_nets,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _aggregate_risk(findings: list[ClinicalFinding]) -> RiskLevel:
        if not findings:
            return RiskLevel.LOW
        return max(
            (f.risk for f in findings),
            key=lambda r: _RISK_ORDER.index(r),
        )

    @staticmethod
    def _determine_action(
        ctx: PatientContext,
        findings: list[ClinicalFinding],
        overall_risk: RiskLevel,
    ) -> RecommendedAction:
        if overall_risk == RiskLevel.HIGH:
            # Some HIGH-risk presentations are best assessed at maternity triage
            # rather than a general A&E.
            maternity_triage_rules = {
                "REDUCED_FETAL_MOVEMENTS",
                "ROM_AT_TERM",
                "BLEEDING_APH",
            }
            high_rule_names = {
                f.rule_name for f in findings if f.risk == RiskLevel.HIGH
            }
            if high_rule_names and high_rule_names.issubset(maternity_triage_rules):
                return RecommendedAction.MATERNITY_TRIAGE
            return RecommendedAction.AE_999

        if overall_risk == RiskLevel.MEDIUM:
            return RecommendedAction.SEE_GP_TODAY

        return RecommendedAction.MONITOR_HOME
