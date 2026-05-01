# Muuza Pregnancy Triage Tool

A clinical decision support tool for triaging pregnancy-related symptoms.
Built in Python with a Streamlit browser interface and a terminal questionnaire mode.

---

## Clinical Safety Limitations

> **This tool does not diagnose. It does not replace clinical assessment.**

- Outputs are decision **support** only — always follow the judgement of a midwife, GP, or obstetrician.
- The tool uses conservative, NICE-aligned triage rules. It is intentionally cautious: when in doubt, it escalates.
- Language is deliberately cautious: "may indicate", "raises concern for", "requires assessment to exclude". It never says "diagnostic of", "rules out", or "definitely".
- All findings cite their NICE guideline source for auditability.
- In any life-threatening emergency, **call 999 immediately** — do not use this tool.

---

## What the Tool Does

The tool takes clinical inputs — gestational age, symptoms (bleeding, pain, nausea, discharge, red-flag signs) — and applies a set of deterministic, NICE-aligned rules to produce:

| Output | Description |
|---|---|
| **Risk level** | LOW / MEDIUM / HIGH |
| **Recommended action** | Monitor at home / See GP today / Maternity triage / A&E / 999 |
| **Patient-friendly explanation** | Plain English, non-alarming, appropriate to risk level |
| **Clinician reasoning** | Per-finding rationale with NICE references |
| **Triggered rules** | Audit trail of which rules fired |
| **Safety-net advice** | Tailored to gestation and risk level |

### NICE guidelines referenced

- NICE CG62 — Antenatal care for uncomplicated pregnancies
- NICE NG25 — Ectopic pregnancy and miscarriage
- NICE NG133 — Hypertension in pregnancy (pre-eclampsia)
- NICE NG201 — Antenatal care (2021)
- NICE NG158 — Venous thromboembolic disease in pregnancy
- RCOG GTG 57 — Reduced fetal movements

---

## How to Run Locally

### 1. Install dependencies

```bash
cd ~/Desktop/Muuza_Pregnancy_Triage_Demo
pip install -r requirements.txt
```

### 2. Launch the browser interface

```bash
cd ~/Desktop/Muuza_Pregnancy_Triage_Demo
streamlit run app.py
```

Opens at `http://localhost:8501`.

The browser UI includes:
- **Sidebar** — 10 preloaded demo scenarios, reset button, clinical safety note
- **Input cards** — Pregnancy stage, Bleeding, Pain, Nausea, Discharge, Red flags, Later pregnancy
- **Run Assessment button** — triggers the deterministic rule engine
- **Results tabs** — Clinical View (action, considerations, doctor review) · Audit Trail (rules, reasoning, JSON) · Case Record (learning pipeline)

### 3. Terminal questionnaire

```bash
python3 -m pregnancy_triage.questionnaire
```

### 4. Demo cases

```bash
python3 demo_cases.py
```

### 5. Run tests

```bash
pytest -q
```

---

## Streamlit Community Cloud Deployment

This app is deployed at: **https://github.com/NemiraZ/muuza-clinical**

To deploy your own instance on [Streamlit Community Cloud](https://streamlit.io/cloud):

| Setting | Value |
|---|---|
| **Repository** | `NemiraZ/muuza-clinical` |
| **Branch** | `main` |
| **Main file path** | `app.py` |

No secrets or environment variables are required. The app is fully self-contained.

---

## Example Outputs

### LOW risk — mild nausea at 8 weeks

```
Risk level : LOW
Action     : Monitor at home

Triggered rules:
  • NAUSEA_MILD_VOMITING
```

### HIGH risk — spotting + one-sided pain at 8 weeks

```
Risk level : HIGH
Action     : Call 999 or go to A&E immediately

Triggered rules:
  • SPOTTING_FIRST_TRIMESTER
  • PAIN_MODERATE
  • ECTOPIC_CLUSTER

Reasoning (ECTOPIC_CLUSTER):
  The combination of early pregnancy (<14 weeks), vaginal bleeding, and
  abdominal pain raises concern for ectopic pregnancy, which requires
  urgent exclusion by ultrasound and serum βhCG measurement.
  NICE ref: NICE NG25 §1.4
```

### HIGH risk — reduced fetal movements at 32 weeks

```
Risk level : HIGH
Action     : Attend maternity triage or assessment unit today

Triggered rules:
  • REDUCED_FETAL_MOVEMENTS
```

---

## Project Structure

```
Muuza_Pregnancy_Triage_Demo/
  app.py                        # Streamlit browser interface
  demo_cases.py                 # 10 demo scenarios with expected outcomes
  requirements.txt
  runtime.txt                   # Python version for Streamlit Cloud
  README.md
  .streamlit/
    config.toml                 # Theme and server settings
  pregnancy_triage/
    __init__.py                 # Package exports
    models.py                   # Data types: RiskLevel, PatientContext, AssessmentResult
    rules.py                    # All clinical rules (one function per domain)
    engine.py                   # ClinicalEngine: runs rules, aggregates risk, determines action
    questionnaire.py            # Terminal-based questionnaire
    renderers.py                # Terminal output + patient/safety-net text generators
  tests/
    test_triage_rules.py        # pytest test suite (50+ assertions)
```

---

## Demo Cases

| # | Scenario | Expected |
|---|---|---|
| 1 | Mild nausea only — 8 weeks | LOW |
| 2 | Increased clear discharge, no red flags — 16 weeks | LOW |
| 3 | Smelly yellow discharge + itching — 20 weeks | MEDIUM |
| 4 | Spotting only — 7 weeks | LOW |
| 5 | Spotting + one-sided pain — 8 weeks | HIGH |
| 6 | Heavy bleeding — 22 weeks | HIGH |
| 7 | Severe pain 9/10 — 18 weeks | HIGH |
| 8 | Shoulder-tip pain + dizziness — 9 weeks | HIGH |
| 9 | Fluid leakage — 28 weeks (PPROM) | HIGH |
| 10 | Reduced fetal movements — 32 weeks | HIGH / Maternity triage |

---

## Licence and Attribution

Built for demonstration and educational purposes.
Not validated for clinical deployment without further review by qualified clinicians.
