import MedicalKnowledge

namespace ClinicalAudit.ScenarioA

open ClinicalAudit

axiom TaroYamada : Patient
axiom obs_essential_hypertension : HasEssentialHypertension TaroYamada
axiom obs_severe_dehydration     : HasSevereDehydration     TaroYamada

theorem thiazide_indicated :
    Indicated TaroYamada Treatment.thiazideDiuretic :=
  JSH2019_Ch5_FirstLine TaroYamada obs_essential_hypertension

theorem thiazide_contraindicated :
    Contraindicated TaroYamada Treatment.thiazideDiuretic :=
  JSN_AKI2016_Diuretics TaroYamada obs_severe_dehydration

theorem collision_detected :
    Collision TaroYamada Treatment.thiazideDiuretic := by
  unfold Collision
  apply And.intro
  · exact thiazide_indicated
  · exact thiazide_contraindicated

theorem absurd : False := by
  apply incompatible_modalities TaroYamada Treatment.thiazideDiuretic
  exact collision_detected

#print axioms absurd

end ClinicalAudit.ScenarioA
