"""Per-locale plain-language gloss table for every MedicalKnowledge symbol.

The scenario files in ``lean/<locale>/`` never define the medical
vocabulary themselves; they import a sibling ``MedicalKnowledge`` and
apply its predicates and axioms to a fresh patient. A reader with no
Lean background can follow the local declarations once the syntax
tooltips are in place, but they still have no way of knowing what
``JSH2019_Ch5_FirstLine`` does or how ``Indicated p t`` is meant to be
read.

This module is the single source of truth for that mapping. Each
locale has its own dictionary so:

* the **English** build (``lean/en/``) talks about ``JohnDoe``,
  ``AHA_ACC_HTN_8_1_5``, ``KDIGO_AKI_3_1_2``, etc., with English
  tooltip prose;
* the **Japanese** build (``lean/ja/``) talks about ``TaroYamada``,
  ``JSH2019_Ch5_FirstLine``, ``JSN_AKI2016_Diuretics``, etc., with
  Japanese tooltip prose.

Universal medical predicates such as ``HasEssentialHypertension`` keep
the same Lean identifier in both locales but their plain-language
``reads`` text is translated. Keeping every entry here (rather than
scattered through ``lean_decorate.py``) makes it obvious where to edit
when a new guideline is added to either ``MedicalKnowledge.lean``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from i18n import normalize_locale


# Symbol roles. A phrase tooltip is composed differently depending on
# what kind of symbol heads the phrase.
ROLE_PATIENT_TYPE = "patient_type"  # `Patient`
ROLE_TREATMENT_CTOR = "treatment_ctor"  # `Treatment.thiazideDiuretic`
ROLE_PROPOSITION = "proposition"  # `False`
ROLE_CONDITION_PRED = "condition_pred"  # `HasEssentialHypertension`
ROLE_DEONTIC_PRED = "deontic_pred"  # `Indicated`, `Contraindicated`
ROLE_COLLISION_DEF = "collision_def"  # `Collision` (a `def`, not a pred)
ROLE_GUIDELINE_AXIOM = "guideline_axiom"  # `JSH2019_Ch5_FirstLine`, etc.
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


# ---------------------------------------------------------------------------
# English (American clinical guidelines).
# ---------------------------------------------------------------------------

_EN_VOCAB: dict[str, VocabEntry] = {
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
    # ---- Guideline axioms (American sources) -------------------------
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


# ---------------------------------------------------------------------------
# Japanese (Japanese clinical guidelines).
# ---------------------------------------------------------------------------

_JA_VOCAB: dict[str, VocabEntry] = {
    # ---- Types / constants -------------------------------------------
    "Patient": VocabEntry(
        role=ROLE_PATIENT_TYPE,
        plain="不透明な `Patient` 型",
        noun="患者",
    ),
    "Treatment.thiazideDiuretic": VocabEntry(
        role=ROLE_TREATMENT_CTOR,
        plain="`Treatment` 列挙体の `thiazideDiuretic` コンストラクタ",
        noun="サイアザイド系利尿薬",
    ),
    "Treatment.ivRegularInsulin": VocabEntry(
        role=ROLE_TREATMENT_CTOR,
        plain="`Treatment` 列挙体の `ivRegularInsulin` コンストラクタ",
        noun="速効型インスリン静注",
    ),
    "Treatment.benzodiazepine": VocabEntry(
        role=ROLE_TREATMENT_CTOR,
        plain="`Treatment` 列挙体の `benzodiazepine` コンストラクタ",
        noun="短時間作用型ベンゾジアゼピン",
    ),
    "False": VocabEntry(
        role=ROLE_PROPOSITION,
        plain="`False` ── 決して真にならない命題",
    ),
    # ---- Condition predicates (Patient → Prop) -----------------------
    "HasEssentialHypertension": VocabEntry(
        role=ROLE_CONDITION_PRED,
        plain="病態述語 `HasEssentialHypertension`",
        reads="本態性高血圧の確定診断を有する",
        shape="Patient → Prop",
    ),
    "HasSevereDehydration": VocabEntry(
        role=ROLE_CONDITION_PRED,
        plain="病態述語 `HasSevereDehydration`",
        reads="重症脱水の臨床所見を呈する",
        shape="Patient → Prop",
    ),
    "HasDiabeticKetoacidosis": VocabEntry(
        role=ROLE_CONDITION_PRED,
        plain="病態述語 `HasDiabeticKetoacidosis`",
        reads="DKA の診断基準を満たす",
        shape="Patient → Prop",
    ),
    "HasSerumPotassiumGE33": VocabEntry(
        role=ROLE_CONDITION_PRED,
        plain="病態述語 `HasSerumPotassiumGE33`",
        reads="血清 K⁺ が 3.3 mEq/L 以上である",
        shape="Patient → Prop",
    ),
    "HasSevereHypokalemia": VocabEntry(
        role=ROLE_CONDITION_PRED,
        plain="病態述語 `HasSevereHypokalemia`",
        reads="重症低カリウム血症（血清 K⁺ < 3.3 mEq/L）を呈する",
        shape="Patient → Prop",
    ),
    "HasAcutePanicEpisode": VocabEntry(
        role=ROLE_CONDITION_PRED,
        plain="病態述語 `HasAcutePanicEpisode`",
        reads="急性かつ重度のパニック発作を呈している",
        shape="Patient → Prop",
    ),
    "HasUntreatedSevereOSA": VocabEntry(
        role=ROLE_CONDITION_PRED,
        plain="病態述語 `HasUntreatedSevereOSA`",
        reads=(
            "終夜睡眠ポリグラフ検査で確定された重症閉塞性睡眠時無呼吸を"
            "有し、未だ持続陽圧呼吸（CPAP）療法が導入されていない"
        ),
        shape="Patient → Prop",
    ),
    # ---- Deontic predicates (Patient → Treatment → Prop) -------------
    "Indicated": VocabEntry(
        role=ROLE_DEONTIC_PRED,
        plain="義務論的述語 `Indicated`",
        reads="に対して適応される",
        shape="Patient → Treatment → Prop",
    ),
    "Contraindicated": VocabEntry(
        role=ROLE_DEONTIC_PRED,
        plain="義務論的述語 `Contraindicated`",
        reads="に対して禁忌である",
        shape="Patient → Treatment → Prop",
    ),
    "Collision": VocabEntry(
        role=ROLE_COLLISION_DEF,
        plain="`Collision` 定義",
        reads="に対して同時に適応かつ禁忌である",
        shape="Patient → Treatment → Prop  := Indicated p t ∧ Contraindicated p t",
    ),
    # ---- Guideline axioms (Japanese sources) -------------------------
    "JSH2019_Ch5_FirstLine": VocabEntry(
        role=ROLE_GUIDELINE_AXIOM,
        plain="日本高血圧学会『高血圧治療ガイドライン2019』第5章の公理",
        reads=(
            "本態性高血圧を有する患者に対し、サイアザイド系利尿薬を"
            "第一選択降圧薬として適応する"
        ),
        shape=(
            "∀ p, HasEssentialHypertension p → "
            "Indicated p Treatment.thiazideDiuretic"
        ),
        source="日本高血圧学会『高血圧治療ガイドライン2019』第5章",
    ),
    "JSN_AKI2016_Diuretics": VocabEntry(
        role=ROLE_GUIDELINE_AXIOM,
        plain="日本腎臓学会ほか『AKI 診療ガイドライン2016』の利尿薬公理",
        reads=(
            "重症脱水を呈する患者に対しては、いかなる利尿薬の投与も"
            "禁忌とする"
        ),
        shape=(
            "∀ p, HasSevereDehydration p → "
            "Contraindicated p Treatment.thiazideDiuretic"
        ),
        source="日本腎臓学会『AKI 診療ガイドライン2016』",
    ),
    "JDS2024_Sec20_1_DKA": VocabEntry(
        role=ROLE_GUIDELINE_AXIOM,
        plain="日本糖尿病学会『糖尿病診療ガイドライン2024』第20-1項 DKA 公理",
        reads=(
            "DKA を呈する患者に対し、速効型インスリンの持続静注を"
            "速やかに開始する"
        ),
        shape=(
            "∀ p, HasDiabeticKetoacidosis p → "
            "Indicated p Treatment.ivRegularInsulin"
        ),
        source="日本糖尿病学会『糖尿病診療ガイドライン2024』第20-1項",
    ),
    "JDS2024_Sec20_1_KMgmt": VocabEntry(
        role=ROLE_GUIDELINE_AXIOM,
        plain="同ガイドライン第20-1項の血清カリウム管理公理",
        reads=(
            "重症低カリウム血症（血清 K⁺ < 3.3 mEq/L）を呈する患者に"
            "対しては、インスリン投与を厳禁とする"
        ),
        shape=(
            "∀ p, HasSevereHypokalemia p → "
            "Contraindicated p Treatment.ivRegularInsulin"
        ),
        source="日本糖尿病学会『糖尿病診療ガイドライン2024』第20-1項",
    ),
    "JSAD_JSNP_Panic2025_Acute": VocabEntry(
        role=ROLE_GUIDELINE_AXIOM,
        plain=(
            "日本不安症学会・日本神経精神薬理学会『パニック症の診療"
            "ガイドライン（2025年版）』の急性期公理"
        ),
        reads=(
            "急性かつ重度のパニック発作を呈する患者に対し、短時間作用型"
            "ベンゾジアゼピンを第一選択薬物療法として適応する"
        ),
        shape=(
            "∀ p, HasAcutePanicEpisode p → "
            "Indicated p Treatment.benzodiazepine"
        ),
        source=(
            "日本不安症学会・日本神経精神薬理学会『パニック症の診療"
            "ガイドライン2025』"
        ),
    ),
    "JRS_SAS2020_BZD": VocabEntry(
        role=ROLE_GUIDELINE_AXIOM,
        plain=(
            "日本呼吸器学会『睡眠時無呼吸症候群（SAS）の診療"
            "ガイドライン2020』の薬物療法安全公理"
        ),
        reads=(
            "未治療の中等症～重症閉塞性睡眠時無呼吸を有する患者に"
            "対しては、ベンゾジアゼピン系薬剤を原則禁忌とする"
        ),
        shape=(
            "∀ p, HasUntreatedSevereOSA p → "
            "Contraindicated p Treatment.benzodiazepine"
        ),
        source="日本呼吸器学会『SAS の診療ガイドライン2020』",
    ),
    # ---- Global axioms / constructors --------------------------------
    "incompatible_modalities": VocabEntry(
        role=ROLE_GLOBAL_AXIOM,
        plain="`incompatible_modalities` 公理",
        reads=(
            "同一の薬剤が同一患者に対して同時に適応かつ禁忌となることは"
            "あり得ない"
        ),
        shape="∀ p t, ¬ (Indicated p t ∧ Contraindicated p t)",
    ),
    "And.intro": VocabEntry(
        role=ROLE_AND_INTRO,
        plain="Lean の `And.intro` コンストラクタ",
        reads=(
            "連言 `P ∧ Q` を証明するには、`P` の証明と `Q` の証明を"
            "それぞれ与える"
        ),
    ),
}


_VOCAB_BY_LOCALE: dict[str, dict[str, VocabEntry]] = {
    "en": _EN_VOCAB,
    "ja": _JA_VOCAB,
}


# Backwards-compatible alias used by any caller that doesn't yet pass a
# locale. Defaults to English so old call sites keep working.
MEDKB_VOCAB: dict[str, VocabEntry] = _EN_VOCAB


def lookup(symbol: str, locale: str = "en") -> Optional[VocabEntry]:
    """Return the vocab entry for an imported MedicalKnowledge symbol.

    Returns ``None`` if ``symbol`` isn't in the table — callers should
    fall back to a generic composition for identifiers declared locally
    in the scenario file (patient names, observation axioms, earlier
    theorems).
    """
    table = _VOCAB_BY_LOCALE[normalize_locale(locale)]
    return table.get(symbol)
