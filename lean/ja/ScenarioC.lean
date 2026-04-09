import MedicalKnowledge

namespace ClinicalAudit.ScenarioC

open ClinicalAudit

axiom IchiroTanaka : Patient
axiom obs_acute_panic_episode  : HasAcutePanicEpisode  IchiroTanaka
axiom obs_untreated_severe_osa : HasUntreatedSevereOSA IchiroTanaka

theorem benzo_indicated :
    Indicated IchiroTanaka Treatment.benzodiazepine :=
  JSAD_JSNP_Panic2025_Acute IchiroTanaka obs_acute_panic_episode

theorem benzo_contraindicated :
    Contraindicated IchiroTanaka Treatment.benzodiazepine :=
  JRS_SAS2020_BZD IchiroTanaka obs_untreated_severe_osa

theorem collision_detected :
    Collision IchiroTanaka Treatment.benzodiazepine := by
  unfold Collision
  apply And.intro
  · exact benzo_indicated
  · exact benzo_contraindicated

theorem absurd : False := by
  apply incompatible_modalities IchiroTanaka Treatment.benzodiazepine
  exact collision_detected

#print axioms absurd

end ClinicalAudit.ScenarioC
