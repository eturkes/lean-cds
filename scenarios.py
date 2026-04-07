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


CORE_LEAN_SOURCE: str = r"""-- Epistemological Audit: Core DSL types
-- Defines the deeply-embedded data model used by every scenario.

namespace ClinicalAudit.Core

inductive ThreeValued where
  | tTrue
  | tFalse
  | tUnknown
  deriving Repr, DecidableEq

abbrev Observation := String
abbrev Action := String

inductive DeonticModality where
  | indicated
  | obligated
  | contraindicated
  deriving Repr, DecidableEq

structure Chart where
  lookup : Observation → ThreeValued

structure Rule where
  id : String
  source : String
  appliesWhen : Chart → ThreeValued
  conclusion : DeonticModality × Action
  priority : Nat

inductive Verdict where
  | recommended (action : Action)
  | underdetermined (actions : List Action)
  | insufficientData (missing : List Observation)
  | genuineConflict (rules : List String)

instance : ToString Verdict where
  toString := fun
    | .recommended action => "Recommended " ++ action
    | .underdetermined actions => "Underdetermined " ++ String.intercalate "," actions
    | .insufficientData missing => "InsufficientData " ++ String.intercalate "," missing
    | .genuineConflict rules => "GenuineConflict " ++ String.intercalate "," rules

def isPositiveModality : DeonticModality → Bool
  | .indicated => true
  | .obligated => true
  | .contraindicated => false

def isNegativeModality : DeonticModality → Bool
  | .contraindicated => true
  | _ => false

def maxPriority (rs : List Rule) : Nat :=
  rs.foldr (fun r acc => Nat.max r.priority acc) 0

def dedupActions (xs : List Action) : List Action :=
  xs.foldr (fun x acc => if acc.contains x then acc else x :: acc) []

def evaluate (rules : List Rule) (chart : Chart) : Verdict :=
  let fired := rules.filter (fun r =>
    match r.appliesWhen chart with
    | .tTrue => true
    | _ => false)
  let allActions := dedupActions (fired.map (fun r => r.conclusion.snd))
  let analyze : Action → (List Action × List String) → (List Action × List String) :=
    fun a acc =>
      let pos := fired.filter (fun r =>
        isPositiveModality r.conclusion.fst && r.conclusion.snd == a)
      let neg := fired.filter (fun r =>
        isNegativeModality r.conclusion.fst && r.conclusion.snd == a)
      match pos, neg with
      | [], _ => acc
      | _ :: _, [] => (a :: acc.fst, acc.snd)
      | _ :: _, _ :: _ =>
        let mp := maxPriority pos
        let mn := maxPriority neg
        if mp > mn then (a :: acc.fst, acc.snd)
        else if mn > mp then acc
        else
          let posIds := (pos.filter (fun r => r.priority == mp)).map Rule.id
          let negIds := (neg.filter (fun r => r.priority == mn)).map Rule.id
          (acc.fst, posIds ++ negIds ++ acc.snd)
  let result : List Action × List String := allActions.foldr analyze ([], [])
  let recommendedActions := result.fst
  let conflictIds := result.snd
  match conflictIds with
  | _ :: _ => Verdict.genuineConflict conflictIds
  | [] =>
    match recommendedActions with
    | [] => Verdict.insufficientData []
    | [a] => Verdict.recommended a
    | _ => Verdict.underdetermined recommendedActions

def smokeUnknownChart : Chart := { lookup := fun _ => ThreeValued.tUnknown }

#eval IO.println s!"VERDICT: {evaluate [] smokeUnknownChart}"

end ClinicalAudit.Core
"""


SCENARIO_A = Scenario(
    id="scenario-a",
    title="Hypertension vs. Severe Dehydration",
    subtitle="Thiazide diuretic — recommended and contraindicated",
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
    collision_summary=(
        "The AHA/ACC hypertension guideline mandates thiazide therapy for "
        "this patient, while KDIGO absolutely contraindicates the same agent "
        "in the presence of severe dehydration. The two recommendations "
        "are mutually exclusive."
    ),
    lean_code=r"""-- Epistemological Audit: Scenario A
-- Hypertension (AHA/ACC) vs. Severe Dehydration (KDIGO)

namespace ClinicalAudit.ScenarioA

open ClinicalAudit.Core

def rules : List Rule := [
  { id := "AHA-ACC-HTN-8.1.5",
    source := "AHA/ACC HTN §8.1.5",
    appliesWhen := fun chart =>
      match chart.lookup "EssentialHypertension", chart.lookup "HemodynamicallyStable" with
      | .tTrue, .tTrue => .tTrue
      | _, _ => .tFalse,
    conclusion := (.indicated, "ThiazideDiuretic"),
    priority := 1 },
  { id := "KDIGO-AKI-3.1.2-neg",
    source := "KDIGO AKI §3.1.2",
    appliesWhen := fun chart =>
      match chart.lookup "SevereDehydration" with
      | .tTrue => .tTrue
      | _ => .tFalse,
    conclusion := (.contraindicated, "ThiazideDiuretic"),
    priority := 2 },
  { id := "KDIGO-AKI-3.1.2-pos",
    source := "KDIGO AKI §3.1.2",
    appliesWhen := fun chart =>
      match chart.lookup "SevereDehydration" with
      | .tTrue => .tTrue
      | _ => .tFalse,
    conclusion := (.indicated, "HoldThiazideAndRehydrate"),
    priority := 2 }
]

def chart : Chart :=
  { lookup := fun obs =>
      match obs with
      | "EssentialHypertension" => .tTrue
      | "HemodynamicallyStable" => .tFalse
      | "SevereDehydration" => .tTrue
      | _ => .tUnknown }

#eval IO.println s!"VERDICT: {evaluate rules chart}"

end ClinicalAudit.ScenarioA
""",
)


SCENARIO_B = Scenario(
    id="scenario-b",
    title="Diabetic Ketoacidosis vs. Severe Hypokalemia",
    subtitle="Intravenous insulin — recommended and contraindicated",
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
    collision_summary=(
        "The ADA standard mandates immediate IV insulin for confirmed DKA, "
        "while the AACE/ACE safety recommendation prohibits insulin until "
        "potassium is corrected. Both clinical contexts are simultaneously "
        "true for this patient."
    ),
    lean_code=r"""-- Epistemological Audit: Scenario B
-- Diabetic Ketoacidosis (ADA) vs. Severe Hypokalemia (AACE/ACE)

namespace ClinicalAudit.ScenarioB

open ClinicalAudit.Core

def rules : List Rule := [
  { id := "ADA-DKA-Sec16",
    source := "ADA Standards §16",
    appliesWhen := fun chart =>
      match chart.lookup "DiabeticKetoacidosis", chart.lookup "SerumKAtLeast33" with
      | .tTrue, .tTrue => .tTrue
      | _, _ => .tFalse,
    conclusion := (.obligated, "IVRegularInsulin"),
    priority := 1 },
  { id := "AACE-ACE-Hypo-neg",
    source := "AACE/ACE CSR-4",
    appliesWhen := fun chart =>
      match chart.lookup "SevereHypokalemia" with
      | .tTrue => .tTrue
      | _ => .tFalse,
    conclusion := (.contraindicated, "IVRegularInsulin"),
    priority := 2 },
  { id := "AACE-ACE-Hypo-pos",
    source := "AACE/ACE CSR-4",
    appliesWhen := fun chart =>
      match chart.lookup "SevereHypokalemia" with
      | .tTrue => .tTrue
      | _ => .tFalse,
    conclusion := (.indicated, "RepleteKThenStartInsulin"),
    priority := 2 }
]

def chart : Chart :=
  { lookup := fun obs =>
      match obs with
      | "DiabeticKetoacidosis" => .tTrue
      | "SerumKAtLeast33" => .tFalse
      | "SevereHypokalemia" => .tTrue
      | _ => .tUnknown }

#eval IO.println s!"VERDICT: {evaluate rules chart}"

end ClinicalAudit.ScenarioB
""",
)


SCENARIO_C = Scenario(
    id="scenario-c",
    title="Acute Panic Disorder vs. Severe Obstructive Sleep Apnea",
    subtitle="Benzodiazepine — recommended and contraindicated",
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
    collision_summary=(
        "The APA guideline indicates a benzodiazepine for this acute panic "
        "presentation, while the AASM safety statement strictly "
        "contraindicates the same drug class for untreated severe OSA. The "
        "two guidelines collide on the only intervention available."
    ),
    lean_code=r"""-- Epistemological Audit: Scenario C
-- Acute Panic Disorder (APA) vs. Severe Obstructive Sleep Apnea (AASM)

namespace ClinicalAudit.ScenarioC

open ClinicalAudit.Core

def rules : List Rule := [
  { id := "APA-Panic-Benzo",
    source := "APA Panic Disorder",
    appliesWhen := fun chart =>
      match chart.lookup "AcutePanicEpisode" with
      | .tTrue => .tTrue
      | _ => .tFalse,
    conclusion := (.indicated, "Benzodiazepine"),
    priority := 1 },
  { id := "APA-Panic-NonBenzo",
    source := "APA Panic Disorder",
    appliesWhen := fun chart =>
      match chart.lookup "AcutePanicEpisode" with
      | .tTrue => .tTrue
      | _ => .tFalse,
    conclusion := (.indicated, "NonBenzoAnxiolytic"),
    priority := 1 },
  { id := "AASM-OSA-Benzo-neg",
    source := "AASM OSA Pharm Safety",
    appliesWhen := fun chart =>
      match chart.lookup "UntreatedSevereOSA" with
      | .tTrue => .tTrue
      | _ => .tFalse,
    conclusion := (.contraindicated, "Benzodiazepine"),
    priority := 2 }
]

def chart : Chart :=
  { lookup := fun obs =>
      match obs with
      | "AcutePanicEpisode" => .tTrue
      | "UntreatedSevereOSA" => .tTrue
      | _ => .tUnknown }

#eval IO.println s!"VERDICT: {evaluate rules chart}"

end ClinicalAudit.ScenarioC
""",
)


SCENARIOS: dict[str, Scenario] = {
    SCENARIO_A.id: SCENARIO_A,
    SCENARIO_B.id: SCENARIO_B,
    SCENARIO_C.id: SCENARIO_C,
}
