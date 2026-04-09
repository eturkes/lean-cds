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

axiom JSH2019_Ch5_FirstLine :
    ∀ (p : Patient),
      HasEssentialHypertension p → Indicated p Treatment.thiazideDiuretic

axiom JSN_AKI2016_Diuretics :
    ∀ (p : Patient),
      HasSevereDehydration p → Contraindicated p Treatment.thiazideDiuretic

axiom JDS2024_Sec20_1_DKA :
    ∀ (p : Patient),
      HasDiabeticKetoacidosis p → Indicated p Treatment.ivRegularInsulin

axiom JDS2024_Sec20_1_KMgmt :
    ∀ (p : Patient),
      HasSevereHypokalemia p → Contraindicated p Treatment.ivRegularInsulin

axiom JSAD_JSNP_Panic2025_Acute :
    ∀ (p : Patient),
      HasAcutePanicEpisode p → Indicated p Treatment.benzodiazepine

axiom JRS_SAS2020_BZD :
    ∀ (p : Patient),
      HasUntreatedSevereOSA p → Contraindicated p Treatment.benzodiazepine

end ClinicalAudit
