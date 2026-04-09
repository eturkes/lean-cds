import MedicalKnowledge

namespace ClinicalAudit.ScenarioB

open ClinicalAudit

axiom HanakoSuzuki : Patient
axiom obs_diabetic_ketoacidosis : HasDiabeticKetoacidosis HanakoSuzuki
axiom obs_severe_hypokalemia    : HasSevereHypokalemia    HanakoSuzuki

theorem insulin_indicated :
    Indicated HanakoSuzuki Treatment.ivRegularInsulin :=
  JDS2024_Sec20_1_DKA HanakoSuzuki obs_diabetic_ketoacidosis

theorem insulin_contraindicated :
    Contraindicated HanakoSuzuki Treatment.ivRegularInsulin :=
  JDS2024_Sec20_1_KMgmt HanakoSuzuki obs_severe_hypokalemia

theorem collision_detected :
    Collision HanakoSuzuki Treatment.ivRegularInsulin := by
  unfold Collision
  apply And.intro
  · exact insulin_indicated
  · exact insulin_contraindicated

theorem absurd : False := by
  apply incompatible_modalities HanakoSuzuki Treatment.ivRegularInsulin
  exact collision_detected

#print axioms absurd

end ClinicalAudit.ScenarioB
