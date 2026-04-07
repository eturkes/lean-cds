/-
  ScenarioA.lean — Hypertension (AHA/ACC) vs. severe dehydration (KDIGO).

  72-year-old patient with a 15-year history of essential hypertension
  presents to the ED with acute gastroenteritis and clinical signs of
  severe dehydration. The AHA/ACC HTN guideline indicates a thiazide
  diuretic; the KDIGO AKI guideline contraindicates any diuretic in this
  hemodynamic context. The two recommendations apply simultaneously and
  the patient cannot lawfully receive both.

  This file proves, by tactic, that the encoded axioms entail a deontic
  contradiction for `JohnDoe`, and therefore — via `incompatible_modalities`
  — entail `False`. The final `#print axioms` line emits the precise list
  of axioms the kernel actually used, so the host process can confirm the
  proof was not stubbed with `sorry`.
-/

import MedicalKnowledge

namespace ClinicalAudit.ScenarioA

open ClinicalAudit

/-! ## Patient axiomatization

    `JohnDoe` is a fresh inhabitant of `Patient`. The two `obs_*` axioms
    encode the chart-derived findings the audit needs. -/

axiom JohnDoe : Patient
axiom obs_essential_hypertension : HasEssentialHypertension JohnDoe
axiom obs_severe_dehydration     : HasSevereDehydration     JohnDoe

/-- The AHA/ACC HTN axiom fires on JohnDoe and concludes that a thiazide
    diuretic is indicated. -/
theorem thiazide_indicated :
    Indicated JohnDoe Treatment.thiazideDiuretic :=
  AHA_ACC_HTN_8_1_5 JohnDoe obs_essential_hypertension

/-- The KDIGO AKI axiom fires on JohnDoe and concludes that any diuretic
    is contraindicated. -/
theorem thiazide_contraindicated :
    Contraindicated JohnDoe Treatment.thiazideDiuretic :=
  KDIGO_AKI_3_1_2 JohnDoe obs_severe_dehydration

/-- The deontic collision: thiazide diuretic is simultaneously indicated
    and contraindicated for JohnDoe. -/
theorem collision_detected :
    Collision JohnDoe Treatment.thiazideDiuretic := by
  unfold Collision
  apply And.intro
  · exact thiazide_indicated
  · exact thiazide_contraindicated

/-- Final audit theorem: the encoded axioms entail `False`. -/
theorem absurd : False := by
  apply incompatible_modalities JohnDoe Treatment.thiazideDiuretic
  exact collision_detected

-- Emit the trusted-axiom witness for the host parser.
#print axioms absurd

end ClinicalAudit.ScenarioA
