"""
Clinical decision rules for the Muuza Pregnancy Triage tool.
Each rule function accepts a PatientContext and returns a list of ClinicalFindings.

Rules are based on:
  - NICE CG62  : Antenatal care for uncomplicated pregnancies
  - NICE NG25  : Ectopic pregnancy and miscarriage
  - NICE NG133 : Hypertension in pregnancy (including pre-eclampsia)
  - NICE NG201 : Antenatal care (2021)
  - NICE NG158 : Venous thromboembolic disease in pregnancy
  - RCOG GTG 57: Reduced fetal movements

Language conventions:
  - "may indicate"  / "raises concern for"  / "requires assessment to exclude"
  - Avoid: "diagnostic of", "rules out", "classic sign", "definitely"
"""

from __future__ import annotations
from .models import PatientContext, ClinicalFinding, RiskLevel, RecommendedAction

# ---------------------------------------------------------------------------
# Rule: absolute emergencies
# ---------------------------------------------------------------------------

def rule_absolute_emergencies(ctx: PatientContext) -> list[ClinicalFinding]:
    findings: list[ClinicalFinding] = []

    if ctx.seizure:
        findings.append(ClinicalFinding(
            rule_name="EMERGENCY_SEIZURE",
            symptom="Seizure or loss of consciousness",
            detail="Patient is or has been fitting",
            risk=RiskLevel.HIGH,
            reasoning=(
                "Seizure during pregnancy requires immediate emergency management. "
                "Eclampsia should be considered and requires IV magnesium sulphate "
                "and urgent obstetric review. Assessment cannot be deferred."
            ),
            nice_ref="NICE NG133 §1.5 (eclampsia management)",
            patient_summary=(
                "A seizure during pregnancy requires emergency treatment right now. "
                "Call 999 immediately."
            ),
        ))

    if ctx.chest_pain and ctx.breathlessness:
        findings.append(ClinicalFinding(
            rule_name="EMERGENCY_CHEST_PAIN_SOB",
            symptom="Chest pain with breathlessness",
            detail="Both chest pain and breathlessness are reported",
            risk=RiskLevel.HIGH,
            reasoning=(
                "The combination of chest pain and breathlessness in pregnancy "
                "raises concern for pulmonary embolism, which occurs at higher "
                "rates during pregnancy and the postnatal period. Urgent assessment "
                "and imaging are required."
            ),
            nice_ref="NICE NG158 §1.2 (diagnosis of VTE in pregnancy)",
            patient_summary=(
                "Chest pain with breathlessness may indicate a serious condition "
                "and requires immediate hospital assessment."
            ),
        ))

    if ctx.trauma:
        findings.append(ClinicalFinding(
            rule_name="EMERGENCY_TRAUMA",
            symptom="Abdominal trauma",
            detail="Trauma or blow to the abdomen reported",
            risk=RiskLevel.HIGH,
            reasoning=(
                "Any abdominal trauma during pregnancy requires urgent obstetric "
                "assessment regardless of apparent severity. Placental abruption, "
                "uterine injury, and fetal compromise should be excluded with "
                "clinical examination, CTG, and ultrasound as indicated."
            ),
            nice_ref="NICE CG62 §1.2 (referral thresholds)",
            patient_summary=(
                "Any blow or trauma to your abdomen during pregnancy needs "
                "urgent assessment at a maternity unit."
            ),
        ))

    if ctx.fluid_gush:
        if ctx.weeks < 37:
            findings.append(ClinicalFinding(
                rule_name="PPROM",
                symptom="Possible pre-term prelabour rupture of membranes (PPROM)",
                detail=f"Sudden fluid loss reported at {ctx.gestation_label}",
                risk=RiskLevel.HIGH,
                reasoning=(
                    "A sudden gush of fluid before 37 weeks may indicate "
                    "pre-term prelabour rupture of membranes (PPROM). "
                    "This requires urgent hospital assessment to confirm with "
                    "speculum examination, assess for cord presentation, identify "
                    "infection, and plan management. Pre-term birth and infection "
                    "risk are significantly increased."
                ),
                nice_ref="NICE NG25 §1.1; NICE CG62 §1.5 (PPROM management)",
                patient_summary=(
                    "A sudden gush of fluid before 37 weeks may mean your waters "
                    "have broken early. This needs urgent assessment today."
                ),
            ))
        else:
            findings.append(ClinicalFinding(
                rule_name="ROM_AT_TERM",
                symptom="Possible rupture of membranes at term",
                detail=f"Sudden fluid loss reported at {ctx.gestation_label}",
                risk=RiskLevel.MEDIUM,
                reasoning=(
                    "A sudden gush of fluid at or after 37 weeks may indicate "
                    "term rupture of membranes. Maternity unit attendance is "
                    "required to confirm with speculum examination, assess fetal "
                    "presentation, and plan induction or expectant management."
                ),
                nice_ref="NICE CG70 (induction of labour)",
                patient_summary=(
                    "A sudden gush of fluid at term may mean your waters have "
                    "broken. Contact your maternity unit today."
                ),
            ))

    return findings


# ---------------------------------------------------------------------------
# Rule: bleeding
# ---------------------------------------------------------------------------

def rule_bleeding(ctx: PatientContext) -> list[ClinicalFinding]:
    findings: list[ClinicalFinding] = []

    if not ctx.has_bleeding:
        return findings

    if ctx.bleeding_with_clots:
        findings.append(ClinicalFinding(
            rule_name="BLEEDING_WITH_CLOTS",
            symptom="Clots passed with vaginal bleeding",
            detail="Clots present alongside bleeding",
            risk=RiskLevel.HIGH,
            reasoning=(
                "Passage of clots alongside vaginal bleeding may indicate "
                "significant haemorrhage or ongoing pregnancy loss. Urgent "
                "assessment is required to establish the cause, estimate blood "
                "loss, and ensure haemodynamic stability."
            ),
            nice_ref="NICE NG25 §1.3 (management of miscarriage)",
            patient_summary=(
                "Passing clots with bleeding during pregnancy requires urgent "
                "assessment today."
            ),
        ))

    amount = ctx.bleeding_amount

    if amount in ("heavy", "soaking"):
        findings.append(ClinicalFinding(
            rule_name="BLEEDING_HEAVY",
            symptom="Heavy vaginal bleeding",
            detail=f"Bleeding described as: {amount}",
            risk=RiskLevel.HIGH,
            reasoning=(
                "Heavy vaginal bleeding during pregnancy requires immediate "
                "assessment at any gestation. Possible causes include miscarriage, "
                "placenta praevia, and placental abruption. Haemodynamic assessment "
                "and haematological investigation should not be delayed."
            ),
            nice_ref="NICE NG25 §1.3; NICE CG62 §1.3 (antepartum haemorrhage)",
            patient_summary=(
                "Heavy bleeding during pregnancy requires emergency assessment. "
                "Go to A&E or call 999 now."
            ),
        ))

    elif amount == "light":
        if ctx.weeks >= 24:
            findings.append(ClinicalFinding(
                rule_name="BLEEDING_APH",
                symptom="Antepartum haemorrhage (light bleeding ≥24 weeks)",
                detail=f"Light vaginal bleeding at {ctx.gestation_label}",
                risk=RiskLevel.HIGH,
                reasoning=(
                    "Any vaginal bleeding after 24 weeks of gestation is considered "
                    "antepartum haemorrhage until assessed otherwise. Placenta "
                    "praevia and placental abruption should be excluded urgently. "
                    "There is no safe threshold for blood loss at this gestation "
                    "without clinical assessment."
                ),
                nice_ref="NICE CG62 §1.3 (antepartum haemorrhage)",
                patient_summary=(
                    "Any bleeding after 24 weeks needs urgent assessment today. "
                    "Do not wait — go to your maternity unit."
                ),
            ))
        elif ctx.weeks <= 12:
            findings.append(ClinicalFinding(
                rule_name="BLEEDING_FIRST_TRIMESTER_LIGHT",
                symptom="Light vaginal bleeding in first trimester",
                detail=f"Light bleeding at {ctx.gestation_label}",
                risk=RiskLevel.MEDIUM,
                reasoning=(
                    "Light bleeding in the first trimester may have several causes "
                    "including implantation bleeding, cervical ectropion, or "
                    "threatened miscarriage. Ectopic pregnancy should also be "
                    "considered. An early pregnancy assessment unit (EPAU) referral "
                    "with ultrasound scan and serum βhCG is recommended to establish "
                    "location and viability of the pregnancy."
                ),
                nice_ref="NICE NG25 §1.2 (threatened miscarriage); §1.4 (ectopic)",
                patient_summary=(
                    "Light bleeding in early pregnancy should be reviewed by a "
                    "doctor or midwife today to check on the pregnancy."
                ),
            ))
        else:
            findings.append(ClinicalFinding(
                rule_name="BLEEDING_SECOND_TRIMESTER_LIGHT",
                symptom="Light vaginal bleeding — second trimester",
                detail=f"Light bleeding at {ctx.gestation_label}",
                risk=RiskLevel.MEDIUM,
                reasoning=(
                    "Vaginal bleeding in the second trimester warrants prompt "
                    "clinical assessment. Possible causes include cervical "
                    "incompetence, low-lying placenta, or cervical pathology. "
                    "A same-day review with ultrasound where available is "
                    "recommended."
                ),
                nice_ref="NICE CG62 §1.3",
                patient_summary=(
                    "Any bleeding in pregnancy should be assessed by a doctor "
                    "or midwife today."
                ),
            ))

    elif amount == "spots":
        if ctx.weeks <= 12:
            findings.append(ClinicalFinding(
                rule_name="SPOTTING_FIRST_TRIMESTER",
                symptom="Spotting — first trimester",
                detail=f"Spotting (a few drops) at {ctx.gestation_label}",
                risk=RiskLevel.LOW,
                reasoning=(
                    "Spotting (a few drops of blood) in the first trimester is "
                    "common and is often benign — causes include implantation "
                    "bleeding and cervical ectropion. In the absence of pain or "
                    "other concerning features, home monitoring is appropriate. "
                    "If spotting increases, becomes heavier, or is accompanied "
                    "by pain, seek review promptly."
                ),
                nice_ref="NICE NG25 §1.1 (definition of threatened miscarriage)",
                patient_summary=(
                    "A small amount of spotting in early pregnancy is common "
                    "and often not serious. Monitor at home and contact your "
                    "midwife or GP if it gets heavier or you develop pain."
                ),
            ))
        else:
            findings.append(ClinicalFinding(
                rule_name="SPOTTING_AFTER_FIRST_TRIMESTER",
                symptom="Spotting after the first trimester",
                detail=f"Spotting at {ctx.gestation_label}",
                risk=RiskLevel.MEDIUM,
                reasoning=(
                    "Any visible bleeding after 12 weeks should be assessed "
                    "promptly. Although spotting may have a benign cause such "
                    "as cervical ectropion, low-lying placenta and other "
                    "obstetric causes should be excluded."
                ),
                nice_ref="NICE CG62 §1.3",
                patient_summary=(
                    "Any spotting after the first trimester should be reviewed "
                    "by a doctor or midwife today."
                ),
            ))

    return findings


# ---------------------------------------------------------------------------
# Rule: pain
# ---------------------------------------------------------------------------

def rule_pain(ctx: PatientContext) -> list[ClinicalFinding]:
    findings: list[ClinicalFinding] = []

    if not ctx.has_pain:
        return findings

    severity = ctx.pain_severity
    location = ctx.pain_location or "unspecified"
    character = ctx.pain_character or "unspecified"

    if ctx.shoulder_tip_pain:
        findings.append(ClinicalFinding(
            rule_name="PAIN_SHOULDER_TIP",
            symptom="Shoulder-tip pain",
            detail="Pain at the tip of the shoulder reported",
            risk=RiskLevel.HIGH,
            reasoning=(
                "Shoulder-tip pain in pregnancy may be associated with "
                "diaphragmatic irritation caused by intraperitoneal blood or "
                "fluid. In early pregnancy, this raises concern for ruptured "
                "ectopic pregnancy, which requires urgent exclusion. At any "
                "gestation, unexplained shoulder-tip pain warrants emergency "
                "assessment."
            ),
            nice_ref="NICE NG25 §1.4 (ectopic pregnancy presentation)",
            patient_summary=(
                "Pain at the tip of the shoulder may indicate a serious "
                "condition inside the abdomen. Seek emergency care immediately."
            ),
        ))

    if severity >= 8:
        findings.append(ClinicalFinding(
            rule_name="PAIN_SEVERE",
            symptom="Severe abdominal or pelvic pain (≥8/10)",
            detail=f"Severity {severity}/10 — location: {location}, character: {character}",
            risk=RiskLevel.HIGH,
            reasoning=(
                "Severe abdominal or pelvic pain in pregnancy requires urgent "
                "assessment. The differential includes ectopic pregnancy, "
                "placental abruption, appendicitis, and pre-term labour, "
                "depending on gestation. Severity alone warrants same-day "
                "emergency evaluation."
            ),
            nice_ref="NICE CG62 §1.2; NICE NG25 §1.3",
            patient_summary=(
                "Severe pain during pregnancy needs emergency assessment. "
                "Go to A&E or call 999 now."
            ),
        ))

    elif severity >= 5:
        risk = RiskLevel.HIGH if (ctx.weeks < 14 and ctx.has_bleeding) else RiskLevel.MEDIUM
        findings.append(ClinicalFinding(
            rule_name="PAIN_MODERATE",
            symptom="Moderate abdominal or pelvic pain (5–7/10)",
            detail=f"Severity {severity}/10 — location: {location}, character: {character}",
            risk=risk,
            reasoning=(
                "Moderate abdominal pain warrants same-day clinical review. "
                "In early pregnancy with concurrent bleeding, ectopic pregnancy "
                "and miscarriage should be assessed urgently. "
                "At later gestations, uterine, placental, or intra-abdominal "
                "causes should be considered."
            ),
            nice_ref="NICE NG25 §1.2; NICE CG62 §1.2",
            patient_summary=(
                "Moderate pain during pregnancy should be reviewed by a "
                "doctor or midwife today."
            ),
        ))

    elif severity > 0:
        if character == "cramping" and not ctx.has_bleeding:
            findings.append(ClinicalFinding(
                rule_name="PAIN_MILD_CRAMPING_NO_BLEEDING",
                symptom="Mild cramping without bleeding",
                detail=f"Severity {severity}/10 cramping, location: {location}",
                risk=RiskLevel.LOW,
                reasoning=(
                    "Mild cramping without bleeding is common during pregnancy "
                    "and may reflect round ligament stretching, uterine growth, "
                    "or Braxton Hicks contractions. Monitor at home; seek review "
                    "if cramping worsens, becomes regular, or bleeding develops."
                ),
                nice_ref="NICE CG62 §1 (normal pregnancy symptoms)",
                patient_summary=(
                    "Mild cramping without bleeding is often a normal part of "
                    "pregnancy. Monitor at home and contact your midwife if it "
                    "worsens or you develop bleeding."
                ),
            ))
        else:
            findings.append(ClinicalFinding(
                rule_name="PAIN_MILD",
                symptom="Mild pain",
                detail=f"Severity {severity}/10 — location: {location}, character: {character}",
                risk=RiskLevel.LOW,
                reasoning=(
                    "Mild pain in the absence of other concerning features may "
                    "be physiological. Mention at the next routine midwife contact "
                    "and seek earlier review if it worsens."
                ),
                nice_ref="NICE CG62 §1",
                patient_summary=(
                    "Mild pain can be normal in pregnancy. Mention this to your "
                    "midwife and seek advice if it gets worse."
                ),
            ))

    return findings


# ---------------------------------------------------------------------------
# Rule: nausea / vomiting
# ---------------------------------------------------------------------------

def rule_nausea(ctx: PatientContext) -> list[ClinicalFinding]:
    findings: list[ClinicalFinding] = []

    if not ctx.has_nausea:
        return findings

    if ctx.unable_to_keep_fluids:
        findings.append(ClinicalFinding(
            rule_name="HYPEREMESIS_SEVERE",
            symptom="Unable to keep fluids down — possible hyperemesis gravidarum",
            detail=f"Vomiting {ctx.vomiting_frequency}×/day; unable to maintain hydration",
            risk=RiskLevel.HIGH,
            reasoning=(
                "Inability to retain any fluids may indicate hyperemesis "
                "gravidarum (HG) — severe nausea and vomiting in pregnancy "
                "associated with dehydration, electrolyte disturbance, and "
                "weight loss. IV rehydration and anti-emetic therapy are often "
                "required; hospital admission should be considered. Thyroid "
                "function and urinalysis for ketonuria should be assessed."
            ),
            nice_ref="NICE CG62 §1; NICE guidelines on nausea/vomiting in pregnancy (2024 update)",
            patient_summary=(
                "Being unable to keep fluids down for more than 12 hours "
                "requires urgent medical assessment today. You may need a "
                "drip to rehydrate."
            ),
        ))

    elif ctx.vomiting_frequency >= 5:
        findings.append(ClinicalFinding(
            rule_name="NAUSEA_FREQUENT_VOMITING",
            symptom="Frequent vomiting (≥5 episodes in 24 hours)",
            detail=f"Vomiting {ctx.vomiting_frequency}×/day",
            risk=RiskLevel.MEDIUM,
            reasoning=(
                "Vomiting five or more times per day raises concern for "
                "developing hyperemesis gravidarum. A same-day GP review "
                "is recommended for anti-emetic treatment and hydration "
                "assessment before dehydration develops."
            ),
            nice_ref="NICE CG62 §1",
            patient_summary=(
                "Vomiting this frequently may need medical treatment. "
                "Contact your GP or midwife today."
            ),
        ))

    elif ctx.vomiting_frequency >= 1:
        findings.append(ClinicalFinding(
            rule_name="NAUSEA_MILD_VOMITING",
            symptom="Nausea with vomiting",
            detail=f"Vomiting {ctx.vomiting_frequency}×/day; able to maintain hydration",
            risk=RiskLevel.LOW,
            reasoning=(
                "Nausea and vomiting affect the majority of pregnant women and "
                "are expected, particularly in the first trimester. When "
                "hydration is maintained, management with dietary modification "
                "and rest is appropriate. Seek review if symptoms worsen."
            ),
            nice_ref="NICE CG62 §1 (common symptoms in pregnancy)",
            patient_summary=(
                "Nausea and some vomiting are very common in pregnancy. "
                "Stay hydrated and rest. Contact your midwife if it gets worse."
            ),
        ))

    else:
        findings.append(ClinicalFinding(
            rule_name="NAUSEA_WITHOUT_VOMITING",
            symptom="Nausea without vomiting",
            detail="Nausea only; no vomiting reported",
            risk=RiskLevel.LOW,
            reasoning=(
                "Nausea without vomiting is one of the most common symptoms "
                "in early pregnancy. No specific intervention is required "
                "unless symptoms progress to frequent vomiting or inability "
                "to maintain hydration."
            ),
            nice_ref="NICE CG62 §1",
            patient_summary=(
                "Nausea without vomiting is normal in pregnancy. "
                "Monitor and contact your midwife if you start vomiting frequently."
            ),
        ))

    return findings


# ---------------------------------------------------------------------------
# Rule: discharge
# ---------------------------------------------------------------------------

def rule_discharge(ctx: PatientContext) -> list[ClinicalFinding]:
    findings: list[ClinicalFinding] = []

    if not ctx.has_discharge_change:
        return findings

    colour = ctx.discharge_colour

    if colour == "watery":
        risk = RiskLevel.HIGH if ctx.weeks < 37 else RiskLevel.MEDIUM
        findings.append(ClinicalFinding(
            rule_name="DISCHARGE_WATERY_POSSIBLE_ROM",
            symptom="Sudden watery vaginal discharge — possible rupture of membranes",
            detail=f"Watery discharge at {ctx.gestation_label}",
            risk=risk,
            reasoning=(
                "A sudden or persistent watery discharge may indicate rupture "
                "of the membranes. Before 37 weeks this may represent PPROM "
                "and requires emergency obstetric assessment. At term, maternity "
                "unit attendance is required to confirm rupture, assess fetal "
                "presentation, and plan management."
            ),
            nice_ref="NICE NG25 §1.1; NICE CG70 (induction of labour)",
            patient_summary=(
                "A sudden watery discharge may mean your waters have broken. "
                "This needs to be assessed by a midwife or doctor today."
            ),
        ))

    elif colour in ("yellow_green", "grey"):
        findings.append(ClinicalFinding(
            rule_name="DISCHARGE_ABNORMAL_COLOUR",
            symptom="Abnormal vaginal discharge colour",
            detail=f"Discharge colour: {colour.replace('_', '/')}",
            risk=RiskLevel.MEDIUM,
            reasoning=(
                "Yellow-green or grey vaginal discharge may indicate infection "
                "such as bacterial vaginosis (BV), trichomoniasis, or other "
                "sexually transmitted infections. BV in pregnancy is associated "
                "with an increased risk of pre-term birth and second-trimester "
                "miscarriage. Swabs and treatment are indicated. A same-day "
                "GP or midwife review is recommended."
            ),
            nice_ref="NICE CG62 §1 (screening for infection in pregnancy)",
            patient_summary=(
                "An unusual discharge colour may indicate an infection that "
                "should be treated during pregnancy. Contact your GP or "
                "midwife today."
            ),
        ))

    elif colour == "pink_brown":
        if ctx.weeks >= 24:
            findings.append(ClinicalFinding(
                rule_name="DISCHARGE_PINK_BROWN_APH",
                symptom="Pink/brown-tinged discharge ≥24 weeks",
                detail=f"Pink/brown discharge at {ctx.gestation_label}",
                risk=RiskLevel.HIGH,
                reasoning=(
                    "Pink or blood-tinged discharge after 24 weeks should be "
                    "assessed as possible antepartum haemorrhage. Clinical "
                    "examination, CTG, and ultrasound may be required to "
                    "exclude placenta praevia or abruption."
                ),
                nice_ref="NICE CG62 §1.3 (antepartum haemorrhage)",
                patient_summary=(
                    "Any pink or blood-tinged discharge after 24 weeks needs "
                    "urgent assessment at your maternity unit today."
                ),
            ))
        else:
            findings.append(ClinicalFinding(
                rule_name="DISCHARGE_PINK_BROWN_EARLY",
                symptom="Pink/brown-tinged discharge before 24 weeks",
                detail=f"Pink/brown discharge at {ctx.gestation_label}",
                risk=RiskLevel.MEDIUM,
                reasoning=(
                    "Pink or brown discharge before 24 weeks may represent old "
                    "blood and may be associated with threatened miscarriage, "
                    "implantation, or cervical pathology. An early pregnancy "
                    "assessment and scan are recommended."
                ),
                nice_ref="NICE NG25 §1.2 (threatened miscarriage)",
                patient_summary=(
                    "Pink or brown discharge should be reviewed by your GP or "
                    "midwife today to check the pregnancy."
                ),
            ))

    elif colour == "clear_white":
        if ctx.discharge_odour:
            findings.append(ClinicalFinding(
                rule_name="DISCHARGE_CLEAR_ODOROUS",
                symptom="Clear/white discharge with odour",
                detail="Clear or white discharge with unusual smell",
                risk=RiskLevel.MEDIUM,
                reasoning=(
                    "An unusual odour with vaginal discharge, even if the colour "
                    "appears normal, may indicate bacterial vaginosis or other "
                    "infection. BV in pregnancy is associated with pre-term birth "
                    "risk and should be treated. A GP or midwife review for "
                    "swabs and possible treatment is recommended."
                ),
                nice_ref="NICE CG62 §1 (infection screening)",
                patient_summary=(
                    "An unusual smell from vaginal discharge may indicate an "
                    "infection. Contact your GP or midwife today."
                ),
            ))
        else:
            findings.append(ClinicalFinding(
                rule_name="DISCHARGE_CLEAR_INCREASED",
                symptom="Increased clear/white discharge — no odour",
                detail="Increased non-odorous clear or white discharge",
                risk=RiskLevel.LOW,
                reasoning=(
                    "An increase in clear or white, odourless vaginal discharge "
                    "(leucorrhoea) is a normal physiological change in pregnancy "
                    "caused by elevated oestrogen levels. No specific intervention "
                    "is required unless the colour, consistency, or smell changes."
                ),
                nice_ref="NICE CG62 §1 (normal pregnancy changes)",
                patient_summary=(
                    "More clear or white discharge without an unusual smell is "
                    "a normal part of pregnancy. No action needed unless it changes."
                ),
            ))

    return findings


# ---------------------------------------------------------------------------
# Rule: itching (obstetric cholestasis screen)
# ---------------------------------------------------------------------------

def rule_itching(ctx: PatientContext) -> list[ClinicalFinding]:
    findings: list[ClinicalFinding] = []

    if not ctx.has_itching:
        return findings

    if ctx.weeks >= 28:
        findings.append(ClinicalFinding(
            rule_name="ITCHING_OC_SCREEN_LATE",
            symptom="Generalised itching — obstetric cholestasis assessment needed",
            detail=f"Itching reported at {ctx.gestation_label}",
            risk=RiskLevel.MEDIUM,
            reasoning=(
                "Generalised itching in the third trimester, particularly "
                "affecting the palms and soles, may be associated with "
                "intrahepatic cholestasis of pregnancy (ICP/obstetric cholestasis). "
                "ICP is associated with an increased risk of pre-term birth "
                "and adverse fetal outcomes. LFTs and bile acids should be "
                "checked. A same-day GP or midwife review is recommended."
            ),
            nice_ref="NICE CG62 §1 (itching in pregnancy); RCOG GTG 43",
            patient_summary=(
                "Itching in late pregnancy may need investigation to check your "
                "liver function. Please contact your GP or midwife today."
            ),
        ))
    else:
        findings.append(ClinicalFinding(
            rule_name="ITCHING_EARLY_PREGNANCY",
            symptom="Generalised itching",
            detail=f"Itching reported at {ctx.gestation_label}",
            risk=RiskLevel.MEDIUM,
            reasoning=(
                "Generalised itching in pregnancy warrants review to exclude "
                "dermatological and hepatic causes. Although obstetric cholestasis "
                "is more common later in pregnancy, a GP or midwife review for "
                "assessment and blood tests is recommended."
            ),
            nice_ref="NICE CG62 §1",
            patient_summary=(
                "Itching during pregnancy should be checked by your GP or "
                "midwife to rule out any underlying cause."
            ),
        ))

    return findings


# ---------------------------------------------------------------------------
# Rule: fetal movements (≥24 weeks only)
# ---------------------------------------------------------------------------

def rule_fetal_movements(ctx: PatientContext) -> list[ClinicalFinding]:
    findings: list[ClinicalFinding] = []

    if ctx.weeks < 24 or ctx.reduced_movements is not True:
        return findings

    findings.append(ClinicalFinding(
        rule_name="REDUCED_FETAL_MOVEMENTS",
        symptom="Reduced fetal movements",
        detail=f"Movement reduction reported at {ctx.gestation_label}",
        risk=RiskLevel.HIGH,
        reasoning=(
            "Reduced fetal movements (RFM) after 24 weeks of gestation is "
            "associated with an increased risk of fetal compromise and "
            "stillbirth. Current NICE and RCOG guidance states that all women "
            "reporting RFM after 24 weeks should be assessed with CTG and/or "
            "ultrasound on the same day. Telephone reassurance alone is "
            "not appropriate."
        ),
        nice_ref="NICE CG62 §1.4 (fetal movements); RCOG GTG 57",
        patient_summary=(
            "A reduction in your baby's movements needs assessment at your "
            "maternity unit today. Do not wait — contact them now."
        ),
    ))

    return findings


# ---------------------------------------------------------------------------
# Rule: pre-eclampsia cluster (≥20 weeks)
# ---------------------------------------------------------------------------

def rule_preeclampsia(ctx: PatientContext) -> list[ClinicalFinding]:
    findings: list[ClinicalFinding] = []

    if ctx.weeks < 20:
        return findings

    pe_feature_count = sum([
        ctx.headache_severe,
        ctx.visual_disturbance,
        ctx.facial_hand_swelling,
    ])

    if pe_feature_count >= 2:
        features_present = []
        if ctx.headache_severe:
            features_present.append("severe headache")
        if ctx.visual_disturbance:
            features_present.append("visual disturbances")
        if ctx.facial_hand_swelling:
            features_present.append("facial/hand swelling")

        findings.append(ClinicalFinding(
            rule_name="PREECLAMPSIA_CLUSTER_HIGH",
            symptom="Multiple pre-eclampsia symptoms — urgent BP and urine assessment required",
            detail=f"Features present: {', '.join(features_present)}",
            risk=RiskLevel.HIGH,
            reasoning=(
                "Two or more features from the pre-eclampsia symptom cluster "
                "after 20 weeks of pregnancy — severe headache, visual "
                "disturbances, and sudden swelling of the face or hands — "
                "require immediate blood pressure measurement and urinalysis. "
                "Pre-eclampsia is a potentially serious condition in pregnancy "
                "and assessment should not be deferred to a routine appointment."
            ),
            nice_ref="NICE NG133 §1.2 (diagnosis of pre-eclampsia)",
            patient_summary=(
                "Your symptoms may indicate a serious condition called "
                "pre-eclampsia. Seek urgent care now — go to A&E or call 999."
            ),
        ))

    elif pe_feature_count == 1:
        feature = (
            "severe headache" if ctx.headache_severe
            else "visual disturbances" if ctx.visual_disturbance
            else "facial/hand swelling"
        )
        findings.append(ClinicalFinding(
            rule_name="PREECLAMPSIA_SINGLE_FEATURE",
            symptom="Single pre-eclampsia symptom — requires BP and urine check",
            detail=f"Feature present: {feature}",
            risk=RiskLevel.MEDIUM,
            reasoning=(
                "One feature from the pre-eclampsia symptom cluster warrants "
                "a same-day blood pressure measurement and urinalysis to screen "
                "for pre-eclampsia. If BP is elevated or proteinuria is present, "
                "escalate to HIGH risk management."
            ),
            nice_ref="NICE NG133 §1.2",
            patient_summary=(
                "This symptom may need checking for a condition called "
                "pre-eclampsia. See your GP or midwife today."
            ),
        ))

    return findings


# ---------------------------------------------------------------------------
# Rule: ectopic cluster (early pregnancy <14 weeks)
# ---------------------------------------------------------------------------

def rule_ectopic_cluster(ctx: PatientContext) -> list[ClinicalFinding]:
    findings: list[ClinicalFinding] = []

    if ctx.weeks >= 14:
        return findings

    # Shoulder-tip pain is already handled by rule_pain — avoid duplication
    shoulder_tip_already_flagged = ctx.shoulder_tip_pain

    score = sum([
        ctx.has_bleeding,
        ctx.has_pain and ctx.pain_severity >= 4,
        ctx.dizziness,
    ])

    if score >= 2 or (ctx.has_bleeding and ctx.has_pain and ctx.pain_severity >= 3):
        findings.append(ClinicalFinding(
            rule_name="ECTOPIC_CLUSTER",
            symptom="Symptom combination that may be consistent with ectopic pregnancy",
            detail=(
                f"Bleeding: {ctx.has_bleeding}, "
                f"pain ≥4/10: {ctx.has_pain and ctx.pain_severity >= 4}, "
                f"dizziness: {ctx.dizziness}"
            ),
            risk=RiskLevel.HIGH,
            reasoning=(
                "The combination of early pregnancy (<14 weeks), vaginal "
                "bleeding, and abdominal pain raises concern for ectopic "
                "pregnancy, which requires urgent exclusion by ultrasound and "
                "serum βhCG measurement. Ectopic pregnancy can be life-threatening "
                "if rupture occurs. Emergency assessment should not be delayed."
            ),
            nice_ref="NICE NG25 §1.4 (assessment of suspected ectopic pregnancy)",
            patient_summary=(
                "Your symptoms in early pregnancy need urgent assessment to "
                "check that the pregnancy is in the right place. "
                "Go to A&E now."
            ),
        ))

    return findings


# ---------------------------------------------------------------------------
# Rule: dizziness
# ---------------------------------------------------------------------------

def rule_dizziness(ctx: PatientContext) -> list[ClinicalFinding]:
    findings: list[ClinicalFinding] = []

    if not ctx.dizziness:
        return findings

    if ctx.has_bleeding or (ctx.has_pain and ctx.pain_severity >= 5) or ctx.shoulder_tip_pain:
        findings.append(ClinicalFinding(
            rule_name="DIZZINESS_WITH_PAIN_OR_BLEEDING",
            symptom="Dizziness with pain or bleeding",
            detail="Dizziness reported alongside pain or bleeding",
            risk=RiskLevel.HIGH,
            reasoning=(
                "Dizziness occurring alongside significant pain or vaginal "
                "bleeding may reflect haemodynamic compromise. In early "
                "pregnancy this may be associated with significant blood loss "
                "from ectopic pregnancy or miscarriage. Urgent assessment is "
                "required."
            ),
            nice_ref="NICE NG25 §1.4; NICE CG62 §1.2",
            patient_summary=(
                "Dizziness together with pain or bleeding needs emergency "
                "assessment. Call 999 or go to A&E."
            ),
        ))
    else:
        findings.append(ClinicalFinding(
            rule_name="DIZZINESS_ISOLATED",
            symptom="Dizziness",
            detail="Dizziness without associated pain or bleeding",
            risk=RiskLevel.LOW,
            reasoning=(
                "Mild dizziness in pregnancy is common and may reflect "
                "postural hypotension, anaemia, or low blood sugar. In the "
                "absence of other concerning features, rest and adequate "
                "hydration are appropriate. Mention to the midwife at the "
                "next contact."
            ),
            nice_ref="NICE CG62 §1 (common symptoms in pregnancy)",
            patient_summary=(
                "Mild dizziness can be normal in pregnancy. Rest, stay "
                "hydrated, and mention this to your midwife."
            ),
        ))

    return findings


# ---------------------------------------------------------------------------
# Rule: fever
# ---------------------------------------------------------------------------

def rule_fever(ctx: PatientContext) -> list[ClinicalFinding]:
    findings: list[ClinicalFinding] = []

    if not ctx.fever:
        return findings

    temp_detail = f"{ctx.fever_temp}°C" if ctx.fever_temp > 0 else "temperature not recorded"

    findings.append(ClinicalFinding(
        rule_name="FEVER",
        symptom="Fever",
        detail=f"Fever reported — {temp_detail}",
        risk=RiskLevel.MEDIUM,
        reasoning=(
            "Fever (≥38°C) in pregnancy may indicate infection and should be "
            "assessed promptly. Possible causes include urinary tract infection, "
            "chorioamnionitis, or other systemic infection. Untreated infection "
            "in pregnancy may affect fetal wellbeing and increase the risk of "
            "pre-term labour. A same-day GP or midwife review is recommended."
        ),
        nice_ref="NICE CG62 §1.2 (assessment of infection in pregnancy)",
        patient_summary=(
            "A fever during pregnancy should be assessed by your GP or midwife "
            "today, as infections need treating promptly in pregnancy."
        ),
    ))

    return findings


# ---------------------------------------------------------------------------
# All rules — order determines evaluation sequence (for audit trail)
# ---------------------------------------------------------------------------

ALL_RULES = [
    rule_absolute_emergencies,
    rule_bleeding,
    rule_pain,
    rule_ectopic_cluster,
    rule_nausea,
    rule_discharge,
    rule_itching,
    rule_fetal_movements,
    rule_preeclampsia,
    rule_dizziness,
    rule_fever,
]
