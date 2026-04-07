/-
  ScenarioB.lean — Diabetic ketoacidosis (ADA) vs. severe hypokalaemia
  (AACE/ACE).

  34-year-old patient with type 1 diabetes presents in DKA (plasma glucose
  612 mg/dL, arterial pH 7.18, HCO₃⁻ 9 mEq/L, anion gap 28, moderate
  ketonuria) with a measured serum potassium of 2.9 mEq/L. The ADA
  Standards of Care indicate IV regular insulin for DKA; the AACE/ACE
  Critical Safety Recommendation contraindicates insulin until potassium
  has been repleted to ≥ 3.3 mEq/L. The literal reading of the ADA rule
  fires before the precondition is satisfied, producing a deontic
  collision on the same patient.

  This file proves, by tactic, that the encoded axioms entail a deontic
  contradiction on `JaneRoe` and therefore `False`.
-/

import MedicalKnowledge

namespace ClinicalAudit.ScenarioB

open ClinicalAudit

axiom JaneRoe : Patient
axiom obs_diabetic_ketoacidosis : HasDiabeticKetoacidosis JaneRoe
axiom obs_severe_hypokalemia    : HasSevereHypokalemia    JaneRoe

theorem insulin_indicated :
    Indicated JaneRoe Treatment.ivRegularInsulin :=
  ADA_DKA_Sec16 JaneRoe obs_diabetic_ketoacidosis

theorem insulin_contraindicated :
    Contraindicated JaneRoe Treatment.ivRegularInsulin :=
  AACE_ACE_CSR4 JaneRoe obs_severe_hypokalemia

theorem collision_detected :
    Collision JaneRoe Treatment.ivRegularInsulin := by
  unfold Collision
  apply And.intro
  · exact insulin_indicated
  · exact insulin_contraindicated

theorem absurd : False := by
  apply incompatible_modalities JaneRoe Treatment.ivRegularInsulin
  exact collision_detected

#print axioms absurd

end ClinicalAudit.ScenarioB
