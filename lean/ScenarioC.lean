import MedicalKnowledge

namespace ClinicalAudit.ScenarioC

open ClinicalAudit

axiom RichardRoe : Patient
axiom obs_acute_panic_episode : HasAcutePanicEpisode RichardRoe
axiom obs_untreated_severe_osa : HasUntreatedSevereOSA RichardRoe

theorem benzo_indicated :
    Indicated RichardRoe Treatment.benzodiazepine :=
  APA_Panic_Acute RichardRoe obs_acute_panic_episode

theorem benzo_contraindicated :
    Contraindicated RichardRoe Treatment.benzodiazepine :=
  AASM_OSA_PharmSafety RichardRoe obs_untreated_severe_osa

theorem collision_detected :
    Collision RichardRoe Treatment.benzodiazepine := by
  unfold Collision
  apply And.intro
  · exact benzo_indicated
  · exact benzo_contraindicated

theorem absurd : False := by
  apply incompatible_modalities RichardRoe Treatment.benzodiazepine
  exact collision_detected

#print axioms absurd

end ClinicalAudit.ScenarioC
