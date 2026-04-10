namespace ClinicalAudit

opaque Patient : Type

inductive Treatment where
  | thiazideDiuretic
  | ivRegularInsulin
  | benzodiazepine
  deriving Repr, DecidableEq

opaque HasEssentialHypertension : Patient → Prop
opaque HasSevereDehydration     : Patient → Prop

opaque HasDiabeticKetoacidosis  : Patient → Prop
opaque HasSerumPotassiumGE33    : Patient → Prop
opaque HasSevereHypokalemia     : Patient → Prop

opaque HasAcutePanicEpisode     : Patient → Prop
opaque HasUntreatedSevereOSA    : Patient → Prop

opaque Indicated      : Patient → Treatment → Prop
opaque Contraindicated : Patient → Treatment → Prop

def Collision (p : Patient) (t : Treatment) : Prop :=
  Indicated p t ∧ Contraindicated p t

axiom incompatible_modalities :
    ∀ (p : Patient) (t : Treatment), ¬ (Indicated p t ∧ Contraindicated p t)

axiom AHA_ACC_HTN_8_1_6 :
    ∀ (p : Patient),
      HasEssentialHypertension p → Indicated p Treatment.thiazideDiuretic

axiom KDIGO_AKI_3_4 :
    ∀ (p : Patient),
      HasSevereDehydration p → Contraindicated p Treatment.thiazideDiuretic

axiom ADA_DKA_Sec16 :
    ∀ (p : Patient),
      HasDiabeticKetoacidosis p → Indicated p Treatment.ivRegularInsulin

axiom ADA_DKA_Sec16_KSafety :
    ∀ (p : Patient),
      HasSevereHypokalemia p → Contraindicated p Treatment.ivRegularInsulin

axiom APA_Panic_Acute :
    ∀ (p : Patient),
      HasAcutePanicEpisode p → Indicated p Treatment.benzodiazepine

axiom AASM_OSA_PharmSafety :
    ∀ (p : Patient),
      HasUntreatedSevereOSA p → Contraindicated p Treatment.benzodiazepine

end ClinicalAudit
