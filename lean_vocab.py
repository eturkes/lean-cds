"""Plain-English gloss table for every MedicalKnowledge symbol used.

The scenario files in ``lean/`` never define the medical vocabulary
themselves; they import ``MedicalKnowledge`` and apply its predicates
and axioms to a fresh patient. A reader with no Lean background can
follow the local declarations once the syntax tooltips are in place,
but they still have no way of knowing what ``AHA_ACC_HTN_8_1_5`` does
or how ``Indicated p t`` is meant to be read.

This module is the single source of truth for that mapping. Each
entry describes one imported symbol's role, its underlying Lean
shape, and the plain-English phrasing the hover tooltips use when
that symbol appears as the head of a multi-word phrase in a scenario
file. Keeping it here (rather than scattered through
``lean_decorate.py``) makes it obvious where to edit when a new
guideline is added to ``MedicalKnowledge.lean``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


# Symbol roles. A phrase tooltip is composed differently depending on
# what kind of symbol heads the phrase.
ROLE_PATIENT_TYPE = "patient_type"  # `Patient`
ROLE_TREATMENT_CTOR = "treatment_ctor"  # `Treatment.thiazideDiuretic`
ROLE_PROPOSITION = "proposition"  # `False`
ROLE_CONDITION_PRED = "condition_pred"  # `HasEssentialHypertension`
ROLE_DEONTIC_PRED = "deontic_pred"  # `Indicated`, `Contraindicated`
ROLE_COLLISION_DEF = "collision_def"  # `Collision` (a `def`, not a pred)
ROLE_GUIDELINE_AXIOM = "guideline_axiom"  # `AHA_ACC_HTN_8_1_5`, etc.
ROLE_GLOBAL_AXIOM = "global_axiom"  # `incompatible_modalities`
ROLE_AND_INTRO = "and_intro"  # `And.intro`


@dataclass(frozen=True)
class VocabEntry:
    """One imported MedicalKnowledge symbol as the tooltip should read it."""

    role: str
    # ``plain`` is the atomic noun phrase used when the symbol is
    # mentioned but not applied — "the AHA/ACC hypertension guideline".
    plain: str
    # ``reads`` is how the symbol reads when applied to its arguments —
    # for ``HasEssentialHypertension``, "has essential hypertension".
    reads: str = ""
    # ``shape`` captures the Lean type signature the reader can refer
    # back to when the composed tooltip is not enough.
    shape: str = ""
    # ``source`` names the real-world publication a guideline axiom
    # encodes. Only populated for ``ROLE_GUIDELINE_AXIOM``.
    source: str = ""
    # ``noun`` is the way a treatment constructor reads when it is an
    # argument of a deontic predicate — ``a thiazide diuretic``.
    noun: str = ""


# The medical vocabulary. Keys are the Lean identifiers as they appear
# in the scenario files; values carry the plain-English phrasings used
# by the hover tooltip composer in ``lean_decorate.compose_group_tip``.

MEDKB_VOCAB: dict[str, VocabEntry] = {
    # ---- Types / constants -------------------------------------------
    "Patient": VocabEntry(
        role=ROLE_PATIENT_TYPE,
        plain="the opaque `Patient` type",
        noun="a patient",
    ),
    "Treatment.thiazideDiuretic": VocabEntry(
        role=ROLE_TREATMENT_CTOR,
        plain="the `thiazideDiuretic` constructor of the `Treatment` enum",
        noun="a thiazide diuretic",
    ),
    "Treatment.ivRegularInsulin": VocabEntry(
        role=ROLE_TREATMENT_CTOR,
        plain="the `ivRegularInsulin` constructor of the `Treatment` enum",
        noun="IV regular insulin",
    ),
    "Treatment.benzodiazepine": VocabEntry(
        role=ROLE_TREATMENT_CTOR,
        plain="the `benzodiazepine` constructor of the `Treatment` enum",
        noun="a short-acting benzodiazepine",
    ),
    "False": VocabEntry(
        role=ROLE_PROPOSITION,
        plain="`False` — the proposition that is never true",
    ),
    # ---- Condition predicates (Patient → Prop) -----------------------
    "HasEssentialHypertension": VocabEntry(
        role=ROLE_CONDITION_PRED,
        plain="the condition predicate `HasEssentialHypertension`",
        reads="has a confirmed diagnosis of essential hypertension",
        shape="Patient → Prop",
    ),
    "HasSevereDehydration": VocabEntry(
        role=ROLE_CONDITION_PRED,
        plain="the condition predicate `HasSevereDehydration`",
        reads="shows clinical evidence of severe dehydration",
        shape="Patient → Prop",
    ),
    "HasDiabeticKetoacidosis": VocabEntry(
        role=ROLE_CONDITION_PRED,
        plain="the condition predicate `HasDiabeticKetoacidosis`",
        reads="meets DKA criteria",
        shape="Patient → Prop",
    ),
    "HasSerumPotassiumGE33": VocabEntry(
        role=ROLE_CONDITION_PRED,
        plain="the condition predicate `HasSerumPotassiumGE33`",
        reads="has serum K⁺ at least 3.3 mEq/L",
        shape="Patient → Prop",
    ),
    "HasSevereHypokalemia": VocabEntry(
        role=ROLE_CONDITION_PRED,
        plain="the condition predicate `HasSevereHypokalemia`",
        reads="has severe hypokalaemia (serum K⁺ below 3.3 mEq/L)",
        shape="Patient → Prop",
    ),
    "HasAcutePanicEpisode": VocabEntry(
        role=ROLE_CONDITION_PRED,
        plain="the condition predicate `HasAcutePanicEpisode`",
        reads="is presenting in an acute, debilitating panic episode",
        shape="Patient → Prop",
    ),
    "HasUntreatedSevereOSA": VocabEntry(
        role=ROLE_CONDITION_PRED,
        plain="the condition predicate `HasUntreatedSevereOSA`",
        reads=(
            "has polysomnography-confirmed severe obstructive sleep "
            "apnoea and is not yet on positive airway pressure therapy"
        ),
        shape="Patient → Prop",
    ),
    # ---- Deontic predicates (Patient → Treatment → Prop) -------------
    "Indicated": VocabEntry(
        role=ROLE_DEONTIC_PRED,
        plain="the deontic predicate `Indicated`",
        reads="is indicated for",
        shape="Patient → Treatment → Prop",
    ),
    "Contraindicated": VocabEntry(
        role=ROLE_DEONTIC_PRED,
        plain="the deontic predicate `Contraindicated`",
        reads="is contraindicated for",
        shape="Patient → Treatment → Prop",
    ),
    "Collision": VocabEntry(
        role=ROLE_COLLISION_DEF,
        plain="the `Collision` def",
        reads="is simultaneously indicated AND contraindicated for",
        shape="Patient → Treatment → Prop  := Indicated p t ∧ Contraindicated p t",
    ),
    # ---- Guideline axioms --------------------------------------------
    "AHA_ACC_HTN_8_1_5": VocabEntry(
        role=ROLE_GUIDELINE_AXIOM,
        plain="the AHA/ACC hypertension guideline §8.1.5 axiom",
        reads=(
            "if a patient has essential hypertension, a thiazide diuretic "
            "is indicated for them"
        ),
        shape=(
            "∀ p, HasEssentialHypertension p → "
            "Indicated p Treatment.thiazideDiuretic"
        ),
        source="AHA/ACC Hypertension Guideline §8.1.5",
    ),
    "KDIGO_AKI_3_1_2": VocabEntry(
        role=ROLE_GUIDELINE_AXIOM,
        plain="the KDIGO Acute Kidney Injury guideline §3.1.2 axiom",
        reads=(
            "if a patient has severe dehydration, any diuretic is "
            "contraindicated for them"
        ),
        shape=(
            "∀ p, HasSevereDehydration p → "
            "Contraindicated p Treatment.thiazideDiuretic"
        ),
        source="KDIGO AKI Guideline §3.1.2",
    ),
    "ADA_DKA_Sec16": VocabEntry(
        role=ROLE_GUIDELINE_AXIOM,
        plain="the ADA Standards of Care §16 axiom",
        reads=(
            "if a patient is in DKA, IV regular insulin is indicated "
            "for them"
        ),
        shape=(
            "∀ p, HasDiabeticKetoacidosis p → "
            "Indicated p Treatment.ivRegularInsulin"
        ),
        source="ADA Standards of Care §16",
    ),
    "AACE_ACE_CSR4": VocabEntry(
        role=ROLE_GUIDELINE_AXIOM,
        plain="the AACE/ACE Critical Safety Recommendation 4 axiom",
        reads=(
            "if a patient has severe hypokalaemia, insulin is "
            "contraindicated for them"
        ),
        shape=(
            "∀ p, HasSevereHypokalemia p → "
            "Contraindicated p Treatment.ivRegularInsulin"
        ),
        source="AACE/ACE Critical Safety Recommendation 4",
    ),
    "APA_Panic_Acute": VocabEntry(
        role=ROLE_GUIDELINE_AXIOM,
        plain="the APA panic-disorder guideline axiom",
        reads=(
            "if a patient is in an acute panic episode, a short-acting "
            "benzodiazepine is indicated for them"
        ),
        shape=(
            "∀ p, HasAcutePanicEpisode p → "
            "Indicated p Treatment.benzodiazepine"
        ),
        source="APA Panic Disorder Practice Guideline",
    ),
    "AASM_OSA_PharmSafety": VocabEntry(
        role=ROLE_GUIDELINE_AXIOM,
        plain="the AASM OSA pharmacologic-safety axiom",
        reads=(
            "if a patient has untreated severe obstructive sleep "
            "apnoea, benzodiazepines are contraindicated for them"
        ),
        shape=(
            "∀ p, HasUntreatedSevereOSA p → "
            "Contraindicated p Treatment.benzodiazepine"
        ),
        source="AASM Adult OSA Guideline, Pharmacologic Safety Statement",
    ),
    # ---- Global axioms / constructors --------------------------------
    "incompatible_modalities": VocabEntry(
        role=ROLE_GLOBAL_AXIOM,
        plain="the `incompatible_modalities` axiom",
        reads=(
            "no treatment can be simultaneously indicated and "
            "contraindicated for the same patient"
        ),
        shape="∀ p t, ¬ (Indicated p t ∧ Contraindicated p t)",
    ),
    "And.intro": VocabEntry(
        role=ROLE_AND_INTRO,
        plain="Lean's `And.intro` constructor",
        reads=(
            "to prove a conjunction `P ∧ Q`, supply a proof of `P` and "
            "a proof of `Q` separately"
        ),
    ),
}


def lookup(symbol: str) -> Optional[VocabEntry]:
    """Return the vocab entry for an imported MedicalKnowledge symbol.

    Returns ``None`` if ``symbol`` isn't in the table — callers should
    fall back to a generic composition for identifiers declared locally
    in the scenario file (patient names, observation axioms, earlier
    theorems).
    """
    return MEDKB_VOCAB.get(symbol)
