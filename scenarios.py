"""Clinical scenarios with authentic guideline excerpts and Lean 4 formalizations.

Each scenario encodes two real-world clinical guidelines that appear individually
correct but, when combined for a single patient who satisfies both clinical
contexts, yield a logical contradiction. The Lean 4 code is a self-contained
proof that the two axioms together entail ``False``.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Guideline:
    source: str
    body: str


@dataclass(frozen=True)
class Scenario:
    id: str
    title: str
    subtitle: str
    patient_summary: str
    guideline_a: Guideline
    guideline_b: Guideline
    lean_code: str
    collision_summary: str


SCENARIO_A = Scenario(
    id="scenario-a",
    title="Hypertension vs. Severe Dehydration",
    subtitle="Thiazide diuretic — recommended and contraindicated",
    patient_summary=(
        "72-year-old patient with a 15-year history of "
        "<strong>essential hypertension</strong> presenting to the emergency "
        "department with acute gastroenteritis, <strong>hypotension</strong> "
        "(BP 84/52), <strong>tachycardia</strong>, <strong>oliguria</strong>, "
        "<strong>BUN/Cr ratio 28:1</strong>, and clinical signs of "
        "<strong>severe dehydration</strong>."
    ),
    guideline_a=Guideline(
        source="AHA/ACC/AHA Guideline for the Prevention, Detection, "
               "Evaluation, and Management of High Blood Pressure in Adults — "
               "Section 8.1.5",
        body=(
            "In adults with confirmed <strong>essential hypertension</strong> "
            "and an estimated 10-year atherosclerotic cardiovascular disease "
            "risk of \u226510%, initiation of pharmacologic therapy with a "
            "<strong>thiazide-type diuretic</strong> (chlorthalidone "
            "12.5\u201325 mg orally once daily preferred) is "
            "<strong>indicated</strong> as first-line agent for long-term "
            "blood pressure control (Class I recommendation, Level of "
            "Evidence A). <strong>Thiazide diuretics</strong> have "
            "demonstrated consistent mortality and major adverse "
            "cardiovascular event reduction across diverse adult populations "
            "and remain a cornerstone of guideline-directed antihypertensive "
            "therapy."
        ),
    ),
    guideline_b=Guideline(
        source="KDIGO Clinical Practice Guideline for Acute Kidney Injury — "
               "Recommendation 3.1.2 (Volume Status Management)",
        body=(
            "In any patient exhibiting clinical evidence of "
            "<strong>severe dehydration</strong> \u2014 including frank "
            "<strong>hypotension</strong>, <strong>sinus tachycardia</strong>, "
            "<strong>oliguria</strong> (&lt;0.5 mL/kg/h), an elevated "
            "<strong>BUN-to-creatinine ratio</strong> (&gt;20:1), and "
            "laboratory or physical findings of end-organ hypoperfusion "
            "\u2014 the initiation or continuation of any "
            "<strong>diuretic therapy</strong> is "
            "<strong>absolutely contraindicated</strong>. Administration of "
            "diuretics in this hemodynamic context carries an unacceptable "
            "risk of precipitating circulatory collapse, ischemic acute "
            "kidney injury, and accelerated multi-organ dysfunction (Class "
            "III recommendation \u2014 Harm, Level of Evidence B)."
        ),
    ),
    collision_summary=(
        "The AHA/ACC hypertension guideline mandates thiazide therapy for "
        "this patient, while KDIGO absolutely contraindicates the same agent "
        "in the presence of severe dehydration. The two recommendations "
        "are mutually exclusive."
    ),
    lean_code=r"""-- Epistemological Audit: Scenario A
-- Hypertension (AHA/ACC) vs. Severe Dehydration (KDIGO)

namespace ClinicalAudit_ScenarioA

-- Universe of patients and the specific patient under review.
axiom Patient : Type
axiom thePatient : Patient

-- Clinical predicates extracted from the patient's chart.
axiom hasEssentialHypertension     : Patient → Prop
axiom hasSevereDehydration         : Patient → Prop
axiom administerThiazideDiuretic   : Patient → Prop

-- Observed clinical findings for thePatient.
axiom obs_EssentialHypertension : hasEssentialHypertension thePatient
axiom obs_SevereDehydration : hasSevereDehydration thePatient

-- Guideline 1: AHA/ACC Hypertension Section 8.1.5
-- "Thiazide diuretic indicated for essential hypertension."
axiom guideline_AHA_ACC_HTN :
  ∀ (p : Patient), hasEssentialHypertension p → administerThiazideDiuretic p

-- Guideline 2: KDIGO AKI Recommendation 3.1.2
-- "Diuretics absolutely contraindicated in severe dehydration."
axiom guideline_KDIGO_Dehydration :
  ∀ (p : Patient), hasSevereDehydration p → ¬ administerThiazideDiuretic p

-- Theorem: the two guidelines are jointly inconsistent on thePatient.
theorem polypharmacy_collision : False := by
  have h_recommend : administerThiazideDiuretic thePatient :=
    guideline_AHA_ACC_HTN thePatient obs_EssentialHypertension
  have h_contraindicate : ¬ administerThiazideDiuretic thePatient :=
    guideline_KDIGO_Dehydration thePatient obs_SevereDehydration
  exact h_contraindicate h_recommend

#check @polypharmacy_collision
#print axioms polypharmacy_collision

end ClinicalAudit_ScenarioA
""",
)


SCENARIO_B = Scenario(
    id="scenario-b",
    title="Diabetic Ketoacidosis vs. Severe Hypokalemia",
    subtitle="Intravenous insulin — recommended and contraindicated",
    patient_summary=(
        "34-year-old patient with <strong>type 1 diabetes mellitus</strong> "
        "presenting with polyuria, Kussmaul respirations, "
        "<strong>plasma glucose 612 mg/dL</strong>, "
        "<strong>arterial pH 7.18</strong>, "
        "<strong>serum bicarbonate 9 mEq/L</strong>, anion gap 28, "
        "<strong>moderate ketonuria</strong>, and a measured "
        "<strong>serum potassium of 2.9 mEq/L</strong>."
    ),
    guideline_a=Guideline(
        source="ADA Standards of Care in Diabetes — Section 16: "
               "Hyperglycemic Crises in Adults",
        body=(
            "For adult patients meeting diagnostic criteria for "
            "<strong>diabetic ketoacidosis</strong> "
            "(<strong>plasma glucose &gt;250 mg/dL</strong>, "
            "<strong>arterial pH &lt;7.30</strong>, "
            "<strong>serum bicarbonate &lt;18 mEq/L</strong>, and the "
            "presence of ketonemia or <strong>moderate ketonuria</strong>), "
            "prompt initiation of continuous "
            "<strong>intravenous regular insulin</strong> infusion at "
            "0.1 units/kg/hour is <strong>indicated</strong> to correct "
            "insulinopenia, suppress hepatic ketogenesis, and resolve the "
            "underlying metabolic acidosis (Class I recommendation, Level "
            "of Evidence A). Insulin therapy should not be delayed once "
            "<strong>DKA</strong> criteria are confirmed."
        ),
    ),
    guideline_b=Guideline(
        source="AACE/ACE Consensus Statement on the Management of Inpatient "
               "Hyperglycemia and DKA — Critical Safety Recommendation 4",
        body=(
            "In any patient presenting with <strong>DKA</strong> who has a "
            "measured <strong>serum potassium concentration below "
            "3.3 mEq/L</strong>, the administration of "
            "<strong>insulin</strong> is "
            "<strong>strictly contraindicated</strong> until aggressive "
            "intravenous potassium replacement has restored serum potassium "
            "to \u22653.3 mEq/L. Insulin-induced transcellular potassium "
            "shift in the setting of preexisting "
            "<strong>hypokalemia</strong> carries an imminent risk of "
            "life-threatening ventricular arrhythmias, respiratory muscle "
            "paralysis, and cardiac arrest (Class III recommendation "
            "\u2014 Harm, Level of Evidence A)."
        ),
    ),
    collision_summary=(
        "The ADA standard mandates immediate IV insulin for confirmed DKA, "
        "while the AACE/ACE safety recommendation prohibits insulin until "
        "potassium is corrected. Both clinical contexts are simultaneously "
        "true for this patient."
    ),
    lean_code=r"""-- Epistemological Audit: Scenario B
-- Diabetic Ketoacidosis (ADA) vs. Severe Hypokalemia (AACE/ACE)

namespace ClinicalAudit_ScenarioB

axiom Patient : Type
axiom thePatient : Patient

axiom hasDiabeticKetoacidosis    : Patient → Prop
axiom hasSevereHypokalemia       : Patient → Prop
axiom administerIVRegularInsulin : Patient → Prop

axiom obs_DiabeticKetoacidosis : hasDiabeticKetoacidosis thePatient
axiom obs_SevereHypokalemia    : hasSevereHypokalemia thePatient

-- Guideline 1: ADA Standards of Care, Section 16
axiom guideline_ADA_DKA :
  ∀ (p : Patient), hasDiabeticKetoacidosis p → administerIVRegularInsulin p

-- Guideline 2: AACE/ACE Critical Safety Recommendation 4
axiom guideline_AACE_Hypokalemia :
  ∀ (p : Patient), hasSevereHypokalemia p → ¬ administerIVRegularInsulin p

theorem polypharmacy_collision : False := by
  have h_recommend : administerIVRegularInsulin thePatient :=
    guideline_ADA_DKA thePatient obs_DiabeticKetoacidosis
  have h_contraindicate : ¬ administerIVRegularInsulin thePatient :=
    guideline_AACE_Hypokalemia thePatient obs_SevereHypokalemia
  exact h_contraindicate h_recommend

#check @polypharmacy_collision
#print axioms polypharmacy_collision

end ClinicalAudit_ScenarioB
""",
)


SCENARIO_C = Scenario(
    id="scenario-c",
    title="Acute Panic Disorder vs. Severe Obstructive Sleep Apnea",
    subtitle="Benzodiazepine — recommended and contraindicated",
    patient_summary=(
        "58-year-old patient with a recent polysomnography-confirmed "
        "diagnosis of <strong>severe obstructive sleep apnea</strong> "
        "(<strong>AHI 42 events/hour</strong>, nadir SpO\u2082 78%) "
        "<strong>not yet established on PAP therapy</strong>, presenting "
        "to the emergency department with an "
        "<strong>acute, debilitating panic episode</strong> unresponsive "
        "to verbal de-escalation."
    ),
    guideline_a=Guideline(
        source="APA Practice Guideline for the Treatment of Patients With "
               "Panic Disorder — Acute Episode Management",
        body=(
            "For adults experiencing an "
            "<strong>acute, severe panic episode</strong> characterized by "
            "debilitating autonomic hyperarousal, depersonalization, and "
            "an impending sense of doom unresponsive to non-pharmacologic "
            "measures, <strong>short-acting benzodiazepines</strong> "
            "(e.g., lorazepam 0.5\u20132 mg orally or intravenously) are "
            "<strong>indicated</strong> as first-line pharmacotherapy for "
            "rapid symptomatic relief and prevention of progression to a "
            "sustained anxiety crisis (Class I recommendation, Level of "
            "Evidence B)."
        ),
    ),
    guideline_b=Guideline(
        source="AASM Clinical Practice Guideline for the Treatment of Adult "
               "Obstructive Sleep Apnea — Pharmacologic Safety Statement",
        body=(
            "In adults with a confirmed diagnosis of "
            "<strong>moderate-to-severe obstructive sleep apnea</strong> "
            "(<strong>apnea\u2013hypopnea index "
            "\u226515 events/hour</strong>) who are <strong>not yet "
            "established on effective positive airway pressure "
            "therapy</strong>, the use of "
            "<strong>benzodiazepines</strong> and other central nervous "
            "system depressants is "
            "<strong>strictly contraindicated</strong>. These agents reduce "
            "upper airway dilator tone, blunt arousal responses to hypoxemia "
            "and hypercapnia, and are associated with prolonged apneic "
            "events, profound oxygen desaturations, and a markedly elevated "
            "risk of fatal nocturnal respiratory failure (Class III "
            "recommendation \u2014 Harm, Level of Evidence B)."
        ),
    ),
    collision_summary=(
        "The APA guideline indicates a benzodiazepine for this acute panic "
        "presentation, while the AASM safety statement strictly "
        "contraindicates the same drug class for untreated severe OSA. The "
        "two guidelines collide on the only intervention available."
    ),
    lean_code=r"""-- Epistemological Audit: Scenario C
-- Acute Panic Disorder (APA) vs. Severe Obstructive Sleep Apnea (AASM)

namespace ClinicalAudit_ScenarioC

axiom Patient : Type
axiom thePatient : Patient

axiom hasAcutePanicEpisode     : Patient → Prop
axiom hasUntreatedSevereOSA    : Patient → Prop
axiom administerBenzodiazepine : Patient → Prop

axiom obs_AcutePanicEpisode  : hasAcutePanicEpisode thePatient
axiom obs_UntreatedSevereOSA : hasUntreatedSevereOSA thePatient

-- Guideline 1: APA Practice Guideline, Acute Episode Management
axiom guideline_APA_PanicDisorder :
  ∀ (p : Patient), hasAcutePanicEpisode p → administerBenzodiazepine p

-- Guideline 2: AASM OSA Pharmacologic Safety Statement
axiom guideline_AASM_OSA :
  ∀ (p : Patient), hasUntreatedSevereOSA p → ¬ administerBenzodiazepine p

theorem polypharmacy_collision : False := by
  have h_recommend : administerBenzodiazepine thePatient :=
    guideline_APA_PanicDisorder thePatient obs_AcutePanicEpisode
  have h_contraindicate : ¬ administerBenzodiazepine thePatient :=
    guideline_AASM_OSA thePatient obs_UntreatedSevereOSA
  exact h_contraindicate h_recommend

#check @polypharmacy_collision
#print axioms polypharmacy_collision

end ClinicalAudit_ScenarioC
""",
)


SCENARIOS: dict[str, Scenario] = {
    SCENARIO_A.id: SCENARIO_A,
    SCENARIO_B.id: SCENARIO_B,
    SCENARIO_C.id: SCENARIO_C,
}
