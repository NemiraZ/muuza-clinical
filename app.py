"""
Muuza — Clinical Triage Support  |  streamlit run app.py

Product layer architecture (visible in UI structure):
  Input Layer        → structured symptom capture form
  Decision Layer     → ClinicalEngine (rules.py / engine.py) — deterministic, NICE-aligned
  Interpretation     → clinical considerations, patient explanation, safety-net
  Clinician Layer    → doctor review, structured feedback capture
  System Layer       → metadata, audit trail, case learning pipeline
"""

from __future__ import annotations
from datetime import datetime
import streamlit as st
from pregnancy_triage import (
    PatientContext, ClinicalEngine, RiskLevel, RecommendedAction, AssessmentResult,
)

# ── Constants ─────────────────────────────────────────────────────────────────

_ENGINE_VERSION = "MuuzaTriage v0.1.0"
_RULESET_LABEL  = "NICE-aligned  (CG62 · NG25 · NG133 · NG201 · NG158 · RCOG GTG 57)"
_TOTAL_RULES    = 11

# ── Page config & engine ──────────────────────────────────────────────────────

st.set_page_config(
    page_title="Muuza — Clinical Triage Support",
    layout="wide",
    initial_sidebar_state="expanded",
)
_engine = ClinicalEngine()

# ── CSS (Muuza design system) ─────────────────────────────────────────────────

st.markdown("""
<style>
/* ── Global ── */
.stApp { background: #FAF7F8; }
section.main > div.block-container {
    padding-top: 1.25rem; padding-bottom: 4rem; max-width: 1200px;
}

/* ── Sidebar ── */
section[data-testid="stSidebar"] { background: #1e1b4b; }
section[data-testid="stSidebar"] .stMarkdown p,
section[data-testid="stSidebar"] .stMarkdown li,
section[data-testid="stSidebar"] label { color: #c4b5fd !important; }
section[data-testid="stSidebar"] .stMarkdown h3 { color: #f5f3ff !important; }
section[data-testid="stSidebar"] hr { border-color: rgba(196,181,253,0.2); }
section[data-testid="stSidebar"] .stButton > button {
    background: rgba(139,92,246,0.15);
    border: 1px solid rgba(196,181,253,0.3);
    color: #f5f3ff !important; border-radius: 8px;
    width: 100%; font-weight: 600; transition: background 0.2s;
}
section[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(139,92,246,0.3);
}

/* ── Input section cards ── */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: #FFFFFF !important; border-radius: 12px !important;
    border: 1px solid #E5E7EB !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.05) !important; margin-bottom: 0.75rem;
}

/* ── Run Assessment button ── */
div[data-testid="stButton"] > button[kind="primary"] {
    background: linear-gradient(90deg, #7c3aed, #8B5CF6) !important;
    border: none !important; border-radius: 10px !important;
    font-size: 1.05rem !important; font-weight: 700 !important;
    letter-spacing: 0.02em !important; padding: 0.7rem 2rem !important;
    box-shadow: 0 4px 14px rgba(139,92,246,0.3) !important; transition: all 0.2s !important;
}
div[data-testid="stButton"] > button[kind="primary"]:hover {
    box-shadow: 0 6px 20px rgba(139,92,246,0.45) !important;
    transform: translateY(-1px) !important;
}

/* ── Page header ── */
.page-header {
    background: #FFFFFF; border-radius: 14px; border-left: 5px solid #8B5CF6;
    padding: 1.6rem 2rem 1.3rem; margin-bottom: 1.25rem;
    box-shadow: 0 1px 4px rgba(0,0,0,0.05);
}
.ph-title { font-size: 1.45rem; font-weight: 800; color: #1F2937; margin: 0 0 0.2rem; letter-spacing: -0.01em; }
.ph-sub   { font-size: 0.93rem; color: #6B7280; margin: 0 0 0.9rem; }
.ph-bullets { list-style: none; padding: 0; margin: 0 0 1rem; }
.ph-bullets li {
    font-size: 0.83rem; color: #6B7280;
    padding: 0.15rem 0 0.15rem 1.3rem; position: relative;
}
.ph-bullets li::before {
    content: "→"; position: absolute; left: 0; color: #8B5CF6; font-weight: 700;
}
.ph-disc {
    font-size: 0.74rem; color: #6B7280; background: #F9FAFB;
    border-radius: 6px; padding: 0.5rem 0.75rem; line-height: 1.55;
}

/* ── Product layer labels ── */
.layer-label {
    font-size: 0.64rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.13em; color: #6B7280;
    margin: 1.1rem 0 0.65rem; padding-bottom: 0.38rem; border-bottom: 1px solid #E5E7EB;
}

/* ── Section label inside input cards ── */
.sec-label {
    font-size: 0.72rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.09em; color: #6B7280;
    margin: 0 0 0.8rem; padding-bottom: 0.5rem; border-bottom: 1px solid #F3F4F6;
}

/* ── Generic output card ── */
.ocard       { background: #FFFFFF; border-radius: 12px; padding: 1.15rem 1.4rem 1rem; margin-bottom: 0.9rem; box-shadow: 0 1px 4px rgba(0,0,0,0.07); }
.ocard-label { font-size: 0.67rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; color: #6B7280; margin-bottom: 0.55rem; }
.ocard-body  { color: #1F2937; font-size: 0.93rem; line-height: 1.65; }

/* ── Risk badge ── */
.risk-badge { display: inline-block; padding: 0.3rem 1.2rem; border-radius: 9999px; font-weight: 800; font-size: 1.1rem; letter-spacing: 0.08em; }
.rb-LOW    { background: #D1FAE5; color: #065F46; border: 2px solid #10B981; }
.rb-MEDIUM { background: #FEF3C7; color: #92400E; border: 2px solid #F59E0B; }
.rb-HIGH   { background: #FEE2E2; color: #991B1B; border: 2px solid #EF4444; }

/* ── Action pill ── */
.action-pill { border-radius: 0 10px 10px 0; padding: 0.85rem 1.1rem; font-weight: 600; font-size: 0.92rem; line-height: 1.45; margin-top: 0.1rem; }
.ap-LOW    { background: #ECFDF5; border-left: 5px solid #10B981; color: #065F46; }
.ap-MEDIUM { background: #FFFBEB; border-left: 5px solid #F59E0B; color: #78350F; }
.ap-HIGH   { background: #FFF1F2; border-left: 5px solid #EF4444; color: #881337; }

/* ── Clinician findings ── */
.finding  { border-radius: 8px; padding: 0.8rem 1rem; margin-bottom: 0.6rem; background: #F9FAFB; border: 1px solid #E5E7EB; }
.f-HIGH   { border-left: 4px solid #EF4444; }
.f-MEDIUM { border-left: 4px solid #F59E0B; }
.f-LOW    { border-left: 4px solid #10B981; }
.f-top    { display: flex; align-items: baseline; gap: 0.5rem; flex-wrap: wrap; }
.f-sym    { font-weight: 700; color: #1F2937; font-size: 0.87rem; }
.f-rule   { font-family: monospace; font-size: 0.71rem; color: #6B7280; background: #F3F4F6; padding: 1px 7px; border-radius: 4px; flex-shrink: 0; }
.f-risk-LOW    { font-size:0.7rem; font-weight:700; color:#065F46; background:#D1FAE5; padding:1px 7px; border-radius:9999px; }
.f-risk-MEDIUM { font-size:0.7rem; font-weight:700; color:#92400E; background:#FEF3C7; padding:1px 7px; border-radius:9999px; }
.f-risk-HIGH   { font-size:0.7rem; font-weight:700; color:#991B1B; background:#FEE2E2; padding:1px 7px; border-radius:9999px; }
.f-detail { font-size: 0.77rem; color: #6B7280; margin-top: 0.25rem; font-style: italic; }
.f-text   { font-size: 0.83rem; color: #6B7280; margin-top: 0.35rem; line-height: 1.55; }
.f-nice   { font-size: 0.71rem; color: #9CA3AF; margin-top: 0.25rem; }
.f-pat    { font-size: 0.78rem; color: #6B7280; margin-top: 0.3rem; background: #F9FAFB; border-left: 2px solid #D1D5DB; padding: 0.3rem 0.6rem; border-radius: 0 4px 4px 0; font-style: italic; }

/* ── Rule chips ── */
.chips { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 0.5rem; }
.chip  { background: #EDE9FE; color: #4C1D95; padding: 3px 10px; border-radius: 4px; font-family: monospace; font-size: 0.76rem; font-weight: 600; }

/* ── Safety-net items ── */
.sn-item { padding: 0.58rem 0.85rem; background: #F0FDFA; border-left: 3px solid #14B8A6; border-radius: 0 6px 6px 0; margin-bottom: 0.45rem; font-size: 0.85rem; color: #134E4A; line-height: 1.5; }

/* ── Clinical considerations ── */
.consid-item   { border-radius: 8px; padding: 0.75rem 1rem; margin-bottom: 0.55rem; background: #F9FAFB; border: 1px solid #E5E7EB; border-left: 4px solid #8B5CF6; }
.consid-title  { font-weight: 700; color: #1F2937; font-size: 0.86rem; }
.consid-text   { font-size: 0.82rem; color: #6B7280; margin-top: 0.25rem; line-height: 1.55; }
.consid-caveat { font-size: 0.72rem; color: #9CA3AF; margin-top: 0.2rem; font-style: italic; }

/* ── System metadata strip ── */
.meta-strip { background: #F9FAFB; border: 1px solid #E5E7EB; border-radius: 8px; padding: 0.7rem 1rem; display: flex; flex-wrap: wrap; gap: 0.6rem 1.5rem; margin-bottom: 0.9rem; }
.meta-item  { font-size: 0.75rem; color: #6B7280; }
.meta-key   { font-weight: 700; color: #6B7280; }
.meta-value { font-family: monospace; color: #1F2937; }

/* ── Doctor review ── */
.dr-header { font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.09em; color: #6B7280; margin: 0 0 0.75rem; padding-bottom: 0.45rem; border-bottom: 1px solid #F3F4F6; }
.dr-saved  { display: inline-block; background: #D1FAE5; color: #065F46; font-size: 0.75rem; font-weight: 700; border-radius: 9999px; padding: 3px 12px; margin-top: 0.5rem; }

/* ── Case learning pipeline ── */
.pipeline-note { font-size: 0.78rem; color: #6B7280; line-height: 1.6; background: #FDF4FF; border-radius: 6px; padding: 0.6rem 0.85rem; margin-bottom: 0.75rem; border-left: 3px solid #EC4899; }

/* ── Footer ── */
.footer-disc { font-size: 0.74rem; color: #6B7280; padding: 0.8rem 1.1rem; background: #FFFFFF; border-radius: 8px; line-height: 1.6; margin-top: 1rem; border: 1px solid #E5E7EB; }
</style>
""", unsafe_allow_html=True)

# ── Demo cases ────────────────────────────────────────────────────────────────

_DEMO_CASES: dict[str, PatientContext | None] = {
    "— select a demo case —": None,
    "1 · Mild nausea only — 8 w  (LOW)": PatientContext(
        weeks=8, has_nausea=True, vomiting_frequency=1,
    ),
    "2 · Clear discharge, no red flags — 16 w  (LOW)": PatientContext(
        weeks=16, has_discharge_change=True, discharge_colour="clear_white",
    ),
    "3 · Smelly discharge + itching — 20 w  (MEDIUM)": PatientContext(
        weeks=20, has_discharge_change=True, discharge_colour="yellow_green",
        discharge_odour=True, has_itching=True,
    ),
    "4 · Spotting only — 7 w  (LOW)": PatientContext(
        weeks=7, has_bleeding=True, bleeding_amount="spots",
    ),
    "5 · Spotting + one-sided pain — 8 w  (HIGH)": PatientContext(
        weeks=8, has_bleeding=True, bleeding_amount="spots",
        has_pain=True, pain_severity=5, pain_location="one_sided", pain_character="sharp",
    ),
    "6 · Heavy bleeding — 22 w  (HIGH)": PatientContext(
        weeks=22, has_bleeding=True, bleeding_amount="heavy",
    ),
    "7 · Severe abdominal pain 9/10 — 18 w  (HIGH)": PatientContext(
        weeks=18, has_pain=True, pain_severity=9,
        pain_location="lower_abdomen", pain_character="constant",
    ),
    "8 · Shoulder-tip pain + dizziness — 9 w  (HIGH)": PatientContext(
        weeks=9, has_pain=True, pain_severity=6, pain_location="one_sided",
        pain_character="sharp", shoulder_tip_pain=True, dizziness=True,
    ),
    "9 · Fluid leakage — 28 w / PPROM  (HIGH)": PatientContext(
        weeks=28, fluid_gush=True,
    ),
    "10 · Reduced fetal movements — 32 w  (HIGH / triage)": PatientContext(
        weeks=32, reduced_movements=True,
    ),
}

# ── Session state defaults ────────────────────────────────────────────────────

_DEFAULTS: dict = {
    # Form fields
    "f_weeks": 12,            "f_days": 0,
    "f_has_bleeding": False,  "f_bleeding_amount": "spots",  "f_bleeding_clots": False,
    "f_has_pain": False,      "f_pain_severity": 3,
    "f_pain_location": "lower_abdomen",  "f_pain_character": "cramping",
    "f_shoulder_tip": False,
    "f_has_nausea": False,    "f_vomiting_freq": 0,          "f_no_fluids": False,
    "f_has_discharge": False, "f_discharge_colour": "clear_white",
    "f_odour": False,         "f_itching": False,
    "f_seizure": False,       "f_trauma": False,             "f_fluid_gush": False,
    "f_chest_pain": False,    "f_breathlessness": False,     "f_dizziness": False,
    "f_fever": False,         "f_fever_temp": 38.5,
    "f_headache": False,      "f_visual": False,             "f_swelling": False,
    "f_rfm": False,
    # Doctor review
    "dr_reviewed": False,     "dr_agreement": "Agree",
    "dr_notes": "",           "dr_saved": False,
}

for _k, _v in _DEFAULTS.items():
    st.session_state.setdefault(_k, _v)

st.session_state.setdefault("result", None)
st.session_state.setdefault("gestation_label", "")
st.session_state.setdefault("assessment_ts", "")
st.session_state.setdefault("demo_selector", "— select a demo case —")

# ── Helper functions ──────────────────────────────────────────────────────────

def _populate(ctx: PatientContext) -> None:
    """Write a PatientContext into session-state form keys."""
    ss = st.session_state
    ss["f_weeks"]            = ctx.weeks
    ss["f_days"]             = ctx.days
    ss["f_has_bleeding"]     = ctx.has_bleeding
    ss["f_bleeding_amount"]  = ctx.bleeding_amount if ctx.bleeding_amount != "none" else "spots"
    ss["f_bleeding_clots"]   = ctx.bleeding_with_clots
    ss["f_has_pain"]         = ctx.has_pain
    ss["f_pain_severity"]    = ctx.pain_severity if ctx.pain_severity > 0 else 3
    ss["f_pain_location"]    = ctx.pain_location or "lower_abdomen"
    ss["f_pain_character"]   = ctx.pain_character or "cramping"
    ss["f_shoulder_tip"]     = ctx.shoulder_tip_pain
    ss["f_has_nausea"]       = ctx.has_nausea
    ss["f_vomiting_freq"]    = ctx.vomiting_frequency
    ss["f_no_fluids"]        = ctx.unable_to_keep_fluids
    ss["f_has_discharge"]    = ctx.has_discharge_change
    ss["f_discharge_colour"] = ctx.discharge_colour or "clear_white"
    ss["f_odour"]            = ctx.discharge_odour
    ss["f_itching"]          = ctx.has_itching
    ss["f_seizure"]          = ctx.seizure
    ss["f_trauma"]           = ctx.trauma
    ss["f_fluid_gush"]       = ctx.fluid_gush
    ss["f_chest_pain"]       = ctx.chest_pain
    ss["f_breathlessness"]   = ctx.breathlessness
    ss["f_dizziness"]        = ctx.dizziness
    ss["f_fever"]            = ctx.fever
    ss["f_fever_temp"]       = ctx.fever_temp if ctx.fever_temp > 0 else 38.5
    ss["f_headache"]         = ctx.headache_severe
    ss["f_visual"]           = ctx.visual_disturbance
    ss["f_swelling"]         = ctx.facial_hand_swelling
    ss["f_rfm"]              = bool(ctx.reduced_movements)
    ss["result"]             = None
    ss["dr_saved"]           = False


def _on_demo_change() -> None:
    ctx = _DEMO_CASES.get(st.session_state.get("demo_selector", ""))
    if ctx is not None:
        _populate(ctx)


def _on_reset() -> None:
    for k, v in _DEFAULTS.items():
        st.session_state[k] = v
    st.session_state["result"]          = None
    st.session_state["assessment_ts"]   = ""
    st.session_state["gestation_label"] = ""
    st.session_state["demo_selector"]   = "— select a demo case —"


# ── Display functions ─────────────────────────────────────────────────────────

def _clinical_considerations(result: AssessmentResult) -> list[tuple[str, str]]:
    """
    Map triggered rules to broad non-diagnostic clinical categories.
    Display layer only — no new clinical logic introduced.
    Language is intentionally cautious and non-definitive throughout.
    """
    rules = set(result.triggered_rules)
    cats: list[tuple[str, str]] = []

    if rules & {"BLEEDING_HEAVY", "BLEEDING_APH", "BLEEDING_WITH_CLOTS",
                "BLEEDING_FIRST_TRIMESTER_LIGHT", "BLEEDING_SECOND_TRIMESTER_LIGHT",
                "SPOTTING_FIRST_TRIMESTER", "SPOTTING_AFTER_FIRST_TRIMESTER"}:
        cats.append((
            "Obstetric bleeding",
            "Vaginal bleeding in pregnancy may be associated with a range of conditions "
            "including early pregnancy complications, placental causes, and cervical pathology. "
            "Clinical assessment is required to clarify the cause and extent.",
        ))

    if rules & {"ECTOPIC_CLUSTER", "PAIN_SHOULDER_TIP"}:
        cats.append((
            "Early pregnancy complication",
            "This symptom pattern may be associated with early pregnancy complications. "
            "Assessment is required to exclude serious causes including ectopic implantation.",
        ))

    if rules & {"DISCHARGE_ABNORMAL_COLOUR", "DISCHARGE_CLEAR_ODOROUS",
                "FEVER", "ITCHING_OC_SCREEN_LATE", "ITCHING_EARLY_PREGNANCY"}:
        cats.append((
            "Possible infection or hepatic cause",
            "Reported symptoms may be associated with urogenital infection, systemic infection, "
            "or hepatic causes such as obstetric cholestasis. "
            "Assessment and investigations are required to clarify.",
        ))

    if rules & {"PREECLAMPSIA_CLUSTER_HIGH", "PREECLAMPSIA_SINGLE_FEATURE"}:
        cats.append((
            "Hypertensive disorder of pregnancy",
            "This symptom combination may be associated with hypertensive disorders "
            "including pre-eclampsia. Blood pressure measurement and urinalysis are required.",
        ))

    if rules & {"REDUCED_FETAL_MOVEMENTS"}:
        cats.append((
            "Fetal wellbeing concern",
            "A reduction in fetal movements may be associated with changes in fetal "
            "condition. CTG monitoring and clinical review are required to clarify.",
        ))

    if rules & {"PPROM", "ROM_AT_TERM", "DISCHARGE_WATERY_POSSIBLE_ROM"}:
        cats.append((
            "Membrane integrity",
            "Reported fluid or discharge may be associated with rupture of membranes. "
            "Speculum examination and clinical assessment are required to confirm.",
        ))

    if rules & {"HYPEREMESIS_SEVERE", "NAUSEA_FREQUENT_VOMITING"}:
        cats.append((
            "Significant nausea and vomiting",
            "This presentation may be associated with hyperemesis gravidarum. "
            "Assessment of hydration status and anti-emetic requirements is indicated.",
        ))

    if not cats:
        if result.risk_level == RiskLevel.LOW:
            cats.append((
                "Physiological variation",
                "Reported symptoms may fall within the range of normal physiological "
                "changes in pregnancy. Routine midwife review is appropriate.",
            ))
        else:
            cats.append((
                "Non-specific presentation",
                "Reported symptoms require clinical assessment to determine their cause "
                "and clinical significance.",
            ))

    return cats[:4]


def _findings_html(result: AssessmentResult) -> str:
    """Build the clinician-reasoning HTML block from all findings."""
    _rc = {"LOW": "f-LOW", "MEDIUM": "f-MEDIUM", "HIGH": "f-HIGH"}
    parts = []
    for f in result.findings:
        detail_html = f'<div class="f-detail">{f.detail}</div>' if f.detail else ""
        parts.append(
            f'<div class="finding {_rc.get(f.risk.value, "")}">'
            f'<div class="f-top">'
            f'<span class="f-sym">{f.symptom}</span>'
            f'<span class="f-rule">{f.rule_name}</span>'
            f'<span class="f-risk-{f.risk.value}">{f.risk.value}</span>'
            f'</div>'
            f'{detail_html}'
            f'<div class="f-text">{f.reasoning}</div>'
            f'<div class="f-pat">{f.patient_summary}</div>'
            f'<div class="f-nice">{f.nice_ref}</div>'
            f'</div>'
        )
    return "".join(parts)


def _build_pipeline_record(
    result: AssessmentResult,
    gestation_label: str,
    assessment_ts: str,
) -> dict:
    """Assemble the simulated case learning pipeline record from current session state."""
    dr = {
        "reviewed":       st.session_state.get("dr_reviewed", False),
        "agreement":      st.session_state.get("dr_agreement", "Agree"),
        "clinical_notes": st.session_state.get("dr_notes", "") or "(none recorded)",
        "confirmed":      st.session_state.get("dr_saved", False),
    }
    return {
        "case_id":        "session_demo_001",
        "captured_at":    assessment_ts,
        "pipeline_stage": "awaiting_outcome" if dr["confirmed"] else "feedback_pending",
        "intake": {
            "gestation":           gestation_label,
            "structured_symptoms": result.triggered_rules,
            "capture_method":      "structured_form_v1",
        },
        "engine_output": {
            "risk_level":      result.risk_level.value,
            "action":          result.action.value,
            "rules_triggered": len(result.findings),
            "engine_version":  _ENGINE_VERSION,
            "ruleset":         "NICE-based-triage",
            "deterministic":   True,
        },
        "doctor_feedback": dr,
        "outcome": {
            "status": "awaiting_follow_up",
            "note": (
                "Outcome data not yet recorded. In production, confirmed clinical findings, "
                "intervention taken, and episode resolution would be captured here."
            ),
        },
        "learning_signal": {
            "available": False,
            "reason": "Outcome data is required before a learning signal can be derived.",
            "future_use": (
                "Agreement and disagreement patterns across cases would inform threshold review, "
                "rule weighting, and triage sensitivity calibration."
            ),
        },
    }


# ── Startup auto-load ─────────────────────────────────────────────────────────
# Case 5 (spotting + one-sided pain, 8 w) is pre-loaded on first visit.
# It activates the ectopic cluster rule, producing HIGH risk with multiple
# findings — the deepest clinical output for a live demo.

if not st.session_state.get("_initialized"):
    _startup_ctx = PatientContext(
        weeks=8, has_bleeding=True, bleeding_amount="spots",
        has_pain=True, pain_severity=5, pain_location="one_sided", pain_character="sharp",
    )
    _populate(_startup_ctx)
    st.session_state["result"]          = _engine.assess(_startup_ctx)
    st.session_state["gestation_label"] = "8+0 weeks"
    st.session_state["assessment_ts"]   = datetime.now().strftime("%d %b %Y  %H:%M")
    st.session_state["demo_selector"]   = "5 · Spotting + one-sided pain — 8 w  (HIGH)"
    st.session_state["_initialized"]    = True

# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown(
        '<p style="font-size:1.05rem;font-weight:800;color:#f5f3ff;margin:0 0 0.05rem;">'
        "Muuza Triage</p>"
        '<p style="font-size:0.72rem;color:#a5b4fc;margin:0 0 1rem;">'
        "Clinical Decision Support &nbsp;·&nbsp; NICE-aligned</p>",
        unsafe_allow_html=True,
    )
    st.markdown("---")
    st.markdown(
        '<p style="font-size:0.68rem;font-weight:700;text-transform:uppercase;'
        'letter-spacing:0.09em;color:#a5b4fc;margin:0 0 0.35rem;">Demo Scenarios</p>',
        unsafe_allow_html=True,
    )
    st.selectbox(
        "Load a preset scenario",
        options=list(_DEMO_CASES.keys()),
        key="demo_selector",
        on_change=_on_demo_change,
        label_visibility="collapsed",
    )
    st.markdown("<div style='height:0.35rem'></div>", unsafe_allow_html=True)
    st.button("Reset form to defaults", on_click=_on_reset, use_container_width=True)
    st.markdown("---")
    st.markdown(
        '<p style="font-size:0.68rem;font-weight:700;text-transform:uppercase;'
        'letter-spacing:0.09em;color:#f9a8d4;margin:0 0 0.45rem;">Clinical Safety</p>'
        '<p style="font-size:0.74rem;color:#9CA3AF;line-height:1.65;margin:0;">'
        "This tool provides decision <em>support</em> only. "
        "It does not replace clinical examination, professional judgement, or NICE guidelines."
        "<br><br>"
        'Language is intentionally cautious: <em>"may indicate"</em>, '
        '<em>"requires assessment"</em> — never <em>"diagnostic of"</em> '
        'or <em>"rules out"</em>.'
        "<br><br>"
        'In any emergency, call <strong style="color:#f87171;">999</strong>.'
        "</p>",
        unsafe_allow_html=True,
    )

# ── Page header ───────────────────────────────────────────────────────────────

st.markdown("""
<div class="page-header">
  <p class="ph-title">Muuza &mdash; Clinical Triage Support</p>
  <p class="ph-sub">Structured symptom intake with explainable risk routing for pregnancy-related presentations</p>
  <ul class="ph-bullets">
    <li>Pre-visit symptom structuring for clinical triage and patient flow optimisation</li>
    <li>Deterministic, auditable outputs &mdash; every decision is rule-traceable to a NICE guideline</li>
    <li>Designed for clinician oversight, not autonomous decision-making</li>
  </ul>
  <div class="ph-disc">
    Does not diagnose &nbsp;&middot;&nbsp;
    Supports clinical decision-making &nbsp;&middot;&nbsp;
    Not a replacement for clinical assessment or examination &nbsp;&middot;&nbsp;
    Call 999 in any emergency
  </div>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# INPUT LAYER — Patient Symptom Capture
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown(
    '<p class="layer-label">Input Layer &mdash; Patient Symptom Capture</p>',
    unsafe_allow_html=True,
)

left, right = st.columns([3, 2], gap="large")

# ─── Left column ──────────────────────────────────────────────────────────────

with left:

    with st.container(border=True):
        st.markdown('<p class="sec-label">Pregnancy Stage</p>', unsafe_allow_html=True)
        g1, g2 = st.columns(2)
        with g1:
            weeks = st.number_input(
                "Completed weeks", min_value=1, max_value=42, step=1, key="f_weeks",
            )
        with g2:
            days = st.number_input(
                "Additional days (0–6)", min_value=0, max_value=6, step=1, key="f_days",
            )
        st.caption(f"Gestation: **{int(weeks)}+{int(days)} weeks**")

    with st.container(border=True):
        st.markdown('<p class="sec-label">Bleeding / Spotting</p>', unsafe_allow_html=True)
        has_bleeding = st.checkbox("Vaginal bleeding or spotting present", key="f_has_bleeding")
        bleeding_amount, bleeding_with_clots = "none", False
        if has_bleeding:
            bleeding_amount = st.radio(
                "Amount",
                options=["spots", "light", "heavy", "soaking"],
                format_func=lambda x: {
                    "spots":   "Spots — a few drops on underwear",
                    "light":   "Light — similar to a light period",
                    "heavy":   "Heavy — similar to a heavy period",
                    "soaking": "Soaking through pads",
                }[x],
                horizontal=True,
                key="f_bleeding_amount",
            )
            bleeding_with_clots = st.checkbox(
                "Clots passed alongside the bleeding", key="f_bleeding_clots",
            )

    with st.container(border=True):
        st.markdown('<p class="sec-label">Pain / Cramping</p>', unsafe_allow_html=True)
        has_pain = st.checkbox("Abdominal or pelvic pain or cramping", key="f_has_pain")
        pain_severity, pain_location, pain_character, shoulder_tip_pain = 0, "", "", False
        if has_pain:
            pain_severity = st.slider(
                "Severity  (1 = very mild · 10 = worst imaginable)",
                min_value=1, max_value=10, key="f_pain_severity",
            )
            pc1, pc2 = st.columns(2)
            with pc1:
                pain_location = st.selectbox(
                    "Location",
                    options=["lower_abdomen", "upper_abdomen", "one_sided", "generalised"],
                    format_func=lambda x: {
                        "lower_abdomen": "Lower abdomen / pelvis",
                        "upper_abdomen": "Upper abdomen / under ribs",
                        "one_sided":     "One-sided (left or right)",
                        "generalised":   "All over / hard to pinpoint",
                    }[x],
                    key="f_pain_location",
                )
            with pc2:
                pain_character = st.selectbox(
                    "Character",
                    options=["cramping", "constant", "sharp", "pressure"],
                    format_func=lambda x: {
                        "cramping": "Cramping / comes and goes",
                        "constant": "Constant / always there",
                        "sharp":    "Sharp / stabbing",
                        "pressure": "Pressure / heaviness",
                    }[x],
                    key="f_pain_character",
                )
            shoulder_tip_pain = st.checkbox(
                "Pain at the tip of the shoulder (not the neck or upper arm)",
                key="f_shoulder_tip",
            )

    with st.container(border=True):
        st.markdown('<p class="sec-label">Nausea / Vomiting</p>', unsafe_allow_html=True)
        has_nausea = st.checkbox("Nausea or vomiting present", key="f_has_nausea")
        vomiting_frequency, unable_to_keep_fluids = 0, False
        if has_nausea:
            vomiting_frequency = st.number_input(
                "Times vomited in last 24 h  (0 = nausea only)",
                min_value=0, max_value=30, step=1, key="f_vomiting_freq",
            )
            if vomiting_frequency > 0:
                unable_to_keep_fluids = st.checkbox(
                    "Unable to keep any fluids down for more than 12 hours",
                    key="f_no_fluids",
                )

# ─── Right column ─────────────────────────────────────────────────────────────

with right:

    with st.container(border=True):
        st.markdown('<p class="sec-label">Discharge Changes</p>', unsafe_allow_html=True)
        has_discharge_change = st.checkbox(
            "Change in vaginal discharge (amount, colour, or smell)",
            key="f_has_discharge",
        )
        discharge_colour, discharge_odour, has_itching = "", False, False
        if has_discharge_change:
            discharge_colour = st.selectbox(
                "Appearance",
                options=["clear_white", "yellow_green", "grey", "pink_brown", "watery"],
                format_func=lambda x: {
                    "clear_white":  "Clear or white — more than usual",
                    "yellow_green": "Yellow or green",
                    "grey":         "Grey",
                    "pink_brown":   "Pink or brown-tinged",
                    "watery":       "Sudden watery gush / continuous leak",
                }[x],
                key="f_discharge_colour",
            )
            discharge_odour = st.checkbox("Unusual or unpleasant smell", key="f_odour")
            has_itching     = st.checkbox("Generalised itching of the skin", key="f_itching")

    with st.container(border=True):
        st.markdown('<p class="sec-label">Red-Flag Symptoms</p>', unsafe_allow_html=True)
        seizure        = st.checkbox("Fitting or loss of consciousness",               key="f_seizure")
        trauma         = st.checkbox("Fall or blow to the abdomen",                    key="f_trauma")
        fluid_gush     = st.checkbox("Sudden gush or leak of fluid (possible waters)", key="f_fluid_gush")
        chest_pain     = st.checkbox("Chest pain",                                     key="f_chest_pain")
        breathlessness = st.checkbox("New or worsening breathlessness",                key="f_breathlessness")
        dizziness      = st.checkbox("Dizziness or feeling faint",                     key="f_dizziness")
        fever          = st.checkbox("Fever — temperature 38 °C or above",             key="f_fever")
        fever_temp     = 0.0
        if fever:
            fever_temp = st.number_input(
                "Temperature (°C) — enter 0 if not measured",
                min_value=0.0, max_value=42.0, step=0.1, key="f_fever_temp",
            )

    headache_severe = visual_disturbance = facial_hand_swelling = reduced_movements = False
    if weeks >= 20:
        with st.container(border=True):
            st.markdown('<p class="sec-label">Later Pregnancy</p>', unsafe_allow_html=True)
            st.caption("Pre-eclampsia screening — relevant from 20 weeks")
            headache_severe      = st.checkbox(
                "Severe headache not relieved by paracetamol", key="f_headache",
            )
            visual_disturbance   = st.checkbox(
                "Visual disturbances — flashing lights, blurred vision", key="f_visual",
            )
            facial_hand_swelling = st.checkbox(
                "Sudden swelling of face, hands, or feet", key="f_swelling",
            )
            if weeks >= 24:
                st.caption("Fetal movements — relevant from 24 weeks")
                reduced_movements = st.checkbox(
                    "Reduction in baby's movements compared to usual pattern", key="f_rfm",
                )

# ═══════════════════════════════════════════════════════════════════════════════
# DECISION LAYER — Triage Engine
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown(
    '<p class="layer-label">Decision Layer &mdash; Triage Engine  '
    '<span style="font-weight:400;text-transform:none;letter-spacing:0;">'
    f'({_ENGINE_VERSION} &nbsp;·&nbsp; {_TOTAL_RULES} rules &nbsp;·&nbsp; Deterministic)'
    '</span></p>',
    unsafe_allow_html=True,
)

run = st.button("Run Assessment", type="primary", use_container_width=True)

if run:
    ctx = PatientContext(
        weeks=int(weeks),
        days=int(days),
        has_bleeding=has_bleeding,
        bleeding_amount=bleeding_amount if has_bleeding else "none",
        bleeding_with_clots=bleeding_with_clots,
        has_pain=has_pain,
        pain_severity=int(pain_severity) if has_pain else 0,
        pain_location=pain_location if has_pain else "",
        pain_character=pain_character if has_pain else "",
        shoulder_tip_pain=shoulder_tip_pain,
        has_nausea=has_nausea,
        vomiting_frequency=int(vomiting_frequency) if has_nausea else 0,
        unable_to_keep_fluids=unable_to_keep_fluids,
        has_discharge_change=has_discharge_change,
        discharge_colour=discharge_colour if has_discharge_change else "",
        discharge_odour=discharge_odour,
        has_itching=has_itching,
        reduced_movements=reduced_movements if weeks >= 24 else None,
        headache_severe=headache_severe,
        visual_disturbance=visual_disturbance,
        facial_hand_swelling=facial_hand_swelling,
        fever=fever,
        fever_temp=float(fever_temp) if fever else 0.0,
        chest_pain=chest_pain,
        breathlessness=breathlessness,
        dizziness=dizziness,
        seizure=seizure,
        trauma=trauma,
        fluid_gush=fluid_gush,
    )
    st.session_state["result"]          = _engine.assess(ctx)
    st.session_state["gestation_label"] = f"{int(weeks)}+{int(days)} weeks"
    st.session_state["assessment_ts"]   = datetime.now().strftime("%d %b %Y  %H:%M")
    st.session_state["dr_saved"]        = False

# ═══════════════════════════════════════════════════════════════════════════════
# RESULTS
# ═══════════════════════════════════════════════════════════════════════════════

if st.session_state.get("result") is not None:
    result: AssessmentResult = st.session_state["result"]
    gestation_label: str     = st.session_state.get("gestation_label", "")
    assessment_ts: str       = st.session_state.get("assessment_ts", "")
    rv: str                  = result.risk_level.value

    st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)
    st.markdown(
        '<hr style="border:none;border-top:1px solid #E5E7EB;margin-bottom:0.9rem;">',
        unsafe_allow_html=True,
    )

    # ── Risk summary (always visible above tabs) ───────────────────────────────

    badge_col, meta_col = st.columns([1, 4])
    with badge_col:
        st.markdown(
            f'<div style="padding-top:0.3rem">'
            f'<span class="risk-badge rb-{rv}">{rv}</span></div>',
            unsafe_allow_html=True,
        )
    with meta_col:
        st.markdown(
            f'<div style="padding-top:0.55rem;font-size:0.82rem;color:#6B7280;">'
            f'Assessed at <strong style="color:#1F2937">{gestation_label}</strong>'
            f'&nbsp;&nbsp;·&nbsp;&nbsp;{len(result.findings)} rule(s) triggered'
            f'&nbsp;&nbsp;·&nbsp;&nbsp;Deterministic output'
            f'&nbsp;&nbsp;·&nbsp;&nbsp;{assessment_ts}'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height:0.6rem'></div>", unsafe_allow_html=True)

    # ── Result tabs ───────────────────────────────────────────────────────────

    tab_clinical, tab_audit, tab_case = st.tabs([
        "Clinical View",
        "Audit Trail",
        "Case Record",
    ])

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 1 — INTERPRETATION + CLINICIAN LAYER
    # ─────────────────────────────────────────────────────────────────────────

    with tab_clinical:

        st.markdown(
            '<p class="layer-label">Interpretation Layer</p>',
            unsafe_allow_html=True,
        )

        # Recommended action + patient explanation
        act_col, pat_col = st.columns(2, gap="large")
        with act_col:
            st.markdown(
                f'<div class="ocard">'
                f'<div class="ocard-label">Recommended Action</div>'
                f'<div class="action-pill ap-{rv}">{result.action.value}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
        with pat_col:
            st.markdown(
                f'<div class="ocard">'
                f'<div class="ocard-label">For the Patient</div>'
                f'<div class="ocard-body">{result.patient_explanation}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

        # Clinical considerations
        consid_html = "".join(
            f'<div class="consid-item">'
            f'<div class="consid-title">{title}</div>'
            f'<div class="consid-text">{text}</div>'
            f'<div class="consid-caveat">'
            f'Non-diagnostic &nbsp;·&nbsp; Requires assessment to clarify'
            f'</div>'
            f'</div>'
            for title, text in _clinical_considerations(result)
        )
        st.markdown(
            f'<div class="ocard">'
            f'<div class="ocard-label">Clinical Considerations (non-diagnostic)</div>'
            f'{consid_html}'
            f'</div>',
            unsafe_allow_html=True,
        )

        # Safety-net advice
        sn_html = "".join(
            f'<div class="sn-item">{item}</div>' for item in result.safety_net_advice
        )
        st.markdown(
            f'<div class="ocard">'
            f'<div class="ocard-label">Safety-Net Advice</div>'
            f'{sn_html}'
            f'</div>',
            unsafe_allow_html=True,
        )

        # ── Clinician Layer ────────────────────────────────────────────────────

        st.markdown(
            '<p class="layer-label">Clinician Layer &mdash; Doctor Review</p>',
            unsafe_allow_html=True,
        )

        with st.container(border=True):
            st.markdown('<p class="dr-header">Doctor Review</p>', unsafe_allow_html=True)
            dr_reviewed = st.checkbox("Reviewed by clinician", key="dr_reviewed")

            if dr_reviewed:
                dr_col1, dr_col2 = st.columns([1, 2])
                with dr_col1:
                    st.selectbox(
                        "Clinical agreement with triage output",
                        options=["Agree", "Partially agree", "Disagree"],
                        key="dr_agreement",
                    )
                with dr_col2:
                    st.text_area(
                        "Clinical notes",
                        key="dr_notes",
                        placeholder=(
                            "Add clinical context, observations, differential "
                            "considerations, or caveats..."
                        ),
                        height=90,
                    )
                if st.button("Confirm review", key="dr_save_btn"):
                    st.session_state["dr_saved"] = True
                if st.session_state.get("dr_saved"):
                    st.markdown(
                        '<span class="dr-saved">Review confirmed and saved to session</span>',
                        unsafe_allow_html=True,
                    )
            else:
                st.caption(
                    "Check the box above to record a clinical review of this assessment."
                )

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 2 — SYSTEM LAYER: AUDIT TRAIL
    # ─────────────────────────────────────────────────────────────────────────

    with tab_audit:

        st.markdown(
            '<p class="layer-label">System Layer &mdash; Audit Trail &amp; Traceability</p>',
            unsafe_allow_html=True,
        )

        # System metadata
        st.markdown(
            f'<div class="meta-strip">'
            f'<span class="meta-item">'
            f'<span class="meta-key">Engine</span>&nbsp;'
            f'<span class="meta-value">{_ENGINE_VERSION}</span>'
            f'</span>'
            f'<span class="meta-item">'
            f'<span class="meta-key">Ruleset</span>&nbsp;'
            f'<span class="meta-value">{_RULESET_LABEL}</span>'
            f'</span>'
            f'<span class="meta-item">'
            f'<span class="meta-key">Rules triggered</span>&nbsp;'
            f'<span class="meta-value">{len(result.findings)} / {_TOTAL_RULES}</span>'
            f'</span>'
            f'<span class="meta-item">'
            f'<span class="meta-key">Mode</span>&nbsp;'
            f'<span class="meta-value">Deterministic — no ML component</span>'
            f'</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # Triggered rule chips
        chips = "".join(
            f'<span class="chip">{r}</span>' for r in result.triggered_rules
        )
        st.markdown(
            f'<div class="ocard">'
            f'<div class="ocard-label">Triggered Rules — Audit Trail</div>'
            f'<div class="chips">{chips}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # Full clinician reasoning
        with st.expander(
            f"Clinician Reasoning — {len(result.findings)} finding(s)  "
            f"[for clinical use only]",
            expanded=True,
        ):
            st.markdown(_findings_html(result), unsafe_allow_html=True)

        # Raw JSON
        with st.expander("Raw JSON output (for integration / audit)"):
            st.json({
                "gestation":           gestation_label,
                "assessed_at":         assessment_ts,
                "risk_level":          rv,
                "action":              result.action.value,
                "triggered_rules":     result.triggered_rules,
                "findings": [
                    {
                        "rule":     f.rule_name,
                        "symptom":  f.symptom,
                        "risk":     f.risk.value,
                        "detail":   f.detail,
                        "nice_ref": f.nice_ref,
                    }
                    for f in result.findings
                ],
                "patient_explanation": result.patient_explanation,
                "safety_net_advice":   result.safety_net_advice,
            })

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 3 — SYSTEM LAYER: CASE RECORD & LEARNING PIPELINE
    # ─────────────────────────────────────────────────────────────────────────

    with tab_case:

        st.markdown(
            '<p class="layer-label">'
            'System Layer &mdash; Case Record &amp; Learning Pipeline'
            '</p>',
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="pipeline-note">'
            "This view illustrates how structured triage data, clinician feedback, "
            "and patient outcomes would be composed into a persistent learning record in production. "
            "Each case record would be linked to a patient episode and used to calibrate triage "
            "thresholds as outcome data accumulates over time. "
            "No data is persisted or transmitted in this demo — all state is local to the session."
            "</div>",
            unsafe_allow_html=True,
        )

        st.json(_build_pipeline_record(result, gestation_label, assessment_ts))

    # ── Footer ────────────────────────────────────────────────────────────────

    st.markdown(
        '<div class="footer-disc">'
        "<strong>Disclaimer:</strong> This tool provides clinical decision support only. "
        "Outputs are deterministic given the same inputs and are fully auditable via the "
        "triggered rules listed in the Audit Trail tab. Results do not replace clinical "
        "examination, professional judgement, or current NICE guidelines. "
        "Always follow local clinical protocols."
        "</div>",
        unsafe_allow_html=True,
    )
