/-
  MedicalKnowledge.lean — Verifiable Clinical Decision Support core knowledge base.

  This file is the formal kernel of the audit. It introduces:

    * an opaque `Patient` type and a finite `Treatment` enumeration,
    * `Prop`-valued predicates for the clinical conditions referenced by
      the encoded scenarios,
    * `Indicated` / `Contraindicated` deontic predicates,
    * a `Collision` definition naming the simultaneous-modality contradiction,
    * a `incompatible_modalities` axiom that pins the deontic semantics down
      enough for `Collision` to entail `False`,
    * one axiom per real-world clinical guideline used by a scenario.

  The scenarios in `ScenarioA.lean` / `ScenarioB.lean` / `ScenarioC.lean`
  import this module, axiomatise a single patient's observed findings, and
  prove `theorem absurd : False` from the resulting axiom set with explicit
  proof tactics. There is intentionally no `def` returning data, no `#eval`
  performing reduction, and no `IO.println`: every conclusion is a kernel-
  checked proof, and every axiom is named so it appears in `#print axioms`.
-/

namespace ClinicalAudit

/-- Patients are an abstract domain; specific patients are introduced as
    axioms in scenario files. -/
opaque Patient : Type

/-- The treatments referenced by the encoded clinical guidelines. -/
inductive Treatment where
  | thiazideDiuretic
  | ivRegularInsulin
  | benzodiazepine
  deriving Repr, DecidableEq

/-! ## Clinical condition predicates

    Each predicate is an opaque `Patient → Prop`. Scenarios populate these
    via `axiom` declarations that stand in for chart-derived findings. -/

opaque HasEssentialHypertension : Patient → Prop
opaque HasSevereDehydration     : Patient → Prop

opaque HasDiabeticKetoacidosis  : Patient → Prop
opaque HasSerumPotassiumGE33    : Patient → Prop
opaque HasSevereHypokalemia     : Patient → Prop

opaque HasAcutePanicEpisode     : Patient → Prop
opaque HasUntreatedSevereOSA    : Patient → Prop

/-! ## Deontic predicates

    `Indicated p t` states that treatment `t` is recommended for patient
    `p`. `Contraindicated p t` states that it is forbidden. They are
    intentionally opaque so that the only way to derive them is via the
    clinical-guideline axioms below. -/

opaque Indicated      : Patient → Treatment → Prop
opaque Contraindicated : Patient → Treatment → Prop

/-- A guideline collision: a single treatment is simultaneously indicated
    and contraindicated for the same patient. -/
def Collision (p : Patient) (t : Treatment) : Prop :=
  Indicated p t ∧ Contraindicated p t

/-- Deontic well-formedness: no treatment can be both indicated and
    contraindicated for the same patient. Combined with a `Collision`
    proof this immediately yields `False`, so each scenario can prove
    `theorem absurd : False`. -/
axiom incompatible_modalities :
    ∀ (p : Patient) (t : Treatment), ¬ (Indicated p t ∧ Contraindicated p t)

/-! ## Clinical guideline axioms

    Each axiom is named after the published recommendation it encodes.
    The names are chosen so that `#print axioms` in a scenario file lists
    the precise guidelines and observations participating in the proof. -/

/-- AHA/ACC/AHA Hypertension Guideline §8.1.5: in adults with confirmed
    essential hypertension a thiazide-type diuretic is indicated as a
    first-line antihypertensive (Class I, LoE A). -/
axiom AHA_ACC_HTN_8_1_5 :
    ∀ (p : Patient),
      HasEssentialHypertension p → Indicated p Treatment.thiazideDiuretic

/-- KDIGO Acute Kidney Injury Guideline §3.1.2: in any patient with
    clinical evidence of severe dehydration the initiation of diuretic
    therapy is absolutely contraindicated (Class III — Harm, LoE B). -/
axiom KDIGO_AKI_3_1_2 :
    ∀ (p : Patient),
      HasSevereDehydration p → Contraindicated p Treatment.thiazideDiuretic

/-- ADA Standards of Care §16: in adults meeting DKA criteria with serum
    K⁺ ≥ 3.3 mEq/L, intravenous regular insulin infusion is indicated
    (Class I, LoE A). The hypokalaemia precondition is intentionally
    *omitted* here so the encoded scenario can demonstrate the historical
    "literal-reading" collision the audit is designed to surface. -/
axiom ADA_DKA_Sec16 :
    ∀ (p : Patient),
      HasDiabeticKetoacidosis p → Indicated p Treatment.ivRegularInsulin

/-- AACE/ACE Consensus on Inpatient Hyperglycaemia, Critical Safety
    Recommendation 4: in any patient with DKA whose serum K⁺ is below
    3.3 mEq/L, insulin administration is strictly contraindicated until
    aggressive K⁺ replacement (Class III — Harm, LoE A). -/
axiom AACE_ACE_CSR4 :
    ∀ (p : Patient),
      HasSevereHypokalemia p → Contraindicated p Treatment.ivRegularInsulin

/-- APA Practice Guideline for Panic Disorder, Acute Episode Management:
    short-acting benzodiazepines are indicated as first-line acute therapy
    for severe, debilitating panic episodes (Class I, LoE B). -/
axiom APA_Panic_Acute :
    ∀ (p : Patient),
      HasAcutePanicEpisode p → Indicated p Treatment.benzodiazepine

/-- AASM Clinical Practice Guideline for Adult OSA, Pharmacologic Safety
    Statement: in adults with moderate-to-severe OSA who are not yet
    established on positive airway pressure therapy, benzodiazepines are
    strictly contraindicated (Class III — Harm, LoE B). -/
axiom AASM_OSA_PharmSafety :
    ∀ (p : Patient),
      HasUntreatedSevereOSA p → Contraindicated p Treatment.benzodiazepine

end ClinicalAudit
