"""Clinical scenarios with authentic guideline excerpts and Lean 4 metadata.

Each scenario describes a single patient context in which two real-world
clinical guidelines collide. The actual formal verification lives in static
``.lean`` files under the ``lean/`` directory; this module merely declares
the ID-to-filename mapping plus the natural-language metadata that the UI
needs to render the scenario panel.

The host process never injects user-controlled strings into the Lean source.
Each scenario references a pre-written file by name, and the verifier
invokes ``lean`` against that file directly.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

LEAN_DIR: Path = Path(__file__).resolve().parent / "lean"
KNOWLEDGE_BASE_FILE: Path = LEAN_DIR / "MedicalKnowledge.lean"
KNOWLEDGE_BASE_MODULE: str = "MedicalKnowledge"


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
    lean_filename: str
    audit_summary: str
    plain_english: str

    @property
    def lean_path(self) -> Path:
        return LEAN_DIR / self.lean_filename

    def read_lean_source(self) -> str:
        return self.lean_path.read_text(encoding="utf-8")


SCENARIO_A = Scenario(
    id="scenario-a",
    title="Hypertension vs. Severe Dehydration",
    subtitle="Thiazide diuretic — indicated and contraindicated",
    patient_summary=(
        "72-year-old patient with a 15-year history of "
        "<strong class=\"cds-cond\">essential hypertension</strong> "
        "presenting to the emergency department with acute gastroenteritis, "
        "<strong class=\"cds-find\">hypotension</strong> (BP 84/52), "
        "<strong class=\"cds-find\">tachycardia</strong>, "
        "<strong class=\"cds-find\">oliguria</strong>, "
        "<strong class=\"cds-find\">BUN/Cr ratio 28:1</strong>, and "
        "clinical signs of "
        "<strong class=\"cds-cond\">severe dehydration</strong>."
    ),
    guideline_a=Guideline(
        source="AHA/ACC/AHA Guideline for the Prevention, Detection, "
               "Evaluation, and Management of High Blood Pressure in Adults — "
               "Section 8.1.5",
        body=(
            "In adults with confirmed "
            "<strong class=\"cds-cond\">essential hypertension</strong> and "
            "an estimated 10-year atherosclerotic cardiovascular disease "
            "risk of \u226510%, initiation of pharmacologic therapy with a "
            "<strong class=\"cds-int\">thiazide-type diuretic</strong> "
            "(chlorthalidone 12.5\u201325 mg orally once daily preferred) "
            "is <strong class=\"cds-ind\">indicated</strong> as first-line "
            "agent for long-term blood pressure control (Class I "
            "recommendation, Level of Evidence A). "
            "<strong class=\"cds-int\">Thiazide diuretics</strong> have "
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
            "<strong class=\"cds-cond\">severe dehydration</strong> \u2014 "
            "including frank "
            "<strong class=\"cds-find\">hypotension</strong>, "
            "<strong class=\"cds-find\">sinus tachycardia</strong>, "
            "<strong class=\"cds-find\">oliguria</strong> (&lt;0.5 mL/kg/h), "
            "an elevated "
            "<strong class=\"cds-find\">BUN-to-creatinine ratio</strong> "
            "(&gt;20:1), and laboratory or physical findings of end-organ "
            "hypoperfusion \u2014 the initiation or continuation of any "
            "<strong class=\"cds-int\">diuretic therapy</strong> is "
            "<strong class=\"cds-con\">absolutely contraindicated</strong>. "
            "Administration of diuretics in this hemodynamic context "
            "carries an unacceptable risk of precipitating circulatory "
            "collapse, ischemic acute kidney injury, and accelerated "
            "multi-organ dysfunction (Class III recommendation \u2014 Harm, "
            "Level of Evidence B)."
        ),
    ),
    lean_filename="ScenarioA.lean",
    audit_summary=(
        "The Lean 4 Formalization above proves "
        "<code>Indicated JohnDoe ThiazideDiuretic \u2227 "
        "Contraindicated JohnDoe ThiazideDiuretic</code> from the AHA/ACC "
        "and KDIGO axioms, then derives <code>False</code> via "
        "<code>incompatible_modalities</code>. The kernel-trusted axiom "
        "list is the precise set of guidelines and chart findings "
        "participating in the contradiction."
    ),
    plain_english=(
        "The system has mathematically proven that, for this 72-year-old "
        "patient, it is impossible to simultaneously follow Guideline 1 "
        "(the AHA/ACC recommendation to start a thiazide diuretic for "
        "essential hypertension) and Guideline 2 (the KDIGO safety "
        "statement that forbids any diuretic in severe dehydration) "
        "without violating the fundamental rule that a single drug "
        "cannot be both <em>indicated</em> and <em>contraindicated</em> "
        "for the same patient at the same time."
    ),
)


SCENARIO_B = Scenario(
    id="scenario-b",
    title="Diabetic Ketoacidosis vs. Severe Hypokalemia",
    subtitle="Intravenous insulin — indicated and contraindicated",
    patient_summary=(
        "34-year-old patient with type 1 diabetes mellitus presenting with "
        "polyuria, Kussmaul respirations, "
        "<strong class=\"cds-find\">plasma glucose 612 mg/dL</strong>, "
        "<strong class=\"cds-find\">arterial pH 7.18</strong>, "
        "<strong class=\"cds-find\">serum bicarbonate 9 mEq/L</strong>, "
        "anion gap 28, "
        "<strong class=\"cds-find\">moderate ketonuria</strong>, and a "
        "measured "
        "<strong class=\"cds-find\">serum potassium of 2.9 mEq/L</strong>."
    ),
    guideline_a=Guideline(
        source="ADA Standards of Care in Diabetes — Section 16: "
               "Hyperglycemic Crises in Adults",
        body=(
            "For adult patients meeting diagnostic criteria for "
            "<strong class=\"cds-cond\">diabetic ketoacidosis</strong> "
            "(<strong class=\"cds-find\">plasma glucose &gt;250 mg/dL</strong>, "
            "<strong class=\"cds-find\">arterial pH &lt;7.30</strong>, "
            "<strong class=\"cds-find\">serum bicarbonate &lt;18 mEq/L</strong>, "
            "and the presence of ketonemia or "
            "<strong class=\"cds-find\">moderate ketonuria</strong>), "
            "prompt initiation of continuous "
            "<strong class=\"cds-int\">intravenous regular insulin</strong> "
            "infusion at 0.1 units/kg/hour is "
            "<strong class=\"cds-ind\">indicated</strong> to correct "
            "insulinopenia, suppress hepatic ketogenesis, and resolve the "
            "underlying metabolic acidosis (Class I recommendation, Level "
            "of Evidence A). Insulin therapy should not be delayed once "
            "<strong class=\"cds-cond\">DKA</strong> criteria are confirmed."
        ),
    ),
    guideline_b=Guideline(
        source="AACE/ACE Consensus Statement on the Management of Inpatient "
               "Hyperglycemia and DKA — Critical Safety Recommendation 4",
        body=(
            "In any patient presenting with "
            "<strong class=\"cds-cond\">DKA</strong> who has a measured "
            "<strong class=\"cds-find\">serum potassium concentration below "
            "3.3 mEq/L</strong>, the administration of "
            "<strong class=\"cds-int\">insulin</strong> is "
            "<strong class=\"cds-con\">strictly contraindicated</strong> "
            "until aggressive intravenous potassium replacement has restored "
            "serum potassium to \u22653.3 mEq/L. Insulin-induced "
            "transcellular potassium shift in the setting of preexisting "
            "<strong class=\"cds-cond\">hypokalemia</strong> carries an "
            "imminent risk of life-threatening ventricular arrhythmias, "
            "respiratory muscle paralysis, and cardiac arrest (Class III "
            "recommendation \u2014 Harm, Level of Evidence A)."
        ),
    ),
    lean_filename="ScenarioB.lean",
    audit_summary=(
        "The Lean 4 Formalization above proves "
        "<code>Indicated JaneRoe IVRegularInsulin \u2227 "
        "Contraindicated JaneRoe IVRegularInsulin</code> from the ADA and "
        "AACE/ACE axioms, then derives <code>False</code> via "
        "<code>incompatible_modalities</code>. The literal reading of the "
        "ADA insulin axiom drops the K\u207a \u2265 3.3 mEq/L precondition, "
        "which is exactly the encoder bug the audit is designed to expose."
    ),
    plain_english=(
        "The system has mathematically proven that, for this 34-year-old "
        "patient in diabetic ketoacidosis with a serum potassium of "
        "2.9 mEq/L, it is impossible to simultaneously follow Guideline 1 "
        "(the ADA Standards of Care directive to start IV regular insulin "
        "in DKA) and Guideline 2 (the AACE/ACE critical safety "
        "recommendation that forbids insulin while serum potassium is "
        "below 3.3 mEq/L) without violating the fundamental rule that a "
        "single drug cannot be both <em>indicated</em> and "
        "<em>contraindicated</em> for the same patient at the same time."
    ),
)


SCENARIO_C = Scenario(
    id="scenario-c",
    title="Acute Panic Disorder vs. Severe Obstructive Sleep Apnea",
    subtitle="Benzodiazepine — indicated and contraindicated",
    patient_summary=(
        "58-year-old patient with a recent polysomnography-confirmed "
        "diagnosis of "
        "<strong class=\"cds-cond\">severe obstructive sleep apnea</strong> "
        "(<strong class=\"cds-find\">AHI 42 events/hour</strong>, nadir "
        "SpO\u2082 78%) "
        "<strong class=\"cds-find\">not yet established on PAP "
        "therapy</strong>, presenting to the emergency department with an "
        "<strong class=\"cds-cond\">acute, debilitating panic "
        "episode</strong> unresponsive to verbal de-escalation."
    ),
    guideline_a=Guideline(
        source="APA Practice Guideline for the Treatment of Patients With "
               "Panic Disorder — Acute Episode Management",
        body=(
            "For adults experiencing an "
            "<strong class=\"cds-cond\">acute, severe panic episode</strong> "
            "characterized by debilitating autonomic hyperarousal, "
            "depersonalization, and an impending sense of doom unresponsive "
            "to non-pharmacologic measures, "
            "<strong class=\"cds-int\">short-acting benzodiazepines</strong> "
            "(e.g., lorazepam 0.5\u20132 mg orally or intravenously) are "
            "<strong class=\"cds-ind\">indicated</strong> as first-line "
            "pharmacotherapy for rapid symptomatic relief and prevention of "
            "progression to a sustained anxiety crisis (Class I "
            "recommendation, Level of Evidence B)."
        ),
    ),
    guideline_b=Guideline(
        source="AASM Clinical Practice Guideline for the Treatment of Adult "
               "Obstructive Sleep Apnea — Pharmacologic Safety Statement",
        body=(
            "In adults with a confirmed diagnosis of "
            "<strong class=\"cds-cond\">moderate-to-severe obstructive "
            "sleep apnea</strong> "
            "(<strong class=\"cds-find\">apnea\u2013hypopnea index "
            "\u226515 events/hour</strong>) who are "
            "<strong class=\"cds-find\">not yet established on effective "
            "positive airway pressure therapy</strong>, the use of "
            "<strong class=\"cds-int\">benzodiazepines</strong> and other "
            "central nervous system depressants is "
            "<strong class=\"cds-con\">strictly contraindicated</strong>. "
            "These agents reduce upper airway dilator tone, blunt arousal "
            "responses to hypoxemia and hypercapnia, and are associated "
            "with prolonged apneic events, profound oxygen desaturations, "
            "and a markedly elevated risk of fatal nocturnal respiratory "
            "failure (Class III recommendation \u2014 Harm, Level of "
            "Evidence B)."
        ),
    ),
    lean_filename="ScenarioC.lean",
    audit_summary=(
        "The Lean 4 Formalization above proves "
        "<code>Indicated RichardRoe Benzodiazepine \u2227 "
        "Contraindicated RichardRoe Benzodiazepine</code> from the APA and "
        "AASM axioms, then derives <code>False</code> via "
        "<code>incompatible_modalities</code>. The audit surfaces the "
        "literal collision the APA recommendation produces in untreated "
        "severe OSA."
    ),
    plain_english=(
        "The system has mathematically proven that, for this 58-year-old "
        "patient with polysomnography-confirmed severe obstructive sleep "
        "apnea who is not yet on PAP therapy, it is impossible to "
        "simultaneously follow Guideline 1 (the APA panic-disorder "
        "recommendation to administer a short-acting benzodiazepine for "
        "an acute episode) and Guideline 2 (the AASM safety statement "
        "forbidding benzodiazepines in untreated severe OSA) without "
        "violating the fundamental rule that a single drug cannot be "
        "both <em>indicated</em> and <em>contraindicated</em> for the "
        "same patient at the same time."
    ),
)


SCENARIOS: dict[str, Scenario] = {
    SCENARIO_A.id: SCENARIO_A,
    SCENARIO_B.id: SCENARIO_B,
    SCENARIO_C.id: SCENARIO_C,
}
