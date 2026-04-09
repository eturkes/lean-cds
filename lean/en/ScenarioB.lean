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
