"""
pytest test suite for the Muuza Pregnancy Triage clinical rules.

Each test verifies the expected risk level and, where critical,
the recommended action for a specific clinical scenario.
Tests are named to serve as living documentation of the rule behaviour.
"""

import pytest
from pregnancy_triage import (
    PatientContext,
    ClinicalEngine,
    RiskLevel,
    RecommendedAction,
)
from pregnancy_triage.rules import (
    rule_bleeding,
    rule_pain,
    rule_nausea,
    rule_discharge,
    rule_fetal_movements,
    rule_preeclampsia,
    rule_ectopic_cluster,
    rule_absolute_emergencies,
    rule_itching,
    rule_dizziness,
    rule_fever,
)

engine = ClinicalEngine()


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def assess(ctx: PatientContext):
    return engine.assess(ctx)


# ---------------------------------------------------------------------------
# Demo case 1: mild nausea only at 8 weeks
# ---------------------------------------------------------------------------

class TestMildNauseaOnly:
    def setup_method(self):
        self.ctx = PatientContext(weeks=8, has_nausea=True, vomiting_frequency=1)
        self.result = assess(self.ctx)

    def test_risk_is_low(self):
        assert self.result.risk_level == RiskLevel.LOW

    def test_action_is_monitor_home(self):
        assert self.result.action == RecommendedAction.MONITOR_HOME

    def test_nausea_rule_triggered(self):
        assert "NAUSEA_MILD_VOMITING" in self.result.triggered_rules

    def test_no_high_risk_rules(self):
        assert all(f.risk != RiskLevel.HIGH for f in self.result.findings)


# ---------------------------------------------------------------------------
# Demo case 2: increased clear/white discharge, no odour, no red flags
# ---------------------------------------------------------------------------

class TestClearDischargeNoRedFlags:
    def setup_method(self):
        self.ctx = PatientContext(
            weeks=16,
            has_discharge_change=True,
            discharge_colour="clear_white",
            discharge_odour=False,
        )
        self.result = assess(self.ctx)

    def test_risk_is_low(self):
        assert self.result.risk_level == RiskLevel.LOW

    def test_action_is_monitor_home(self):
        assert self.result.action == RecommendedAction.MONITOR_HOME

    def test_discharge_rule_triggered(self):
        assert "DISCHARGE_CLEAR_INCREASED" in self.result.triggered_rules


# ---------------------------------------------------------------------------
# Demo case 3: smelly discharge + itching at 20 weeks
# ---------------------------------------------------------------------------

class TestSmellyDischargeWithItching:
    def setup_method(self):
        self.ctx = PatientContext(
            weeks=20,
            has_discharge_change=True,
            discharge_colour="yellow_green",
            discharge_odour=True,
            has_itching=True,
        )
        self.result = assess(self.ctx)

    def test_risk_is_medium(self):
        assert self.result.risk_level == RiskLevel.MEDIUM

    def test_action_is_see_gp_today(self):
        assert self.result.action == RecommendedAction.SEE_GP_TODAY

    def test_discharge_colour_rule_triggered(self):
        assert "DISCHARGE_ABNORMAL_COLOUR" in self.result.triggered_rules

    def test_itching_rule_triggered(self):
        assert "ITCHING_EARLY_PREGNANCY" in self.result.triggered_rules


# ---------------------------------------------------------------------------
# Demo case 4: spotting only at 7 weeks, no pain, no other symptoms
# ---------------------------------------------------------------------------

class TestSpottingOnlyAt7Weeks:
    def setup_method(self):
        self.ctx = PatientContext(
            weeks=7,
            has_bleeding=True,
            bleeding_amount="spots",
        )
        self.result = assess(self.ctx)

    def test_risk_is_low(self):
        assert self.result.risk_level == RiskLevel.LOW

    def test_action_is_monitor_home(self):
        assert self.result.action == RecommendedAction.MONITOR_HOME

    def test_spotting_rule_triggered(self):
        assert "SPOTTING_FIRST_TRIMESTER" in self.result.triggered_rules

    def test_no_ectopic_rule_without_pain(self):
        assert "ECTOPIC_CLUSTER" not in self.result.triggered_rules


# ---------------------------------------------------------------------------
# Demo case 5: spotting + one-sided pain at 8 weeks (ectopic concern)
# ---------------------------------------------------------------------------

class TestSpottingWithOneSidedPainAt8Weeks:
    def setup_method(self):
        self.ctx = PatientContext(
            weeks=8,
            has_bleeding=True,
            bleeding_amount="spots",
            has_pain=True,
            pain_severity=5,
            pain_location="one_sided",
            pain_character="sharp",
        )
        self.result = assess(self.ctx)

    def test_risk_is_high(self):
        assert self.result.risk_level == RiskLevel.HIGH

    def test_action_is_ae(self):
        assert self.result.action == RecommendedAction.AE_999

    def test_ectopic_cluster_rule_triggered(self):
        assert "ECTOPIC_CLUSTER" in self.result.triggered_rules


# ---------------------------------------------------------------------------
# Demo case 6: heavy bleeding at any gestation
# ---------------------------------------------------------------------------

class TestHeavyBleeding:
    def setup_method(self):
        self.ctx = PatientContext(
            weeks=22,
            has_bleeding=True,
            bleeding_amount="heavy",
        )
        self.result = assess(self.ctx)

    def test_risk_is_high(self):
        assert self.result.risk_level == RiskLevel.HIGH

    def test_action_is_ae(self):
        assert self.result.action == RecommendedAction.AE_999

    def test_heavy_bleeding_rule_triggered(self):
        assert "BLEEDING_HEAVY" in self.result.triggered_rules


# ---------------------------------------------------------------------------
# Demo case 7: severe abdominal pain (9/10) at 18 weeks
# ---------------------------------------------------------------------------

class TestSevereAbdominalPain:
    def setup_method(self):
        self.ctx = PatientContext(
            weeks=18,
            has_pain=True,
            pain_severity=9,
            pain_location="lower_abdomen",
            pain_character="constant",
        )
        self.result = assess(self.ctx)

    def test_risk_is_high(self):
        assert self.result.risk_level == RiskLevel.HIGH

    def test_action_is_ae(self):
        assert self.result.action == RecommendedAction.AE_999

    def test_severe_pain_rule_triggered(self):
        assert "PAIN_SEVERE" in self.result.triggered_rules


# ---------------------------------------------------------------------------
# Demo case 8: shoulder-tip pain + dizziness at 9 weeks
# ---------------------------------------------------------------------------

class TestShoulderTipPainWithDizziness:
    def setup_method(self):
        self.ctx = PatientContext(
            weeks=9,
            has_pain=True,
            pain_severity=6,
            pain_location="one_sided",
            pain_character="sharp",
            shoulder_tip_pain=True,
            dizziness=True,
        )
        self.result = assess(self.ctx)

    def test_risk_is_high(self):
        assert self.result.risk_level == RiskLevel.HIGH

    def test_action_is_ae(self):
        assert self.result.action == RecommendedAction.AE_999

    def test_shoulder_tip_rule_triggered(self):
        assert "PAIN_SHOULDER_TIP" in self.result.triggered_rules


# ---------------------------------------------------------------------------
# Demo case 9: fluid leakage at 28 weeks (PPROM)
# ---------------------------------------------------------------------------

class TestFluidLeakageAt28Weeks:
    def setup_method(self):
        self.ctx = PatientContext(weeks=28, fluid_gush=True)
        self.result = assess(self.ctx)

    def test_risk_is_high(self):
        assert self.result.risk_level == RiskLevel.HIGH

    def test_action_is_ae(self):
        assert self.result.action == RecommendedAction.AE_999

    def test_pprom_rule_triggered(self):
        assert "PPROM" in self.result.triggered_rules


# ---------------------------------------------------------------------------
# Demo case 10: reduced fetal movements at 32 weeks
# ---------------------------------------------------------------------------

class TestReducedFetalMovementsAt32Weeks:
    def setup_method(self):
        self.ctx = PatientContext(weeks=32, reduced_movements=True)
        self.result = assess(self.ctx)

    def test_risk_is_high(self):
        assert self.result.risk_level == RiskLevel.HIGH

    def test_action_is_maternity_triage(self):
        assert self.result.action == RecommendedAction.MATERNITY_TRIAGE

    def test_rfm_rule_triggered(self):
        assert "REDUCED_FETAL_MOVEMENTS" in self.result.triggered_rules


# ---------------------------------------------------------------------------
# Additional rule-level unit tests
# ---------------------------------------------------------------------------

class TestPreeclampsiaRules:
    def test_two_features_is_high_risk(self):
        ctx = PatientContext(weeks=30, headache_severe=True, visual_disturbance=True)
        findings = rule_preeclampsia(ctx)
        assert any(f.risk == RiskLevel.HIGH for f in findings)
        assert any(f.rule_name == "PREECLAMPSIA_CLUSTER_HIGH" for f in findings)

    def test_one_feature_is_medium_risk(self):
        ctx = PatientContext(weeks=26, headache_severe=True)
        findings = rule_preeclampsia(ctx)
        assert any(f.risk == RiskLevel.MEDIUM for f in findings)

    def test_no_features_returns_empty(self):
        ctx = PatientContext(weeks=30)
        findings = rule_preeclampsia(ctx)
        assert findings == []

    def test_not_triggered_before_20_weeks(self):
        ctx = PatientContext(weeks=18, headache_severe=True, visual_disturbance=True)
        findings = rule_preeclampsia(ctx)
        assert findings == []


class TestHyperemesisRules:
    def test_unable_to_keep_fluids_is_high(self):
        ctx = PatientContext(weeks=10, has_nausea=True, vomiting_frequency=8, unable_to_keep_fluids=True)
        findings = rule_nausea(ctx)
        assert any(f.risk == RiskLevel.HIGH for f in findings)

    def test_frequent_vomiting_is_medium(self):
        ctx = PatientContext(weeks=10, has_nausea=True, vomiting_frequency=6)
        findings = rule_nausea(ctx)
        assert any(f.risk == RiskLevel.MEDIUM for f in findings)

    def test_mild_vomiting_is_low(self):
        ctx = PatientContext(weeks=9, has_nausea=True, vomiting_frequency=2)
        findings = rule_nausea(ctx)
        assert all(f.risk == RiskLevel.LOW for f in findings)

    def test_nausea_only_is_low(self):
        ctx = PatientContext(weeks=8, has_nausea=True, vomiting_frequency=0)
        findings = rule_nausea(ctx)
        assert all(f.risk == RiskLevel.LOW for f in findings)


class TestBleedingRules:
    def test_soaking_bleed_is_high(self):
        ctx = PatientContext(weeks=12, has_bleeding=True, bleeding_amount="soaking")
        findings = rule_bleeding(ctx)
        assert any(f.risk == RiskLevel.HIGH for f in findings)

    def test_light_bleed_at_24_weeks_is_high(self):
        ctx = PatientContext(weeks=24, has_bleeding=True, bleeding_amount="light")
        findings = rule_bleeding(ctx)
        assert any(f.risk == RiskLevel.HIGH for f in findings)

    def test_light_bleed_first_trimester_is_medium(self):
        ctx = PatientContext(weeks=10, has_bleeding=True, bleeding_amount="light")
        findings = rule_bleeding(ctx)
        assert any(f.risk == RiskLevel.MEDIUM for f in findings)
        assert not any(f.risk == RiskLevel.HIGH for f in findings)

    def test_spotting_at_7_weeks_is_low(self):
        ctx = PatientContext(weeks=7, has_bleeding=True, bleeding_amount="spots")
        findings = rule_bleeding(ctx)
        assert all(f.risk == RiskLevel.LOW for f in findings)

    def test_clots_escalate_to_high(self):
        ctx = PatientContext(weeks=9, has_bleeding=True, bleeding_amount="light", bleeding_with_clots=True)
        findings = rule_bleeding(ctx)
        assert any(f.risk == RiskLevel.HIGH for f in findings)


class TestFetalMovements:
    def test_rfm_before_24_weeks_not_triggered(self):
        ctx = PatientContext(weeks=23, reduced_movements=True)
        findings = rule_fetal_movements(ctx)
        assert findings == []

    def test_rfm_at_24_weeks_is_high(self):
        ctx = PatientContext(weeks=24, reduced_movements=True)
        findings = rule_fetal_movements(ctx)
        assert any(f.risk == RiskLevel.HIGH for f in findings)

    def test_rfm_none_returns_empty(self):
        ctx = PatientContext(weeks=30, reduced_movements=False)
        findings = rule_fetal_movements(ctx)
        assert findings == []


class TestShoulderTipPain:
    def test_shoulder_tip_is_always_high(self):
        ctx = PatientContext(weeks=8, has_pain=True, pain_severity=3, shoulder_tip_pain=True)
        findings = rule_pain(ctx)
        assert any(f.rule_name == "PAIN_SHOULDER_TIP" and f.risk == RiskLevel.HIGH for f in findings)


class TestEmergencyRules:
    def test_seizure_is_high(self):
        ctx = PatientContext(weeks=32, seizure=True)
        findings = rule_absolute_emergencies(ctx)
        assert any(f.risk == RiskLevel.HIGH for f in findings)

    def test_chest_pain_with_sob_is_high(self):
        ctx = PatientContext(weeks=20, chest_pain=True, breathlessness=True)
        findings = rule_absolute_emergencies(ctx)
        assert any(f.risk == RiskLevel.HIGH for f in findings)

    def test_trauma_is_high(self):
        ctx = PatientContext(weeks=25, trauma=True)
        findings = rule_absolute_emergencies(ctx)
        assert any(f.risk == RiskLevel.HIGH for f in findings)

    def test_pprom_before_37_weeks_is_high(self):
        ctx = PatientContext(weeks=30, fluid_gush=True)
        findings = rule_absolute_emergencies(ctx)
        assert any(f.risk == RiskLevel.HIGH for f in findings)

    def test_rom_at_term_is_medium(self):
        ctx = PatientContext(weeks=39, fluid_gush=True)
        findings = rule_absolute_emergencies(ctx)
        assert any(f.risk == RiskLevel.MEDIUM for f in findings)


class TestFeverRule:
    def test_fever_is_medium(self):
        ctx = PatientContext(weeks=20, fever=True, fever_temp=38.5)
        findings = rule_fever(ctx)
        assert any(f.risk == RiskLevel.MEDIUM for f in findings)


class TestItchingRule:
    def test_itching_at_late_gestation_is_medium(self):
        ctx = PatientContext(weeks=32, has_itching=True)
        findings = rule_itching(ctx)
        assert any(f.risk == RiskLevel.MEDIUM for f in findings)
        assert any(f.rule_name == "ITCHING_OC_SCREEN_LATE" for f in findings)

    def test_itching_early_is_medium(self):
        ctx = PatientContext(weeks=20, has_itching=True)
        findings = rule_itching(ctx)
        assert any(f.risk == RiskLevel.MEDIUM for f in findings)


class TestDizzinessRule:
    def test_dizziness_alone_is_low(self):
        ctx = PatientContext(weeks=14, dizziness=True)
        findings = rule_dizziness(ctx)
        assert all(f.risk == RiskLevel.LOW for f in findings)

    def test_dizziness_with_bleeding_is_high(self):
        ctx = PatientContext(weeks=9, dizziness=True, has_bleeding=True, bleeding_amount="light")
        findings = rule_dizziness(ctx)
        assert any(f.risk == RiskLevel.HIGH for f in findings)


class TestOverallRiskAggregation:
    def test_highest_risk_wins(self):
        ctx = PatientContext(
            weeks=9,
            has_nausea=True,
            vomiting_frequency=2,
            has_bleeding=True,
            bleeding_amount="spots",
            has_pain=True,
            pain_severity=6,
            pain_location="one_sided",
            pain_character="sharp",
        )
        result = assess(ctx)
        assert result.risk_level == RiskLevel.HIGH

    def test_no_symptoms_is_low(self):
        ctx = PatientContext(weeks=12)
        result = assess(ctx)
        assert result.risk_level == RiskLevel.LOW

    def test_result_has_patient_explanation(self):
        ctx = PatientContext(weeks=10, has_nausea=True, vomiting_frequency=1)
        result = assess(ctx)
        assert len(result.patient_explanation) > 20

    def test_result_has_safety_net_advice(self):
        ctx = PatientContext(weeks=10, has_nausea=True, vomiting_frequency=1)
        result = assess(ctx)
        assert len(result.safety_net_advice) >= 1

    def test_triggered_rules_matches_finding_rule_names(self):
        ctx = PatientContext(weeks=32, reduced_movements=True, has_nausea=True, vomiting_frequency=1)
        result = assess(ctx)
        assert result.triggered_rules == [f.rule_name for f in result.findings]
