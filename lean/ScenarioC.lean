/-
  ScenarioC.lean — Acute panic disorder (APA) vs. severe untreated
  obstructive sleep apnoea (AASM).

  58-year-old patient with polysomnography-confirmed severe OSA
  (AHI 42 events/hour, nadir SpO₂ 78%) not yet established on PAP
  therapy presents to the ED in an acute, debilitating panic episode
  unresponsive to verbal de-escalation. The APA panic-disorder guideline
  indicates a short-acting benzodiazepine; the AASM OSA pharmacologic-
  safety statement contraindicates benzodiazepines in untreated severe
  OSA. The two recommendations apply to the same patient and produce a
  deontic collision.

  This file proves, by tactic, that the encoded axioms entail a deontic
  contradiction on `RichardRoe` and therefore `False`.
-/

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
