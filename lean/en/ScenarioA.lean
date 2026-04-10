import MedicalKnowledge

namespace ClinicalAudit.ScenarioA

open ClinicalAudit

axiom JohnDoe : Patient
axiom obs_essential_hypertension : HasEssentialHypertension JohnDoe
axiom obs_severe_dehydration     : HasSevereDehydration     JohnDoe

theorem thiazide_indicated :
    Indicated JohnDoe Treatment.thiazideDiuretic :=
  AHA_ACC_HTN_8_1_6 JohnDoe obs_essential_hypertension

theorem thiazide_contraindicated :
    Contraindicated JohnDoe Treatment.thiazideDiuretic :=
  KDIGO_AKI_3_4 JohnDoe obs_severe_dehydration

theorem collision_detected :
    Collision JohnDoe Treatment.thiazideDiuretic := by
  unfold Collision
  apply And.intro
  · exact thiazide_indicated
  · exact thiazide_contraindicated

theorem absurd : False := by
  apply incompatible_modalities JohnDoe Treatment.thiazideDiuretic
  exact collision_detected

#print axioms absurd

end ClinicalAudit.ScenarioA
